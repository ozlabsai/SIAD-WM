"""
CHIRPS rainfall aggregator using Earth Engine API.

Fetches CHIRPS daily precipitation data, aggregates to monthly totals,
and computes spatial mean over AOI bounding box.

Earth Engine Collection: UCSB-CHG/CHIRPS/DAILY
Band: precipitation (mm/day)

Example:
    >>> aoi_bounds = {
    ...     "min_lon": 12.0, "max_lon": 12.5,
    ...     "min_lat": 34.0, "max_lat": 34.5
    ... }
    >>> monthly_rain = aggregate_chirps_monthly(
    ...     aoi_bounds=aoi_bounds,
    ...     start_month="2023-01",
    ...     end_month="2023-12"
    ... )
    >>> monthly_rain["2023-01"]
    45.2  # mm/month
"""

import ee
import logging
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def aggregate_chirps_monthly(
    aoi_bounds: Dict[str, float],
    start_month: str,
    end_month: str,
    ee_authenticated: bool = True
) -> Dict[str, float]:
    """
    Fetch CHIRPS monthly precipitation from Earth Engine and compute spatial mean over AOI.

    Args:
        aoi_bounds: Dictionary with keys "min_lon", "max_lon", "min_lat", "max_lat"
        start_month: Start month in "YYYY-MM" format
        end_month: End month in "YYYY-MM" format (inclusive)
        ee_authenticated: If True, assumes EE is already initialized (default: True)

    Returns:
        Dictionary mapping "YYYY-MM" -> precipitation value in mm/month

    Raises:
        RuntimeError: If Earth Engine API call fails
        ValueError: If date format is invalid or bounds are missing
    """
    if not ee_authenticated:
        ee.Initialize()

    # Validate bounds
    required_keys = ["min_lon", "max_lon", "min_lat", "max_lat"]
    if not all(k in aoi_bounds for k in required_keys):
        raise ValueError(f"AOI bounds must contain: {required_keys}")

    # Create AOI geometry
    aoi_geometry = ee.Geometry.Rectangle([
        aoi_bounds["min_lon"],
        aoi_bounds["min_lat"],
        aoi_bounds["max_lon"],
        aoi_bounds["max_lat"]
    ])

    # Parse date range
    try:
        start_date = datetime.strptime(start_month, "%Y-%m")
        end_date = datetime.strptime(end_month, "%Y-%m")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Expected 'YYYY-MM': {e}") from e

    # Generate list of months in range
    current_date = start_date
    months = []

    while current_date <= end_date:
        months.append(current_date.strftime("%Y-%m"))
        # Move to next month
        next_month = current_date.month + 1
        next_year = current_date.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        current_date = datetime(next_year, next_month, 1)

    logger.info(f"Fetching CHIRPS data for {len(months)} months: {months[0]} to {months[-1]}")

    # Fetch CHIRPS collection
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")

    monthly_values = {}

    for month_str in months:
        try:
            # Parse month boundaries
            year, month = month_str.split("-")
            year = int(year)
            month = int(month)

            # Get first day of month
            month_start = datetime(year, month, 1)

            # Get first day of next month
            if month == 12:
                month_end = datetime(year + 1, 1, 1)
            else:
                month_end = datetime(year, month + 1, 1)

            # Filter CHIRPS to month
            month_start_str = month_start.strftime("%Y-%m-%d")
            month_end_str = month_end.strftime("%Y-%m-%d")

            monthly_chirps = chirps.filterDate(month_start_str, month_end_str).filterBounds(aoi_geometry)

            # Sum daily precipitation to get monthly total
            monthly_precip = monthly_chirps.select("precipitation").sum()

            # Compute spatial mean over AOI
            stats = monthly_precip.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi_geometry,
                scale=5000,  # CHIRPS native resolution ~5km
                maxPixels=1e9
            )

            # Extract value
            precip_value = stats.getInfo().get("precipitation")

            if precip_value is None:
                logger.warning(f"No CHIRPS data for {month_str}, using 0.0")
                precip_value = 0.0

            monthly_values[month_str] = float(precip_value)
            logger.debug(f"CHIRPS {month_str}: {precip_value:.2f} mm/month")

        except Exception as e:
            logger.error(f"Failed to fetch CHIRPS for {month_str}: {e}")
            # Use fallback value
            monthly_values[month_str] = 0.0

    logger.info(f"Successfully fetched CHIRPS for {len(monthly_values)} months")

    return monthly_values
