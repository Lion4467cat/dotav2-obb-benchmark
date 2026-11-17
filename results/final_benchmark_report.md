# DOTA v2.0 Benchmark Report (`val` split, OBB `le90`)

## Evaluation Data Source

All Track B metrics below are from the **official DOTA v2.0 val split** (593 images,
7,122 tiled 1024x1024 patches, 81,048 instances) using the official retrain
`epoch_22.pth` checkpoint evaluated on the official 18-class annotations.

Track A metrics are from Phase 1 (A100, official data, same 7,122-patch tiling).

## Core Metrics vs Target Reference

| Model / Reference | Precision (F1-opt) | Recall (F1-opt) | F1-score | mAP50 | mAP50-95 | AP75 | Epoch |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Reference Target (User Provided) | `0.7430` | `0.5670` | `0.6432` | `0.5970` | `0.4210` | — | — |
| Track A: Rotated Faster R-CNN (R50 + FPN, 1x) | 0.8157 | 0.7563 | 0.7849 | 0.6049 | 0.3146 | 0.2785 | 10 |
| Track B: Oriented R-CNN (ConvNeXt-S + PAFPN + KLD, 2x) | **0.8745** | **0.8313** | **0.8524** | **0.7015** | **0.4235** | **0.4553** | 22 |

## Diagnostic & Operational Metrics

| Metric | Track A (Baseline) | Track B (Flagship) | Δ (B − A) |
| :--- | :---: | :---: | :---: |
| F1-Optimal Confidence Threshold | 0.8103 | 0.8039 | −0.0064 |
| Macro F1 (18-class unweighted mean) | 0.6285 | 0.7297 | +0.1012 |
| Macro Precision (18-class mean) | 0.6797 | 0.7709 | +0.0912 |
| Macro Recall (18-class mean) | 0.5903 | 0.6980 | +0.1077 |
| Class-Agnostic AP50 | 0.7985 | 0.8765 | +0.0780 |
| Classification Gap (Agnostic − AP50) | 0.1936 | 0.1750 | -0.0186 |
| Scale AP50: Small (area ≤ 32² px) | 0.4874 | 0.6064 | +0.1190 |
| Scale AP50: Medium (32²–96² px) | 0.5881 | 0.6783 | +0.0902 |
| Scale AP50: Large (area > 96² px) | 0.6602 | 0.8290 | +0.1688 |
| Orientation Error: Mean, All TP (deg) | 6.42° | 4.93° | -1.49° |
| Orientation Error: Median, All TP (deg) | 2.62° | 1.57° | -1.05° |
| Orientation Error: Mean, Elongated (AR ≥ 1.5) | 3.78° | 2.05° | -1.73° |
| Orientation Error: Median, Elongated (AR ≥ 1.5) | 2.55° | 1.47° | -1.08° |
| Easy GT Recall (non-difficult, n=69,542) | 0.7564 | 0.8313 | +0.0749 |
| Difficult GT Recall (flagged, n=70,561) | 0.2630 | 0.2978 | +0.0348 |
| Total Predictions (conf ≥ 0.05) | 180,555 | 129,046 | −51,509 |
| Model Parameters | not recorded | 70.24 M | — |
| Inference Throughput | 11.36 FPS (A100) | 5.70 FPS (RTX 4060) | — |
| Peak VRAM | 2.86 GiB (A100) | 4.20 GiB (RTX 4060) | — |

## Precision / Recall / F1 at Operating Points

| Conf Threshold | Track A Precision | Track A Recall | Track A F1 | Track B Precision | Track B Recall | Track B F1 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.25 | 0.5869 | 0.8351 | 0.6893 | 0.7416 | 0.8879 | 0.8082 |
| 0.30 | 0.6133 | 0.8310 | 0.7058 | 0.7563 | 0.8847 | 0.8155 |
| 0.50 | 0.6983 | 0.8148 | 0.7521 | 0.8023 | 0.8711 | 0.8353 |
| **F1-Optimal** | **0.8157** (thr=0.8103) | **0.7563** | **0.7849** | **0.8745** (thr=0.8039) | **0.8313** | **0.8524** |

## Per-Class AP50 Summary (Sorted by Gain)

| Class | n (GT) | Track A AP50 | Track B AP50 | Δ AP50 | Track B AP75 | Track B AP50-95 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| helipad | 4 | 0.0000 | 0.3333 | +0.3333 | 0.3333 | 0.2083 |
| harbor | 4,102 | 0.6067 | 0.8033 | +0.1966 | 0.3659 | 0.3970 |
| bridge | 745 | 0.3901 | 0.5689 | +0.1788 | 0.1451 | 0.2331 |
| basketball-court | 242 | 0.6067 | 0.7609 | +0.1542 | 0.6620 | 0.5631 |
| airport | 67 | 0.4492 | 0.6012 | +0.1520 | 0.0800 | 0.1931 |
| large-vehicle | 9,118 | 0.7296 | 0.8674 | +0.1378 | 0.6571 | 0.5518 |
| soccer-ball-field | 103 | 0.5525 | 0.6613 | +0.1088 | 0.5802 | 0.4866 |
| helicopter | 116 | 0.5346 | 0.6277 | +0.0931 | 0.1776 | 0.2749 |
| ship | 23,075 | 0.8237 | 0.9127 | +0.0890 | 0.6915 | 0.5696 |
| small-vehicle | 21,258 | 0.7653 | 0.8225 | +0.0572 | 0.4166 | 0.4411 |
| baseball-diamond | 357 | 0.6984 | 0.7521 | +0.0537 | 0.4152 | 0.4282 |
| roundabout | 278 | 0.7123 | 0.7633 | +0.0510 | 0.5261 | 0.4715 |
| ground-track-field | 192 | 0.7285 | 0.7691 | +0.0406 | 0.6528 | 0.5300 |
| swimming-pool | 1,195 | 0.6367 | 0.6669 | +0.0302 | 0.1158 | 0.2628 |
| plane | 3,976 | 0.9072 | 0.9321 | +0.0249 | 0.8008 | 0.6471 |
| tennis-court | 1,414 | 0.9385 | 0.9553 | +0.0168 | 0.9243 | 0.8228 |
| storage-tank | 3,273 | 0.8081 | 0.8222 | +0.0141 | 0.6503 | 0.5410 |
| container-crane | 27 | 0.0000 | 0.0066 | +0.0066 | 0.0000 | 0.0010 |
| **Mean (18 classes)** | **69,542** | **0.6049** | **0.7015** | **+0.0966** | **0.4553** | **0.4235** |
