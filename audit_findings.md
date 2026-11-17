# Audit — ADA_REPORT_S_S_GOKULA_SWAMY.pdf

**Document:** *Deep Learning-Based Aerial Object Detection Using Oriented Faster R-CNN on the DOTA Dataset* (21 pages, 8 tables, 11 figures)
**Audit date:** 2026-11-16
**Method:** full text extraction (`pdftotext -layout`), table extraction from the source DOCX, scripted arithmetic checks, annotation recount from the official val annfiles, and visual inspection of every figure and of pages 1–21.

---

## 0. Verification summary (scripted)

| Check | Result |
|---|---|
| Table 5: TP + FN = 69,542 for all four rows | **PASS** (69,542 × 4) |
| Table 5: P, R, F1 recomputed from TP/FP/FN | **PASS** (all within 5e-5) |
| Table 6: 18 class counts sum to 69,542 | **PASS** |
| Table 6: class-mean AP50 = 0.6968, AP50-95 = 0.4175 | **PASS** (0.69681 / 0.41747) |
| Table 7: 18 class counts sum to 69,542; means 0.6049 / 0.3146 | **PASS** |
| Table 8: every Δ = B − A; mean Δ = +0.0919 | **PASS** (18/18) |
| Table 8: mean B AP50 = 0.6968 | **PASS** |
| Fig. 1 bar labels sum to 69,542 | **PASS** (23,075 + … + 4 = 69,542) |
| TOC page numbers vs actual headings | **PASS** (26/26 entries) |
| GT recount from `official_val/split_ss/val/annfiles` | 69,542 non-difficult + 70,561 difficult = **140,103** annotations |
| Phase-2 validation tiling size | **5,297 patches** (log: 2,649 val iterations × 2 GPUs), not 7,122 |

No arithmetic error was found in Tables 5–8 or in Fig. 1. The defects below are semantic, structural and evidential.

---

## 1. High severity

### F1 — "Controlled comparison" is unsupported (item a)
- **Where:** Abstract p2 ("making the comparison controlled"); §6.1 p6 ("making the track-level comparison controlled"); §13 p10 ("the remaining difference is hardware phase, which does not affect accuracy"); Fig. 5 caption p11 ("controlled same-patch comparison").
- **Evidence:** Table 3 (p8) lists seven differences between the tracks: detector, backbone/neck, regression loss, sampling/augmentation, optimizer/schedule, epochs (12 vs 24), and hardware. A controlled comparison varies one factor; here at least seven vary, and the tracks are also different architectures.
- **Fix:** Replace with "same-tiling evaluation" everywhere and enumerate the uncontrolled factors once in §13 and once in §9. Delete "which does not affect accuracy".

### F2 — Conclusion contradicts Table 8 on the largest gains (item b)
- **Where:** §19 p20: "with the largest gains on dense small objects (small-vehicle AP50 0.8220 vs 0.7653)".
- **Evidence:** Table 8 p17–18: small-vehicle Δ = +0.0567, rank **11 of 18**; median Δ lies between +0.0583 and +0.0698. Largest: helipad +0.2500, harbor +0.1960, bridge +0.1672, basketball-court +0.1554, large-vehicle +0.1391.
- **Fix:** State the measured top-five deltas; present small-vehicle as a dense-object case with a below-median gain.

### F3 — Table 1 misstates the Phase-2 tiling (item c)
- **Where:** Table 1 p5: "Phase 2 validation tiling — 7,122 patches"; contradicted by §6.1 p6 ("The two training phases used different validation tilings").
- **Evidence:** Training log `2026-11-15_track_b_final_epochs_17-24.log`: `Epoch(val) [20][…/2649]` with 2 GPUs → 5,297 validation patches. The project benchmark report records 5,297 patches / 458 images for the non-official tiling.
- **Fix:** 5,297 patches (458 images) for the non-official Phase-2 tiling; keep 7,122 for the official tiling.

