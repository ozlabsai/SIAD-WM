#!/usr/bin/env python3
"""Diagnose RGB composite artifacts

Compares different RGB composite strategies to identify artifacts:
1. Per-image percentile normalization (current)
2. Global percentile normalization (across all images)
3. Fixed normalization using dataset statistics
4. Raw band visualization without normalization

This will help us understand if artifacts come from the RGB conversion.
"""

import argparse
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def create_rgb_composite_per_image(bands: np.ndarray) -> np.ndarray:
    """Current method: per-image percentile normalization"""
    rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]

    for i in range(3):
        channel = rgb[:, :, i]
        vmin, vmax = np.percentile(channel, [2, 98])
        rgb[:, :, i] = np.clip((channel - vmin) / (vmax - vmin + 1e-8), 0, 1)

    return rgb


def create_rgb_composite_global(bands_list: list) -> list:
    """Global percentile normalization across all images"""
    # Stack all images to compute global percentiles
    all_bands = np.stack(bands_list, axis=0)  # [N, C, H, W]

    rgbs = []
    for bands in bands_list:
        rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]

        for i, channel_idx in enumerate([2, 1, 0]):
            # Use global percentiles across all images
            vmin, vmax = np.percentile(all_bands[:, channel_idx], [2, 98])
            rgb[:, :, i] = np.clip((rgb[:, :, i] - vmin) / (vmax - vmin + 1e-8), 0, 1)

        rgbs.append(rgb)

    return rgbs


def create_rgb_composite_fixed(bands: np.ndarray, stats: dict) -> np.ndarray:
    """Fixed normalization using dataset statistics"""
    rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]

    for i, channel_idx in enumerate([2, 1, 0]):
        mean = stats['mean'][channel_idx]
        std = stats['std'][channel_idx]

        # Normalize to ±3σ range
        vmin, vmax = mean - 3*std, mean + 3*std
        rgb[:, :, i] = np.clip((rgb[:, :, i] - vmin) / (vmax - vmin + 1e-8), 0, 1)

    return rgb


def create_rgb_composite_raw(bands: np.ndarray) -> np.ndarray:
    """Raw band values without normalization (just clip to [0, 1])"""
    rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]
    return np.clip(rgb, 0, 1)


def diagnose_tile(gallery_path: str, tile_id: str, output_path: str):
    """Compare RGB composite methods for a single tile"""
    gallery_path = Path(gallery_path)
    tile_file = gallery_path / f"{tile_id}.npz"

    if not tile_file.exists():
        print(f"ERROR: Tile {tile_id} not found at {tile_file}")
        return

    # Load data
    data = np.load(tile_file)

    # Get raw 8-band data (we need to reconstruct from RGB... wait, we only saved RGB!)
    # This is a problem - we can't diagnose the issue without raw band data

    print("ERROR: Gallery only contains RGB composites, not raw 8-band data!")
    print("We need to regenerate gallery with raw bands saved.")
    print()
    print("Solution: Modify generate_gallery.py to save:")
    print("  - context_bands (8-channel raw)")
    print("  - pred_bands (6 x 8-channel raw)")
    print("  - target_bands (6 x 8-channel raw)")
    print()
    print("Then we can test different RGB composite strategies.")


def main():
    parser = argparse.ArgumentParser(description="Diagnose RGB composite artifacts")
    parser.add_argument("--gallery", default="siad-command-center/data/gallery")
    parser.add_argument("--tile-id", default=None, help="Specific tile to diagnose")
    parser.add_argument("--output", default="rgb_diagnostics.png")

    args = parser.parse_args()

    # Find a tile to diagnose
    gallery_path = Path(args.gallery)

    if args.tile_id:
        tile_id = args.tile_id
    else:
        # Find first available tile
        tiles = list(gallery_path.glob("tile_*.npz"))
        if not tiles:
            print(f"ERROR: No tiles found in {gallery_path}")
            return
        tile_id = tiles[0].stem

    diagnose_tile(args.gallery, tile_id, args.output)


if __name__ == "__main__":
    main()
