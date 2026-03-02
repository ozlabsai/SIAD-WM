"""
Smoke test for Reporting/UI Agent

Tests report generation with a single mock hotspot to verify:
- Template rendering works
- Base64 encoding succeeds
- HTML file size is reasonable
- All expected sections present
"""

import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from siad.report import build_report


def create_mock_hotspot():
    """Create minimal mock hotspot for testing."""
    return {
        "hotspot_id": "hotspot_001",
        "aoi_id": "test-aoi",
        "tile_ids": ["tile_x000_y000", "tile_x001_y000", "tile_x000_y001"],
        "centroid": {"lon": 12.25, "lat": 34.25},
        "first_detected_month": "2023-06",
        "persistence_months": 3,
        "confidence_tier": "Structural",
        "max_acceleration_score": 0.87,
        "attribution": {
            "sar_contribution": 0.6,
            "optical_contribution": 0.25,
            "lights_contribution": 0.15
        }
    }


def create_mock_manifest():
    """Create minimal mock manifest with 2 timesteps."""
    return {
        ("tile_x000_y000", "2022-12"): "gs://mock/2022-12.tif",
        ("tile_x000_y000", "2023-09"): "gs://mock/2023-09.tif",
    }


def create_mock_config():
    """Create minimal mock AOI config."""
    return {
        "aoi": {
            "aoi_id": "test-aoi",
            "bounds": {
                "min_lon": 12.0,
                "max_lon": 12.5,
                "min_lat": 34.0,
                "max_lat": 34.5
            }
        },
        "data": {
            "start_month": "2021-01",
            "end_month": "2023-12"
        }
    }


def test_report_generation():
    """Smoke test: Generate report for single mock hotspot."""
    print("Running smoke test: report generation with mock hotspot...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create mock input files
        hotspots_path = tmpdir / "hotspots.json"
        manifest_path = tmpdir / "manifest.jsonl"
        config_path = tmpdir / "config.yaml"
        output_path = tmpdir / "report.html"

        # Write hotspots.json
        hotspots_path.write_text(json.dumps([create_mock_hotspot()]))

        # Write manifest.jsonl
        manifest_entries = []
        for (tile_id, month), gcs_uri in create_mock_manifest().items():
            manifest_entries.append(json.dumps({
                "tile_id": tile_id,
                "month": month,
                "gcs_uri": gcs_uri,
                "rain_anom": 0.0,
                "temp_anom": 0.0,
                "s2_valid_frac": 0.9,
                "band_order_version": "v1",
                "preprocessing_version": "20260301"
            }))
        manifest_path.write_text("\n".join(manifest_entries))

        # Write config.yaml
        import yaml
        config_path.write_text(yaml.dump(create_mock_config()))

        # Generate report (skip timelines for smoke test)
        try:
            build_report(
                hotspots_json_path=str(hotspots_path),
                manifest_path=str(manifest_path),
                config_path=str(config_path),
                output_html_path=str(output_path),
                scenarios=["neutral"],
                skip_timelines=True,
                residuals_csv_path=None
            )
        except Exception as e:
            print(f"FAIL: Report generation raised exception: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Validate output
        if not output_path.exists():
            print("FAIL: Output HTML file not created")
            return False

        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"  Generated report size: {file_size_mb:.2f} MB")

        if file_size_mb > 10:
            print(f"WARN: Report size exceeds 10 MB (actual: {file_size_mb:.2f} MB)")

        # Validate HTML content
        html_content = output_path.read_text()

        required_sections = [
            "SIAD Infrastructure Acceleration Report",
            "Executive Summary",
            "Area of Interest Overview",
            "Detected Hotspots",
            "hotspot_001",
            "Structural"
        ]

        for section in required_sections:
            if section not in html_content:
                print(f"FAIL: Missing required section: {section}")
                return False

        print("PASS: All validations passed")
        print(f"  - Report contains {len(required_sections)} required sections")
        print(f"  - File size: {file_size_mb:.2f} MB")
        return True


if __name__ == "__main__":
    success = test_report_generation()
    sys.exit(0 if success else 1)
