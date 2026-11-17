# Changelog

All notable changes to this repository. Release assets published before the
official retrain were from the pre-correction lineage and were removed on
2026-11-18; see "Download the model" in the README.

## [1.3.0] — 2026-11-18 — Track B official retrain completed (epochs 23 & 24)

### Added
- Official-retrain epochs **23 and 24** trained and validated on Kaggle (2×Tesla T4),
  resumed from the official-retrain `epoch_22.pth` checkpoint (new private Kaggle
  dataset `ada-trackb-epoch22` on the project account `bhaghwanss`).
- Epoch-24 official validation (7,122 patches): **dota/mAP 0.6535**; final
  `test.py` pass identical (0.6535).
- Extended evaluation of `epoch_24.pth` on the official val split: mAP50
  **0.7127**, AP75 **0.4664**, mAP50-95 **0.4320**, class-agnostic AP50 0.8803,
  classification gap 0.1676, scale AP50 0.622 / 0.683 / 0.839 (s/m/l), mean angle
  error 4.88° (all TPs) / 2.05° (elongated), easy recall 0.8335, difficult
  recall 0.3019, F1-optimal 0.8511 at conf 0.834, 136,612 predictions.
- `colab/trackB_official_finish_ep23_24_kaggle.ipynb` + `scripts/build_finish_ep23_24_nb.py`
  (validated: nbformat, kernelspec, AST; resumes from `epoch_22.pth`, re-tiles the
  official data, trains epochs 23–24, validates at 24, packages deliverables with a
  SHA-256 manifest).
- `results/trackb_official_ep23_24/` — training log, `scalars.json`, configs,
  `extended_metrics.json`, `preds.pkl`, manifest, deliverables report.
- `results/logs/2026-11-18_track_b_epochs_23-24_kaggle.log` — full kernel log.

### Changed
- README: all Track B metrics replaced with the official-retrain epoch-24 numbers
  (dota/mAP 0.6535, mAP50 0.7127, mAP50-95 0.4320, F1 0.8511, AP75 0.4664,
  F1-optimal confidence 0.834, throughput 2.52 img/s @ 9.25 GiB on 2×T4).
- README "Download the model": pre-correction release assets marked removed
  (2026-11-18) and the initial release's notes updated in place; the canonical
  `epoch_24.pth` (SHA-256 `d855c250…4995f`, 858 MB) is published as the
  **v1.3.0** asset together with its SHA-256 sidecar; `dota_obb.download` and the
  Gradio UI re-pointed at v1.3.0 with digest verification.
- Package version unified at **1.3.0** (`pyproject.toml`, `dota_obb.__version__`).
- `results/extended_metrics.json` / `results/preds.pkl`: sync with the epoch-24
  evaluation; figures regenerated; internship report rebuilt (30 pp.) to the
  epoch-24 numbers.
- `scripts/gradio_app.py`, `scripts/make_all_figures.py`: F1-optimal threshold
  reference and metrics fallbacks updated to the epoch-24 values.
- `scripts/build_colab_notebook.py`: unchanged (still the Colab handover doc).

### Notes
- No best-checkpoint file was produced (the resumed run inherits the
  pre-correction `message_hub` best-score tracker (0.6883, recorded on the
  non-official tiling), and no post-resume validation exceeded it. Epoch 24 is
  the final checkpoint and was used directly for all reported metrics.
- First finish-attempt notebooks failed **before execution** on missing
  `outputs`/`execution_count` (nbformat) and missing `kernelspec` (papermill) —
  both fixed and validated; the running v4 notebook executed all cells to
  completion.
- Epoch-22's in-training validation was cut by the 12-hour Kaggle cap; its
  number in docs is the local official-val evaluation pass (dota/mAP 0.6366).

## [1.2.0] — 2026-11-16 — Repository audit, registry and documentation sync

### Fixed
- `scripts/download_dotav2.py`: the `--source huggingface` branch no longer
  downloads the non-official Ultralytics `DOTAv2.zip`. Source selection is now
  mutually exclusive via `_download_for_source()` — mixing archives was the
  mechanism behind the Phase-2 data-source defect.
- `scripts/run_kaggle.py`: the GPU pipeline now requests `--source huggingface`
  (official 18-class DOTA v2.0) instead of `ultralytics`.
- `dota_obb/model.py`: `predict()["num_detections"]` now equals the number of
  returned detections above `score_thr` (previously counted every raw box).
- `dota_obb/model.py`, `dota_obb/download.py`: downloaded weights are verified
  against the published SHA-256 before use; unused imports removed.
- `scripts/run_track_eval.py`: parameter counting builds the model under the
  `mmrotate` registry scope, so `operational.params_m` is populated instead of
  silently `null`.
- `pyproject.toml`: `testpaths`/`norecursedirs` added — `uv run pytest` no longer
  collects the vendored `mmrotate` tree (47 collection errors before).
- `scripts/merge_test_preds.py`: imports the canonical class list and falls back
  to CPU when CUDA is unavailable; `scripts/infer_test_tiles.py` does the same.

### Changed
- Version unified at **1.2.0** (`pyproject.toml`, `dota_obb.__version__`).
- `[project.optional-dependencies].ui` added so `pip install -e ".[ui]"`
  documented in the README actually works.
- Gradio UI threshold caption corrected: the validation F1-optimal threshold is
  **0.8279** (the previous 0.5182 belonged to the superseded Phase-2 tiling).
- Notebook generator and `colab_runner.ipynb` prose now describe
  `DATA_SOURCE = 'huggingface'` as the default, matching the code.

### Documentation
- README: Track A per-class AP50/recall replaced with measured official-val
  values (the old column averaged 0.5412, i.e. the mmengine difficult-included
  mAP, while the table claimed extended mAP50 0.6049). Angle-error rows
  un-swapped (all-TP 6.42° mean; elongated 3.78°). Parameter count corrected to
  70.24 M (Track B) / 41.37 M (Track A).
- README: release table now lists exact sizes and SHA-256 digests, plus explicit
  checkpoint status (recommended / resume-only / deprecated).
- `results/final_benchmark_report.md`: Track A per-class, scale-AP50, angle and
  parameter rows synced with the evaluation artifacts.
- `results/extended_metrics.json`: `operational.params_m` corrected 49.0 → 70.24.
- Internship report: title changed to “Using **Oriented** Faster R-CNN”; PDF
  regenerated. `docs/REPORT_FORMAT_FIX_PROMPT.md` marked historical.
- Added regression tests for download-source exclusivity, version consistency,
  and README per-class consistency.

## [1.1.0] — 2026-11-16 — Official-val re-evaluation correction

- Track B re-evaluated on the official DOTA v2.0 val split (593 images, 7,122
  patches); Phase-2 numbers retained as a superseded appendix.
- Report and README corrected; same weights as the initial release.

## [1.0.0] — 2026-11-15 — Track B flagship (epoch 24)

- Initial release of the Track B weights (pre-correction lineage; both Track B assets were
  removed on 2026-11-18) alongside the phase-1 anchor checkpoint.
