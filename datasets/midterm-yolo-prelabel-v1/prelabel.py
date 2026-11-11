"""Generate unreviewed AnyLabeling rectangles in a new folder, without changing originals."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

import torch
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
NAMES = ["cube", "sph", "cyl", "tpri", "cone", "tet"]
CONFIDENCE = 0.25


def main() -> None:
    source_images = ROOT / "images"
    weights = ROOT / "model" / "best.pt"
    output = ROOT / "prelabel_v1"
    if output.exists():
        raise SystemExit(f"Output exists; no existing labels overwritten: {output}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA GPU unavailable; prelabeling stopped.")
    with (ROOT / "manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by_name = {row["image"]: row for row in rows}
    if len(by_name) != len(rows) or not all((source_images / name).is_file() for name in by_name):
        raise SystemExit("Manifest has duplicate or missing images; stopped before writing.")
    model = YOLO(str(weights))
    actual_names = [model.names[i] for i in range(6)]
    if actual_names != NAMES:
        raise SystemExit(f"Model class order mismatch: {actual_names}")
    torch.set_num_threads(4)
    target_images = output / "images"
    target_images.mkdir(parents=True)
    for row in rows:
        shutil.copy2(source_images / row["image"], target_images / row["image"])

    # The empty-tray group is kept for human review; do not invent background labels.
    infer_paths = [str(target_images / row["image"]) for row in rows if row["kind"] != "empty"]
    predictions = {}
    results = model.predict(source=infer_paths, stream=True, device=0, imgsz=640,
                            batch=8, rect=True, conf=CONFIDENCE, verbose=False)
    for index, result in enumerate(results, 1):
        name = Path(result.path).name
        if name not in by_name or name in predictions:
            raise RuntimeError(f"Unexpected or duplicate inference result: {name}")
        height, width = result.orig_shape
        shapes = []
        labels = []
        for box in result.boxes:
            cls = int(box.cls.item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            x1, x2 = max(0.0, min(width, x1)), max(0.0, min(width, x2))
            y1, y2 = max(0.0, min(height, y1)), max(0.0, min(height, y2))
            if x2 <= x1 or y2 <= y1:
                continue
            shapes.append({"label": NAMES[cls], "text": "", "points": [[round(x1, 2), round(y1, 2)],
                           [round(x2, 2), round(y2, 2)]], "group_id": None,
                           "shape_type": "rectangle", "flags": {}})
            labels.append(f"{NAMES[cls]}:{float(box.conf.item()):.2f}")
        if shapes:
            document = {"version": "0.4.43", "flags": {}, "shapes": shapes,
                        "imagePath": name, "imageData": None,
                        "imageHeight": height, "imageWidth": width}
            (target_images / f"{Path(name).stem}.json").write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        predictions[name] = {"count": len(shapes), "labels": "; ".join(labels)}
        if index % 50 == 0:
            print(f"Prelabeled {index}/{len(infer_paths)} images", flush=True)

    if len(predictions) != len(infer_paths):
        raise RuntimeError(f"Missing inference results: {len(predictions)}/{len(infer_paths)}")
    review_rows = []
    for row in rows:
        p = predictions.get(row["image"], {"count": 0, "labels": ""})
        review_rows.append({**row, "predicted_boxes": p["count"], "predictions": p["labels"],
                            "review_status": "unreviewed"})
    with (output / "review_queue.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = list(rows[0]) + ["predicted_boxes", "predictions", "review_status"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review_rows)
    summary = {"created": datetime.now().astimezone().isoformat(timespec="seconds"),
               "total_images": len(rows), "inferred_images": len(predictions),
               "known_empty_skipped": sum(row["kind"] == "empty" for row in rows),
               "images_with_boxes": sum(p["count"] > 0 for p in predictions.values()),
               "no_boxes_needing_review": sum(p["count"] == 0 for p in predictions.values()),
               "boxes_by_class": dict(Counter(s.split(":")[0] for p in predictions.values()
                                              for s in p["labels"].split("; ") if s)),
               "confidence_threshold": CONFIDENCE, "imgsz": 640,
               "model_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
               "reviewed": False}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# 自动预标注：全部待人工复核\n\n"
        "在 AnyLabeling 打开 `images/`。模型生成的 JSON 只是候选框，逐张检查类别、漏框、误框和框的位置，修改后保存。"
        "`review_queue.csv` 初始状态均为 unreviewed；无 JSON 的照片也必须检查，不能自动当作空盘。"
        "已知空盘组未运行预测，需人工确认。保留独立新摆放照片做测试。\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Open in AnyLabeling: {target_images}")


if __name__ == "__main__":
    main()
