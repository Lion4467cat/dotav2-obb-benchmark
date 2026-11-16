"""DOTA v2.0 Oriented Faster R-CNN benchmark suite (Track B)."""

from .model import load_model, predict, render_detections

__version__ = "1.2.0"

__all__ = ["__version__", "load_model", "predict", "render_detections"]
