@echo off
setlocal
set "CMSIS_PACK_ROOT=D:\EmbeddedDev\KeilPacks"
set "ARMLM_CACHED_LICENSES_LOCATION=D:\EmbeddedDev\ArmLicenses"
set "TEMP=D:\EmbeddedDev\motion-build-tmp"
set "TMP=D:\EmbeddedDev\motion-build-tmp"
if not exist "%TEMP%" mkdir "%TEMP%"
cd /d "D:\EmbeddedDev\VisionClawMotion\MDK-ARM"
if errorlevel 1 goto fail
if not exist "VisionClaw_Motion.uvprojx" goto fail
start "" "D:\EmbeddedDev\Keil_v5\UV4\UV4.exe" "D:\EmbeddedDev\VisionClawMotion\MDK-ARM\VisionClaw_Motion.uvprojx"
exit /b 0
:fail
echo Could not find VisionClaw_Motion project.
pause
exit /b 1
