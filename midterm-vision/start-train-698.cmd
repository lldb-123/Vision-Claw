@echo off
setlocal
cd /d "%~dp0"
set "YOLO_OFFLINE=1"
if defined VISION_PYTHON (
    set "PYTHON_EXE=%VISION_PYTHON%"
) else (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
)

if not exist "%PYTHON_EXE%" (
    echo Missing Python environment: %PYTHON_EXE%
    exit /b 1
)
if not exist "weights\yolov8n.pt" (
    echo Missing local pretrained weights: weights\yolov8n.pt
    exit /b 1
)
if not exist "dataset\data.yaml" (
    echo Missing local dataset: dataset\data.yaml
    exit /b 1
)

"%PYTHON_EXE%" "train.py" --data "dataset\data.yaml" --epochs 100 --imgsz 640 --batch 8 --workers 0
exit /b %errorlevel%
