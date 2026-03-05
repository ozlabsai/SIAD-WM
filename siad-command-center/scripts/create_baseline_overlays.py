#!/usr/bin/env python
"""
Generate baseline overlays from HDF5 data.

Baseline scores are tile-level (scalar per month), so we create uniform color
overlays representing the overall baseline performance for that tile/month.

Output:
  - Persistence: tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_persist_baseline.png
  - Seasonal: tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_seasonal_baseline.png
"""

import json
from pathlib import Path

import h5py
import numpy as np
from PIL import Image


# Color palette (same as residual overlays)
COLOR_MAP = {
    "normal": (46, 125, 50, 200),      # Green
    "elevated": (251, 192, 45, 200),   # Yellow
    "high": (255, 152, 0, 200),        # Orange
    "critical": (244, 67, 54, 230),    # Red
}

THRESHOLDS = [0.3, 0.6, 0.8]


def map_score_to_color(score: float) -> tuple[int, int, int, int]:
    """Map baseline score to RGBA color."""
    if score < THRESHOLDS[0]:
        return COLOR_MAP["normal"]
    elif score < THRESHOLDS[1]:
        return COLOR_MAP["elevated"]
    elif score < THRESHOLDS[2]:
        return COLOR_MAP["high"]
    else:
        return COLOR_MAP["critical"]


def tile_id_to_hdf5_key(tile_id: int) -> str:
    """Convert tile_id to HDF5 key format."""
    x = tile_id % 5
    y = tile_id // 5
    return f"tile_x{x:03d}_y{y:03d}"


def generate_uniform_overlay(
    score: float,
    output_size: tuple[int, int] = (128, 128)
) -> Image.Image:
    """
    Generate uniform color overlay for tile-level baseline score.

    Args:
        score: Scalar baseline score for the tile/month
        output_size: Target image size (width, height)

    Returns:
        PIL Image with uniform RGBA color
    """
    # Get color for score
    color = map_score_to_color(score)

    # Create uniform RGBA image
    img_array = np.full((*output_size, 4), color, dtype=np.uint8)

    # Convert to PIL image
    img = Image.fromarray(img_array, mode="RGBA")

    return img


def process_tile_baselines(
    hdf5_file: h5py.File,
    tile_id: int,
    output_base: Path,
    num_months: int = 6
):
    """Process baseline overlays for one tile."""
    hdf5_key = tile_id_to_hdf5_key(tile_id)

    if hdf5_key not in hdf5_file:
        print(f"Warning: {hdf5_key} not found in HDF5 file")
        return

    tile_group = hdf5_file[hdf5_key]
    baselines = tile_group["baselines"]

    # Load baseline data (scalar scores per month)
    persistence = baselines["persistence"][:]  # Shape: (12,)
    seasonal = baselines["seasonal"][:]        # Shape: (12,)

    tile_dir = output_base / f"tile_{tile_id:03d}"

    for month in range(1, num_months + 1):
        # Get month scores (0-indexed)
        persist_score = float(persistence[month - 1])
        seasonal_score = float(seasonal[month - 1])

        # Create overlay directory
        overlay_dir = tile_dir / f"month_{month:02d}" / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)

        # Generate persistence overlay (uniform color)
        persist_overlay = generate_uniform_overlay(persist_score)
        persist_path = overlay_dir / f"2024-{month:02d}_persist_baseline.png"
        persist_overlay.save(persist_path)

        # Generate seasonal overlay (uniform color)
        seasonal_overlay = generate_uniform_overlay(seasonal_score)
        seasonal_path = overlay_dir / f"2024-{month:02d}_seasonal_baseline.png"
        seasonal_overlay.save(seasonal_path)

        print(f"Generated: {persist_path} (score={persist_score:.3f})")
        print(f"Generated: {seasonal_path} (score={seasonal_score:.3f})")


def generate_all_baseline_overlays(
    hdf5_path: Path,
    metadata_path: Path,
    output_base: Path
):
    """Generate baseline overlays for all tiles in seed dataset."""
    # Load metadata
    with open(metadata_path) as f:
        metadata = json.load(f)

    tile_ids = [tile["tile_id"] for tile in metadata["tiles"]]
    num_months = metadata["num_months"]

    print(f"Processing {len(tile_ids)} tiles x {num_months} months...")

    # Open HDF5 file
    with h5py.File(hdf5_path, "r") as hdf5_file:
        for tile_id in tile_ids:
            print(f"\nProcessing tile {tile_id} baselines...")
            process_tile_baselines(hdf5_file, tile_id, output_base, num_months)

    print("\n=== Baseline Overlay Generation Complete ===")
    print(f"Generated persistence and seasonal overlays for tiles: {tile_ids}")


def main():
    base_dir = Path(__file__).parent.parent
    hdf5_path = base_dir / "data" / "residuals_test.h5"
    metadata_path = base_dir / "data" / "aoi_sf_seed" / "metadata.json"
    output_base = base_dir / "data" / "aoi_sf_seed" / "tiles"

    generate_all_baseline_overlays(hdf5_path, metadata_path, output_base)


if __name__ == "__main__":
    main()
