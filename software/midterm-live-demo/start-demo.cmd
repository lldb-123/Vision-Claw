@echo off
cd /d "%~dp0"
echo Starting camera and model. Please wait...
if not exist ".venv\Scripts\python.exe" (
  echo Demo Python environment not found.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" live_demo.py
if errorlevel 1 pause
