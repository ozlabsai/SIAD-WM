#!/usr/bin/env python3
"""Create manifest.jsonl from exported GeoTIFFs

Scans a directory of GeoTIFF files and creates a manifest for training.

Usage:
    python scripts/create_manifest.py --data-dir data/geotiffs --output data/manifest.jsonl
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict
import re


def extract_tile_month(filename: str):
    """Extract tile_id and month from filename

    Expected format: tile_x000_y001_2023-05.tif
    """
    match = re.match(r'(tile_x\d+_y\d+)_(\d{4}-\d{2})\.tif', filename)
    if match:
        return match.group(1), match.group(2)
    return None, None


def create_manifest(data_dir: str, output_path: str, min_months: int = 12):
    """Create manifest.jsonl from GeoTIFF files

    Args:
        data_dir: Directory containing GeoTIFF files
        output_path: Where to save manifest.jsonl
        min_months: Minimum number of months required per tile
    """
    data_dir = Path(data_dir)

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print(f"   Make sure to download GeoTIFFs first:")
        print(f"   gsutil -m rsync -r gs://siad-exports/test-export {data_dir}")
        return

    # Scan all GeoTIFFs
    print(f"Scanning {data_dir} for GeoTIFF files...")
    tile_data = defaultdict(list)

    for tif_path in data_dir.glob("*.tif"):
        tile_id, month = extract_tile_month(tif_path.name)
        if tile_id and month:
            tile_data[tile_id].append((month, str(tif_path)))

    print(f"Found {len(tile_data)} unique tiles")

    # Create manifest entries
    manifest_samples = []
    skipped_tiles = []

    for tile_id, month_files in sorted(tile_data.items()):
        # Sort by month
        month_files = sorted(month_files, key=lambda x: x[0])

        if len(month_files) < min_months:
            skipped_tiles.append((tile_id, len(month_files)))
            continue

        months = [m for m, _ in month_files]
        observations = [f for _, f in month_files]

        # Create dummy actions (will be replaced with real climate anomalies)
        # For now: [rain_anomaly, temp_anomaly] = [0.0, 0.0]
        actions = [[0.0, 0.0] for _ in months]

        sample = {
            "tile_id": tile_id,
            "months": months,
            "observations": observations,
            "actions": actions
        }

        manifest_samples.append(sample)

    # Save manifest
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        for sample in manifest_samples:
            f.write(json.dumps(sample) + '\n')

    # Summary
    print(f"\n{'='*60}")
    print(f"Manifest created: {output_path}")
    print(f"{'='*60}")
    print(f"✓ Valid tiles: {len(manifest_samples)}")
    print(f"  Total tile-months: {sum(len(s['months']) for s in manifest_samples)}")

    if skipped_tiles:
        print(f"\n⚠️  Skipped {len(skipped_tiles)} tiles (< {min_months} months):")
        for tile_id, count in skipped_tiles[:5]:
            print(f"  {tile_id}: {count} months")
        if len(skipped_tiles) > 5:
            print(f"  ... and {len(skipped_tiles) - 5} more")

    # Sample entry
    if manifest_samples:
        sample = manifest_samples[0]
        print(f"\n📋 Sample entry:")
        print(f"  Tile: {sample['tile_id']}")
        print(f"  Months: {len(sample['months'])} ({sample['months'][0]} to {sample['months'][-1]})")
        print(f"  First observation: {sample['observations'][0]}")

    print(f"\n{'='*60}")
    print(f"Ready to train!")
    print(f"  ./scripts/train_a100.sh {output_path}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Create manifest.jsonl from GeoTIFFs")
    parser.add_argument("--data-dir", type=str, required=True,
                       help="Directory containing GeoTIFF files")
    parser.add_argument("--output", type=str, default="data/manifest.jsonl",
                       help="Output manifest path")
    parser.add_argument("--min-months", type=int, default=12,
                       help="Minimum months required per tile")
    args = parser.parse_args()

    create_manifest(args.data_dir, args.output, args.min_months)


if __name__ == "__main__":
    main()
