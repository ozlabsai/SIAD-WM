"""Unit tests for temporal feature computation

Tests the compute_temporal_features() function per contracts/dataset_api.md.
Validates:
- Range constraints ([-1, 1])
- Unit circle property (sin² + cos² ≈ 1)
- Year boundary continuity (Dec→Jan smooth transition)
- Correctness for specific months
"""

import pytest
import numpy as np
from datetime import datetime

from siad.data.preprocessing import compute_temporal_features


class TestComputeTemporalFeatures:
    """Test temporal feature extraction from timestamps"""

    def test_compute_temporal_features_range(self):
        """Verify month_sin and month_cos are in [-1, 1] for all months"""
        for month in range(1, 13):
            timestamp = datetime(2025, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            # Range constraints
            assert -1 <= month_sin <= 1, (
                f"month_sin={month_sin} out of range for month {month}"
            )
            assert -1 <= month_cos <= 1, (
                f"month_cos={month_cos} out of range for month {month}"
            )

    def test_temporal_features_unit_circle(self):
        """Verify sin² + cos² ≈ 1 for all months (unit circle property)"""
        for month in range(1, 13):
            timestamp = datetime(2025, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            # Unit circle property: sin² + cos² = 1
            unit_circle_check = month_sin**2 + month_cos**2

            assert 0.99 <= unit_circle_check <= 1.01, (
                f"Unit circle violation for month {month}: "
                f"sin²+cos² = {unit_circle_check}"
            )

    def test_year_boundary_continuity(self):
        """Verify Dec→Jan distance < 0.6 (smooth year boundary)"""
        # December (month 12)
        dec_timestamp = datetime(2024, 12, 15)
        dec_sin, dec_cos = compute_temporal_features(dec_timestamp)

        # January (month 1)
        jan_timestamp = datetime(2025, 1, 15)
        jan_sin, jan_cos = compute_temporal_features(jan_timestamp)

        # Euclidean distance in (sin, cos) space
        distance = np.sqrt((jan_sin - dec_sin)**2 + (jan_cos - dec_cos)**2)

        assert distance < 0.6, (
            f"Dec→Jan distance too large: {distance:.3f} "
            f"(should be <0.6 for smooth year boundary)"
        )

    def test_temporal_features_all_months(self):
        """Verify correct values for representative months (Jan, Apr, Jul, Oct)"""
        # Test cases: (month, expected_angle_degrees)
        test_cases = [
            (1, 30),    # January: 30°
            (4, 120),   # April: 120°
            (7, 210),   # July: 210°
            (10, 300),  # October: 300°
        ]

        for month, expected_angle_deg in test_cases:
            timestamp = datetime(2025, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            # Convert expected angle to radians
            expected_angle_rad = np.deg2rad(expected_angle_deg)
            expected_sin = np.sin(expected_angle_rad)
            expected_cos = np.cos(expected_angle_rad)

            # Check values match (within floating point tolerance)
            assert np.isclose(month_sin, expected_sin, atol=1e-6), (
                f"Month {month}: sin mismatch. "
                f"Expected {expected_sin:.6f}, got {month_sin:.6f}"
            )
            assert np.isclose(month_cos, expected_cos, atol=1e-6), (
                f"Month {month}: cos mismatch. "
                f"Expected {expected_cos:.6f}, got {month_cos:.6f}"
            )

    def test_temporal_features_deterministic(self):
        """Verify function is deterministic (same input → same output)"""
        timestamp = datetime(2025, 6, 15)

        # Call multiple times
        result1 = compute_temporal_features(timestamp)
        result2 = compute_temporal_features(timestamp)

        assert result1 == result2, "Function should be deterministic"

    def test_temporal_features_year_invariant(self):
        """Verify temporal features are year-invariant (only month matters)"""
        # Same month, different years
        june_2024 = datetime(2024, 6, 15)
        june_2025 = datetime(2025, 6, 15)
        june_2026 = datetime(2026, 6, 15)

        sin_2024, cos_2024 = compute_temporal_features(june_2024)
        sin_2025, cos_2025 = compute_temporal_features(june_2025)
        sin_2026, cos_2026 = compute_temporal_features(june_2026)

        # All should be identical (year doesn't matter)
        assert np.isclose(sin_2024, sin_2025, atol=1e-10)
        assert np.isclose(sin_2024, sin_2026, atol=1e-10)
        assert np.isclose(cos_2024, cos_2025, atol=1e-10)
        assert np.isclose(cos_2024, cos_2026, atol=1e-10)
