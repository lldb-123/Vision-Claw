$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$env:TEMP='D:\EmbeddedDev\motion-build-tmp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
$gcc=(Get-ChildItem 'D:\EmbeddedDev\STM32CubeIDE' -Filter arm-none-eabi-gcc.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
$vendor='D:\EmbeddedDev\STM32_Workspace\Task1_CubeMX_Fixed'
$drivers=Join-Path $vendor 'Drivers'
$flags=@('-mcpu=cortex-m4','-mthumb','-mfloat-abi=hard','-mfpu=fpv4-sp-d16','-DSTM32F407xx','-DUSE_HAL_DRIVER','-Os','-g3','-Wall','-Wextra','-ffunction-sections','-fdata-sections','-Iplatform','-Iplatform/device','-ICore/Inc',"-I$drivers\STM32F4xx_HAL_Driver\Inc","-I$drivers\CMSIS\Include","-I$drivers\CMSIS\Device\ST\STM32F4xx\Include")
$sources=@('platform\startup.c','platform\main.c','Core\Src\motion_control.c','Core\Src\stm32_actuators.c',"$vendor\Core\Src\system_stm32f4xx.c")
foreach($name in @('hal','hal_cortex','hal_rcc','hal_rcc_ex','hal_flash','hal_flash_ex','hal_pwr','hal_pwr_ex','hal_gpio','hal_tim','hal_tim_ex','hal_uart','hal_dma')){$sources+=Join-Path $drivers "STM32F4xx_HAL_Driver\Src\stm32f4xx_$name.c"}
$objects=@()
foreach($src in $sources){$obj=Join-Path 'build' (([IO.Path]::GetFileNameWithoutExtension($src))+'.o');& $gcc @flags -c $src -o $obj;if($LASTEXITCODE){throw "Compile failed: $src"};$objects+=$obj}
& $gcc @flags @objects '-Tplatform/stm32f407ve.ld' '-Wl,--gc-sections,-Map=build/motion.map' '--specs=nano.specs' '--specs=nosys.specs' -lm -o build\motion.elf
if($LASTEXITCODE){throw 'Link failed'}
& (Join-Path (Split-Path $gcc) 'arm-none-eabi-objcopy.exe') -O ihex build\motion.elf build\motion.hex
& (Join-Path (Split-Path $gcc) 'arm-none-eabi-size.exe') build\motion.elf


