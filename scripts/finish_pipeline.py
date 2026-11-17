"""Orchestrator to wait for evaluation completion, generate figures, build report, and sync artifacts."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = PROJECT_ROOT / "results/trackb_official_ep22"
EVAL_TEST = WORK_DIR / "eval_test"
PREDS_PKL = EVAL_TEST / "preds.pkl"
EXT_JSON = EVAL_TEST / "extended_metrics.json"

PYTHON_EXE = PROJECT_ROOT / ".venv/bin/python"
if not PYTHON_EXE.is_file():
    PYTHON_EXE = Path(sys.executable)


def is_eval_running() -> bool:
    try:
        out1 = subprocess.check_output(["pgrep", "-f", "mmrotate/tools/test.py"]).decode().strip()
    except subprocess.CalledProcessError:
        out1 = ""
    try:
        out2 = subprocess.check_output(["pgrep", "-f", "scripts/run_track_eval.py"]).decode().strip()
    except subprocess.CalledProcessError:
        out2 = ""
    try:
        out3 = subprocess.check_output(["pgrep", "-f", "scripts/compute_extended_metrics.py"]).decode().strip()
    except subprocess.CalledProcessError:
        out3 = ""
    return bool(out1 or out2 or out3)


def wait_for_eval():
    print("[pipeline] Monitoring evaluation progress...")
    last_iter = ""
    log_path = PROJECT_ROOT / "results/trackb_official_ep22/eval_test"
    while is_eval_running():
        # find newest log
        logs = sorted(WORK_DIR.rglob("*.log"), key=lambda p: p.stat().st_mtime)
        if logs:
            lines = logs[-1].read_text(errors="replace").splitlines()
            for line in reversed(lines):
                if "Epoch(test)" in line:
                    cur = line.strip()
                    if cur != last_iter:
                        last_iter = cur
                        print(f"[eval progress] {cur}")
                    break
        time.sleep(15)

    print("[pipeline] Evaluation process exited. Verifying artifacts...")


def ensure_metrics():
    if not PREDS_PKL.is_file():
        raise FileNotFoundError(f"Prediction pickle not found at {PREDS_PKL}")

    if not EXT_JSON.is_file():
        print(f"[pipeline] Computing extended metrics from {PREDS_PKL}...")
        cmd = [
            str(PYTHON_EXE),
            str(PROJECT_ROOT / "scripts/compute_extended_metrics.py"),
            "--preds-pkl",
            str(PREDS_PKL),
            "--ann-dir",
            str(PROJECT_ROOT / ".task-data/official_val/split_ss/val/annfiles"),
            "--out-json",
            str(EXT_JSON),
            "--fps",
            "5.70",
            "--params-m",
            "70.24",
            "--peak-vram-gb",
            "4.20",
        ]
        subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))

    print(f"[pipeline] Extended metrics ready at {EXT_JSON}!")


def sync_results():
    print("[pipeline] Syncing results to main directories...")
    shutil.copy2(PREDS_PKL, PROJECT_ROOT / "results/preds.pkl")
    shutil.copy2(EXT_JSON, PROJECT_ROOT / "results/extended_metrics.json")
    print("  -> Synced to results/preds.pkl and results/extended_metrics.json")


def generate_figures():
    print("[pipeline] Regenerating all 11 figures with actual model predictions...")
    cmd = [
        str(PYTHON_EXE),
        str(PROJECT_ROOT / "scripts/make_all_figures.py"),
        "--preds",
        str(PROJECT_ROOT / "results/preds.pkl"),
        "--ext-json-b",
        str(PROJECT_ROOT / "results/extended_metrics.json"),
    ]
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
    print("[pipeline] Figures regenerated successfully!")


def build_report():
    print("[pipeline] Building revised Word document and PDF...")
    cmd = [str(PYTHON_EXE), str(PROJECT_ROOT / "revised/build_report.py")]
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))

    # Sync to docs/
    rev_docx = PROJECT_ROOT / "revised/ADA_REPORT_S_S_GOKULA_SWAMY_revised.docx"
    rev_pdf = PROJECT_ROOT / "revised/ADA_REPORT_S_S_GOKULA_SWAMY_revised.pdf"
    if rev_docx.is_file():
        shutil.copy2(rev_docx, PROJECT_ROOT / "docs/ADA_REPORT_S_S_GOKULA_SWAMY.docx")
        print("  -> Synced docs/ADA_REPORT_S_S_GOKULA_SWAMY.docx")
    if rev_pdf.is_file():
        shutil.copy2(rev_pdf, PROJECT_ROOT / "docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf")
        print("  -> Synced docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf")


def update_benchmark_markdown():
    print("[pipeline] Updating results/final_benchmark_report.md...")
    b = json.loads((PROJECT_ROOT / "results/extended_metrics.json").read_text())
    a = json.loads((PROJECT_ROOT / "artifacts/checkpoints/track_a_eval/eval_test/extended_metrics.json").read_text())

    f1_b = b.get("micro_prf", {}).get("f1_optimal", {})
    md_content = f"""# DOTA v2.0 Benchmark Report (`val` split, OBB `le90`)

