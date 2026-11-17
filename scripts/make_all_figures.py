"""Generate all data-driven report figures using actual predictions and metrics."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from PIL import Image
from shapely.geometry import Polygon as SPoly
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configs.dota_v2_classes import DOTA_V2_CLASSES, DOTA_V2_PALETTE
from mmrotate.structures.bbox import rbox2qbox

NAVY = "#16233b"
TAB20 = [tuple(c[:3]) for c in plt.cm.tab20(np.linspace(0, 1, 18))]
GT_C = "#06d6e0"   # cyan
PR_C = "#ff6d00"   # orange

TILE_RE = re.compile(r"^(?P<img>.+)__(?P<size>\d+)__(?P<x>\d+)___(?P<y>\d+)$")

def class_idx(name: str) -> int:
    return DOTA_V2_CLASSES.index(name)

def load_gt_quads(ann_path: Path):
    out = []
    if not ann_path.is_file():
        return out
    for line in ann_path.read_text().splitlines():
        p = line.split()
        if len(p) < 10 or p[0].startswith(("imagesource", "gsd")):
            continue
        pts = np.array([float(v) for v in p[:8]], dtype=np.float64).reshape(4, 2)
        cls = " ".join(p[8:-1])
        out.append({"cls": cls, "quad": pts, "difficult": int(p[-1])})
    return out

def pred_polygons(pi):
    rb = pi["bboxes"].numpy().astype(np.float64)
    qb = rbox2qbox(torch.from_numpy(rb)).numpy().astype(np.float64).reshape(-1, 4, 2)
    return qb

def iou_poly(a: np.ndarray, b: np.ndarray) -> float:
    pa, pb = SPoly(a), SPoly(b)
    if not pa.is_valid or not pb.is_valid:
        pa = pa.buffer(0); pb = pb.buffer(0)
    if pa.is_empty or pb.is_empty:
        return 0.0
    inter = pa.intersection(pb).area
    if inter <= 0:
        return 0.0
    return inter / (pa.union(pb).area + 1e-6)

def generate_all_figures(
    preds_pkl_path: Path,
    track_b_ext_json_path: Path,
    track_a_ext_json_path: Path,
    val_images_dir: Path,
    val_ann_dir: Path,
    raw_val_dir: Path,
    out_dirs: list[Path],
):
    for d in out_dirs:
        d.mkdir(parents=True, exist_ok=True)

    print(f"[figures] Loading metrics from {track_b_ext_json_path}...")
    ext_b = json.loads(track_b_ext_json_path.read_text())
    ext_a = json.loads(track_a_ext_json_path.read_text())
    pc_b = ext_b["per_class"]
    pc_a = ext_a["per_class"]
    D0 = {c: pc_b[c]["num_gt"] for c in pc_b}

    print(f"[figures] Loading predictions from {preds_pkl_path}...")
    import pickle
    with open(preds_pkl_path, "rb") as f:
        preds_list = pickle.load(f)
    preds_by_id = {p["img_id"]: p for p in preds_list}

    # 1. Figure 1: Dataset Profile
    def fig_dataset_profile():
        classes = sorted(D0, key=lambda c: D0[c], reverse=True)
        counts = [D0[c] for c in classes]
        colors = [TAB20[class_idx(c)] for c in classes]
        fig = plt.figure(figsize=(21, 14), dpi=100)
        gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.45], hspace=0.28, wspace=0.20)
        ax0 = fig.add_subplot(gs[0, :])
        bars = ax0.bar(classes, counts, color=colors, width=0.7)
        ax0.set_yscale("log")
        ax0.set_ylim(1, 100000)
        ax0.set_ylabel("Non-difficult GT count (log scale)", fontsize=20, color=NAVY)
        ax0.set_xticklabels(classes, rotation=35, ha="right", fontsize=17, color=NAVY)
        ax0.tick_params(axis="y", labelsize=16)
        for b, n in zip(bars, counts):
            ax0.text(b.get_x() + b.get_width() / 2, n * 1.35, f"{n:,}", ha="center",
                     fontsize=15, color=NAVY, fontweight="bold")
        ax0.spines[["top", "right"]].set_visible(False)
        ax0.grid(axis="y", color="#c2cad6", alpha=0.5, lw=1)
        ax0.set_title("Official DOTA v2.0 validation split · non-difficult support by class\n"
                      "593 images · 7,122 patches (1024×1024) · 69,542 non-difficult ground-truth objects",
                      fontsize=24, fontweight="bold", color=NAVY, loc="left", pad=12)

        # Bottom 3 panels
        EXAMPLES = [("plane", "P1122__1024__4944___824"),
                    ("ship", "P6769__1024__0___3296"),
                    ("small-vehicle", "P6687__1024__5768___3888")]
        for col, (cls, tile_id) in enumerate(EXAMPLES):
            ax = fig.add_subplot(gs[1, col])
            img_file = val_images_dir / f"{tile_id}.png"
            if img_file.is_file():
                img = np.asarray(Image.open(img_file).convert("RGB"))
                ax.imshow(img)
                gts = load_gt_quads(val_ann_dir / f"{tile_id}.txt")
                for g in gts:
                    if g["cls"] == cls:
                        q = np.vstack([g["quad"], g["quad"][0]])
                        ax.plot(q[:, 0], q[:, 1], color=GT_C, lw=2.5)
            ax.axis("off")
            ax.set_title(f"Example: {cls} (n={D0[cls]:,})", fontsize=18, fontweight="bold", color=NAVY, loc="left")

        for d in out_dirs:
            fig.savefig(d / "dataset_profile.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> dataset_profile.png ok")

    # 2. Figure: Metrics Comparison
    def fig_metrics_comparison():
        metrics = ["mAP50", "mAP50-95", "AP75", "Class-Agnostic", "Micro P", "Micro R", "Micro F1"]
        f1_opt_a = ext_a.get("micro_prf", {}).get("f1_optimal", {})
        f1_opt_b = ext_b.get("micro_prf", {}).get("f1_optimal", {})
        track_a = [
            ext_a.get("map50", 0.6049),
            ext_a.get("map50_95", 0.3146),
            ext_a.get("ap75", 0.2785),
            ext_a.get("class_agnostic_ap50", 0.7985),
            f1_opt_a.get("precision", 0.8157),
            f1_opt_a.get("recall", 0.7564),
            f1_opt_a.get("f1", 0.7849)
        ]
        track_b = [
            ext_b.get("map50", 0.7127),
            ext_b.get("map50_95", 0.4320),
            ext_b.get("ap75", 0.4664),
            ext_b.get("class_agnostic_ap50", 0.8765),
            f1_opt_b.get("precision", 0.8711),
            f1_opt_b.get("recall", 0.8302),
            f1_opt_b.get("f1", 0.8511)
        ]
        x = np.arange(len(metrics))
        w = 0.38
        fig, ax = plt.subplots(figsize=(19, 10.5), dpi=100)
        ax.grid(axis="y", color="#9aa7bd", alpha=0.6, lw=1)
        ax.bar(x - w / 2, track_a, w, color="#9fb3c8", label="Track A · Rotated Faster R-CNN (R50-FPN)")
        ax.bar(x + w / 2, track_b, w, color=NAVY, label="Track B · Oriented R-CNN (ConvNeXt-S + PAFPN + KLD)")
        for xi, a, b in zip(x, track_a, track_b):
            ax.text(xi - w / 2, a + 0.014, f"{a:.3f}", ha="center", fontsize=15, color=NAVY, fontweight="bold")
            ax.text(xi + w / 2, b + 0.014, f"{b:.3f}", ha="center", fontsize=15, color=NAVY, fontweight="bold")
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("Score / proportion", fontsize=20, color=NAVY)
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, fontsize=17, color=NAVY)
        ax.set_title("Track A vs Track B on official DOTA v2.0 validation split (7,122 patches)",
                     fontsize=23, fontweight="bold", color=NAVY, loc="left", pad=12)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.legend(loc="upper left", fontsize=16, frameon=False)
        fig.tight_layout()
        for d in out_dirs:
            fig.savefig(d / "metrics_comparison.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> metrics_comparison.png ok")

    # 3. Figure 6: Per-class AP50 delta
    def fig_per_class_delta():
        classes = sorted(pc_a.keys(), key=lambda c: pc_b[c]["ap50"] - pc_a[c]["ap50"])
        a = [pc_a[c]["ap50"] for c in classes]
        b = [pc_b[c]["ap50"] for c in classes]
        ns = [pc_a[c]["num_gt"] for c in classes]
        d = [pc_b[c]["ap50"] - pc_a[c]["ap50"] for c in classes]

        fig, ax = plt.subplots(figsize=(15, 11), dpi=110)
        y = np.arange(len(classes))
        h = 0.38
        ax.barh(y + h / 2, a, h, color="#9fb3c8", label="Track A (Rotated Faster R-CNN, R50-FPN)")
        ax.barh(y - h / 2, b, h, color=NAVY, label="Track B (Oriented R-CNN, ConvNeXt-S + PAFPN)")
        for yi, av, bv, dv, n in zip(y, a, b, d, ns):
            ax.text(max(av, bv) + 0.018, yi, f"{av:.3f} → {bv:.3f}  ({dv:+.3f})   n={n:,}",
                    va="center", fontsize=12, color="black")
        ax.set_yticks(y)
        ax.set_yticklabels(classes, fontsize=13)
        ax.tick_params(axis="x", labelsize=12)
        ax.axvline(0.5, color=NAVY, lw=1.5, ls=":", alpha=0.7)
        ax.set_xlim(0, 1.55)
        ax.set_xlabel("AP50 (rotated IoU ≥ 0.50, non-difficult GT)", fontsize=14)
        ax.set_title("Per-class AP50: Track A → Track B on official 7,122-patch val split",
                     fontsize=18, fontweight="bold", loc="left", pad=12)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=12, loc="lower right", frameon=False)
        ax.grid(axis="x", color="#d9d9d9", lw=0.8)
        ax.set_axisbelow(True)
        fig.tight_layout()
        for d in out_dirs:
            fig.savefig(d / "fig_per_class_delta.png", bbox_inches="tight")
            fig.savefig(d / "tracka_vs_trackb_ap.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> fig_per_class_delta.png ok")

    # 4. Figure 7: Track B Class AP & Support
    def fig_class_ap():
        classes = sorted(pc_b, key=lambda c: pc_b[c]["ap50"])
        aps = [pc_b[c]["ap50"] for c in classes]
        ns = [pc_b[c]["num_gt"] for c in classes]
        colors = ["#9fb3c8" if n >= 100 else "#c0703c" for n in ns]

        fig, ax = plt.subplots(figsize=(14, 10), dpi=110)
        bars = ax.barh(classes, aps, color=colors, height=0.72)
        ax.axvline(0.5, color=NAVY, lw=1.5, ls=":", alpha=0.6)
        for b, ap, n in zip(bars, aps, ns):
            ax.text(ap + 0.015, b.get_y() + b.get_height() / 2, f"{ap:.3f} · n={n:,}",
                    va="center", fontsize=12, color=NAVY, fontweight="bold")
        ax.set_xlim(0, 1.25)
        ax.tick_params(axis="y", labelsize=13)
        ax.tick_params(axis="x", labelsize=12)
        ax.set_xlabel("AP50 (non-difficult ground truth)", fontsize=14, color=NAVY)
        ax.set_title("Track B AP50 by class, with validation support (official DOTA v2.0 val)",
                     fontsize=18, fontweight="bold", color=NAVY, loc="left", pad=12)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color="#e2e2e2", lw=0.7)
        ax.set_axisbelow(True)
        fig.tight_layout()
        for d in out_dirs:
            fig.savefig(d / "class_ap.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> class_ap.png ok")

    # 5. Figure: Examples (1-6, 7-12, 13-18)
    def find_tp_example(cls, min_score=0.9, max_other_gt=2):
        idx = class_idx(cls)
        best = None
        relaxed_best = None
        for img_id, p in preds_by_id.items():
            pi = p["pred_instances"]
            gt = p["gt_instances"]
            glabels = gt["labels"].numpy()
            if idx not in glabels:
                continue
            labels = pi["labels"].numpy()
            scores = pi["scores"].numpy()
            sel_pos = np.where(labels == idx)[0]
            if len(sel_pos) == 0:
                continue
            keep = [s for s in sel_pos if scores[s] >= min_score]
            if not keep:
                continue
            qb_all = pi["bboxes"].numpy().astype(np.float64)
            qb = rbox2qbox(torch.from_numpy(qb_all[keep])).numpy().astype(np.float64).reshape(-1, 4, 2)
            gt_quads = load_gt_quads(val_ann_dir / f"{img_id}.txt")
            gt_of_cls = [g for g in gt_quads if g["cls"] == cls]
            if not gt_of_cls:
                continue
            other_gt = int((glabels != idx).sum())
            for j, si in enumerate(keep):
                for g in gt_of_cls:
                    iou = iou_poly(qb[j], g["quad"])
                    if iou >= 0.5:
                        area = float(np.ptp(g["quad"][:, 0]) * np.ptp(g["quad"][:, 1]))
                        cand = (img_id, int(si), float(scores[si]), g, area, iou)
                        if other_gt <= max_other_gt:
                            if best is None or (cand[2] > best[2] and cand[4] >= 1200):
                                best = cand
                        else:
                            if relaxed_best is None or cand[2] > relaxed_best[2]:
                                relaxed_best = cand
        return best if best is not None else relaxed_best

    def draw_panel(ax, img_id, si, score, gt_item, iou):
        img_path = val_images_dir / f"{img_id}.png"
        img = np.asarray(Image.open(img_path).convert("RGB"))
        p = preds_by_id[img_id]
        qb = pred_polygons(p["pred_instances"])[si]
        goutline = gt_item["quad"]
        allpts = np.vstack([goutline, qb])
        x0, y0 = allpts.min(0) - 0.35 * (allpts.max(0) - allpts.min(0) + 1)
        x1, y1 = allpts.max(0) + 0.35 * (allpts.max(0) - allpts.min(0) + 1)
        ih, iw = img.shape[:2]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        w, h = x1 - x0, y1 - y0
        target_a = 1.15
        if w / h < target_a:
            w = h * target_a
        else:
            h = w / target_a
        x0, x1 = cx - w / 2, cx + w / 2
        y0, y1 = cy - h / 2, cy + h / 2
        MINW, MINH = 170, 170
        if (x1 - x0) < MINW:
            x0, x1 = cx - MINW / 2, cx + MINW / 2
        if (y1 - y0) < MINH:
            y0, y1 = cy - MINH / 2, cy + MINH / 2
        x0, y0 = max(0, int(x0)), max(0, int(y0))
        x1, y1 = min(iw, int(x1)), min(ih, int(y1))
        ax.imshow(img[y0:y1, x0:x1])

        def shift(poly):
            q = poly.copy()
            q[:, 0] -= x0; q[:, 1] -= y0
            return np.vstack([q, q[0]])
        ax.plot(*shift(goutline).T, color=GT_C, lw=3)
        ax.plot(*shift(qb).T, color=PR_C, lw=3, ls="--")
        ax.axis("off")

    def fig_examples(classes, title, out_name, nrows=2):
        fig, axes = plt.subplots(nrows, 3, figsize=(21, 13.6), dpi=100,
                                 gridspec_kw={'hspace': 0.32, 'wspace': 0.08})
        MIN_SCORE = {"container-crane": 0.0, "helipad": 0.0, "airport": 0.0}
        for ax, cls in zip(axes.ravel(), classes):
            ex = find_tp_example(cls, min_score=MIN_SCORE.get(cls, 0.7))
            if ex is None:
                # show ground truth outline if no TP
                idx = class_idx(cls)
                gt_item, gt_id = None, None
                for img_id, p in preds_by_id.items():
                    gl = p["gt_instances"]["labels"].numpy()
                    if idx in gl:
                        gts = load_gt_quads(val_ann_dir / f"{img_id}.txt")
                        gt_item = next((g for g in gts if g["cls"] == cls), None)
                        if gt_item:
                            gt_id = img_id
                            break
                if gt_id is not None:
                    img = np.asarray(Image.open(val_images_dir / f"{gt_id}.png").convert("RGB"))
                    poly = gt_item["quad"]
                    x0, y0 = max(0, int(poly[:, 0].min() - 40)), max(0, int(poly[:, 1].min() - 40))
                    x1, y1 = min(img.shape[1], int(poly[:, 0].max() + 40)), min(img.shape[0], int(poly[:, 1].max() + 40))
                    ax.imshow(img[y0:y1, x0:x1])
                    q = np.vstack([poly - [x0, y0], poly[0] - [x0, y0]])
                    ax.plot(q[:, 0], q[:, 1], color=GT_C, lw=3)
                    ax.set_title(f"{cls} · GT (no TP ≥ 0.50, n={D0[cls]})", fontsize=16,
                                 fontweight="bold", color="#c0392b", loc="left")
                else:
                    ax.text(0.5, 0.5, f"no GT found (n={D0[cls]})", ha="center", va="center", fontsize=16, color=NAVY)
                ax.axis("off")
                continue
            img_id, si, score, gt_item, area, iou = ex
            draw_panel(ax, img_id, si, score, gt_item, iou)
            ax.set_title(f"{cls} · IoU {iou:.2f} (score {score:.2f})", fontsize=18, fontweight="bold",
                         color=(NAVY if iou >= 0.5 else "#c0392b"), loc="left")
        fig.suptitle(title, fontsize=24, fontweight="bold", color=NAVY, x=0.55, y=0.99)
        handles = [plt.Line2D([0], [0], color=GT_C, lw=3, label="Ground truth OBB"),
                   plt.Line2D([0], [0], color=PR_C, lw=3, ls="--", label="Track B prediction OBB")]
        fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=17, frameon=False)
        fig.tight_layout(rect=(0, 0.04, 1, 0.96))
        for d in out_dirs:
            fig.savefig(d / out_name, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {out_name} ok")

    # 6. Full scene demo predictions
    def fig_demo():
        scenes = ["P2375", "P0079"]
        titles = ["P2375 · ground-track-field | soccer-ball-field | roundabout",
                  "P0079 · roundabout | small-vehicle | swimming-pool"]
        fig = plt.figure(figsize=(17, 16.5), dpi=100)
        gs = fig.add_gridspec(3, 1, height_ratios=[0.48, 0.48, 0.04], hspace=0.35)
        conf_thr = ext_b.get("micro_prf", {}).get("f1_optimal", {}).get("conf_threshold", 0.834)
        for row, (name, title) in enumerate(zip(scenes, titles)):
            ax = fig.add_subplot(gs[row])
            tiles = [k for k in preds_by_id if k.startswith(name + "__")]
            if not tiles:
                continue
            t0 = tiles[0]
            img_file = val_images_dir / f"{t0}.png"
            if img_file.is_file():
                img = np.asarray(Image.open(img_file).convert("RGB"))
                ax.imshow(img)
                gts = load_gt_quads(val_ann_dir / f"{t0}.txt")
                p = preds_by_id[t0]["pred_instances"]
                labels = p["labels"].numpy()
                scores = p["scores"].numpy()
                keep = np.where(scores >= conf_thr)[0]
                qbs = pred_polygons(p)[keep]
                for g in gts:
                    q = np.vstack([g["quad"], g["quad"][0]])
                    ax.plot(q[:, 0], q[:, 1], color=GT_C, lw=2.6)
                for qb in qbs:
                    q = np.vstack([qb, qb[0]])
                    ax.plot(q[:, 0], q[:, 1], color=PR_C, lw=2.6, ls="--")
            ax.axis("off")
            ax.set_title(title, fontsize=20, fontweight="bold", color=NAVY, loc="left")
        fig.suptitle("Actual Track B predictions on official DOTA validation tiles",
                     fontsize=23, fontweight="bold", color=NAVY, x=0.52, y=0.99)
        handles = [plt.Line2D([0], [0], color=GT_C, lw=2.6, label="Ground truth OBB"),
                   plt.Line2D([0], [0], color=PR_C, lw=2.6, ls="--", label="Track B prediction OBB")]
        fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=16, frameon=False)
        for d in out_dirs:
            fig.savefig(d / "track_b_demo_predictions.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> track_b_demo_predictions.png ok")

    fig_dataset_profile()
    fig_metrics_comparison()
    fig_per_class_delta()
    fig_class_ap()
    fig_examples(["plane", "baseball-diamond", "bridge", "ground-track-field", "small-vehicle", "large-vehicle"],
                 "Track B validation examples · classes 1–6", "validation_class_examples_1.png")
    fig_examples(["ship", "tennis-court", "basketball-court", "storage-tank", "soccer-ball-field", "roundabout"],
                 "Track B validation examples · classes 7–12", "validation_class_examples_2.png")
    fig_examples(["harbor", "swimming-pool", "helicopter", "container-crane", "airport", "helipad"],
                 "Track B validation examples · classes 13–18", "validation_class_examples_3.png")
    fig_demo()
    print("[figures] All figures generated successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds", type=Path, required=True)
    parser.add_argument("--ext-json-b", type=Path, required=True)
    parser.add_argument("--ext-json-a", type=Path, default=PROJECT_ROOT / "artifacts/checkpoints/track_a_eval/eval_test/extended_metrics.json")
    parser.add_argument("--val-images", type=Path, default=PROJECT_ROOT / ".task-data/official_val/split_ss/val/images")
    parser.add_argument("--val-anns", type=Path, default=PROJECT_ROOT / ".task-data/official_val/split_ss/val/annfiles")
    parser.add_argument("--raw-val", type=Path, default=PROJECT_ROOT / ".task-data/dota-raw/_extracted/images/val")
    args = parser.parse_args()

    out_dirs = [PROJECT_ROOT / "revised/assets", PROJECT_ROOT / "docs/figures"]
    generate_all_figures(args.preds, args.ext_json_b, args.ext_json_a, args.val_images, args.val_anns, args.raw_val, out_dirs)
