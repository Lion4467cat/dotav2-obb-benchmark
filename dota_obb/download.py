"""Download Track B model weights from the GitHub release into the cache dir."""

from __future__ import annotations

import urllib.request

from .model import (
    CACHE_DIR,
    DEFAULT_CKPT,
    DEFAULT_CKPT_SHA256,
    DEFAULT_CKPT_URL,
    sha256_file,
)


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = CACHE_DIR / DEFAULT_CKPT.name
    if dst.is_file():
        print(f"Model weights already present at {dst}")
        return
    print(f"Downloading {DEFAULT_CKPT_URL} -> {dst}")
    urllib.request.urlretrieve(DEFAULT_CKPT_URL, dst)
    actual = sha256_file(dst)
    if actual != DEFAULT_CKPT_SHA256:
        dst.unlink()
        raise SystemExit(
            f"Checksum mismatch: expected {DEFAULT_CKPT_SHA256}, got {actual}"
        )
    print(f"Done: {dst} ({dst.stat().st_size / 1024 / 1024:.1f} MiB, sha256 verified)")


if __name__ == "__main__":
    main()