### F4 — "Phase 1 records 0.6063 / 0.6039" has no track and no provenance (item c)
- **Where:** §10.1 p9.
- **Evidence:** No log in the repository contains 0.6063 or 0.6039 (grep over `results/logs` and `.task-data`). If read as Track A, they conflict with Track A's best 0.5412 (Table 4); they are most plausibly Track B A100-stage values but the text never says so.
- **Fix:** Label the track and stage explicitly, or drop the sentence; mark provenance `[AUTHOR TO CONFIRM]`.

### F5 — Track B's training data for epochs 17–24 is never disclosed (item d)
- **Where:** §6.1 and §10.1 discuss the non-official source only as an evaluation problem.
- **Evidence:** `scripts/run_kaggle.py` downloads **both** splits with `--source ultralytics` before tiling; the 2,649-iteration validation loop proves that tiling was in use during the continuation. Consequence: epochs 17–24 saw 16-class labels with no airport/helipad positives and no difficulty flags, while epochs 1–16 used the official 18-class data.
- **Fix:** State the training-data consequence in the data-provenance note and in the limitations.

### F6 — Track A F1-optimal threshold is not "not available" (item e)
- **Where:** Table 4 p10: "F1-optimal confidence threshold — not available", while the same row set reports P/R/F1 "at F1-optimal threshold".
- **Evidence:** `track_a_eval/eval_test/extended_metrics.json`: `micro_prf.f1_optimal.conf_threshold = 0.8103`.
- **Fix:** Report 0.8103.

### F7 — Throughput/memory compared across incomparable hardware (item e)
- **Where:** Table 4 p10: "17.38 img/s / 28.04 GiB" vs "5.70 img/s / 4.20 GiB".
- **Evidence:** Track A figure is the A100 training-time validation; Track B's 5.70 img/s is the local RTX 4060 evaluation pass (artifact `operational.fps`). No batch size, no hardware label, no note that the numbers are not comparable.
- **Fix:** Label hardware and batch size; state explicitly that the pair is not a throughput comparison, or move it to a note.

### F8 — Fig. 9 caption omits two of the six classes shown (item h)
- **Where:** Fig. 9 caption p14 lists "harbor, swimming-pool, helicopter, and container-crane"; the figure shows six panels including airport and helipad.
- **Fix:** Caption all six classes.

### F9 — "TP 0.07" contradicts the stated TP rule (item h)
- **Where:** Fig. 9 p14, helipad panel; §14 p12 defines TP as rotated IoU ≥ 0.50.
- **Evidence:** The label reads "helipad · TP 0.07"; the crop shows a clearly offset prediction.
- **Fix:** Relabel as IoU with an explicit "not a TP" marker and discuss it as a failure case (done in the revised figure).

### F10 — Checkpoint selection and reporting use the same validation split (item i)
- **Where:** Table 3 p8 ("Best checkpoint: epoch 24 (official-val dota/mAP 0.6352)"); §13 reports the same split.
- **Evidence:** No held-out split, single seed, no confidence intervals anywhere.
- **Fix:** State the selection-on-validation protocol and the absence of variance estimates in §6 and §9.

### F11 — Reproducibility details are missing (item k)
- **Where:** §9–§12; Table 3.
- **Evidence:** No library versions (torch/mmcv/mmdet/mmengine/mmrotate), no batch size, no LR milestones (Track A `[8, 11]`), no NMS IoU (0.7) or score cut-off (0.05, `max_per_img` 2000), no rotation range (prob 0.5, range 180°), no checkpoint/repository location beyond "present in the project artifacts".
- **Fix:** Add a reproducibility table and state the 0.05 score cut-off that produces the 133,986 predictions.

