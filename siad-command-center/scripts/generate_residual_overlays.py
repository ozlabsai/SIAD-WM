#!/usr/bin/env python
"""
Generate residual overlays from HDF5 data.

Loads residual scores from residuals_test.h5, applies discrete color mapping,
and saves as PNG overlays matching satellite imagery dimensions.

Color mapping:
  - Green (0.0-0.3): Normal
  - Yellow (0.3-0.6): Elevated
  - Orange (0.6-0.8): High
  - Red (0.8-1.0): Critical

Output: data/aoi_sf_seed/tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_wm_residual.png
"""

import json
from pathlib import Path

import h5py
import numpy as np
from PIL import Image


# Color palette for residual visualization (RGBA)
COLOR_MAP = {
    "normal": (46, 125, 50, 200),      # Green
    "elevated": (251, 192, 45, 200),   # Yellow
    "high": (255, 152, 0, 200),        # Orange
    "critical": (244, 67, 54, 230),    # Red
}

# Thresholds for color mapping
THRESHOLDS = [0.3, 0.6, 0.8]


def map_residual_to_color(residual: float) -> tuple[int, int, int, int]:
    """Map residual score to RGBA color."""
    if residual < THRESHOLDS[0]:
        return COLOR_MAP["normal"]
    elif residual < THRESHOLDS[1]:
        return COLOR_MAP["elevated"]
    elif residual < THRESHOLDS[2]:
        return COLOR_MAP["high"]
    else:
        return COLOR_MAP["critical"]


def tile_id_to_hdf5_key(tile_id: int) -> str:
    """
    Convert tile_id to HDF5 key format.

    HDF5 uses grid layout: tile_x000_y000, tile_x000_y001, etc.
    Assumes 5x4 grid (20 tiles total in HDF5), mapping tile_id sequentially.
    """
    # Map tile_id 0-19 to x,y coordinates
    # Grid: 5 columns x 4 rows
    x = tile_id % 5
    y = tile_id // 5
    return f"tile_x{x:03d}_y{y:03d}"


def generate_residual_overlay(
    residuals: np.ndarray,
    output_size: tuple[int, int] = (128, 128)
) -> Image.Image:
    """
    Generate color-mapped residual overlay.

    Args:
        residuals: 1D array of 256 residual scores
        output_size: Target image size (width, height)

    Returns:
        PIL Image with RGBA color mapping
    """
    # Reshape from 256 tokens to 16x16 grid
    grid = residuals.reshape(16, 16)

    # Create RGBA image
    img_array = np.zeros((16, 16, 4), dtype=np.uint8)

    # Apply color mapping
    for i in range(16):
        for j in range(16):
            img_array[i, j] = map_residual_to_color(grid[i, j])

    # Convert to PIL image
    img = Image.fromarray(img_array, mode="RGBA")

    # Upscale to match satellite imagery
    img = img.resize(output_size, Image.NEAREST)

    return img


def process_tile(
    hdf5_file: h5py.File,
    tile_id: int,
    output_base: Path,
    num_months: int = 6
):
    """Process all months for one tile."""
    hdf5_key = tile_id_to_hdf5_key(tile_id)

    if hdf5_key not in hdf5_file:
        print(f"Warning: {hdf5_key} not found in HDF5 file")
        return

    tile_group = hdf5_file[hdf5_key]
    residuals = tile_group["residuals"][:]  # Shape: (12, 256)

    tile_dir = output_base / f"tile_{tile_id:03d}"

    for month in range(1, num_months + 1):
        month_residuals = residuals[month - 1]  # 0-indexed

        # Create overlay directory
        overlay_dir = tile_dir / f"month_{month:02d}" / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)

        # Generate overlay image
        overlay_img = generate_residual_overlay(month_residuals)

        # Save overlay
        output_path = overlay_dir / f"2024-{month:02d}_wm_residual.png"
        overlay_img.save(output_path)

        print(f"Generated: {output_path}")


def generate_all_overlays(
    hdf5_path: Path,
    metadata_path: Path,
    output_base: Path
):
    """
    Generate residual overlays for all tiles in seed dataset.

    Args:
        hdf5_path: Path to residuals_test.h5
        metadata_path: Path to seed metadata.json
        output_base: Base directory for output (data/aoi_sf_seed/tiles)
    """
    # Load metadata
    with open(metadata_path) as f:
        metadata = json.load(f)

    tile_ids = [tile["tile_id"] for tile in metadata["tiles"]]
    num_months = metadata["num_months"]

    print(f"Processing {len(tile_ids)} tiles x {num_months} months...")

    # Open HDF5 file
    with h5py.File(hdf5_path, "r") as hdf5_file:
        for tile_id in tile_ids:
            print(f"\nProcessing tile {tile_id}...")
            process_tile(hdf5_file, tile_id, output_base, num_months)

    print("\n=== Overlay Generation Complete ===")
    print(f"Generated overlays for tiles: {tile_ids}")
    print(f"Months per tile: {num_months}")


def main():
    base_dir = Path(__file__).parent.parent
    hdf5_path = base_dir / "data" / "residuals_test.h5"
    metadata_path = base_dir / "data" / "aoi_sf_seed" / "metadata.json"
    output_base = base_dir / "data" / "aoi_sf_seed" / "tiles"

    generate_all_overlays(hdf5_path, metadata_path, output_base)


if __name__ == "__main__":
    main()
