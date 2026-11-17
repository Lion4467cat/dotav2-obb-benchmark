> **HISTORICAL — superseded.** This is the audit of the pre-correction shipped document
> (21 pages). The report has since been rebuilt twice: against the epoch-22 official-retrain
> evaluation and then the epoch-24 evaluation. Numbers quoted below describe the superseded
> document only; the current report's figures are in `docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf`.

# PROMPT — Fix formatting faults in ADA internship report DOCX

> **Status: historical.** This is a one-off working prompt used on 2026-11-16 for
> the formatting pass. It is superseded by §15.1 of the report and by
> `CHANGELOG.md`; numbers quoted below (e.g. the retired "0.417" Track A
> small-vehicle AP50) are outdated. Do not execute it again.

Copy everything below this line as the prompt.

---

## TASK

Fix all formatting, layout, and residual content faults in
`docs/ADA_REPORT_S_S_GOKULA_SWAMY.docx` (Aeronautical Development Agency
internship report, "Deep Learning-Based Aerial Object Detection Using Faster
R-CNN on the DOTA Dataset"). The document was recently re-scored on the
official DOTA v2.0 val split; some numbers were updated but formatting was
never professionally normalized, and three paragraphs still carry the old
(pre-correction) narrative. Do NOT change any metric numbers — they are
verified and final. Only fix what is listed below. After editing the DOCX,
recompile the PDF with LibreOffice:

    libreoffice --headless --convert-to pdf --outdir docs/ docs/ADA_REPORT_S_S_GOKULA_SWAMY.docx

Work via python (zipfile + regex on word/document.xml / word/styles.xml), as
python-docx is not installed. Paragraph indices below refer to the index of
the match from `re.finditer(r'<w:p[ >].*?</w:p>', xml, re.S)` on the current
file — re-derive them with the same regex and verify by prefix text before
each edit (abort on mismatch).

## A. CRITICAL CONTENT FAULTS (pre-correction narrative remnants)

- **A1. Para ~330 (end of §19 Conclusion).** Currently says:
  "precision increased, but recall and F1 fell relative to the recorded Track
  A baseline; small objects remain harder; and the rarest classes lack enough
  validation coverage. Since the phases used different patch tilings and Track
  B is not an ablation study, ..."
  This is now FALSE — on the official val split Track B beats Track A on ALL
  three (P 0.8711 vs 0.8157, R 0.8302 vs 0.7564, F1 0.8502 vs 0.7849) on the
  SAME 7,122-patch tiling. Rewrite the whole paragraph to:
  "The results support the practical value of oriented detection for overhead
  objects: on the identical official 7,122-patch validation tiling, Track B
  improves precision, recall, and F1 over the Track A baseline, with the
  largest gains on dense small objects (small-vehicle AP50 0.8220 vs 0.417).
  Small objects remain harder than large ones (small AP50 0.6089 vs large
  0.8135), and the rarest classes (container-crane 27, airport 67, helipad 4
  non-difficult instances) still lack enough validation coverage for strong
  claims. Track B is not an ablation study, so these results describe the
  completed system and do not establish which individual component caused the
  score changes."

- **A2. Para ~45 (§3.1 Project scope).** Currently ends: "The local
  extended-metric artifact evaluates fresh Track B predictions against the
  restored Phase 2 validation annotations [7], [8]."
  Replace the trailing sentence with: "The local extended-metric artifact
  evaluates fresh Track B predictions against the official DOTA v2.0
  validation annotations, staged after correcting a non-official Phase-2 data
  source [7], [8]."

- **A3. Para ~63 (first table, row label).** Label cell reads
  "Phase 2 validation tiling" but the corrected value cell (para ~64) now
  describes the official split. Change the label to:
  "Official validation tiling (final Track B evaluation)".
  Also change the para ~62 label "Phase 1 validation tiling" to
  "Phase 1 validation tiling (Track A measurements)" for symmetry.

## B. TITLE PAGE (paras 0–7)

- **B1. Missing space, para 1.** "Deep Learning-Based Aerial Object
  DetectionUsing Faster R-CNN on the DOTA Dataset" → insert the space:
  "...Detection Using Faster R-CNN...". Also update the running footer
  (word/footer1.xml) if it repeats the same title — check it for the same
  missing space.
- **B2. Para 6 line-breaking bug.** Text is two fields jammed together with no
  separator: "Guide: [Guide Name]TD (ATD): [TD Name]". Split into TWO centered
  lines: "Guide: [Guide Name]" and "TD (ATD): [TD Name]" (insert a
  paragraph break or <w:br/>), and center the paragraph — it is currently the
  only left-aligned line on the title page.
- **B3. Unfilled placeholders.** Paras 6–7 contain "[Guide Name]", "[TD Name]",
  "[Start Date] – [End Date]". If the user has not supplied real names/dates,
  keep them but style them consistently; flag them to the user in the final
  summary as items they must fill in. Do NOT invent names or dates.
- **B4. Font inconsistency.** Title page runs use direct Times New Roman bold;
  the document default is Aptos 10pt. Unify: apply the built-in **Title**
  style (or define a custom TitlePage style) to para 0 (report type), para 1
  (project title), and use a centered Subtitle-like style for paras 2–7. Pick
  ONE font family for the whole document (recommendation: keep the existing
  Aptos/Aptos Display pairing used by the body and headings, and convert the
  title-page runs from Times New Roman to it; alternatively convert the whole
  document to Times New Roman 12pt body — do whichever requires less churn,
  but the result must be ONE family throughout).
- **B5. Title-page visual hierarchy.** Para 0 "INTERNSHIP PROJECT REPORT" and
  para 1 title are both bold same-size lines. Make para 1 the visually
  dominant element (Title style, ~28pt), para 0 a small-caps-style overline
  (~12pt, letter-spaced), and paras 2–7 ~11–12pt with 6pt spacing between
  blocks. Add ~24pt space before "Guide:" block.

## C. TABLE OF CONTENTS (paras 14–33)

- **C1. The CONTENTS list is fake.** It is 20 hand-typed paragraphs with
  literal "…" leader dots, no page numbers, no hyperlinks, and no TOC field.
  Delete paras 14–33 and insert a real Word TOC field that collects Heading1 +
  Heading2:
  ```xml
  <w:p><w:pPr><w:pStyle w:val="TOC1"/></w:pPr>
    <w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>
    <w:r><w:instrText xml:space="preserve"> TOC \o "1-2" \h \z \u </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="separate"/></w:r>
    <w:r><w:t>Right-click and choose "Update Field" to populate.</w:t></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
  ```
  After recompiling with LibreOffice, force field update during conversion
  (libreoffice does not auto-update TOC fields; if the placeholder text would
  ship, instead pre-populate the TOC entries with correct page numbers derived
  from the recompiled PDF, as static text with right-aligned tab leader dots —
  a "populated static TOC" — so the shipped PDF looks right; keep the field
  wrapper so Word users can refresh).
- **C2. TOC casing.** Headings are ALL CAPS ("1. INTRODUCTION"); the old TOC
  mixed casing ("1. Introduction…"). Whatever the TOC shows must match the
  headings exactly.
- **C3. ABSTRACT (para 9) and CONTENTS (para 13) use Heading1** and would be
  collected by the TOC field. Change them to a dedicated unnumbered look
  (e.g., a custom "FrontMatterHeading" style with identical H1 formatting) OR
  mark them with \n switch handling — simplest: give them the custom style so
  the TOC only lists sections 1–20.

## D. HEADINGS

- **D1. Unnumbered subsections in §17 Discussion.** Paras ~311 "What worked
  well" and ~316 "What did not work as well / limits" are Heading2 without
  numbers, breaking the 3.1 / 6.1 / 10.1 / 13.1 pattern. Rename to
  "17.1 What worked well" and "17.2 What did not work as well / limits".
- **D2. Heading style hygiene.** Heading4–9 styles in styles.xml still carry
  the default Office blue theme (4F81BD / 243F60 / 404040). They are unused
  but a latent trap. Normalize Heading4–9 fonts/colors to match Heading1–3
  (Aptos, color 171717) so any future use inherits the correct look.
- **D3. Keep-heading-together.** Add `<w:keepNext/>` to Heading1/2/3 style
  definitions so headings never sit alone at the bottom of a page.
- **D4. Spacing.** Heading1 styles currently rely on document defaults; set
  explicit spacing: Heading1 before=360 after=160, Heading2 before=240
  after=120, Heading3 before=180 after=100 (twips). Remove reliance on empty
  paragraphs for spacing (see F2).

## E. BODY TEXT

- **E1. Markdown backticks, para ~135.** "The logged MMRotate `dota/mAP` is
  reported separately from the custom extended evaluator's `map50`." Backticks
  are markdown artifacts — replace with italic runs: *dota/mAP* and *map50*.
  Scan the entire document for any other backtick occurrences and fix the same
  way.
- **E2. Justification.** Body paragraphs are default left-aligned with no
  explicit setting. For a formal report, set body paragraphs (the
  "(none/default)" narrative ones — NOT headings, NOT table cells, NOT
  captions) to justified: `<w:jc w:val="both"/>`. Do this via the Normal
  style or a new BodyText style, not per-run.
- **E3. Line spacing.** Normal has no explicit spacing; set
  `<w:spacing w:after="120" w:line="276" w:lineRule="auto"/>` (1.15 line, 6pt
  after) on the Normal style for readable body text, then DELETE the empty
  spacer paragraphs (fault F2 below).

## F. LAYOUT / STRUCTURE

- **F1. Page margins.** Current: top/bottom 1037 twips (~1.8 cm), left/right
  1195 (~2.1 cm) — cramped for a bound academic report. Set
  `<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"
  w:header="720" w:footer="720" w:gutter="0"/>` (1" all around).
- **F2. Empty spacer paragraphs.** 17 empty paragraphs (indices ~8, 69, 70,
  77, 91, 94, 121, 124, 174, 176, 214, 217, 220, 222, 224, 227, 305) are used
  as vertical space. After E3 gives styles real spacing, delete them — EXCEPT
  para 8 (between title page and ABSTRACT, likely intentional page break area)
  and any empty paragraph immediately preceding a page break. Verify no two
  consecutive empty paragraphs remain anywhere.
- **F3. Page break before major sections.** Insert an explicit page break
  before ABSTRACT (para 9), CONTENTS (para 13), and "1. INTRODUCTION" (para
  34) so the front matter is cleanly separated. Do not page-break every H1 —
  only these three.
- **F4. Title page footer.** footer2.xml (first-page footer) contains a PAGE
  field, so the title page shows a page number. Standard practice: no page
  number on the title page. Empty the first-page footer's page-number run (or
  set titlePg behavior so the first page footer is blank).

## G. TABLES (6 tables: paras 51–68, 79–90, 97–120, 138–173, 179–213, 229–304)

- **G1. No table captions.** Figures have numbered captions; tables have
  none. Add a caption paragraph ABOVE each table, matching figure caption
  style (see H1):
  - Table 1 (51–68): "Table 1. Dataset and tiling summary for both training
    phases and the final official validation split."
  - Table 2 (79–90): "Table 2. Proposed two-track system pipeline, from data
    preparation through evaluation."
  - Table 3 (97–120): "Table 3. Software and hardware configuration of Track A
    and Track B."
  - Table 4 (138–173): "Table 4. Headline validation metrics, official DOTA
    v2.0 val split (7,122 patches), Track A vs Track B."
  - Table 5 (179–213): "Table 5. Precision, recall, and F1 operating points at
    fixed confidence thresholds (Track B, official val)."
  - Table 6 (229–304): "Table 6. Per-class AP50 and AP50-95 with
    non-difficult ground-truth support (Track B, official val)."
- **G2. Header rows.** Each table's first row is direct-bold with no shading
  and will not repeat across page breaks. For EVERY table: (a) add light
  header shading `<w:shd w:val="clear" w:fill="F2F2F2"/>` to the first-row
  cell properties; (b) add `<w:tblHeader/>` to the first row's
  `<w:trPr>` so the header repeats on page breaks (Table 6 spans pages).
- **G3. Middle-dot header.** Para ~140 "Track B · official val" →
  "Track B (official val)" for consistency with para 139 "Track A · Phase 1"
  → change BOTH to "Track A (Phase 1)" / "Track B (official val)".
- **G4. Numeric alignment.** Numeric table cells are center-aligned — keep as
  is. First-column text cells keep left alignment. Do not change values.

## H. FIGURES & CAPTIONS (paras 71, 78, 95, 125, 177, 218, 221, 223, 225, 228)

- **H1. Caption consistency.** Captions are direct italic+centered runs; the
  built-in Caption style is blue bold 9pt (wrong look). Define a custom
  "FigCaption" style: centered, italic, 9pt, color 595959, spacing before=60
  after=240, and apply it to all 10 caption paragraphs (replacing their
  current direct jc/italic formatting).
- **H2. Figure 4 staleness check.** The embedded image4.png (training_setup,
  Figure 4, para ~125 area) was generated BEFORE the official-val correction.
  Render the recompiled PDF page containing Figure 4 and inspect it: if it
  displays "5,297", "Phase 2 tiling", or Phase-2 metric values, regenerate it
  from `docs/figures/training_setup.png` current source (or flag to user if
  no corrected source exists). Figures 1, 5, 6, 7, 8, 9, 10 were already
  swapped to corrected versions — do not touch them.

## I. STYLES / THEME CLEANUP

- **I1. Unify colors.** Body Normal color is 1E1E1E, headings 171717 — near
  duplicates that render inconsistently across viewers. Set all body and
  heading text to 000000 (pure black) — this is a print report. Keep table
  border color CFD8E3 as is.
- **I2. Normalize Heading4–9** per D2.
- **I3. Character-level sweep.** Verify: degree sign "°" used consistently;
  multiplication sign "×" in "1024 × 1024"; en-dash "–" in ranges ("1–16",
  "17–24"); minus sign "−" (U+2212) only in the metric-difference sentence
  (para ~175) — leave math usage, but replace any hyphen-as-minus in
  prose ranges. Check "Tesla T4" / "A100" naming consistency.

## J. VERIFICATION (mandatory, in order)

1. Re-run the stale-token scan on the final document text — must return NONE:
   `0.7065 0.4258 0.4487 0.5182 0.7264 0.8409 0.6394 5,297 120,013 121,615
   0.4985 0.6004 0.8783 0.7584` (the single 0.6893 in the para-127 historical
   sentence is ALLOWED; "0.6892" appears only in historical-log sentences).
2. Confirm "DetectionUsing" no longer appears anywhere (document + footers).
3. Confirm "precision increased, but recall" no longer appears.
4. Recompile the PDF: `libreoffice --headless --convert-to pdf --outdir
   docs/ docs/ADA_REPORT_S_S_GOKULA_SWAMY.docx`.
5. Render QA: `pdftoppm -png -r 80` the title page, TOC page, first results
   table page, and the page with Table 6; visually inspect each (title
   centered with no page number, TOC with page numbers and leader dots, table
   headers shaded, captions gray italic, no orphan headings at page bottoms).
6. `pdftotext` sanity scan: page numbers present in TOC, "17.1"/"17.2"
   present, "Table 1." … "Table 6." present, backticks absent.
7. Commit DOCX + PDF together with message
   "docs(report): professional formatting pass and final narrative corrections"
   and push.

## HARD CONSTRAINTS

- Do NOT alter any metric value, class name, or claim that is already correct.
- Do NOT invent guide names, dates, or a server score.
- Do NOT touch results/, README.md, or figures other than what H2 requires.
- Preserve all existing run properties where a paragraph is not explicitly
  listed for restyling.
- Keep the document valid: after every XML edit, the file must still open in
  LibreOffice (test-convert before the final compile).

---

*End of prompt. Generated 2026-11-16 after full-format inspection of the
post-correction DOCX (commit 785dca95).*
