# 工创赛中期检查：YOLOv8n 六形状训练工程

状态：**用户已在原电脑训练出六形状初级模型；按最新要求，当前分支暂不提交照片。** [仓库首轮数据目录](../../datasets/midterm-yolo-v1/README.md)保留 236 张图片对应的 YOLO 标签与清单，训练/验证为 196/40，六类 ID 已重排。最佳模型副本和其余 462 张照片的待审核候选 JSON 见[第二批数据目录](../../datasets/midterm-yolo-prelabel-v1/README.md)；[自上次提交以来的进展](../../docs/midterm-yolo-progress-since-a24ea14-2026-11-11.md)记录了训练结果和局限。原电脑训练工程位于 `F:\gcs_medium_check_YOLO_model`，照片和虚拟环境均保留在原电脑。

## 类别约定

| ID | 标签 | 形状 |
| ---: | --- | --- |
| 0 | `cube` | 正方体 |
| 1 | `sph` | 球体 |
| 2 | `cyl` | 圆柱体 |
| 3 | `tpri` | 三棱柱 |
| 4 | `cone` | 圆锥体 |
| 5 | `tet` | 四面体 |

AnyLabeling 导出的 `classes.txt` **可能不按此顺序，且只包含拍到的类别**。`prepare_dataset.py` 根据类名重映射每一行标签 ID；不要把 `tttest_yolo/yolo_first/labels/image.txt` 原样配上上表的 `data.yaml` 训练。颜色在后续传统视觉模块处理，不进入这六个 YOLO 类。

## 固定相机拍正式照片

双击 `start-capture.cmd`。在预览窗口直接输入组别名（例如 `cube_black`），按 **Enter** 确定；之后每按一次 **空格**就保存一张。换组别按 **B**，输入新组别并按 Enter；退出按 **Q**。拍摄前确认预览显示托盘。组别名只用小写字母、数字、下划线和短横线。

新照片保存到本工程 `dataset_photos/<组别>/photo_000001.png`，每组独立编号。保存的是相机原帧，窗口上的提示文字不进入照片；程序不会强制设置曝光或白平衡。`dataset_photos/` 已排除 Git。原 `captures/` 是旧版脚本目录，不再作为新照片输入。

相机默认尝试当前外接托盘相机的 MSMF 索引 1、DirectShow 索引 0。若设备重插后索引变化，可在终端运行 `python .\capture.py --backend msmf --camera-index 1` 等指定后端和索引。正式采集尽量固定机位、光照和拨料件位置。

## 目前即可检查单图导出

在 PowerShell 中进入本工程：

```powershell
Set-Location .\software\midterm-yolo-model
& 'C:\Users\Lenovo\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe' .\prepare_dataset.py --source 'C:\Users\Lenovo\Desktop\tttest_yolo\yolo_first' --audit-only
```

这只读检查图片、标签、坐标和类名，不复制照片，也不启动训练。

## 正式数据准备

1. 在 AnyLabeling 标六种形状的矩形框。导出选 **YOLO (.txt) → Detection (Bounding Boxes)**，先不使用软件的随机 train/val/test 划分。每个正式导出目录应含 `classes.txt`、`images/`、`labels/`。空盘图如果没有导出 `.txt`，为它建立同名空 `.txt`；程序不会悄悄把漏标图片视作空盘。
2. 在工程外保存一份原始导出。为最终数据集制作 UTF-8 `splits.csv`，至少三列：

   ```csv
   image,scene_id,split
   photo_0001.jpg,scene_0001,train
   photo_0002.jpg,scene_0002,val
   photo_0003.jpg,scene_0003,test
   ```

   `image` 是相对于导出目录 `images/` 的文件名或子路径；`scene_id` 表示一次摆放，同一摆放的连拍、近重复和增强副本必须同组同划分。`split` 只能是 `train`、`val`、`test`。先保证 train/val 均含六类；最终盲测图在模型确定后新拍，再纳入 test。阶段性训练可先没有 test。
3. 先审计，再生成**新的**训练数据目录（不会覆盖已有目录）：

   ```powershell
   & 'C:\Users\Lenovo\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe' .\prepare_dataset.py --source 'D:\your_export' --audit-only
   & 'C:\Users\Lenovo\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe' .\prepare_dataset.py --source 'D:\your_export' --splits-csv '.\splits.csv' --out '.\dataset_v1'
   ```

   把示例 `D:\your_export` 改成实际 AnyLabeling 导出目录。结果含 `images/train|val|test`、`labels/train|val|test`、`data.yaml`、`dataset_summary.json`；无 test 时不生成 test。检查逐类框数及几张叠框图后再训练。

## RTX 5060 训练环境

本机 RTX 5060 Laptop GPU 约 8 GiB，驱动 582.05；系统默认 Python 3.14 的 PyTorch 为 CPU 版。本工程使用独立的 Python 3.12.13 虚拟环境。官方 [PyTorch 2.14.1 的 Windows CUDA 13.0 安装命令](https://pytorch.org/get-started/previous-versions/)适配当前驱动；[PyTorch 的 Blackwell 说明](https://pytorch.org/blog/pytorch-2-12-release-blog/)给出的 Windows 最低驱动为 580.88。

```powershell
Set-Location .\software\midterm-yolo-model
uv venv .venv --python 'C:\Users\Lenovo\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe'
uv pip install --python .\.venv\Scripts\python.exe torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cu130
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__,torch.version.cuda,torch.cuda.is_available(),torch.cuda.get_device_name(0))"
```

完成后须看到 CUDA `True` 和 RTX 5060，并运行一次 CUDA 张量运算检查；这不启动模型训练。本次用户要求环境就绪后仍暂停训练。
## 训练与新照片推理

有至少六类的 train/val 后，先短跑 3 轮检查链路，再正式训练：

```powershell
.\.venv\Scripts\python.exe .\train.py --data '..\..\datasets\midterm-yolo-v1\data.yaml' --smoke
.\.venv\Scripts\python.exe .\train.py --data '..\..\datasets\midterm-yolo-v1\data.yaml' --epochs 100 --imgsz 640 --batch 8
```

训练固定使用预训练 `yolov8n.pt` 和 CUDA GPU 0；Windows 默认 `workers=0`。首次训练若显存不足，改 `--batch 4`。输出位于 `runs/train_日期时间/weights/best.pt`，同目录保存训练配置、曲线、数据文件副本及环境/标签摘要。`--smoke` 的权重仅用于检查流程，不作为中期模型。

```powershell
.\.venv\Scripts\python.exe .\predict.py --weights '.\runs\train_日期时间\weights\best.pt' --source 'D:\new_photo.jpg'
```

新照片叠框结果保存到 `runs/predict_日期时间/`。这只输出六形状；黑、白、红、黄、深蓝、浅蓝的传统视觉判色仍是独立模块。

## 当前需要现场确认的事项

- 正式照片是否始终由同一固定机位、相机设置和灯光拍摄；如改变，应按批次记录。
- 六形状在正式训练集和验证集是否都有可辨实例；最终还需独立新摆放照片做测试。
- 每张图的拍摄/摆放组 `scene_id` 如何记录，以保证近重复图不跨 train、val、test。拿到首批照片后即可按实际文件名生成 `splits.csv`。

目前无需先给出所有拍摄细节才能使用代码审计单图导出；训练需要数据和 GPU 环境就绪。
