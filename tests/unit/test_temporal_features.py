"""Unit tests for temporal feature computation (User Story 1)

Tests the core temporal feature extraction per contracts/dataset_api.md.
Validates range, unit circle property, year boundary continuity, and correctness.
"""

import pytest
import numpy as np
from datetime import datetime

from siad.data.preprocessing import compute_temporal_features


class TestComputeTemporalFeatures:
    """Test compute_temporal_features() per contracts"""

    def test_compute_temporal_features_range(self):
        """Verify month_sin/cos in [-1, 1] for all months"""
        for month in range(1, 13):
            timestamp = datetime(2025, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            assert -1 <= month_sin <= 1, f"month_sin={month_sin} out of range for month {month}"
            assert -1 <= month_cos <= 1, f"month_cos={month_cos} out of range for month {month}"

    def test_temporal_features_unit_circle(self):
        """Verify sin² + cos² ≈ 1 for all months (unit circle property)"""
        for month in range(1, 13):
            timestamp = datetime(2025, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            unit_circle = month_sin**2 + month_cos**2
            assert 0.99 <= unit_circle <= 1.01, (
                f"Month {month}: unit circle property violated, "
                f"sin²+cos² = {unit_circle} (expected ≈1.0)"
            )

    def test_year_boundary_continuity(self):
        """Verify Dec→Jan distance < 0.6 (smooth year boundary)"""
        dec_timestamp = datetime(2024, 12, 15)
        jan_timestamp = datetime(2025, 1, 15)

        dec_sin, dec_cos = compute_temporal_features(dec_timestamp)
        jan_sin, jan_cos = compute_temporal_features(jan_timestamp)

        # Euclidean distance in (sin, cos) space
        distance = np.sqrt((jan_sin - dec_sin)**2 + (jan_cos - dec_cos)**2)

        assert distance < 0.6, (
            f"Dec→Jan transition not smooth: distance={distance:.3f} (expected <0.6)"
        )

    def test_temporal_features_all_months(self):
        """Verify correct values for specific months"""
        test_cases = [
            (1, 30),    # Jan: 30 degrees
            (4, 120),   # Apr: 120 degrees
            (7, 210),   # Jul: 210 degrees
            (10, 300),  # Oct: 300 degrees
        ]

        for month, expected_degrees in test_cases:
            timestamp = datetime(2025, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            # Expected values
            expected_radians = np.deg2rad(expected_degrees)
            expected_sin = np.sin(expected_radians)
            expected_cos = np.cos(expected_radians)

            # Allow 1e-6 tolerance for floating point
            assert np.isclose(month_sin, expected_sin, atol=1e-6), (
                f"Month {month}: month_sin={month_sin}, expected {expected_sin}"
            )
            assert np.isclose(month_cos, expected_cos, atol=1e-6), (
                f"Month {month}: month_cos={month_cos}, expected {expected_cos}"
            )

    def test_temporal_features_deterministic(self):
        """Verify same month produces same features"""
        timestamp1 = datetime(2024, 5, 1)
        timestamp2 = datetime(2024, 5, 15)
        timestamp3 = datetime(2024, 5, 31)

        result1 = compute_temporal_features(timestamp1)
        result2 = compute_temporal_features(timestamp2)
        result3 = compute_temporal_features(timestamp3)

        # All May dates should produce identical features
        assert result1 == result2 == result3, (
            "Same month should produce identical temporal features regardless of day"
        )

    def test_temporal_features_year_invariant(self):
        """Verify features are year-invariant (only depend on month)"""
        month_sin_2024, month_cos_2024 = compute_temporal_features(datetime(2024, 6, 15))
        month_sin_2025, month_cos_2025 = compute_temporal_features(datetime(2025, 6, 15))
        month_sin_2026, month_cos_2026 = compute_temporal_features(datetime(2026, 6, 15))

        assert month_sin_2024 == month_sin_2025 == month_sin_2026, (
            "month_sin should be year-invariant"
        )
        assert month_cos_2024 == month_cos_2025 == month_cos_2026, (
            "month_cos should be year-invariant"
        )
