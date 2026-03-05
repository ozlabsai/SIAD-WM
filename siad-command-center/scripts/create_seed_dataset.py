#!/usr/bin/env python
"""
Create seed dataset by extracting 2 tiles x 6 months from existing data.

Selects tiles with clear change events (onset months 4-6) for demo purposes.
Extracts Jan-Jun 2024 (months 1-6) from the full 12-month dataset.

Output structure:
  data/aoi_sf_seed/
    tiles/
      tile_000/
        month_01/
          actual.png
          predicted.png
          residual.png
    metadata.json
    months.json
"""

import json
import shutil
from pathlib import Path


def select_demo_tiles(metadata: dict, num_tiles: int = 2) -> list[int]:
    """
    Select tiles with diverse change types and early onset months.

    Prioritizes tiles with onset in months 4-6 for clear demonstration.
    """
    # Filter tiles with onset months 4-6 and diverse change types
    candidates = [
        tile for tile in metadata["tiles"]
        if 4 <= tile["onset_month"] <= 6
    ]

    # Select diverse change types
    selected = []
    change_types_seen = set()

    for tile in candidates:
        change_type = tile["change_type"]
        if change_type not in change_types_seen and change_type != "seasonal_only":
            selected.append(tile["tile_id"])
            change_types_seen.add(change_type)
            if len(selected) >= num_tiles:
                break

    # Fallback: just take first N if diversity requirement not met
    if len(selected) < num_tiles:
        selected = [tile["tile_id"] for tile in candidates[:num_tiles]]

    return selected


def copy_tile_month(src_base: Path, dst_base: Path, tile_id: int, month: int):
    """Copy imagery files for one tile/month."""
    src_month_dir = src_base / f"tile_{tile_id:03d}" / f"month_{month:02d}"
    dst_month_dir = dst_base / f"tile_{tile_id:03d}" / f"month_{month:02d}"

    if not src_month_dir.exists():
        print(f"Warning: Source not found: {src_month_dir}")
        return

    dst_month_dir.mkdir(parents=True, exist_ok=True)

    # Copy PNG files
    for png_file in src_month_dir.glob("*.png"):
        shutil.copy2(png_file, dst_month_dir / png_file.name)


def create_seed_dataset(
    src_dir: Path,
    dst_dir: Path,
    num_tiles: int = 2,
    num_months: int = 6
):
    """
    Extract seed dataset from full dataset.

    Args:
        src_dir: Source directory (data/satellite_imagery)
        dst_dir: Destination directory (data/aoi_sf_seed)
        num_tiles: Number of tiles to extract (default: 2)
        num_months: Number of months to extract (default: 6)
    """
    # Load metadata
    metadata_path = src_dir / "metadata.json"
    with open(metadata_path) as f:
        metadata = json.load(f)

    # Select tiles
    selected_tile_ids = select_demo_tiles(metadata, num_tiles)
    print(f"Selected tiles: {selected_tile_ids}")

    # Filter metadata
    selected_tiles = [
        tile for tile in metadata["tiles"]
        if tile["tile_id"] in selected_tile_ids
    ]

    # Copy imagery for selected tiles and months
    src_tiles_dir = src_dir / "tiles"
    dst_tiles_dir = dst_dir / "tiles"

    for tile in selected_tiles:
        tile_id = tile["tile_id"]
        print(f"Processing tile {tile_id} ({tile['change_type']})...")

        for month in range(1, num_months + 1):
            copy_tile_month(src_tiles_dir, dst_tiles_dir, tile_id, month)

    # Create seed metadata
    seed_metadata = {
        "tiles": selected_tiles,
        "tile_size": metadata["tile_size"],
        "num_months": num_months,
        "change_types": {
            tile["change_type"]: 1
            for tile in selected_tiles
        }
    }

    dst_metadata_path = dst_dir / "metadata.json"
    with open(dst_metadata_path, "w") as f:
        json.dump(seed_metadata, f, indent=2)

    print(f"Wrote: {dst_metadata_path}")

    # Create months.json
    months_data = {
        "months": [
            {"month": i, "label": f"2024-{i:02d}"} for i in range(1, num_months + 1)
        ],
        "num_months": num_months
    }

    months_path = dst_dir / "months.json"
    with open(months_path, "w") as f:
        json.dump(months_data, f, indent=2)

    print(f"Wrote: {months_path}")

    # Report statistics
    print("\n=== Seed Dataset Created ===")
    print(f"Tiles: {num_tiles} (IDs: {selected_tile_ids})")
    print(f"Months: {num_months} (Jan-Jun 2024)")
    print(f"Change types: {list(seed_metadata['change_types'].keys())}")

    # Calculate size
    total_size = sum(
        f.stat().st_size for f in dst_dir.rglob("*") if f.is_file()
    )
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")


def main():
    base_dir = Path(__file__).parent.parent
    src_dir = base_dir / "data" / "satellite_imagery"
    dst_dir = base_dir / "data" / "aoi_sf_seed"

    # Create output directory
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Create seed dataset
    create_seed_dataset(src_dir, dst_dir, num_tiles=2, num_months=6)


if __name__ == "__main__":
    main()
