"""
Timeline Plotter

Generates temporal residual score plots for hotspots showing acceleration over time.
Highlights persistence windows and first detection dates.
"""

import io
import base64
from datetime import datetime
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_timeline_plot(
    hotspot_id: str,
    residuals_timeseries: List[Dict],
    first_detected_month: str,
    persistence_months: int,
    output_size: tuple = (10, 4)
) -> str:
    """
    Generate timeline plot showing residual scores over time.

    Args:
        hotspot_id: Hotspot identifier (for plot title)
        residuals_timeseries: List of dicts with keys {month, residual_score}
                               (aggregated across all tiles in hotspot cluster)
        first_detected_month: ISO 8601 month string (e.g., "2023-06")
        persistence_months: Number of consecutive months above threshold
        output_size: Figure size in inches (width, height)

    Returns:
        Base64-encoded PNG image string

    Example:
        >>> residuals = [
        ...     {"month": "2021-01", "residual_score": 0.12},
        ...     {"month": "2021-02", "residual_score": 0.15},
        ...     ...
        ... ]
        >>> plot_b64 = generate_timeline_plot("hotspot_001", residuals, "2023-06", 3)
    """
    try:
        if not residuals_timeseries:
            logger.warning(f"No residuals data for {hotspot_id}, generating placeholder")
            return _generate_placeholder_timeline(hotspot_id, "No data available")

        # Parse dates and scores
        months = [datetime.strptime(r["month"], "%Y-%m") for r in residuals_timeseries]
        scores = [r["residual_score"] for r in residuals_timeseries]

        # Sort by date
        sorted_pairs = sorted(zip(months, scores), key=lambda x: x[0])
        months, scores = zip(*sorted_pairs) if sorted_pairs else ([], [])

        # Parse first detected month
        first_detected = datetime.strptime(first_detected_month, "%Y-%m")

        # Create figure
        fig, ax = plt.subplots(figsize=output_size, dpi=150)

        # Plot residual scores
        ax.plot(months, scores, linewidth=2, color="#1976D2", label="Residual Score")

        # Highlight persistence window (first_detected to first_detected + persistence_months)
        if persistence_months > 0:
            from dateutil.relativedelta import relativedelta
            persistence_end = first_detected + relativedelta(months=persistence_months)

            # Find y-range for shading
            y_min, y_max = ax.get_ylim()
            ax.axvspan(
                first_detected,
                persistence_end,
                alpha=0.2,
                color="#D32F2F",
                label=f"Persistence Window ({persistence_months}mo)"
            )

        # Mark first detected month (vertical dashed line)
        ax.axvline(
            first_detected,
            linestyle="--",
            linewidth=2,
            color="#D32F2F",
            label="First Detected"
        )

        # Axis labels
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Residual Score", fontsize=12)
        ax.set_title(f"{hotspot_id} - Acceleration Timeline", fontsize=14, fontweight="bold")

        # Grid
        ax.grid(True, linestyle="--", alpha=0.3, which="both")

        # Legend
        ax.legend(loc="upper left", framealpha=0.9)

        # Format x-axis dates
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))  # Show every 6 months
        fig.autofmt_xdate(rotation=45)

        # Tight layout
        plt.tight_layout()

        # Encode to base64
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    except Exception as e:
        logger.error(f"Failed to generate timeline for {hotspot_id}: {e}")
        return _generate_placeholder_timeline(hotspot_id, str(e))


def _generate_placeholder_timeline(hotspot_id: str, message: str) -> str:
    """
    Generate placeholder timeline plot with error message.

    Args:
        hotspot_id: Hotspot identifier
        message: Error message to display

    Returns:
        Base64-encoded PNG image string
    """
    fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
    ax.text(
        0.5, 0.5,
        f"{hotspot_id}\n{message}",
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


def aggregate_residuals_for_hotspot(
    hotspot: Dict,
    residuals_csv_path: str
) -> List[Dict]:
    """
    Aggregate residual scores across all tiles in hotspot cluster.

    Args:
        hotspot: Hotspot dict with tile_ids list
        residuals_csv_path: Path to residuals_timeseries.csv
                            (expected format: tile_id, month, residual_score)

    Returns:
        List of dicts with keys {month, residual_score} (median across tiles)

    Note:
        This is a skeleton implementation. Full implementation requires:
        1. CSV parsing (pandas or csv module)
        2. Filtering by tile_ids in hotspot
        3. Aggregation (median or mean) per month
    """
    # TODO: Implement CSV loading and aggregation
    # For now, return mock data for smoke test
    logger.warning(f"Using mock residuals data for {hotspot['hotspot_id']}")

    # Generate synthetic timeline (36 months)
    from dateutil.relativedelta import relativedelta
    first_detected = datetime.strptime(hotspot["first_detected_month"], "%Y-%m")
    start_month = first_detected - relativedelta(months=18)

    residuals = []
    for i in range(36):
        month = start_month + relativedelta(months=i)
        # Simulate gradual increase starting near first_detected
        if month < first_detected:
            score = 0.05 + np.random.rand() * 0.05
        else:
            score = 0.2 + np.random.rand() * 0.3
        residuals.append({
            "month": month.strftime("%Y-%m"),
            "residual_score": score
        })

    return residuals
