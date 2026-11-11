# 独立实时演示窗口

此目录是原电脑 `F:\VisionClaw_LiveDemo` 的代码快照，与训练工程分开。默认读取仓库中的 `datasets/midterm-yolo-prelabel-v1/model/best.pt`，使用固定托盘相机显示六形状的中文检测框、置信度和计数。颜色识别尚未实现，也不会自动保存视频。

在 Windows 上为本目录建立独立 `.venv`，安装与训练机兼容的 CUDA PyTorch、Ultralytics、OpenCV、Pillow、NumPy 后双击 `start-demo.cmd`。原电脑已为该独立演示目录配置好环境，可直接使用原目录运行；仓库不包含虚拟环境。若权重或摄像头位置不同，可在本目录执行：

```powershell
.\.venv\Scripts\python.exe .\live_demo.py --weights 'D:\path\best.pt' --backend msmf --camera-index 1
```

默认先试 MSMF 索引 1，再试 DirectShow 索引 0。`--check` 只读一帧并推理，不打开交互窗口；正式窗口按 Q、Esc 或关闭窗口退出。该程序只在原电脑做过单帧相机与 GPU 推理检查；用户现场反馈三棱柱常被识别为正方体，不能把验证集指标当作混放现场的准确率。
