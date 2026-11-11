@echo off
setlocal
set "PROJECT_DIR=%~dp0"
set "PROJECT=%PROJECT_DIR%VisionClaw_Motion.uvprojx"
if not exist "%PROJECT%" goto fail

set "UV4="
for %%P in (
  "D:\EmbeddedDev\Keil_v5\UV4\UV4.exe"
  "C:\Keil_v5\UV4\UV4.exe"
  "C:\Keil5\UV4\UV4.exe"
  "D:\Keil_v5\UV4\UV4.exe"
  "D:\Keil5\UV4\UV4.exe"
) do if not defined UV4 if exist "%%~P" set "UV4=%%~P"
if not defined UV4 goto keil_fail
if exist "D:\EmbeddedDev\KeilPacks" set "CMSIS_PACK_ROOT=D:\EmbeddedDev\KeilPacks"
if exist "D:\EmbeddedDev\ArmLicenses" set "ARMLM_CACHED_LICENSES_LOCATION=D:\EmbeddedDev\ArmLicenses"

start "" "%UV4%" "%PROJECT%"
exit /b 0
:fail
echo Could not find VisionClaw_Motion project.
pause
exit /b 1
:keil_fail
echo Could not find UV4.exe. Install Keil MDK-ARM or add its path to this script.
pause
exit /b 1
