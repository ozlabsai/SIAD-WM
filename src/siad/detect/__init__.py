"""
Detection module for SIAD MVP.

Implements counterfactual-based acceleration detection:
- Rollout engine for neutral scenario predictions
- Acceleration scoring (divergence from neutral baseline)
- Persistence filtering and spatial clustering
- Modality attribution (SAR/optical/lights decomposition)
"""

from .rollout_engine import RolloutEngine
from .scoring import (
    compute_acceleration_scores,
    flag_tiles_by_percentile,
)
from .persistence import filter_by_persistence, find_consecutive_runs
from .clustering import cluster_tiles, build_tile_grid
from .attribution import (
    compute_modality_attribution,
    classify_hotspot,
    normalize_contributions,
)

__all__ = [
    "RolloutEngine",
    "compute_acceleration_scores",
    "flag_tiles_by_percentile",
    "filter_by_persistence",
    "find_consecutive_runs",
    "cluster_tiles",
    "build_tile_grid",
    "compute_modality_attribution",
    "classify_hotspot",
    "normalize_contributions",
]
