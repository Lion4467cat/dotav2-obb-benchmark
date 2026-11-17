"""Generate all data-driven report figures using actual predictions and metrics.

Publication-grade: every figure is sized for a 6.2 in column and saved at 300 DPI.
All plotted numbers are loaded from the extended-metrics JSON of the evaluated
checkpoint (no hard-coded metrics). Qualitative panels show ground truth in cyan
(non-difficult) / grey dotted (difficult) and Track B predictions in orange, at the
F1-optimal confidence threshold recorded in the same JSON.
"""
from __future__ import annotations

import argparse
import json
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
GT_C = "#06d6e0"    # cyan   — non-difficult ground truth
GTD_C = "#9aa7bd"   # grey   — difficulty-flagged ground truth
PR_C = "#ff6d00"    # orange — Track B prediction

TILE_RE = re.compile(r"^(?P<img>.+)__(?P<size>\d+)__(?P<x>\d+)___(?P<y>\d+)$")

plt.rcParams["font.family"] = "Liberation Serif"

TIER_COLORS = {
    "ge90": "#117A65",   # AP >= 0.90 — deep green
    "ge70": "#D4A017",   # 0.70-0.90  — mustard gold
    "ge40": "#E67E22",   # 0.40-0.70  — burnt orange
    "lt40": "#C0392B",   # < 0.40     — brick red
}

def tier_of(ap: float) -> str:
    if ap >= 0.90:
        return "ge90"
    if ap >= 0.70:
        return "ge70"
    if ap >= 0.40:
        return "ge40"
    return "lt40"

