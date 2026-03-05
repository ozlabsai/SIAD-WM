#!/usr/bin/env python3
"""Create test HDF5 file with realistic residual data for 3 tiles

This script generates a minimal test dataset for the SIAD demo v2.0.
It creates data for 3 tiles with realistic score patterns and metadata.
"""

import h5py
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuration
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "residuals_test.h5"
NUM_MONTHS = 12
NUM_TOKENS = 256
TILES = ["tile_x000_y000", "tile_x000_y001", "tile_x001_y000"]

# Tile metadata
TILE_METADATA = {
    "tile_x000_y000": {
        "lat": 37.7599,
        "lon": -122.3894,
        "region": "san_francisco_mission_bay",
        "onset_idx": 5,  # June 2024
        "peak_score": 0.82
    },
    "tile_x000_y001": {
        "lat": 40.2599,
        "lon": -122.3894,
        "region": "northern_agricultural_belt",
        "onset_idx": 6,  # July 2024
        "peak_score": 0.71
    },
    "tile_x001_y000": {
        "lat": 37.7599,
        "lon": -119.8894,
        "region": "central_industrial_zone",
        "onset_idx": 7,  # August 2024
        "peak_score": 0.68
    }
}


def generate_tile_scores(onset_idx: int, peak_score: float, num_months: int) -> np.ndarray:
    """Generate realistic tile scores with onset spike pattern

    Args:
        onset_idx: Month index where anomaly begins (0-based)
        peak_score: Maximum score at onset
        num_months: Total number of months

    Returns:
        Array of scores with realistic onset pattern
    """
    scores = np.zeros(num_months, dtype=np.float32)

    for i in range(num_months):
        if i < onset_idx:
            # Pre-onset: low baseline with small noise
            scores[i] = 0.2 + np.random.random() * 0.15
        else:
            # Post-onset: spike then gradual decay
            months_since_onset = i - onset_idx
            scores[i] = peak_score - (months_since_onset * 0.05) + (np.random.random() * 0.08)

    # Clip to valid range [0, 1]
    scores = np.clip(scores, 0.0, 1.0)

    return scores


def generate_token_residuals(tile_scores: np.ndarray, num_tokens: int) -> np.ndarray:
    """Generate token-level residuals from tile scores

    Tile score is the 90th percentile of token residuals, so we generate
    token residuals that satisfy this constraint.

    Args:
        tile_scores: Array of tile scores (one per month)
        num_tokens: Number of spatial tokens (256)

    Returns:
        Array of shape (T, 256) with token residuals
    """
    num_months = len(tile_scores)
    residuals = np.zeros((num_months, num_tokens), dtype=np.float32)

    for t in range(num_months):
        # Generate tokens with ~90th percentile = tile_score
        # Use beta distribution for realistic spread
        base_residuals = np.random.beta(2, 5, num_tokens) * tile_scores[t]

        # Ensure 90th percentile matches tile score
        p90 = np.percentile(base_residuals, 90)
        if p90 > 0:
            base_residuals = base_residuals * (tile_scores[t] / p90)

        # Add some high-value outliers to match 90th percentile
        num_hotspots = int(num_tokens * 0.1)  # Top 10%
        hotspot_indices = np.random.choice(num_tokens, num_hotspots, replace=False)
        base_residuals[hotspot_indices] = tile_scores[t] + np.random.random(num_hotspots) * 0.15

        # Clip to valid range
        residuals[t] = np.clip(base_residuals, 0.0, 1.0)

    return residuals


def generate_baseline_scores(world_model_scores: np.ndarray, baseline_type: str) -> np.ndarray:
    """Generate baseline scores that are worse than world model

    Args:
        world_model_scores: World model tile scores
        baseline_type: "persistence", "seasonal", or "linear"

    Returns:
        Baseline scores (higher = worse prediction)
    """
    num_months = len(world_model_scores)

    if baseline_type == "persistence":
        # Persistence is worst for dynamic changes
        # Add 0.2-0.3 to world model scores
        return world_model_scores + (0.2 + np.random.random(num_months) * 0.1)

    elif baseline_type == "seasonal":
        # Seasonal is better than persistence but still worse than world model
        # Add 0.15-0.25 to world model scores
        return world_model_scores + (0.15 + np.random.random(num_months) * 0.1)

    elif baseline_type == "linear":
        # Linear is between persistence and seasonal
        # Add 0.1-0.2 to world model scores
        return world_model_scores + (0.1 + np.random.random(num_months) * 0.1)

    else:
        raise ValueError(f"Unknown baseline type: {baseline_type}")


def generate_timestamps(start_month: str, num_months: int) -> np.ndarray:
    """Generate monthly timestamps

    Args:
        start_month: Starting month in YYYY-MM format
        num_months: Number of months to generate

    Returns:
        Array of timestamp strings (YYYY-MM)
    """
    from datetime import datetime, timedelta
    import calendar

    year, month = map(int, start_month.split('-'))
    timestamps = []

    for _ in range(num_months):
        timestamps.append(f"{year:04d}-{month:02d}")

        # Increment month
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Return as fixed-length string array
    return np.array(timestamps, dtype='S7')


