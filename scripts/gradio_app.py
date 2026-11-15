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
REPO_ROOT = Path(__file__).resolve().parent.parent

from dota_obb import load_model, predict


def _run(image: np.ndarray | None, score_thr: float):
    if image is None:
        return None, [], "Choose an aerial image or one of the examples below."
    model = load_model()
    result = predict(image, score_thr=float(score_thr), model=model)
    detections = result["detections"]
    if not detections:
        summary = f"No detections above {score_thr:.2f} confidence."
    else:
        class_count = len({d["class"] for d in detections})
        summary = (
            f"{len(detections)} detections across {class_count} classes · "
            f"confidence ≥ {score_thr:.2f}"
        )
    rows = [[d["class"], f"{d['score']:.3f}", f"{d['angle_rad']:.3f} rad"] for d in detections]
    return result["annotated"], rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true", help="create a public gradio.live link")
    args = parser.parse_args()

    print("Loading Track B model (first request builds it)...")
    model = load_model()
    print("Model ready.")

    css = """
    .gradio-container {max-width: 1480px !important; margin: auto !important;}
    .hero {padding: 20px 24px; border: 1px solid #dbe3ec; border-radius: 16px;
           background: linear-gradient(115deg,#f8fbff 0%,#f3f7fb 60%,#fff7ed 100%);}
    .hero h1 {margin: 0 0 8px; letter-spacing: -.025em;}
    .hero p {margin: 0; color: #475569; line-height: 1.55;}
    .panel {border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px;}
    .status {font-weight: 600; color: #334155;}
    footer {display:none !important;}
    """
    with gr.Blocks(title="DOTA v2.0 · Track B detector", css=css, theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """<div class='hero'>
            <h1>DOTA v2.0 · Oriented object detection</h1>
            <p>Track B · Oriented R-CNN with ConvNeXt-Small and PAFPN · Epoch 24 checkpoint<br>
            Upload an aerial image to inspect class, confidence, and rotated-box predictions.</p>
            </div>"""
        )
        with gr.Row(equal_height=False):
            with gr.Column(scale=1, elem_classes="panel"):
                image = gr.Image(type="numpy", label="Input aerial image", height=390)
                threshold = gr.Slider(
                    0.1, 0.9, value=0.52, step=0.01,
                    label="Minimum confidence", info="Default is rounded to 0.52 from the validation F1-optimal threshold (0.5182).",
                )
                run = gr.Button("Run detection", variant="primary")
            with gr.Column(scale=1, elem_classes="panel"):
                output = gr.Image(type="numpy", label="Track B oriented predictions", height=390)
                status = gr.Markdown("Select an image and run detection.", elem_classes="status")
        detections = gr.Dataframe(
            headers=["Class", "Confidence", "Angle"],
            datatype=["str", "str", "str"],
            label="Detected objects", interactive=False, wrap=True,
        )
        examples = [
            str(REPO_ROOT / "docs" / "demo" / "validation_plane_vehicles.png"),
            str(REPO_ROOT / "docs" / "demo" / "validation_court_vehicles.png"),
            str(REPO_ROOT / "docs" / "demo" / "validation_helicopter_vehicles.png"),
        ]
        gr.Examples(examples=examples, inputs=image, label="Try an aerial example")
        gr.Markdown(
            "Predictions are qualitative. Benchmark scores in the report were measured on the separate DOTA validation split."
        )
        run.click(_run, inputs=[image, threshold], outputs=[output, detections, status])
        image.change(_run, inputs=[image, threshold], outputs=[output, detections, status], queue=True)
    demo.launch(server_name="0.0.0.0", server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