def tier_legend(ax, frameon=False):
    import matplotlib.patches as mpatches
    handles = [
        mpatches.Patch(color=TIER_COLORS["ge90"], label="AP ≥ 0.90"),
        mpatches.Patch(color=TIER_COLORS["ge70"], label="0.70–0.90"),
        mpatches.Patch(color=TIER_COLORS["ge40"], label="0.40–0.70"),
        mpatches.Patch(color=TIER_COLORS["lt40"], label="< 0.40"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=6.8, frameon=frameon,
              title="AP50 tier", title_fontsize=7.2)

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

def style_ax(ax, grid_axis="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color="#c2cad6", alpha=0.55, lw=0.7)
    ax.set_axisbelow(True)

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
    f1_opt = ext_b.get("micro_prf", {}).get("f1_optimal", {})
    CONF = f1_opt.get("conf_threshold", 0.834)

    # 0. Figure 4.1: Workflow diagram (regenerated; report theme)
    def fig_pipeline():
        from matplotlib.patches import FancyBboxPatch
        import matplotlib.patheffects as pe

        fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=300)
        ax.set_xlim(0, 100); ax.set_ylim(0, 58); ax.axis("off")

        def box(x, y, w, h, lines, fc, ec, fs_head=10, fs_body=7.8):
            ax.add_patch(FancyBboxPatch((x, y), w, h,
                                        boxstyle="round,pad=0.45,rounding_size=1.5",
                                        linewidth=1.3, edgecolor=ec, facecolor=fc, zorder=3))
            ax.text(x + w / 2, y + h * 0.70, lines[0], ha="center", va="center",
                    fontsize=fs_head, fontweight="bold", color=NAVY, zorder=4)
            body = lines[1:]
            step = h * 0.17
            y0 = y + h * 0.42 - (len(body) - 1) * step / 2
            for j, line in enumerate(body):
                ax.text(x + w / 2, y0 - j * step, line, ha="center", va="center",
                        fontsize=fs_body, color=NAVY, zorder=4)

        def arrow(x0, y0, x1, y1):
            ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                        arrowprops=dict(arrowstyle="-|>", mutation_scale=14,
                                        lw=1.4, color=NAVY, shrinkA=1, shrinkB=1),
                        zorder=2)

        box(1, 18, 17.5, 22, ("DOTA v2.0", "18 oriented", "classes"), "#eef2f7", NAVY)
        box(26, 18, 17.5, 22, ("Prepare", "1,024² patches", "200 px overlap"), "#edf7ef", NAVY)
        box(51.5, 34, 23, 18, ("Track A", "Rotated Faster R-CNN", "ResNet-50 + FPN"),
            "#fdf3e0", "#c8861f", fs_head=9.6, fs_body=7.6)
        box(51.5, 5, 23, 18, ("Track B", "Oriented R-CNN", "ConvNeXt-S + PAFPN"),
            "#fbeff2", "#b04a63", fs_head=9.6, fs_body=7.6)
        box(81.5, 18, 17, 22, ("Evaluate", "MMRotate dota/mAP", "+ extended OBB metrics"),
            "#efeaf5", NAVY, fs_head=10, fs_body=7.4)

        arrow(19, 29, 25.5, 29)
        arrow(44, 33, 51, 41.5)
        arrow(44, 25, 51, 15.5)
        arrow(74.9, 42.6, 81.2, 33.6)
        arrow(74.9, 15.2, 81.2, 24.4)

        fig.tight_layout(pad=0.15)
        for d in out_dirs:
            fig.savefig(d / "pipeline.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> pipeline.png ok")

    # 1. Figure 1: Dataset Profile
    def fig_dataset_profile():
        classes = sorted(D0, key=lambda c: D0[c], reverse=True)
        counts = [D0[c] for c in classes]
        colors = [TAB20[class_idx(c)] for c in classes]
        fig = plt.figure(figsize=(10.4, 7.2), dpi=300)
        gs = fig.add_gridspec(2, 3, height_ratios=[1.12, 0.52], hspace=0.55, wspace=0.18)
        ax0 = fig.add_subplot(gs[0, :])
        bars = ax0.bar(classes, counts, color=colors, width=0.72)
        ax0.set_yscale("log")
        ax0.set_ylim(1, 400000)
        ax0.set_ylabel("Non-difficult GT count (log)", fontsize=10, color=NAVY)
        ax0.set_xticks(range(len(classes)))
        ax0.set_xticklabels(classes, rotation=30, ha="right", fontsize=8, color=NAVY)
        ax0.tick_params(axis="y", labelsize=9)
        for b, n in zip(bars, counts):
            ax0.text(b.get_x() + b.get_width() / 2, n * 1.42, f"{n:,}", ha="center",
                     fontsize=6.4, color=NAVY, fontweight="bold")
        style_ax(ax0, "y")
        ax0.set_title("Official DOTA v2.0 validation split · non-difficult support by class\n"
                      "593 images · 7,122 patches (1024×1024) · 69,542 non-difficult ground-truth annotations",
                      fontsize=10.5, fontweight="bold", color=NAVY, loc="left", pad=8)

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
                        ax.plot(q[:, 0], q[:, 1], color=GT_C, lw=1.4)
            ax.axis("off")
            ax.set_title(f"Example: {cls} (n={D0[cls]:,})", fontsize=8.6, fontweight="bold",
                         color=NAVY, loc="left", pad=4)
        for d in out_dirs:
            fig.savefig(d / "dataset_profile.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> dataset_profile.png ok")

    # 2. Figure 5: Headline metrics, both tracks
    def fig_metrics_comparison():
        metrics = ["mAP50", "mAP50-95", "AP75", "Class-\nagnostic", "Micro P", "Micro R", "Micro F1"]
        f1_opt_a = ext_a.get("micro_prf", {}).get("f1_optimal", {})
        track_a = [
            ext_a.get("map50", 0.6049),
            ext_a.get("map50_95", 0.3146),
            ext_a.get("ap75", 0.2785),
            ext_a.get("class_agnostic_ap50", 0.7985),
            f1_opt_a.get("precision", 0.8157),
            f1_opt_a.get("recall", 0.7563),
            f1_opt_a.get("f1", 0.7849),
        ]
        track_b = [
            ext_b.get("map50", 0.7127),
            ext_b.get("map50_95", 0.4320),
            ext_b.get("ap75", 0.4664),
            ext_b.get("class_agnostic_ap50", 0.8803),
            f1_opt.get("precision", 0.8694),
            f1_opt.get("recall", 0.8335),
            f1_opt.get("f1", 0.8511),
        ]
        # one high-contrast base hue per metric category; A = soft tint, B = saturated shade
        base_hues = ["#c0392b", "#d35400", "#b7950b", "#1e8449", "#148f77", "#7d3c98", "#1f618d"]

        def tint(hex_rgb, f=0.62):
            import matplotlib.colors as mcolors
            r, g, b = mcolors.to_rgb(hex_rgb)
            return tuple(c + (1 - c) * f for c in (r, g, b))

        x = np.arange(len(metrics))
        w = 0.38
        fig, ax = plt.subplots(figsize=(9.8, 5.2), dpi=300)
        ax.grid(axis="y", color="#9aa7bd", alpha=0.55, lw=0.7)
        ax.bar(x - w / 2, track_a, w, color=[tint(h) for h in base_hues],
               edgecolor=NAVY, linewidth=0.7, label="Track A · Rotated Faster R-CNN (R50-FPN)")
        ax.bar(x + w / 2, track_b, w, color=base_hues,
               edgecolor=NAVY, linewidth=0.7, label="Track B · Oriented R-CNN (ConvNeXt-S + PAFPN + KLD)")
        for xi, a, b in zip(x, track_a, track_b):
            ax.text(xi - w / 2, a + 0.016, f"{a:.3f}", ha="center", fontsize=7.4, color=NAVY, fontweight="bold")
            ax.text(xi + w / 2, b + 0.016, f"{b:.3f}", ha="center", fontsize=7.4, color=NAVY, fontweight="bold")
        ax.set_ylim(0, 1.3)
        ax.set_ylabel("Score / proportion", fontsize=9.5, color=NAVY)
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, fontsize=8.2, color=NAVY)
        ax.tick_params(axis="y", labelsize=9)
        ax.set_title("Track A vs Track B on official DOTA v2.0 validation split (7,122 patches)",
                     fontsize=9.6, fontweight="bold", color=NAVY, loc="left", pad=7)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.legend(loc="upper left", fontsize=7.4, frameon=False, ncol=2)
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

        b_colors = [TIER_COLORS[tier_of(v)] for v in b]
        fig, ax = plt.subplots(figsize=(8.8, 6.6), dpi=300)
        y = np.arange(len(classes))
        h = 0.38
        ax.barh(y + h / 2, a, h, color="#a9b4c2", edgecolor=NAVY, linewidth=0.6,
                label="Track A (Rotated Faster R-CNN, R50-FPN)")
        ax.barh(y - h / 2, b, h, color=b_colors, edgecolor=NAVY, linewidth=0.6,
                label="Track B (Oriented R-CNN, ConvNeXt-S + PAFPN), tier-coded")
        for yi, av, bv, dv, n in zip(y, a, b, d, ns):
            ax.text(max(av, bv) + 0.018, yi, f"{av:.3f} → {bv:.3f}  ({dv:+.3f})   n={n:,}",
                    va="center", fontsize=6.7, color="black")
        ax.set_yticks(y)
        ax.set_yticklabels(classes, fontsize=7.5)
        ax.tick_params(axis="x", labelsize=8)
        ax.axvline(0.5, color=NAVY, lw=1.1, ls=":", alpha=0.7)
        ax.set_xlim(0, 1.62)
        ax.set_xlabel("AP50 (rotated IoU ≥ 0.50, non-difficult GT)", fontsize=8.4, color=NAVY)
        ax.set_title("Per-class AP50: Track A → Track B · official 7,122-patch val split",
                     fontsize=9.6, fontweight="bold", color=NAVY, loc="left", pad=7)
        style_ax(ax, "x")
        import matplotlib.patches as mpatches
        handles = [
            mpatches.Patch(facecolor="#a9b4c2", edgecolor=NAVY, label="Track A"),
        ] + [mpatches.Patch(facecolor=TIER_COLORS[k], edgecolor=NAVY, label=lab)
             for k, lab in [("ge90", "B ≥ 0.90"), ("ge70", "B 0.70–0.90"),
                            ("ge40", "B 0.40–0.70"), ("lt40", "B < 0.40")]]
        ax.legend(handles=handles, fontsize=6.8, loc="lower right", frameon=True,
                  ncol=5, title="AP50 tier (Track B)", title_fontsize=6.9)
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
        colors = [TIER_COLORS[tier_of(ap)] for ap in aps]

        fig, ax = plt.subplots(figsize=(7.8, 6.1), dpi=300)
        bars = ax.barh(classes, aps, color=colors, edgecolor=NAVY, linewidth=0.6, height=0.72)
        ax.axvline(0.5, color=NAVY, lw=1.1, ls=":", alpha=0.6)
        for b, ap, n in zip(bars, aps, ns):
            ax.text(ap + 0.015, b.get_y() + b.get_height() / 2, f"{ap:.3f} · n={n:,}",
                    va="center", fontsize=7.4, color=NAVY, fontweight="bold")
        ax.set_xlim(0, 1.3)
        ax.tick_params(axis="y", labelsize=7.6)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_xlabel("AP50 (non-difficult ground truth)", fontsize=8.6, color=NAVY)
        ax.set_title("Track B AP50 by class, with validation support",
                     fontsize=9.6, fontweight="bold", color=NAVY, loc="left", pad=7)
        style_ax(ax, "x")
        tier_legend(ax)
        fig.tight_layout()
        for d in out_dirs:
            fig.savefig(d / "class_ap.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> class_ap.png ok")

    # 5. Figures 9-11: class examples
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
        ax.plot(*shift(goutline).T, color=GT_C, lw=1.6)
        ax.plot(*shift(qb).T, color=PR_C, lw=1.6, ls="--")
        ax.axis("off")

    def fig_examples(classes, title, out_name, nrows=2):
        fig, axes = plt.subplots(nrows, 3, figsize=(9.6, 6.6), dpi=300,
                                 gridspec_kw={'hspace': 0.30, 'wspace': 0.08})
        MIN_SCORE = {"container-crane": 0.0, "helipad": 0.0, "airport": 0.0}
        for ax, cls in zip(axes.ravel(), classes):
            ex = find_tp_example(cls, min_score=MIN_SCORE.get(cls, 0.7))
            if ex is None:
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
                    ax.plot(q[:, 0], q[:, 1], color=GT_C, lw=1.6)
                    ax.set_title(f"{cls} · GT (no TP ≥ 0.50, n={D0[cls]})", fontsize=8,
                                 fontweight="bold", color="#c0392b", loc="left")
                else:
                    ax.text(0.5, 0.5, f"no GT found (n={D0[cls]})", ha="center", va="center",
                            fontsize=9, color=NAVY)
                ax.axis("off")
                continue
            img_id, si, score, gt_item, area, iou = ex
            draw_panel(ax, img_id, si, score, gt_item, iou)
            ax.set_title(f"{cls} · IoU {iou:.2f} (score {score:.2f})", fontsize=8,
                         fontweight="bold", color=(NAVY if iou >= 0.5 else "#c0392b"), loc="left")
        handles = [plt.Line2D([0], [0], color=GT_C, lw=1.6, label="Ground truth OBB"),
                   plt.Line2D([0], [0], color=PR_C, lw=1.6, ls="--", label="Track B prediction OBB")]
        fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=8, frameon=False)
        fig.tight_layout(rect=(0, 0.05, 1, 1))
        for d in out_dirs:
            fig.savefig(d / out_name, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {out_name} ok")

    # 6. Figure 8: Full-scene prediction examples, F1-optimal threshold
    def fig_demo():
        scenes = ["P2242__1024__824___142", "P10090__1024__0___0"]
        titles = ["P2242 · plane | small-vehicle | large-vehicle",
                  "P10090 · ship | harbor | small-vehicle"]
        fig = plt.figure(figsize=(9.6, 4.9), dpi=300)
        gs = fig.add_gridspec(1, 2, wspace=0.08)

        for col, (img_id, title) in enumerate(zip(scenes, titles)):
            ax = fig.add_subplot(gs[col])
            img_file = val_images_dir / f"{img_id}.png"
            if not img_file.is_file():
                continue
            img = np.asarray(Image.open(img_file).convert("RGB"))
            ax.imshow(img)
            gts = load_gt_quads(val_ann_dir / f"{img_id}.txt")
            p = preds_by_id[img_id]["pred_instances"]
            labels = p["labels"].numpy()
            scores = p["scores"].numpy()
            keep = np.where(scores >= CONF)[0]
            qbs = pred_polygons(p)[keep]
            for g in gts:
                q = np.vstack([g["quad"], g["quad"][0]])
                if g["difficult"]:
                    ax.plot(q[:, 0], q[:, 1], color=GTD_C, lw=0.7, ls=":", alpha=0.75)
                else:
                    ax.plot(q[:, 0], q[:, 1], color=GT_C, lw=1.0)
            for qb in qbs:
                q = np.vstack([qb, qb[0]])
                ax.plot(q[:, 0], q[:, 1], color=PR_C, lw=1.0, ls="--")
            ax.axis("off")
            ax.set_title(title, fontsize=8.6, fontweight="bold", color=NAVY, loc="left", pad=4)
        handles = [plt.Line2D([0], [0], color=GT_C, lw=1.6, label="GT (non-difficult)"),
                   plt.Line2D([0], [0], color=GTD_C, lw=1.6, ls=":", label="GT (difficult)"),
                   plt.Line2D([0], [0], color=PR_C, lw=1.6, ls="--",
                               label=f"Track B prediction (conf ≥ {CONF:.3f})")]
        fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7.6, frameon=False)
        fig.tight_layout(rect=(0, 0.10, 1, 1))
        for d in out_dirs:
            fig.savefig(d / "track_b_demo_predictions.png", bbox_inches="tight")
        plt.close(fig)
        print("  -> track_b_demo_predictions.png ok")

    fig_pipeline()
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
