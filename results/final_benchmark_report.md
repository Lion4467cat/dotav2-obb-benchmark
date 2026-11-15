# DOTA v2.0 Benchmark Report (`val` split, OBB `le90`)

## Core Metrics vs Target Reference

| Model / Reference | Precision (F1-opt) | Recall (F1-opt) | F1-score | mAP50 | mAP50-95 | AP75 | Best Step |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Reference Target (User Provided) | `0.7430` | `0.5670` | `0.6432` | `0.5970` | `0.4210` | — | — |
| Track B: Oriented Faster R-CNN (ConvNeXt-S + PAFPN + KLD, 2x) | 0.8408 | 0.6394 | 0.7264 | **0.7064** | 0.4257 | 0.4489 | 24 |

## OBB-Specific Diagnostic & Operational Metrics

| Metric | Track A (Baseline) | Track B (Flagship) |
| :--- | :---: | :---: |
| F1-Optimal Conf Threshold | — | 0.5180 |
| Macro Precision (18-class mean) | — | 0.8054 |
| Macro Recall (18-class mean) | — | 0.6906 |
| Precision @ conf=0.30 | — | 0.7977 |
| Recall @ conf=0.30 | — | 0.6580 |
| Precision @ conf=0.50 | — | 0.8374 |
| Recall @ conf=0.50 | — | 0.6412 |
| Scale AP50: Small (< 32^2 px^2) | — | 0.6005 |
| Scale AP50: Medium (32^2..96^2) | — | 0.7582 |
| Scale AP50: Large (> 96^2 px^2) | — | 0.8783 |
| Class-Agnostic Localization AP50 | — | 0.6494 |
| Classification Confusion Gap | — | 0.0000 |
| Mean Angle Error - All TPs | — | 4.77 deg |
| Mean Angle Error - Elongated (AR>=1.5) | — | 2.50 deg |
| Easy GT Recall (difficult=0) | — | 0.6395 |
| Difficult GT Recall (difficult=1) | — | 0.7377 |
| Validation Throughput | — | 2.60 img/s |
| Model Parameters | — | — |
| Peak GPU Memory | — | 8.98 GiB |

## Per-Class AP@0.5 Breakdown

| Class | Track A AP50 | Track B AP50 | Delta AP50 | Track A AP50-95 | Track B AP50-95 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `plane` | — | 0.9253 | — | — | 0.6403 |
| `baseball-diamond` | — | 0.8449 | — | — | 0.4667 |
| `bridge` | — | 0.5683 | — | — | 0.2366 |
| `ground-track-field` | — | 0.7926 | — | — | 0.5476 |
| `small-vehicle` | — | 0.4986 | — | — | 0.2366 |
| `large-vehicle` | — | 0.8323 | — | — | 0.5218 |
| `ship` | — | 0.9098 | — | — | 0.5701 |
| `tennis-court` | — | 0.9480 | — | — | 0.8162 |
| `basketball-court` | — | 0.7465 | — | — | 0.5430 |
| `storage-tank` | — | 0.6528 | — | — | 0.4169 |
| `soccer-ball-field` | — | 0.6458 | — | — | 0.4073 |
| `roundabout` | — | 0.7479 | — | — | 0.4512 |
| `harbor` | — | 0.8422 | — | — | 0.4218 |
| `swimming-pool` | — | 0.6515 | — | — | 0.2606 |
| `helicopter` | — | 0.6630 | — | — | 0.2677 |
| `container-crane` | — | 0.0327 | — | — | 0.0075 |
| `airport` | — | 0.0000 | — | — | 0.0000 |
| `helipad` | — | 0.0000 | — | — | 0.0000 |
