"""Live shape and color detection demo for the fixed tray camera."""

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

from color_vision import COLOR_NAMES, COLOR_RGB, classify_color


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
    panel_width = 315
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    canvas = Image.new("RGB", (width + panel_width, height), (242, 246, 250))
    canvas.paste(image, (0, 0))
    draw = ImageDraw.Draw(canvas)
    font = load_font(19)
    small = load_font(18)
    title = load_font(29)
    shape_counts: Counter[str] = Counter()
    color_counts: Counter[str] = Counter()
    detections: list[str] = []
    used_labels: list[tuple[int, int, int, int]] = []
    if result.boxes is not None:
        for box in result.boxes:
            name = str(result.names[int(box.cls.item())])
            if name not in SHAPES:
                continue
            chinese, _ = SHAPES[name]
            score = float(box.conf.item())
            coords = box.xyxy[0].tolist()
            color_name = classify_color(frame, tuple(coords))
            color = COLOR_RGB[color_name]
            x1, y1, x2, y2 = [int(v) for v in coords]
            x1, x2 = max(0, x1), min(width - 1, x2)
            y1, y2 = max(0, y1), min(height - 1, y2)
            if color_name == "white":
                draw.rectangle((x1 - 1, y1 - 1, x2 + 1, y2 + 1), outline=(65, 75, 85), width=6)
            draw.rectangle((x1, y1, x2, y2), outline=color, width=4)
            label = f"{COLOR_NAMES[color_name]} {chinese}"
            bounds = draw.textbbox((0, 0), label, font=font)
            label_width = bounds[2] - bounds[0] + 16
            label_height = bounds[3] - bounds[1] + 10
            label_x = min(x1, max(0, width - label_width))
            nearby = (y1 - label_height, y2 + 2, y1 + 2, y2 - label_height)
            free_rows = sorted(range(0, max(1, height - label_height + 1), label_height + 2),
                               key=lambda row: min(abs(row - y1), abs(row - y2)))
            candidates = (*nearby, *free_rows)
            chosen = None
            for candidate_y in candidates:
                if not 0 <= candidate_y <= height - label_height:
                    continue
                rectangle = (label_x, candidate_y, label_x + label_width,
                             candidate_y + label_height)
                if all(rectangle[2] <= old[0] or old[2] <= rectangle[0] or
                       rectangle[3] <= old[1] or old[3] <= rectangle[1]
                       for old in used_labels):
                    chosen = rectangle
                    break
            if chosen is None:
                chosen = (label_x, max(0, min(height - label_height, y1)),
                          label_x + label_width, max(label_height, min(height, y1 + label_height)))
            used_labels.append(chosen)
            draw.rectangle(chosen, fill=color)
            text_color = (25, 35, 45) if color_name in ("white", "yellow", "blue") else "white"
            draw.text((chosen[0] + 8, chosen[1] + 3 - bounds[1]), label,
                      font=font, fill=text_color)
            shape_counts[name] += 1
            color_counts[color_name] += 1
            detections.append(f"{label} {score:.2f}")

    left = width + 24
    right = width + panel_width - 24
    draw.text((left, 22), "实时颜色与形状识别", font=title, fill=(25, 44, 65))
    draw.text((left, 67), f"当前识别：{sum(shape_counts.values())} 件", font=font, fill=(25, 44, 65))
    draw.line((left, 105, right, 105), fill=(205, 216, 225), width=2)
    draw.text((left, 112), "颜色", font=small, fill=(70, 89, 105))
    for i, (name, chinese) in enumerate(COLOR_NAMES.items()):
        y = 140 + i * 32
        swatch = COLOR_RGB[name]
        draw.ellipse((left, y + 4, left + 18, y + 22), fill=swatch, outline=(90, 100, 110))
        draw.text((left + 29, y), chinese, font=small, fill=(35, 53, 70))
        draw.text((right - 24, y), str(color_counts[name]), font=small, fill=(35, 53, 70))
    draw.line((left, 340, right, 340), fill=(205, 216, 225), width=2)
    draw.text((left, 347), "形状", font=small, fill=(70, 89, 105))
    for i, (name, (chinese, swatch)) in enumerate(SHAPES.items()):
        y = 375 + i * 32
        draw.ellipse((left, y + 4, left + 18, y + 22), fill=swatch)
        draw.text((left + 29, y), chinese, font=small, fill=(35, 53, 70))
        draw.text((right - 24, y), str(shape_counts[name]), font=small, fill=(35, 53, 70))
    draw.line((left, 575, right, 575), fill=(205, 216, 225), width=2)
    draw.text((left, 587), f"画面速度  {fps:.1f} FPS", font=small, fill=(70, 89, 105))
    draw.text((left, 619), f"置信度阈值  {confidence:.2f}", font=small, fill=(70, 89, 105))
    draw.text((left, 651), "按 Q 或 Esc 退出", font=small, fill=(70, 89, 105))
    return cv2.cvtColor(np.asarray(canvas), cv2.COLOR_RGB2BGR), detections


def main():
    parser = argparse.ArgumentParser(description="Live six-shape, six-color camera demo")
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
            _, detections = render(frame, result, 0.0, args.conf)
            print(f"CUDA: {torch.cuda.get_device_name(0)}; detected: {len(detections)}")
            for detection in detections:
                print(detection)
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
