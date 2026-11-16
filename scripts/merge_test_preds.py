"""Merge tile-level DOTA-v2.0 test-dev predictions into full-image coordinates.

Reads the pickle produced by infer_test_tiles.py, translates le90 boxes from
1024x1024 tiles back to original image space, applies per-(image, class)
rotated NMS, and writes the 18 Task1_<class>.txt files plus a submission zip.
"""

from __future__ import annotations

import argparse
import math
import pickle
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image

DOTA_V2_CLASSES = (
    "plane", "baseball-diamond", "bridge", "ground-track-field", "small-vehicle",
    "large-vehicle", "ship", "tennis-court", "basketball-court", "storage-tank",
    "soccer-ball-field", "roundabout", "harbor", "swimming-pool", "helicopter",
    "container-crane", "airport", "helipad",
)

TILE_RE = re.compile(r"^(?P<img_id>.+)__(?P<size>\d+)__(?P<x>\d+)___(?P<y>\d+)$")


def le90_corners(box: np.ndarray) -> np.ndarray:
    x, y, w, h, a = (float(v) for v in box)
    c, s = math.cos(a), math.sin(a)
    dx, dy = w / 2.0, h / 2.0
    pts = []
    for ddx, ddy in ((dx, dy), (dx, -dy), (-dx, -dy), (-dx, dy)):
        pts.append((x + ddx * c - ddy * s, y + ddx * s + ddy * c))
    return np.array(pts, dtype=np.float64)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds-pkl", default=".task-data/test_tile_preds.pkl")
    parser.add_argument("--test-images", default=".task-data/dota-raw/_extracted/images/test")
    parser.add_argument("--out-dir", default="results/task1_submission")
    parser.add_argument("--iou-thr", type=float, default=0.5)
    args = parser.parse_args()

    test_images = Path(args.test_images)
    sizes = {}
    for p in test_images.iterdir():
        with Image.open(p) as im:
            sizes[p.stem] = im.size  # (W, H)

    with open(args.preds_pkl, "rb") as f:
        tiles = pickle.load(f)
    print(f"[merge] {len(tiles)} tiles, {sum(len(t['scores']) for t in tiles)} raw detections")

    # (img_id, class) -> lists of (score, cx, cy, w, h, angle)
    grouped: dict[tuple[str, int], list[tuple]] = defaultdict(list)
    n_in_image = 0
    for tile in tiles:
        m = TILE_RE.match(tile["tile"])
        if not m:
            raise ValueError(f"unparsable tile name: {tile['tile']}")
        img_id = m.group("img_id")
        x_off, y_off = int(m.group("x")), int(m.group("y"))
        W, H = sizes[img_id]
        for score, label, box in zip(tile["scores"], tile["labels"], tile["bboxes"]):
            cx, cy = float(box[0]) + x_off, float(box[1]) + y_off
            if not (0.0 <= cx < W and 0.0 <= cy < H):
                continue
            n_in_image += 1
            grouped[(img_id, int(label))].append(
                (float(score), cx, cy, float(box[2]), float(box[3]), float(box[4]))
            )
    print(f"[merge] {n_in_image} detections inside original image bounds")

    from mmcv.ops import nms_rotated

    per_class: dict[int, list[str]] = {i: [] for i in range(len(DOTA_V2_CLASSES))}
    n_after_nms = 0
    for (img_id, cls), dets in grouped.items():
        boxes = torch.tensor([d[1:] for d in dets], dtype=torch.float32, device="cuda:0")
        scores = torch.tensor([d[0] for d in dets], dtype=torch.float32, device="cuda:0")
        if len(dets) == 1:
            keep = [0]
        else:
            _, keep_idx = nms_rotated(boxes, scores, args.iou_thr)
            keep = keep_idx.cpu().tolist()
        for i in keep:
            s, cx, cy, w, h, a = dets[i]
            pts = le90_corners(np.array([cx, cy, w, h, a]))
            coords = " ".join(f"{v:.1f}" for v in pts.reshape(-1))
            per_class[cls].append(f"{img_id} {s:.4f} {coords}")
            n_after_nms += 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    empty = []
    for i, name in enumerate(DOTA_V2_CLASSES):
        lines = per_class[i]
        if not lines:
            empty.append(name)
        (out_dir / f"Task1_{name}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        print(f"[merge] Task1_{name}.txt: {len(lines)} detections")

    zip_path = out_dir / "Task1.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in DOTA_V2_CLASSES:
            zf.write(out_dir / f"Task1_{name}.txt", arcname=f"Task1_{name}.txt")
    print(f"[merge] {n_after_nms} detections after NMS; wrote {zip_path}")
    if empty:
        print(f"[merge] WARNING empty class files: {empty}")


if __name__ == "__main__":
    main()
