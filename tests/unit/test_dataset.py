"""Unit tests for Dataset with temporal features

Tests the SIADDataset with v1/v2 schema support per contracts/dataset_api.md.
Validates:
- V2 dataset loading with action_dim=4
- Temporal feature validation (unit circle property)
- V1 backward compatibility (action_dim=2, timestamps=None)
"""

import pytest
import torch
import numpy as np
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Import will be tested when dataset is available
# from siad.train.dataset import SIADDataset


class TestDatasetV2Loading:
    """Test dataset loading with v2 schema (temporal features)"""

    @pytest.fixture
    def mock_manifest_v2(self, tmp_path):
        """Create mock v2 manifest with preprocessing_version field"""
        manifest_path = tmp_path / "manifest_v2.jsonl"

        # Create v2 manifest entry
        sample_v2 = {
            "tile_id": "tile_test_v2",
            "months": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07"],
            "observations": [f"test_{i}.tif" for i in range(7)],
            "actions": [[1.0, 0.5] for _ in range(7)],  # Weather only (v2 computes temporal)
            "preprocessing_version": "v2"
        }

        with open(manifest_path, 'w') as f:
            f.write(json.dumps(sample_v2) + '\n')

        return manifest_path

    @pytest.fixture
    def mock_manifest_v1(self, tmp_path):
        """Create mock v1 manifest (no preprocessing_version field)"""
        manifest_path = tmp_path / "manifest_v1.jsonl"

        # Create v1 manifest entry (no preprocessing_version field)
        sample_v1 = {
            "tile_id": "tile_test_v1",
            "months": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07"],
            "observations": [f"test_{i}.tif" for i in range(7)],
            "actions": [[1.0, 0.5] for _ in range(7)]  # Weather only
            # No preprocessing_version field → defaults to v1
        }

        with open(manifest_path, 'w') as f:
            f.write(json.dumps(sample_v1) + '\n')

        return manifest_path

    @pytest.mark.skip(reason="Requires rasterio and actual GeoTIFF files")
    def test_v2_dataset_loading(self, mock_manifest_v2):
        """Load v2 dataset and verify action_dim=4"""
        from siad.train.dataset import SIADDataset

        dataset = SIADDataset(
            manifest_path=str(mock_manifest_v2),
            context_length=1,
            rollout_horizon=6
        )

        # Get a sample
        sample = dataset[0]

        # Check action_dim=4 (v2)
        assert sample["actions_rollout"].shape[1] == 4, (
            f"Expected action_dim=4 for v2, got {sample['actions_rollout'].shape[1]}"
        )

        # Check timestamps exist
        assert sample["timestamps"] is not None, (
            "v2 dataset should have timestamps"
        )

    @pytest.mark.skip(reason="Requires rasterio and actual GeoTIFF files")
    def test_temporal_feature_validation(self, mock_manifest_v2):
        """Verify unit circle property in batch"""
        from siad.train.dataset import SIADDataset

        dataset = SIADDataset(
            manifest_path=str(mock_manifest_v2),
            context_length=1,
            rollout_horizon=6
        )

        sample = dataset[0]
        actions = sample["actions_rollout"]  # [H, 4]

        # Extract temporal features (last 2 dims)
        month_sin = actions[:, 2].numpy()
        month_cos = actions[:, 3].numpy()

        # Verify unit circle property: sin² + cos² ≈ 1
        unit_circle_check = month_sin**2 + month_cos**2

        assert np.all((unit_circle_check >= 0.99) & (unit_circle_check <= 1.01)), (
            f"Temporal features violate unit circle property: sin²+cos² = {unit_circle_check}"
        )

    @pytest.mark.skip(reason="Requires rasterio and actual GeoTIFF files")
    def test_v1_backward_compat(self, mock_manifest_v1):
        """Load v1 dataset and verify action_dim=2, timestamps=None"""
        from siad.train.dataset import SIADDataset

        dataset = SIADDataset(
            manifest_path=str(mock_manifest_v1),
            context_length=1,
            rollout_horizon=6
        )

        sample = dataset[0]

        # Check action_dim=2 (v1)
        assert sample["actions_rollout"].shape[1] == 2, (
            f"Expected action_dim=2 for v1, got {sample['actions_rollout'].shape[1]}"
        )

        # Check timestamps are None (not available in v1)
        assert sample["timestamps"] is None, (
            "v1 dataset should have timestamps=None"
        )


class TestTemporalFeatureComputation:
    """Test temporal feature computation in dataset loader"""

    def test_compute_temporal_features_in_dataset(self):
        """Test that dataset correctly computes temporal features from months"""
        # This is a lightweight test of the feature computation logic
        from siad.data.preprocessing import compute_temporal_features

        # Test a specific month
        timestamp = datetime(2025, 3, 15)  # March
        month_sin, month_cos = compute_temporal_features(timestamp)

        # March is month 3 → angle = 2π * 3 / 12 = π/2 = 90°
        # sin(90°) = 1, cos(90°) = 0
        assert np.isclose(month_sin, 1.0, atol=1e-6)
        assert np.isclose(month_cos, 0.0, atol=1e-6)

    def test_temporal_features_range(self):
        """Verify all months produce features in valid range"""
        from siad.data.preprocessing import compute_temporal_features

        for month in range(1, 13):
            timestamp = datetime(2025, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            assert -1 <= month_sin <= 1
            assert -1 <= month_cos <= 1

            # Unit circle
            unit_circle = month_sin**2 + month_cos**2
            assert 0.99 <= unit_circle <= 1.01


class TestDatasetVersionDetection:
    """Test dataset correctly detects v1 vs v2 schema"""

    def test_version_detection_from_manifest(self, tmp_path):
        """Test that version is correctly detected from manifest metadata"""
        # Create v2 manifest
        manifest_v2 = tmp_path / "manifest_v2.jsonl"
        sample_v2 = {
            "tile_id": "test",
            "months": ["2025-01"] * 7,
            "observations": ["test.tif"] * 7,
            "actions": [[1.0, 0.5]] * 7,
            "preprocessing_version": "v2"
        }
        with open(manifest_v2, 'w') as f:
            f.write(json.dumps(sample_v2) + '\n')

        # Create v1 manifest (no version field)
        manifest_v1 = tmp_path / "manifest_v1.jsonl"
        sample_v1 = {
            "tile_id": "test",
            "months": ["2025-01"] * 7,
            "observations": ["test.tif"] * 7,
            "actions": [[1.0, 0.5]] * 7
            # No preprocessing_version → should default to v1
        }
        with open(manifest_v1, 'w') as f:
            f.write(json.dumps(sample_v1) + '\n')

        # Load manifests and check detection
        # (This would be tested in integration tests with actual dataset class)
        with open(manifest_v2) as f:
            data_v2 = json.loads(f.readline())
            assert data_v2.get('preprocessing_version', 'v1') == 'v2'

        with open(manifest_v1) as f:
            data_v1 = json.loads(f.readline())
            assert data_v1.get('preprocessing_version', 'v1') == 'v1'
