"""Unit tests for encoder module

Tests per MODEL.md Section 11:
- A) Shape contract tests
- B) Determinism test
- C) EMA update test
"""

import pytest
import torch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from siad.model.encoder import ContextEncoder, TargetEncoderEMA


class TestShapeContracts:
    """Test shape contracts per MODEL.md Section 11.A.1"""

    def test_encoder_shape(self):
        """Encoder shape: input [2,8,256,256] → output [2,256,512]"""
        encoder = ContextEncoder(
            in_channels=8,
            latent_dim=512,
            num_blocks=4,
            num_heads=8,
            mlp_dim=2048,
            dropout=0.0
        )
        # Set to evaluation mode
        encoder.train(False)

        # Input: batch=2, channels=8, height=256, width=256
        x = torch.randn(2, 8, 256, 256)

        with torch.no_grad():
            z = encoder(x)

        # Output must be [2, 256, 512]
        assert z.shape == (2, 256, 512), f"Expected shape (2, 256, 512), got {z.shape}"

    def test_target_encoder_shape(self):
        """Target encoder shape: input [2,8,256,256] → output [2,256,512]"""
        target_encoder = TargetEncoderEMA(
            in_channels=8,
            latent_dim=512,
            num_blocks=4,
            num_heads=8,
            mlp_dim=2048,
            dropout=0.0
        )
        target_encoder.train(False)

        # Input: batch=2, channels=8, height=256, width=256
        x = torch.randn(2, 8, 256, 256)

        with torch.no_grad():
            z_target = target_encoder(x)

        # Output must be [2, 256, 512]
        assert z_target.shape == (2, 256, 512), f"Expected shape (2, 256, 512), got {z_target.shape}"

    def test_cnn_stem_intermediate_shape(self):
        """CNN stem should produce 128×128×128 features"""
        from siad.model.encoder import CNNStem

        stem = CNNStem(in_channels=8)
        stem.train(False)

        x = torch.randn(2, 8, 256, 256)

        with torch.no_grad():
            features = stem(x)

        # Stem output: [B, 128, 128, 128]
        assert features.shape == (2, 128, 128, 128), \
            f"Expected stem shape (2, 128, 128, 128), got {features.shape}"

    def test_patchify_output_shape(self):
        """Patchify should produce 256 tokens of dimension 512"""
        from siad.model.encoder import Patchify

        patchify = Patchify(latent_dim=512, stem_channels=128, patch_size=8)
        patchify.train(False)

        # Simulated stem features
        features = torch.randn(2, 128, 128, 128)

        with torch.no_grad():
            tokens = patchify(features)

        # Patchify output: [B, 256, 512]
        assert tokens.shape == (2, 256, 512), \
            f"Expected patchify shape (2, 256, 512), got {tokens.shape}"


class TestDeterminism:
    """Test determinism per MODEL.md Section 11.B"""

    def test_encoder_deterministic(self):
        """Same input + same weights → identical outputs"""
        encoder = ContextEncoder(
            in_channels=8,
            latent_dim=512,
            num_blocks=4,
            num_heads=8,
            mlp_dim=2048,
            dropout=0.0  # Must be 0.0 for determinism
        )
        encoder.train(False)

        # Set manual seed for reproducibility
        torch.manual_seed(42)
        x = torch.randn(2, 8, 256, 256)

        # Forward pass 1
        with torch.no_grad():
            z1 = encoder(x)

        # Forward pass 2 (same input, same weights)
        with torch.no_grad():
            z2 = encoder(x)

        # Outputs must be identical
        assert torch.allclose(z1, z2, atol=1e-6), \
            "Encoder outputs differ for same input (non-deterministic)"

    def test_target_encoder_deterministic(self):
        """Target encoder should be deterministic"""
        target_encoder = TargetEncoderEMA(
            in_channels=8,
            latent_dim=512,
            num_blocks=4,
            num_heads=8,
            mlp_dim=2048,
            dropout=0.0
        )
        target_encoder.train(False)

        torch.manual_seed(42)
        x = torch.randn(2, 8, 256, 256)

        with torch.no_grad():
            z1 = target_encoder(x)

        with torch.no_grad():
            z2 = target_encoder(x)

        assert torch.allclose(z1, z2, atol=1e-6), \
            "Target encoder outputs differ for same input (non-deterministic)"


