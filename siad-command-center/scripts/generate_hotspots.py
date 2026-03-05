#!/usr/bin/env python
"""
Generate hotspot GeoJSON files from residual data.

Identifies regions with residuals above 95th percentile threshold, finds
connected components, and converts pixel coordinates to lat/lon polygons.

Output:
  - Per-month GeoJSON: tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_wm_hotspots.geojson
  - Aggregated ranking: hotspots_ranked.json
"""

import json
from pathlib import Path

import h5py
import numpy as np
from scipy import ndimage


def tile_id_to_hdf5_key(tile_id: int) -> str:
    """Convert tile_id to HDF5 key format."""
    x = tile_id % 5
    y = tile_id // 5
    return f"tile_x{x:03d}_y{y:03d}"


def pixels_to_latlon(
    pixels: np.ndarray,
    tile_metadata: dict,
    grid_size: int = 16
) -> list[tuple[float, float]]:
    """
    Convert pixel coordinates to lat/lon.

    Args:
        pixels: Nx2 array of (row, col) pixel coordinates in 16x16 grid
        tile_metadata: Tile metadata with lat/lon center
        grid_size: Size of residual grid (16x16)

    Returns:
        List of (lon, lat) tuples (GeoJSON order)
    """
    # Get tile center
    center_lat = tile_metadata["latitude"]
    center_lon = tile_metadata["longitude"]

    # Approximate degrees per pixel (rough estimate)
    # Assuming tile covers ~0.5 degrees (~55km at equator)
    tile_extent_deg = 0.5
    deg_per_pixel = tile_extent_deg / grid_size

    # Convert pixels to lat/lon offsets from center
    coords = []
    for row, col in pixels:
        # Invert row (image coordinates have origin at top-left)
        lat_offset = (grid_size / 2 - row) * deg_per_pixel
        lon_offset = (col - grid_size / 2) * deg_per_pixel

        lat = center_lat + lat_offset
        lon = center_lon + lon_offset
        coords.append((lon, lat))  # GeoJSON order: [lon, lat]

    return coords


def create_polygon_from_region(
    labeled_array: np.ndarray,
    region_id: int,
    tile_metadata: dict
) -> list[list[float]]:
    """
    Create polygon boundary from connected region.

    Uses convex hull of region pixels as simplified polygon.
    """
    # Get pixels belonging to this region
    rows, cols = np.where(labeled_array == region_id)
    pixels = np.column_stack([rows, cols])

    if len(pixels) < 3:
        # Need at least 3 points for polygon
        return []

    # Create bounding box as simplified polygon
    min_row, max_row = rows.min(), rows.max()
    min_col, max_col = cols.min(), cols.max()

    # Define corners (clockwise from top-left)
    corners = np.array([
        [min_row, min_col],
        [min_row, max_col],
        [max_row, max_col],
        [max_row, min_col],
        [min_row, min_col],  # Close polygon
    ])

    # Convert to lat/lon
    coords = pixels_to_latlon(corners, tile_metadata)

    return coords


def detect_hotspots(
    residuals: np.ndarray,
    tile_metadata: dict,
    threshold_percentile: float = 90.0,
    min_size: int = 2
) -> list[dict]:
    """
    Detect hotspot regions in residual grid.

    Args:
        residuals: 1D array of 256 residual scores
        tile_metadata: Tile metadata dictionary
        threshold_percentile: Percentile threshold for hotspot detection
        min_size: Minimum region size (in pixels)

    Returns:
        List of GeoJSON feature dictionaries
    """
    # Reshape to 16x16 grid
    grid = residuals.reshape(16, 16)

    # Calculate threshold
    threshold = np.percentile(residuals, threshold_percentile)

    # Binary mask of high-residual regions
    binary_mask = grid > threshold

    # Find connected components
    labeled_array, num_features = ndimage.label(binary_mask)

    # Extract features
    features = []
    for region_id in range(1, num_features + 1):
        # Get region stats
        region_mask = labeled_array == region_id
        region_size = region_mask.sum()

        if region_size < min_size:
            continue

        # Calculate region score (mean residual)
        region_scores = grid[region_mask]
        mean_score = float(region_scores.mean())
        max_score = float(region_scores.max())

        # Create polygon
        polygon_coords = create_polygon_from_region(
            labeled_array, region_id, tile_metadata
        )

        if not polygon_coords:
            continue

        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            },
            "properties": {
                "region_id": region_id,
                "size_pixels": int(region_size),
                "mean_score": round(mean_score, 3),
                "max_score": round(max_score, 3),
                "severity": "critical" if max_score >= 0.8 else
                           "high" if max_score >= 0.6 else "elevated"
            }
        }

        features.append(feature)

    return features


