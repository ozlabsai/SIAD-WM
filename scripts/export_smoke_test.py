#!/usr/bin/env python3
"""
Smoke test for Data/GEE Pipeline.

Tests:
- EE authentication
- Tile grid generation (1 tile × 2 months)
- S1/S2/VIIRS collection
- Band stacking per BAND_ORDER_V1
- GCS export (dry-run mode)
- Manifest generation

Usage:
    uv run python scripts/export_smoke_test.py --dry-run
    uv run python scripts/export_smoke_test.py  # Live export
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import ee
from siad.data.collectors.ee_auth import authenticate_ee, test_ee_connection
from siad.data.collectors.sentinel1_collector import Sentinel1Collector
from siad.data.collectors.sentinel2_collector import Sentinel2Collector
from siad.data.preprocessing.tiling import generate_tile_grid
from siad.data.preprocessing.reprojection import reproject_and_stack, BAND_ORDER_V1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('logs/smoke_test.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)


def smoke_test_config():
    """
    Smoke test configuration.

    Returns:
        dict: Test config
    """
    return {
        'aoi_id': 'smoke-test',
        'aoi_bounds': {
            # Small AOI: 10×10 km in Sicily (low cloud, good data availability)
            'min_lon': 14.0,
            'max_lon': 14.1,
            'min_lat': 37.5,
            'max_lat': 37.6
        },
        'months': ['2023-01', '2023-02'],  # 2 months only
        'gcs_bucket': 'siad-smoke-test',
        'max_tiles': 4,  # Limit to 4 tiles for speed
        'resolution_m': 10,
        'tile_size_px': 256
    }


def test_ee_authentication():
    """Test 1: EE authentication."""
    logger.info("=" * 60)
    logger.info("TEST 1: Earth Engine Authentication")
    logger.info("=" * 60)

    try:
        authenticate_ee()
        assert test_ee_connection(), "EE connection test failed"
        logger.info("✓ EE authentication successful")
        return True
    except Exception as e:
        logger.error(f"✗ EE authentication failed: {e}")
        return False


def test_tile_grid_generation(config):
    """Test 2: Tile grid generation."""
    logger.info("=" * 60)
    logger.info("TEST 2: Tile Grid Generation")
    logger.info("=" * 60)

    try:
        tiles = generate_tile_grid(
            config['aoi_bounds'],
            tile_size_px=config['tile_size_px'],
            resolution_m=config['resolution_m']
        )

        logger.info(f"Generated {len(tiles)} tiles")

        # Limit to max_tiles for smoke test
        tiles = tiles[:config['max_tiles']]
        logger.info(f"Limited to {len(tiles)} tiles for smoke test")

        # Validate tile properties
        for tile in tiles:
            assert tile.tile_id.startswith('tile_'), f"Invalid tile ID: {tile.tile_id}"
            assert len(tile.bounds) == 4, f"Invalid bounds: {tile.bounds}"
            assert tile.geometry is not None, "Missing geometry"

        logger.info(f"✓ Generated {len(tiles)} valid tiles")
        return tiles

    except Exception as e:
        logger.error(f"✗ Tile grid generation failed: {e}")
        return None


def test_data_collection(config, tiles):
    """Test 3: S1/S2/VIIRS collection."""
    logger.info("=" * 60)
    logger.info("TEST 3: Data Collection (S1/S2)")
    logger.info("=" * 60)

    try:
        # Initialize collectors
        s1_collector = Sentinel1Collector()
        s2_collector = Sentinel2Collector()

        # Test first tile, first month
        tile = tiles[0]
        month = config['months'][0]
        start_date = f"{month}-01"
        end_date = f"{month}-28"

        logger.info(f"Testing tile {tile.tile_id} for {month}")

        # Validate S1
        s1_valid = s1_collector.validate(tile.geometry, start_date, end_date)
        logger.info(f"S1 validation: {s1_valid}")
        assert s1_valid['available'], "S1 data not available"

        # Validate S2
        s2_valid = s2_collector.validate(tile.geometry, start_date, end_date)
        logger.info(f"S2 validation: {s2_valid}")
        assert s2_valid['available'], "S2 data not available"

        # Collect S1
        s1_image = s1_collector.collect(tile.geometry, start_date, end_date)
        assert s1_image is not None, "S1 collection returned None"

        # Collect S2
        s2_image = s2_collector.collect(tile.geometry, start_date, end_date)
        assert s2_image is not None, "S2 collection returned None"

        # Create dummy VIIRS (use constant for smoke test)
        viirs_image = ee.Image.constant(0.5).rename('avg_rad')

        logger.info("✓ Data collection successful")
        return s1_image, s2_image, viirs_image

    except Exception as e:
        logger.error(f"✗ Data collection failed: {e}")
        return None, None, None


def test_band_stacking(s1_image, s2_image, viirs_image, tile):
    """Test 4: Band stacking per BAND_ORDER_V1."""
    logger.info("=" * 60)
    logger.info("TEST 4: Band Stacking (BAND_ORDER_V1)")
    logger.info("=" * 60)

    try:
        # Reproject and stack
        stacked = reproject_and_stack(
            s1_image, s2_image, viirs_image,
            tile.geometry
        )

        # Validate band names
        band_names = stacked.bandNames().getInfo()
        logger.info(f"Band names: {band_names}")

        assert band_names == BAND_ORDER_V1, \
            f"Band order mismatch! Expected {BAND_ORDER_V1}, got {band_names}"

        logger.info("✓ Band stacking successful")
        return stacked

    except Exception as e:
        logger.error(f"✗ Band stacking failed: {e}")
        return None


def test_export_dry_run(stacked_image, tile, month, config, dry_run=True):
    """Test 5: GCS export (dry-run or live)."""
    logger.info("=" * 60)
    logger.info(f"TEST 5: GCS Export ({'DRY-RUN' if dry_run else 'LIVE'})")
    logger.info("=" * 60)

    try:
        # Export configuration
        export_config = {
            'image': stacked_image,
            'description': f"{config['aoi_id']}_{tile.tile_id}_{month}",
            'bucket': config['gcs_bucket'],
            'fileNamePrefix': f"siad/{config['aoi_id']}/{tile.tile_id}/{month}",
            'region': tile.geometry,
            'scale': config['resolution_m'],
            'crs': 'EPSG:3857',
            'maxPixels': 1e9,
            'fileFormat': 'GeoTIFF',
            'formatOptions': {'cloudOptimized': True}
        }

        if dry_run:
            logger.info("DRY-RUN: Export configuration:")
            logger.info(json.dumps({k: str(v) for k, v in export_config.items()}, indent=2))
            logger.info("✓ Export dry-run successful")
            return True
        else:
            # Live export
            task = ee.batch.Export.image.toCloudStorage(**export_config)
            task.start()

            logger.info(f"Started export task: {task.id}")
            logger.info(f"Status: {task.status()}")
            logger.info("✓ Export started (check EE task manager)")
            return task

    except Exception as e:
        logger.error(f"✗ Export failed: {e}")
        return None


def test_manifest_generation(config, tiles, dry_run=True):
    """Test 6: Manifest generation."""
    logger.info("=" * 60)
    logger.info("TEST 6: Manifest Generation")
    logger.info("=" * 60)

    try:
        manifest_rows = []

        for tile in tiles:
            for month in config['months']:
                # Create manifest row
                row = {
                    'aoi_id': config['aoi_id'],
                    'tile_id': tile.tile_id,
                    'month': month,
                    'gcs_uri': f"gs://{config['gcs_bucket']}/siad/{config['aoi_id']}/{tile.tile_id}/{month}.tif",
                    'rain_anom': 0.0,  # Placeholder
                    'temp_anom': None,
                    's2_valid_frac': 0.85,  # Placeholder
                    'band_order_version': 'v1',
                    'preprocessing_version': '20260301'
                }

                manifest_rows.append(row)

        logger.info(f"Generated {len(manifest_rows)} manifest rows")

        if dry_run:
            logger.info("Sample manifest rows:")
            for row in manifest_rows[:2]:
                logger.info(json.dumps(row, indent=2))
        else:
            # Write to file
            output_path = Path('data/outputs') / config['aoi_id'] / 'manifest.jsonl'
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                for row in manifest_rows:
                    f.write(json.dumps(row) + '\n')

            logger.info(f"Wrote manifest to {output_path}")

        logger.info("✓ Manifest generation successful")
        return manifest_rows

    except Exception as e:
        logger.error(f"✗ Manifest generation failed: {e}")
        return None


def run_smoke_test(dry_run=True):
    """
    Run full smoke test pipeline.

    Args:
        dry_run: If True, don't actually export to GCS

    Returns:
        bool: True if all tests pass
    """
    logger.info("=" * 60)
    logger.info("SIAD Data/GEE Pipeline - Smoke Test")
    logger.info(f"Mode: {'DRY-RUN' if dry_run else 'LIVE EXPORT'}")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Load config
    config = smoke_test_config()

    # Test 1: EE auth
    if not test_ee_authentication():
        return False

    # Test 2: Tile grid
    tiles = test_tile_grid_generation(config)
    if tiles is None:
        return False

    # Test 3: Data collection
    s1, s2, viirs = test_data_collection(config, tiles)
    if s1 is None or s2 is None or viirs is None:
        return False

    # Test 4: Band stacking
    stacked = test_band_stacking(s1, s2, viirs, tiles[0])
    if stacked is None:
        return False

    # Test 5: Export
    export_result = test_export_dry_run(stacked, tiles[0], config['months'][0], config, dry_run)
    if export_result is None:
        return False

    # Test 6: Manifest
    manifest = test_manifest_generation(config, tiles, dry_run)
    if manifest is None:
        return False

    # Summary
    logger.info("=" * 60)
    logger.info("SMOKE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("✓ All tests passed!")
    logger.info(f"Total tiles: {len(tiles)}")
    logger.info(f"Total months: {len(config['months'])}")
    logger.info(f"Total exports: {len(tiles) * len(config['months'])}")
    logger.info(f"Band order: {BAND_ORDER_V1}")
    logger.info("=" * 60)

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='SIAD Data/GEE Pipeline Smoke Test')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry-run mode (no actual GCS exports)'
    )
    args = parser.parse_args()

    # Create logs directory
    Path('logs').mkdir(exist_ok=True)

    # Run smoke test
    success = run_smoke_test(dry_run=args.dry_run)

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
