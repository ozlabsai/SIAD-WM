"""
Anomaly computation using month-of-year climatology baselines.

Algorithm:
1. Group values by month-of-year (1-12)
2. For each month M, compute mean and std across all M's in baseline period
3. Z-score for month M in year Y: (value_Y_M - mean_M) / (std_M + epsilon)

Example:
    >>> values = {
    ...     "2021-01": 45.2, "2021-02": 32.8, ...,
    ...     "2022-01": 50.1, "2022-02": 35.3, ...,
    ...     "2023-01": 42.7, "2023-02": 30.5, ...
    ... }
    >>> anomalies = compute_month_of_year_anomalies(values, baseline_years=3)
    >>> anomalies["2023-01"]  # Z-score relative to Jan climatology
    -0.35
"""

from collections import defaultdict
import numpy as np
from typing import Dict, Optional

try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    EE_AVAILABLE = False


def compute_month_of_year_anomalies(
    values: Dict[str, float],
    baseline_years: int = 3,
    epsilon: float = 1e-6
) -> Dict[str, float]:
    """
    Compute z-score anomalies using month-of-year climatology baselines.

    Args:
        values: Dictionary mapping "YYYY-MM" -> value (precipitation in mm or temperature in K)
        baseline_years: Number of years to use for climatology baseline (default: 3)
        epsilon: Small constant to avoid division by zero (default: 1e-6)

    Returns:
        Dictionary mapping "YYYY-MM" -> z-score anomaly

    Raises:
        ValueError: If values dict is empty or contains invalid date strings
    """
    if not values:
        raise ValueError("Values dictionary cannot be empty")

    # Group values by month-of-year (1-12)
    month_groups = defaultdict(list)
    sorted_dates = sorted(values.keys())

    for date_str in sorted_dates:
        try:
            year, month = date_str.split("-")
            month_of_year = int(month)  # 1-12

            if not (1 <= month_of_year <= 12):
                raise ValueError(f"Invalid month in date string: {date_str}")

            month_groups[month_of_year].append((date_str, values[date_str]))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid date string format: {date_str}. Expected 'YYYY-MM'") from e

    # Compute climatology (mean, std) for each month-of-year
    climatology = {}

    for month_of_year in range(1, 13):
        if month_of_year not in month_groups:
            # No data for this month-of-year (cold-start or sparse data)
            climatology[month_of_year] = {"mean": 0.0, "std": 1.0}
            continue

        month_data = month_groups[month_of_year]

        # Use last N years for baseline (rolling window)
        if len(month_data) > baseline_years:
            month_data = month_data[-baseline_years:]

        month_values = [val for _, val in month_data]

        if len(month_values) == 0:
            # No samples for this month (should not happen, but handle gracefully)
            climatology[month_of_year] = {"mean": 0.0, "std": 1.0}
        elif len(month_values) == 1:
            # Single sample: use value as mean, std = 1.0 (anomaly = 0)
            climatology[month_of_year] = {
                "mean": month_values[0],
                "std": 1.0
            }
        else:
            # Normal case: compute mean and std
            mean_val = float(np.mean(month_values))
            std_val = float(np.std(month_values))

            # Add epsilon to avoid division by zero
            if std_val < epsilon:
                std_val = epsilon

            climatology[month_of_year] = {
                "mean": mean_val,
                "std": std_val
            }

    # Compute z-scores
    anomalies = {}

    for date_str in sorted_dates:
        year, month = date_str.split("-")
        month_of_year = int(month)

        value = values[date_str]
        mean = climatology[month_of_year]["mean"]
        std = climatology[month_of_year]["std"]

        z_score = (value - mean) / std
        anomalies[date_str] = float(z_score)

    return anomalies


def get_climatology_stats(
    values: Dict[str, float],
    baseline_years: int = 3,
    epsilon: float = 1e-6
) -> Dict[int, Dict[str, float]]:
    """
    Get climatology statistics (mean, std) for each month-of-year.

    Useful for debugging and validation.

    Args:
        values: Dictionary mapping "YYYY-MM" -> value
        baseline_years: Number of years to use for climatology baseline
        epsilon: Small constant added to std to avoid division by zero

    Returns:
        Dictionary mapping month-of-year (1-12) -> {"mean": float, "std": float}
    """
    # Re-use logic from compute_month_of_year_anomalies
    # This is a helper function for inspection/debugging
    month_groups = defaultdict(list)
    sorted_dates = sorted(values.keys())

    for date_str in sorted_dates:
        year, month = date_str.split("-")
        month_of_year = int(month)
        month_groups[month_of_year].append(values[date_str])

    climatology = {}

    for month_of_year in range(1, 13):
        if month_of_year not in month_groups:
            climatology[month_of_year] = {"mean": 0.0, "std": 1.0}
            continue

        month_values = month_groups[month_of_year]

        if len(month_values) > baseline_years:
            month_values = month_values[-baseline_years:]

        if len(month_values) == 0:
            climatology[month_of_year] = {"mean": 0.0, "std": 1.0}
        elif len(month_values) == 1:
            climatology[month_of_year] = {
                "mean": month_values[0],
                "std": 1.0
            }
        else:
            mean_val = float(np.mean(month_values))
            std_val = float(np.std(month_values))

            if std_val < epsilon:
                std_val = epsilon

            climatology[month_of_year] = {
                "mean": mean_val,
                "std": std_val
            }

    return climatology


def compute_rain_anomaly(
    chirps_image,
    month: str,
    tile_geometry,
    baseline_years: int = 3
) -> float:
    """
    Compute rainfall anomaly for a given month using CHIRPS data.

    This is a simplified version for testing - computes deviation from
    a simple mean rather than full climatology.

    Args:
        chirps_image: CHIRPS ee.Image with precipitation data
        month: Month string in "YYYY-MM" format
        tile_geometry: Tile geometry for spatial reduction
        baseline_years: Number of baseline years (placeholder)

    Returns:
        float: Rainfall anomaly z-score (simplified)
    """
    if not EE_AVAILABLE:
        raise ImportError("Earth Engine not available")

    # For MVP/testing: compute mean precipitation over tile
    # In production, this would compare against historical climatology
    stats = chirps_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=tile_geometry,
        scale=5000,  # 5km for CHIRPS
        maxPixels=1e9
    ).getInfo()

    precip_mm = stats.get('precipitation', 0.0)

    # Simplified anomaly: (value - historical_mean) / historical_std
    # For testing, use dummy baseline values
    # June-August baseline mean: ~50mm, std: ~20mm (example values)
    historical_mean = 50.0
    historical_std = 20.0

    z_score = (precip_mm - historical_mean) / historical_std

    return float(z_score)
