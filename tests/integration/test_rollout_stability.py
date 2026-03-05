"""Integration tests for rollout stability across seasonal boundaries (User Story 2)"""

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
        """Test Nov→Apr rollout (6 steps crossing winter)"""
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.train(False)

        # Create rollout: Nov→Dec→Jan→Feb→Mar→Apr
        months = [11, 12, 1, 2, 3, 4]
        H = len(months)
        batch_size = 1

        actions_rollout = torch.zeros(batch_size, H, 4)

        for k, month in enumerate(months):
            year = 2025 if month >= 11 else 2026
            timestamp = datetime(year, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)
            actions_rollout[0, k, 2] = month_sin
            actions_rollout[0, k, 3] = month_cos

        # Verify Dec→Jan transition is smooth
        dec_temporal = actions_rollout[0, 1, 2:4]
        jan_temporal = actions_rollout[0, 2, 2:4]
        distance = torch.dist(dec_temporal, jan_temporal)
        assert distance < 0.6

        # Run rollout
        z0 = torch.randn(batch_size, 256, 512)
        with torch.no_grad():
            z_pred = model.rollout(z0, actions_rollout, H=H)

        assert z_pred.shape == (batch_size, H, 256, 512)
        assert not torch.isnan(z_pred).any()

    @pytest.mark.integration
    def test_temporal_features_propagate_through_rollout(self):
        """Verify temporal features affect rollout predictions"""
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.train(False)

        batch_size = 2
        H = 6
        z0 = torch.randn(batch_size, 256, 512)

        # Winter vs summer rollouts
        actions_winter = torch.zeros(batch_size, H, 4)
        actions_summer = torch.zeros(batch_size, H, 4)

        # Same weather
        actions_winter[:, :, :2] = torch.randn(batch_size, H, 2)
        actions_summer[:, :, :2] = actions_winter[:, :, :2].clone()

        # Different temporal
        for k in range(H):
            winter_ts = datetime(2025, k + 1, 15)
            summer_ts = datetime(2025, k + 7, 15)
            w_sin, w_cos = compute_temporal_features(winter_ts)
            s_sin, s_cos = compute_temporal_features(summer_ts)
            actions_winter[:, k, 2] = w_sin
            actions_winter[:, k, 3] = w_cos
            actions_summer[:, k, 2] = s_sin
            actions_summer[:, k, 3] = s_cos

        with torch.no_grad():
            z_pred_winter = model.rollout(z0, actions_winter, H=H)
            z_pred_summer = model.rollout(z0, actions_summer, H=H)

        difference = torch.dist(z_pred_winter, z_pred_summer)
        assert difference > 0.0

    @pytest.mark.integration
    def test_rollout_with_zero_temporal_features(self):
        """Test model handles zero temporal features gracefully"""
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.train(False)

        batch_size = 2
        H = 6
        z0 = torch.randn(batch_size, 256, 512)

        actions = torch.zeros(batch_size, H, 4)
        actions[:, :, :2] = torch.randn(batch_size, H, 2)

        with torch.no_grad():
            z_pred = model.rollout(z0, actions, H=H)

        assert not torch.isnan(z_pred).any()
        assert z_pred.shape == (batch_size, H, 256, 512)

    @pytest.mark.integration
    def test_year_boundary_continuity_in_rollout(self):
        """Verify year boundaries don't cause discontinuities"""
        model = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model.train(False)

        batch_size = 1
        H = 4
        z0 = torch.randn(batch_size, 256, 512)

        # Oct→Nov→Dec→Jan
        months = [10, 11, 12, 1]
        actions = torch.zeros(batch_size, H, 4)

        for k, month in enumerate(months):
            year = 2024 if month >= 10 else 2025
            timestamp = datetime(year, month, 15)
            month_sin, month_cos = compute_temporal_features(timestamp)
            actions[0, k, 2] = month_sin
            actions[0, k, 3] = month_cos

        with torch.no_grad():
            z_pred = model.rollout(z0, actions, H=H)

        # Check Dec→Jan change vs Oct→Nov
        z_dec = z_pred[0, 2]
        z_jan = z_pred[0, 3]
        z_oct = z_pred[0, 0]
        z_nov = z_pred[0, 1]

        change_dec_jan = torch.dist(z_dec, z_jan)
        change_oct_nov = torch.dist(z_oct, z_nov)

        assert change_dec_jan < 2.0 * change_oct_nov
