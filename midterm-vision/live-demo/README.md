# 实时六形状演示

`live_demo.py` 使用固定托盘相机，在窗口中显示六形状中文检测框、置信度和计数。默认读取 [`../weights/best.pt`](../weights/best.pt)，即 698 张数据训练得到的最佳模型。颜色识别尚未集成，也不会自动保存视频。

先准备 Python 环境，需有 CUDA PyTorch、Ultralytics、OpenCV、Pillow 和 NumPy。在原电脑上可复用已有训练环境：

```powershell
Set-Location 'C:\Users\Lenovo\Documents\ChatGPT\工创赛-midterm-vision\midterm-vision\live-demo'
$env:VISION_PYTHON = 'F:\gcs_medium_check_YOLO_model\.venv\Scripts\python.exe'
.\start-demo.cmd
```

或直接运行 `& $env:VISION_PYTHON .\live_demo.py --check`，只读取一帧并推理，不打开交互窗口。相机默认依次尝试 MSMF 索引 1、DirectShow 索引 0；可用 `--backend`、`--camera-index` 指定。正式窗口按 Q、Esc 或关闭窗口退出。

此代码先前仅用首轮模型完成过单帧相机与 GPU 链路检查；**仓库中的新最佳权重尚未在实时窗口做现场验收**。验证集指标不等于现场混放、新光照的准确率。