def create_test_hdf5():
    """Create test HDF5 file with realistic residual data"""

    print(f"Creating test HDF5 file: {OUTPUT_PATH}")

    # Ensure directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing file
    if OUTPUT_PATH.exists():
        print(f"  Removing existing file...")
        OUTPUT_PATH.unlink()

    # Create HDF5 file with SWMR support
    with h5py.File(OUTPUT_PATH, 'w', libver='latest') as f:
        # Global metadata
        f.attrs['schema_version'] = '1.0'
        f.attrs['num_tiles'] = len(TILES)
        f.attrs['date_range_start'] = '2024-01'
        f.attrs['date_range_end'] = '2024-12'
        f.attrs['encoder_checkpoint'] = 'checkpoints/encoder_best.pth'
        f.attrs['transition_checkpoint'] = 'checkpoints/transition_best.pth'
        f.attrs['created_at'] = datetime.now().isoformat()

        print(f"  Creating {len(TILES)} tiles...")

        for tile_id in TILES:
            print(f"    Processing {tile_id}...")
            meta = TILE_METADATA[tile_id]

            # Create tile group
            tile_group = f.create_group(tile_id)

            # Add tile metadata
            tile_group.attrs['lat'] = meta['lat']
            tile_group.attrs['lon'] = meta['lon']
            tile_group.attrs['region'] = meta['region']
            tile_group.attrs['tile_size_km'] = 256
            tile_group.attrs['context_month'] = '2024-01'
            tile_group.attrs['horizon'] = 6
            tile_group.attrs['model_version'] = 'v2.0-test'
            tile_group.attrs['weather_normalized'] = True
            tile_group.attrs['created_at'] = datetime.now().isoformat()

            # Generate tile scores with onset pattern
            tile_scores = generate_tile_scores(
                onset_idx=meta['onset_idx'],
                peak_score=meta['peak_score'],
                num_months=NUM_MONTHS
            )

            # Generate token-level residuals
            residuals = generate_token_residuals(tile_scores, NUM_TOKENS)

            # Generate timestamps
            timestamps = generate_timestamps('2024-01', NUM_MONTHS)

            # Generate baseline scores
            persistence = generate_baseline_scores(tile_scores, 'persistence')
            seasonal = generate_baseline_scores(tile_scores, 'seasonal')

            # Create datasets with compression
            tile_group.create_dataset(
                'residuals',
                data=residuals,
                dtype=np.float32,
                compression='gzip',
                compression_opts=4,
                chunks=(1, NUM_TOKENS)
            )

            tile_group.create_dataset(
                'tile_scores',
                data=tile_scores,
                dtype=np.float32,
                compression='gzip',
                compression_opts=4,
                chunks=(12,)
            )

            tile_group.create_dataset(
                'timestamps',
                data=timestamps,
                dtype='S7'
            )

            # Create baselines group
            baseline_group = tile_group.create_group('baselines')

            baseline_group.create_dataset(
                'persistence',
                data=persistence,
                dtype=np.float32,
                compression='gzip',
                compression_opts=4
            )

            baseline_group.create_dataset(
                'seasonal',
                data=seasonal,
                dtype=np.float32,
                compression='gzip',
                compression_opts=4
            )

            print(f"      Created datasets: residuals {residuals.shape}, scores {tile_scores.shape}")
            print(f"      Peak score: {tile_scores.max():.3f} at month {tile_scores.argmax()}")

        # Enable SWMR mode for concurrent reads
        f.swmr_mode = True

    print(f"✅ Test HDF5 file created successfully!")
    print(f"   Location: {OUTPUT_PATH}")
    print(f"   Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
    print(f"   Tiles: {len(TILES)}")
    print(f"   Months per tile: {NUM_MONTHS}")
    print(f"   Tokens per month: {NUM_TOKENS}")


def validate_file():
    """Validate the created HDF5 file"""
    print(f"\nValidating file structure...")

    with h5py.File(OUTPUT_PATH, 'r', libver='latest', swmr=True) as f:
        # Check global attributes
        assert 'schema_version' in f.attrs
        print(f"  ✓ Schema version: {f.attrs['schema_version']}")

        # Check each tile
        for tile_id in TILES:
            assert tile_id in f
            tile_group = f[tile_id]

            # Check required datasets
            assert 'residuals' in tile_group
            assert 'tile_scores' in tile_group
            assert 'timestamps' in tile_group
            assert 'baselines' in tile_group

            # Check shapes
            T = tile_group['tile_scores'].shape[0]
            assert tile_group['residuals'].shape == (T, NUM_TOKENS)
            assert tile_group['timestamps'].shape == (T,)

            # Check baselines
            baseline_group = tile_group['baselines']
            assert 'persistence' in baseline_group
            assert 'seasonal' in baseline_group

            # Check data ranges
            residuals = tile_group['residuals'][:]
            assert np.all(residuals >= 0.0) and np.all(residuals <= 1.0)

            scores = tile_group['tile_scores'][:]
            assert np.all(scores >= 0.0) and np.all(scores <= 1.0)

            print(f"  ✓ {tile_id}: residuals {residuals.shape}, scores {scores.shape}")

    print(f"✅ Validation passed!")


if __name__ == "__main__":
    create_test_hdf5()
    validate_file()
    print("\n🎉 Test HDF5 file ready for use!")
