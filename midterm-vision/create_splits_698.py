"""Create reproducible scene-grouped train/val assignments for the 698-photo dataset.

Dry run by default. Pass --apply with a new --out name to write a split CSV and audit summary.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "dataset"
DEFAULT_OUT = DEFAULT_SOURCE / "splits.csv"
CLASS_NAMES = ("cube", "sph", "cyl", "tpri", "cone", "tet")
CROP = (250, 180, 1080, 640)


def photo_number(row: dict[str, str]) -> int:
    return int(Path(row["image"]).stem.rsplit("_", 1)[1])


def boxes_for(source: Path, row: dict[str, str]) -> list[tuple[int, float, float, float, float]]:
    label = source / "labels" / Path(row["image"]).with_suffix(".txt")
    result = []
    for raw in label.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip():
            continue
        pieces = raw.split()
        if len(pieces) != 5:
            raise ValueError(f"Invalid label line: {label}: {raw!r}")
        cls = int(pieces[0])
        x, y, w, h = map(float, pieces[1:])
        if not (0 <= cls < 6 and 0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
            raise ValueError(f"Invalid box: {label}: {raw!r}")
        result.append((cls, x * 1280, y * 720, w * 1280, h * 720))
    return result


def same_layout(a: list[tuple], b: list[tuple]) -> bool:
    if not a or len(a) != len(b) or sorted(x[0] for x in a) != sorted(x[0] for x in b):
        return False
    remaining = set(range(len(b)))
    comparisons = []
    for first in a:
        candidates = [j for j in remaining if b[j][0] == first[0]]
        j = min(candidates, key=lambda k: math.hypot(first[1] - b[k][1], first[2] - b[k][2]))
        remaining.remove(j)
        second = b[j]
        comparisons.append((math.hypot(first[1] - second[1], first[2] - second[2]),
                            abs(first[3] - second[3]), abs(first[4] - second[4])))
    if len(a) == 1:
        distance, width_diff, height_diff = comparisons[0]
        return distance <= 35 and width_diff <= 30 and height_diff <= 30
    return (max(item[0] for item in comparisons) <= 50
            and sum(item[0] for item in comparisons) / len(comparisons) <= 22
            and max(max(item[1], item[2]) for item in comparisons) <= 35)


def tray_thumbnail(source: Path, row: dict[str, str]) -> np.ndarray:
    with Image.open(source / "images" / row["image"]) as image:
        return np.asarray(image.convert("RGB").crop(CROP).resize((166, 92)), dtype=np.int16)


def build_scene_groups(source: Path, rows: list[dict[str, str]]) -> list[tuple[str, list[dict[str, str]]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["group"]].append(row)
    scenes = []
    for group, group_rows in sorted(grouped.items()):
        group_rows.sort(key=photo_number)
        if group == "empty":
            # Empty frames share nearly identical backgrounds. Keep short capture runs together.
            components = [group_rows[i:i + 3] for i in range(0, len(group_rows), 3)]
        else:
            descriptions = [boxes_for(source, row) for row in group_rows]
            thumbnails = [tray_thumbnail(source, row) for row in group_rows] if group_rows[0]["kind"] == "mixed" else []
            parent = list(range(len(group_rows)))

            def find(i: int) -> int:
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i

            for i in range(len(group_rows)):
                for j in range(i + 1, len(group_rows)):
                    close = same_layout(descriptions[i], descriptions[j])
                    if not close and thumbnails:
                        close = float(np.abs(thumbnails[i] - thumbnails[j]).mean()) < 5.0
                    if close:
                        parent[find(i)] = find(j)
            by_root: dict[int, list[dict[str, str]]] = defaultdict(list)
            for i, row in enumerate(group_rows):
                by_root[find(i)].append(row)
            components = sorted(by_root.values(), key=lambda c: min(photo_number(x) for x in c))
        if len(components) < 2:
            raise ValueError(f"{group} has fewer than two independent scene groups")
        for number, component in enumerate(components, 1):
            scenes.append((f"{group}__scene_{number:03d}", component))
    return scenes


def choose_validation_scenes(group_scenes: list[tuple[str, list[dict[str, str]]]],
                             ratio: float, rng: random.Random) -> set[str]:
    order = list(group_scenes)
    rng.shuffle(order)
    possible: dict[int, tuple[str, ...]] = {0: ()}
    for scene_id, members in order:
        size = len(members)
        for current, chosen in list(possible.items()):
            possible.setdefault(current + size, chosen + (scene_id,))
    total = sum(len(members) for _, members in group_scenes)
    target = max(1, round(total * ratio))
    options = [n for n in possible if 0 < n < total]
    if not options:
        raise ValueError("Cannot allocate both train and val")
    best = min(options, key=lambda n: (abs(n - target), n > target, n))
    return set(possible[best])


def make_plan(source: Path, ratio: float, seed: int):
    with (source / "manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 698 or len({r["image"] for r in rows}) != 698:
        raise ValueError("Expected 698 unique images in manifest")
    if (source / "classes.txt").read_text(encoding="utf-8-sig").splitlines() != list(CLASS_NAMES):
        raise ValueError("Class order differs from train.py")
    if {r["kind"] for r in rows} != {"single", "mixed", "empty"}:
        raise ValueError("Unexpected image kind")
    for row in rows:
        if not (source / "images" / row["image"]).is_file():
            raise ValueError(f"Missing image: {row['image']}")
        boxes = boxes_for(source, row)
        if len(boxes) != int(row["object_count"]):
            raise ValueError(f"Box count mismatch: {row['image']}")
        if row["kind"] == "empty" and boxes:
            raise ValueError(f"Empty group has boxes: {row['image']}")
    scenes = build_scene_groups(source, rows)
    by_group: dict[str, list[tuple[str, list[dict[str, str]]]]] = defaultdict(list)
    for scene_id, members in scenes:
        by_group[members[0]["group"]].append((scene_id, members))
    rng = random.Random(seed)
    val_ids = set()
    for group in sorted(by_group):
        val_ids.update(choose_validation_scenes(by_group[group], ratio, rng))
    assignments = {}
    for scene_id, members in scenes:
        split = "val" if scene_id in val_ids else "train"
        for row in members:
            assignments[row["image"]] = (scene_id, split)
    if len(assignments) != len(rows):
        raise ValueError("Some images received no assignment")
    image_counts = Counter(split for _, split in assignments.values())
    class_counts = {"train": Counter(), "val": Counter()}
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        split = assignments[row["image"]][1]
        group_counts[row["group"]][split] += 1
        class_counts[split].update(CLASS_NAMES[box[0]] for box in boxes_for(source, row))
    if any(group_counts[g]["train"] == 0 or group_counts[g]["val"] == 0 for g in group_counts):
        raise ValueError("At least one capture group lacks train or val")
    if any(class_counts[s][name] == 0 for s in ("train", "val") for name in CLASS_NAMES):
        raise ValueError("At least one shape class is absent from train or val")
    summary = {
        "source": str(source), "seed": seed, "validation_ratio_target": ratio,
        "grouping": {
            "single": "same group and nearly identical box center/size; connected components",
            "mixed": "same layout or tray thumbnail mean absolute pixel difference < 5; connected components",
            "empty": "consecutive runs of three photos",
        },
        "images": dict(image_counts), "scene_groups": len(scenes),
        "scene_groups_by_split": dict(Counter("val" if scene_id in val_ids else "train" for scene_id, _ in scenes)),
        "objects": {s: {name: class_counts[s][name] for name in CLASS_NAMES} for s in ("train", "val")},
        "capture_groups": {g: dict(group_counts[g]) for g in sorted(group_counts)},
        "test": "not assigned; use new independent camera placements later",
    }
    return assignments, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Group near-duplicate camera photos before splitting")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--val-ratio", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--apply", action="store_true", help="Write CSV and summary; default is read-only preview")
    args = parser.parse_args()
    if not 0.05 <= args.val_ratio <= 0.4:
        parser.error("val-ratio must be between 0.05 and 0.4")
    source = args.source.resolve()
    assignments, summary = make_plan(source, args.val_ratio, args.seed)
    print(json.dumps({key: summary[key] for key in ("images", "scene_groups", "scene_groups_by_split", "objects")}, ensure_ascii=False, indent=2))
    if not args.apply:
        print("Dry run only; add --apply to create split files.")
        return
    out = args.out.resolve()
    report = out.with_name(out.stem + "_summary.json")
    if out.exists() or report.exists():
        raise SystemExit(f"Output exists; choose a new path: {out}")
    if out.parent != source:
        raise SystemExit("For this project, write the split table in the dataset directory")
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image", "scene_id", "split"))
        for image in sorted(assignments):
            scene_id, split = assignments[image]
            writer.writerow((image, scene_id, split))
    summary["created"] = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {out} and {report}")


if __name__ == "__main__":
    main()