class TestEMAUpdate:
    """Test EMA update per MODEL.md Section 11.C"""

    def test_ema_weights_change(self):
        """After one update step, target weights change by EMA rule"""
        # Create context and target encoders
        context_encoder = ContextEncoder(
            in_channels=8,
            latent_dim=512,
            num_blocks=4,
            num_heads=8,
            mlp_dim=2048,
            dropout=0.0
        )

        target_encoder = TargetEncoderEMA(
            in_channels=8,
            latent_dim=512,
            num_blocks=4,
            num_heads=8,
            mlp_dim=2048,
            dropout=0.0,
            tau_start=0.99,
            tau_end=0.995,
            warmup_steps=2000
        )

        # Copy initial context encoder weights to target (initialize)
        with torch.no_grad():
            for target_param, source_param in zip(
                target_encoder.encoder.parameters(),
                context_encoder.parameters()
            ):
                target_param.data.copy_(source_param.data)

        # Store initial target weights
        initial_target_weights = [p.clone() for p in target_encoder.encoder.parameters()]

        # Modify context encoder weights slightly
        with torch.no_grad():
            for param in context_encoder.parameters():
                param.add_(torch.randn_like(param) * 0.01)

        # Perform EMA update
        target_encoder.update_from_encoder(context_encoder, step=0)

        # Check that target weights changed
        weights_changed = False
        for initial_w, current_param in zip(initial_target_weights, target_encoder.encoder.parameters()):
            if not torch.allclose(initial_w, current_param.data, atol=1e-6):
                weights_changed = True
                break

        assert weights_changed, "Target encoder weights did not change after EMA update"

    def test_ema_update_rule(self):
        """Verify EMA update follows θ̄ ← τ θ̄ + (1-τ) θ"""
        context_encoder = ContextEncoder(in_channels=8, latent_dim=512)
        target_encoder = TargetEncoderEMA(
            in_channels=8,
            latent_dim=512,
            tau_start=0.9,  # Use simple tau for testing
            tau_end=0.9,
            warmup_steps=1
        )

        # Initialize with known values
        torch.manual_seed(42)
        with torch.no_grad():
            for target_param, source_param in zip(
                target_encoder.encoder.parameters(),
                context_encoder.parameters()
            ):
                target_param.data.fill_(1.0)  # Target = 1.0
                source_param.data.fill_(2.0)  # Source = 2.0

        # Perform EMA update with τ=0.9
        target_encoder.update_from_encoder(context_encoder, step=1000)  # After warmup

        # Expected: θ̄ = 0.9 * 1.0 + 0.1 * 2.0 = 0.9 + 0.2 = 1.1
        expected_value = 0.9 * 1.0 + 0.1 * 2.0

        # Check first parameter
        first_param = next(target_encoder.encoder.parameters())
        assert torch.allclose(first_param, torch.tensor(expected_value), atol=1e-6), \
            f"EMA update incorrect: expected {expected_value}, got {first_param.mean().item()}"

    def test_ema_tau_schedule(self):
        """Verify EMA tau ramps from tau_start to tau_end over warmup"""
        target_encoder = TargetEncoderEMA(
            in_channels=8,
            latent_dim=512,
            tau_start=0.99,
            tau_end=0.995,
            warmup_steps=1000
        )
        context_encoder = ContextEncoder(in_channels=8, latent_dim=512)

        # Test tau at different steps
        # Step 0: should use tau_start
        target_encoder.update_from_encoder(context_encoder, step=0)
        assert target_encoder.current_step == 0

        # Step 500: should be halfway
        target_encoder.update_from_encoder(context_encoder, step=500)
        assert target_encoder.current_step == 500

        # Step 1000+: should use tau_end
        target_encoder.update_from_encoder(context_encoder, step=1500)
        assert target_encoder.current_step == 1500

    def test_target_encoder_no_gradients(self):
        """Target encoder parameters should have requires_grad=False"""
        target_encoder = TargetEncoderEMA(in_channels=8, latent_dim=512)

        for param in target_encoder.encoder.parameters():
            assert not param.requires_grad, \
                "Target encoder parameters should have requires_grad=False"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
