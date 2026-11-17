# Track B official retrain — Colab handover

`trackB_official_retrain.ipynb` resumes Track B at epoch 16 and trains epochs 17–24 on the official
DOTA v2.0 trainval split, then re-evaluates on the official 7,122-patch validation tiling.

## Before the first run

1. Create `MyDrive/ada_trackB_official/checkpoints/` in your Drive.
2. Upload `artifacts/checkpoints/epoch_16.pth` (849 MB) into it.
3. Open the notebook in Colab with a GPU runtime (T4, L4 or A100 all work; the notebook adapts the
   batch/accumulation split to the memory it finds and always keeps an effective batch of 8).

## Run order

| Cell | What it does | Notes |
|---|---|---|
| 1 | Mount Drive, detect GPU, define paths | stops if `epoch_16.pth` is missing |
| 2 | Install torch 2.0.1 / mmcv 2.0.1 / mmdet 3.1.0 / mmengine 0.9.1 | falls back once if this Python has no wheels; **restart the runtime afterwards** |
| 3 | Clone repo at `a2ecd69d`, clone MMRotate dev-1.x, apply the chunked rotated-IoU patch | prints every version |
| 4 | Download official trainval + val archives, tile 1024/200, assert the counts | caches `split_ss_dotav2_tiled.tar` (~3.5 GB) on Drive; asserts 7,122 val patches, 18 classes, 69,542 / 70,561, ~13,136 train patches |
| 5 | Rebuild the config embedded in `epoch_16.pth`, apply the resume overrides | prints the effective batch and the expected epoch-17 LR |
| 6 | Smoke test, 50 iterations | asserts resume epoch 16, LR 2.0366e-05, finite loss; prints it/s and the ETA |
| 7 | **Train** | re-run this cell after any disconnect; it resumes from the newest checkpoint |
| 8 | Final evaluation | mmengine dota/mAP plus the extended evaluator on the official tiling |
| 9 | Arithmetic checks, comparison table, deliverables | writes `comparison_table.md`, `results_trackB_official_retrain.json`, `deviations.md` |

## What the run writes to Drive

```
MyDrive/ada_trackB_official/
  checkpoints/epoch_16.pth                     (you upload this)
  checkpoints/trackB_official_epoch_{17..24}.pth   every epoch, pruned to last 2 + all >= 20
  checkpoints/trackB_official_iter_latest.pth      rolling intra-epoch save (every 300 iters)
  data/raw_train_counts.json                   image-level class counts, written once
  raw_archives/{train,val}/                    one-time, ~10 GB
  work_dirs/trackB_official_ep17-24/           config, logs, epoch checkpoints, eval_test/
  logs/, comparison_table.md, results_trackB_official_retrain.json, deviations.md
```

Total Drive footprint is about 16 GB. The tiled set (~24 GB of PNGs) lives on Colab's local disk only. The old run (`track_b_convnext_s_pafpn_kld_2x`) is never
touched, and neither is any checkpoint under `artifacts/checkpoints/`.

## Validation cadence

Validation runs at the end of epochs **20, 22, 23 and 24** only, driven by a hook; the training loop's
own interval is disabled. Each validation pass over 7,122 patches costs roughly 20–25 minutes on a T4.

## If something goes wrong

- **Cell 2 fails on both stacks**: Colab's Python has no matching wheel. Report the printed pip
  output; the fallback is torch 2.2.2 / mmcv 2.2.0 / mmdet 3.3.0 / mmengine 0.10.4, which the
  notebook tries automatically.
- **Cell 4 asserts on the val count**: the tiling did not reproduce 7,122 patches. Do not train;
  send the printed counts.
- **Cell 6 asserts on the LR**: the resume did not land on the cosine value for epoch 17. Do not
  train; send the printed LR.
- **OOM in cell 6 or 7**: the notebook already drops to batch 2 × 4 accumulation below 14 GB. If it
  still OOMs, stop and report rather than changing anything else.

## Kaggle notebooks (official retrain, 2 × T4)

Two generated notebooks cover the official-data continuation:

- `trackB_official_retrain_kaggle.ipynb` — resumes Track B at epoch 16, re-tiles the official
  DOTA v2.0 data and trains epochs 17–24. Session 2a used this notebook and hit the 12-hour cap
  during the epoch-22 validation. Build it with `python scripts/build_colab_notebook.py`-adjacent
  generators; it is committed for reproducibility.
- `trackB_official_finish_ep23_24_kaggle.ipynb` — resumes from `epoch_22.pth` (official retrain
  end-of-session checkpoint), trains **epochs 23 and 24**, validates at epoch 24, runs the extended
  evaluation and packages deliverables with a SHA-256 manifest. Session 2b used this notebook
  (`bhaghwanss/trackb-finish-ep23-24`, v4); it completed cleanly. Build it with
  `python scripts/build_finish_ep23_24_nb.py`.

Session 2b scale/identity facts: resume anchor `epoch_22.pth` (official retrain, sha256
`747d2076…f1041a`), attached as the private Kaggle dataset `bhaghwanss/ada-trackb-epoch22`;
training data re-downloaded and re-tiled inside the session (official v1.0 + v2.0 archives merged,
1,830 train images → 24,151 patches; official val → 7,122 patches, 81,048 annotations);
`epoch_24.pth` dota/mAP (validation) **0.6535**. Outputs live in `results/trackb_official_ep23_24/`.

Both notebooks provision the same pinned venv as Colab, apply the same two mmrotate patches, and
assert the official patch counts before training. Validation runs at epoch 24 only (`val_interval=2`).
The epoch-23/24 run inherits the pre-correction `message_hub` best-score tracker (0.6883,
non-official tiling): no post-resume validation exceeded it, so no best-checkpoint file
was saved — `epoch_24.pth` is the final artifact.
