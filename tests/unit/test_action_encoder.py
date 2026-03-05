"""Unit tests for ActionEncoder with temporal features (User Story 1)

Tests action encoder forward pass, shape contracts, and dimension handling.
"""

import pytest
import torch

from siad.model.actions import ActionEncoder


class TestActionEncoder:
    """Test ActionEncoder with v2 temporal features"""

    def test_action_encoder_forward_v2(self):
        """Forward pass with [B, 4] input (v2: weather + temporal features)"""
        encoder = ActionEncoder(action_dim=4)
        actions_v2 = torch.randn(8, 4)  # [rain_anom, temp_anom, month_sin, month_cos]

        embeddings = encoder(actions_v2)

        assert embeddings is not None
        assert embeddings.shape == (8, 128)
        assert not torch.isnan(embeddings).any()

    def test_action_encoder_shape_contract(self):
        """Verify output shape [B, 128] contract"""
        encoder = ActionEncoder(action_dim=4)

        for batch_size in [1, 4, 16, 32]:
            actions = torch.randn(batch_size, 4)
            embeddings = encoder(actions)
            assert embeddings.shape == (batch_size, 128), (
                f"Expected shape ({batch_size}, 128), got {embeddings.shape}"
            )

    def test_action_encoder_dimension_mismatch(self):
        """Verify error when input != action_dim"""
        encoder = ActionEncoder(action_dim=4)
        actions_wrong = torch.randn(8, 2)  # Wrong dimension

        with pytest.raises(RuntimeError):
            encoder(actions_wrong)

    def test_action_encoder_v1_compatibility(self):
        """Test with action_dim=2 (v1: weather only)"""
        encoder = ActionEncoder(action_dim=2)
        actions_v1 = torch.randn(8, 2)

        embeddings = encoder(actions_v1)
        assert embeddings.shape == (8, 128)

    def test_action_encoder_default_params(self):
        """Verify default action_dim=4 for v2"""
        encoder = ActionEncoder()
        assert encoder.action_dim == 4

    def test_action_encoder_gradient_flow(self):
        """Verify gradients flow through encoder"""
        encoder = ActionEncoder(action_dim=4)
        actions = torch.randn(4, 4, requires_grad=True)

        embeddings = encoder(actions)
        loss = embeddings.sum()
        loss.backward()

        assert actions.grad is not None
        assert not torch.isnan(actions.grad).any()

    def test_action_encoder_output_range(self):
        """Check output is not unbounded (SiLU should bound it)"""
        encoder = ActionEncoder(action_dim=4)
        actions = torch.randn(100, 4)

        embeddings = encoder(actions)

        # SiLU output should be somewhat bounded for random input
        assert embeddings.abs().max() < 100, "Embeddings suspiciously large"

    def test_action_encoder_batch_independence(self):
        """Verify batch samples are processed independently"""
        encoder = ActionEncoder(action_dim=4)

        # Process individually
        action1 = torch.randn(1, 4)
        action2 = torch.randn(1, 4)
        embed1 = encoder(action1)
        embed2 = encoder(action2)

        # Process as batch
        actions_batch = torch.cat([action1, action2], dim=0)
        embeds_batch = encoder(actions_batch)

        # Should be identical
        assert torch.allclose(embeds_batch[0], embed1[0], atol=1e-6)
        assert torch.allclose(embeds_batch[1], embed2[0], atol=1e-6)

    def test_action_encoder_temporal_features_zero(self):
        """Test with zero temporal features (simulates v1 checkpoint upgrade)"""
        encoder = ActionEncoder(action_dim=4)

        # Weather features with zero temporal
        actions = torch.zeros(8, 4)
        actions[:, :2] = torch.randn(8, 2)  # Weather only, temporal=0

        embeddings = encoder(actions)
        assert embeddings.shape == (8, 128)
        assert not torch.isnan(embeddings).any()
