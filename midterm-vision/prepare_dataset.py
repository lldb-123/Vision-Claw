"""Validate an AnyLabeling YOLO export and build a fixed six-class dataset."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path


CLASS_NAMES = ("cube", "sph", "cyl", "tpri", "cone", "tet")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLITS = ("train", "val", "test")


def read_classes(source: Path) -> list[str]:
    path = source / "classes.txt"
    if not path.is_file():
        raise ValueError(f"缺少 {path}")
    names = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not names or len(names) != len(set(names)):
        raise ValueError("classes.txt 为空或有重复类名")
    unknown = sorted(set(names) - set(CLASS_NAMES))
    if unknown:
        raise ValueError(f"出现未约定的类名 {unknown}；请先核对 AnyLabeling 标签")
    return names


def read_label(path: Path, source_names: list[str]) -> tuple[list[str], Counter[str]]:
    if not path.is_file():
        raise ValueError(f"图片缺少同名标签：{path}；空盘图请提供空的 .txt")
    converted: list[str] = []
    counts: Counter[str] = Counter()
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not raw.strip():
            continue
        parts = raw.split()
        if len(parts) != 5:
            raise ValueError(f"{path}:{number} 应为 class x_center y_center width height")
        try:
            source_id = int(parts[0])
            x, y, w, h = map(float, parts[1:])
        except ValueError as exc:
            raise ValueError(f"{path}:{number} 含非数字标签") from exc
        if not 0 <= source_id < len(source_names):
            raise ValueError(f"{path}:{number} 类别 ID {source_id} 超出 classes.txt 范围")
        if not all(math.isfinite(v) for v in (x, y, w, h)):
            raise ValueError(f"{path}:{number} 坐标含 NaN/无穷大")
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
            raise ValueError(f"{path}:{number} 坐标须在归一化范围内且框宽高大于 0")
        tolerance = 1e-5
        if x - w / 2 < -tolerance or x + w / 2 > 1 + tolerance or y - h / 2 < -tolerance or y + h / 2 > 1 + tolerance:
            raise ValueError(f"{path}:{number} 框超出图片边界")
        name = source_names[source_id]
        converted.append(f"{CLASS_NAMES.index(name)} {' '.join(parts[1:])}")
        counts[name] += 1
    return converted, counts


def inspect_export(source: Path) -> tuple[dict[str, tuple[Path, list[str], Counter[str]]], list[str]]:
    source = source.resolve()
    source_names = read_classes(source)
    image_root = source / "images"
    label_root = source / "labels"
    if not image_root.is_dir() or not label_root.is_dir():
        raise ValueError("导出目录应包含 images/、labels/ 和 classes.txt")
    images = sorted(p for p in image_root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    if not images:
        raise ValueError(f"{image_root} 中没有图片")
    records: dict[str, tuple[Path, list[str], Counter[str]]] = {}
    for image in images:
        relative = image.relative_to(image_root)
        key = relative.as_posix()
        label = label_root / relative.with_suffix(".txt")
        converted, counts = read_label(label, source_names)
        records[key] = (image, converted, counts)
    return records, source_names


def read_splits(path: Path, image_keys: set[str]) -> dict[str, tuple[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"image", "scene_id", "split"}.issubset(reader.fieldnames):
            raise ValueError("划分 CSV 必须有 image,scene_id,split 三列")
        assignments: dict[str, tuple[str, str]] = {}
        scene_splits: dict[str, str] = {}
        for row_number, row in enumerate(reader, 2):
            image = (row.get("image") or "").strip().replace("\\", "/")
            scene_id = (row.get("scene_id") or "").strip()
            split = (row.get("split") or "").strip().lower()
            if image not in image_keys or not scene_id or split not in SPLITS:
                raise ValueError(f"划分 CSV 第 {row_number} 行图片、scene_id 或 split 无效：{image!r}")
            if image in assignments:
                raise ValueError(f"划分 CSV 中图片重复：{image}")
            if scene_id in scene_splits and scene_splits[scene_id] != split:
                raise ValueError(f"同一摆放组 {scene_id} 被分到不同集合")
            scene_splits[scene_id] = split
            assignments[image] = (scene_id, split)
    missing = sorted(image_keys - assignments.keys())
    if missing:
        raise ValueError(f"划分 CSV 缺少 {len(missing)} 张图片，例如 {missing[:3]}")
    if not {"train", "val"}.issubset({split for _, split in assignments.values()}):
        raise ValueError("至少需要非空 train 和 val；单图导出只能审计，不能正式训练")
    return assignments


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 AnyLabeling 导出，按类名重映射为固定六类")
    parser.add_argument("--source", type=Path, required=True, help="含 classes.txt、images/、labels/ 的导出目录")
    parser.add_argument("--audit-only", action="store_true", help="仅检查标签，不复制数据")
    parser.add_argument("--splits-csv", type=Path, help="含 image,scene_id,split 三列的人工划分表")
    parser.add_argument("--out", type=Path, help="新数据集目录；不能已经存在")
    parser.add_argument("--link-images", action="store_true", help="同一 NTFS 卷用硬链接共享图片数据，避免再复制照片")
    args = parser.parse_args()

    source = args.source.resolve()
    records, source_names = inspect_export(source)
    totals: Counter[str] = Counter()
    for _, _, counts in records.values():
        totals.update(counts)
    print("AnyLabeling 原类别顺序:", source_names)
    print("训练固定类别顺序:", list(CLASS_NAMES))
    print("图片数:", len(records), "框数:", sum(totals.values()))
    print("逐类框数:", {name: totals[name] for name in CLASS_NAMES})
    if args.audit_only:
        return
    if args.splits_csv is None or args.out is None:
        parser.error("构建数据集需要同时提供 --splits-csv 和 --out；当前单图可用 --audit-only")

    assignments = read_splits(args.splits_csv.resolve(), set(records))
    split_images: Counter[str] = Counter()
    split_classes: dict[str, Counter[str]] = defaultdict(Counter)
    for key, (_, _, counts) in records.items():
        split = assignments[key][1]
        split_images[split] += 1
        split_classes[split].update(counts)
    for split in ("train", "val"):
        absent = [name for name in CLASS_NAMES if split_classes[split][name] == 0]
        if absent:
            raise ValueError(f"{split} 缺少类别 {absent}；先补照片或修改划分")

    output = args.out.resolve()
    if output.exists():
        raise ValueError(f"输出目录已存在，为避免覆盖请换一个新目录：{output}")
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("输出目录不能位于原始导出目录内，也不能包含原始导出目录")
    output.mkdir(parents=True)
    for key, (image, converted, _) in records.items():
        split = assignments[key][1]
        relative = Path(key)
        image_dest = output / "images" / split / relative
        label_dest = output / "labels" / split / relative.with_suffix(".txt")
        image_dest.parent.mkdir(parents=True, exist_ok=True)
        label_dest.parent.mkdir(parents=True, exist_ok=True)
        if args.link_images:
            try:
                os.link(image, image_dest)
            except OSError as exc:
                raise ValueError(f"图片硬链接失败（需同一 NTFS 卷）：{image} -> {image_dest}: {exc}") from exc
        else:
            shutil.copy2(image, image_dest)
        label_dest.write_text("\n".join(converted) + ("\n" if converted else ""), encoding="utf-8")

    yaml_lines = [
        f"path: {json.dumps(output.as_posix(), ensure_ascii=False)}",
        "train: images/train",
        "val: images/val",
    ]
    if split_images["test"]:
        yaml_lines.append("test: images/test")
    yaml_lines.append("names:")
    yaml_lines.extend(f"  {i}: {name}" for i, name in enumerate(CLASS_NAMES))
    (output / "data.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    shutil.copy2(args.splits_csv, output / "splits.csv")
    summary = {
        "source": str(source),
        "image_storage": "hardlink" if args.link_images else "copy",
        "original_classes": source_names,
        "canonical_classes": list(CLASS_NAMES),
        "images": dict(split_images),
        "objects": {split: {name: split_classes[split][name] for name in CLASS_NAMES} for split in SPLITS if split_images[split]},
    }
    (output / "dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("已创建:", output)
    print(json.dumps(summary["images"], ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        raise SystemExit(f"数据检查失败：{exc}") from exc
