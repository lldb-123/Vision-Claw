$ErrorActionPreference='Stop'
$env:CMSIS_PACK_ROOT='D:\EmbeddedDev\KeilPacks'
$env:ARMLM_CACHED_LICENSES_LOCATION='D:\EmbeddedDev\ArmLicenses'
$env:TEMP='D:\EmbeddedDev\motion-build-tmp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
$project=Join-Path $PSScriptRoot 'VisionClaw_Motion.uvprojx'
$log=Join-Path $PSScriptRoot 'keil-build.log'
$arguments='-b "'+$project+'" -t VisionClaw_Motion -o "'+$log+'"'
$p=Start-Process 'D:\EmbeddedDev\Keil_v5\UV4\UV4.exe' -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log}
if($p.ExitCode -gt 1){throw "Keil build failed: $($p.ExitCode)"}
