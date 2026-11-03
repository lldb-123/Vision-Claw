$ErrorActionPreference = 'Stop'
$taskDriver = Join-Path $PSScriptRoot 'tools\stlink_driver'
if (-not (Test-Path -LiteralPath (Join-Path $taskDriver 'stlink_dbg_winusb.inf'))) {
    Write-Host '本仓库不附带第三方驱动。请从 ST 官方下载 STSW-LINK009，按 README 解压到 tools\stlink_driver。'
    exit 1
}
$taskIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$taskPrincipal = [Security.Principal.WindowsPrincipal]::new($taskIdentity)
if (-not $taskPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host 'Windows 需要管理员权限安装 USB 驱动，接下来会显示系统提示。'
    $taskArguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $PSCommandPath + '"'))
    try {
        $taskProcess = Start-Process -FilePath 'powershell.exe' -Verb RunAs -WindowStyle Hidden -ArgumentList $taskArguments -Wait -PassThru
        if ($taskProcess.ExitCode -ne 0) { throw ('安装未完成，退出码：' + $taskProcess.ExitCode) }
        Write-Host '驱动安装命令已完成。若设备未刷新，请拔插一次 ST-Link。'
        exit 0
    } catch {
        Write-Host $_.Exception.Message
        exit 1
    }
}

$taskLogDirectory = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Path $taskLogDirectory -Force | Out-Null
Start-Transcript -Path (Join-Path $taskLogDirectory 'install_driver.log') -Append | Out-Null
try {
    $taskCatalog = Join-Path $taskDriver 'stlinkdbgwinusb_x64.cat'
    $taskSignature = Get-AuthenticodeSignature -LiteralPath $taskCatalog
    if ($taskSignature.Status -ne 'Valid' -or $taskSignature.SignerCertificate.Subject -notmatch 'STMicroelectronics') {
        throw '驱动目录签名校验失败，未安装。'
    }
    & pnputil.exe /add-driver (Join-Path $taskDriver 'stlink_dbg_winusb.inf') /install
    $taskResult = $LASTEXITCODE
    if ($taskResult -notin @(0, 3010)) { throw ('pnputil 返回：' + $taskResult) }
    & pnputil.exe /scan-devices
    Get-CimInstance Win32_PnPEntity -Filter "PNPDeviceID LIKE 'USB%VID_0483&PID_3748%'" | Select-Object Name, ConfigManagerErrorCode | Format-List
} catch {
    Write-Host $_.Exception.Message
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
