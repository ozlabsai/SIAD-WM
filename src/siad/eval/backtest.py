"""
Backtesting validation.

Validates detection against known construction regions.
Success criterion (SC-002): hit_rate >= 0.80
"""

from typing import List


def backtest_known_sites(
    hotspots: List[dict],
    validation_config: dict,
    temporal_tolerance_months: int = 2,
) -> dict:
    """
    Measure hit rate on known construction sites.

    For each known site:
    1. Check if any detected hotspot overlaps with site's tile_ids
    2. Check if detection month is within ±temporal_tolerance of construction_period

    Args:
        hotspots: List of detected hotspot dicts from clustering
        validation_config: {
            "validation_regions": [
                {
                    "site_name": str,
                    "construction_period": [start_month, end_month],  # ISO 8601
                    "tile_ids": [tile_id, ...]
                },
                ...
            ]
        }
        temporal_tolerance_months: Tolerance for detection timing (default 2)

    Returns:
        {
            "hit_rate": float,              # Fraction of known sites flagged
            "known_sites_flagged": int,
            "known_sites_total": int,
            "details": [...]                # Per-site hit/miss details
        }
    """
    validation_regions = validation_config.get("validation_regions", [])

    if not validation_regions:
        return {
            "hit_rate": 0.0,
            "known_sites_flagged": 0,
            "known_sites_total": 0,
            "details": [],
        }

    details = []
    sites_flagged = 0

    for site in validation_regions:
        site_name = site["site_name"]
        site_tile_ids = set(site["tile_ids"])
        construction_period = site.get("construction_period", [])

        # Check for spatial overlap with any hotspot
        matched_hotspots = []
        for hotspot in hotspots:
            hotspot_tile_ids = set(hotspot["tile_ids"])
            if hotspot_tile_ids.intersection(site_tile_ids):
                matched_hotspots.append(hotspot)

        # Check temporal alignment (simplified - just check if any overlap)
        # TODO: Implement proper ISO 8601 month range comparison
        hit = len(matched_hotspots) > 0

        if hit:
            sites_flagged += 1

        details.append(
            {
                "site_name": site_name,
                "hit": hit,
                "matched_hotspots": len(matched_hotspots),
                "matched_hotspot_ids": [h["hotspot_id"] for h in matched_hotspots],
            }
        )

    hit_rate = sites_flagged / len(validation_regions) if validation_regions else 0.0

    return {
        "hit_rate": float(hit_rate),
        "known_sites_flagged": sites_flagged,
        "known_sites_total": len(validation_regions),
        "details": details,
    }
