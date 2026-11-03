"""任务调度。识别器输出物体，STM32 执行路径，界面负责展示。"""
from pathlib import Path
import json
import time
from datetime import datetime
import cv2
from .client import DeviceError, TaskCancelled
from .vision import ImageSource, CoordinateMapper, annotate

ROOT = Path(__file__).resolve().parents[1]

def load_config():
    return json.loads((ROOT / "configs/default.json").read_text(encoding="utf-8"))

class SortEngine:
    def __init__(self, source, detector, client, config=None, emit=None):
        self.source, self.detector, self.client = source, detector, client
        self.config = config or load_config()
        self.emit = emit or (lambda event, value: None)
        self.boxes = {}
        self.counts = [0] * self.config["sorting"]["bins"]
        self.records = []
        self.started_at = None
        self.log_path = None

    def snapshot(self):
        image = self.source.read()
        detections = self.detector.detect(image)
        self.emit("frame", {"image": annotate(image, detections), "raw": image, "detections": detections})
        return image, detections

    def record(self, data):
        if self.log_path is None:
            log_dir = ROOT / "logs"
            log_dir.mkdir(exist_ok=True)
            self.log_path = log_dir / f"round_{datetime.now():%Y%m%d_%H%M%S_%f}.jsonl"
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(data, ensure_ascii=False) + "\n")

    def run(self, cancel, one=False):
        if isinstance(self.source, ImageSource):
            raise DeviceError("静态图片用于分析；分拣需要相机重新拍摄物体位置")
        if self.client is None:
            raise DeviceError("请先连接 STM32")
        if self.source.is_demo and not self.client.homed:
            self.emit("state", "模拟设备回原点")
            self.client.execute("HOME", cancel=cancel)
        if not self.client.homed:
            raise DeviceError("请先回原点")
        if self.started_at is None:
            self.started_at = time.monotonic()
        while not cancel.is_set():
            elapsed = time.monotonic() - self.started_at
            remaining = self.config["sorting"]["round_seconds"] - elapsed
            if remaining <= 0:
                self.emit("state", "本轮时间已到")
                return
            image, detections = self.snapshot()
            if not detections:
                self.emit("state", "演示处理完毕" if self.source.is_demo else "当前画面未检测到可识别目标")
                return
            # 此排序仅决定候选顺序；实际拨板路径由下位机结合机构实现。
            target = detections[0]
            key = target.category(self.source.is_demo)
            mapper = self.source.mapper if self.source.is_demo else CoordinateMapper.load(ROOT / "configs/calibration.json", (image.shape[1], image.shape[0]))
            x_mm, y_mm = mapper.convert(target.center)
            if key not in self.boxes:
                if len(self.boxes) >= len(self.counts):
                    raise DeviceError("储物盒已全部分配，新类别没有空盒")
                self.boxes[key] = len(self.boxes) + 1
            box = self.boxes[key]
            if self.counts[box-1] >= self.config["sorting"]["capacity_per_bin"]:
                raise DeviceError(f"{box} 号盒已达到配置容量")
            self.emit("state", f"{target.label} → {box} 号盒")
            old_timeout = self.client.config.get("motion_timeout", 12.0)
            self.client.config["motion_timeout"] = min(old_timeout, remaining)
            try:
                result = self.client.execute("SORT", round(x_mm * 100), round(y_mm * 100), box, cancel=cancel)
            finally:
                self.client.config["motion_timeout"] = old_timeout
            if result.args != ("SORT", "ENTRY_VERIFIED"):
                raise DeviceError("动作结束，但入盒尚未验证；请核实后再继续")
            self.counts[box-1] += 1
            record = {"index": len(self.records)+1, "label": target.label, "category": list(key), "box": box,
                      "x_mm": round(x_mm, 2), "y_mm": round(y_mm, 2), "task_id": result.seq,
                      "session": result.session, "simulated": self.source.is_demo,
                      "elapsed_seconds": round(time.monotonic()-self.started_at, 2)}
            self.records.append(record)
            self.record(record)
            x, y, w, h = target.bbox
            self.emit("sorted", {"record": record, "counts": self.counts.copy(), "thumbnail": image[y:y+h, x:x+w].copy()})
            if self.source.is_demo:
                self.source.remove(target)
            if one:
                self.snapshot()
                self.emit("state", "单件处理完成")
                return
        raise TaskCancelled("已停止")
