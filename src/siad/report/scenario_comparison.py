"""
Scenario Comparison Generator

Generates side-by-side heatmaps comparing acceleration scores across counterfactual scenarios
(e.g., neutral weather vs observed conditions).
"""

import io
import base64
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_scenario_comparison(
    aoi_id: str,
    scenarios: List[str],
    scores_dir: str,
    aoi_bounds: Dict[str, float],
    output_size: tuple = (12, 6)
) -> List[Dict[str, str]]:
    """
    Generate scenario comparison heatmaps.

    Args:
        aoi_id: AOI identifier
        scenarios: List of scenario names (e.g., ["neutral", "observed"])
        scores_dir: Directory containing score GeoTIFFs
                    (expected format: scores_{scenario}_{month}.tif)
        aoi_bounds: Dict with keys {min_lon, max_lon, min_lat, max_lat}
        output_size: Figure size in inches (width, height) per scenario

    Returns:
        List of dicts with keys:
            - name: Scenario name
            - heatmap_b64: Base64-encoded PNG heatmap

    Note:
        This is a skeleton implementation. Full implementation requires:
        1. rasterio to load score GeoTIFFs
        2. Temporal aggregation (max or 90th percentile across months)
        3. Spatial resampling to common grid
    """
    comparison = []

    for scenario in scenarios:
        try:
            logger.info(f"Generating heatmap for scenario: {scenario}")

            # TODO: Load score GeoTIFFs for this scenario
            # score_files = glob.glob(f"{scores_dir}/scores_{scenario}_*.tif")
            # with rasterio.open(score_files[0]) as src:
            #     scores = src.read(1)  # Read first band
            #     ...

            # SKELETON: Generate mock heatmap (random noise for now)
            heatmap_b64 = _generate_mock_heatmap(scenario, aoi_bounds, output_size)

            comparison.append({
                "name": scenario.capitalize(),
                "heatmap_b64": heatmap_b64
            })

        except Exception as e:
            logger.error(f"Failed to generate heatmap for {scenario}: {e}")
            comparison.append({
                "name": scenario.capitalize(),
                "heatmap_b64": _generate_placeholder_heatmap(scenario, str(e))
            })

    return comparison


def _generate_mock_heatmap(
    scenario: str,
    aoi_bounds: Dict[str, float],
    output_size: tuple
) -> str:
    """
    Generate mock heatmap for smoke testing.

    Args:
        scenario: Scenario name
        aoi_bounds: AOI bounds dict
        output_size: Figure size in inches

    Returns:
        Base64-encoded PNG image string
    """
    # Create synthetic heatmap (random noise with spatial correlation)
    rng = np.random.RandomState(hash(scenario) % 2**32)
    H, W = 100, 100

    # Generate spatially smooth noise (simulate acceleration scores)
    from scipy.ndimage import gaussian_filter
    noise = rng.rand(H, W)
    smooth_noise = gaussian_filter(noise, sigma=3)

    # Scale to [0, 1] range
    scores = (smooth_noise - smooth_noise.min()) / (smooth_noise.max() - smooth_noise.min())

    # Create figure
    fig, ax = plt.subplots(figsize=output_size, dpi=150)

    # Plot heatmap
    im = ax.imshow(
        scores,
        cmap="hot",
        interpolation="bilinear",
        origin="lower",
        extent=[
            aoi_bounds["min_lon"],
            aoi_bounds["max_lon"],
            aoi_bounds["min_lat"],
            aoi_bounds["max_lat"]
        ]
    )

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Acceleration Score", fontsize=12)

    # Axis labels
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.set_title(f"{scenario.capitalize()} Scenario - Acceleration Heatmap", fontsize=14, fontweight="bold")

    # Grid
    ax.grid(True, linestyle="--", alpha=0.3, color="white")

    # Tight layout
    plt.tight_layout()

    # Encode to base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _generate_placeholder_heatmap(scenario: str, message: str) -> str:
    """
    Generate placeholder heatmap with error message.

    Args:
        scenario: Scenario name
        message: Error message to display

    Returns:
        Base64-encoded PNG image string
    """
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    ax.text(
        0.5, 0.5,
        f"{scenario.capitalize()} Scenario\n{message}",
        ha="center",
        va="center",
        fontsize=12,
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
