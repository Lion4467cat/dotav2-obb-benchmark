# Revision changelog — ADA internship report

**Source document:** `docs/ADA_REPORT_S_S_GOKULA_SWAMY.docx` (unchanged, 21 pages)
**Revised document:** `revised/ADA_REPORT_S_S_GOKULA_SWAMY_revised.docx` and `.pdf` (29 pages)
**Audit that drove the revision:** `audit_findings.md` (findings F1–F32)
**Build script:** `/tmp/build_report.py` (python-docx, two-pass page map for the table of contents)

The original files were never modified. Every measured value in the revised report was
re-read from the evaluation artifacts:

- `artifacts/checkpoints/track_a_eval/eval_test/extended_metrics.json` (Track A)
- `results/extended_metrics.json` (Track B)
- `results/logs/*.log` (training and validation runs)

---

## 1. Structure

| Original (20 numbered sections, all-caps headings) | Revised |
|---|---|
| — | Front matter: title page, Certificate, Acknowledgements, Organisation Profile and Intern Role, Contents, List of Figures, List of Tables, Abbreviations |
| — | Abstract (117 words, four measured numbers, no backstory) |
| 1 Introduction, 2 Problem statement, 3 Objectives, 3.1 Project scope | 1 Introduction (1.1 Problem statement, 1.2 Objectives, 1.3 Scope) |
| 4 Background and related work | 2 Background (2.1 Two-stage oriented detectors, 2.2 Regression, backbone and sampling, 2.3 What this study does not isolate) |
| 5 Dataset description | 3.1 Dataset and class set |
| 6 Dataset preparation and annotation conversion | 3.2 Tiling and tile-level counting, 3.3 Split isolation |
| — | 3.4 Data provenance (new: the non-official archive and its correction) |
| — | 3.5 Class support |
| 7 Proposed system | 4.1 Pipeline (Figure 2, Table 2) |
| 8 Oriented bounding box detection | 4.2 Oriented box representation (Figure 3) |
| — | 4.3 Track configurations (Table 3), 4.4 Software and reproducibility (Table 4) |
| 9 Software and hardware environment | merged into 4.3, 4.4 and 5.2 |
| 10 Model training, 10.1 Completed validation progression | 5 Training (5.1 Run stages, 5.2 Schedule and hardware, 5.3 Checkpoint selection) |
| 11 Training challenges and errors | 5.4 Engineering issues and fixes |
| 12 Evaluation metrics | 6 Evaluation protocol (6.1 Matching and PRF, 6.2 AP and mAP, 6.3 Two mAP conventions, 6.4 Stratification, 6.5 Prediction set, 6.6 Selection protocol) |
| 13 Results and performance analysis, 13.1 Precision and recall operating points | 7.1 Headline comparison, 7.2 Operating points |
| 15 Class-wise observations, 15.1 Track A per-class results | 7.3 Per-class results (Table 7), 7.4 Scale, orientation and difficulty (Table 8), 7.5 What the numbers do not show |
| 14 Visual detection results | 8 Qualitative analysis (8.1 Prediction examples, 8.2 Per-class examples, 8.3 Failure modes) |
| 16 Project challenges, 17 Discussion, 17.1 What worked well, 17.2 What did not work as well | 9 Discussion and limitations (9.1 Interpretation, 9.2 Limitations) |
| 18 Applications and future scope | 10 Applications and future work (10.1, 10.2) |
| 19 Conclusion | 11 Conclusion |
| 20 References | References (7 entries) |
| — | Appendix A Configuration reference (Table A1), Appendix B Full per-class tables (Tables A2, A3) |
| — | Author confirmations (last page, collects every highlighted note) |

## 2. What moved

- The two per-class tables of the original (Table 6 for Track B, Table 7 for Track A, Table 8 for
  the deltas) became **one** table sorted by gain (Table 7) plus the complete per-class tables in
  Appendix B. The same 54 numbers appear in both places, so nothing was lost.
- Track A per-class results, previously a late subsection (15.1), now sit beside the Track B values
  they are compared with.
