#!/usr/bin/env python3
"""
Smoke test for SIAD report generation.

Creates mock hotspots and generates a minimal HTML report.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from siad.report import build_report


def create_mock_hotspots():
    """Create mock hotspots for testing."""
    hotspots = [
        {
            "hotspot_id": "hotspot_001",
            "aoi_id": "smoke-test",
            "tile_ids": ["tile_x000_y000", "tile_x001_y000", "tile_x000_y001"],
            "centroid": {"lon": 14.05, "lat": 37.55},
            "first_detected_month": "2023-06",
            "persistence_months": 4,
            "confidence_tier": "Structural",
            "max_acceleration_score": 2.73,
            "attribution": {
                "sar_contribution": 0.65,
                "optical_contribution": 0.20,
                "lights_contribution": 0.15,
            },
            "thumbnails": {
                "s1_before": None,
                "s1_after": None,
                "s2_before": None,
                "s2_after": None,
                "viirs_before": None,
                "viirs_after": None,
            },
        },
        {
            "hotspot_id": "hotspot_002",
            "aoi_id": "smoke-test",
            "tile_ids": ["tile_x002_y000", "tile_x003_y000", "tile_x002_y001"],
            "centroid": {"lon": 14.08, "lat": 37.58},
            "first_detected_month": "2023-08",
            "persistence_months": 2,
            "confidence_tier": "Activity",
            "max_acceleration_score": 1.85,
            "attribution": {
                "sar_contribution": 0.15,
                "optical_contribution": 0.25,
                "lights_contribution": 0.60,
            },
            "thumbnails": {
                "s1_before": None,
                "s1_after": None,
                "s2_before": None,
                "s2_after": None,
                "viirs_before": None,
                "viirs_after": None,
            },
        },
    ]

    return hotspots


def create_mock_manifest():
    """Create mock manifest for testing."""
    import yaml

    # Mock manifest rows (just a few)
    manifest_rows = [
        {
            "aoi_id": "smoke-test",
            "tile_id": "tile_x000_y000",
            "month": "2023-01",
            "gcs_uri": "gs://mock/tile.tif",
            "rain_anom": 0.0,
            "temp_anom": 0.0,
            "s2_valid_frac": 0.85,
            "band_order_version": "v1",
            "preprocessing_version": "20260301",
        }
    ]

    manifest_path = Path("/tmp/siad_mock_manifest.jsonl")
    with open(manifest_path, "w") as f:
        for row in manifest_rows:
            f.write(json.dumps(row) + "\n")

    # Mock config
    config = {
        "aoi": {
            "aoi_id": "smoke-test",
            "bounds": {
                "min_lon": 14.0,
                "max_lon": 14.1,
                "min_lat": 37.5,
                "max_lat": 37.6,
            },
        }
    }

    config_path = Path("/tmp/siad_mock_config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return manifest_path, config_path


def test_report_generation():
    """Run smoke test for report generation."""
    print("SIAD Report Generation Smoke Test")
    print("=" * 60)

    # 1. Create mock data
    print("\n[1/4] Creating mock hotspots...")
    hotspots = create_mock_hotspots()
    print(f"  ✓ Created {len(hotspots)} mock hotspots")

    # Write to temp file
    hotspots_path = Path("/tmp/siad_mock_hotspots.json")
    with open(hotspots_path, "w") as f:
        json.dump(hotspots, f, indent=2)
    print(f"  ✓ Wrote hotspots to {hotspots_path}")

    print("\n[2/4] Creating mock manifest and config...")
    manifest_path, config_path = create_mock_manifest()
    print(f"  ✓ Created manifest: {manifest_path}")
    print(f"  ✓ Created config: {config_path}")

    # 3. Generate report
    print("\n[3/4] Generating HTML report...")
    try:
        output_path = Path("/tmp/siad_smoke_report.html")

        # Generate report
        build_report(
            hotspots_json_path=str(hotspots_path),
            manifest_path=str(manifest_path),
            config_path=str(config_path),
            output_html_path=str(output_path),
            skip_timelines=True,  # Skip for speed
        )

        print(f"  ✓ Generated report: {output_path}")

    except Exception as e:
        print(f"  ✗ Report generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 4. Verify output
    print("\n[4/4] Verifying output...")
    if not output_path.exists():
        print("  ✗ Output file not found")
        return False

    # Check file size
    file_size = output_path.stat().st_size
    print(f"  ✓ Output file size: {file_size:,} bytes")

    # Check it's valid HTML (simple check)
    with open(output_path) as f:
        content = f.read()

    if "<html" not in content.lower():
        print("  ✗ Output is not valid HTML")
        return False

    if "hotspot_001" not in content:
        print("  ✗ Hotspot data not found in output")
        return False

    print("  ✓ Output is valid HTML with hotspot data")

    # Cleanup
    hotspots_path.unlink()
    manifest_path.unlink()
    config_path.unlink()
    # Keep output_path for manual inspection

    print("\n" + "=" * 60)
    print(f"✓ SMOKE TEST PASSED")
    print(f"  Report saved to: {output_path}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = test_report_generation()
    sys.exit(0 if success else 1)
