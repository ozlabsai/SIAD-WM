"""Unit tests for checkpoint dimension upgrade (User Story 2)

Tests backward compatibility mechanism for loading v1 checkpoints into v2 models.
"""

import pytest
import torch

from siad.model.wm import WorldModel


class TestCheckpointUpgrade:
    """Test checkpoint dimension upgrade v1→v2"""

    def test_checkpoint_dimension_match(self):
        """Load v2 checkpoint into v2 model (no padding)"""
        model_v2_source = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        checkpoint_v2 = model_v2_source.state_dict()

        model_v2_target = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2_target.load_state_dict(checkpoint_v2, verbose=False)

        # Should load without modification
        assert True

    def test_checkpoint_dimension_upgrade(self):
        """Load v1 checkpoint into v2 model (with padding)"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)

        # Verify action encoder weight shape upgraded
        v2_action_weight = model_v2.action_encoder.mlp[0].weight
        assert v2_action_weight.shape[1] == 4

    def test_zero_init_neutrality(self):
        """Verify padded temporal feature weights are exactly 0.0"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)

        # Check temporal feature weights (columns 2:4) are zero
        v2_action_weight = model_v2.action_encoder.mlp[0].weight
        temporal_weights = v2_action_weight[:, 2:4]

        assert torch.all(temporal_weights == 0.0), (
            "Temporal feature weights should be zero-initialized"
        )

    def test_checkpoint_downgrade_error(self):
        """Verify error when loading v2 into v1 model"""
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        checkpoint_v2 = model_v2.state_dict()

        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)

        with pytest.raises(ValueError, match="Cannot load checkpoint.*Downgrading"):
            model_v1.load_state_dict(checkpoint_v2, verbose=False)

    def test_zero_init_forward_pass(self):
        """Verify model works after upgrade (forward pass)"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)
        model_v2.train(False)  # Set to inference mode

        # Forward pass
        x = torch.randn(2, 8, 256, 256)
        actions = torch.randn(2, 6, 4)

        with torch.no_grad():
            z = model_v2.encode(x)
            z_pred = model_v2.rollout(z, actions, H=6)

        assert z_pred.shape == (2, 6, 256, 512)
        assert not torch.isnan(z_pred).any()

    def test_upgrade_preserves_other_weights(self):
        """Verify that only action encoder weights are modified"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        # Find a non-action-encoder weight
        encoder_keys = [k for k in checkpoint_v1.keys() if 'context_encoder' in k and 'weight' in k]
        if len(encoder_keys) == 0:
            pytest.skip("No encoder weights found to test")

        encoder_key = encoder_keys[0]
        original_encoder_weight = checkpoint_v1[encoder_key].clone()

        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)

        # Verify encoder weight unchanged
        loaded_encoder_weight = model_v2.state_dict()[encoder_key]
        assert torch.allclose(original_encoder_weight, loaded_encoder_weight), (
            "Non-action-encoder weights should not be modified"
        )

    def test_multiple_upgrades_idempotent(self):
        """Verify loading upgraded checkpoint again doesn't modify it"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        # First upgrade
        model_v2_first = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2_first.load_state_dict(checkpoint_v1, verbose=False)
        checkpoint_v2 = model_v2_first.state_dict()

        # Second load (should be no-op)
        model_v2_second = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2_second.load_state_dict(checkpoint_v2, verbose=False)

        # Verify identical
        for key in checkpoint_v2.keys():
            assert torch.allclose(checkpoint_v2[key], model_v2_second.state_dict()[key])
