# 工创赛中期检查：YOLOv8n 六形状训练工程

状态：**代码已准备，尚未安装本工程的训练环境、正式拍摄或训练。** 本目录是同步到仓库的训练工程；用户原电脑 `F:\gcs_medium_check_YOLO_model` 保留开发副本。原电脑桌面 `tttest_yolo/yolo_first` 目前只有 1 张练习照片和 5 种可见形状，适合检查导出格式，不能用于六类模型训练；原图、标签和虚拟环境没有纳入仓库。

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

## 目前即可检查单图导出

在 PowerShell 中从仓库根目录进入本工程；将示例导出目录换成实际路径：

```powershell
Set-Location '.\software\midterm-yolo-model'
python .\prepare_dataset.py --source 'D:\your_export' --audit-only
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
   python .\prepare_dataset.py --source 'D:\your_export' --audit-only
   python .\prepare_dataset.py --source 'D:\your_export' --splits-csv '.\splits.csv' --out '.\dataset_v1'
   ```

   把示例 `D:\your_export` 改成实际 AnyLabeling 导出目录。结果含 `images/train|val|test`、`labels/train|val|test`、`data.yaml`、`dataset_summary.json`；无 test 时不生成 test。检查逐类框数及几张叠框图后再训练。

## RTX 5060 训练环境

用户原电脑已读到 RTX 5060 Laptop GPU（约 8 GiB，驱动 582.05）。系统默认 Python 3.14 的 PyTorch 是 `+cpu`，CUDA 不可用，不能用它训练。原电脑 `py -0p` 能列出 uv 管理的 Python 3.12.13，但 `py -3.12` **不能**选中它；在该电脑上使用已核实的解释器完整路径创建独立环境：

```powershell
# 以下命令在 software/midterm-yolo-model 目录执行
& 'C:\Users\Lenovo\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

然后从 [PyTorch 官方安装页](https://pytorch.org/get-started/locally/)选择 **Windows / Pip / Python / 支持 RTX 50 系列的 CUDA 12.8 或更新构建**，把官网给出的安装命令在这个 `.venv` 中执行；再运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

最后一行应显示 CUDA 为 `True` 且设备是 RTX 5060。`train.py` 还会执行一次真实 CUDA 矩阵运算，避免只看见显卡却使用了不兼容的 PyTorch 构建；失败时停止，不自动改用 CPU。[PyTorch 关于 Blackwell `sm_120` 支持的说明](https://discuss.pytorch.org/t/pytorch-support-for-sm-120-nvidia-geforce-rtx-5060/220941)

## 训练与新照片推理

有至少六类的 train/val 后，先短跑 3 轮检查链路，再正式训练：

```powershell
.\.venv\Scripts\python.exe .\train.py --data '.\dataset_v1\data.yaml' --smoke
.\.venv\Scripts\python.exe .\train.py --data '.\dataset_v1\data.yaml' --epochs 100 --imgsz 640 --batch 8
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
