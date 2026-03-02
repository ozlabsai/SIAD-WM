#!/usr/bin/env python3
"""Create mock GeoTIFF files and manifest for testing dataset loading

Generates synthetic 8-band GeoTIFFs for 2 tiles × 12 months to test SIADDataset.

Usage:
    uv run scripts/create_mock_geotiffs.py --output-dir data/mock_test
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import numpy as np
import json

try:
    import rasterio
    from rasterio.transform import from_bounds
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    print("ERROR: rasterio not installed. Install with: uv add rasterio")
    sys.exit(1)


def create_mock_geotiff(
    output_path: Path,
    num_bands: int = 8,
    width: int = 256,
    height: int = 256,
    seed: int = 42
):
    """Create a single mock GeoTIFF with random data

    Args:
        output_path: Where to save the GeoTIFF
        num_bands: Number of bands (default 8 for SIAD)
        width: Image width in pixels
        height: Image height in pixels
        seed: Random seed for reproducibility
    """
    rng = np.random.RandomState(seed)

    # Generate random data for each band
    # Use different distributions to simulate real satellite data
    data = np.zeros((num_bands, height, width), dtype=np.float32)

    # Sentinel-2 optical bands (0-3): B2, B3, B4, B8 - scaled to [0, 1]
    for i in range(4):
        data[i] = rng.uniform(0.0, 1.0, (height, width))

    # Sentinel-1 SAR bands (4-5): VV, VH - scaled to [-30, 0] dB converted to linear
    for i in range(4, 6):
        db_values = rng.uniform(-30, 0, (height, width))
        data[i] = 10 ** (db_values / 10)  # Convert dB to linear

    # VIIRS lights (6): Typically low values with some hotspots
    lights = rng.exponential(0.1, (height, width))
    data[6] = np.clip(lights, 0, 1)

    # S2 valid mask (7): Binary mask with some cloud coverage
    data[7] = rng.choice([0, 1], size=(height, width), p=[0.2, 0.8])

    # Create GeoTIFF with minimal georeferencing
    # Use a dummy transform (1 degree per pixel)
    transform = from_bounds(
        west=-180, south=-90, east=-179, north=-89,
        width=width, height=height
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=num_bands,
        dtype=rasterio.float32,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(data)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Create mock GeoTIFF data for testing")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/mock_test",
        help="Output directory for GeoTIFFs and manifest"
    )
    parser.add_argument(
        "--num-tiles",
        type=int,
        default=2,
        help="Number of tiles to generate"
    )
    parser.add_argument(
        "--num-months",
        type=int,
        default=12,
        help="Number of months per tile"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    tiles_dir = output_dir / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating mock GeoTIFF dataset:")
    print(f"  Output directory: {output_dir}")
    print(f"  Tiles: {args.num_tiles}")
    print(f"  Months: {args.num_months}")

    manifest_samples = []

    for tile_idx in range(args.num_tiles):
        tile_id = f"tile_x{tile_idx:03d}_y{tile_idx:03d}"
        print(f"\nGenerating tile: {tile_id}")

        months = []
        observations = []
        actions = []

        for month_idx in range(1, args.num_months + 1):
            month = f"2023-{month_idx:02d}"
            months.append(month)

            # Create GeoTIFF filename
            geotiff_filename = f"{tile_id}_{month}.tif"
            geotiff_path = tiles_dir / geotiff_filename
            relative_path = f"tiles/{geotiff_filename}"

            # Generate GeoTIFF
            seed = tile_idx * 1000 + month_idx
            create_mock_geotiff(geotiff_path, seed=seed)
            observations.append(relative_path)

            # Generate random actions [rain_anom, temp_anom]
            rng = np.random.RandomState(seed)
            rain_anom = float(rng.uniform(-2, 2))
            temp_anom = float(rng.uniform(-1, 1))
            actions.append([rain_anom, temp_anom])

            print(f"  Created: {geotiff_filename}")

        # Add to manifest
        manifest_samples.append({
            "tile_id": tile_id,
            "months": months,
            "observations": observations,
            "actions": actions
        })

    # Write manifest.jsonl
    manifest_path = output_dir / "manifest.jsonl"
    with open(manifest_path, 'w') as f:
        for sample in manifest_samples:
            f.write(json.dumps(sample) + '\n')

    print(f"\nManifest created: {manifest_path}")
    print(f"Total samples: {len(manifest_samples)}")

    # Print example usage
    print("\n" + "=" * 80)
    print("Mock dataset created successfully!")
    print("=" * 80)
    print("\nTo test the dataset loader, run:")
    print(f"  python -c \"from siad.train import SIADDataset; ")
    print(f"  ds = SIADDataset('{manifest_path}', data_root='{output_dir}'); ")
    print(f"  print('Dataset length:', len(ds)); ")
    print(f"  sample = ds[0]; ")
    print(f"  print('Sample keys:', sample.keys())\"")

    return 0


if __name__ == "__main__":
    exit(main())
