"""Unit tests for checkpoint dimension upgrade

Tests the WorldModel.load_state_dict() with backward compatibility per contracts/model_api.md.
Validates:
- Dimension match (v2→v2)
- Dimension upgrade (v1→v2 with padding)
- Zero-initialization neutrality
- Dimension downgrade error (v2→v1)
"""

import pytest
import torch

from siad.model.wm import WorldModel


class TestCheckpointUpgrade:
    """Test checkpoint loading with automatic dimension upgrade"""

    def test_checkpoint_dimension_match(self):
        """Load v2 checkpoint into v2 model (no padding needed)"""
        # Create v2 model
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        # Create v2 checkpoint (action_dim=4)
        checkpoint_v2 = model_v2.state_dict()

        # Load should succeed without modification
        model_v2.load_state_dict(checkpoint_v2, verbose=False)

        # Verify action encoder weight shape
        action_weight = model_v2.action_encoder.mlp[0].weight
        assert action_weight.shape == (64, 4), (
            f"Expected weight shape [64, 4], got {action_weight.shape}"
        )

    def test_checkpoint_dimension_upgrade(self):
        """Load v1 checkpoint (action_dim=2) into v2 model (action_dim=4)"""
        # Create v1 model and checkpoint
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        # Create v2 model
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        # Load v1 checkpoint into v2 model (should auto-upgrade)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)

        # Verify weight shape was upgraded
        action_weight = model_v2.action_encoder.mlp[0].weight
        assert action_weight.shape == (64, 4), (
            f"Expected upgraded weight shape [64, 4], got {action_weight.shape}"
        )

    def test_zero_init_neutrality(self):
        """Verify padded temporal feature weights are exactly 0.0"""
        # Create v1 checkpoint
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        # Get v1 weights for comparison
        v1_action_weight = checkpoint_v1['action_encoder.mlp.0.weight']  # [64, 2]

        # Load into v2 model
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)

        # Get upgraded weights
        v2_action_weight = model_v2.action_encoder.mlp[0].weight  # [64, 4]

        # Check that existing weights are preserved
        assert torch.allclose(v2_action_weight[:, :2], v1_action_weight, atol=1e-6), (
            "Existing v1 weights should be preserved exactly"
        )

        # Check that new temporal feature weights are exactly zero
        temporal_weights = v2_action_weight[:, 2:4]
        assert torch.all(temporal_weights == 0.0), (
            f"Temporal feature weights should be zero-initialized, but got non-zero values: "
            f"mean={temporal_weights.mean()}, std={temporal_weights.std()}"
        )

    def test_checkpoint_downgrade_error(self):
        """Verify error when loading v2 checkpoint into v1 model"""
        # Create v2 checkpoint
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        checkpoint_v2 = model_v2.state_dict()

        # Create v1 model
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)

        # Loading v2 into v1 should raise ValueError
        with pytest.raises(ValueError, match="Cannot load checkpoint with action_dim=4"):
            model_v1.load_state_dict(checkpoint_v2, verbose=False)

    def test_zero_init_forward_pass(self):
        """Verify zero-initialized temporal features don't break forward pass"""
        # Create v1 checkpoint and load into v2 model
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)

        # Test forward pass with v2 actions (including zero temporal features)
        batch_size = 4
        actions_v2 = torch.zeros(batch_size, 4)
        actions_v2[:, :2] = torch.randn(batch_size, 2)  # Weather features
        # actions_v2[:, 2:4] remain zero (temporal features)

        # Forward pass should work without errors
        embeddings = model_v2.action_encoder(actions_v2)
        assert embeddings.shape == (batch_size, 128)
        assert not torch.isnan(embeddings).any()

    def test_upgrade_preserves_other_weights(self):
        """Verify upgrade only modifies action encoder, not other model weights"""
        # Create v1 checkpoint
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        # Save a copy of some encoder weight for comparison (use first available key)
        encoder_keys = [k for k in checkpoint_v1.keys() if 'context_encoder' in k]
        if not encoder_keys:
            pytest.skip("No encoder weights found to verify")

        encoder_key = encoder_keys[0]
        original_encoder_weight = checkpoint_v1[encoder_key].clone()

        # Load into v2 model
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2.load_state_dict(checkpoint_v1, verbose=False)

        # Verify encoder weights are unchanged
        upgraded_encoder_weight = model_v2.state_dict()[encoder_key]
        assert torch.allclose(upgraded_encoder_weight, original_encoder_weight, atol=1e-6), (
            f"Encoder weights should not be modified during action dimension upgrade (key: {encoder_key})"
        )

    def test_multiple_upgrades_idempotent(self):
        """Verify loading checkpoint multiple times gives same result"""
        # Create v1 checkpoint
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        checkpoint_v1 = model_v1.state_dict()

        # Load into v2 model (first time)
        model_v2_first = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2_first.load_state_dict(checkpoint_v1, verbose=False)

        # Load into another v2 model (second time)
        model_v2_second = WorldModel(action_dim=4, in_channels=8, latent_dim=512)
        model_v2_second.load_state_dict(checkpoint_v1, verbose=False)

        # Both should have identical weights
        for key in model_v2_first.state_dict():
            weight_first = model_v2_first.state_dict()[key]
            weight_second = model_v2_second.state_dict()[key]
            assert torch.allclose(weight_first, weight_second, atol=1e-9), (
                f"Weights should be identical for key {key}"
            )
