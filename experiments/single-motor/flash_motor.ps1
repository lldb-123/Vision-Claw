param(
    [string]$OpenOcdPath = '',
    [string]$OpenOcdScripts = ''
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskExecutable = $OpenOcdPath
if (-not $taskExecutable) {
    $taskExecutable = Join-Path $PSScriptRoot 'tools\xpack-openocd-0.12.0-7\bin\openocd.exe'
    if (-not (Test-Path -LiteralPath $taskExecutable)) {
        $taskCommand = Get-Command openocd -ErrorAction SilentlyContinue
        if ($taskCommand) { $taskExecutable = $taskCommand.Source }
    }
}
if (-not (Test-Path -LiteralPath $taskExecutable -PathType Leaf)) {
    throw '未找到 OpenOCD。按 README 准备 tools 下的便携工具，或使用 -OpenOcdPath 指定 exe。'
}
$taskScripts = $OpenOcdScripts
if (-not $taskScripts) {
    $taskToolRoot = Split-Path -Parent (Split-Path -Parent $taskExecutable)
    $taskCandidates = @((Join-Path $taskToolRoot 'openocd\scripts'), (Join-Path $taskToolRoot 'share\openocd\scripts'))
    $taskScripts = $taskCandidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'target\stm32f4x.cfg') } | Select-Object -First 1
}
if (-not $taskScripts -or -not (Test-Path -LiteralPath (Join-Path $taskScripts 'target\stm32f4x.cfg'))) {
    throw '未找到 OpenOCD 目标脚本目录，请使用 -OpenOcdScripts 指定 scripts 文件夹。'
}
$taskLogDirectory = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Path $taskLogDirectory -Force | Out-Null
$taskDevice = Get-CimInstance Win32_PnPEntity -Filter "PNPDeviceID LIKE 'USB%VID_0483&PID_3748%'"
if (-not $taskDevice) {
    Write-Host '没有检测到 ST-Link，请接到电脑 USB 后重试。'
    exit 1
}
if (-not ($taskDevice | Where-Object { $_.ConfigManagerErrorCode -eq 0 })) {
    Write-Host 'ST-Link 的 Windows 驱动尚未正常加载，先运行 1_安装STLink驱动.cmd。'
    exit 1
}
Write-Host '正在下载持续旋转程序：PA0=STEP，PA1=DIR，PA4=EN。'
Write-Host '电机电池应保持断开；写入会替换原程序的首个 Flash 扇区，并保存备份。'
# The connected V2J37 probe supports the native SWD transport.
$taskPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    # OpenOCD writes normal progress to stderr, including on successful runs.
    $taskOutput = & $taskExecutable -s $taskScripts -f interface/stlink.cfg -c 'transport select swd' -f target/stm32f4x.cfg -c 'adapter speed 100' -c 'gdb port disabled; tcl port disabled; telnet port disabled' -f flash_motor.cfg 2>&1
    $taskResult = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $taskPreference
}
$taskOutput | ForEach-Object { $_.ToString() } | Tee-Object -FilePath (Join-Path $taskLogDirectory 'flash.log')
if ($taskResult -ne 0) {
    Write-Host '下载未完成。若提示 unable to connect to the target，说明下载器到 STM32 的 SWD 连接未建立。'
    Write-Host '先检查：开发板自身 USB 供电；ST-Link DIO→PA13/SWDIO，CLK→PA14/SWCLK，GND→GND。'
    Write-Host '不要把 SWIM 当成 SWDIO。电机电池保持断开。'
    exit $taskResult
}
Write-Host '下载及校验完成。STM32 暂停，EN 已关闭；按开发板 RESET 才开始转动。'
Write-Host '接通电机电池，按一次 RESET：约 1 秒后起转，逐渐加速，然后持续旋转。'
Write-Host '停止：断开电机电池。复位键会重新启动旋转，不是停止键。'
