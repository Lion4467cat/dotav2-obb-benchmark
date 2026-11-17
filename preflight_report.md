# Preflight report — Track B official retrain, epochs 17–24

**Date:** 2026-11-16
**Scope:** resume Track B (Oriented R-CNN, ConvNeXt-S + PAFPN, Gaussian KLD, ClassBalancedDataset)
at epoch 16 and train epochs 17–24 on official DOTA v2.0 data, then re-evaluate on the official
7,122-patch validation tiling.

**Verdict: CONDITIONAL GO.** Four of the five preflight items pass with evidence. Two blockers were
found, both environmental rather than methodological: (1) no official training tiling exists on this
machine and 419 of the 1,830 training images are absent; (2) this session has no Google Colab runtime
and no browser/CDP bridge, so the job cannot be started from here.

Resolution agreed: the job runs from a self-contained notebook
(`colab/trackB_official_retrain.ipynb`) that the author runs on Colab. The notebook performs the
download, the one-time tiling, the resume, the training, the evaluation and the arithmetic checks
itself, so the two blockers are handled inside the run rather than before it.

---

## 1. Checkpoint state — PASS

`artifacts/checkpoints/epoch_16.pth` (849 MB, 2026-11-14 23:25)

| Item | Value |
|---|---|
| Top-level keys | `meta`, `state_dict`, `message_hub`, `optimizer`, `param_schedulers` |
| Epoch / iteration | 16 / 26,274 |
| Optimizer state | 390 parameter-state tensors, 1 param group (AdamW) |
| Scheduler state | LinearLR warmup (500 iters, start_factor 0.001, completed) + CosineAnnealingLR |
| Cosine state | `T_max=24`, `eta_min=1e-6`, `base=1e-4`, `last_step=16`, `_last_value=2.575e-05` |
| Seed | 1143503445 |
| Experiment name | `benchmark_oriented_faster_rcnn_convnext_s_pafpn_kld_2x_dotav2_20261114_082341` |

The stored cosine value 2.575e-05 is exactly `1e-6 + (1e-4 − 1e-6)·(1 + cos(π·16/24))/2`, so the
optimizer and scheduler state are internally consistent with epoch 16. A true resume is possible.

`epoch_20.pth` in the same directory is **9 bytes** and is not a checkpoint. It is part of the
contaminated run and must not be used for anything.

## 2. Provenance of epoch 16 — PASS

The config embedded in the checkpoint (`meta['cfg']`, 27,890 characters) records:

- `data_root = '/content/data/split_ss_dotav2/'`, `ann_file='train/annfiles/'`
- `dataset_meta.classes` = all **18** classes, in the standard order, including airport, helipad
  and container-crane.
- `train_cfg = EpochBasedTrainLoop(max_epochs=24, val_interval=2)`
- 26,274 iterations after 16 epochs → 1,642 iterations per epoch → **13,136 patches per epoch** at
  an effective batch of 8.
- 1,830 official trainval images × 7.18 patches per image = 13,139. The iteration count therefore
  matches the official 1,830-image trainval tiling and not any smaller set.

**Conclusion:** epochs 1–16 trained on the official 18-class trainval tiling. The contamination
starts at epoch 17, where the continuation switched to the Ultralytics archive.

## 3. Data verification — PARTIAL PASS (train tiling missing)

### 3.1 Official validation tiling — PASS

`.task-data/official_val/split_ss/val/`: 593 source images → **7,122 patches** (images and annfiles).

| Quantity | Measured | Required | Status |
|---|---|---|---|
| Patches | 7,122 | 7,122 | PASS |
| Non-difficult annotations | 69,542 | 69,542 | PASS |
| Difficulty-flagged annotations | 70,561 (66,178 flag-1 + 4,383 flag-2) | 70,561 | PASS |
| Classes | 18 | 18 | PASS |
| Total annotations | 140,103 | 140,103 | PASS |

### 3.2 Official training annotations — PASS (downloaded during preflight)

`.task-data/official_train/raw_archives/train/train/annotations/version2.0/` — 1,830 files,
268,627 instances, difficulty flags preserved (141,708 flag-0, 126,919 flag-1), 18 classes:

