# DOTA v2.0 Oriented Faster R-CNN Benchmark

Internship project (Aeronautical Development Agency): oriented (rotated) object
detection on the full 18-class **DOTA v2.0** dataset using the OpenMMLab
**MMRotate** framework. Two Faster R-CNN tracks were built, trained and
benchmarked under the `le90` oriented-bounding-box convention.

## Results at a glance

**Track B (flagship), epoch 24 — best checkpoint `best_dota_mAP_epoch_24.pth`**

| | dota/mAP | mAP50 | mAP50-95 | F1 | Precision | Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Track A (baseline) | 0.5412 | 0.6049 | 0.3146 | 0.7849 | 0.8157 | 0.7564 |
| **Track B (final)** | **0.6892** | **0.7064** | **0.4257** | **0.7264** | **0.8408** | **0.6394** |

Scale AP50 (small / medium / large): **0.601 / 0.758 / 0.878** · Angle error (elongated TPs): **2.50 deg** (mean) / 1.77 deg (median) · F1-optimal confidence: **0.518** · 2.60 img/s @ 8.98 GiB VRAM

Full write-up: [`docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf`](docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf)

- **Track A (baseline)** — Rotated Faster R-CNN, ResNet-50 + FPN, Smooth-L1 loss, 12 epochs.
- **Track B (flagship)** — Oriented R-CNN, ConvNeXt-Small + PAFPN, Gaussian KLD loss, ClassBalancedDataset, 24 epochs.

Training was run in two phases:

| Phase | Hardware | What happened |
| :--- | :--- | :--- |
| 1 | NVIDIA A100-SXM4-80GB (Colab) | Track A (12 ep) + Track B epochs 1–16; Track B reached 0.6883 dota/mAP |
| 2 | 2× NVIDIA Tesla T4 (Kaggle, 12h sessions) | Track B epochs 17–24, resumed from the saved epoch-16 checkpoint; final evaluation |

## Final results (Phase-2 Kaggle evaluation)

Validation split, 5,297 tiled 1024×1024 patches, 120,013 non-difficult GT instances.

| Metric | Track A (baseline) | Track B (flagship, epoch 24) |
| :--- | :---: | :---: |
| Official dota/mAP (18-class macro) | 0.5412 | **0.6892** |
| Extended evaluator mAP50 | 0.6049 | **0.7064** |
| Strict mAP50-95 | 0.3146 | **0.4257** |
| AP75 | 0.2785 | **0.4489** |
| Precision (F1-optimal, conf = 0.518) | 0.8157 | **0.8408** |
| Recall (F1-optimal, conf = 0.518) | 0.7564 | **0.6394** |
| F1-score (F1-optimal, conf = 0.518) | 0.7849 | **0.7264** |
| Scale AP50 (small/med/large) | 0.4875 / 0.5882 / 0.6602 | **0.6005 / 0.7582 / 0.8783** |
| Mean angle error (all TPs) | 3.78 deg (mean, Phase-1 A100) | **4.77 deg mean / 1.85 deg median** |
| Mean angle error (elongated TPs) | 2.55 deg (median, Phase-1 A100) | **2.50 deg mean / 1.77 deg median** |
| Easy / Difficult GT recall | 0.7565 / 0.2631 | **0.6395 / 0.7377** |
| F1-optimal confidence threshold | — | 0.518 |
| Validation throughput | 17.38 FPS | 2.60 FPS |
| Peak GPU memory | 28.04 GiB | 8.98 GiB |

**Phase-1 vs Phase-2 numbers.** Track A metrics and the per-class Track A column were measured in Phase 1 (A100, 7,122-patch tiling). Track B metrics in this repo are the Phase-2 results (5,297-patch tiling). The two tilings differ, so treat Track A / Track B cross-tiling deltas as approximate. Airport and helipad have **zero validation instances** in the Phase-2 tiling; their Track B AP50 is 0.0 (reported as such, not hidden).

## Per-class breakdown (AP50, recall @ F1-optimal)

Track A = Phase 1 (A100). Track B = Phase 2 (Kaggle, `best_dota_mAP_epoch_24`).

| Class | Track A (AP / Recall) | Track B (AP / Recall) | ΔAP |
| :--- | :---: | :---: | :---: |
| plane | 0.809 / 0.876 | **0.925 / 0.895** | +0.116 |
| baseball-diamond | 0.664 / 0.858 | **0.845 / 0.832** | +0.181 |
| bridge | 0.374 / 0.586 | **0.568 / 0.598** | +0.194 |
| ground-track-field | 0.690 / 0.883 | **0.793 / 0.781** | +0.103 |
| small-vehicle | 0.417 / 0.492 | **0.499 / 0.523** | +0.082 |
| large-vehicle | 0.676 / 0.802 | **0.832 / 0.767** | +0.156 |
| ship | 0.776 / 0.801 | **0.910 / 0.884** | +0.134 |
| tennis-court | 0.901 / 0.934 | **0.948 / 0.931** | +0.047 |
| basketball-court | 0.596 / 0.702 | **0.747 / 0.698** | +0.151 |
| storage-tank | 0.600 / 0.638 | **0.653 / 0.637** | +0.053 |
| soccer-ball-field | 0.536 / 0.745 | **0.646 / 0.642** | +0.110 |
| roundabout | 0.603 / 0.778 | **0.748 / 0.722** | +0.145 |
| harbor | 0.552 / 0.697 | **0.842 / 0.826** | +0.290 |
| swimming-pool | 0.556 / 0.681 | **0.652 / 0.681** | +0.096 |
| helicopter | 0.542 / 0.633 | **0.663 / 0.559** | +0.121 |
| container-crane | 0.000 / 0.000 | **0.033 / 0.074** | +0.033 |
| airport | 0.450 / 0.598 | **0.000 / 0.000** | -0.450 |
| helipad | 0.000 / 0.000 | **0.000 / 0.000** | 0.000 |

