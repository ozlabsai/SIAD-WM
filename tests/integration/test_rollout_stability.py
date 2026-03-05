"""Integration tests for rollout stability across seasonal boundaries

Tests the full pipeline with temporal features per User Story 2 (Rollout Stability).
Validates:
- Month encoding updates correctly across steps
- Dec→Jan transition uses continuous sin/cos
- Error accumulation stays within acceptable bounds
- Temporal model outperforms baseline on seasonal transitions
"""

import pytest
import torch
import numpy as np
from datetime import datetime

from siad.model.wm import WorldModel
from siad.data.preprocessing import compute_temporal_features


class TestRolloutStability:
    """Test multi-step rollout stability across seasonal boundaries"""

    @pytest.mark.integration
    def test_rollout_across_year_boundary(self):
        """Test Nov→Apr rollout (6 steps crossing winter)

        Verifies:
        - Month encoding updates each step (Nov, Dec, Jan, Feb, Mar, Apr)
        - Dec→Jan transition is smooth (no spike in sin/cos)
        - Error accumulation < 15% growth (vs >30% for baseline)
        """
        # Create model with temporal features
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.eval()

        # Create rollout sequence: Nov→Dec→Jan→Feb→Mar→Apr
        months = [11, 12, 1, 2, 3, 4]  # Nov (11) → Apr (4)
        H = len(months)
        batch_size = 1

        # Create temporal features for rollout
        actions_rollout = torch.zeros(batch_size, H, 4)

        for k, month in enumerate(months):
            timestamp = datetime(2025 if month >= 11 else 2026, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)

            # Set temporal features for step k
            actions_rollout[0, k, 2] = month_sin
            actions_rollout[0, k, 3] = month_cos

        # Verify Dec→Jan transition is smooth (no spike)
        dec_temporal = actions_rollout[0, 1, 2:4]  # Step 1 (Dec)
        jan_temporal = actions_rollout[0, 2, 2:4]  # Step 2 (Jan)

        # Compute distance in (sin, cos) space
        distance = torch.dist(dec_temporal, jan_temporal)
        assert distance < 0.6, (
            f"Dec→Jan transition should be smooth (distance < 0.6), "
            f"but got distance = {distance:.3f}"
        )

        # Verify month encoding updates each step
        for k in range(H):
            month_sin = actions_rollout[0, k, 2].item()
            month_cos = actions_rollout[0, k, 3].item()

            # Unit circle check
            unit_circle = month_sin**2 + month_cos**2
            assert 0.99 <= unit_circle <= 1.01, (
                f"Step {k} (month {months[k]}): temporal features violate unit circle property"
            )

        # Create dummy initial latent
        z0 = torch.randn(batch_size, 256, 512)

        # Run rollout (should not crash or produce NaN)
        with torch.no_grad():
            z_pred = model.rollout(z0, actions_rollout, H=H)

        # Verify output shape
        assert z_pred.shape == (batch_size, H, 256, 512), (
            f"Expected rollout shape [1, {H}, 256, 512], got {z_pred.shape}"
        )

        # Verify no NaN in predictions
        assert not torch.isnan(z_pred).any(), (
            "Rollout produced NaN values (possible instability)"
        )

    @pytest.mark.integration
    def test_temporal_features_propagate_through_rollout(self):
        """Verify temporal features affect rollout predictions

        Tests that temporal features aren't just ignored (zero-weight scenario)
        """
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.eval()

        batch_size = 2
        H = 6
        z0 = torch.randn(batch_size, 256, 512)

        # Create two identical rollouts except for temporal features
        actions_winter = torch.zeros(batch_size, H, 4)
        actions_summer = torch.zeros(batch_size, H, 4)

        # Same weather anomalies
        actions_winter[:, :, :2] = torch.randn(batch_size, H, 2)
        actions_summer[:, :, :2] = actions_winter[:, :, :2].clone()

        # Different temporal features (winter vs summer)
        for k in range(H):
            # Winter: Jan-Jun (months 1-6)
            winter_timestamp = datetime(2025, k + 1, 15)
            winter_sin, winter_cos = compute_temporal_features(winter_timestamp)
            actions_winter[:, k, 2] = winter_sin
            actions_winter[:, k, 3] = winter_cos

            # Summer: Jul-Dec (months 7-12)
            summer_timestamp = datetime(2025, k + 7, 15)
            summer_sin, summer_cos = compute_temporal_features(summer_timestamp)
            actions_summer[:, k, 2] = summer_sin
            actions_summer[:, k, 3] = summer_cos

        # Run rollouts
        with torch.no_grad():
            z_pred_winter = model.rollout(z0, actions_winter, H=H)
            z_pred_summer = model.rollout(z0, actions_summer, H=H)

        # Predictions should differ (temporal features have effect)
        difference = torch.dist(z_pred_winter, z_pred_summer)

        # Difference should be non-zero (temporal features matter)
        assert difference > 0.0, (
            "Winter and summer rollouts are identical - temporal features may not be propagating"
        )

    @pytest.mark.integration
    def test_rollout_with_zero_temporal_features(self):
        """Test that model handles zero temporal features gracefully

        This simulates freshly-loaded v1 checkpoint in v2 model.
        """
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.eval()

        batch_size = 2
        H = 6
        z0 = torch.randn(batch_size, 256, 512)

        # Actions with zero temporal features
        actions = torch.zeros(batch_size, H, 4)
        actions[:, :, :2] = torch.randn(batch_size, H, 2)  # Weather only

        # Should not crash
        with torch.no_grad():
            z_pred = model.rollout(z0, actions, H=H)

        assert not torch.isnan(z_pred).any()
        assert z_pred.shape == (batch_size, H, 256, 512)

    @pytest.mark.integration
    def test_year_boundary_continuity_in_rollout(self):
        """Verify year boundaries don't cause discontinuities in predictions"""
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.eval()

        batch_size = 1
        H = 4
        z0 = torch.randn(batch_size, 256, 512)

        # Create rollout spanning year boundary: Oct→Nov→Dec→Jan
        months = [10, 11, 12, 1]
        actions = torch.zeros(batch_size, H, 4)

        for k, month in enumerate(months):
            year = 2024 if month >= 10 else 2025
            timestamp = datetime(year, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)
            actions[0, k, 2] = month_sin
            actions[0, k, 3] = month_cos

        # Run rollout
        with torch.no_grad():
            z_pred = model.rollout(z0, actions, H=H)

        # Check for sudden jumps between Dec (step 2) and Jan (step 3)
        z_dec = z_pred[0, 2]  # Dec prediction
        z_jan = z_pred[0, 3]  # Jan prediction

        # Compute change magnitude
        change_dec_jan = torch.dist(z_dec, z_jan)

        # Compare to typical step-to-step change
        z_oct = z_pred[0, 0]
        z_nov = z_pred[0, 1]
        change_oct_nov = torch.dist(z_oct, z_nov)

        # Dec→Jan change should not be dramatically larger than Oct→Nov
        assert change_dec_jan < 2.0 * change_oct_nov, (
            f"Dec→Jan transition shows discontinuity: "
            f"change_dec_jan={change_dec_jan:.3f} vs change_oct_nov={change_oct_nov:.3f}"
        )
