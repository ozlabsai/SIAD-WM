"""
AOI Overview Map Generator

Generates static basemap showing AOI bounds with hotspot markers color-coded by confidence tier.
Uses matplotlib to avoid external API dependencies (Mapbox, OSM tile servers).
"""

import io
import base64
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# Confidence tier color scheme
TIER_COLORS = {
    "Structural": "#D32F2F",      # Red
    "Activity": "#F57C00",         # Orange
    "Environmental": "#1976D2"     # Blue
}


def generate_aoi_map(
    aoi_bounds: Dict[str, float],
    hotspots: List[Dict],
    output_size: Tuple[int, int] = (1200, 800),
    tile_size_km: float = 2.56
) -> str:
    """
    Generate AOI overview map with hotspot markers.

    Args:
        aoi_bounds: Dict with keys {min_lon, max_lon, min_lat, max_lat}
        hotspots: List of hotspot dicts (from hotspots.json)
        output_size: Figure size in pixels (width, height)
        tile_size_km: Tile grid spacing in kilometers (for grid overlay)

    Returns:
        Base64-encoded PNG image string

    Example:
        >>> aoi_bounds = {"min_lon": 12.0, "max_lon": 12.5, "min_lat": 34.0, "max_lat": 34.5}
        >>> hotspots = [{"centroid": {"lon": 12.25, "lat": 34.25}, "confidence_tier": "Structural"}]
        >>> map_b64 = generate_aoi_map(aoi_bounds, hotspots)
    """
    # Create figure
    dpi = 150
    fig_width = output_size[0] / dpi
    fig_height = output_size[1] / dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

    # Extract bounds
    min_lon = aoi_bounds["min_lon"]
    max_lon = aoi_bounds["max_lon"]
    min_lat = aoi_bounds["min_lat"]
    max_lat = aoi_bounds["max_lat"]

    # Set axis limits with 5% padding
    lon_padding = (max_lon - min_lon) * 0.05
    lat_padding = (max_lat - min_lat) * 0.05
    ax.set_xlim(min_lon - lon_padding, max_lon + lon_padding)
    ax.set_ylim(min_lat - lat_padding, max_lat + lat_padding)

    # Light gray background
    ax.set_facecolor("#f5f5f5")

    # Draw AOI bounding box
    aoi_rect = mpatches.Rectangle(
        (min_lon, min_lat),
        max_lon - min_lon,
        max_lat - min_lat,
        linewidth=2,
        edgecolor="#333333",
        facecolor="none",
        label="AOI Boundary"
    )
    ax.add_patch(aoi_rect)

    # Draw tile grid overlay (faint grid lines)
    # Approximate: 1 degree ≈ 111 km at equator
    # tile_size_km converted to degrees (rough approximation)
    tile_size_deg = tile_size_km / 111.0

    lon_grid = np.arange(min_lon, max_lon, tile_size_deg)
    lat_grid = np.arange(min_lat, max_lat, tile_size_deg)

    for lon in lon_grid:
        ax.axvline(lon, color="#cccccc", linewidth=0.5, alpha=0.5)
    for lat in lat_grid:
        ax.axhline(lat, color="#cccccc", linewidth=0.5, alpha=0.5)

    # Plot hotspot markers
    tier_counts = {"Structural": 0, "Activity": 0, "Environmental": 0}
    for hotspot in hotspots:
        centroid = hotspot["centroid"]
        tier = hotspot["confidence_tier"]
        color = TIER_COLORS.get(tier, "#999999")
        tier_counts[tier] += 1

        ax.scatter(
            centroid["lon"],
            centroid["lat"],
            c=color,
            s=100,
            marker="o",
            edgecolors="white",
            linewidths=1.5,
            alpha=0.8,
            zorder=10
        )

    # Legend
    legend_patches = [
        mpatches.Patch(color=TIER_COLORS["Structural"], label=f"Structural ({tier_counts['Structural']})"),
        mpatches.Patch(color=TIER_COLORS["Activity"], label=f"Activity ({tier_counts['Activity']})"),
        mpatches.Patch(color=TIER_COLORS["Environmental"], label=f"Environmental ({tier_counts['Environmental']})"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", framealpha=0.9)

    # Axis labels
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.set_title("AOI Overview with Detected Hotspots", fontsize=14, fontweight="bold")

    # Grid
    ax.grid(True, linestyle="--", alpha=0.3, color="#666666")

    # Tight layout
    plt.tight_layout()

    # Encode to base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    return img_base64


def generate_aoi_map_fallback(error_message: str) -> str:
    """
    Generate minimal fallback map with error message.

    Args:
        error_message: Error message to display

    Returns:
        Base64-encoded PNG image string
    """
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    ax.text(
        0.5, 0.5,
        f"Map Generation Failed\n{error_message}",
        ha="center",
        va="center",
        fontsize=14,
        color="red",
        transform=ax.transAxes
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
