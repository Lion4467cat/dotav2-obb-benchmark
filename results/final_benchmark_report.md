# DOTA v2.0 Benchmark Report (`val` split, OBB `le90`)

## Evaluation Data Source

All Track B metrics below are from the **official DOTA v2.0 val split** (593 images,
7,122 tiled 1024x1024 patches, 81,048 instances) using the official retrain
`epoch_24.pth` checkpoint (epochs 23–24 completed in a resumed Kaggle 2×T4 run;
epoch-24 validation dota/mAP **0.6535**, identical for the final `test.py` pass)
evaluated on the official 18-class annotations.

Track A metrics are from Phase 1 (A100, official data, same 7,122-patch tiling).

## Core Metrics vs Target Reference

| Model / Reference | Precision (F1-opt) | Recall (F1-opt) | F1-score | mAP50 | mAP50-95 | AP75 | Epoch |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Reference Target (User Provided) | `0.7430` | `0.5670` | `0.6432` | `0.5970` | `0.4210` | — | — |
| Track A: Rotated Faster R-CNN (R50 + FPN, 1x) | 0.8157 | 0.7563 | 0.7849 | 0.6049 | 0.3146 | 0.2785 | 10 |
| Track B: Oriented R-CNN (ConvNeXt-S + PAFPN + KLD, 2x) | **0.8694** | **0.8335** | **0.8511** | **0.7127** | **0.4320** | **0.4664** | 24 |

## Diagnostic & Operational Metrics

| Metric | Track A (Baseline) | Track B (Flagship) | Δ (B − A) |
| :--- | :---: | :---: | :---: |
| F1-Optimal Confidence Threshold | 0.8103 | 0.8340 | +0.0237 |
| Macro F1 (18-class unweighted mean) | 0.6285 | 0.7319 | +0.1034 |
| Macro Precision (18-class mean) | 0.6797 | 0.7644 | +0.0847 |
| Macro Recall (18-class mean) | 0.5903 | 0.7066 | +0.1163 |
| Class-Agnostic AP50 | 0.7985 | 0.8803 | +0.0818 |
| Classification Gap (Agnostic − AP50) | 0.1936 | 0.1676 | -0.0260 |
| Scale AP50: Small (area ≤ 32² px) | 0.4874 | 0.6220 | +0.1346 |
| Scale AP50: Medium (32²–96² px) | 0.5881 | 0.6826 | +0.0945 |
| Scale AP50: Large (area > 96² px) | 0.6602 | 0.8394 | +0.1792 |
| Orientation Error: Mean, All TP (deg) | 6.42° | 4.88° | -1.54° |
| Orientation Error: Median, All TP (deg) | 2.62° | 1.56° | -1.06° |
| Orientation Error: Mean, Elongated (AR ≥ 1.5) | 3.78° | 2.05° | -1.73° |
| Orientation Error: Median, Elongated (AR ≥ 1.5) | 2.55° | 1.46° | -1.09° |
| Easy GT Recall (non-difficult, n=69,542) | 0.7564 | 0.8335 | +0.0771 |
| Difficult GT Recall (flagged, n=70,561) | 0.2630 | 0.3019 | +0.0389 |
| Total Predictions (conf ≥ 0.05) | 180,555 | 136,612 | −43,943 |
| Model Parameters | not recorded | 70.24 M | — |
| Inference Throughput | 11.36 FPS (A100) | 2.52 img/s (Kaggle 2×T4, batch 1) | — |
| Peak VRAM | 2.86 GiB (A100) | 9.25 GiB (Kaggle 2×T4) | — |

## Precision / Recall / F1 at Operating Points

