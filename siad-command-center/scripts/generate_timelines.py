#!/usr/bin/env python
"""
Generate timeline JSON files from HDF5 data.

Creates timeseries.json for each tile containing:
  - Monthly scores (world model, persistence, seasonal)
  - Onset detection (first month above threshold)
  - Persistence duration (consecutive months above threshold)

Output: tiles/{tile_id}/timeseries.json
"""

import json
from pathlib import Path

import h5py
import numpy as np


def tile_id_to_hdf5_key(tile_id: int) -> str:
    """Convert tile_id to HDF5 key format."""
    x = tile_id % 5
    y = tile_id // 5
    return f"tile_x{x:03d}_y{y:03d}"


def detect_onset(scores: np.ndarray, threshold_percentile: float = 90.0) -> int:
    """
    Detect onset month (first month above threshold).

    Args:
        scores: Array of monthly scores
        threshold_percentile: Percentile threshold for detection

    Returns:
        Onset month (1-indexed), or -1 if no onset detected
    """
    threshold = np.percentile(scores, threshold_percentile)

    for month_idx, score in enumerate(scores):
        if score > threshold:
            return month_idx + 1  # 1-indexed

    return -1


def calculate_persistence(
    scores: np.ndarray,
    onset_month: int,
    threshold_percentile: float = 90.0
) -> int:
    """
    Calculate persistence duration from onset month.

    Args:
        scores: Array of monthly scores
        onset_month: Onset month (1-indexed)
        threshold_percentile: Percentile threshold

    Returns:
        Number of consecutive months above threshold
    """
    if onset_month == -1:
        return 0

    threshold = np.percentile(scores, threshold_percentile)
    onset_idx = onset_month - 1

    duration = 0
    for idx in range(onset_idx, len(scores)):
        if scores[idx] > threshold:
            duration += 1
        else:
            break

    return duration


def generate_tile_timeline(
    hdf5_file: h5py.File,
    tile_metadata: dict,
    num_months: int = 6
) -> dict:
    """
    Generate timeline data for one tile.

    Returns timeline dictionary with monthly scores and statistics.
    """
    tile_id = tile_metadata["tile_id"]
    hdf5_key = tile_id_to_hdf5_key(tile_id)

    if hdf5_key not in hdf5_file:
        print(f"Warning: {hdf5_key} not found in HDF5 file")
        return {}

    tile_group = hdf5_file[hdf5_key]

    # Load data
    residuals = tile_group["residuals"][:]  # Shape: (12, 256)
    tile_scores = tile_group["tile_scores"][:]  # Shape: (12,)
    persistence_baseline = tile_group["baselines"]["persistence"][:]
    seasonal_baseline = tile_group["baselines"]["seasonal"][:]

    # Calculate mean residual per month
    mean_residuals = residuals.mean(axis=1)  # Shape: (12,)

    # Detect onset and persistence for world model
    onset_month = detect_onset(mean_residuals[:num_months])
    persistence_duration = calculate_persistence(
        mean_residuals, onset_month
    )

    # Build monthly data
    monthly_data = []
    for month in range(1, num_months + 1):
        month_idx = month - 1

        monthly_data.append({
            "month": month,
            "label": f"2024-{month:02d}",
            "scores": {
                "world_model": round(float(mean_residuals[month_idx]), 3),
                "world_model_tile": round(float(tile_scores[month_idx]), 3),
                "persistence": round(float(persistence_baseline[month_idx]), 3),
                "seasonal": round(float(seasonal_baseline[month_idx]), 3)
            },
            "anomaly": bool(mean_residuals[month_idx] > np.percentile(mean_residuals[:num_months], 90))
        })

    # Build timeline
    timeline = {
        "tile_id": tile_id,
        "change_type": tile_metadata["change_type"],
        "location": {
            "latitude": tile_metadata["latitude"],
            "longitude": tile_metadata["longitude"]
        },
        "analysis": {
            "onset_month": onset_month,
            "persistence_duration": persistence_duration,
            "max_score": round(float(mean_residuals[:num_months].max()), 3),
            "max_score_month": int(mean_residuals[:num_months].argmax() + 1)
        },
        "timeline": monthly_data
    }

    return timeline


def generate_all_timelines(
    hdf5_path: Path,
    metadata_path: Path,
    output_base: Path
):
    """Generate timeline JSON files for all tiles."""
    # Load metadata
    with open(metadata_path) as f:
        metadata = json.load(f)

    num_months = metadata["num_months"]

    print(f"Processing {len(metadata['tiles'])} tiles...")

    # Open HDF5 file
    with h5py.File(hdf5_path, "r") as hdf5_file:
        for tile_metadata in metadata["tiles"]:
            tile_id = tile_metadata["tile_id"]
            print(f"\nProcessing tile {tile_id} timeline...")

            # Generate timeline
            timeline = generate_tile_timeline(
                hdf5_file, tile_metadata, num_months
            )

            if not timeline:
                continue

            # Save to file
            tile_dir = output_base / f"tile_{tile_id:03d}"
            tile_dir.mkdir(parents=True, exist_ok=True)

            output_path = tile_dir / "timeseries.json"
            with open(output_path, "w") as f:
                json.dump(timeline, f, indent=2)

            print(f"Generated: {output_path}")
            print(f"  Onset: month {timeline['analysis']['onset_month']}")
            print(f"  Persistence: {timeline['analysis']['persistence_duration']} months")
            print(f"  Max score: {timeline['analysis']['max_score']} (month {timeline['analysis']['max_score_month']})")

    print("\n=== Timeline Generation Complete ===")


def main():
    base_dir = Path(__file__).parent.parent
    hdf5_path = base_dir / "data" / "residuals_test.h5"
    metadata_path = base_dir / "data" / "aoi_sf_seed" / "metadata.json"
    output_base = base_dir / "data" / "aoi_sf_seed" / "tiles"

    generate_all_timelines(hdf5_path, metadata_path, output_base)


if __name__ == "__main__":
    main()