### F12 — References [7] and [8] do not support the correction claim (item l)
- **Where:** §3.1 p4 cites [7], [8] for "staged after correcting a non-official Phase-2 data source".
- **Evidence:** [7] is the DOTA dataset-description page and [8] the evaluation/submission page. Neither documents the Ultralytics `DOTAv2.zip` or its 458-image/16-class subset.
- **Fix:** Cite the actual archive used (Ultralytics v1.0 release URL) or mark `[AUTHOR TO CONFIRM]`.

---

## 2. Medium severity

### F13 — Tile occurrences are called "objects/instances" (item f)
- **Where:** §12 p9 ("69,542 non-difficult ground-truth objects"); Tables 6–8 ("Non-difficult GT"); Table 1 p5 ("69,542 objects").
- **Evidence:** 200 px overlap duplicates objects across tiles; Fig. 1's own axis is labelled "tile occurrences". Total tile-level annotations are 140,103 (69,542 + 70,561), not a count of unique objects.
- **Fix:** Define tile-level counting in the Data section and use "tile-level annotations" thereafter.

### F14 — 70,561 difficult annotations are never explained (item f)
- **Where:** Table 1 p5 only.
- **Evidence:** The DOTA difficulty flag is never defined, nor is its role in `dota/mAP` (`diff_thr=100`, difficult included) versus the extended evaluator (non-difficult only).
- **Fix:** Define the flag and the two conventions in the Data and Evaluation sections.

### F15 — The 70% IoF rule appears only in Future Scope (item g)
- **Where:** §18 p19; it is the stated cause of weak airport/container-crane scores but is never defined where the data are described.
- **Evidence:** `scripts/prepare_dotav2_patches.py`: `iof_thr: 0.7`, `img_rate_thr: 0.6`.
- **Fix:** Define the rule in the Data section and reference it from the per-class discussion.

### F16 — Qualitative figures are best-case only (item h)
- **Where:** Figs. 7–9 p13–14.
- **Evidence:** 16 of 18 crops are IoU 1.00; the remaining two are 0.97 and 0.68; no false positive, miss, or duplicate is discussed. The helipad panel is the only failure and is mislabelled TP.
- **Fix:** Add a short failure subsection and keep the helipad case as the worked failure.

### F17 — Fig. 6 misses/false positives are not discussed (item h)
- **Where:** Fig. 6 p12 and §14.
- **Evidence:** In tile P2375 the ground truth includes tennis-court, which is not predicted; "large-vehicle 0.97" appears without a matching ground-truth entry in the crop key.
- **Fix:** Discuss both in the qualitative section.

### F18 — Fig. 11 is unreadable and single-track (item h)
- **Where:** p16.
- **Evidence:** At page width the axis labels are ~4 pt; only Track A values are printed; the legend is illegible.
- **Fix:** Rebuilt from the Table 8 data with both-track labels, sorted by delta (revised document).

### F19 — Redundancy and structure (item j)
- **Where:** Abstract p2; §3.1 p4; §6.1 p6; §10.1 p9; §13 p10; §16 p18; §17.2 p19; §19 p19–20.
- **Evidence:** The non-official-data story appears in eight places; data preparation is described three times (§5, §6, §7); §11 and §16 overlap; §17.2 opens with a positive bullet ("precision, recall, and F1 are all higher"); Tables 6, 7 and 8 repeat the same per-class data three times.
- **Fix:** One boxed provenance note with one-line pointers; merged sections; one combined per-class table.

### F20 — Layout: large blank areas (item m)
- **Where:** p20 (~90% blank), p6 (lower half blank), p11–p13 (figure-induced gaps), Fig. 1 squeezed to ~2.6 in width.
- **Evidence:** Ink-coverage measurement: p20 = 3.7% ink; p6 = 13.6%.
- **Fix:** Remove forced breaks, reflow, size figures to the text width.

### F21 — Front matter incomplete (item l)
- **Where:** Title page and p3.
- **Evidence:** `[Guide Name]`, `[TD Name]`; no certificate, acknowledgements, organisation profile, intern role, list of figures, list of tables, or abbreviations.
- **Fix:** Add placeholder pages and lists (revised document).

