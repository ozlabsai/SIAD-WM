"""
False-positive testing validation.

Measures FP rate on agriculture/monsoon regions.
Success criterion (SC-003): fp_rate < 0.20
"""

from typing import List


def test_false_positive_rate(
    hotspots: List[dict],
    fp_config: dict,
    acceptable_tiers: List[str] = None,
) -> dict:
    """
    Measure false positive rate on non-infrastructure regions.

    For each FP region:
    1. Count hotspots that overlap with region's tile_ids
    2. Exclude hotspots with confidence_tier in acceptable_tiers
    3. Compute FP rate = flagged_tiles / total_tiles

    Args:
        hotspots: List of detected hotspot dicts from clustering
        fp_config: {
            "false_positive_regions": [
                {
                    "region_name": str,
                    "land_cover": str,  # "agriculture" | "seasonal_water"
                    "tile_ids": [tile_id, ...]
                },
                ...
            ]
        }
        acceptable_tiers: List of confidence tiers to exclude from FP count
                         (default: ["Environmental"])

    Returns:
        {
            "fp_rate": float,               # Should be < 0.20 per SC-003
            "agriculture_hotspots": int,    # Non-acceptable hotspots in FP regions
            "agriculture_tiles_total": int,
            "details": [...]
        }
    """
    if acceptable_tiers is None:
        acceptable_tiers = ["Environmental"]

    fp_regions = fp_config.get("false_positive_regions", [])

    if not fp_regions:
        return {
            "fp_rate": 0.0,
            "agriculture_hotspots": 0,
            "agriculture_tiles_total": 0,
            "details": [],
        }

    # Aggregate all FP region tile IDs
    all_fp_tile_ids = set()
    for region in fp_regions:
        all_fp_tile_ids.update(region["tile_ids"])

    # Count hotspots in FP regions (excluding acceptable tiers)
    fp_hotspot_count = 0
    details = []

    for region in fp_regions:
        region_name = region["region_name"]
        region_tile_ids = set(region["tile_ids"])

        # Find hotspots overlapping this region
        matched_hotspots = []
        for hotspot in hotspots:
            hotspot_tile_ids = set(hotspot["tile_ids"])
            confidence_tier = hotspot.get("confidence_tier", "Unknown")

            if hotspot_tile_ids.intersection(region_tile_ids):
                # Exclude acceptable tiers
                if confidence_tier not in acceptable_tiers:
                    matched_hotspots.append(hotspot)

        fp_hotspot_count += len(matched_hotspots)

        details.append(
            {
                "region_name": region_name,
                "land_cover": region.get("land_cover", "unknown"),
                "fp_hotspots": len(matched_hotspots),
                "total_tiles": len(region_tile_ids),
                "matched_hotspot_ids": [h["hotspot_id"] for h in matched_hotspots],
            }
        )

    # Compute FP rate
    total_fp_tiles = len(all_fp_tile_ids)
    fp_rate = fp_hotspot_count / total_fp_tiles if total_fp_tiles > 0 else 0.0

    return {
        "fp_rate": float(fp_rate),
        "agriculture_hotspots": fp_hotspot_count,
        "agriculture_tiles_total": total_fp_tiles,
        "details": details,
    }
