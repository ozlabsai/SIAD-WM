"""
Smoke test for anomaly computation module.

Tests:
1. Compute month-of-year anomalies with synthetic seasonal data
2. Verify anomalies are centered at 0.0 (mean ≈ 0)
3. Verify seasonal pattern is removed
4. Verify z-scores are in reasonable range [-3, +3]
5. Verify manifest injection works correctly

Runtime: < 5 seconds (no Earth Engine calls)
"""

try:
    import pytest
except ImportError:
    pytest = None  # pytest not available, tests can still run standalone

import numpy as np
import json
import tempfile
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from siad.actions.anomaly_computer import compute_month_of_year_anomalies, get_climatology_stats
from siad.actions.manifest_injector import inject_anomalies_to_manifest, validate_manifest_anomalies


class TestAnomalyComputation:
    """Test suite for anomaly computation logic."""

    def test_seasonal_pattern_removal(self):
        """Test that month-of-year anomalies remove seasonal patterns."""
        # Create synthetic data: 3 years with strong seasonal pattern
        # High in summer (June-Aug), low in winter (Dec-Feb)
        np.random.seed(42)

        values = {}
        for year in [2021, 2022, 2023]:
            for month in range(1, 13):
                date_str = f"{year}-{month:02d}"
                # Seasonal pattern: sin wave with 12-month period
                seasonal_value = 50 + 30 * np.sin(2 * np.pi * (month - 1) / 12)
                # Add small noise
                noise = np.random.normal(0, 5)
                values[date_str] = seasonal_value + noise

        # Compute anomalies
        anomalies = compute_month_of_year_anomalies(values, baseline_years=3)

        # Verify: mean ≈ 0, std ≈ 1
        anom_values = list(anomalies.values())
        mean_anom = np.mean(anom_values)
        std_anom = np.std(anom_values)

        assert abs(mean_anom) < 0.3, f"Anomalies should be centered at 0, got {mean_anom}"
        assert 0.7 < std_anom < 1.3, f"Anomalies should have std ≈ 1, got {std_anom}"

        # Verify: all anomalies in reasonable range
        assert all(-3 <= a <= 3 for a in anom_values), "Anomalies should be in [-3, +3]"

    def test_cold_start_handling(self):
        """Test anomaly computation with < 3 years baseline (cold-start)."""
        # Single year of data
        values = {}
        for month in range(1, 13):
            date_str = f"2023-{month:02d}"
            values[date_str] = 50.0 + 10.0 * month  # Linear trend

        # Compute anomalies with 3-year baseline (but only 1 year available)
        anomalies = compute_month_of_year_anomalies(values, baseline_years=3)

        # Verify: anomalies computed (all should be 0.0 since single sample per month)
        assert len(anomalies) == 12
        # With single sample per month, std = 1.0, so anomaly = 0.0
        anom_values = list(anomalies.values())
        assert all(a == 0.0 for a in anom_values), "Single sample should produce zero anomalies"

    def test_zero_variance_handling(self):
        """Test anomaly computation with zero variance (identical values)."""
        # All months have same value (e.g., desert with 0 rainfall)
        values = {}
        for year in [2021, 2022, 2023]:
            for month in range(1, 13):
                date_str = f"{year}-{month:02d}"
                values[date_str] = 0.0  # Zero rainfall every month

        # Compute anomalies
        anomalies = compute_month_of_year_anomalies(values, baseline_years=3, epsilon=1e-6)

        # Verify: anomalies are 0.0 (since all values are identical)
        anom_values = list(anomalies.values())
        assert all(abs(a) < 0.01 for a in anom_values), "Zero variance should produce near-zero anomalies"

    def test_climatology_stats(self):
        """Test climatology statistics computation."""
        # Create data with known mean/std per month
        values = {}
        for year in [2021, 2022, 2023]:
            for month in range(1, 13):
                date_str = f"{year}-{month:02d}"
                # Each month has different mean (10, 20, 30, ...)
                values[date_str] = 10.0 * month + np.random.normal(0, 1)

        # Get climatology
        climatology = get_climatology_stats(values, baseline_years=3)

        # Verify: 12 months
        assert len(climatology) == 12

        # Verify: January mean ≈ 10, February mean ≈ 20, etc.
        for month in range(1, 13):
            expected_mean = 10.0 * month
            actual_mean = climatology[month]["mean"]
            assert abs(actual_mean - expected_mean) < 5.0, f"Month {month} mean should be ≈ {expected_mean}"