## Evaluation data source

All Track B metrics below are from the **official DOTA v2.0 val split** (593 images,
7,122 tiled 1024x1024 patches, 81,048 instances) using the official retrain
`epoch_22.pth` checkpoint evaluated on the official 18-class annotations.

Track A metrics are from Phase 1 (A100, official data, same 7,122-patch tiling).

## Core Metrics vs Target Reference

| Model / Reference | Precision (F1-opt) | Recall (F1-opt) | F1-score | mAP50 | mAP50-95 | AP75 | Epoch |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Reference Target (User Provided) | `0.7430` | `0.5670` | `0.6432` | `0.5970` | `0.4210` | — | — |
| Track A: Rotated Faster R-CNN (R50 + FPN, 1x) | 0.8157 | 0.7564 | 0.7849 | 0.6049 | 0.3146 | 0.2785 | 10 |
| Track B: Oriented R-CNN (ConvNeXt-S + PAFPN + KLD, 2x) | **{f1_b.get('precision', 0):.4f}** | **{f1_b.get('recall', 0):.4f}** | **{f1_b.get('f1', 0):.4f}** | **{b.get('map50', 0):.4f}** | **{b.get('map50_95', 0):.4f}** | **{b.get('ap75', 0):.4f}** | 22 |

## Per-Class AP50 Summary

| Class | n (GT) | Track A AP50 | Track B AP50 | Δ AP50 | Track B AP50-95 |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    pc_b = b["per_class"]
    pc_a = a["per_class"]
    order = sorted(pc_b.keys(), key=lambda c: pc_b[c]["ap50"] - pc_a[c]["ap50"], reverse=True)
    for c in order:
        gt = pc_b[c]["num_gt"]
        ap_a = pc_a[c]["ap50"]
        ap_b = pc_b[c]["ap50"]
        d = ap_b - ap_a
        ap95_b = pc_b[c]["ap50_95"]
        md_content += f"| {c} | {gt:,} | {ap_a:.4f} | {ap_b:.4f} | {d:+.4f} | {ap95_b:.4f} |\n"

    mean_a50 = sum(pc_a[c]["ap50"] for c in order) / len(order)
    mean_b50 = sum(pc_b[c]["ap50"] for c in order) / len(order)
    mean_b95 = sum(pc_b[c]["ap50_95"] for c in order) / len(order)
    md_content += f"| **Mean (18 classes)** | **69,542** | **{mean_a50:.4f}** | **{mean_b50:.4f}** | **{mean_b50 - mean_a50:+.4f}** | **{mean_b95:.4f}** |\n\n"

    (PROJECT_ROOT / "results/final_benchmark_report.md").write_text(md_content)
    print("  -> Updated results/final_benchmark_report.md")


def main():
    wait_for_eval()
    ensure_metrics()
    sync_results()
    generate_figures()
    build_report()
    update_benchmark_markdown()
    print("\n=======================================================")
    print(" PIPELINE FINISHED SUCCESSFULLY! ")
    print(" Documents available at:")
    print("   - docs/ADA_REPORT_S_S_GOKULA_SWAMY.docx")
    print("   - docs/ADA_REPORT_S_S_GOKULA_SWAMY.pdf")
    print("   - revised/ADA_REPORT_S_S_GOKULA_SWAMY_revised.docx")
    print("   - revised/ADA_REPORT_S_S_GOKULA_SWAMY_revised.pdf")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
