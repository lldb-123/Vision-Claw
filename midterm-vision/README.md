# 中期检查六形状模型

这里是中期检查使用的完整 YOLOv8n 资料。它只检测六种**形状**；颜色识别仍是独立模块。原电脑 `F:\gcs_medium_check_YOLO_model` 保留原件，本目录是经过哈希核对的仓库副本。

## 内容

| 路径 | 内容 |
| --- | --- |
| [`dataset/`](dataset/README.md) | 唯一一份 698 张 PNG、668 份可编辑 AnyLabeling JSON、698 份 YOLO 标签、清单和划分。30 张空盘的标签为空文件。 |
| [`weights/best.pt`](weights/best.pt) | 本轮训练的最佳六形状权重，来自第 79 轮。 |
| [`weights/yolov8n.pt`](weights/yolov8n.pt) | 当时训练使用的基础预训练权重，供离线复现。 |
| [`results/metrics.json`](results/metrics.json) | 训练参数、六类验证指标和适用范围。曲线与少量示例图也在 `results/`。 |
| `train.py`、`start-train-698.cmd` | 数据审计与 GPU 训练；当前仓库数据使用图片清单，无需复制 train/val 图片。 |
| `create_splits_698.py`、`prepare_dataset.py` | 场景组划分的可复现脚本，以及其他 AnyLabeling 导出的审计/整理脚本。 |
| `predict.py`、`capture.py`、`start-capture.cmd` | 单图推理和固定相机拍摄。 |
| [`live-demo/`](live-demo/README.md) | 独立实时窗口，默认使用本目录的最佳权重。 |

六类 ID 顺序固定为 `0 cube、1 sph、2 cyl、3 tpri、4 cone、5 tet`。数据按近重复场景组、固定种子 42 划为训练 558 张和验证 140 张；没有独立测试集。

## 已验证的结果

`best.pt` 在同批次 140 张验证图、168 个目标上的重新验证结果：Precision **0.975**、Recall **0.974**、mAP50 **0.995**、mAP50-95 **0.970**。逐类数据在 [`results/metrics.json`](results/metrics.json)；四面体 Precision 约 0.882，验证预览里仍有黑色圆锥误判为四面体。训练和验证来自同一拍摄批次，这些分数**不是新场景实物准确率**。后续需要用新摆放、混放和变化光照的照片独立测试。

## 获取与运行

照片和 `.pt` 使用 Git LFS；克隆后先执行 `git lfs pull`。仓库不包含虚拟环境、训练运行目录或机器标定。原电脑现有 Python 环境可直接用于只读验证和推理；以下命令在本目录执行：

```powershell
$py = 'F:\gcs_medium_check_YOLO_model\.venv\Scripts\python.exe'
& $py -c "from pathlib import Path; from train import check_dataset; print(check_dataset(Path('dataset/data.yaml'))[1])"
& $py .\predict.py --weights .\weights\best.pt --source 'D:\new_photo.jpg'
```

若需要**重新训练**，先在本目录准备包含 CUDA PyTorch 和 `requirements.txt` 依赖的 `.venv`，或指定已有环境，再运行：

```powershell
$env:VISION_PYTHON = 'F:\gcs_medium_check_YOLO_model\.venv\Scripts\python.exe'
.\start-train-698.cmd
```

启动脚本设置 Ultralytics 离线模式，使用仓库内的基础权重和 `dataset/data.yaml`，默认最多 100 轮、图像尺寸 640、batch 8、workers 0。运行输出进入被 Git 忽略的 `runs/`；查看已有模型无需重新训练。

原分支中的首轮 236 图标签、旧预标注 JSON/队列和首轮模型是阶段性资料，已从当前目录树移除。需要追溯可查看整理前的 Git 提交 `70fa3fb`；它们不应与本目录的正式标签和权重混用。
