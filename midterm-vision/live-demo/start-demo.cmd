@echo off
cd /d "%~dp0"
set "YOLO_OFFLINE=1"
echo Starting camera and model. Please wait...
if defined VISION_PYTHON (
  set "PYTHON_EXE=%VISION_PYTHON%"
) else (
  set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
)
if not exist "%PYTHON_EXE%" (
  echo Demo Python environment not found.
  pause
  exit /b 1
)
"%PYTHON_EXE%" live_demo.py
if errorlevel 1 pause
