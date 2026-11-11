"""Run a trained six-shape model on a new local image."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from train import check_cuda


def main() -> None:
    parser = argparse.ArgumentParser(description="用 best.pt 对新照片推理并保存叠框图")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    if not args.weights.is_file() or not args.source.exists():
        parser.error("请提供存在的 --weights 和 --source 路径")
    if not 0 < args.conf < 1:
        parser.error("--conf 应在 0 和 1 之间")
    check_cuda()
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("缺少 ultralytics，请先按 README 安装训练环境") from exc
    output_root = Path(__file__).resolve().parent / "runs"
    name = "predict_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    model = YOLO(str(args.weights.resolve()))
    model.predict(
        source=str(args.source.resolve()),
        device=0,
        imgsz=args.imgsz,
        conf=args.conf,
        save=True,
        project=str(output_root),
        name=name,
        exist_ok=False,
    )
    print("叠框图保存在:", output_root / name)


if __name__ == "__main__":
    main()
