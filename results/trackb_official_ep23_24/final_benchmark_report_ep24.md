# DOTA v2.0 Final Benchmark Report (Official Full Run: 24 Epochs)

## Run Details
- Dataset: Official DOTA v2.0 (1,830 train / 593 val, 7,122 patches, 18 classes, difficulty flags preserved)
- Model: Oriented Faster R-CNN (ConvNeXt-S + PAFPN + Gaussian KLD loss)
- Schedule: 2x (24 Epochs complete)

## Core Metrics Comparison

| Model / Milestone | Precision (F1-opt) | Recall (F1-opt) | F1-Score | mAP50 | mAP50-95 | AP75 | Epoch |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Reference Target | 0.7430 | 0.5670 | 0.6432 | 0.5970 | 0.4210 | — | — |
| Track A (Baseline R50 1x) | 0.8157 | 0.7563 | 0.7849 | 0.6049 | 0.3146 | 0.2785 | 10 |
| Track B (Epoch 22 Milestone) | 0.8745 | 0.8313 | 0.8524 | 0.7015 | 0.4235 | 0.4553 | 22 |
| **Track B (Epoch 24 Final)** | **0.8694** | **0.8335** | **0.8511** | **0.7127** | **0.4320** | **0.4664** | **24** |

## Diagnostic Metrics
- Class-Agnostic AP50: 0.8803
- Classification Gap: 0.1676
- Orientation Error (Mean): 0.00°
- Orientation Error (Median): 0.00°
- Easy GT Recall: 0.8335
- Difficult GT Recall: 0.3019
