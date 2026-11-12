"""Standalone live shape detection demo for the fixed tray camera."""

from __future__ import annotations

import argparse
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
SHAPES = {
    "cube": ("正方体", (37, 105, 191)),
    "sph": ("球体", (13, 139, 139)),
    "cyl": ("圆柱体", (168, 100, 20)),
    "tpri": ("三棱柱", (135, 72, 165)),
    "cone": ("圆锥体", (191, 76, 64)),
    "tet": ("四面体", (84, 115, 61)),
}


@lru_cache(maxsize=8)
def load_font(size: int):
    for path in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def open_camera(backend: str, index: int | None):
    if backend == "auto":
        choices = [(cv2.CAP_MSMF, 1 if index is None else index),
                   (cv2.CAP_DSHOW, 0 if index is None else index)]
    else:
        api = cv2.CAP_MSMF if backend == "msmf" else cv2.CAP_DSHOW
        choices = [(api, index if index is not None else (1 if backend == "msmf" else 0))]
    for api, camera_index in choices:
        cap = cv2.VideoCapture(camera_index, api)
        if cap.isOpened():
            for _ in range(12):
                ok, frame = cap.read()
                if ok and frame is not None and frame.size:
                    return cap, frame, camera_index
                time.sleep(0.1)
        cap.release()
    raise RuntimeError("无法读取相机。请先关闭其他占用相机的软件并检查连接。")


def render(frame, result, fps: float, confidence: float):
    height, width = frame.shape[:2]
    panel_width = 300
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    canvas = Image.new("RGB", (width + panel_width, height), (242, 246, 250))
    canvas.paste(image, (0, 0))
    draw = ImageDraw.Draw(canvas)
    font = load_font(22)
    small = load_font(18)
    title = load_font(29)
    counts: Counter[str] = Counter()
    if result.boxes is not None:
        for box in result.boxes:
            name = str(result.names[int(box.cls.item())])
            if name not in SHAPES:
                continue
            chinese, color = SHAPES[name]
            score = float(box.conf.item())
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            x1, x2 = max(0, x1), min(width - 1, x2)
            y1, y2 = max(0, y1), min(height - 1, y2)
            draw.rectangle((x1, y1, x2, y2), outline=color, width=4)
            label = f"{chinese} {score:.2f}"
            bounds = draw.textbbox((0, 0), label, font=font)
            label_width = bounds[2] - bounds[0] + 16
            label_height = bounds[3] - bounds[1] + 10
            top = max(0, y1 - label_height)
            right = min(width, x1 + label_width)
            draw.rectangle((x1, top, right, top + label_height), fill=color)
            draw.text((x1 + 8, top + 3 - bounds[1]), label, font=font, fill="white")
            counts[name] += 1

    left = width + 24
    draw.text((left, 26), "实时形状识别", font=title, fill=(25, 44, 65))
    draw.text((left, 78), f"当前识别：{sum(counts.values())} 件", font=font, fill=(25, 44, 65))
    draw.line((left, 122, width + panel_width - 24, 122), fill=(205, 216, 225), width=2)
    for i, (name, (chinese, color)) in enumerate(SHAPES.items()):
        y = 145 + i * 50
        draw.ellipse((left, y + 7, left + 15, y + 22), fill=color)
        draw.text((left + 27, y), chinese, font=font, fill=(35, 53, 70))
        draw.text((width + panel_width - 70, y), str(counts[name]), font=font, fill=(35, 53, 70))
    draw.line((left, 467, width + panel_width - 24, 467), fill=(205, 216, 225), width=2)
    draw.text((left, 491), f"画面速度  {fps:.1f} FPS", font=small, fill=(70, 89, 105))
    draw.text((left, 527), f"置信度阈值  {confidence:.2f}", font=small, fill=(70, 89, 105))
    draw.text((left, 563), "按 Q 或 Esc 退出", font=small, fill=(70, 89, 105))
    draw.text((left, 600), "当前只识别形状", font=small, fill=(70, 89, 105))
    return cv2.cvtColor(np.asarray(canvas), cv2.COLOR_RGB2BGR), counts


def main():
    parser = argparse.ArgumentParser(description="Live six-shape camera demo")
    parser.add_argument("--weights", type=Path, default=ROOT.parent / "weights" / "best.pt")
    parser.add_argument("--backend", choices=("auto", "msmf", "dshow"), default="auto")
    parser.add_argument("--camera-index", type=int)
    parser.add_argument("--conf", type=float, default=0.4)
    parser.add_argument("--check", action="store_true", help="Read and infer one frame without opening a window")
    args = parser.parse_args()
    if not args.weights.is_file():
        raise RuntimeError(f"找不到模型文件：{args.weights}")
    if not 0 < args.conf < 1:
        raise RuntimeError("置信度阈值须在 0 和 1 之间。")
    if not torch.cuda.is_available():
        raise RuntimeError("未检测到可用 CUDA，请检查显卡驱动和演示环境。")
    torch.set_num_threads(4)
    cv2.setNumThreads(2)
    model = YOLO(str(args.weights))
    cap, frame, camera_index = open_camera(args.backend, args.camera_index)
    print(f"Camera: {cap.getBackendName()} index={camera_index} {frame.shape[1]}x{frame.shape[0]}")
    try:
        if args.check:
            result = model.predict(frame, device=0, imgsz=640, conf=args.conf,
                                   agnostic_nms=True, verbose=False)[0]
            render(frame, result, 0.0, args.conf)
            print(f"CUDA: {torch.cuda.get_device_name(0)}; detected: {len(result.boxes)}")
            return
        title = "Vision-Claw Live Demo"
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, 1400, 720)
        cv2.imshow(title, frame)
        cv2.waitKey(1)
        last_time = time.monotonic()
        fps = 0.0
        failures = 0
        while True:
            ok, candidate = cap.read()
            if not ok or candidate is None or not candidate.size:
                failures += 1
                if failures >= 30:
                    raise RuntimeError("相机连续读帧失败，请关闭其他相机软件后重试。")
                time.sleep(0.05)
                continue
            frame = candidate
            failures = 0
            result = model.predict(frame, device=0, imgsz=640, conf=args.conf,
                                   agnostic_nms=True, verbose=False)[0]
            now = time.monotonic()
            instant = 1.0 / max(now - last_time, 0.001)
            fps = instant if not fps else 0.85 * fps + 0.15 * instant
            last_time = now
            view, _ = render(frame, result, fps, args.conf)
            cv2.imshow(title, view)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            try:
                if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
