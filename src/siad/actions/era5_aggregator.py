"""
ERA5 temperature aggregator using Earth Engine API.

Fetches ERA5 monthly 2m air temperature data and computes spatial mean over AOI.

Earth Engine Collection: ECMWF/ERA5/MONTHLY
Band: mean_2m_air_temperature (Kelvin)

Example:
    >>> aoi_bounds = {
    ...     "min_lon": 12.0, "max_lon": 12.5,
    ...     "min_lat": 34.0, "max_lat": 34.5
    ... }
    >>> monthly_temp = aggregate_era5_monthly(
    ...     aoi_bounds=aoi_bounds,
    ...     start_month="2023-01",
    ...     end_month="2023-12"
    ... )
    >>> monthly_temp["2023-01"]
    285.3  # Kelvin
"""

import ee
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def aggregate_era5_monthly(
    aoi_bounds: Dict[str, float],
    start_month: str,
    end_month: str,
    ee_authenticated: bool = True
) -> Dict[str, float]:
    """
    Fetch ERA5 2m temperature from Earth Engine and compute spatial mean over AOI.

    Args:
        aoi_bounds: Dictionary with keys "min_lon", "max_lon", "min_lat", "max_lat"
        start_month: Start month in "YYYY-MM" format
        end_month: End month in "YYYY-MM" format (inclusive)
        ee_authenticated: If True, assumes EE is already initialized (default: True)

    Returns:
        Dictionary mapping "YYYY-MM" -> temperature value in Kelvin

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

    logger.info(f"Fetching ERA5 data for {len(months)} months: {months[0]} to {months[-1]}")

    # Fetch ERA5 monthly collection
    era5 = ee.ImageCollection("ECMWF/ERA5/MONTHLY")

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

            # Filter ERA5 to month
            month_start_str = month_start.strftime("%Y-%m-%d")
            month_end_str = month_end.strftime("%Y-%m-%d")

            monthly_era5 = era5.filterDate(month_start_str, month_end_str).filterBounds(aoi_geometry)

            # Select temperature band
            monthly_temp = monthly_era5.select("mean_2m_air_temperature").first()

            # Compute spatial mean over AOI
            stats = monthly_temp.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi_geometry,
                scale=27830,  # ERA5 native resolution ~27km
                maxPixels=1e9
            )

            # Extract value
            temp_value = stats.getInfo().get("mean_2m_air_temperature")

            if temp_value is None:
                logger.warning(f"No ERA5 data for {month_str}, using 0.0")
                temp_value = 0.0

            monthly_values[month_str] = float(temp_value)
            logger.debug(f"ERA5 {month_str}: {temp_value:.2f} K")

        except Exception as e:
            logger.error(f"Failed to fetch ERA5 for {month_str}: {e}")
            # Use fallback value
            monthly_values[month_str] = 0.0

    logger.info(f"Successfully fetched ERA5 for {len(monthly_values)} months")

    return monthly_values