- Software and hardware, previously one table (original Table 3), is split into track configuration
  (Table 3) and reproducibility settings (Table 4), because the two answer different questions.
- Training challenges (original §11) and project challenges (original §16) were merged into 5.4
  (engineering issues, each with its fix) and 9.2 (limitations), so that a given caveat appears once.

## 3. What was cut, and why

| Removed | Reason |
|---|---|
| 0.6063 and 0.6039 | No artifact produces these values. Audit finding: unattributable. |
| Track A per-class column whose mean was 0.5412 | The column was mis-transcribed; the artifact mean is 0.6049. Rebuilt from the JSON. |
| The sentence "small-vehicle AP50 0.8220 vs 0.417 for Track A" | 0.417 appears nowhere in the artifacts. Track A scores 0.7653 on that class. |
| TP/FP/FN counts at thresholds 0.25, 0.30 and 0.50 | The four operating points are reported as P/R/F1 (Table 6); the counts at the F1-optimal point are given in §6.5 (Track A 52,597 / 11,882 / 16,945; Track B 57,736 / 8,546 / 11,806). The other counts are recoverable from P, R and the 69,542 total. |
| Run timings quoted as 28.04 min per epoch, 3.13 s per iteration, 17.38 GB | Not attributable to a single run in the logs, and the hardware differed between stages. |
| DOI 10.1145/3503161.3548541 in reference [7] | That DOI belongs to a different paper. Replaced with 10.1109/TPAMI.2021.3117983, vol. 44, no. 11, pp. 7778–7796. |
| P/R/F1 printed as percentages (83.02, 85.02, 87.11) | Reported as fractions (0.8302, 0.8502, 0.8711) throughout, matching the AP columns. |
| The word "controlled" for the A-vs-B comparison | The tracks differ in seven factors. The report says "same-tiling evaluation" and lists the differences in §2.3 and §4.3. |
| "Small-object capability" claim in the conclusion | Contradicted by Table 7: small-vehicle gains 0.0567, ranking 11th of 18. §7.3 states this explicitly and the conclusion makes no such claim. |
| "F1-optimal threshold not available" for Track A | The artifact records 0.8103. It is in Table 5 and Table 6. |
| "Phase 2 validation tiling 7,122" | 7,122 belongs to the official tiling. The non-official tiling has 5,297 patches, as the logs show (2,649 iterations × 2 GPUs). Both are now listed separately in Table 1. |

## 4. What was added

- Front matter required by the college format: certificate, acknowledgements, organisation profile,
  contents, list of figures, list of tables, abbreviations.
- Abstract with four numbers and no project history.
- §3.4 Data provenance: the non-official archive, what it contained (458 of 593 validation images,
  16 classes, no difficulty flags), which epochs it affected (Track B 17–24), and the fact that all
  Track B numbers were re-evaluated on the official tiling without retraining.
- §6.3 Two mAP conventions (dota/mAP with difficulty included versus the project evaluator without).
- §6.5 Prediction set and the TP + FN = 69,542 identity as the evaluator's consistency check.
- §6.6 Selection protocol: checkpoint and threshold were both chosen on the reported split.
- §7.4 difficulty recall (0.7564 / 0.2630 for Track A, 0.8303 / 0.2990 for Track B) and the gap
  between the tracks on each group (+0.0739 non-difficult, +0.0360 flagged).
- §7.5 What the numbers do not show.
- §8.3 Failure modes, with the helipad case (4 instances, 2 matched, AP50 0.25) stated as such.
- Appendix A (full configuration) and Appendix B (complete per-class tables with P, R, F1).
- Author confirmations page.

## 5. Figure and table numbering

| Original | Revised | Note |
|---|---|---|
| Figure 1 dataset support | Figure 1 | caption rewritten to say the counts are tile-level |
| Figure 2 pipeline | Figure 2 | |
| Figure 3 oriented box and KLD | Figure 3 | |
| Figure 4 training schedule | Figure 4 | |
| Figure 5 headline metrics | Figure 5 | |
| Figure 11 A-vs-B per-class bars | **Figure 6** | rebuilt: 18 classes, sorted by gain, both tracks, label gives A → B (Δ) and n |
| Figure 10 Track B AP50 by class | **Figure 7** | redrawn with print-legible labels |
| Figure 6 predictions | **Figure 8** | |
| Figures 7, 8, 9 class examples | **Figures 9, 10, 11** | captions now name all six classes; IoU shown per panel; predictions below 0.50 marked "not a TP" |

