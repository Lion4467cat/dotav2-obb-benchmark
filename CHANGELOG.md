# Changelog

All notable changes to this repository. Model weights themselves have not
changed since v1.0.0.

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
- Report and README corrected; same weights as v1.0.0.

## [1.0.0] — 2026-11-15 — Track B flagship (epoch 24)

- Initial release: `best_dota_mAP_epoch_24.pth`, `epoch_24.pth`, `epoch_16.pth`.
