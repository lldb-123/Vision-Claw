"""Classify the six competition colors inside a YOLO detection box."""

from __future__ import annotations

import cv2
import numpy as np


COLOR_NAMES = {
    "red": "红色",
    "black": "黑色",
    "white": "白色",
    "navyblue": "深蓝色",
    "blue": "浅蓝色",
    "yellow": "黄色",
}

COLOR_RGB = {
    "red": (205, 49, 64),
    "black": (42, 48, 58),
    "white": (220, 223, 228),
    "navyblue": (32, 64, 166),
    "blue": (35, 155, 222),
    "yellow": (235, 186, 38),
}


def classify_color(frame: np.ndarray, xyxy: tuple[float, float, float, float]) -> str:
    """Use the center of a box, avoiding tray pixels near its border.

    The thresholds were checked against the 625 single-object photos from the
    current fixed camera. A small dark or colorful object can win over a white
    tray background; blue shades are separated by hue after that masking.
    """
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = xyxy
    x1, x2 = sorted((max(0, min(width, x1)), max(0, min(width, x2))))
    y1, y2 = sorted((max(0, min(height, y1)), max(0, min(height, y2))))
    box_w, box_h = x2 - x1, y2 - y1
    if box_w < 4 or box_h < 4:
        return "white"

    left = max(0, int(x1 + box_w * 0.18))
    right = min(width, int(x2 - box_w * 0.18))
    top = max(0, int(y1 + box_h * 0.18))
    bottom = min(height, int(y2 - box_h * 0.18))
    crop = frame[top:bottom, left:right]
    if crop.size == 0:
        return "white"
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    yy, xx = np.ogrid[-1:1:complex(0, crop.shape[0]), -1:1:complex(0, crop.shape[1])]
    center = (xx * xx + yy * yy) <= 1.0
    pixels = hsv[center]
    h, s, v = pixels[:, 0], pixels[:, 1], pixels[:, 2]

    dark = v < 75
    chromatic = (s >= 65) & (v >= 70)
    if dark.mean() >= 0.35:
        return "black"
    if chromatic.mean() < 0.16:
        return "white"

    hue = float(np.median(h[chromatic]))
    if hue <= 10 or hue >= 160:
        return "red"
    if 17 <= hue <= 45:
        return "yellow"
    if 88 <= hue <= 125:
        return "blue" if hue < 109 else "navyblue"

    # Very unusual lighting: choose the nearest of the six observed prototypes.
    value = float(np.median(v))
    saturation = float(np.median(s))
    if value < 85:
        return "black"
    if saturation < 55:
        return "white"
    anchors = {"red": 176, "yellow": 27, "blue": 103, "navyblue": 114}
    return min(anchors, key=lambda name: min(abs(hue - anchors[name]), 180 - abs(hue - anchors[name])))
