# DOTA v2.0 Benchmark Report (`val` split, OBB `le90`)

## Evaluation data source

All Track B metrics below are from the **official DOTA v2.0 val split** (593 images,
7,122 tiled 1024x1024 patches, 81,048 instances) using the saved
`best_dota_mAP_epoch_24.pth` checkpoint — a pure evaluation pass, no retraining.

An earlier Phase-2 evaluation used a non-official data source (Ultralytics
DOTAv2.zip) that shipped only 458 val images with 16-class YOLO labels and
stripped difficulty flags. Those numbers are preserved in
[Appendix: Phase-2 (superseded)](#appendix-phase-2-superseded) for traceability.
See [Data source correction](#data-source-correction) for details.

Track A metrics are from Phase 1 (A100, official data, same 7,122-patch tiling).

## Core Metrics vs Target Reference

| Model / Reference | Precision (F1-opt) | Recall (F1-opt) | F1-score | mAP50 | mAP50-95 | AP75 | Best Step |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Reference Target (User Provided) | `0.7430` | `0.5670` | `0.6432` | `0.5970` | `0.4210` | — | — |
| Track A: Rotated Faster R-CNN (R50 + FPN, 1x) | 0.8157 | 0.7564 | 0.7849 | 0.6049 | 0.3146 | 0.2785 | 12 |
| Track B: Oriented Faster R-CNN (ConvNeXt-S + PAFPN + KLD, 2x) | **0.8711** | **0.8302** | **0.8502** | **0.6968** | **0.4175** | **0.4347** | 24 |
| Track B (mmengine `dota/mAP`, difficult-included) | — | — | — | — | — | — | 0.6352 |

**Note on two mAP conventions.** The mmengine `DOTAMetric` reports
`dota/mAP: 0.6352` (18-class macro, IoU 0.5, `diff_thr=100` — includes
difficult GT). The extended evaluator reports `mAP50: 0.6968` computed on
non-difficult GT only (`difficult=0`). Both conventions were also used in
Phase 1; the extended (d0-only) number is the apples-to-apples comparison
against Track A's 0.6049.

## OBB-Specific Diagnostic & Operational Metrics

| Metric | Track A (Baseline) | Track B (Flagship) |
| :--- | :---: | :---: |
| F1-Optimal Conf Threshold | — | 0.8279 |
| Macro Precision (18-class mean) | — | 0.7677 |
| Macro Recall (18-class mean) | — | 0.7018 |
| Precision @ conf=0.30 | — | 0.7368 |
| Recall @ conf=0.30 | — | 0.8893 |
| Precision @ conf=0.50 | — | 0.7869 |
| Recall @ conf=0.50 | — | 0.8765 |
| Scale AP50: Small (< 32^2 px^2) | 0.4874 | 0.6089 |
| Scale AP50: Medium (32^2..96^2) | 0.5881 | 0.6844 |
| Scale AP50: Large (> 96^2 px^2) | 0.6602 | 0.8135 |
| Class-Agnostic Localization AP50 | — | 0.8765 |
| Classification Confusion Gap | — | 0.1797 |
| Mean Angle Error - All TPs | 6.42 deg | 4.83 deg |
| Mean Angle Error - Elongated (AR>=1.5) | 3.78 deg | 2.05 deg |
| Easy GT Recall (difficult=0) | 0.7565 | 0.8303 |
| Difficult GT Recall (difficult=1) | 0.2631 | 0.299 |
| Validation Throughput | 17.38 FPS (Phase 1) | 5.70 img/s |
| Model Parameters | 41.37 M | 70.24 M |
| Peak GPU Memory | 28.04 GiB (Phase 1) | 4.20 GiB |

**Difficult recall.** Official DOTA v2.0 val contains 70,561 difficult instances
(46% of all GT). Track B's difficult recall of 0.299 is measured against these
genuinely difficult boxes (tiny, occluded, or ambiguous). The earlier Phase-2
"0.738 difficult recall" was measured against only 3,888 truncated boxes whose
difficulty flags had been stripped — it was not comparable.

## Per-Class AP@0.5 Breakdown

Track A = epoch-10 checkpoint re-evaluated on the official val tiling. Track B = official val, `best_dota_mAP_epoch_24`.
Extended evaluator (non-difficult GT). GT counts are non-difficult occurrences.

| Class | #GT (d0) | Track A AP50 | Track B AP50 | Delta AP50 | Track B AP50-95 | Track B AP75 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `plane` | 3,976 | 0.907 | **0.936** | +0.029 | 0.650 | 0.810 |
| `baseball-diamond` | 357 | 0.698 | **0.757** | +0.058 | 0.427 | 0.424 |
| `bridge` | 745 | 0.390 | **0.557** | +0.167 | 0.233 | 0.138 |
| `ground-track-field` | 192 | 0.729 | **0.798** | +0.070 | 0.553 | 0.663 |
| `small-vehicle` | 21,258 | 0.765 | **0.822** | +0.057 | 0.431 | 0.391 |
| `large-vehicle` | 9,118 | 0.730 | **0.869** | +0.139 | 0.552 | 0.651 |
| `ship` | 23,075 | 0.824 | **0.911** | +0.087 | 0.570 | 0.692 |
| `tennis-court` | 1,414 | 0.939 | **0.957** | +0.018 | 0.823 | 0.924 |
| `basketball-court` | 242 | 0.607 | **0.762** | +0.155 | 0.560 | 0.665 |
| `storage-tank` | 3,273 | 0.808 | **0.829** | +0.020 | 0.549 | 0.653 |
| `soccer-ball-field` | 103 | 0.552 | **0.672** | +0.120 | 0.484 | 0.596 |
| `roundabout` | 278 | 0.712 | **0.763** | +0.050 | 0.461 | 0.492 |
| `harbor` | 4,102 | 0.607 | **0.803** | +0.196 | 0.399 | 0.369 |
| `swimming-pool` | 1,195 | 0.637 | **0.669** | +0.032 | 0.263 | 0.121 |
| `helicopter` | 116 | 0.535 | **0.669** | +0.134 | 0.271 | 0.167 |
| `container-crane` | 27 | 0.000 | **0.032** | +0.032 | 0.007 | 0.000 |
| `airport` | 67 | 0.449 | **0.488** | +0.038 | 0.139 | 0.005 |
| `helipad` | 4 | 0.000 | **0.250** | +0.250 | 0.144 | 0.063 |

**mmengine per-class AP** (includes difficult GT, `diff_thr=100`):

| Class | gts | dets | recall | ap |
| :--- | :---: | :---: | :---: | :---: |
| plane | 4,859 | 5,501 | 0.924 | 0.896 |
| baseball-diamond | 436 | 824 | 0.904 | 0.742 |
| bridge | 893 | 2,264 | 0.703 | 0.540 |
| ground-track-field | 265 | 664 | 0.902 | 0.780 |
| small-vehicle | 82,824 | 63,898 | 0.534 | 0.503 |
| large-vehicle | 10,620 | 16,810 | 0.865 | 0.779 |
| ship | 26,347 | 27,887 | 0.877 | 0.813 |
| tennis-court | 1,539 | 1,715 | 0.951 | 0.908 |
| basketball-court | 292 | 450 | 0.832 | 0.735 |
| storage-tank | 5,117 | 4,275 | 0.642 | 0.617 |
| soccer-ball-field | 247 | 520 | 0.781 | 0.639 |
| roundabout | 338 | 505 | 0.749 | 0.653 |
| harbor | 4,689 | 6,302 | 0.845 | 0.766 |
| swimming-pool | 1,375 | 1,891 | 0.716 | 0.618 |
| helicopter | 128 | 315 | 0.820 | 0.672 |
| container-crane | 28 | 62 | 0.107 | 0.043 |
| airport | 102 | 99 | 0.598 | 0.459 |
| helipad | 4 | 4 | 0.500 | 0.273 |
| **mAP** | | | | **0.635** |

**Low-support classes.** Container-crane (27 non-difficult GT), airport (67), and
helipad (4) have very few instances; their AP is reported with the support count
and should be interpreted cautiously. Airport's AP75 of 0.005 suggests
partial-box problems — large airport polygons may fail the >=70% IoF tiling rule;
multi-scale tiling would likely improve this.

## Precision / Recall / F1 at fixed confidence thresholds

Track B, official val, extended evaluator (non-difficult GT):

| Conf | Precision | Recall | F1 | TP | FP | FN |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.25 | 0.722 | 0.893 | 0.798 | 62,067 | 23,892 | 7,475 |
| 0.30 | 0.737 | 0.889 | 0.806 | 61,846 | 22,089 | 7,696 |
| 0.50 | 0.787 | 0.877 | 0.829 | 60,954 | 16,510 | 8,588 |
| **0.8279 (F1-opt)** | **0.871** | **0.830** | **0.850** | 57,736 | 8,546 | 11,806 |

## Data source correction

The Phase-2 Kaggle evaluation (`scripts/run_kaggle.py`) downloaded data via
`--source ultralytics`, fetching `DOTAv2.zip` from the yolov5 v1.0 GitHub
release. That archive is **not official DOTA v2.0**:

- It ships only 458 of the 593 official val images (the v1.0/v1.5-era subset).
- Labels are 16-class YOLO-OBB format (class ids 0-15); airport (16) and
  helipad (17) are absent entirely.
- Difficulty flags are stripped (forced to 0 during YOLO-to-labelTxt conversion).
- All 104 official val airport + 2 helipad instances live in the 135 new
  GF-2/CycloMedia val images the zip omits.

Phase 1 was unaffected because the Colab notebook used `DATA_SOURCE =
'huggingface'` (isaaccorley/dota — official v2.0, 593 val images).

The official-val re-evaluation was performed by:
1. Downloading official val images + annotations from `isaaccorley/dota`.
2. Assembling the canonical 593-image val split with original-format
   annotations (81,048 instances, difficulty flags intact).
3. Re-tiling with the same 1024/200 recipe (7,122 patches, matching Phase 1).
4. Running Track B (`best_dota_mAP_epoch_24.pth`) and recomputing all metrics.

No retraining was performed. The tiling method (1024x1024, 200px overlap,
stride 824, `iof_thr=0.7`) was correct throughout — only the data source was
wrong.

## Appendix: Phase-2 (superseded)

These numbers are from the non-official Ultralytics data source (458 val
images, 5,297 patches, 16 classes, stripped difficulty). They are superseded
by the official-val results above and retained only for traceability.

| Metric | Phase-2 (superseded) | Official val (current) |
| :--- | :---: | :---: |
| dota/mAP (mmengine) | 0.6893 | 0.6352 |
| Extended mAP50 (d0 GT) | 0.7065 | 0.6968 |
| Extended mAP50-95 | 0.4258 | 0.4175 |
| AP75 | 0.4487 | 0.4347 |
| Precision (F1-opt) | 0.8409 | 0.8711 |
| Recall (F1-opt) | 0.6394 | 0.8302 |
| Easy recall | 0.6395 | 0.8303 |
| Difficult recall | 0.7382 | 0.299 |
| Val patches | 5,297 | 7,122 |
| Val images | 458 | 593 |
| Classes with GT | 16 | 18 |

The mAP drop (0.689->0.635) is not model regression. The official split adds
135 dense GF-2/CycloMedia scenes with 70,561 officially-difficult GT that
Phase 2 never saw. Extended d0-only mAP50 is nearly unchanged (0.697 vs 0.707).
The recall jump (0.639->0.830) reflects proper difficulty flag handling: Phase 2
counted all 120,013 instances as "easy" (flags stripped), while the official
evaluator separates 69,542 easy from 70,561 difficult.
