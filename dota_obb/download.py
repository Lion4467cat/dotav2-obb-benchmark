"""Download Track B model weights from the GitHub release into the cache dir."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from .model import DEFAULT_CKPT_URL, CACHE_DIR, DEFAULT_CKPT


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / DEFAULT_CKPT.name
    if dst.is_file():
        print(f"Model weights already present at {dst}")
        return
    print(f"Downloading {DEFAULT_CKPT_URL} -> {dst}")
    urllib.request.urlretrieve(DEFAULT_CKPT_URL, dst)
    print(f"Done: {dst} ({dst.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
