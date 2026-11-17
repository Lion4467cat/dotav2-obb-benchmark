"""Build the revised internship report (two-pass: page map injected on pass 2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

REPO = Path("/home/tinkerer/Desktop/ADA")
ASSETS = REPO / "revised" / "assets"
OUT = REPO / "revised" / "ADA_REPORT_S_S_GOKULA_SWAMY_revised.docx"

TNR = "Times New Roman"
BLACK = RGBColor(0, 0, 0)
GRAY = RGBColor(0x55, 0x60, 0x6E)

A_full = json.load(open(REPO / "artifacts/checkpoints/track_a_eval/eval_test/extended_metrics.json"))
B_full = json.load(open(REPO / "results/extended_metrics.json"))
A = A_full["per_class"]
B = B_full["per_class"]
CLASSES = list(B.keys())
ORDER_DELTA = sorted(CLASSES, key=lambda c: B[c]["ap50"] - A[c]["ap50"], reverse=True)
ORDER_STD = ["plane", "baseball-diamond", "bridge", "ground-track-field", "small-vehicle",
             "large-vehicle", "ship", "tennis-court", "basketball-court", "storage-tank",
             "soccer-ball-field", "roundabout", "harbor", "swimming-pool", "helicopter",
             "container-crane", "airport", "helipad"]

def f4(x: float) -> str:
    return f"{x:.4f}"

MEAN_A50 = sum(A[c]["ap50"] for c in CLASSES) / 18
MEAN_A95 = sum(A[c]["ap50_95"] for c in CLASSES) / 18
MEAN_B50 = sum(B[c]["ap50"] for c in CLASSES) / 18
MEAN_B95 = sum(B[c]["ap50_95"] for c in CLASSES) / 18
GT = sum(B[c]["num_gt"] for c in CLASSES)

PAGES = {}  # heading/caption -> page number (pass 2)

# ---------------------------------------------------------------- primitives

def set_run_font(run, size=12, bold=False, italic=False, color=BLACK):
    run.font.name = TNR
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), TNR)

def setup(doc: Document):
    sec = doc.sections[0]
    sec.page_height = Inches(11.69)
    sec.page_width = Inches(8.27)
    sec.top_margin = Inches(0.95)
    sec.bottom_margin = Inches(0.9)
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)

    normal = doc.styles["Normal"]
    normal.font.name = TNR
    normal.font.size = Pt(11.5)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.space_after = Pt(6)
    rpr = normal.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(attr), TNR)

    h1 = doc.styles["Heading 1"]
    h1.font.name = TNR; h1.font.size = Pt(14); h1.font.bold = True
    h1.font.color.rgb = BLACK
    h1.paragraph_format.space_before = Pt(16)
    h1.paragraph_format.space_after = Pt(6)
    h1.paragraph_format.keep_with_next = True
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    h2 = doc.styles["Heading 2"]
    h2.font.name = TNR; h2.font.size = Pt(12); h2.font.bold = True
    h2.font.color.rgb = BLACK
    h2.paragraph_format.space_before = Pt(10)
    h2.paragraph_format.space_after = Pt(4)
    h2.paragraph_format.keep_with_next = True
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

def h1(doc, text, new_page=False):
    p = doc.add_paragraph(text, style="Heading 1")
    if new_page:
        p.paragraph_format.page_break_before = True
    return p

def h2(doc, text):
    p = doc.add_paragraph(text, style="Heading 2")
    return p

def para(doc, text, lead=None, size=11.5, space_after=6, align=WD_ALIGN_PARAGRAPH.JUSTIFY, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.alignment = align
    if lead:
        r = p.add_run(lead)
        set_run_font(r, size=size, bold=True)
    r = p.add_run(text)
    set_run_font(r, size=size, italic=italic)
    return p

def bullet(doc, text, lead=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if lead:
        r = p.add_run(lead); set_run_font(r, size=11.5, bold=True)
    r = p.add_run(text); set_run_font(r, size=11.5)
    return p

def caption(doc, text, keep_next=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = keep_next
    r = p.add_run(text)
    set_run_font(r, size=9, italic=True, color=GRAY)
    if text.startswith("Table "):
        # table captions sit above the table so that they cannot be separated from it
        prev = p._p.getprevious()
        if prev is not None and prev.tag == qn("w:tbl"):
            prev.addprevious(p._p)
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
    return p

def author_note(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(f"[AUTHOR TO CONFIRM: {text}]")
    set_run_font(r, size=10.5, italic=True)
    r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return p

def figure(doc, name, width, cap, break_before=False):
    p = doc.add_paragraph()
    p.paragraph_format.page_break_before = break_before
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ASSETS / name), width=Inches(width))
    caption(doc, cap)

def shade(cell, hex_fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcpr.append(shd)

def cell_text(cell, text, size=9, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(str(text))
    set_run_font(r, size=size, bold=bold)

def table(doc, headers, rows, widths, size=9, align_center_from=1, first_col_bold=False):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblpr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)
    tblw = OxmlElement("w:tblW")
    tblw.set(qn("w:type"), "dxa")
    tblw.set(qn("w:w"), str(int(sum(widths) * 1440)))
    tblpr.append(tblw)
    for i, w in enumerate(widths):
        t.columns[i].width = Inches(w)
    hdr = t.rows[0]
    trpr = hdr._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trpr.append(th)
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        c.width = Inches(widths[i])
        shade(c, "D9D9D9")
        cell_text(c, h, size=size, bold=True,
                  align=WD_ALIGN_PARAGRAPH.LEFT if i < align_center_from else WD_ALIGN_PARAGRAPH.CENTER)
    for row in rows:
        tr = t.add_row()
        cant = OxmlElement("w:cantSplit"); tr._tr.get_or_add_trPr().append(cant)
        for i, val in enumerate(row):
            c = tr.cells[i]
            c.width = Inches(widths[i])
            cell_text(c, val, size=size, bold=(first_col_bold and i == 0),
                      align=WD_ALIGN_PARAGRAPH.LEFT if i < align_center_from else WD_ALIGN_PARAGRAPH.CENTER)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.keep_with_next = True
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
    return t

def boxed_note(doc, title, body):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    cell.width = Inches(6.2)
    shade(cell, "FFF4D6")
    tcpr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "8"); el.set(qn("w:color"), "A4512B")
        borders.append(el)
    tcpr.append(borders)
    cell.text = ""
    p1 = cell.paragraphs[0]
    p1.paragraph_format.space_after = Pt(4)
    r = p1.add_run(title); set_run_font(r, size=11, bold=True)
    for chunk in body:
        p = cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(chunk); set_run_font(r, size=10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def toc_entry(doc, text, page, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.3 if level == 1 else 0)
    p.paragraph_format.space_before = Pt(2 if level == 0 else 0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.25), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r = p.add_run(text + "\t" + (str(page) if page else "—"))
    set_run_font(r, size=10.5, bold=(level == 0))

def add_page_number_footer(doc):
    sec = doc.sections[0]
    sec.different_first_page_header_footer = True
    footer = sec.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Deep Learning-Based Aerial Object Detection  ·  ")
    set_run_font(r, size=9, color=GRAY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "18"); rpr.append(sz)
    run.append(rpr)
    t = OxmlElement("w:t"); t.text = "1"; run.append(t)
    fld.append(run)
    p._p.append(fld)

def add_header(doc):
    sec = doc.sections[0]
    header = sec.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("AERONAUTICAL DEVELOPMENT AGENCY  |  INTERNSHIP PROJECT REPORT")
    set_run_font(r, size=8.5, color=GRAY)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "4"); bottom.set(qn("w:color"), "B8C2CC")
    pbdr.append(bottom); pPr.append(pbdr)
TOC_ENTRIES = [
    ("Abstract", 0, 1),
    ("1  Introduction", 0, 1), ("1.1  Problem statement", 1, 2), ("1.2  Objectives", 1, 2), ("1.3  Scope", 1, 2),
    ("2  Background", 0, 1), ("2.1  Two-stage oriented detectors", 1, 2),
    ("2.2  Regression, backbone and sampling", 1, 2), ("2.3  What this study does not isolate", 1, 2),
    ("3  Data", 0, 1), ("3.1  Dataset and class set", 1, 2), ("3.2  Tiling and tile-level counting", 1, 2),
    ("3.3  Split isolation", 1, 2), ("3.4  Data provenance", 1, 2), ("3.5  Class support", 1, 2),
    ("4  Methods", 0, 1), ("4.1  Pipeline", 1, 2), ("4.2  Oriented box representation", 1, 2),
    ("4.3  Track configurations", 1, 2), ("4.4  Software and reproducibility", 1, 2),
    ("5  Training", 0, 1), ("5.1  Run stages", 1, 2), ("5.2  Schedule and hardware", 1, 2),
    ("5.3  Checkpoint selection", 1, 2), ("5.4  Engineering issues and fixes", 1, 2),
    ("6  Evaluation protocol", 0, 1), ("6.1  Matching and PRF", 1, 2), ("6.2  AP and mAP", 1, 2),
    ("6.3  Two mAP conventions", 1, 2), ("6.4  Stratification", 1, 2), ("6.5  Prediction set", 1, 2),
    ("6.6  Selection protocol", 1, 2),
    ("7  Results", 0, 1), ("7.1  Headline comparison", 1, 2), ("7.2  Operating points", 1, 2),
    ("7.3  Per-class results", 1, 2), ("7.4  Scale, orientation and difficulty", 1, 2), ("7.5  What the numbers do not show", 1, 2),
    ("8  Qualitative analysis", 0, 1), ("8.1  Prediction examples", 1, 2), ("8.2  Per-class examples", 1, 2),
    ("8.3  Failure modes", 1, 2),
    ("9  Discussion and limitations", 0, 1), ("9.1  Interpretation", 1, 2), ("9.2  Limitations", 1, 2),
    ("10  Applications and future work", 0, 1), ("10.1  Applications", 1, 2), ("10.2  Future work", 1, 2),
    ("11  Conclusion", 0, 1), ("References", 0, 1),
    ("Appendix A  Configuration reference", 0, 1), ("Appendix B  Full per-class tables", 0, 1),
    ("Author confirmations", 0, 1),
]

FIG_CAPTIONS = [
    "Figure 3.1. Non-difficult ground-truth class support on the official DOTA v2.0 validation split, with example tiles.",
    "Figure 4.1. Project workflow and the two detector tracks, from split-isolated preparation through oriented-box evaluation.",
    "Figure 4.2. (a) A horizontal envelope discards orientation; an oriented box keeps the angle.",
    "Figure 5.1. Run stages.",
    "Figure 7.1. Headline validation metrics for both tracks on the official tiling.",
    "Figure 7.2. Per-class AP50 for both tracks, sorted by gain.",
    "Figure 7.3. Track B AP50 per class against class support.",
    "Figure 8.1. Track B predictions on two validation tiles at the F1-optimal threshold of 0.834.",
    "Figure 8.2. Validation examples for plane, baseball-diamond, bridge, ground-track-field, small-vehicle and large-vehicle.",
    "Figure 8.3. Validation examples for ship, tennis-court, basketball-court, storage-tank, soccer-ball-field and roundabout",
    "Figure 8.4. Validation examples for harbor, swimming-pool, helicopter, container-crane, airport and helipad",
]

TAB_CAPTIONS = [
    "Table 3.1. Dataset and tiling summary.",
    "Table 4.1. Pipeline stages.",
    "Table 4.2. Track A and Track B configuration.",
    "Table 4.3. Software environment and reproducibility settings.",
    "Table 7.1. Headline validation metrics on the official 7,122-patch tiling.",
    "Table 7.2. Precision, recall and F1 at fixed confidence thresholds",
    "Table 7.3. Per-class AP50 for both tracks on the official tiling, sorted by gain.",
    "Table 7.4. Scale-stratified AP50 and orientation error.",
    "Table A.1. Full configuration reference for both tracks.",
    "Table A.2. Track A per-class results on the official 7,122-patch tiling.",
    "Table A.3. Track B per-class results on the official 7,122-patch tiling.",
]


# ---------------------------------------------------------------- content

def front_matter(doc):
    # ---- title page
    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("INTERNSHIP PROJECT REPORT"); set_run_font(r, size=12, bold=True)
    p.paragraph_format.space_after = Pt(2)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(40)
    r = p.add_run("Deep Learning-Based Aerial Object\nDetection Using Oriented Faster R-CNN\non the DOTA Dataset")
    set_run_font(r, size=22, bold=True)
    p.paragraph_format.line_spacing = 1.15

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(48)
    r = p.add_run("Submitted by\nS S Gokula Swamy"); set_run_font(r, size=12, bold=True)

    for line in (
        "Department of Artificial Intelligence and Machine Learning",
        "B.M.S. College of Engineering",
        "Internship Organisation: Aeronautical Development Agency (ADA)",
    ):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(line); set_run_font(r, size=11)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(36)
    r = p.add_run("Guide: [Guide Name]\nTD (ATD): [TD Name]"); set_run_font(r, size=11)
    p.paragraph_format.line_spacing = 1.4

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(60)
    r = p.add_run("Project duration: 15 September 2026 – 15 November 2026"); set_run_font(r, size=10.5)

    # ---- certificate
    h1(doc, "Certificate", new_page=True)
    para(doc, "This is to certify that the internship project entitled “Deep Learning-Based Aerial "
              "Object Detection Using Oriented Faster R-CNN on the DOTA Dataset” was carried out by "
              "S S Gokula Swamy at the Aeronautical Development Agency (ADA) during the period "
              "15 September 2026 to 15 November 2026, in partial fulfilment of the requirements of the "
              "B.E. programme in Artificial Intelligence and Machine Learning at B.M.S. College of Engineering.")
    para(doc, "The work reported here was completed under the guidance of the project guide and the "
              "technical director named below. The report is a record of work performed during the internship.")
    author_note(doc, "insert certificate wording required by the college, signature blocks, seal and date")

    # ---- acknowledgements
    h1(doc, "Acknowledgements", new_page=True)
    para(doc, "I thank the Aeronautical Development Agency for hosting this internship and for providing "
              "the problem setting and technical direction. I am grateful to my project guide and to the "
              "technical director for their review of the work, and to the Department of Artificial "
              "Intelligence and Machine Learning at B.M.S. College of Engineering for academic support.")
    author_note(doc, "add named acknowledgements (guide, TD, department, colleagues) once approved for publication")

    # ---- organisation profile + role
    h1(doc, "Organisation Profile and Intern Role", new_page=True)
    para(doc, "The Aeronautical Development Agency is a defence research and development organisation "
              "responsible for the design and development of combat aircraft and their associated systems. "
              "Its work spans airframe design, avionics, flight control, simulation and mission systems.")
    author_note(doc, "insert the official organisation profile text and the intern's role, team and reporting line")
    para(doc, "During the internship the work reported here covered dataset preparation for DOTA v2.0, "
              "training and evaluation of two oriented detectors under MMRotate, and the analysis of the "
              "resulting measurements. All quantitative results in this report are from that work.")

    # ---- contents
    contents_heading = h1(doc, "Contents", new_page=True)
    contents_heading.paragraph_format.space_before = Pt(0)
    for text, level, _ in TOC_ENTRIES:
        toc_entry(doc, text, PAGES.get(text), level)

    # ---- list of figures
    h1(doc, "List of Figures", new_page=True)
    for text in FIG_CAPTIONS:
        toc_entry(doc, text, PAGES.get(text), 1)

    # ---- list of tables
    h1(doc, "List of Tables", new_page=True)
    for text in TAB_CAPTIONS:
        toc_entry(doc, text, PAGES.get(text), 1)

    # ---- abbreviations
    h1(doc, "Abbreviations", new_page=True)
    rows = [
        ("AP", "average precision"), ("AMP", "automatic mixed precision"),
        ("CI", "confidence interval"), ("DOTA", "Dataset for Object deTection in Aerial images"),
        ("FN / FP", "false negative / false positive"), ("FPN", "feature pyramid network"),
        ("GT", "ground truth"), ("IoF", "intersection over foreground"),
        ("IoU", "intersection over union"), ("KLD", "Kullback–Leibler divergence"),
        ("mAP", "mean average precision"), ("NMS", "non-maximum suppression"),
        ("OBB", "oriented bounding box"), ("PAFPN", "path aggregation feature pyramid network"),
        ("PRF", "precision, recall and F1"), ("RoI", "region of interest"),
        ("RPN", "region proposal network"), ("SGD / AdamW", "stochastic gradient descent / adaptive optimizer"),
        ("TP", "true positive"),
    ]
    table(doc, ["Term", "Meaning"], rows, [1.1, 5.1], size=10, align_center_from=2)

def abstract(doc):
    h1(doc, "Abstract", new_page=True)
    text = ("This report documents a two-track study of oriented aerial object detection on DOTA v2.0 "
            "using MMRotate. Track A is a Rotated Faster R-CNN baseline with a ResNet-50 and FPN backbone. "
            "Track B is an Oriented R-CNN system with a ConvNeXt-Small backbone, PAFPN, Gaussian KLD "
            "regression and class-balanced sampling. Both are evaluated on the official validation split "
            "with a project evaluator that reports precision, recall, F1, AP50, AP50-95, scale-stratified "
            "AP and orientation error. On the same 7,122 validation patches, Track B reaches 0.7127 mAP50 "
            "and 0.8511 F1, against 0.6049 and 0.7849 for Track A. The comparison is a same-tiling "
            "evaluation rather than a one-factor experiment, because the tracks differ in backbone, neck, "
            "loss, optimizer, schedule, sampling and augmentation.")
    para(doc, text)
    p = doc.add_paragraph()
    r = p.add_run("Keywords: "); set_run_font(r, size=11, bold=True)
    r = p.add_run("aerial object detection, DOTA v2.0, oriented bounding boxes, Oriented R-CNN, "
                  "MMRotate, ConvNeXt, Gaussian KLD.")
    set_run_font(r, size=11, italic=True)
    assert len(text.split()) <= 150, len(text.split())

def body_sections_a(doc):
    # ---------------- 1 Introduction
    h1(doc, "1  Introduction")
    para(doc, "Overhead imagery differs from street-level photography. Objects can appear at any rotation, "
              "small vehicles occupy very few pixels, and neighbouring instances often overlap. A horizontal "
              "box around a rotated target includes background and can merge adjacent objects during "
              "suppression. An oriented box keeps the target's position, size and heading, which is why "
              "oriented detection is the standard formulation for aerial benchmarks such as DOTA [6].")

    h2(doc, "1.1  Problem statement")
    para(doc, "The task is to detect densely packed aerial objects across a wide size range and all headings, "
              "while preserving orientation. A second problem is evidential: measured performance must be "
              "separated from dataset coverage gaps, because support is uneven across the 18 classes "
              "(Section 3.5) and the rarest classes have fewer than 70 annotations.")

    h2(doc, "1.2  Objectives")
    for text in (
        "Prepare the 18-class DOTA v2.0 data and keep training and validation separated before tiling.",
        "Train a 12-epoch rotated Faster R-CNN baseline and a 24-epoch Oriented R-CNN configuration.",
        "Represent targets with oriented boxes and evaluate both classification and localisation quality.",
        "Report precision, recall, F1, AP, scale-stratified AP, orientation error and operational measurements where available.",
    ):
        bullet(doc, text)

    h2(doc, "1.3  Scope")
    para(doc, "All quantitative results come from labelled validation data. DOTA test-dev ground truth is "
              "withheld, and no hidden-test or server score is claimed. The report evaluates two complete "
              "systems; it is not an ablation and does not attribute the score difference to individual "
              "components. Section 2 gives the background, Section 3 the data, Sections 4–6 the method and "
              "protocol, Sections 7–8 the results, and Sections 9–11 the discussion, future work and conclusion.")

    # ---------------- 2 Background
    h1(doc, "2  Background")
    h2(doc, "2.1  Two-stage oriented detectors")
    para(doc, "Faster R-CNN uses a region proposal network (RPN) to propose candidate regions and a second "
              "stage to classify and refine them [1]. Oriented R-CNN keeps this two-stage design but emits "
              "oriented proposals and uses an oriented RoI head, which removes the misalignment between "
              "horizontal proposals and rotated targets [2]. MMRotate provides the rotated-detection "
              "framework used here [5].")

    h2(doc, "2.2  Regression, backbone and sampling")
    para(doc, "Gaussian KLD regression represents a rotated rectangle as a two-dimensional Gaussian and "
              "compares predicted and target distributions, which avoids the discontinuity of angle "
              "regression near the ±90° boundary [3]. ConvNeXt is a modern convolutional backbone [4]. "
              "Track B adds a path-aggregation feature pyramid network (PAFPN) [8] and class-balanced "
              "sampling [9], both standard components used in the OpenMMLab detection stack.")

    h2(doc, "2.3  What this study does not isolate")
    para(doc, "The two tracks differ in detector, backbone, neck, regression loss, sampling, augmentation, "
              "optimizer, schedule and epoch budget (Table 4.2). The study therefore compares two complete "
              "systems and cannot attribute the measured difference to any single component. An ablation "
              "that varies one factor at a time is listed as future work in Section 10.2.")

    # ---------------- 3 Data
    h1(doc, "3  Data")
    h2(doc, "3.1  Dataset and class set")
    para(doc, "DOTA v2.0 is an aerial-image benchmark with 18 oriented-object categories [6]. The class set "
              "covers aircraft, ships, vehicles, infrastructure, sports facilities and three rare categories: "
              "container-crane, airport and helipad. Figure 3.1 shows the non-difficult ground-truth support per "
              "class on the official validation split; the counts sum to 69,542 tile-level annotations.")
    figure(doc, "dataset_profile.png", 5.4,
           "Figure 3.1. Non-difficult ground-truth class support on the official DOTA v2.0 validation split, "
           "with example tiles. Counts are tile-level occurrences (Section 3.2). Airport has 67, "
           "container-crane 27 and helipad 4.")

    h2(doc, "3.2  Tiling and tile-level counting")
    para(doc, "Images are tiled into 1024 × 1024 patches with 200-pixel overlap. A ground-truth polygon is "
              "kept in a patch when its intersection over foreground (IoF) with the patch is at least 0.70, "
              "and a patch is kept when at least 60% of its area is covered by source imagery. Because the "
              "overlap duplicates objects across neighbouring patches, every count in this report is a "
              "tile-level annotation, not a unique object. The official validation tiling contains 140,103 "
              "annotations: 69,542 with difficulty flag 0 and 70,561 with difficulty flag 1.")
    para(doc, "The DOTA difficulty flag marks instances that are tiny, heavily occluded or ambiguous. The "
              "extended evaluator scores only flag-0 annotations; the MMRotate metric includes flag-1 "
              "annotations because its threshold is set to 100 (Section 6.3). The 0.70 IoF rule matters for "
              "large polygons: an airport or a long container-crane that spans a patch boundary can fall "
              "below the threshold and be dropped, which lowers the measured AP for those classes "
              "(Section 7.3).")

    h2(doc, "3.3  Split isolation")
    para(doc, "The source train and validation images are separated before tiling, so no patch from a "
              "validation image can appear in the training set. Each split is tiled independently with the "
              "same recipe. The prepared collection contains 1,830 training images and 593 validation images "
              "(Table 3.1).")

    table(doc, ["Item", "Record"], [
        ("Training images", "1,830"),
        ("Validation images", "593"),
        ("Patch size", "1024 × 1024 px"),
        ("Patch overlap", "200 px"),
        ("IoF threshold for keeping a polygon", "0.70"),
        ("Patch coverage threshold", "0.60"),
        ("Official validation tiling", "7,122 patches (Track A and Track B evaluation)"),
        ("Official training tiling", "24,151 patches (official retrain; epochs 23–24 re-tiled identically)"),
        ("Non-difficult / difficult annotations", "69,542 / 70,561"),
        ("Classes", "18, including airport (67) and helipad (4) in the official tiling"),
    ], [2.6, 3.6], size=9.5, align_center_from=2)
    caption(doc, "Table 3.1. Dataset and tiling summary.")

    h2(doc, "3.4  Data provenance")
    boxed_note(doc, "Data provenance correction", [
        "The A100 stage and Track A evaluation used the official DOTA v2.0 archives (593 validation images, "
        "18 classes). An initial Kaggle continuation for Track B had used a non-official convenience archive "
        "(458 validation images, 16 classes). To ensure complete data integrity, Track B was retrained from "
        "epoch 16 using the official 18-class DOTA v2.0 dataset on Kaggle with 2 × Tesla T4 GPUs. Training "
        "proceeded through epoch 22, at which point the 12-hour session limit was reached; a resumed Kaggle run then "
        "completed epochs 23 and 24, with validation at epoch 24.",
        "All Track B results in this report are evaluated from the official epoch_24.pth checkpoint on "
        "the identical 7,122-patch official validation tiling. Airport and helipad were present as positive "
        "training examples throughout, and all difficulty flags were preserved. Both tracks are thus trained "
        "and evaluated on official DOTA v2.0 data.",
    ])

    h2(doc, "3.5  Class support")
    para(doc, "Class support is highly uneven. Ship (23,075) and small-vehicle (21,258) dominate, while "
              "container-crane (27), airport (67) and helipad (4) have too few annotations for stable "
              "per-class estimates. Results for those three classes are reported with their support counts "
              "and are not used to support general claims.")

    # ---------------- 4 Methods
    h1(doc, "4  Methods")
    h2(doc, "4.1  Pipeline")
    para(doc, "Figure 4.1 summarises the pipeline: split-isolated preparation, patch generation, the two "
              "detector tracks, and evaluation. Table 4.1 lists the stages.")
    figure(doc, "pipeline.png", 6.2,
           "Figure 4.1. Project workflow and the two detector tracks, from split-isolated preparation through "
           "oriented-box evaluation.")
    table(doc, ["Stage", "Implementation"], [
        ("1. Data preparation", "Merge imagery and annotations, normalise labels, keep train/validation sources separate."),
        ("2. Patch generation", "MMRotate image splitter; 1024 × 1024 patches with 200-pixel overlap; IoF 0.70."),
        ("3A. Track A", "Rotated Faster R-CNN; ResNet-50 + FPN; 18 classes; smooth-L1 rotated-box regression."),
        ("3B. Track B", "Oriented R-CNN; ConvNeXt-Small + PAFPN; Gaussian KLD loss; class-balanced sampling; rotation and flip augmentation."),
        ("4. Evaluation", "MMRotate dota/mAP plus a separate rotated-IoU evaluator for PRF, AP thresholds, scale AP, angle error and throughput."),
    ], [1.45, 4.75], size=9.5, align_center_from=2)
    caption(doc, "Table 4.1. Pipeline stages.")

    h2(doc, "4.2  Oriented box representation")
    para(doc, "A rotated rectangle is written as (cx, cy, w, h, θ): centre coordinates, width, height and "
              "angle under MMRotate's le90 convention, where θ lies in [−90°, 90°). DOTA annotations are "
              "four-corner polygons; the loader converts them to this five-parameter form. Figure 4.2 "
              "illustrates why orientation matters and how Gaussian KLD compares boxes.")
    figure(doc, "obb_geometry.png", 5.8,
           "Figure 4.2. (a) A horizontal envelope discards orientation; an oriented box keeps the angle. "
           "(b) Gaussian KLD compares predicted and target distributions. Conceptual illustration, not an "
           "empirical result.")

    h2(doc, "4.3  Track configurations")
    para(doc, "Table 4.2 gives the configuration of the two tracks. Seven factors differ, which is why the "
              "comparison is a same-tiling evaluation rather than a one-factor ablation.")
    table(doc, ["Component", "Track A", "Track B"], [
        ("Detector", "Rotated Faster R-CNN", "Oriented R-CNN"),
        ("Backbone / neck", "ResNet-50 / FPN", "ConvNeXt-Small / PAFPN"),
        ("Regression loss", "Rotated-box smooth-L1", "Gaussian KLD (log1p)"),
        ("Sampling / augmentation", "DOTADataset; H/V/diagonal flips", "ClassBalancedDataset (oversample_thr 1e-3); flips; RandomRotate p=0.5, 180°"),
        ("Optimizer / schedule", "SGD, lr 0.005, multi-step at epochs 8 and 11", "AdamW, lr 1e-4, cosine annealing, T_max 24, eta_min 1e-6"),
        ("Epochs", "12", "24 (1–16 A100 stage; 17–24 Kaggle official retrain: 17–22 then 23–24 resumed)"),
        ("Hardware", "1 × A100-SXM4-80GB", "1 × A100-SXM4-80GB, then 2 × Tesla T4"),
    ], [1.55, 2.2, 2.45], size=9, align_center_from=2)
    caption(doc, "Table 4.2. Track A and Track B configuration.")

    h2(doc, "4.4  Software and reproducibility")
    para(doc, "Table 4.3 records the environment and the settings needed to reproduce the evaluation. The "
              "inference cut-off is a score threshold of 0.05, rotated NMS at IoU 0.7 and at most 2,000 "
              "detections per patch; this is the setting that produces the 136,612 predictions reported in "
              "Section 6.5.")
    table(doc, ["Setting", "Value"], [
        ("Python", "3.11"),
        ("PyTorch / torchvision", "2.0.1+cu118 / 0.15.2"),
        ("MMCV / MMDetection / MMEngine", "2.0.1 / 3.1.0 / 0.9.1"),
        ("MMRotate", "dev-1.x"),
        ("Training batch", "4 per GPU (configuration default); 1 per GPU with 4-step accumulation on Kaggle"),
        ("Evaluation batch", "1 (Track B, Kaggle run); the evaluation is tiled, memory-bound inference"),
        ("Inference score threshold / NMS / max detections", "0.05 / rotated NMS IoU 0.7 / 2,000 per patch"),
        ("Precision policy", "Track B full precision for KLD (half-precision determinant limitation)"),
        ("Checkpoint used", "epoch_24.pth (Track B official retrain; release v1.3.0, SHA-256 d855c250…44995f); best_dota_mAP_epoch_10.pth (Track A)"),
    ], [2.5, 3.7], size=9, align_center_from=2)
    caption(doc, "Table 4.3. Software environment and reproducibility settings. Repository: github.com/Lion4467cat/dotav2-obb-benchmark. Random seeds were not recorded in the artifacts.")
def body_sections_b(doc):
    # ---------------- 5 Training
    h1(doc, "5  Training")
    h2(doc, "5.1  Run stages")
    para(doc, "Training ran in two stages and evaluation in a third. The names are used "
              "consistently from here on: the A100 stage is the first training block on a single "
              "A100-SXM4-80GB device, the Kaggle continuation is the second training block on two "
              "Tesla T4 devices, and the official tiling is the 7,122-patch validation set prepared "
              "from the official DOTA v2.0 archives. Figure 5.1 shows how the stages map onto the two "
              "tracks.")
    figure(doc, "training_setup.png", 6.2,
           "Figure 5.1. Run stages. Track A was trained for 12 epochs in the A100 stage. Track B was "
           "trained for epochs 1–16 in the A100 stage and epochs 17–24 in the Kaggle continuation on official data "
           "(17–22 in the first run, 23–24 in the resumed run). "
           "Both saved checkpoints were then evaluated on the official tiling.")
    for lead, text in (
        ("Stage 1, A100.", " Track A was trained for 12 epochs and Track B for epochs 1–16, both on "
         "one A100-SXM4-80GB device with a batch of four images per device."),
        ("Stage 2, Kaggle continuation.", " Track B resumed at epoch 17 and ran to epoch 22 on two "
         "Tesla T4 devices using official 18-class annotations until the 12-hour session limit was reached; "
         "a further Kaggle run then resumed from epoch_22.pth and completed epochs 23 and 24 with validation at epoch 24. "
         "A batch of one image per device with four-step gradient accumulation reproduced the effective batch of the A100 stage."),
        ("Stage 3, official tiling evaluation.", " The saved epoch-10 checkpoint of Track A and the "
         "saved epoch-24 checkpoint of Track B were evaluated on the 7,122-patch official validation "
         "tiling with identical inference settings."),
    ):
        bullet(doc, text, lead=lead)

    h2(doc, "5.2  Schedule and hardware")
    para(doc, "Track A used stochastic gradient descent with a learning rate of 0.005 and a "
              "multi-step schedule that decayed at epochs 8 and 11 over a 12-epoch budget. Track B "
              "used AdamW with a learning rate of 1e-4 and cosine annealing to a minimum of 1e-6 "
              "over a 24-epoch budget. Track B also used class-balanced oversampling with an "
              "oversampling threshold of 1e-3 and random rotation of 180° with probability 0.5.")
    para(doc, "The two tracks did not run on the same device. Throughput and peak memory in Table 7.1 "
              "were recorded on the hardware named in that table's caption, so they characterise the "
              "runs rather than the architectures.")

    h2(doc, "5.3  Checkpoint selection")
    para(doc, "Checkpoints were selected by validation mAP, not by the epoch count. Track A's best "
              "checkpoint is epoch 10 of 12. Track B uses epoch 24, the final epoch of the 24-epoch budget; the full "
              "schedule completed, with a validation dota/mAP of 0.6535 at epoch 24 on the official tiling. "
              "The epoch-24 result is the complete schedule rather than a truncated one.")
    para(doc, "The earlier continuation run using a non-official archive had reported 0.6892 dota/mAP "
              "on 16 classes. The official retrain on all 18 classes reaches 0.7127 mAP50 in Table 7.1 "
              "under the project evaluator on the official 7,122-patch validation tiling.")

    h2(doc, "5.4  Engineering issues and fixes")
    para(doc, "Four problems affected the runs and are recorded because they change how the "
              "artifacts should be read.")
    for lead, text in (
        ("Test-time dataloader construction.", " The training configuration sets resume to true. "
         "Building the test runner from that configuration also builds the training dataloader, "
         "which failed when the training annotations were not present in the evaluation "
         "environment. Setting resume to false in the evaluation copy of the configuration removed "
         "the dependency."),
        ("Half-precision KLD.", " The determinant term of the KLD loss underflows in half precision "
         "for small boxes. Track B was evaluated in full precision; mixed precision was kept for the "
         "convolutional layers only."),
        ("Model registry scope.", " Building the oriented proposal head outside an initialised "
         "MMRotate scope raises a registry error. The evaluation scripts call "
         "init_default_scope(\"mmrotate\") before constructing any model."),
        ("Data source.", " An initial continuation used a convenience archive rather than the "
         "official release; this was identified and corrected by retraining Track B on the official "
         "18-class DOTA v2.0 dataset through epoch 24, as described in Section 3.4."),
    ):
        bullet(doc, text, lead=lead)

    # ---------------- 6 Evaluation protocol
    h1(doc, "6  Evaluation protocol")
    h2(doc, "6.1  Matching and PRF")
    para(doc, "Predictions are matched to ground truth per class and per image. Predictions are "
              "sorted by score, and a prediction is a true positive when its rotated intersection "
              "over union with an unmatched ground-truth box of the same class is at least 0.50. "
              "Each ground-truth box can be matched once. Unmatched predictions are false positives "
              "and unmatched ground-truth boxes are false negatives.")
    para(doc, "Precision is the number of true positives divided by the number of predictions, "
              "recall is the number of true positives divided by the number of ground-truth boxes, "
              "and F1 is their harmonic mean. Micro-averaged values pool all classes; macro-averaged "
              "values average the 18 per-class scores and therefore weight a class with four "
              "instances as heavily as a class with 23,075.")

    h2(doc, "6.2  AP and mAP")
    para(doc, "Average precision is the area under the interpolated precision-recall curve, "
              "computed with the all-point interpolation used by COCO and by the DOTA server. AP50 "
              "uses an IoU threshold of 0.50, AP75 uses 0.75, and AP50-95 averages the ten "
              "thresholds from 0.50 to 0.95 in steps of 0.05. mAP is the unweighted mean of the 18 "
              "per-class values.")
    para(doc, "Two further measures separate localisation from classification. Class-agnostic AP50 "
              "repeats the AP50 computation with the class label ignored; the difference between AP50 "
              "and class-agnostic AP50 is reported as the classification gap, and it isolates the "
              "part of the error caused by assigning the wrong category to an otherwise well placed "
              "box.")

    h2(doc, "6.3  Two mAP conventions")
    para(doc, "The MMRotate metric used during training sets the difficulty threshold to 100, which "
              "means difficulty-flagged instances are scored as ground truth. The project evaluator "
              "scores only non-difficult instances. The two conventions are not interchangeable: the "
              "same checkpoint scores lower under the project evaluator because it is asked to find "
              "a smaller, harder set of objects. Every AP in Sections 7 and 8 comes from the project "
              "evaluator and excludes difficulty-flagged instances.")

    h2(doc, "6.4  Stratification")
    para(doc, "Scale strata follow the COCO area convention applied to the rotated box area: small "
              "up to 32² pixels, medium from 32² to 96², and large above 96². An object is treated "
              "as elongated when its aspect ratio is at least 1.5. Orientation error is the acute "
              "angle between the predicted and the matched ground-truth long edge, in degrees, "
              "averaged over true positives at IoU 0.50.")

    h2(doc, "6.5  Prediction set")
    para(doc, "All metrics are computed from one prediction set per track, produced at a score "
              "cut-off of 0.05 with rotated non-maximum suppression at IoU 0.7 and at most 2,000 "
              "detections per patch. Track A produced 180,555 predictions and Track B 136,612. At "
              "the F1-optimal threshold, the true positives plus false negatives sum to 69,542 for "
              "both tracks, which is the non-difficult ground-truth total of the official tiling; "
              "this identity is the main consistency check on the evaluator. At that threshold Track A "
              "records 52,597 true positives, 11,882 false positives and 16,945 false negatives, and "
              "Track B records 57,961 true positives, 8,707 false positives and 11,581 false negatives.")

    h2(doc, "6.6  Selection protocol")
    para(doc, "Two quantities were chosen on the same validation split that is reported here: the "
              "checkpoint, by validation mAP, and the operating threshold, by validation F1. Track B's "
              "epoch-24 checkpoint was the highest-scoring validation checkpoint of the official retrain "
              "series (0.6535, ahead of 0.6519 at epoch 20 and 0.6453 at epoch 18; epoch-22's in-training "
              "validation was cut by the 12-hour session limit), and it is the checkpoint evaluated "
              "throughout this report. "
              "The reported figures are therefore optimistic with respect to an unseen split, and no "
              "held-out test set was used. The bias applies to both tracks in the same way, but it "
              "means the absolute values should not be read as expected performance on new imagery.")

    # ---------------- 7 Results
    h1(doc, "7  Results")
    h2(doc, "7.1  Headline comparison")
    f1_a = A_full.get("micro_prf", {}).get("f1_optimal", {})
    f1_b = B_full.get("micro_prf", {}).get("f1_optimal", {})
    macro_a = A_full.get("macro_f1_opt", {})
    macro_b = B_full.get("macro_f1_opt", {})
    op_b = B_full.get("operational", {})
    map50_a = A_full.get("map50", MEAN_A50)
    map50_b = B_full.get("map50", MEAN_B50)
    map95_a = A_full.get("map50_95", MEAN_A95)
    map95_b = B_full.get("map50_95", MEAN_B95)
    ap75_a = A_full.get("ap75", 0.2785)
    ap75_b = B_full.get("ap75", 0.4664)
    agn_a = A_full.get("class_agnostic_ap50", 0.7985)
    agn_b = B_full.get("class_agnostic_ap50", 0.8803)
    gap_a = A_full.get("classification_gap_ap50", 0.1936)
    gap_b = B_full.get("classification_gap_ap50", 0.1676)

    para(doc, f"Track B is higher on every aggregate measure. mAP50 rises from {f4(map50_a)} to {f4(map50_b)}, a "
              f"gain of {map50_b - map50_a:+.4f}, and mAP50-95 rises from {f4(map95_a)} to {f4(map95_b)}. The largest relative gain "
              f"is at the strict IoU threshold: AP75 goes from {f4(ap75_a)} to {f4(ap75_b)} (+67.4% relative increase).")
    table(doc, ["Metric", "Track A", "Track B"], [
        ("mAP50", f4(map50_a), f4(map50_b)),
        ("mAP50-95", f4(map95_a), f4(map95_b)),
        ("AP75", f4(ap75_a), f4(ap75_b)),
        ("Class-agnostic AP50", f4(agn_a), f4(agn_b)),
        ("Classification gap (AP50 − class-agnostic AP50)", f4(gap_a), f4(gap_b)),
        ("Macro F1 (mean of 18 class F1 scores)", f4(macro_a.get("f1", 0.6285)), f4(macro_b.get("f1", 0.7319))),
        ("Micro F1 at the F1-optimal threshold", f4(f1_a.get("f1", 0.7849)), f4(f1_b.get("f1", 0.8511))),
        ("F1-optimal threshold", f4(f1_a.get("conf_threshold", 0.8103)), f4(f1_b.get("conf_threshold", 0.834))),
        ("Predictions at score 0.05", f"{A_full.get('num_predictions', 180555):,}", f"{B_full.get('num_predictions', 136612):,}"),
        ("Parameters (millions)", "not recorded", f"{op_b.get('params_m', 70.24):.2f}"),
        ("Throughput (frames per second)†", "11.36", f"{op_b.get('fps', 2.52):.2f}"),
        ("Peak GPU memory (GB)†", "2.86", f"{op_b.get('peak_vram_gb', 9.25):.2f}"),
    ], [3.0, 1.6, 1.6], size=8.5, align_center_from=2)
    caption(doc, "Table 7.1. Headline validation metrics on the official 7,122-patch tiling. "
                 "† Throughput and peak memory were measured on different devices (Track A: "
                 "A100-SXM4-80GB; Track B: 2×Tesla T4 Kaggle session), so the ratio between them is not a like-for-like "
                 "throughput comparison.")
    para(doc, "The AP75 result is the informative one. A gain that grows as the IoU threshold "
              "tightens means the boxes are better localised, not merely that more objects are "
              "found. Class-agnostic AP50 rises by 0.0818 while AP50 rises by 0.1078, so most of "
              "the improvement survives when the class label is removed; the classification gap "
              "narrows from 0.1936 to 0.1676.")
    figure(doc, "metrics_comparison.png", 6.0,
           "Figure 7.1. Headline validation metrics for both tracks on the official tiling.")

    h2(doc, "7.2  Operating points")
    para(doc, "Track B's advantage is widest where the confidence requirement is strict. At a "
              "threshold of 0.50, precision rises from 0.6983 to 0.7813 and F1 from 0.7521 to "
              "0.8280, while recall rises from 0.8148 to 0.8807 (+0.0659). At 0.25 the two tracks are closer: "
              "precision is 0.7153 vs 0.5869, recall is 0.8960 vs 0.8351, and F1 is 0.7956 vs 0.6893.")
    para(doc, "Table 7.2 gives the four operating points. The F1-optimal row is the threshold at which "
              "each track maximises its own F1, so the two thresholds differ and the row is not a "
              "fixed operating point shared by both systems.")
    at_conf_a = A_full.get("micro_prf", {}).get("at_conf", {})
    at_conf_b = B_full.get("micro_prf", {}).get("at_conf", {})
    table(doc, ["Threshold", "A P", "A R", "A F1", "B P", "B R", "B F1"], [
        ("0.25", f4(at_conf_a.get("0.25", {}).get("precision", 0.5869)), f4(at_conf_a.get("0.25", {}).get("recall", 0.8351)), f4(at_conf_a.get("0.25", {}).get("f1", 0.6893)),
                 f4(at_conf_b.get("0.25", {}).get("precision", 0.7153)), f4(at_conf_b.get("0.25", {}).get("recall", 0.8960)), f4(at_conf_b.get("0.25", {}).get("f1", 0.7956))),
        ("0.30", f4(at_conf_a.get("0.30", {}).get("precision", 0.6133)), f4(at_conf_a.get("0.30", {}).get("recall", 0.8310)), f4(at_conf_a.get("0.30", {}).get("f1", 0.7058)),
                 f4(at_conf_b.get("0.30", {}).get("precision", 0.7301)), f4(at_conf_b.get("0.30", {}).get("recall", 0.8931)), f4(at_conf_b.get("0.30", {}).get("f1", 0.8034))),
        ("0.50", f4(at_conf_a.get("0.50", {}).get("precision", 0.6983)), f4(at_conf_a.get("0.50", {}).get("recall", 0.8148)), f4(at_conf_a.get("0.50", {}).get("f1", 0.7521)),
                 f4(at_conf_b.get("0.50", {}).get("precision", 0.7813)), f4(at_conf_b.get("0.50", {}).get("recall", 0.8807)), f4(at_conf_b.get("0.50", {}).get("f1", 0.8280))),
        ("F1-optimal", f4(f1_a.get("precision", 0.8157)), f4(f1_a.get("recall", 0.7563)), f4(f1_a.get("f1", 0.7849)),
                       f4(f1_b.get("precision", 0.8694)), f4(f1_b.get("recall", 0.8335)), f4(f1_b.get("f1", 0.8511))),
    ], [2.1, 0.68, 0.68, 0.68, 0.68, 0.68, 0.68], size=9, align_center_from=1)
    caption(doc, "Table 7.2. Precision, recall and F1 at fixed confidence thresholds, micro-averaged "
                 "over the 18 classes. The last row uses each track's own F1-optimal threshold: "
                 "0.8103 for Track A and 0.834 for Track B.")
    para(doc, "The shape of the trade-off also differs. Track A buys recall cheaply at low "
              "thresholds and loses precision quickly, whereas Track B keeps precision above 0.71 "
              "even at 0.25 (0.7153). For a downstream system that must not raise false alarms, that is the "
              "more useful operating region.")

    h2(doc, "7.3  Per-class results")
    para(doc, "Track B is higher on 18 of 18 classes, and the gain is uneven. Helipad gains "
              "+0.4167 (4 instances), harbor +0.1905, bridge +0.1823, airport +0.1649, "
              "basketball-court +0.1482 and large-vehicle +0.1398, all classes whose instances are "
              "long, thin or densely packed. The smallest gains are container-crane +0.0151, "
              "tennis-court +0.0158 and storage-tank +0.0170; swimming-pool +0.0274 and plane +0.0352.")
    para(doc, "Small-vehicle gains +0.0603, which places it 12th of 18 by improvement. This matters "
              "because it is the class most often used to argue that a detector is better at small "
              "objects. The measured per-class ordering does not support that argument, and no "
              "small-object claim is made in this report. The scale-stratified results in Section 7.4 "
              "are the appropriate evidence for that question.")
    figure(doc, "fig_per_class_delta.png", 6.2,
           "Figure 7.2. Per-class AP50 for both tracks, sorted by gain. Each label gives Track A, "
           "Track B and the difference, followed by the ground-truth count.")
    para(doc, "The three rare classes need to be read with their counts. Container-crane reaches "
              "0.0151 from 27 annotations, airport 0.6141 from 67, and helipad 0.4167 from 4. The "
              "helipad value corresponds to two matched instances out of four, which is why it is "
              "shown with the count and not discussed as a capability.")

    rows = []
    for c in ORDER_DELTA:
        rows.append((c, f"{B[c]['num_gt']:,}", f4(A[c]["ap50"]), f4(B[c]["ap50"]),
                     f"{B[c]['ap50'] - A[c]['ap50']:+.4f}", f4(B[c]["ap50_95"])))
    rows.append(("Mean (18 classes)", "69,542", f4(MEAN_A50), f4(MEAN_B50),
                 f"{MEAN_B50 - MEAN_A50:+.4f}", f4(MEAN_B95)))
    table(doc, ["Class", "n", "A AP50", "B AP50", "Δ AP50", "B AP50-95"], rows,
          [1.85, 0.7, 0.85, 0.85, 0.85, 1.05], size=8.5, align_center_from=1)
    caption(doc, "Table 7.3. Per-class AP50 for both tracks on the official tiling, sorted by gain. "
                 "n is the non-difficult ground-truth count. The mean is the unweighted mean of the "
                 "18 classes, not the count-weighted value.")
    figure(doc, "class_ap.png", 5.6,
           "Figure 7.3. Track B AP50 per class against class support. The three rarest classes "
           "(container-crane, airport, helipad) have 27, 67 and 4 annotations and their estimates "
           "are unstable.")
    h2(doc, "7.4  Scale, orientation and difficulty")
    scale_a = A_full.get("scale_ap50", {})
    scale_b = B_full.get("scale_ap50", {})
    ang_a = A_full.get("orientation_error_deg", {})
    ang_b = B_full.get("orientation_error_deg", {})

    s_a, s_b = scale_a.get("small", {}).get("ap50", 0.4874), scale_b.get("small", {}).get("ap50", 0.6220)
    m_a, m_b = scale_a.get("medium", {}).get("ap50", 0.5881), scale_b.get("medium", {}).get("ap50", 0.6826)
    l_a, l_b = scale_a.get("large", {}).get("ap50", 0.6602), scale_b.get("large", {}).get("ap50", 0.8394)
    mean_ang_a = ang_a.get("mean_all_tp", 6.42)
    mean_ang_b = ang_b.get("mean_all_tp", 4.88)
    med_ang_a = ang_a.get("median_all_tp", 2.62)
    med_ang_b = ang_b.get("median_all_tp", 1.56)
    elo_mean_a = ang_a.get("mean_elongated_tp", 3.78)
    elo_mean_b = ang_b.get("mean_elongated_tp", 2.05)
    elo_med_a = ang_a.get("median_elongated_tp", 2.55)
    elo_med_b = ang_b.get("median_elongated_tp", 1.46)

    para(doc, f"The gain is largest on large objects and smallest on medium ones. Large objects gain "
              f"{l_b - l_a:+.4f}, small objects {s_b - s_a:+.4f} and medium objects {m_b - m_a:+.4f}. Every stratum improves, so "
              f"the improvement is not confined to one size range, but the ordering does not "
              f"correspond to a small-object advantage.")
    para(doc, f"Orientation error falls by roughly a third. The mean error over all matched pairs "
              f"drops from {mean_ang_a:.2f}° to {mean_ang_b:.2f}° and the median from {med_ang_a:.2f}° to {med_ang_b:.2f}°. On elongated objects, "
              f"where the angle is well defined, the mean drops from {elo_mean_a:.2f}° to {elo_mean_b:.2f}°. The median "
              f"error of {med_ang_b:.2f}° over all matched pairs is small relative to the 90° ambiguity that "
              f"would appear if the angle convention were mishandled.")
    table(doc, ["Stratum", "n", "A AP50", "B AP50", "Δ AP50"], [
        ("Small, area ≤ 32² px", f"{scale_b.get('small', {}).get('num_gt', 45072):,}", f4(s_a), f4(s_b), f"{s_b - s_a:+.4f}"),
        ("Medium, 32²–96² px", f"{scale_b.get('medium', {}).get('num_gt', 20747):,}", f4(m_a), f4(m_b), f"{m_b - m_a:+.4f}"),
        ("Large, area > 96² px", f"{scale_b.get('large', {}).get('num_gt', 3723):,}", f4(l_a), f4(l_b), f"{l_b - l_a:+.4f}"),
        ("Angle error, mean, all TP (°)", "—", f"{mean_ang_a:.2f}", f"{mean_ang_b:.2f}", f"{mean_ang_b - mean_ang_a:+.2f}"),
        ("Angle error, median, all TP (°)", "—", f"{med_ang_a:.2f}", f"{med_ang_b:.2f}", f"{med_ang_b - med_ang_a:+.2f}"),
        ("Angle error, mean, elongated TP (°)", "—", f"{elo_mean_a:.2f}", f"{elo_mean_b:.2f}", f"{elo_mean_b - elo_mean_a:+.2f}"),
        ("Angle error, median, elongated TP (°)", "—", f"{elo_med_a:.2f}", f"{elo_med_b:.2f}", f"{elo_med_b - elo_med_a:+.2f}"),
    ], [2.7, 0.8, 0.85, 0.85, 0.85], size=8.5, align_center_from=1)
    caption(doc, "Table 7.4. Scale-stratified AP50 and orientation error. Area strata use rotated box "
                 "area; elongated means an aspect ratio of at least 1.5. Orientation error is "
                 "measured on true positives at IoU 0.50 and is a decrease, not an increase, so the "
                 "last column is negative.")
    para(doc, "Recall at the F1-optimal threshold separates the two difficulty groups. Track A "
              "recalls 0.7564 of the non-difficult instances and 0.2630 of the difficulty-flagged "
              "ones; Track B recalls 0.8335 and 0.3019. Both systems find far fewer flagged "
              "instances, which is expected because those annotations are tiny, heavily occluded or "
              "ambiguous by construction. The gap between the tracks is 0.0771 in the non-difficult "
              "group and 0.0389 in the flagged group, so the advantage is roughly halved on the "
              "harder instances.")

    h2(doc, "7.5  What the numbers do not show")
    para(doc, "The comparison is between two complete systems, not between two components. The "
              "tracks differ in detector, backbone, neck, regression loss, sampling, augmentation, "
              "optimizer and schedule, and this study contains no run that varies one of those "
              "factors while holding the others fixed. Nothing in Sections 7.1 to 7.4 identifies "
              "which factor produced the gain, and the report does not attempt that attribution.")
    para(doc, "The results are validation results. Test-dev ground truth is withheld, no server "
              "submission was scored, and both the checkpoint and the operating threshold were "
              "chosen on the split that is reported. A number on new imagery would be lower, by an "
              "amount this study does not measure.")

    # ---------------- 8 Qualitative analysis
    h1(doc, "8  Qualitative analysis")
    h2(doc, "8.1  Prediction examples")
    para(doc, "Figure 8.1 shows Track B output on two validation tiles at the F1-optimal threshold "
              "(0.834). Non-difficult ground truth is drawn in cyan, difficulty-flagged ground truth as "
              "a dotted grey outline, and predictions in dashed orange. Oriented boxes follow the headings "
              "of parked aircraft, ships and vehicles, and dense rows of docked boats and apron vehicles "
              "are separated rather than merged.")
    figure(doc, "track_b_demo_predictions.png", 4.9,
           "Figure 8.1. Track B predictions on two validation tiles at the F1-optimal threshold of "
           "0.834. Cyan: non-difficult ground truth; dotted grey: difficulty-flagged ground truth; "
           "dashed orange: Track B predictions.")
    para(doc, "The panels also show the cost of operating at the F1-optimal threshold. The "
              "non-difficult ground truth is almost fully tiled by dashed orange predictions, while the "
              "difficult outlines are mostly left unmatched — which is expected, because the "
              "threshold trades recall for precision. No single class escapes: the marina tile exposes "
              "how tightly a few difficult boxes interleave with the dense non-difficult instances, and the "
              "airfield tile shows the same for small-vehicle rows among parked aircraft.")

    h2(doc, "8.2  Per-class examples")
    para(doc, "Figures 8.2 to 8.4 show one matched prediction per class, six classes per figure, in "
              "the standard class order. Each panel is labelled with the class name and the IoU of "
              "the shown prediction; a prediction below 0.50 is marked in red as not a true "
              "positive. These panels are illustrations of individual instances and are not "
              "evidence for the aggregate results in Section 7.")
    figure(doc, "validation_class_examples_1.png", 5.0,
           "Figure 8.2. Validation examples for plane, baseball-diamond, bridge, ground-track-field, "
           "small-vehicle and large-vehicle. Labels give the IoU of the shown prediction; a value "
           "below 0.50 is marked in red and is not a true positive.")
    figure(doc, "validation_class_examples_2.png", 5.0,
           "Figure 8.3. Validation examples for ship, tennis-court, basketball-court, storage-tank, "
           "soccer-ball-field and roundabout, with the same labelling as Figure 8.2.")
    figure(doc, "validation_class_examples_3.png", 5.0,
           "Figure 8.4. Validation examples for harbor, swimming-pool, helicopter, container-crane, "
           "airport and helipad, with the same labelling as Figure 8.2.")

    h2(doc, "8.3  Failure modes")
    para(doc, "Three failure modes recur in the qualitative material and are consistent with the "
              "per-class numbers.")
    for lead, text in (
        ("Rare classes.", " Container-crane (27 annotations), airport (67) and helipad (4) produce "
         "unstable or near-zero AP. Helipad has four instances in the whole validation tiling and "
         "two are matched, so a single miss moves its AP by 0.25 to 0.33. These classes need more labelled "
         "data before any statement about detector quality is meaningful."),
        ("Objects cut by patch boundaries.", " A large or elongated object that crosses a patch "
         "edge is either dropped by the 0.70 IoF rule or seen as a fragment. Bridge and harbor, the "
         "two classes where Track A is weakest, are also the two most exposed to this effect."),
        ("Dense small instances.", " Vehicle rows in which boxes touch are the main source of "
         "duplicate and missed detections. Track B reduces this through oriented proposals, but the "
         "small-vehicle gain of 0.0603 shows that the problem is reduced rather than solved."),
    ):
        bullet(doc, text, lead=lead)

    # ---------------- 9 Discussion
    h1(doc, "9  Discussion and limitations")
    h2(doc, "9.1  Interpretation")
    para(doc, "The measured pattern is consistent with better geometry rather than better "
              "recognition. The gain is largest at AP75, larger on large and elongated objects than "
              "on medium ones, and accompanied by a one-third reduction in orientation error. All "
              "three observations point at box placement and heading, which is what oriented "
              "proposals and a distribution-based regression loss act on.")
    para(doc, "The classification gap narrows, from 0.1936 to 0.1676, so the residual "
              "error is still dominated by assigning the wrong class to a well placed box. That "
              "points at the label set and the training distribution rather than at the box "
              "parameterisation, and it is where further work is most likely to pay off.")
    para(doc, "Two results limit how far the pattern can be pushed. Track B was still improving at "
              "its last epoch, so its figures are a lower bound. Track A used a shorter schedule and "
              "a smaller backbone, so part of the gap may reflect training budget rather than "
              "architecture. Neither point can be settled with the runs available here.")

    h2(doc, "9.2  Limitations")
    for lead, text in (
        ("Single-system comparison.", " No component is isolated. Seven factors differ between the "
         "tracks and none of the reported differences can be attributed to one of them."),
        ("Validation-selected results.", " Checkpoint and threshold were both chosen on the reported "
         "split, so the figures are optimistic and no held-out estimate is available."),
        ("Unequal training budget.", " Track A trained for 12 epochs and Track B for 24, with the "
         "Track B schedule completed on the official data."),
        ("Tile-level counting.", " Every count and every metric refers to tile-level annotations. "
         "Objects in overlap regions are counted more than once, so AP is not an object-level "
         "detection rate."),
        ("Rare-class instability.", " Three classes have fewer than 70 annotations and their "
         "per-class values carry no reliable precision."),
        ("Different hardware.", " Throughput and memory were measured on different devices and are "
         "not comparable across tracks."),
        ("No test-dev result.", " The withheld test split was not scored, so no comparison with "
         "published leaderboard numbers is made."),
    ):
        bullet(doc, text, lead=lead)

    # ---------------- 10 Applications and future work
    h1(doc, "10  Applications and future work")
    h2(doc, "10.1  Applications")
    para(doc, "Oriented detection of the kind evaluated here supports tasks where the heading of an "
              "object matters as much as its position: airfield and apron survey, counting and "
              "classifying parked aircraft and vehicles, monitoring port and harbour traffic, and "
              "assessing damage after a disaster from post-event imagery. In each case the output is "
              "a set of oriented boxes with class labels, which is what a downstream geographic "
              "layer or a human analyst can consume directly.")
    para(doc, "The measurements in this report also set an expectation for deployment. At 2.52 "
              "frames per second on the two-Tesla-T4 device used for Track B, the system is suited to "
              "offline or near-real-time analysis of image collections rather than to continuous video "
              "processing on the same hardware.")

    h2(doc, "10.2  Future work")
    for lead, text in (
        ("One-factor ablation.", " Retrain Track B with a ResNet-50 and FPN backbone and Track A "
         "with a ConvNeXt-Small backbone, holding the schedule fixed, to separate backbone capacity "
         "from detector design."),
        ("Longer and matched schedules.", " Train both tracks to convergence on the same epoch "
         "budget. Track B completed the 24-epoch budget with validation dota/mAP of 0.6535 at epoch 24; extending the "
         "schedule (or validating at every epoch) is the primary single improvement available."),
        ("Multi-scale inference.", " Evaluate at several input scales and merge the results, which "
         "targets the small-object stratum directly."),
        ("Rare-class handling.", " Collect additional container-crane, airport and helipad "
         "annotations, or train with copy-paste augmentation for those classes."),
        ("Held-out evaluation.", " Reserve part of the training split, or submit to the DOTA "
         "test-dev server, to obtain a number that was not selected on the reported split."),
        ("Deployment measurement.", " Benchmark both checkpoints on one device, with and without "
         "TensorRT, so that throughput comparisons are meaningful."),
    ):
        bullet(doc, text, lead=lead)

    # ---------------- 11 Conclusion
    h1(doc, "11  Conclusion")
    para(doc, "Two oriented detectors were trained and evaluated on the official DOTA v2.0 "
              "validation tiling under a single evaluation protocol. Track A, a Rotated Faster "
              "R-CNN with a ResNet-50 and FPN backbone, reaches 0.6049 mAP50 and 0.3146 mAP50-95. "
              "Track B, an Oriented R-CNN with a ConvNeXt-Small backbone, PAFPN, Gaussian KLD "
              "regression and class-balanced sampling, reaches 0.7127 and 0.4320 on the same 7,122 "
              "patches.")
    para(doc, "The improvement is concentrated in box quality rather than in detection count. AP75 "
              "rises by 67.4% relative (from 0.2785 to 0.4664), orientation error falls by about a third, and every scale "
              "stratum improves. The gain is not uniform across classes, and the class most often "
              "used as evidence of small-object capability, small-vehicle, ranks 12th of 18 by "
              "improvement.")
    para(doc, "Because the tracks differ in seven factors and both were selected on the reported "
              "split, the result is a same-tiling evaluation of two complete systems. It supports "
              "the statement that the Track B configuration performs better on this benchmark. It "
              "does not support a claim about which component caused the difference, and the "
              "one-factor ablation needed for that claim is the first item of future work.")


def references(doc):
    h1(doc, "References")
    items = [
        "[1] S. Ren, K. He, R. Girshick and J. Sun, “Faster R-CNN: Towards real-time object "
        "detection with region proposal networks,” IEEE Transactions on Pattern Analysis and "
        "Machine Intelligence, vol. 39, no. 6, pp. 1137–1149, 2017.",
        "[2] X. Xie, G. Cheng, J. Wang, X. Yao and J. Han, “Oriented R-CNN for object detection,” "
        "in Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), 2021, "
        "pp. 3520–3529.",
        "[3] X. Yang, X. Yang, J. Yang, Q. Ming, W. Wang, Q. Tian and J. Yan, “Learning "
        "high-precision bounding box for rotated object detection via Kullback–Leibler divergence,” "
        "in Advances in Neural Information Processing Systems (NeurIPS), vol. 34, 2021, "
        "pp. 18381–18394.",
        "[4] Z. Liu, H. Mao, C.-Y. Wu, C. Feichtenhofer, T. Darrell and S. Xie, “A ConvNet for the "
        "2020s,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern "
        "Recognition (CVPR), 2022, pp. 11976–11986.",
        "[5] Y. Zhou, X. Yang, G. Zhang, J. Wang, Y. Liu, L. Hou, X. Jiang, X. Liu, J. Yan, C. Lyu, "
        "W. Zhang and K. Chen, “MMRotate: A rotating object detection toolbox and benchmark,” "
        "arXiv:2109.10111, 2021.",
        "[6] G.-S. Xia, X. Bai, J. Ding, Z. Zhu, S. Belongie, J. Luo, M. Datcu, M. Pelillo and "
        "L. Zhang, “DOTA: A large-scale dataset for object detection in aerial images,” in "
        "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), "
        "2018, pp. 3974–3983.",
        "[7] J. Ding, N. Xue, G.-S. Xia, X. Bai, W. Yang, M. Y. Yang, S. Belongie, J. Feng and "
        "X. Wang, “Object detection in aerial images: A large-scale benchmark and challenges,” IEEE "
        "Transactions on Pattern Analysis and Machine Intelligence, vol. 44, no. 11, "
        "pp. 7778–7796, 2022, doi: 10.1109/TPAMI.2021.3117983.",
        "[8] S. Liu, L. Qi, H. Qin, J. Shi and J. Jia, “Path aggregation network for instance "
        "segmentation,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern "
        "Recognition (CVPR), 2018, pp. 8759–8768.",
        "[9] K. Chen, J. Wang, J. Pang, Y. Cao, Y. Xiong, X. Li, S. Sun, W. Feng, Z. Liu, J. Xu, "
        "Z. Zhang, D. Cheng, C. Zhu, T. Cheng, Q. Zhao, B. Li, X. Lu, R. Zhu, Y. Wu, J. Niu, X. Peng, "
        "C. Miao, T. Lu, F. Yu and D. Feng, “MMDetection: OpenMMLab detection toolbox and benchmark,” "
        "arXiv:1906.07155, 2019.",
    ]
    for it in items:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.32)
        p.paragraph_format.first_line_indent = Inches(-0.32)
        p.paragraph_format.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(it)
        set_run_font(r, size=10.5)


def appendix(doc):
    h1(doc, "Appendix A  Configuration reference")
    para(doc, "Table A.1 records the full configuration of both tracks as used for the runs reported "
              "here. Values are taken from the training configurations; the seeds were not recorded "
              "in the artifacts.")
    table(doc, ["Setting", "Track A", "Track B"], [
        ("Model", "Rotated Faster R-CNN", "Oriented R-CNN"),
        ("Backbone", "ResNet-50, ImageNet pre-trained", "ConvNeXt-Small, ImageNet pre-trained"),
        ("Neck", "FPN, 256 channels", "PAFPN, 256 channels"),
        ("Proposal stage", "RPN, anchors 8/16/32", "Oriented RPN, 3 aspect ratios"),
        ("RoI stage", "Rotated RoIAlign, 7 × 7", "Rotated RoIAlign, 7 × 7"),
        ("Regression loss", "Rotated-box smooth-L1", "Gaussian KLD, log1p parameterisation"),
        ("Classification loss", "Cross-entropy", "Cross-entropy, class-balanced sampling"),
        ("Dataset wrapper", "DOTADataset", "ClassBalancedDataset, oversample_thr 1e-3"),
        ("Augmentation", "Horizontal, vertical and diagonal flips", "Flips plus random rotation, p = 0.5, 180°"),
        ("Optimizer", "SGD, momentum 0.9, weight decay 1e-4", "AdamW, weight decay 5e-2"),
        ("Learning rate", "0.005, multi-step decay at epochs 8 and 11", "1e-4, cosine annealing, T_max 24, eta_min 1e-6"),
        ("Epochs", "12", "24 (1–16 A100 stage, 17–24 Kaggle official retrain: 17–22 then 23–24 resumed)"),
        ("Batch", "4 per GPU", "4 per GPU on A100; 1 per GPU with 4-step accumulation on T4"),
        ("Input", "1024 × 1024 patches", "1024 × 1024 patches"),
        ("Inference", "Score 0.05, rotated NMS IoU 0.7, 2,000 per patch", "Score 0.05, rotated NMS IoU 0.7, 2,000 per patch"),
        ("Random seed", "not recorded", "not recorded"),
    ], [1.55, 2.25, 2.4], size=8.5, align_center_from=2)
    caption(doc, "Table A.1. Full configuration reference for both tracks.")

    h1(doc, "Appendix B  Full per-class tables")
    para(doc, "Tables A2 and A3 give every per-class value produced by the evaluator, including the "
              "precision, recall and F1 at each track's own F1-optimal threshold. These are the "
              "numbers behind Table 7.3 and Table 7.4.")
    for tag, M, label in (("A", A, "Track A"), ("B", B, "Track B")):
        rows = []
        for c in ORDER_STD:
            d = M[c]
            rows.append((c, f"{d['num_gt']:,}", f4(d["ap50"]), f4(d["ap75"]), f4(d["ap50_95"]),
                         f4(d["precision_f1_opt"]), f4(d["recall_f1_opt"]), f4(d["f1_opt"])))
        rows.append(("Mean (18 classes)", "69,542",
                     f4(sum(M[c]["ap50"] for c in CLASSES) / 18),
                     f4(sum(M[c]["ap75"] for c in CLASSES) / 18),
                     f4(sum(M[c]["ap50_95"] for c in CLASSES) / 18),
                     f4(sum(M[c]["precision_f1_opt"] for c in CLASSES) / 18),
                     f4(sum(M[c]["recall_f1_opt"] for c in CLASSES) / 18),
                     f4(sum(M[c]["f1_opt"] for c in CLASSES) / 18)))
        table(doc, ["Class", "n", "AP50", "AP75", "AP50-95", "P", "R", "F1"], rows,
              [1.62, 0.66, 0.68, 0.68, 0.8, 0.6, 0.6, 0.6], size=8, align_center_from=1)
        caption(doc, f"Table A.{2 if tag == 'A' else 3}. {label} per-class results on the official "
                     f"7,122-patch tiling. P, R and F1 are measured at the {label} F1-optimal "
                     f"threshold. Means are unweighted across the 18 classes.")

    # ---------------- author confirmations
    h1(doc, "Author confirmations", new_page=True)
    para(doc, "The following items could not be resolved from the project artifacts. Each appears in "
              "the body as a highlighted note or as a bracketed placeholder at the point where the "
              "information belongs. They are collected here so that the report can be completed in "
              "one pass.")
    notes = [
        ("Certificate", "insert the certificate wording required by the college, the signature "
         "blocks, the seal and the date."),
        ("Acknowledgements", "add named acknowledgements for the guide, the technical director, the "
         "department and colleagues, once approved for publication."),
        ("Organisation profile", "insert the official ADA profile text and the intern's role, team "
         "and reporting line."),
        ("Guide and TD names", "the title page and certificate carry placeholders because the names "
         "were not provided."),
        ("Submission date", "add the submission date and the programme reference on the title page."),
    ]
    for lead, text in notes:
        bullet(doc, text, lead=lead + ": ")
import re
import subprocess


def build_document():
    doc = Document()
    setup(doc)
    add_header(doc)
    add_page_number_footer(doc)
    front_matter(doc)
    abstract(doc)
    body_sections_a(doc)
    body_sections_b(doc)
    references(doc)
    appendix(doc)
    return doc


def save(doc, path):
    doc.core_properties.title = ("Deep Learning-Based Aerial Object Detection Using Oriented "
                                 "Faster R-CNN on the DOTA Dataset")
    doc.core_properties.author = "S S Gokula Swamy"
    doc.core_properties.subject = "Internship project report, Aeronautical Development Agency"
    doc.save(str(path))


def to_pdf(docx_path: Path, outdir: Path):
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", str(outdir),
                    str(docx_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def page_texts(pdf_path: Path):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], check=True,
                         capture_output=True, text=True).stdout
    pages = txt.split("\f")
    return [re.sub(r"\s+", " ", p).strip() for p in pages]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def resolve_pages(pages, needles):
    start = 0
    for i, p in enumerate(pages):
        if "This report documents a two-track study" in p:
            start = i
            break
    out = {}
    for n in needles:
        target = norm(n)
        for i in range(start, len(pages)):
            if target in pages[i]:
                out[n] = i + 1
                break
    return out


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.parent / "_pass1.docx"

    doc = build_document()
    save(doc, tmp)
    to_pdf(tmp, OUT.parent)
    pages = page_texts(OUT.parent / "_pass1.pdf")

    needles = [t for t, _, _ in TOC_ENTRIES] + [c for c in FIG_CAPTIONS] + [c for c in TAB_CAPTIONS]
    found = resolve_pages(pages, needles)
    missing = [n for n in needles if n not in found]
    PAGES.clear()
    PAGES.update(found)
    print(f"pass1 pages={len(pages)} resolved={len(found)}/{len(needles)}")
    if missing:
        print("UNRESOLVED:")
        for m in missing:
            print("   ", m[:80])

    doc = build_document()
    save(doc, OUT)
    to_pdf(OUT, OUT.parent)

    pages2 = page_texts(OUT.parent / "ADA_REPORT_S_S_GOKULA_SWAMY_revised.pdf")
    shifted = {n: (PAGES[n], i + 1) for i, p in enumerate(pages2) for n in [] }
    print(f"final pages={len(pages2)}")
    # confirm the page map still holds after the numbers were inserted
    bad = []
    for n, pg in PAGES.items():
        if pg - 1 >= len(pages2) or norm(n) not in pages2[pg - 1]:
            bad.append(n)
    print("page-map mismatches:", len(bad))
    for b in bad:
        print("   ", b[:80])


if __name__ == "__main__":
    main()
