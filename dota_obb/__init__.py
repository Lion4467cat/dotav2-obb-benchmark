"""DOTA v2.0 Oriented Faster R-CNN benchmark suite (Track B)."""

from .model import load_model, predict, render_detections

__version__ = "1.0.0"

__all__ = ["load_model", "predict", "render_detections", "__version__"]