Standalone benchmark output: [`results/final_benchmark_report.md`](results/final_benchmark_report.md), [`results/extended_metrics.json`](results/extended_metrics.json)

## Precision / Recall / F1 at fixed confidence thresholds

| Conf | Precision | Recall | F1 | TP | FP | FN |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.25 | 0.786 | 0.662 | 0.718 | 79,415 | 21,655 | 40,598 |
| 0.30 | 0.798 | 0.658 | 0.721 | 78,970 | 20,030 | 41,043 |
| 0.50 | 0.837 | 0.641 | 0.726 | 76,952 | 14,943 | 43,061 |
| **0.518 (F1-opt)** | **0.841** | **0.639** | **0.726** | 76,742 | 14,528 | 43,271 |

## Repository layout

```
configs/                    MMRotate config files (tracks A & B) + DOTA v2 class list
scripts/                    data download/tiling, training launcher, evaluation, metrics
tests/                      pytest suite (uv run pytest)
results/                    final benchmark report + extended metrics + training logs
docs/                       internship report (PDF + DOCX)
artifacts/                  (gitignored) model checkpoints, kept local only
SPEC_PLAN.md                design rationale
```

## Running

### Local (CPU only; GPUs are not required for checks)

```bash
uv venv --python 3.11
uv sync
uv run pytest
```

### Kaggle (GPU pipeline, `scripts/run_kaggle.py`)

1. Attach DOTA v2.0 raw archives to the Kaggle input folder (see `scripts/download_dotav2.py`).
2. Run the notebook `colab_runner.ipynb` (or the equivalent Kaggle cell:
   `git clone <repo> && python3 -u scripts/run_kaggle.py`).
3. Steps executed: verify GPUs → provision Python 3.11 OpenMMLab venv via `uv`
   (`scripts/setup_colab.sh`) → patch mmrotate losses → stage epoch_16.pth
   checkpoint (from Google Drive, resume) → download + tile the dataset →
   distributed `torchrun` training (2×T4) → extended evaluation + benchmark report.
4. `scripts/run_kaggle.py` is idempotent: re-running it resumes MMEngine from the
   latest `last_checkpoint` (checkpoint meta carries `epoch`/`iter`).

### Resumability / crash-recovery

- Checkpoints every epoch (`CheckpointHook interval=1`, keep best 3 by `dota/mAP`).
- `scripts/run_kaggle.py` re-derives the dataset deterministically on every fresh
  session (download → tile → clone), so a fresh kernel can always resume.
- Phase 2 was executed exactly this way after two Kaggle kernel restarts; resume
  epochs re-derived from `epoch_16.pth` → `epoch_17` → … → `epoch_24`.

## Results & artifacts

- `results/final_benchmark_report.md` — Track A vs Track B scorecard, per-class AP50.
- `results/extended_metrics.json` — full machine-readable metrics (per-class AP50/AP75/mAP50-95,
  micro PRF at multiple confidence thresholds, scale-bucketed AP, angle errors, FPS, VRAM).
- `results/logs/` — mmengine logs for Phase 2 (`2026-11-15_track_b_final_epochs_17-24.log`).

**Model checkpoints** (~850 MB each) are intentionally excluded from this repo
(`artifacts/checkpoints/`, gitignored) and are available on request. The Phase-1
epoch-16 checkpoint lives on the project Google Drive (`epoch_16.pth`) and the
Phase-2 `epoch_19` resume checkpoint lives in the private Kaggle dataset
`ssgokulaswamy/ada-trackb-epoch19`.

## Known limitations / caveats

- Airport and helipad received 0 annotations in the Phase-2 validation tiling
  (0 ground-truth instances); their AP50 is reported as 0.0.
- Track A metrics are Phase-1 numbers (different validation tiling); deltas across
  phases are approximate. Official `dota/mAP` uses the difficult-instance-excluded
  18-class macro mean from MMRotate.
- `epoch_20.pth` was pruned on Kaggle by the `max_keep_ckpts=3` checkpoint hook
  before it could be archived. Its validation result (0.6879 dota/mAP) is recorded
  in the logs. All other epoch checkpoints (16–24) and `best_dota_mAP_epoch_24.pth`
  are preserved locally under `artifacts/checkpoints/`.
- Kaggle interactive sessions are idle-terminated and have a 12-hour limit; this is
  why the pipeline is built around deterministic re-provisioning and per-epoch resume.

## Acknowledgements

Built with OpenMMLab (MMCV, MMDetection, MMRotate), PyTorch, and the DOTA v2.0
benchmark. Trained on Kaggle Notebooks (2×Tesla T4) and NVIDIA A100.