### F22 — PAFPN and class-balanced sampling are uncited (item l)
- **Where:** §4 p5, §9 p8.
- **Evidence:** References [1]–[6] cover Faster R-CNN, Oriented R-CNN, KLD, ConvNeXt, MMRotate and DOTA; neither PAFPN nor ClassBalancedDataset has a source.
- **Fix:** Add `[CITATION REQUIRED]` placeholders (revised document).

### F23 — "Moderate difficult-instance recall" is unsupported (item e)
- **Where:** §17 p18.
- **Evidence:** Measured difficult recall is 0.299 against 70,561 difficult annotations — low, and "difficult" is undefined.
- **Fix:** Report the number and define the term.

### F24 — §12 claim about excluded classes is incorrect (item k)
- **Where:** §12 p9: "The custom class-averaged AP excludes classes without non-difficult ground truth in the evaluated set."
- **Evidence:** All 18 classes have non-difficult ground truth (minimum 4, helipad).
- **Fix:** Delete the sentence.

### F25 — "Phase 1/Phase 2" is overloaded (item c)
- **Where:** Table 1 p5, Table 4 header p10, §6.1 p6, §10.1 p9, §15.1 p15.
- **Evidence:** The same labels denote hardware stages, tilings, and track provenance ("Track A · Phase 1" vs "Track A on the official tiling").
- **Fix:** Define once, then use "A100 stage", "Kaggle continuation", "non-official tiling", "official tiling".

---

## 3. Low severity

| ID | Where | Finding | Fix |
|---|---|---|---|
| F26 | Table 4 p10 | Track A scale AP50 0.4875 / 0.5882 vs measured 0.4874 / 0.5881 | Use artifact values |
| F27 | Table 3 p8 | Track A "Best logged dota/mAP" has no value | Add 0.5412 or state "see Table 4" |
| F28 | §12 p9 | Lab-notebook voice ("The metrics JSON records…") | Rewrite in report voice |
| F29 | Abstract p2 | 216 words, 28 numeric tokens, includes the data-correction backstory | 150-word abstract, ≤5 numbers, no backstory |
| F30 | p1 | No submission date or institution mark | Template-dependent; `[AUTHOR TO CONFIRM]` |
| F31 | — | "RCNN" / "extendedmetric" extraction artifacts | **Refuted** — no such strings exist; only normal "R-
CNN" line wrapping |
| F32 | p11 | Fig. 5 caption repeats the "controlled" claim | Covered by F1 |

---

## 4. Findings not in the original checklist

1. **Table 1 internally contradicts §6.1** on the Phase-2 tiling (F3) — the strongest single factual error in the document.
2. **The Phase-2 training split is the non-official archive** (F5) — a material confound the report never states; it affects how Track B's rare-class results should be read.
3. **Table 4 reports P/R/F1 "at F1-optimal" with the threshold marked "not available"** (F6) — a direct internal contradiction.
4. **Track B's throughput figure was measured on a different GPU from the one named for training** (F7) — the 5.70 img/s value comes from the RTX 4060 evaluation pass.
5. **Fig. 9 shows six classes but its caption lists four** (F8).
6. **Table 7 has no mean row while Table 8 does** (asymmetry that makes the 0.6049 check non-obvious).
7. **§12's exclusion sentence is factually empty** (F24).
8. **Table 3's Track A validation-selection cell has no value** (F27).

---

## 5. Items requiring author input

- Provenance of 0.6063 / 0.6039 (F4).
- Repository / checkpoint public location (F11).
- Whether the Kaggle continuation's training split used the non-official archive and whether that is to be disclosed as a confound (F5).
- Certificate, guide, TD, organisation profile and intern-role text (F21).
- Citation sources for PAFPN and class-balanced sampling (F22).