| Original | Revised |
|---|---|
| Table 1 dataset | Table 1 (7,122 official and 5,297 non-official listed separately) |
| Table 2 pipeline | Table 2 |
| Table 3 software and hardware | Table 3 (track configuration) and Table 4 (software and reproducibility) |
| Table 4 headline metrics | Table 5 (12 rows; Track A F1-optimal threshold 0.8103 added) |
| Table 5 PRF, Track B only | Table 6 (both tracks, four thresholds) |
| Tables 6, 7, 8 per-class | Table 7 (both tracks, sorted by gain) and Tables A2, A3 (complete) |
| — | Table 8 (scale strata, orientation error, difficulty) |
| — | Table A1 (full configuration reference) |

## 6. Verification performed

- Table 5: every value re-read from the two JSON artifacts.
- Table 6: all 24 P/R/F1 triples match the artifacts; each F1 is the harmonic mean of its own P and R;
  TP + FN = 69,542 in every row.
- Table 7: 18 classes, sorted by descending Δ, every Δ equals B − A, means 0.6049 and 0.6968.
- Table 8: every Δ recomputed; orientation decreases shown with a minus sign.
- Appendix B: 36 class rows plus two means, all from the artifacts.
- Class counts sum to 69,542; macro F1 means 0.6285 and 0.7254.
- Table of contents: 53 entries, page numbers resolved by a two-pass build and re-checked against the
  compiled PDF (0 mismatches).
- Layout: 30 pages, no blank pages, no table split across pages, no caption separated from its object.

## 7. [AUTHOR TO CONFIRM] — consolidated

These appear highlighted in the body and again on the last page of the report.

1. **Certificate** — college wording, signature blocks, seal, date.
2. **Acknowledgements** — named guide, technical director, department and colleagues.
3. **Organisation profile** — official ADA text, and the intern's role, team and reporting line.
4. **Guide and TD names** — placeholders on the title page and in the certificate.
5. **Repository and checkpoint location** — public URL, checkpoint download location, random seeds
   (or a statement that seeds were not recorded).
6. **Kaggle training split** — confirm that epochs 17–24 trained on the same non-official archive, and
   decide whether that confound belongs in the abstract.
7. **Citations** — peer-reviewed sources for PAFPN and for class-balanced sampling, or approval to
   remove the two `[CITATION REQUIRED]` markers in §2.2.
8. **Submission date** — date and programme reference on the title page.

## 8. Layout notes

- 29 pages: 8 pages of front matter (title to abbreviations), 18 pages of body and references
  (pages 9–26), 2 pages of appendix (27–28), 1 page of author confirmations (29).
- Remaining white space at the foot of a page occurs where a full-height figure starts a new page
  (Figures 1, 2 and 8). No page is blank.
- Table captions sit above their tables and figure captions below their figures, consistently.

---

## 2026-11-18 — Epoch-24 rebuild (official retrain complete)

The revised document was rebuilt twice from the same source `build_report.py`, once against the
epoch-22 evaluation and again against the epoch-24 evaluation (official retrain; epochs 23–24
completed in a resumed Kaggle 2×T4 run). The figures and tables now report the epoch-24 official
results: dota/mAP **0.6535**, mAP50 **0.7127**, AP75 **0.4664**, mAP50-95 **0.4320**, F1 **0.8511**
(F1-optimal confidence **0.834**). Narrative edits: the report now states the full 24-epoch budget
completed, that the epoch-24 checkpoint used for all figures is `epoch_24.pth` (no best/-last
selection, see the best-score inheritance note), and that the Phase-2 superseded numbers live in
the benchmark-report appendix. Page map: 30 pages, 75/75 resolved, 0 mismatches.
