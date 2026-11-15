"""Track B flagship model: ConvNeXt-S + PAFPN Oriented Faster R-CNN (le90), DOTA v2.0.

Usage:
    from dota_obb import load_model, predict
    model = load_model()              # loads config + best_dota_mAP_epoch_24.pth
    result = predict(image_bgr)       # dict with 'detections' and 'annotated' (RGB)
"""

from __future__ import annotations

import math
import os
import urllib.request
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "configs" / "benchmark_oriented_faster_rcnn_convnext_s_pafpn_kld_2x_dotav2.py"
DEFAULT_CKPT = REPO_ROOT / "artifacts" / "checkpoints" / "best_dota_mAP_epoch_24.pth"
CACHE_DIR = Path(os.environ.get("DOTA_OBB_CACHE", Path.home() / ".cache" / "dota_obb"))
DEFAULT_CKPT_URL = (
    "https://github.com/Lion4467cat/dotav2-obb-benchmark/releases/download/v1.0.0/best_dota_mAP_epoch_24.pth"
)

DOTA_V2_CLASSES = (
    "plane", "baseball-diamond", "bridge", "ground-track-field", "small-vehicle",
    "large-vehicle", "ship", "tennis-court", "basketball-court", "storage-tank",
    "soccer-ball-field", "roundabout", "harbor", "swimming-pool", "helicopter",
    "container-crane", "airport", "helipad",
)
DOTA_V2_PALETTE = [
    (165, 42, 42), (189, 183, 107), (0, 255, 0), (255, 0, 0), (138, 43, 226),
    (255, 128, 0), (255, 0, 255), (0, 255, 255), (255, 193, 193), (0, 51, 153),
    (255, 250, 205), (0, 139, 139), (255, 255, 0), (147, 116, 116), (0, 0, 255),
    (100, 149, 237), (34, 139, 34), (255, 20, 147),
]

_model = None


def _ensure_checkpoint(checkpoint_path: str | Path | None) -> Path:
    if checkpoint_path is not None:
        path = Path(checkpoint_path)
        if not path.is_file():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        return path
    if DEFAULT_CKPT.is_file():
        return DEFAULT_CKPT
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / DEFAULT_CKPT.name
    if not cached.is_file():
        print(f"Downloading model weights to {cached} ...")
        urllib.request.urlretrieve(DEFAULT_CKPT_URL, cached)
    return cached


def load_model(config_path: str | Path | None = None, checkpoint_path: str | Path | None = None, device: str | None = None):
    global _model
    if _model is not None:
        return _model
    from mmdet.apis import init_detector

    device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
    ckpt = _ensure_checkpoint(checkpoint_path)
    _model = init_detector(str(config_path or DEFAULT_CONFIG), str(ckpt), device=device)
    return _model


def _rbox_corners(box: np.ndarray) -> np.ndarray:
    """(cx, cy, w, h, angle_rad) -> 4 corner points (le90)."""
    x, y, w, h, a = float(box[0]), float(box[1]), float(box[2]), float(box[3]), float(box[4])
    c, s = math.cos(a), math.sin(a)
    dx, dy = w / 2.0, h / 2.0
    pts = []
    for ddx, ddy in ((dx, dy), (dx, -dy), (-dx, -dy), (-dx, dy)):
        pts.append([x + ddx * c - ddy * s, y + ddx * s + ddy * c])
    return np.array(pts, dtype=np.int32)


def render_detections(
    image_rgb: np.ndarray,
    data_sample,
    score_thr: float = 0.3,
    show_labels: bool = True,
) -> tuple[np.ndarray, list[dict]]:
    """Draw le90 boxes + class/score labels onto an RGB image. Returns (annotated_rgb, detections)."""
    import cv2

    img = image_rgb.copy()
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    thick = max(5, img.shape[1] // 180)
    font_scale = float(max(0.62, img.shape[1] / 1100.0))
    inst = data_sample.pred_instances
    bboxes = inst.bboxes.cpu().numpy()
    scores = inst.scores.cpu().numpy()
    labels = inst.labels.cpu().numpy()
    order = np.argsort(-scores)
    detections = []
    for j in order:
        if scores[j] < score_thr:
            continue
        cls = int(labels[j])
        color = DOTA_V2_PALETTE[cls]
        color_bgr = (0, 80, 255)  # bright red — visible on dark aerial imagery
        pts = _rbox_corners(bboxes[j])
        cv2.polylines(img_bgr, [pts.reshape(-1, 1, 2)], True, color_bgr, thick)
        name = DOTA_V2_CLASSES[cls]
        detections.append({"class": name, "score": float(scores[j]), "angle_rad": float(bboxes[j][4])})
        if not show_labels:
            continue
        x, y = int(pts[:, 0].min()), int(pts[:, 1].min())
        text = f"{name[:10]} {scores[j]:.2f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        cv2.rectangle(img_bgr, (x, max(0, y - th - 4)), (x + tw + 2, max(0, y)), color_bgr, -1)
        cv2.putText(img_bgr, text, (x + 1, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2, cv2.LINE_AA)
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), detections


def predict(
    image: np.ndarray,
    score_thr: float = 0.3,
    model=None,
    show_labels: bool = True,
):
    """Run Track B inference on one image.

    Args:
        image: RGB uint8 ndarray (H, W, 3).
        score_thr: minimum score for drawn boxes.
    Returns:
        dict with 'annotated' (RGB uint8), 'detections' (list of dict), 'num_detections'.
    """
    from mmdet.apis import inference_detector

    model = model if model is not None else load_model()
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected an RGB image array with shape (H, W, 3)")
    rgb = np.ascontiguousarray(image)
    # MM models consume BGR; config converts BGR -> RGB via DetDataPreprocessor bgr_to_rgb=True
    import cv2

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    data_sample = inference_detector(model, bgr)
    if isinstance(data_sample, (list, tuple)):
        data_sample = data_sample[0]
    inst = data_sample.pred_instances
    mask = inst.scores.cpu().numpy() >= 0.0
    num = int(mask.sum())
    annotated, detections = render_detections(rgb, data_sample, score_thr=score_thr, show_labels=show_labels)
    return {"annotated": annotated, "detections": detections, "num_detections": num}