class TestManifestInjection:
    """Test suite for manifest injection logic."""

    def test_manifest_injection_basic(self):
        """Test basic manifest injection with rain and temp anomalies."""
        # Create temporary manifest
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            manifest_path = f.name

            # Write sample manifest rows
            for month in ["2023-01", "2023-02", "2023-03"]:
                row = {
                    "aoi_id": "test-aoi",
                    "tile_id": "tile_x000_y000",
                    "month": month,
                    "gcs_uri": f"gs://test/{month}.tif",
                    "rain_anom": 0.0,
                    "temp_anom": 0.0
                }
                f.write(json.dumps(row) + '\n')

        try:
            # Inject anomalies
            rain_anomalies = {
                "2023-01": -0.35,
                "2023-02": 0.12,
                "2023-03": 0.48
            }
            temp_anomalies = {
                "2023-01": 0.08,
                "2023-02": -0.15,
                "2023-03": 0.22
            }

            inject_anomalies_to_manifest(
                manifest_path=manifest_path,
                rain_anomalies=rain_anomalies,
                temp_anomalies=temp_anomalies,
                output_path=None  # Overwrite in-place
            )

            # Verify injected values
            with open(manifest_path, 'r') as f:
                rows = [json.loads(line) for line in f]

            assert len(rows) == 3

            for row in rows:
                month = row["month"]
                assert row["rain_anom"] == rain_anomalies[month]
                assert row["temp_anom"] == temp_anomalies[month]

        finally:
            # Cleanup
            os.unlink(manifest_path)

    def test_manifest_validation(self):
        """Test manifest validation statistics."""
        # Create temporary manifest with known anomalies
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            manifest_path = f.name

            for i, month in enumerate(["2023-01", "2023-02", "2023-03"]):
                row = {
                    "aoi_id": "test-aoi",
                    "tile_id": "tile_x000_y000",
                    "month": month,
                    "gcs_uri": f"gs://test/{month}.tif",
                    "rain_anom": float(i - 1),  # -1, 0, 1
                    "temp_anom": float(i * 0.5)  # 0, 0.5, 1.0
                }
                f.write(json.dumps(row) + '\n')

        try:
            # Validate manifest
            stats = validate_manifest_anomalies(manifest_path)

            assert stats["total_rows"] == 3
            assert stats["missing_rain_anom"] == 0
            assert stats["missing_temp_anom"] == 0

            # Verify rain stats
            assert stats["rain_anom_stats"]["min"] == -1.0
            assert stats["rain_anom_stats"]["max"] == 1.0
            assert abs(stats["rain_anom_stats"]["mean"]) < 0.1  # Mean ≈ 0

            # Verify temp stats
            assert stats["temp_anom_stats"]["min"] == 0.0
            assert stats["temp_anom_stats"]["max"] == 1.0

        finally:
            # Cleanup
            os.unlink(manifest_path)

    def test_manifest_missing_months(self):
        """Test manifest injection with missing months (graceful handling)."""
        # Create temporary manifest
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            manifest_path = f.name

            # Write manifest with months not in anomaly dict
            for month in ["2023-01", "2023-02", "2023-03"]:
                row = {
                    "aoi_id": "test-aoi",
                    "tile_id": "tile_x000_y000",
                    "month": month,
                    "gcs_uri": f"gs://test/{month}.tif",
                    "rain_anom": 0.0
                }
                f.write(json.dumps(row) + '\n')

        try:
            # Inject anomalies (only for January)
            rain_anomalies = {
                "2023-01": -0.35
                # Missing February and March
            }

            inject_anomalies_to_manifest(
                manifest_path=manifest_path,
                rain_anomalies=rain_anomalies,
                temp_anomalies=None,
                output_path=None
            )

            # Verify fallback to 0.0 for missing months
            with open(manifest_path, 'r') as f:
                rows = [json.loads(line) for line in f]

            assert rows[0]["rain_anom"] == -0.35  # January
            assert rows[1]["rain_anom"] == 0.0  # February (fallback)
            assert rows[2]["rain_anom"] == 0.0  # March (fallback)

        finally:
            # Cleanup
            os.unlink(manifest_path)


def test_end_to_end_smoke():
    """End-to-end smoke test: synthetic data → anomalies → manifest injection."""
    # Create synthetic data
    np.random.seed(42)

    rain_values = {}
    temp_values = {}

    for year in [2021, 2022, 2023]:
        for month in range(1, 13):
            date_str = f"{year}-{month:02d}"
            # Rain: seasonal pattern
            rain_values[date_str] = 50 + 30 * np.sin(2 * np.pi * (month - 1) / 12) + np.random.normal(0, 5)
            # Temp: seasonal pattern (shifted phase)
            temp_values[date_str] = 285 + 10 * np.cos(2 * np.pi * (month - 1) / 12) + np.random.normal(0, 2)

    # Compute anomalies
    rain_anomalies = compute_month_of_year_anomalies(rain_values, baseline_years=3)
    temp_anomalies = compute_month_of_year_anomalies(temp_values, baseline_years=3)

    # Create temporary manifest
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        manifest_path = f.name

        for date_str in sorted(rain_values.keys()):
            row = {
                "aoi_id": "test-aoi",
                "tile_id": "tile_x000_y000",
                "month": date_str,
                "gcs_uri": f"gs://test/{date_str}.tif",
                "rain_anom": 0.0,
                "temp_anom": 0.0
            }
            f.write(json.dumps(row) + '\n')

    try:
        # Inject anomalies
        inject_anomalies_to_manifest(
            manifest_path=manifest_path,
            rain_anomalies=rain_anomalies,
            temp_anomalies=temp_anomalies,
            output_path=None
        )

        # Validate manifest
        stats = validate_manifest_anomalies(manifest_path)

        assert stats["total_rows"] == 36  # 3 years × 12 months
        assert stats["missing_rain_anom"] == 0
        assert stats["missing_temp_anom"] == 0

        # Verify anomalies are reasonable
        assert abs(stats["rain_anom_stats"]["mean"]) < 0.3
        assert abs(stats["temp_anom_stats"]["mean"]) < 0.3

        print("END-TO-END SMOKE TEST PASSED")
        print(f"  Rain anomaly stats: {stats['rain_anom_stats']}")
        print(f"  Temp anomaly stats: {stats['temp_anom_stats']}")

    finally:
        # Cleanup
        os.unlink(manifest_path)


if __name__ == "__main__":
    # Run smoke test directly
    test_end_to_end_smoke()
    print("\nAll smoke tests passed!")
