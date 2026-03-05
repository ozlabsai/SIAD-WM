#!/usr/bin/env python3
"""
Convert Earth Engine .npz gallery exports to PNG imagery for the command center.

This script:
1. Reads .npz files from data/gallery/ containing world model predictions
2. Extracts actual satellite imagery (target_rgbs) and model predictions (pred_rgbs)
3. Computes residual anomaly maps (target - predicted)
4. Saves PNGs organized by tile and month for frontend consumption
"""

import numpy as np
from pathlib import Path
from PIL import Image
import json

# Configuration
GALLERY_DIR = Path("data/gallery")
OUTPUT_DIR = Path("data/satellite_imagery/tiles")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Month mapping - assuming 6 timesteps correspond to months 01-06
# You may need to adjust this based on your actual temporal range
MONTH_MAPPING = {
    0: "month_01",
    1: "month_02",
    2: "month_03",
    3: "month_04",
    4: "month_05",
    5: "month_06",
}


def normalize_to_uint8(arr: np.ndarray) -> np.ndarray:
    """Convert float32 [0, 1] array to uint8 [0, 255]."""
    return (np.clip(arr, 0, 1) * 255).astype(np.uint8)


def compute_residual_heatmap(target: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """
    Compute residual heatmap showing prediction errors.

    Returns RGB image where:
    - Blue: Low error (good prediction)
    - Yellow/Orange: Medium error
    - Red: High error (anomaly)
    """
    # Calculate per-pixel MSE across RGB channels
    mse = np.mean((target - pred) ** 2, axis=-1)

    # Normalize MSE to [0, 1] for visualization
    mse_min, mse_max = mse.min(), mse.max()
    if mse_max > mse_min:
        mse_norm = (mse - mse_min) / (mse_max - mse_min)
    else:
        mse_norm = np.zeros_like(mse)

    # Create heatmap using colormap:
    # Low error (0.0) -> Blue (0, 100, 255)
    # Medium error (0.5) -> Yellow (255, 255, 0)
    # High error (1.0) -> Red (255, 0, 0)
    heatmap = np.zeros((*mse.shape, 3), dtype=np.float32)

    # Red channel: increases with error
    heatmap[..., 0] = mse_norm

    # Green channel: peaks at medium error
    heatmap[..., 1] = 1 - 2 * np.abs(mse_norm - 0.5)

    # Blue channel: decreases with error
    heatmap[..., 2] = 1 - mse_norm

    return normalize_to_uint8(heatmap)


def process_tile(npz_path: Path) -> dict:
    """Process a single .npz file and generate all imagery."""
    print(f"\nProcessing {npz_path.name}...")

    # Load data
    data = np.load(npz_path)
    tile_id = npz_path.stem  # e.g., "tile_x000_y001"

    # Create tile directory
    tile_dir = OUTPUT_DIR / tile_id
    tile_dir.mkdir(parents=True, exist_ok=True)

    # Extract arrays
    context_rgb = data["context_rgb"]  # (256, 256, 3)
    target_rgbs = data["target_rgbs"]  # (6, 256, 256, 3)
    pred_rgbs = data["pred_rgbs"]      # (6, 256, 256, 3)
    mse_per_step = data["mse_per_step"]  # (6,)

    stats = {
        "tile_id": tile_id,
        "timesteps": len(target_rgbs),
        "mse_scores": mse_per_step.tolist(),
        "avg_mse": float(mse_per_step.mean()),
    }

    # Process each timestep
    for step_idx in range(len(target_rgbs)):
        month_folder = MONTH_MAPPING[step_idx]
        month_dir = tile_dir / month_folder
        month_dir.mkdir(parents=True, exist_ok=True)

        # Extract imagery for this timestep
        actual = target_rgbs[step_idx]    # Actual satellite observation
        predicted = pred_rgbs[step_idx]   # Model's prediction

        # Save actual satellite imagery
        actual_img = Image.fromarray(normalize_to_uint8(actual))
        actual_img.save(month_dir / "actual.png")

        # Save predicted imagery
        predicted_img = Image.fromarray(normalize_to_uint8(predicted))
        predicted_img.save(month_dir / "predicted.png")

        # Compute and save residual heatmap
        residual = compute_residual_heatmap(actual, predicted)
        residual_img = Image.fromarray(residual)
        residual_img.save(month_dir / "residual.png")

        print(f"  {month_folder}: MSE = {mse_per_step[step_idx]:.4f}")

    return stats


def main():
    """Process all .npz files in the gallery directory."""
    print("=" * 60)
    print("Converting Earth Engine Gallery to PNG Imagery")
    print("=" * 60)

    # Find all .npz files
    npz_files = sorted(GALLERY_DIR.glob("tile_*.npz"))

    if not npz_files:
        print(f"\nNo .npz files found in {GALLERY_DIR}")
        return

    print(f"\nFound {len(npz_files)} tiles to process")

    # Process each tile
    all_stats = []
    for npz_path in npz_files:
        try:
            stats = process_tile(npz_path)
            all_stats.append(stats)
        except Exception as e:
            print(f"Error processing {npz_path.name}: {e}")
            continue

    # Save processing statistics
    stats_path = OUTPUT_DIR / "conversion_stats.json"
    with open(stats_path, "w") as f:
        json.dump({
            "tiles_processed": len(all_stats),
            "tiles": all_stats,
        }, f, indent=2)

    print("\n" + "=" * 60)
    print(f"Conversion complete!")
    print(f"  Processed: {len(all_stats)} tiles")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Stats saved: {stats_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
