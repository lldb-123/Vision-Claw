"""Train a six-shape YOLOv8n detector on CUDA GPU 0 (Windows)."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


CLASS_NAMES = ("cube", "sph", "cyl", "tpri", "cone", "tet")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def check_dataset(data_yaml: Path) -> tuple[Path, dict[str, dict[str, int]], str]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("缺少 PyYAML；请先按 README 安装训练环境") from exc

    if not data_yaml.is_file():
        raise ValueError(f"找不到 {data_yaml}")
    config = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("data.yaml 内容无效")
    raw_names = config.get("names")
    if isinstance(raw_names, dict):
        names = [raw_names.get(i, raw_names.get(str(i))) for i in range(6)]
    elif isinstance(raw_names, list):
        names = raw_names
    else:
        names = None
    if names != list(CLASS_NAMES):
        raise ValueError(f"类别必须按 ID 0–5 为 {list(CLASS_NAMES)}，实际为 {names}")

    root_value = config.get("path", str(data_yaml.parent))
    root = Path(root_value)
    if not root.is_absolute():
        root = data_yaml.parent / root
    root = root.resolve()
    statistics: dict[str, dict[str, int]] = {}
    digest = hashlib.sha256()
    for split in ("train", "val"):
        rel_dir = config.get(split)
        if not isinstance(rel_dir, str):
            raise ValueError(f"data.yaml 缺少 {split} 图片目录")
        image_dir = root / rel_dir
        if not image_dir.is_dir():
            raise ValueError(f"找不到 {split} 图片目录：{image_dir}")
        label_dir = root / "labels" / split
        images = sorted(p for p in image_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
        if not images:
            raise ValueError(f"{split} 没有图片")
        counts: Counter[str] = Counter()
        for image in images:
            label = label_dir / image.relative_to(image_dir).with_suffix(".txt")
            if not label.is_file():
                raise ValueError(f"{image} 缺少标签 {label}；空盘图也需空 .txt")
            contents = label.read_bytes()
            digest.update(str(label.relative_to(root)).encode("utf-8"))
            digest.update(contents)
            for line_no, raw in enumerate(contents.decode("utf-8-sig").splitlines(), 1):
                if not raw.strip():
                    continue
                parts = raw.split()
                if len(parts) != 5:
                    raise ValueError(f"{label}:{line_no} 不是五列 YOLO 检测标签")
                try:
                    class_id = int(parts[0])
                except ValueError as exc:
                    raise ValueError(f"{label}:{line_no} 类别 ID 无效") from exc
                if not 0 <= class_id < 6:
                    raise ValueError(f"{label}:{line_no} 类别 ID {class_id} 超出 0–5")
                counts[CLASS_NAMES[class_id]] += 1
        absent = [name for name in CLASS_NAMES if counts[name] == 0]
        if absent:
            raise ValueError(f"{split} 缺少 {absent}，暂不能训练六类模型")
        statistics[split] = {"images": len(images), **{name: counts[name] for name in CLASS_NAMES}}
    return root, statistics, digest.hexdigest()


def check_cuda() -> tuple[object, str]:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("缺少 PyTorch；请先在独立虚拟环境安装 CUDA 版") from exc
    if not torch.cuda.is_available():
        raise RuntimeError(
            f"CUDA 不可用；当前 torch={torch.__version__}, torch CUDA={torch.version.cuda}。"
            "本脚本不会自动退回 CPU。"
        )
    try:
        tensor = torch.randn((64, 64), device="cuda:0")
        _ = (tensor @ tensor).sum().item()
    except Exception as exc:
        raise RuntimeError("GPU 可见但 CUDA 运算失败；请检查 PyTorch 安装是否支持 RTX 5060") from exc
    device_name = torch.cuda.get_device_name(0)
    return torch, device_name


def main() -> None:
    parser = argparse.ArgumentParser(description="RTX 5060 上训练 YOLOv8n 六形状检测模型")
    parser.add_argument("--data", type=Path, required=True, help="prepare_dataset.py 生成的 data.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8, help="8 GB 显存先从 8 开始；显存不足改 4")
    parser.add_argument("--workers", type=int, default=0, help="Windows 起步用 0，稳定后可调高")
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--smoke", action="store_true", help="仅跑 3 轮确认训练链路")
    args = parser.parse_args()
    if min(args.epochs, args.imgsz, args.batch, args.patience) <= 0 or args.workers < 0:
        parser.error("epochs/imgsz/batch/patience 必须为正，workers 不能为负")

    data_yaml = args.data.resolve()
    _, dataset_stats, label_hash = check_dataset(data_yaml)
    print("数据集检查通过:", json.dumps(dataset_stats, ensure_ascii=False))
    torch, device_name = check_cuda()
    print(f"CUDA 可用：{device_name}；torch={torch.__version__}；CUDA runtime={torch.version.cuda}")
    try:
        import ultralytics
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("缺少 ultralytics；请先按 README 安装训练环境") from exc

    project = Path(__file__).resolve().parent / "runs"
    name = ("smoke" if args.smoke else "train") + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    epochs = 3 if args.smoke else args.epochs
    model = YOLO("yolov8n.pt")
    model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        patience=args.patience,
        device=0,
        project=str(project),
        name=name,
        exist_ok=False,
        seed=42,
        plots=True,
    )
    run_dir = Path(model.trainer.save_dir)
    best = run_dir / "weights" / "best.pt"
    if not best.is_file():
        raise RuntimeError(f"训练结束但未找到 {best}")
    shutil.copy2(data_yaml, run_dir / "data_used.yaml")
    metadata = {
        "model": "yolov8n.pt",
        "data": str(data_yaml),
        "class_names": list(CLASS_NAMES),
        "dataset_stats": dataset_stats,
        "labels_sha256": label_hash,
        "epochs_requested": epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "workers": args.workers,
        "patience": args.patience,
        "device": device_name,
        "python": sys.version,
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "ultralytics": ultralytics.__version__,
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("训练完成，权重:", best)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"无法开始训练：{exc}") from exc
