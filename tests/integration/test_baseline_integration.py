"""Integration tests for baseline module with world model

Tests the full workflow:
1. Load world model
2. Generate predictions with world model
3. Generate predictions with baselines
4. Compare residuals
5. Verify baselines integrate with existing residuals module
"""

import pytest
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from siad.model.wm import WorldModel
from siad.detect.baselines import (
    PersistenceBaseline,
    LinearExtrapolationBaseline,
    compare_baseline_residuals,
    compute_baseline_scores
)
from siad.detect.residuals import compute_residuals
from siad.detect.environmental_norm import generate_neutral_actions


class TestBaselineWorldModelIntegration:
    """Test baselines integrate with world model"""

    @pytest.fixture
    def world_model(self):
        """Create small world model for testing"""
        model = WorldModel(
            in_channels=8,
            latent_dim=512,
            action_dim=2,
            encoder_blocks=2,
            transition_blocks=2,
            dropout=0.0
        )
        model.train(False)
        return model

    def test_baseline_vs_world_model_workflow(self, world_model):
        """Complete workflow: WM predictions vs baseline"""
        x_context = torch.randn(1, 8, 256, 256)
        x_targets = torch.randn(6, 8, 256, 256)

        with torch.no_grad():
            z_context = world_model.encode(x_context)
            actions = generate_neutral_actions(horizon=6, action_dim=2)
            actions = actions.unsqueeze(0)
            z_pred_wm = world_model.rollout(z_context, actions, H=6)
            z_actual = world_model.encode_targets(x_targets)
            z_actual = z_actual.unsqueeze(0)

        baseline = PersistenceBaseline()
        z_pred_baseline = baseline.predict(z_context.squeeze(0), horizon=6)
        z_pred_baseline = z_pred_baseline.unsqueeze(0)

        result = compare_baseline_residuals(
            z_pred_wm,
            z_pred_baseline,
            z_actual,
            baseline_name="persistence"
        )

        assert 'residual_wm' in result
        assert 'residual_baseline' in result
        assert len(result['residual_wm']) == 6

    def test_baseline_with_residuals_module(self, world_model):
        """Baselines use same residual computation as world model"""
        x_context = torch.randn(1, 8, 256, 256)
        x_targets = torch.randn(6, 8, 256, 256)

        with torch.no_grad():
            z_context = world_model.encode(x_context).squeeze(0)
            z_actual = world_model.encode_targets(x_targets)

        baseline = PersistenceBaseline()
        z_pred_baseline = baseline.predict(z_context, horizon=6)

        months = ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06"]
        result = compute_residuals(
            z_pred=z_pred_baseline,
            z_obs=z_actual,
            tile_id="test_tile",
            months=months,
            weather_normalized=True
        )

        assert result.tile_id == "test_tile"
        assert result.residuals.shape == (6, 256)
        assert result.tile_scores.shape == (6,)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
