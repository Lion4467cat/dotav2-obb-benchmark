# DOTA v2.0 Oriented Faster R-CNN Benchmark

Internship project (Aeronautical Development Agency): oriented (rotated) object
detection on the full 18-class **DOTA v2.0** dataset using the OpenMMLab
**MMRotate** framework. Two Faster R-CNN tracks were built, trained and
benchmarked under the `le90` oriented-bounding-box convention.

## Dataset access and license

This repository contains the preparation and evaluation code, not the DOTA
image archives. Obtain DOTA v2.0 from the [official DOTA dataset page](https://captain-whu.github.io/DOTA/dataset.html)
and follow its academic-use terms and the image-source terms. Local archives,
tiles, and annotations are intentionally excluded from GitHub.

## Results at a glance

**Track B (flagship), epoch 24 — final checkpoint `epoch_24.pth`**
Official DOTA v2.0 val split (593 images, 7,122 patches, 18 classes). Full
24-epoch budget completed on the official dataset.

| | dota/mAP (mmengine) | mAP50 (ext, d0) | mAP50-95 | F1 | Precision | Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Track A (baseline) | 0.5412 | 0.6049 | 0.3146 | 0.7849 | 0.8157 | 0.7564 |
| **Track B (official val, epoch 24)** | **0.6535** | **0.7127** | **0.4320** | **0.8511** | **0.8694** | **0.8335** |

Scale AP50 (small / medium / large): **0.622 / 0.683 / 0.839** · Angle error (elongated TPs): **2.05 deg** (mean) / 1.46 deg (median) · F1-optimal confidence: **0.834** · evaluation: 2.52 img/s @ 9.25 GiB peak VRAM (Kaggle 2×T4, batch 1) · 70.2 M parameters

Full write-up: [`docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf`](docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf)

- **Track A (baseline)** — Rotated Faster R-CNN, ResNet-50 + FPN, Smooth-L1 loss, 12 epochs.
- **Track B (flagship)** — Oriented R-CNN, ConvNeXt-Small + PAFPN, Gaussian KLD loss, ClassBalancedDataset, 24 epochs.

Training ran in two phases, with the second phase split across two Kaggle sessions:

| Phase | Hardware | What happened |
| :--- | :--- | :--- |
| 1 | NVIDIA A100-SXM4-80GB (Colab) | Track A (12 ep) + Track B epochs 1–16; official data (HuggingFace) |
| 2a | 2× NVIDIA Tesla T4 (Kaggle, 12h session) | Track B official retrain epochs 17–22, resumed from the epoch-16 checkpoint; session hit the 12-hour cap during epoch-22 validation |
| 2b | 2× NVIDIA Tesla T4 (Kaggle) | Resumed from `epoch_22.pth` (official retrain), completed epochs 23–24, with epoch-24 validation and final evaluation |
| Eval | Kaggle (2×T4) + local cross-check | Official-val evaluation of the saved `epoch_24.pth` (see [Data source correction](#data-source-correction)) |

## Final results (official val evaluation)

Official DOTA v2.0 val split, 593 images → 7,122 tiled 1024×1024 patches,
81,048 instances (69,542 non-difficult, 70,561 difficult). Track A = Phase 1
(A100, same tiling). Track B = the official-val evaluation of the final
`epoch_24.pth` checkpoint, run on Kaggle (2×T4) in the epoch-24 finish notebook.

| Metric | Track A (baseline) | Track B (flagship, epoch 24) |
| :--- | :---: | :---: |
| Official dota/mAP (mmengine, 18-class macro, diff-included) | 0.5412 | **0.6535** |
| Extended evaluator mAP50 (non-difficult GT) | 0.6049 | **0.7127** |
| Strict mAP50-95 | 0.3146 | **0.4320** |
| AP75 | 0.2785 | **0.4664** |
| Precision (F1-optimal, conf = 0.834) | 0.8157 | **0.8694** |
| Recall (F1-optimal, conf = 0.834) | 0.7564 | **0.8335** |
| F1-score (F1-optimal, conf = 0.834) | 0.7849 | **0.8511** |
| Scale AP50 (small/med/large) | 0.4874 / 0.5881 / 0.6602 | **0.6220 / 0.6826 / 0.8394** |
| Mean angle error (all TPs) | 6.42 deg mean / 2.62 deg median | **4.88 deg mean / 1.56 deg median** |
| Mean angle error (elongated TPs) | 3.78 deg mean / 2.55 deg median | **2.05 deg mean / 1.46 deg median** |
| Easy / Difficult GT recall | 0.7565 / 0.2631 | **0.8335 / 0.3019** |
| F1-optimal confidence threshold | — | 0.834 |
| Predictions (conf ≥ 0.05) | 180,555 | 136,612 |
| Validation throughput | 17.38 FPS (Phase 1) | 2.52 img/s (Kaggle 2×T4, batch 1) |
| Peak GPU memory | 28.04 GiB (Phase 1) | 9.25 GiB (Kaggle 2×T4) |

**Two mAP conventions.** mmengine `DOTAMetric` reports `dota/mAP: 0.6535`
(18-class macro, IoU 0.5, `diff_thr=100` — includes difficult GT; identical in
the in-training validation and the final `test.py` pass). The extended
evaluator reports `mAP50: 0.7127` on non-difficult GT only. Both conventions
were used in Phase 1; the extended d0-only number is the apples-to-apples
comparison vs Track A. **Difficult recall** (0.3019) is measured against 70,561
officially-difficult instances — genuinely tiny, occluded, or ambiguous boxes.
The metrics here are from labeled validation data; no hidden-label DOTA server
score is claimed.

## Per-class breakdown (AP50, recall @ F1-optimal)

Track A = Phase 1 (official val, A100). Track B = official val, the epoch-24 checkpoint (`epoch_24.pth`).
Extended evaluator, non-difficult GT. #GT = non-difficult occurrences.

| Class | #GT | Track A (AP / Recall) | Track B (AP / Recall) | ΔAP |
| :--- | :---: | :---: | :---: | :---: |
| plane | 3,976 | 0.907 / 0.858 | **0.942 / 0.914** | +0.035 |
| baseball-diamond | 357 | 0.698 / 0.661 | **0.778 / 0.815** | +0.080 |
| bridge | 745 | 0.390 / 0.467 | **0.572 / 0.616** | +0.182 |
| ground-track-field | 192 | 0.729 / 0.714 | **0.802 / 0.781** | +0.073 |
| small-vehicle | 21,258 | 0.765 / 0.763 | **0.826 / 0.816** | +0.060 |
| large-vehicle | 9,118 | 0.730 / 0.719 | **0.869 / 0.789** | +0.140 |
| ship | 23,075 | 0.824 / 0.802 | **0.917 / 0.892** | +0.093 |
| tennis-court | 1,414 | 0.939 / 0.898 | **0.954 / 0.930** | +0.016 |
| basketball-court | 242 | 0.607 / 0.612 | **0.755 / 0.694** | +0.148 |
| storage-tank | 3,273 | 0.808 / 0.754 | **0.825 / 0.802** | +0.017 |
| soccer-ball-field | 103 | 0.552 / 0.447 | **0.672 / 0.602** | +0.120 |
| roundabout | 278 | 0.712 / 0.705 | **0.771 / 0.788** | +0.059 |
| harbor | 4,102 | 0.607 / 0.638 | **0.797 / 0.778** | +0.190 |
| swimming-pool | 1,195 | 0.637 / 0.589 | **0.664 / 0.675** | +0.028 |
| helicopter | 116 | 0.535 / 0.552 | **0.638 / 0.552** | +0.103 |
| container-crane | 27 | 0.000 / 0.000 | **0.015 / 0.074** | +0.015 |
| airport | 67 | 0.449 / 0.448 | **0.614 / 0.702** | +0.165 |
| helipad | 4 | 0.000 / 0.000 | **0.417 / 0.500** | +0.417 |

**Low-support classes.** Container-crane (27 GT), airport (67), and helipad (4)
have very few instances; their AP should be interpreted cautiously.

Standalone benchmark output: [`results/final_benchmark_report.md`](results/final_benchmark_report.md), [`results/extended_metrics.json`](results/extended_metrics.json)

## Precision / Recall / F1 at fixed confidence thresholds

Track B, official val, extended evaluator (non-difficult GT):

| Conf | Precision | Recall | F1 | TP | FP | FN |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.25 | 0.715 | 0.896 | 0.796 | 62,311 | 24,795 | 7,231 |
| 0.30 | 0.730 | 0.893 | 0.803 | 62,105 | 22,964 | 7,437 |
| 0.50 | 0.781 | 0.881 | 0.828 | 61,244 | 17,141 | 8,298 |
| **0.834 (F1-opt)** | **0.869** | **0.834** | **0.851** | 57,961 | 8,707 | 11,581 |

## Repository layout

```
configs/                    MMRotate configs (Track A / Track B) + canonical DOTA v2 classes
scripts/                    data download/tiling, training launcher, evaluation, metrics
dota_obb/                   installable inference package (load_model / predict / download)
tests/                      pytest suite (uv run pytest)
results/                    benchmark report + extended metrics + training logs + Task 1 files
docs/                       internship report (PDF + DOCX), figures, demo media
colab_runner.ipynb          Colab pipeline notebook (generated by scripts/build_colab_notebook.py)
artifacts/                  (gitignored) model checkpoints, kept local only
SPEC_PLAN.md                design rationale
CHANGELOG.md                release / fix history
```

## Local inference UI (Track B)

Lightweight Gradio UI that runs the published Track B model on your machine.
Inference needs the OpenMMLab stack (torch 2.0.1+cu118, mmcv 2.0.1, mmdet 3.1.0,
mmrotate dev-1.x); `scripts/setup_colab.sh` provisions exactly that environment
and also works on a local Linux machine:

```bash
bash scripts/setup_colab.sh "$PWD" "$HOME/mmrotate_venv"
"$HOME/mmrotate_venv/bin/python" -m pip install -e ".[ui]"   # adds gradio
"$HOME/mmrotate_venv/bin/python" scripts/gradio_app.py       # http://127.0.0.1:7860
```

The package reads its config from the checkout, so install it editable
(`-e`) from this repository rather than from a wheel.

Upload any aerial image (or a tiled 1024x1024 patch), tune the confidence threshold,
and the app draws le90 oriented boxes with class + score labels on the result.
Inference is single image, GPU-accelerated (RTX 4060: ~0.35 s/image) with CPU fallback.
The app includes three real DOTA validation tiles covering planes, vehicles, courts,
and helicopters. Its slider defaults to 0.52, a UI-friendly confidence threshold
for interactive visualization (the validation F1-optimal threshold is 0.834).

### Live demo video

This live Track B run selects a real validation tile, opens **Settings**, and shows
the checkpoint's predictions: 112 detections across three classes at confidence
0.52. The player below is the recorded browser demo. You can also [download the MP4 from this repository](docs/demo/live_track_b_demo.mp4).

[▶ Play the recorded demo in your browser](https://github.com/user-attachments/assets/3fbe5d80-5f6d-4750-9ed3-69e58ebc5a4d)

Example Track B predictions from the saved epoch-24 checkpoint:

![Track B oriented detections on aerial images, with multiple predicted classes](docs/figures/track_b_demo_predictions.png)

## Download the model

| Asset | Release | SHA-256 | Notes |
| :--- | :--- | :--- | :--- |
| `epoch_24.pth` | **v1.3.0** | `d855c250387f7e3f3fbc6b1a2a79a05932a1e11c39e855563c961f5aaa44995f` | **Canonical** — official retrain, 24 epochs; the model behind every epoch-24 number in this README |
| `epoch_24.pth.sha256` | **v1.3.0** | — | checksum sidecar, verified by `dota_obb.download` |
| `epoch_16.pth` | v1.3.0 | `997c52283a66bdf419b58ed7bf4916c210c28ad153adf0963ad80d54f4ff10ed` | Phase-1 anchor (official data; kept for resume reproduction) |

The canonical Track B model is the **official-retrain `epoch_24.pth`**
(SHA-256 above, 858 MB), produced on Kaggle by resuming from the epoch-22
checkpoint (official 18-class DOTA v2.0, difficulty flags preserved) and
completing epochs 23–24. The earlier release weights (the initial release,
later mislabelled as the flagship) came from the **pre-correction lineage** —
the initial Kaggle continuation trained on a non-official convenience archive
(458 val images, 16 classes, stripped difficulty flags; see [Data source correction](#data-source-correction)).
Their assets were **removed from the GitHub releases on 2026-11-18** and the
initial release's notes were updated to say so; those weights are unavailable
for download. `v1.3.0` is the first release built entirely on official data
with matching evaluation provenance.

`dota_obb.download` and the Gradio UI load the **v1.3.0** asset (`epoch_24.pth`)
and verify it against the SHA-256 above before use.

Checkpoint status:

| Checkpoint | |
| :--- | :--- |
| `epoch_24.pth` (v1.3.0 release and `artifacts/checkpoints/`) | **Canonical** |
| `epoch_23.pth` (local only) | Resume-only intermediate; local only |
| `best_dota_mAP_epoch_22.pth` (local only) | Phase-2a resume anchor for the epoch-23/24 run; local only |
| `epoch_16.pth` (v1.3.0 release asset) | Phase-1 anchor; official data; kept for resume reproduction |
| `epoch_20.pth` | Never archived (pruned on Kaggle by `max_keep_ckpts=3`) |

Programmatic download (cached under `~/.cache/dota_obb/`):

```bash
python -m dota_obb.download
```

or use the package directly:

```python
from dota_obb import load_model, predict
model = load_model()                       # auto-downloads if not local
result = predict(image_bgr, score_thr=0.3) # detections + annotated image
```

## Running

### Local (CPU only; GPUs are not required for checks)

```bash
uv venv --python 3.11
uv sync
uv run pytest
```

### Kaggle (GPU pipeline, official retrain and finish notebooks)

Two Kaggle notebooks cover the official-data continuation, both generated from
this repository's scripts:

1. `colab/trackB_official_retrain_kaggle.ipynb` — resumes Track B at epoch 16,
   downloads the official DOTA v2.0 data, re-tiles, trains epochs 17–24, evaluates.
   Stage 2a used this notebook (session hit the 12-hour cap during epoch-22 validation).
2. `colab/trackB_official_finish_ep23_24_kaggle.ipynb` — resumes from `epoch_22.pth`,
   trains epochs 23–24 on 2×T4, validates at epoch 24, runs the extended evaluation
   and packages deliverables. Stage 2b used this notebook; outputs (epoch_23/24.pth,
   logs, `extended_metrics.json`, `preds.pkl`, `manifest.json`) are in
   `results/trackb_official_ep23_24/`.

Both provision the Python 3.11 OpenMMLab venv via `uv` (`scripts/setup_colab.sh`),
patch mmrotate losses, tile the official data with the standard 1024/200 recipe,
and verify patch counts before training (train ≥ 24,000 patches; val == 7,122).

### Resumability / crash-recovery

- Checkpoints every epoch (`CheckpointHook interval=1`, `max_keep_ckpts=3`,
  `save_best='dota/mAP'`).
- Fresh kernels can always resume: the dataset is re-derived deterministically
  and `epoch_22.pth` is attached as a Kaggle dataset (`ada-trackb-epoch22`).
- Phase 2 was executed exactly this way after two Kaggle kernel restarts:
  resume epochs re-derived from `epoch_16.pth` → `epoch_17` → … → `epoch_22`
  (first session), then `epoch_22.pth` → `epoch_23` → `epoch_24` (resumed session).
- The epoch-23/24 run inherits the pre-correction `message_hub` best-score
  tracker (0.6883, recorded on the non-official tiling); no post-resume
  validation exceeded it, so no best-checkpoint file was produced. The
  final model is `epoch_24.pth`, used directly for evaluation.

## Results & artifacts

- `results/trackb_official_ep23_24/` — the epoch-23/24 official-retrain run:
  training log, `scalars.json`, `train_cfg_ep23_24.py`, `eval_cfg.py`,
  `eval_test/extended_metrics.json`, `preds.pkl`, deliverables manifest.
- `results/final_benchmark_report.md` — Track A vs Track B scorecard, per-class AP50, data source correction.
- `results/extended_metrics.json` — full machine-readable metrics (official val, 7,122 patches):
  per-class AP50/AP75/mAP50-95, micro PRF at multiple confidence thresholds, scale-bucketed AP,
  angle errors, difficulty recall, FPS, VRAM.
- `results/logs/` — mmengine logs: Phase 2 (`2026-11-15_track_b_final_epochs_17-24.log`),
  official-val re-evaluation (`2026-11-15_track_b_restored_validation_rerun.log`),
  and the epoch-23/24 official run (`2026-11-18_track_b_epochs_23-24_kaggle.log`).

**Model checkpoints** (~850 MB each) are excluded from this repo
(`artifacts/checkpoints/`, gitignored); the canonical local set is
`epoch_16.pth` (Phase-1 anchor), `epoch_22.pth` / `best_dota_mAP_epoch_22.pth`
(byte-identical, Phase-2a end), and `epoch_23.pth` / `epoch_24.pth` (Phase-2b).
The v1.3.0 release carries `epoch_24.pth`; the pre-correction release assets were
removed on 2026-11-18 (see [Download the model](#download-the-model)).

## Known limitations / caveats

- Official `dota/mAP` uses the difficult-instance-included 18-class macro mean
  from MMRotate (`diff_thr=100`); the extended evaluator's `mAP50` is computed
  on non-difficult GT only. Both conventions are reported.
- Container-crane (27 GT), airport (67), and helipad (4) have very few val
  instances; their AP should be interpreted cautiously. Airport's AP75 of 0.083
  suggests large polygons may fail the >=70% IoF tiling rule — multi-scale tiling
  would likely help.
- Track A metrics were re-evaluated with its epoch-10 best checkpoint on the
  identical 7,122-patch official tiling; the aggregates reproduce the Phase-1
  numbers (mAP50 0.6049, mAP50-95 0.3146). Track B metrics are the official-val
  evaluation of the epoch-24 checkpoint on the same tiling (Kaggle 2×T4).
- The epoch-23/24 Kaggle run resumed from the official-retrain `epoch_22.pth`;
  the resumed run inherits the pre-correction `message_hub` best-score tracker
  (0.6883, non-official tiling), so no best-checkpoint file was produced, and
  none is needed: `epoch_24.pth` is the final artifact and all reported metrics use it. Validation at epochs 18/20/22/24 ran
  on the official tiling (dota/mAP: 0.6453 / 0.6519 / 0.6366* / 0.6535);
  *epoch-22's in-training validation was cut by the 12-hour session limit, so
  its number is the local official-val evaluation pass.
- `epoch_20.pth` was pruned on Kaggle by the `max_keep_ckpts=3` checkpoint hook
  before it could be archived. Its validation result (0.6879 dota/mAP) is recorded
  in the logs.
- Kaggle interactive sessions are idle-terminated and have a 12-hour limit; this is
  why the pipeline is built around deterministic re-provisioning and per-epoch resume.

## Data source correction

The initial Phase-2 Kaggle run (epochs 17–24) used `--source ultralytics`,
fetching `DOTAv2.zip` from the yolov5 v1.0 GitHub release. That archive is **not
official DOTA v2.0**: it ships only 458 of the 593 official val images with 16-class
YOLO labels (no airport/helipad) and stripped difficulty flags. Phase 1 was
unaffected because the Colab notebook used `DATA_SOURCE = 'huggingface'`
(isaaccorley/dota — official v2.0, 593 val images).

The correction was a full official-data retrain of Track B from the epoch-16
checkpoint, using the HuggingFace official archives (merged v1.0 + v2.0 official
imagery, 18 classes, difficulty flags preserved), re-tiled with the same
1024/200 recipe. The first Kaggle retrain (`ssgokulaswamy/trackb-official-retrain`)
completed epochs 17–22 before the 12-hour session cap cut the epoch-22
validation. A resumed session (`bhaghwanss/trackb-finish-ep23-24`) completed
epochs 23–24 with a clean epoch-24 validation and full official-val evaluation —
no weights, losses, optimizer state or seeds were changed relative to the first
retrain; only the epoch range differs. The pre-correction Phase-2 numbers are
retained in the [report appendix](results/final_benchmark_report.md#appendix-phase-2-superseded)
for traceability.

## Acknowledgements

Built with OpenMMLab (MMCV, MMDetection, MMRotate), PyTorch, and the DOTA v2.0
benchmark. Trained on Kaggle Notebooks (2×Tesla T4) and NVIDIA A100.
