"""Unit tests for VC-Reg anti-collapse loss

Tests the core VC-Reg implementation (variance + covariance penalties)
per spec.md M3.1 and research.md Q1.
"""

import pytest
import torch
import torch.nn.functional as F
from siad.train.losses import vcreg_loss


class TestVCRegLoss:
    """Test suite for vcreg_loss() function"""

    def test_variance_penalty_low_variance(self):
        """Test variance penalty activates with low-variance input"""
        # Create low-variance input: all tokens nearly identical
        B, N, D = 4, 256, 512
        z = torch.ones(B, N, D) * 0.5 + torch.randn(B, N, D) * 0.01

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=0.0, eps=1e-4)

        # With low variance, var_loss should be > 0
        assert metrics["ac/var_loss"] > 0.0, "Variance penalty should activate for low-variance input"
        assert metrics["ac/std_mean"] < 1.0, "Mean std should be less than gamma threshold"

        # With beta=0, total loss should equal alpha * var_loss
        expected_total = 25.0 * metrics["ac/var_loss"]
        assert abs(metrics["ac/total"] - expected_total) < 1e-5

    def test_variance_penalty_high_variance(self):
        """Test variance penalty is minimal with high-variance input"""
        # Create high-variance input: diverse random values
        B, N, D = 4, 256, 512
        z = torch.randn(B, N, D) * 2.0  # std ~2.0 >> gamma=1.0

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=0.0, eps=1e-4)

        # With high variance, var_loss should be ~0
        assert metrics["ac/var_loss"] < 0.1, "Variance penalty should be minimal for high-variance input"
        assert metrics["ac/std_mean"] > 1.0, "Mean std should exceed gamma threshold"

    def test_covariance_penalty_correlated_dims(self):
        """Test covariance penalty with correlated dimensions"""
        # Create input with highly correlated dimensions
        B, N, D = 4, 256, 128
        base = torch.randn(B * N, 1)  # Single random vector
        z_flat = base.repeat(1, D) + torch.randn(B * N, D) * 0.1  # Correlated copies
        z = z_flat.reshape(B, N, D)

        loss, metrics = vcreg_loss(z, gamma=0.0, alpha=0.0, beta=1.0, eps=1e-4)

        # With correlated dims, cov_loss should be > 0
        assert metrics["ac/cov_loss"] > 0.0, "Covariance penalty should activate for correlated dimensions"

        # With alpha=0, total loss should equal beta * cov_loss
        expected_total = 1.0 * metrics["ac/cov_loss"]
        assert abs(metrics["ac/total"] - expected_total) < 1e-5

    def test_covariance_penalty_uncorrelated_dims(self):
        """Test covariance penalty is minimal with uncorrelated dimensions"""
        # Create input with independent random dimensions
        B, N, D = 4, 256, 128
        z = torch.randn(B, N, D)

        loss, metrics = vcreg_loss(z, gamma=0.0, alpha=0.0, beta=1.0, eps=1e-4)

        # With uncorrelated dims, cov_loss should be low (not exactly 0 due to sampling)
        assert metrics["ac/cov_loss"] < 0.5, "Covariance penalty should be minimal for uncorrelated dimensions"

    def test_combined_loss(self):
        """Test combined variance + covariance loss computation"""
        # Create input with moderate variance and correlation
        B, N, D = 4, 256, 128
        z = torch.randn(B, N, D) * 0.8  # Moderate variance

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4)

        # Total loss should equal alpha * var_loss + beta * cov_loss
        expected_total = 25.0 * metrics["ac/var_loss"] + 1.0 * metrics["ac/cov_loss"]
        assert abs(metrics["ac/total"] - expected_total) < 1e-5

        # Both penalties should contribute (input has moderate properties)
        assert metrics["ac/var_loss"] >= 0.0
        assert metrics["ac/cov_loss"] >= 0.0

    def test_metrics_structure(self):
        """Test metrics dictionary has all required keys"""
        B, N, D = 4, 256, 512
        z = torch.randn(B, N, D)

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4)

        # Check all required metrics are present
        required_keys = {
            "ac/var_loss",
            "ac/cov_loss",
            "ac/total",
            "ac/std_mean",
            "ac/std_min",
            "ac/std_max",
            "ac/dead_dims_frac",
        }
        assert set(metrics.keys()) == required_keys, f"Missing metrics: {required_keys - set(metrics.keys())}"

        # All metrics should be Python floats (not tensors)
        for key, value in metrics.items():
            assert isinstance(value, float), f"Metric {key} should be float, got {type(value)}"

    def test_dead_dims_tracking(self):
        """Test dead dimensions fraction tracking"""
        # Create input with some dead dimensions (low std)
        B, N, D = 4, 256, 100
        z = torch.randn(B, N, D)

        # Make first 10 dimensions have very low variance
        z[:, :, :10] = torch.ones(B, N, 10) * 0.5

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4)

        # Should detect ~10% dead dimensions
        assert metrics["ac/dead_dims_frac"] > 0.05, "Should detect dead dimensions"
        assert metrics["ac/dead_dims_frac"] < 0.15, "Dead dims fraction should be around 10%"

    def test_4d_input_handling(self):
        """Test vcreg_loss handles 4D input [B, H, N, D] (with horizon)"""
        # Create 4D input (e.g., from predictions with rollout horizon)
        B, H, N, D = 4, 6, 256, 512
        z = torch.randn(B, H, N, D)

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4)

        # Should work without errors
        assert isinstance(loss, torch.Tensor)
        assert loss.ndim == 0  # Scalar loss
        assert "ac/total" in metrics

    def test_3d_input_handling(self):
        """Test vcreg_loss handles 3D input [B, N, D] (encoder outputs)"""
        # Create 3D input (standard encoder outputs)
        B, N, D = 4, 256, 512
        z = torch.randn(B, N, D)

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4)

        # Should work without errors
        assert isinstance(loss, torch.Tensor)
        assert loss.ndim == 0  # Scalar loss
        assert "ac/total" in metrics

    def test_numerical_stability(self):
        """Test numerical stability with zero variance input"""
        # Create constant input (zero variance edge case)
        B, N, D = 4, 256, 128
        z = torch.ones(B, N, D) * 5.0

        loss, metrics = vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4)

        # Should not NaN or Inf
        assert torch.isfinite(loss), "Loss should be finite even with zero variance"
        assert all(not (v != v or abs(v) == float('inf')) for v in metrics.values()), "All metrics should be finite"

        # Variance loss should be maximal (gamma penalty on all dims)
        assert metrics["ac/var_loss"] > 0.5, "Variance penalty should be high for constant input"

    def test_default_parameters(self):
        """Test vcreg_loss with default parameters"""
        B, N, D = 4, 256, 512
        z = torch.randn(B, N, D)

        # Call with defaults: gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4
        loss, metrics = vcreg_loss(z)

        # Should execute without errors
        assert isinstance(loss, torch.Tensor)
        assert "ac/total" in metrics
