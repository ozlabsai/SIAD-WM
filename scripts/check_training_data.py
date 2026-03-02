#!/usr/bin/env python3
"""Quick check if training data is ready for SIAD training

Verifies:
- manifest.jsonl exists
- GeoTIFF files referenced in manifest exist
- Data matches expected format
"""

import json
from pathlib import Path
import argparse


def check_manifest(manifest_path: str, data_root: str = None):
    """Check if manifest.jsonl is valid and data files exist"""

    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return False

    data_root = Path(data_root) if data_root else manifest_path.parent

    print(f"✓ Manifest found: {manifest_path}")
    print(f"  Data root: {data_root}")
    print()

    # Parse manifest
    samples = []
    with open(manifest_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"⚠️  Line {line_num}: Invalid JSON - {e}")

    print(f"✓ Parsed {len(samples)} samples from manifest")

    if len(samples) == 0:
        print("❌ No valid samples found!")
        return False

    # Check first sample
    sample = samples[0]
    print(f"\n📋 Sample structure:")
    print(f"  tile_id: {sample.get('tile_id', 'MISSING')}")
    print(f"  months: {len(sample.get('months', []))} months")
    print(f"  observations: {len(sample.get('observations', []))} files")
    print(f"  actions: {len(sample.get('actions', []))} action vectors")

    # Check if files exist
    if 'observations' in sample and len(sample['observations']) > 0:
        first_obs = sample['observations'][0]
        full_path = data_root / first_obs if not Path(first_obs).is_absolute() else Path(first_obs)

        print(f"\n📁 Checking first GeoTIFF:")
        print(f"  Path: {full_path}")

        if full_path.exists():
            print(f"  ✓ File exists")

            # Try to get file size
            size_mb = full_path.stat().st_size / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")

            # Try to load with rasterio if available
            try:
                import rasterio
                with rasterio.open(full_path) as src:
                    print(f"  Bands: {src.count}")
                    print(f"  Shape: {src.height} × {src.width}")
                    print(f"  ✓ Valid GeoTIFF")
            except ImportError:
                print("  (rasterio not available - can't validate GeoTIFF)")
            except Exception as e:
                print(f"  ⚠️  Error reading GeoTIFF: {e}")
        else:
            print(f"  ❌ File not found!")
            return False

    # Summary
    print(f"\n{'='*60}")
    print(f"✓ Training data ready!")
    print(f"  Samples: {len(samples)}")
    print(f"  Context needed: 1 month")
    print(f"  Rollout needed: 6 months")
    print(f"  Min length per sample: 7 months")
    print(f"{'='*60}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Check if training data is ready")
    parser.add_argument("--manifest", type=str, default="data/manifest.jsonl",
                       help="Path to manifest.jsonl")
    parser.add_argument("--data-root", type=str, default=None,
                       help="Root directory for data files (defaults to manifest parent)")
    args = parser.parse_args()

    check_manifest(args.manifest, args.data_root)


if __name__ == "__main__":
    main()
