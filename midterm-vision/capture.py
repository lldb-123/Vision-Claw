"""Fast fixed-camera photo capture: Enter group, Space shoot, B change group, Q quit."""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

import cv2


def open_camera(backend: str, index: int | None):
    if backend == "auto":
        choices = [(cv2.CAP_MSMF, 1 if index is None else index),
                   (cv2.CAP_DSHOW, 0 if index is None else index)]
    else:
        backend_id = cv2.CAP_MSMF if backend == "msmf" else cv2.CAP_DSHOW
        choices = [(backend_id, index if index is not None else (1 if backend == "msmf" else 0))]
    for backend_id, camera_id in choices:
        camera = cv2.VideoCapture(camera_id, backend_id)
        if camera.isOpened():
            for _ in range(10):
                ok, frame = camera.read()
                if ok and frame is not None and frame.size:
                    return camera, frame, camera_id
                time.sleep(0.1)
        camera.release()
    raise RuntimeError("Camera unavailable. Close other camera apps and retry.")


def next_number(folder: Path) -> int:
    numbers = [int(match.group(1)) for path in folder.glob("photo_*.png")
               if (match := re.fullmatch(r"photo_(\d+)\.png", path.name))]
    return max(numbers, default=0) + 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Enter group, Space shoot, B change group, Q quit")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "dataset_photos")
    parser.add_argument("--backend", choices=("auto", "msmf", "dshow"), default="auto")
    parser.add_argument("--camera-index", type=int)
    args = parser.parse_args()
    if args.camera_index is not None and args.camera_index < 0:
        parser.error("camera index must be >= 0")

    camera, frame, camera_id = open_camera(args.backend, args.camera_index)
    print(f"Camera: {camera.getBackendName()} index={camera_id}, {frame.shape[1]}x{frame.shape[0]}")
    print("Check that the preview shows the tray before taking photos.")
    title = "Vision-Claw Capture"
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, min(frame.shape[1], 1280), min(frame.shape[0], 720))
    group = ""
    entry = ""
    editing = True
    last_shot = 0.0
    status = "Type group name, then Enter"
    count = 0
    failures = 0
    try:
        while True:
            ok, new_frame = camera.read()
            if ok and new_frame is not None and new_frame.size:
                frame = new_frame
                failures = 0
            else:
                failures += 1
                if failures > 30:
                    raise RuntimeError("Camera stopped returning frames")
                time.sleep(0.05)
                continue

            preview = frame.copy()
            cv2.rectangle(preview, (0, 0), (min(frame.shape[1], 1100), 100), (0, 0, 0), -1)
            line1 = f"GROUP: {entry}_  | Enter=select  Backspace=erase  Q=quit" if editing else (
                f"GROUP: {group}  | SPACE=photo  B=change group  Q=quit")
            cv2.putText(preview, line1, (12, 32), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(preview, f"{status}  | saved this session: {count}", (12, 72),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow(title, preview)
            key = cv2.waitKey(20) & 0xFF
            if key in (ord("q"), 27):
                break
            if editing:
                if key in (13, 10):
                    if entry:
                        group = entry
                        editing = False
                        status = "Ready"
                    else:
                        status = "Enter a group name first"
                elif key in (8, 127):
                    entry = entry[:-1]
                elif (ord("a") <= key <= ord("z") or ord("0") <= key <= ord("9")
                      or key in (ord("_"), ord("-"))):
                    if len(entry) < 40:
                        entry += chr(key)
            elif key == ord("b"):
                entry = ""
                editing = True
                status = "Type new group name, then Enter"
            elif key == 32 and time.monotonic() - last_shot > 0.25:
                folder = args.out / group
                folder.mkdir(parents=True, exist_ok=True)
                number = next_number(folder)
                target = folder / f"photo_{number:06d}.png"
                if not cv2.imwrite(str(target), frame):
                    raise RuntimeError(f"Could not save {target}")
                count += 1
                last_shot = time.monotonic()
                status = f"Saved {group}/{target.name}"
                print(status)
            if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
    print(f"Saved {count} photos in {args.out.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
