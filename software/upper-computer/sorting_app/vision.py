"""基础视觉与演示场景；真实三维/表面识别通过 Detector 接口替换。"""
from dataclasses import dataclass
from pathlib import Path
import json
import cv2
import numpy as np

COLOR_NAMES = {"red": "红色", "green": "绿色", "blue": "蓝色", "yellow": "黄色", "unknown": "未知颜色"}
SHAPE_NAMES = {"circle_outline": "圆形轮廓", "square_outline": "方形轮廓", "triangle_outline": "三角轮廓", "polygon_outline": "多边轮廓"}

@dataclass
class Detection:
    center: tuple[float, float]
    bbox: tuple[int, int, int, int]
    color: str
    shape: str
    surface: str = "unknown"
    surface_value: str = ""
    shape_verified: bool = False

    @property
    def label(self):
        return COLOR_NAMES.get(self.color, self.color) + " " + SHAPE_NAMES.get(self.shape, self.shape)

    def category(self, demo=False):
        if not demo and (not self.shape_verified or self.surface == "unknown" or self.color == "unknown"):
            raise ValueError("当前识别器只提供颜色和二维轮廓；请接入立体形状与表面信息识别器")
        return (self.color, self.shape) if demo else (self.color, self.shape, self.surface, self.surface_value)

class BasicDetector:
    """检测饱和的彩色物体。没有将圆形轮廓直接当作圆柱或圆锥。"""
    def __init__(self, config=None):
        self.config = config or {}

    def detect(self, image: np.ndarray) -> list[Detection]:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([0, self.config.get("min_saturation", 75), self.config.get("min_value", 55)]), np.array([179, 255, 255]))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.config.get("min_area", 350):
                continue
            perimeter = cv2.arcLength(contour, True)
            polygon = cv2.approxPolyDP(contour, 0.035 * perimeter, True)
            vertices = len(polygon)
            x, y, w, h = cv2.boundingRect(contour)
            shape = "triangle_outline" if vertices == 3 else "square_outline" if vertices == 4 and 0.8 < w / h < 1.25 else "circle_outline" if vertices >= 6 and 4 * np.pi * area / max(perimeter**2, 1) > 0.75 else "polygon_outline"
            region = np.zeros(mask.shape, np.uint8)
            cv2.drawContours(region, [contour], -1, 255, -1)
            hues = hsv[:, :, 0][(region > 0) & (mask > 0)]
            fractions = {"red": np.mean((hues <= 10) | (hues >= 170)), "yellow": np.mean((hues > 10) & (hues <= 35)), "green": np.mean((hues > 35) & (hues <= 85)), "blue": np.mean((hues > 85) & (hues <= 135))}
            color = max(fractions, key=fractions.get)
            if fractions[color] < 0.6:
                color = "unknown"
            moments = cv2.moments(contour)
            center = (moments["m10"] / moments["m00"], moments["m01"] / moments["m00"])
            detections.append(Detection(center, (x, y, w, h), color, shape))
        return sorted(detections, key=lambda d: (-d.center[1], d.center[0]))

class CoordinateMapper:
    def __init__(self, image_points, machine_points):
        image_points = np.asarray(image_points, dtype=np.float32)
        machine_points = np.asarray(machine_points, dtype=np.float32)
        if image_points.shape != (4, 2) or machine_points.shape != (4, 2):
            raise ValueError("需要四个对应点")
        if abs(cv2.contourArea(image_points)) < 100:
            raise ValueError("标定点退化，请按托盘四角依次选择")
        self.matrix = cv2.getPerspectiveTransform(image_points, machine_points)
        self.image_points, self.machine_points = image_points, machine_points

    def convert(self, center):
        x, y = cv2.perspectiveTransform(np.array([[center]], dtype=np.float32), self.matrix)[0, 0]
        return float(x), float(y)

    def save(self, path, image_size):
        Path(path).write_text(json.dumps({"image_points": self.image_points.tolist(), "machine_points": self.machine_points.tolist(), "image_size": list(image_size)}, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path, image_size):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data["image_size"] != list(image_size):
            raise ValueError("当前图片分辨率与标定文件不同，请重新标定")
        return cls(data["image_points"], data["machine_points"])

class DemoSource:
    is_demo = True
    def __init__(self):
        self.objects = []
        kinds = [(c, s) for c in ("red", "green", "blue") for s in ("circle", "square")] * 2
        order = np.random.default_rng(12).permutation(12)
        for i, k in enumerate(order):
            color, shape = kinds[k]
            self.objects.append({"x": 125 + (i % 4) * 165, "y": 125 + (i // 4) * 175, "color": color, "shape": shape})
        self.mapper = CoordinateMapper([[40, 40], [720, 40], [720, 560], [40, 560]], [[0, 260], [260, 260], [260, 0], [0, 0]])

    def read(self):
        image = np.full((600, 760, 3), (228, 233, 238), np.uint8)
        cv2.rectangle(image, (40, 40), (720, 560), (252, 252, 252), -1)
        cv2.rectangle(image, (40, 40), (720, 560), (180, 180, 180), 2)
        for obj in self.objects:
            x, y = obj["x"], obj["y"]
            color = {"red": (60, 65, 220), "green": (80, 165, 45), "blue": (210, 110, 35)}[obj["color"]]
            if obj["shape"] == "circle":
                cv2.circle(image, (x, y), 29, color, -1, cv2.LINE_AA)
            else:
                cv2.rectangle(image, (x-28, y-28), (x+28, y+28), color, -1)
        return image

    def remove(self, detection):
        obj = min(self.objects, key=lambda o: (o["x"]-detection.center[0])**2+(o["y"]-detection.center[1])**2)
        self.objects.remove(obj)

    def close(self):
        pass

class ImageSource:
    is_demo = False
    def __init__(self, path):
        self.image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if self.image is None:
            raise ValueError("无法读取图片")

    def read(self):
        return self.image.copy()

    def close(self):
        pass

class CameraSource:
    is_demo = False
    def __init__(self, index=0, width=1280, height=720):
        self.capture = cv2.VideoCapture(index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.capture.isOpened():
            self.capture.release()
            raise ValueError("无法打开相机，请检查 configs/default.json 的相机编号")

    def read(self):
        for _ in range(3):
            ok, frame = self.capture.read()
        if not ok:
            raise ValueError("相机没有返回图像")
        return frame

    def close(self):
        self.capture.release()

def annotate(image, detections):
    result = image.copy()
    for i, detection in enumerate(detections, 1):
        x, y, w, h = detection.bbox
        cv2.rectangle(result, (x-5, y-5), (x+w+5, y+h+5), (70, 65, 35), 2)
        cv2.putText(result, f"{i} {detection.color}", (x-4, max(y-10, 16)), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (55, 50, 30), 1, cv2.LINE_AA)
        cv2.drawMarker(result, tuple(map(round, detection.center)), (255, 255, 255), cv2.MARKER_CROSS, 12, 1)
    return result
