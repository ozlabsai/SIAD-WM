"""Unit tests for ActionEncoder

Tests the ActionEncoder module per contracts/model_api.md.
Validates:
- Forward pass with v2 input [B, 4]
- Output shape contract [B, 128]
- Dimension mismatch error handling
- Backward compatibility with v1 dimensions
"""

import pytest
import torch

from siad.model.actions import ActionEncoder


class TestActionEncoder:
    """Test action encoder with temporal features"""

    def test_action_encoder_forward_v2(self):
        """Forward pass with [B, 4] input (v2: weather + temporal features)"""
        # V2: action_dim=4
        encoder = ActionEncoder(action_dim=4)

        # Batch of 8 samples with 4-dimensional actions
        # [rain_anom, temp_anom, month_sin, month_cos]
        batch_size = 8
        actions_v2 = torch.randn(batch_size, 4)

        # Forward pass
        embeddings = encoder(actions_v2)

        # Should succeed without errors
        assert embeddings is not None
        assert isinstance(embeddings, torch.Tensor)

    def test_action_encoder_shape_contract(self):
        """Verify output shape is [B, 128] for v2 input"""
        encoder = ActionEncoder(action_dim=4, output_dim=128)

        batch_size = 16
        actions = torch.randn(batch_size, 4)

        embeddings = encoder(actions)

        # Output shape contract: [B, 128]
        assert embeddings.shape == (batch_size, 128), (
            f"Expected shape [{batch_size}, 128], got {embeddings.shape}"
        )

    def test_action_encoder_dimension_mismatch(self):
        """Verify error when input dimension != action_dim"""
        # Encoder configured for v2 (action_dim=4)
        encoder = ActionEncoder(action_dim=4)

        # Try to pass v1 actions (action_dim=2)
        batch_size = 8
        actions_v1 = torch.randn(batch_size, 2)

        # Should raise RuntimeError due to dimension mismatch
        with pytest.raises(RuntimeError):
            encoder(actions_v1)

    def test_action_encoder_v1_compatibility(self):
        """Test encoder still works with v1 dimensions (action_dim=2)"""
        # V1: action_dim=2 (weather only, no temporal features)
        encoder = ActionEncoder(action_dim=2)

        batch_size = 8
        actions_v1 = torch.randn(batch_size, 2)  # [rain_anom, temp_anom]

        embeddings = encoder(actions_v1)

        # Should work correctly
        assert embeddings.shape == (batch_size, 128)

    def test_action_encoder_default_params(self):
        """Verify default parameters match v2 schema"""
        encoder = ActionEncoder()  # Use defaults

        # Default action_dim should be 4 (v2)
        assert encoder.action_dim == 4, (
            f"Default action_dim should be 4 (v2), got {encoder.action_dim}"
        )

        # Default output_dim should be 128
        assert encoder.output_dim == 128

    def test_action_encoder_gradient_flow(self):
        """Verify gradients flow correctly through encoder"""
        encoder = ActionEncoder(action_dim=4)

        actions = torch.randn(4, 4, requires_grad=True)
        embeddings = encoder(actions)

        # Compute dummy loss and backprop
        loss = embeddings.sum()
        loss.backward()

        # Gradients should exist for input
        assert actions.grad is not None
        assert not torch.isnan(actions.grad).any()

    def test_action_encoder_output_range(self):
        """Verify output embeddings have reasonable magnitude (not collapsed)"""
        encoder = ActionEncoder(action_dim=4)

        # Random actions
        actions = torch.randn(16, 4)
        embeddings = encoder(actions)

        # After SiLU activations, embeddings should not all be zero
        assert embeddings.abs().mean() > 0.01, (
            "Embeddings appear to be collapsed (too close to zero)"
        )

        # Should not have extreme values
        assert embeddings.abs().max() < 100, (
            "Embeddings have unreasonably large values"
        )

    def test_action_encoder_batch_independence(self):
        """Verify batch samples are processed independently (no batch effects)"""
        encoder = ActionEncoder(action_dim=4)

        # Single sample
        action_single = torch.randn(1, 4)
        embedding_single = encoder(action_single)

        # Same sample in a batch
        action_batch = action_single.repeat(8, 1)
        embedding_batch = encoder(action_batch)

        # All batch embeddings should be identical to single embedding
        for i in range(8):
            assert torch.allclose(embedding_batch[i], embedding_single[0], atol=1e-6), (
                f"Batch sample {i} differs from single sample (batch effects detected)"
            )

    def test_action_encoder_temporal_features_zero(self):
        """Verify zero-initialized temporal features produce valid output"""
        encoder = ActionEncoder(action_dim=4)

        # Weather anomalies with zero temporal features
        # This simulates freshly-loaded v1 checkpoint in v2 model
        batch_size = 8
        actions = torch.zeros(batch_size, 4)
        actions[:, :2] = torch.randn(batch_size, 2)  # Only weather is non-zero
        # actions[:, 2:4] remain zero (temporal features)

        embeddings = encoder(actions)

        # Should produce valid embeddings (not NaN, not all zeros)
        assert not torch.isnan(embeddings).any()
        assert embeddings.abs().sum() > 0
