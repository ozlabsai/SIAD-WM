"""Integration tests for training efficiency (User Story 3)"""

import pytest
import torch

from siad.model.wm import WorldModel


class TestModelParameterCount:
    """Test that temporal features add minimal parameters"""

    @pytest.mark.integration
    def test_model_parameter_count(self):
        """Verify parameter count increase is minimal"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        params_v1 = sum(p.numel() for p in model_v1.parameters())
        params_v2 = sum(p.numel() for p in model_v2.parameters())

        param_increase = params_v2 - params_v1
        percent_increase = (param_increase / params_v1) * 100

        print(f"\nParameter count:")
        print(f"  V1 (baseline): {params_v1:,} parameters")
        print(f"  V2 (temporal): {params_v2:,} parameters")
        print(f"  Increase: {param_increase:,} parameters ({percent_increase:.4f}%)")

        # Should be exactly 128 params (2 dims × 64 hidden)
        expected_increase = 128
        assert param_increase == expected_increase
        assert percent_increase < 0.01

    @pytest.mark.integration
    def test_action_encoder_parameter_breakdown(self):
        """Verify parameter increase is isolated to action encoder"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        encoder_params_v1 = sum(p.numel() for p in model_v1.context_encoder.parameters())
        encoder_params_v2 = sum(p.numel() for p in model_v2.context_encoder.parameters())
        assert encoder_params_v1 == encoder_params_v2

        transition_params_v1 = sum(p.numel() for p in model_v1.transition_model.parameters())
        transition_params_v2 = sum(p.numel() for p in model_v2.transition_model.parameters())
        assert transition_params_v1 == transition_params_v2

        action_params_v1 = sum(p.numel() for p in model_v1.action_encoder.parameters())
        action_params_v2 = sum(p.numel() for p in model_v2.action_encoder.parameters())
        assert action_params_v2 > action_params_v1
