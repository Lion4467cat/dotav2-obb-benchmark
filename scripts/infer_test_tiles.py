"""Tile-level inference for DOTA-v2.0 test-dev set with the Track B checkpoint.

Writes a pickle with per-tile le90 detections (tile id, scores, labels, boxes)
to be merged back into full-image coordinates by merge_test_preds.py.
"""

from __future__ import annotations

import argparse
import pickle
import time
from pathlib import Path

import cv2
import numpy as np

TILE_GLOB = "*.png"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/benchmark_oriented_faster_rcnn_convnext_s_pafpn_kld_2x_dotav2.py")
    parser.add_argument("--checkpoint", default="artifacts/checkpoints/best_dota_mAP_epoch_24.pth")
    parser.add_argument("--tiles-dir", default=".task-data/split_ss_dotav2/test/images")
    parser.add_argument("--out", default=".task-data/test_tile_preds.pkl")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--score-thr", type=float, default=0.05)
    args = parser.parse_args()

    import torch
    from mmdet.apis import inference_detector, init_detector

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = init_detector(args.config, args.checkpoint, device=device)
    tiles = sorted(Path(args.tiles_dir).glob(TILE_GLOB))
    print(f"[infer] {len(tiles)} tiles")

    results = []
    t0 = time.time()
    for start in range(0, len(tiles), args.batch_size):
        batch_paths = tiles[start : start + args.batch_size]
        batch_imgs = []
        for p in batch_paths:
            img = cv2.imread(str(p))
            if img is None:
                raise RuntimeError(f"failed to read {p}")
            batch_imgs.append(img)
        samples = inference_detector(model, batch_imgs)
        if not isinstance(samples, (list, tuple)):
            samples = [samples]
        for path, sample in zip(batch_paths, samples):
            inst = sample.pred_instances
            scores = inst.scores.cpu().numpy().astype(np.float32)
            keep = scores >= args.score_thr
            results.append(
                {
                    "tile": path.stem,
                    "scores": scores[keep],
                    "labels": inst.labels.cpu().numpy()[keep].astype(np.int64),
                    "bboxes": inst.bboxes.cpu().numpy().astype(np.float32)[keep],
                }
            )
        done = start + len(batch_paths)
        if done % 400 < args.batch_size:
            elapsed = time.time() - t0
            print(f"[infer] {done}/{len(tiles)} tiles  {done/elapsed:.1f} img/s")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        pickle.dump(results, f, protocol=4)
    n_dets = sum(len(r["scores"]) for r in results)
    print(f"[infer] wrote {out} with {n_dets} detections in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