| Class | Instances | Class | Instances |
|---|---:|---|---:|
| small-vehicle | 169,268 | roundabout | 657 |
| ship | 40,552 | helicopter | 652 |
| large-vehicle | 24,570 | basketball-court | 564 |
| plane | 8,533 | ground-track-field | 498 |
| storage-tank | 7,442 | soccer-ball-field | 421 |
| harbor | 6,459 | airport | 306 |
| tennis-court | 2,777 | container-crane | 256 |
| bridge | 2,497 | helipad | 104 |
| swimming-pool | 2,379 | | |
| baseball-diamond | 692 | **total** | **268,627** |

### 3.3 The labels currently on disk are NOT usable — FAIL if used

`.task-data/dota-raw/train/labelTxt/` (1,411 files, 210,631 instances) has **16 classes** and **no
difficulty flags at all** (every instance is flag 0). Airport and helipad are absent. This is the
Ultralytics conversion, not the official annotation set. Training on it would reproduce exactly the
defect this retrain is meant to remove.

### 3.4 Training images — INCOMPLETE

| Source | Images |
|---|---:|
| Official trainval annotations | 1,830 |
| Images present locally (`dota-raw/train/images`) | 1,411 |
| **Missing** | **419** |

The 419 missing images are not present anywhere else on this machine (checked against
`dota-raw/val` and `official_val/raw_v2.0/val`: zero name overlap). They are inside
`dotav2.0_images_train.tar.gz` (7.72 GB, reachable; HTTP 200 verified).

### 3.5 Split isolation — PASS

Official trainval names ∩ official val names = **0** of 593. No validation image can appear in
training. The tiling is performed per split, so patch-level isolation follows.

## 4. Recipe snapshot (from the epoch-16 config) — PASS

| Setting | Value |
|---|---|
| Model | Oriented R-CNN, ConvNeXt-Small backbone, PAFPN neck |
| Regression loss | Gaussian KLD, log1p parameterisation, **full precision** |
| Sampler | ClassBalancedDataset, `oversample_thr = 1e-3` |
| Augmentation | flips; RandomRotate p=0.5, 180° |
| Optimizer | AdamW, base LR 1e-4, weight decay 5e-2 |
| Schedule | LinearLR warmup 500 iters (start_factor 0.001) → CosineAnnealingLR T_max 24, eta_min 1e-6 |
| Batch in the config | 8 (A100 stage ran on one device) |
| Batch for epochs 17–24 | 4 per Tesla T4 × 2 devices → **effective batch 8** |
| Effective batch | 8 in both phases, reached two different ways |
| Dataloader | `num_workers=4`, `persistent_workers=True` |
| Input | 1024 × 1024 patches |
| Validation interval | every 2 epochs (dota/mAP) |
| Chunked rotated-IoU fix | `scripts/run_kaggle.py::patch_rotate_iou2d_calculator`, 64-row chunks, reusable |
| Resume flag | `resume = True` in the training config (must be `False` in the evaluation copy) |

Expected learning rates for the resumed epochs (cosine, computed from the stored state):

| Epoch | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|---|
| LR | 2.037e-05 | 1.550e-05 | 1.123e-05 | 7.632e-06 | 4.768e-06 | 2.687e-06 | 1.423e-06 | 1.000e-06 |

## 5. GPU — NOT YET DETERMINED FOR THE TARGET

This machine: `NVIDIA GeForce RTX 4060 Laptop GPU, 8,188 MiB, driver 615.78.08`. That is 8 GB —
insufficient for per-GPU batch 4 at 1024² for this model. A local run would require batch 1 with
eight-step accumulation, which preserves the effective batch but roughly triples wall-clock time
relative to a T4 and is not the requested platform.

No Colab runtime is attached to this session, and no browser automation is available to create one.

---

## Blockers

1. **No Colab runtime reachable from this session.** The job cannot be launched from here.
2. **Official training tiling does not exist.** It must be built once: download
   `dotav2.0_images_train.tar.gz` (7.72 GB), pair with the 1,830 official annotations, tile
   1024/200 with IoF 0.70 and coverage 0.60, and assert ~13,136 patches.

## What is already done

- Epoch-16 state verified as a valid resume point.
- Provenance of epochs 1–16 established from the checkpoint itself.
- Official train annotations downloaded and validated (18 classes, flags preserved).
- Validation tiling validated against the report's numbers.
- Split isolation proven at source-image level.
- Recipe captured, including the chunked rotated-IoU patch and the exact LR schedule.
