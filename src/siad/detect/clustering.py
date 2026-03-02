"""
Spatial clustering for hotspot identification.

Groups >= N spatially connected tiles into hotspots using connected components.
"""

from typing import Dict, List

import numpy as np
from scipy.ndimage import label


def build_tile_grid(tile_coords: Dict[str, tuple]) -> tuple:
    """
    Convert tile_id -> (x, y) dict to binary grid.

    Args:
        tile_coords: {tile_id: (x_idx, y_idx)}

    Returns:
        (grid, coord_to_id_map)
        - grid: Binary numpy array [max_x+1, max_y+1]
        - coord_to_id_map: {(x, y): tile_id}
    """
    if not tile_coords:
        return np.zeros((0, 0), dtype=np.int32), {}

    max_x = max(coords[0] for coords in tile_coords.values())
    max_y = max(coords[1] for coords in tile_coords.values())

    grid = np.zeros((max_x + 1, max_y + 1), dtype=np.int32)
    coord_to_id = {}

    for tile_id, (x, y) in tile_coords.items():
        grid[x, y] = 1
        coord_to_id[(x, y)] = tile_id

    return grid, coord_to_id


def cluster_tiles(
    persistent_tiles: dict,
    tile_coords: Dict[str, tuple],
    min_cluster_size: int = 3,
    connectivity: str = "8",
) -> List[dict]:
    """
    Cluster spatially connected tiles into hotspots.

    Args:
        persistent_tiles: {
            tile_id: {
                "persistent_spans": [(start, end), ...],
                "persistence_count": int,
                "max_score": float
            }
        }
        tile_coords: {tile_id: (x_idx, y_idx)} for ALL tiles in AOI
        min_cluster_size: Minimum tiles per cluster (default 3)
        connectivity: "8" for 8-connectivity (diagonal), "4" for rook's case

    Returns:
        [
            {
                "hotspot_id": "hotspot_001",
                "tile_ids": [tile_id, ...],
                "centroid": {"lon": float, "lat": float},  # Placeholder coords
                "first_detected_month": "2023-06",  # Placeholder
                "persistence_months": int,
                "max_acceleration_score": float
            },
            ...
        ]
    """
    # Build grid from persistent tiles only
    persistent_coords = {
        tile_id: tile_coords[tile_id]
        for tile_id in persistent_tiles.keys()
        if tile_id in tile_coords
    }

    if not persistent_coords:
        return []

    grid, coord_to_id = build_tile_grid(persistent_coords)

    # Define connectivity structure
    if connectivity == "8":
        structure = np.ones((3, 3), dtype=int)  # 8-connectivity
    else:
        structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=int)  # 4-connectivity

    # Run connected components labeling
    labeled_grid, num_clusters = label(grid, structure=structure)

    # Extract clusters
    hotspots = []
    for cluster_id in range(1, num_clusters + 1):
        # Find tiles in this cluster
        cluster_coords = np.argwhere(labeled_grid == cluster_id)
        cluster_tile_ids = [
            coord_to_id[(x, y)] for x, y in cluster_coords if (x, y) in coord_to_id
        ]

        # Filter by min size
        if len(cluster_tile_ids) < min_cluster_size:
            continue

        # Compute cluster metadata
        max_score = max(
            persistent_tiles[tid]["max_score"] for tid in cluster_tile_ids
        )
        persistence_months = max(
            persistent_tiles[tid]["persistence_count"] for tid in cluster_tile_ids
        )

        # Centroid (placeholder - use mean of tile indices for now)
        mean_x = np.mean([tile_coords[tid][0] for tid in cluster_tile_ids])
        mean_y = np.mean([tile_coords[tid][1] for tid in cluster_tile_ids])

        hotspot = {
            "hotspot_id": f"hotspot_{cluster_id:03d}",
            "tile_ids": cluster_tile_ids,
            "centroid": {
                "lon": mean_x,  # TODO: Convert to geographic coords (Infra agent)
                "lat": mean_y,
            },
            "first_detected_month": "2023-01",  # TODO: Extract from persistent_spans
            "persistence_months": persistence_months,
            "max_acceleration_score": float(max_score),
        }

        hotspots.append(hotspot)

    return hotspots