| Conf Threshold | Track A Precision | Track A Recall | Track A F1 | Track B Precision | Track B Recall | Track B F1 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.25 | 0.5869 | 0.8351 | 0.6893 | 0.7153 | 0.8960 | 0.7956 |
| 0.30 | 0.6133 | 0.8310 | 0.7058 | 0.7301 | 0.8931 | 0.8034 |
| 0.50 | 0.6983 | 0.8148 | 0.7521 | 0.7813 | 0.8807 | 0.8280 |
| **F1-Optimal** | **0.8157** (thr=0.8103) | **0.7563** | **0.7849** | **0.8694** (thr=0.8340) | **0.8335** | **0.8511** |

## Per-Class AP50 Summary (Sorted by Gain)

| Class | n (GT) | Track A AP50 | Track B AP50 | Δ AP50 | Track B AP75 | Track B AP50-95 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| helipad | 4 | 0.0000 | 0.4167 | +0.4167 | 0.4167 | 0.2667 |
| harbor | 4,102 | 0.6067 | 0.7972 | +0.1905 | 0.3722 | 0.3969 |
| bridge | 745 | 0.3901 | 0.5724 | +0.1823 | 0.1465 | 0.2376 |
| airport | 67 | 0.4492 | 0.6141 | +0.1649 | 0.0834 | 0.2099 |
| basketball-court | 242 | 0.6067 | 0.7549 | +0.1482 | 0.6931 | 0.5674 |
| large-vehicle | 9,118 | 0.7296 | 0.8694 | +0.1398 | 0.6608 | 0.5533 |
| soccer-ball-field | 103 | 0.5525 | 0.6720 | +0.1195 | 0.5774 | 0.4956 |
| helicopter | 116 | 0.5346 | 0.6381 | +0.1035 | 0.1625 | 0.2742 |
| ship | 23,075 | 0.8237 | 0.9169 | +0.0932 | 0.6961 | 0.5726 |
| baseball-diamond | 357 | 0.6984 | 0.7781 | +0.0797 | 0.4474 | 0.4390 |
| ground-track-field | 192 | 0.7285 | 0.8016 | +0.0731 | 0.6940 | 0.5493 |
| small-vehicle | 21,258 | 0.7653 | 0.8256 | +0.0603 | 0.4186 | 0.4438 |
| roundabout | 278 | 0.7123 | 0.7707 | +0.0584 | 0.5061 | 0.4741 |
| plane | 3,976 | 0.9072 | 0.9424 | +0.0352 | 0.8206 | 0.6589 |
| swimming-pool | 1,195 | 0.6367 | 0.6641 | +0.0274 | 0.1227 | 0.2624 |
| storage-tank | 3,273 | 0.8081 | 0.8251 | +0.0170 | 0.6477 | 0.5429 |
| tennis-court | 1,414 | 0.9385 | 0.9543 | +0.0158 | 0.9293 | 0.8291 |
| container-crane | 27 | 0.0000 | 0.0151 | +0.0151 | 0.0000 | 0.0016 |
| **Mean (18 classes)** | **69,542** | **0.6049** | **0.7127** | **+0.1078** | **0.4664** | **0.4320** |

## Appendix: Phase-2 (superseded)

These numbers are from the **original** Kaggle continuation (epochs 17–24, resumed from the
A100 epoch-16 checkpoint), which used a non-official `DOTAv2.zip` archive (Ultralytics yolov5
v1.0 GitHub release): 458 of the 593 official val images, 16 classes (no airport/helipad), no
difficulty flags, tiled to **5,297** patches. They are retained for traceability only and are
**superseded** by everything above.

| Milestone | dota/mAP (val log) | Notes |
| :--- | :---: | :--- |
| epoch 20 (Phase-2 final) | 0.6879 | 5,297-patch tiling, 16 classes |
| epoch 24 (Phase-2 final) | 0.6892 | 5,297-patch tiling, 16 classes |

Source log: `results/logs/2026-11-15_track_b_final_epochs_17-24.log`. The tiling method was
correct; the data source was not. The official retrain (HuggingFace `isaaccorley/dota`, merged
v1.0 + v2.0 train imagery, 18 classes, difficulty flags preserved) replaces these figures; see
the Data source correction section of the README.
