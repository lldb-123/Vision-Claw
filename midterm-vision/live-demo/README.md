# 实时六形状、六颜色演示

`live_demo.py` 使用固定托盘相机和 [`../weights/best.pt`](../weights/best.pt) 检测六种形状；`color_vision.py` 在各检测框中央取像素，用 HSV 的亮度、饱和度与色相判定红、黑、白、深蓝、浅蓝、黄。窗口逐框显示颜色和形状，右侧显示两组计数、FPS。不会自动保存视频，也不修改数据集或模型。

先准备 Python 环境，需有 CUDA PyTorch、Ultralytics、OpenCV、Pillow 和 NumPy。在原电脑上可复用已有训练环境：

```powershell
Set-Location 'C:\Users\Lenovo\Documents\ChatGPT\工创赛-midterm-vision\midterm-vision\live-demo'
$env:VISION_PYTHON = 'F:\gcs_medium_check_YOLO_model\.venv\Scripts\python.exe'
.\start-demo.cmd
```

或直接运行 `& $env:VISION_PYTHON .\live_demo.py --check`，只读取一帧并推理，在终端打印每件物体的颜色、形状和形状置信度，不打开交互窗口。相机默认依次尝试 MSMF 索引 1、DirectShow 索引 0；可用 `--backend`、`--camera-index` 指定。正式窗口按 Q、Esc 或关闭窗口退出。

离线核对：625 张单物体照片用人工标注框取色，625/625 与文件名颜色一致；其中验证集 125 张单物体照片再用新模型的预测框取色，125/125 一致。另用新模型渲染了多物体照片预览。以上照片均来自原拍摄批次；**新权重及颜色模块尚未在实时相机窗口做现场验收**，混放和变化光照仍需实物检查。颜色判断不是 YOLO 的分类置信度，框旁不显示颜色置信度。