def process_tile_hotspots(
    hdf5_file: h5py.File,
    tile_metadata: dict,
    output_base: Path,
    num_months: int = 6
) -> list[dict]:
    """
    Process hotspots for all months of one tile.

    Returns list of hotspot summaries for ranking.
    """
    tile_id = tile_metadata["tile_id"]
    hdf5_key = tile_id_to_hdf5_key(tile_id)

    if hdf5_key not in hdf5_file:
        print(f"Warning: {hdf5_key} not found in HDF5 file")
        return []

    tile_group = hdf5_file[hdf5_key]
    residuals = tile_group["residuals"][:]  # Shape: (12, 256)

    tile_dir = output_base / f"tile_{tile_id:03d}"

    all_hotspots = []

    for month in range(1, num_months + 1):
        month_residuals = residuals[month - 1]

        # Detect hotspots
        features = detect_hotspots(month_residuals, tile_metadata)

        # Create GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        # Save to file
        overlay_dir = tile_dir / f"month_{month:02d}" / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)

        output_path = overlay_dir / f"2024-{month:02d}_wm_hotspots.geojson"
        with open(output_path, "w") as f:
            json.dump(geojson, f, indent=2)

        print(f"Generated: {output_path} ({len(features)} hotspots)")

        # Collect for ranking
        for feature in features:
            hotspot_summary = {
                "tile_id": tile_id,
                "month": month,
                "change_type": tile_metadata["change_type"],
                "location": {
                    "lat": tile_metadata["latitude"],
                    "lon": tile_metadata["longitude"]
                },
                **feature["properties"]
            }
            all_hotspots.append(hotspot_summary)

    return all_hotspots


def generate_all_hotspots(
    hdf5_path: Path,
    metadata_path: Path,
    output_base: Path
):
    """Generate hotspot GeoJSON files for all tiles."""
    # Load metadata
    with open(metadata_path) as f:
        metadata = json.load(f)

    num_months = metadata["num_months"]
    all_hotspots = []

    print(f"Processing {len(metadata['tiles'])} tiles x {num_months} months...")

    # Open HDF5 file
    with h5py.File(hdf5_path, "r") as hdf5_file:
        for tile_metadata in metadata["tiles"]:
            tile_id = tile_metadata["tile_id"]
            print(f"\nProcessing tile {tile_id}...")

            hotspots = process_tile_hotspots(
                hdf5_file, tile_metadata, output_base, num_months
            )
            all_hotspots.extend(hotspots)

    # Create ranked hotspots file
    ranked_hotspots = sorted(
        all_hotspots,
        key=lambda x: x["max_score"],
        reverse=True
    )

    ranked_output = output_base.parent / "hotspots_ranked.json"
    with open(ranked_output, "w") as f:
        json.dump(
            {
                "hotspots": ranked_hotspots,
                "total_count": len(ranked_hotspots)
            },
            f,
            indent=2
        )

    print(f"\n=== Hotspot Generation Complete ===")
    print(f"Total hotspots detected: {len(all_hotspots)}")
    print(f"Ranked hotspots saved to: {ranked_output}")


def main():
    base_dir = Path(__file__).parent.parent
    hdf5_path = base_dir / "data" / "residuals_test.h5"
    metadata_path = base_dir / "data" / "aoi_sf_seed" / "metadata.json"
    output_base = base_dir / "data" / "aoi_sf_seed" / "tiles"

    generate_all_hotspots(hdf5_path, metadata_path, output_base)


if __name__ == "__main__":
    main()
