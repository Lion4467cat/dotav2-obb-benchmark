#!/usr/bin/env python3
"""Lightweight Gradio UI for the DOTA v2.0 Oriented Faster R-CNN (Track B).

Run locally:
    uv pip install -e ".[ui]"
    python scripts/gradio_app.py

or with the full local inference environment (see README -> "Local inference UI").
"""

import argparse
import sys
from pathlib import Path

import gradio as gr
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dota_obb import load_model, predict


def _run(image: np.ndarray | None, score_thr: float):
    if image is None:
        return None, "Upload an image first."
    model = load_model()
    result = predict(image, score_thr=float(score_thr), model=model)
    detections = result["detections"]
    if not detections:
        summary = "No detections above the confidence threshold."
    else:
        lines = [f"{i + 1:3d}. {d['class']:<16} {d['score']:.3f}" for i, d in enumerate(detections)]
        summary = f"{len(detections)} detection(s):\n" + "\n".join(lines)
    return result["annotated"], summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true", help="create a public gradio.live link")
    args = parser.parse_args()

    print("Loading Track B model (first request builds it)...")
    model = load_model()
    print("Model ready.")

    demo = gr.Interface(
        fn=_run,
        inputs=[
            gr.Image(type="numpy", label="Aerial image"),
            gr.Slider(0.1, 0.9, value=0.3, step=0.05, label="Confidence threshold"),
        ],
        outputs=[
            gr.Image(type="numpy", label="Detections (le90 oriented boxes)"),
            gr.Textbox(label="Detected objects", lines=16),
        ],
        title="DOTA v2.0 Oriented Faster R-CNN — Track B",
        description=(
            "ConvNeXt-S + PAFPN Oriented Faster R-CNN (le90) trained on the full 18-class DOTA v2.0. "
            "Checkpoint: best_dota_mAP_epoch_24.pth (mAP50 0.7064, F1 0.7264)."
        ),
        flagging_mode="never",
    )
    demo.launch(server_name="0.0.0.0", server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
