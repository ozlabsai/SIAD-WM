#!/usr/bin/env python3
"""
Compute rainfall and temperature anomalies and inject into manifest.jsonl.

This script:
1. Reads AOI bounds and date range from config YAML
2. Fetches CHIRPS monthly precipitation from Earth Engine
3. Optionally fetches ERA5 monthly temperature from Earth Engine
4. Computes month-of-year z-score anomalies using 3-year baseline
5. Injects anomalies into manifest.jsonl

Usage:
    uv run scripts/compute_anomalies.py \
        --config configs/quickstart-demo.yaml \
        --manifest data/raw/manifest.jsonl \
        --output data/preprocessed/manifest_with_anomalies.jsonl \
        --baseline-years 3 \
        --skip-era5

Arguments:
    --config: Path to AOI config YAML (required)
    --manifest: Path to input manifest.jsonl (required)
    --output: Path to output manifest.jsonl (optional, defaults to overwrite input)
    --baseline-years: Number of years for climatology baseline (default: 3)
    --skip-era5: Skip temperature anomaly computation (optional flag)
    --verbose: Enable verbose logging (optional flag)

Example config YAML (configs/quickstart-demo.yaml):
    aoi:
      aoi_id: "quickstart-demo"
      bounds:
        min_lon: 12.0
        max_lon: 12.5
        min_lat: 34.0
        max_lat: 34.5
    data:
      start_month: "2021-01"
      end_month: "2023-12"
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from siad.actions.chirps_aggregator import aggregate_chirps_monthly
from siad.actions.era5_aggregator import aggregate_era5_monthly
from siad.actions.anomaly_computer import compute_month_of_year_anomalies
from siad.actions.manifest_injector import inject_anomalies_to_manifest, validate_manifest_anomalies


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def load_config(config_path: str) -> dict:
    """Load AOI config from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    parser = argparse.ArgumentParser(
        description="Compute rainfall and temperature anomalies and inject into manifest.jsonl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to AOI config YAML"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to input manifest.jsonl"
    )
    parser.add_argument(
        "--output",
        help="Path to output manifest.jsonl (defaults to overwrite input)"
    )
    parser.add_argument(
        "--baseline-years",
        type=int,
        default=3,
        help="Number of years for climatology baseline (default: 3)"
    )
    parser.add_argument(
        "--skip-era5",
        action="store_true",
        help="Skip temperature anomaly computation"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Load config
        logger.info(f"Loading config from: {args.config}")
        config = load_config(args.config)

        aoi_bounds = config["aoi"]["bounds"]
        start_month = config["data"]["start_month"]
        end_month = config["data"]["end_month"]

        logger.info(f"AOI: {config['aoi']['aoi_id']}")
        logger.info(f"Bounds: {aoi_bounds}")
        logger.info(f"Date range: {start_month} to {end_month}")

        # Initialize Earth Engine
        logger.info("Initializing Earth Engine...")
        import ee
        ee.Initialize()

        # Fetch CHIRPS rainfall
        logger.info("Fetching CHIRPS monthly precipitation...")
        rain_values = aggregate_chirps_monthly(
            aoi_bounds=aoi_bounds,
            start_month=start_month,
            end_month=end_month,
            ee_authenticated=True
        )

        logger.info(f"Fetched CHIRPS for {len(rain_values)} months")
        logger.debug(f"Sample rain values: {dict(list(rain_values.items())[:3])}")

        # Compute rain anomalies
        logger.info(f"Computing rain anomalies (baseline: {args.baseline_years} years)...")
        rain_anomalies = compute_month_of_year_anomalies(
            values=rain_values,
            baseline_years=args.baseline_years
        )

        logger.info(f"Computed rain anomalies for {len(rain_anomalies)} months")
        logger.debug(f"Sample rain anomalies: {dict(list(rain_anomalies.items())[:3])}")

        # Fetch ERA5 temperature (optional)
        temp_anomalies = None

        if not args.skip_era5:
            logger.info("Fetching ERA5 monthly temperature...")
            temp_values = aggregate_era5_monthly(
                aoi_bounds=aoi_bounds,
                start_month=start_month,
                end_month=end_month,
                ee_authenticated=True
            )

            logger.info(f"Fetched ERA5 for {len(temp_values)} months")
            logger.debug(f"Sample temp values: {dict(list(temp_values.items())[:3])}")

            logger.info(f"Computing temp anomalies (baseline: {args.baseline_years} years)...")
            temp_anomalies = compute_month_of_year_anomalies(
                values=temp_values,
                baseline_years=args.baseline_years
            )

            logger.info(f"Computed temp anomalies for {len(temp_anomalies)} months")
            logger.debug(f"Sample temp anomalies: {dict(list(temp_anomalies.items())[:3])}")
        else:
            logger.info("Skipping ERA5 temperature (--skip-era5 flag set)")

        # Inject anomalies into manifest
        logger.info(f"Injecting anomalies into manifest: {args.manifest}")
        output_path = args.output if args.output else args.manifest

        inject_anomalies_to_manifest(
            manifest_path=args.manifest,
            rain_anomalies=rain_anomalies,
            temp_anomalies=temp_anomalies,
            output_path=output_path
        )

        logger.info(f"Successfully wrote updated manifest to: {output_path}")

        # Validate manifest
        logger.info("Validating manifest anomalies...")
        stats = validate_manifest_anomalies(output_path)

        logger.info(f"Manifest validation:")
        logger.info(f"  Total rows: {stats['total_rows']}")
        logger.info(f"  Missing rain_anom: {stats['missing_rain_anom']}")
        logger.info(f"  Missing temp_anom: {stats['missing_temp_anom']}")

        if stats["rain_anom_stats"]:
            logger.info(f"  Rain anomaly stats: {stats['rain_anom_stats']}")

        if stats["temp_anom_stats"]:
            logger.info(f"  Temp anomaly stats: {stats['temp_anom_stats']}")

        logger.info("SUCCESS: Anomaly computation complete")

    except Exception as e:
        logger.error(f"FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
