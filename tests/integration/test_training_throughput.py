"""Integration tests for training efficiency (User Story 3)

Tests performance metrics per contracts to ensure temporal features don't
significantly impact training throughput or model size.

Acceptance Criteria:
- Training throughput decreases by <5%
- Model parameter count remains effectively unchanged
"""

import pytest
import torch
import time
from datetime import datetime

from siad.model.wm import WorldModel
from siad.data.preprocessing import compute_temporal_features


class TestModelParameterCount:
    """Test that temporal features add minimal parameters (US3)"""

    @pytest.mark.integration
    def test_model_parameter_count(self):
        """Verify parameter count increase is minimal (<0.01% of total)"""
        # Create v1 model (baseline)
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)

        # Create v2 model (temporal)
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        # Count parameters
        def count_params(model):
            return sum(p.numel() for p in model.parameters())

        params_v1 = count_params(model_v1)
        params_v2 = count_params(model_v2)

        # Calculate increase
        param_increase = params_v2 - params_v1
        percent_increase = (param_increase / params_v1) * 100

        print(f"\nParameter count:")
        print(f"  V1 (baseline): {params_v1:,} parameters")
        print(f"  V2 (temporal): {params_v2:,} parameters")
        print(f"  Increase: {param_increase:,} parameters ({percent_increase:.4f}%)")

        # Verify increase is exactly from action encoder first layer
        # Linear(2→64) has 2*64 = 128 params
        # Linear(4→64) has 4*64 = 256 params
        # Difference: 256 - 128 = 128 params
        expected_increase = 128  # 2 extra input dims × 64 hidden units
        assert param_increase == expected_increase, (
            f"Expected exactly {expected_increase} parameter increase, got {param_increase}"
        )

        # Verify total increase is negligible (<0.01%)
        assert percent_increase < 0.01, (
            f"Parameter increase {percent_increase:.4f}% exceeds 0.01% threshold"
        )

    @pytest.mark.integration
    def test_action_encoder_parameter_breakdown(self):
        """Verify parameter increase is isolated to action encoder"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        # Check encoder parameters (should be identical)
        encoder_params_v1 = sum(p.numel() for p in model_v1.context_encoder.parameters())
        encoder_params_v2 = sum(p.numel() for p in model_v2.context_encoder.parameters())

        assert encoder_params_v1 == encoder_params_v2, (
            "Context encoder parameters should be unchanged"
        )

        # Check transition parameters (should be identical)
        transition_params_v1 = sum(p.numel() for p in model_v1.transition_model.parameters())
        transition_params_v2 = sum(p.numel() for p in model_v2.transition_model.parameters())

        assert transition_params_v1 == transition_params_v2, (
            "Transition model parameters should be unchanged"
        )

        # Only action encoder should differ
        action_params_v1 = sum(p.numel() for p in model_v1.action_encoder.parameters())
        action_params_v2 = sum(p.numel() for p in model_v2.action_encoder.parameters())

        assert action_params_v2 > action_params_v1, (
            "Action encoder should have more parameters in v2"
        )


class TestTrainingThroughput:
    """Test that training throughput degradation is minimal (<5%)"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_training_throughput_v1_vs_v2(self):
        """Compare training throughput between v1 and v2 models

        Measures samples/second for small training loop to verify <5% degradation.
        """
        # Create models
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        # Create dummy data
        batch_size = 8
        num_batches = 20  # Small number for quick test
        H = 6

        # Prepare batches
        batches_v1 = []
        batches_v2 = []

        for _ in range(num_batches):
            # Observations
            x_context = torch.randn(batch_size, 8, 256, 256)
            x_targets = torch.randn(batch_size, H, 8, 256, 256)

            # Actions v1 (weather only)
            actions_v1 = torch.randn(batch_size, H, 2)

            # Actions v2 (weather + temporal)
            actions_v2 = torch.zeros(batch_size, H, 4)
            actions_v2[:, :, :2] = actions_v1  # Same weather
            # Add temporal features
            for b in range(batch_size):
                for h in range(H):
                    month = (h % 12) + 1
                    timestamp = datetime(2025, month, 15)
                    month_sin, month_cos = compute_temporal_features(timestamp)
                    actions_v2[b, h, 2] = month_sin
                    actions_v2[b, h, 3] = month_cos

            batches_v1.append((x_context, x_targets, actions_v1))
            batches_v2.append((x_context, x_targets, actions_v2))

        # Training loop helper
        def train_epoch(model, batches):
            model.train()
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

            start_time = time.time()

            for x_context, x_targets, actions in batches:
                # Forward pass
                z_context = model.encode(x_context)
                z_targets = model.encode_targets(x_targets[:, 0])  # First target
                z_pred = model.rollout(z_context, actions, H=H)

                # Dummy loss (just for throughput measurement)
                loss = (z_pred[:, 0] - z_targets).pow(2).mean()

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            elapsed = time.time() - start_time
            return elapsed

        # Warmup (not counted)
        train_epoch(model_v1, batches_v1[:2])
        train_epoch(model_v2, batches_v2[:2])

        # Measure v1 throughput
        time_v1 = train_epoch(model_v1, batches_v1)
        samples_v1 = batch_size * num_batches
        throughput_v1 = samples_v1 / time_v1

        # Measure v2 throughput
        time_v2 = train_epoch(model_v2, batches_v2)
        samples_v2 = batch_size * num_batches
        throughput_v2 = samples_v2 / time_v2

        # Calculate degradation
        degradation = (throughput_v1 - throughput_v2) / throughput_v1
        degradation_percent = degradation * 100

        print(f"\nThroughput comparison:")
        print(f"  V1 (baseline): {throughput_v1:.2f} samples/sec")
        print(f"  V2 (temporal): {throughput_v2:.2f} samples/sec")
        print(f"  Degradation: {degradation_percent:.2f}%")

        # Assert <5% degradation
        assert degradation < 0.05, (
            f"Throughput degradation {degradation_percent:.2f}% exceeds 5% threshold"
        )

    @pytest.mark.integration
    def test_forward_pass_latency(self):
        """Compare forward pass latency for action encoding"""
        model_v1 = WorldModel(action_dim=2, in_channels=8, latent_dim=512)
        model_v2 = WorldModel(action_dim=4, in_channels=8, latent_dim=512)

        model_v1.eval()
        model_v2.eval()

        batch_size = 32
        num_iterations = 100

        # Create inputs
        actions_v1 = torch.randn(batch_size, 2)
        actions_v2 = torch.randn(batch_size, 4)

        # Warmup
        with torch.no_grad():
            for _ in range(10):
                model_v1.action_encoder(actions_v1)
                model_v2.action_encoder(actions_v2)

        # Measure v1
        start = time.time()
        with torch.no_grad():
            for _ in range(num_iterations):
                model_v1.action_encoder(actions_v1)
        time_v1 = (time.time() - start) / num_iterations

        # Measure v2
        start = time.time()
        with torch.no_grad():
            for _ in range(num_iterations):
                model_v2.action_encoder(actions_v2)
        time_v2 = (time.time() - start) / num_iterations

        latency_increase = ((time_v2 - time_v1) / time_v1) * 100

        print(f"\nAction encoder latency:")
        print(f"  V1: {time_v1*1000:.3f} ms")
        print(f"  V2: {time_v2*1000:.3f} ms")
        print(f"  Increase: {latency_increase:.2f}%")

        # Latency increase should be minimal (linear layer is fast)
        assert latency_increase < 10, (
            f"Action encoder latency increased by {latency_increase:.2f}% (>10%)"
        )
