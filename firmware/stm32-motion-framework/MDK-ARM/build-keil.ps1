$ErrorActionPreference='Stop'

$uv4Candidates=@(
  'C:\Keil_v5\UV4\UV4.exe',
  'C:\Keil5\UV4\UV4.exe',
  'D:\Keil_v5\UV4\UV4.exe',
  'D:\Keil5\UV4\UV4.exe'
)
$uv4=$uv4Candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if(-not $uv4){throw 'UV4.exe not found. Install Keil MDK-ARM or add its UV4.exe path to this script.'}

$project=Join-Path $PSScriptRoot 'VisionClaw_Motion.uvprojx'
$log=Join-Path $PSScriptRoot 'keil-build.log'
$arguments='-b "'+$project+'" -t VisionClaw_Motion -o "'+$log+'"'
$p=Start-Process $uv4 -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log}
if($p.ExitCode -gt 1){throw "Keil build failed: $($p.ExitCode)"}
