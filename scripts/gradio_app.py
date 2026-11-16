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
    load_model()
    print("Model ready.")

    css = """
    .gradio-container {max-width: 1320px !important; margin: auto !important;}
    .hero {padding: 24px 28px; border: 1px solid #e7d9c8; border-radius: 16px;
           background: linear-gradient(115deg,#fffaf2 0%,#f8f1e7 66%,#f5e7d8 100%);}
    .hero h1 {margin: 0 0 8px; letter-spacing: -.025em; color: #29231e !important;}
    .hero p {margin: 0; color: #51463d !important; line-height: 1.55;}
    .panel {border: 1px solid #ddd4c9; border-radius: 14px; padding: 14px; background: #faf8f4;}
    .status, .status p, .status span, .status strong {font-weight: 600; color: #37302a !important;
             opacity: 1 !important;}
    .status {background: #f3eee6; border: 1px solid #ddd4c9;
             border-radius: 10px; padding: 10px 12px;}
    .step-note {color: #51463d; margin: 10px 2px 14px;}
    .settings-accordion {margin: 16px 0; border: 1px solid #a4512b !important;
                         border-radius: 10px !important; background: #292521 !important;}
    .settings-accordion button, .settings-accordion [data-testid="accordion-header"],
    .settings-accordion span {color: #f2e6d7 !important;}
    .gradio-container button.primary {background: #a4512b !important; border-color: #a4512b !important;}
    .gradio-container button.primary:hover {background: #873f22 !important; border-color: #873f22 !important;}
    .gradio-container table, .gradio-container th, .gradio-container td {border-color: #d9d0c6 !important;}
    .gradio-container thead, .gradio-container th,
    .gradio-container [role="columnheader"] {background: #eee6dc !important; color: #37302a !important;}
    .gradio-container tbody tr:nth-child(even) {background: #f6f2ec !important;}
    .examples {margin-top: 8px;}
    """
    with gr.Blocks(title="DOTA v2.0 · Track B detector") as demo:
        gr.Markdown(
            """<div class='hero'>
            <h1>DOTA v2.0 · Oriented object detection</h1>
            <p>Track B · Oriented R-CNN · ConvNeXt-Small + PAFPN · Epoch 24 checkpoint<br>
            Inspect oriented detections and confidence scores on an aerial image.</p>
            </div>"""
        )
        gr.Markdown(
            "**How to use:** choose a validation example or upload an image, adjust the confidence threshold in Detection settings, then run inference.",
            elem_classes="step-note",
        )
        with gr.Row(equal_height=False):
            with gr.Column(scale=1, elem_classes="panel"):
                image = gr.Image(type="numpy", label="Input aerial image", height=390)
            with gr.Column(scale=1, elem_classes="panel"):
                output = gr.Image(type="numpy", label="Track B oriented predictions", height=390)
                status = gr.Markdown("Select an image and run detection.", elem_classes="status")
        with gr.Accordion("Detection settings", open=True, elem_classes="settings-accordion"):
            threshold = gr.Slider(
                0.1, 0.9, value=0.52, step=0.01,
                label="Minimum confidence", info="0.52 is a UI-friendly default; the validation F1-optimal threshold is 0.8279.",
            )
        run = gr.Button("Run Track B inference", variant="primary")
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
        gr.Examples(
            examples=examples, inputs=image, label="Validation examples",
            examples_per_page=3, cache_examples=False,
        )
        gr.Markdown(
            "Predictions are qualitative. Benchmark scores in the report were measured on the separate DOTA validation split."
        )
        run.click(_run, inputs=[image, threshold], outputs=[output, detections, status])
    demo.launch(
        server_name="127.0.0.1", server_port=args.port, share=args.share,
        css=css, theme=gr.themes.Soft(primary_hue="orange", secondary_hue="stone", neutral_hue="stone"),
    )


if __name__ == "__main__":
    main()
