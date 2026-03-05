"""Unit tests for baseline predictors

Tests per AGENT_1_ARCHITECTURE.md Task 1:
- Persistence baseline: Z_pred = Z_context (no change)
- Seasonal baseline: Z_pred = Z_{t-12} (same as last year)
- Linear extrapolation baseline: Fit trend and extrapolate
"""

import pytest
import torch
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from siad.detect.baselines import (
    PersistenceBaseline,
    SeasonalBaseline,
    LinearExtrapolationBaseline,
    compare_baseline_residuals,
    compute_baseline_scores,
    create_baseline_predictor
)


class TestPersistenceBaseline:
    """Test persistence baseline: Z_pred = Z_context"""

    def test_persistence_single_sample(self):
        """Persistence repeats context for unbatched input"""
        baseline = PersistenceBaseline()

        z_context = torch.randn(256, 512)
        z_pred = baseline.predict(z_context, horizon=6)

        # Output shape should be [H, 256, 512]
        assert z_pred.shape == (6, 256, 512)

        # All timesteps should be identical to context
        for t in range(6):
            assert torch.allclose(z_pred[t], z_context), \
                f"Timestep {t} differs from context"

    def test_persistence_batched(self):
        """Persistence repeats context for batched input"""
        baseline = PersistenceBaseline()

        z_context = torch.randn(4, 256, 512)
        z_pred = baseline.predict(z_context, horizon=6)

        # Output shape should be [B, H, 256, 512]
        assert z_pred.shape == (4, 6, 256, 512)

        # Each sample's predictions should match its context
        for b in range(4):
            for t in range(6):
                assert torch.allclose(z_pred[b, t], z_context[b]), \
                    f"Batch {b}, timestep {t} differs from context"

    def test_persistence_varying_horizon(self):
        """Persistence works with different horizons"""
        baseline = PersistenceBaseline()

        z_context = torch.randn(256, 512)

        for horizon in [1, 3, 6, 12]:
            z_pred = baseline.predict(z_context, horizon=horizon)
            assert z_pred.shape == (horizon, 256, 512), \
                f"Wrong shape for horizon={horizon}"

            # All timesteps should be identical
            for t in range(horizon):
                assert torch.allclose(z_pred[t], z_context)

    def test_persistence_deterministic(self):
        """Persistence is deterministic"""
        baseline = PersistenceBaseline()

        z_context = torch.randn(256, 512)
        z_pred1 = baseline.predict(z_context, horizon=6)
        z_pred2 = baseline.predict(z_context, horizon=6)

        assert torch.allclose(z_pred1, z_pred2), \
            "Persistence baseline is non-deterministic"


class TestSeasonalBaseline:
    """Test seasonal baseline: Z_pred = Z_{t-12}"""

    def test_seasonal_with_preencoded_latents(self):
        """Seasonal baseline uses pre-encoded historical latents"""
        baseline = SeasonalBaseline()

        z_context = torch.randn(256, 512)  # Not used directly
        z_historical = torch.randn(6, 256, 512)  # Historical observations

        z_pred = baseline.predict(z_context, horizon=6, z_historical=z_historical)

        # Output should match historical data
        assert z_pred.shape == (6, 256, 512)
        assert torch.allclose(z_pred, z_historical), \
            "Seasonal baseline should return historical latents unchanged"

    def test_seasonal_batched(self):
        """Seasonal baseline works with batched inputs"""
        baseline = SeasonalBaseline()

        z_context = torch.randn(4, 256, 512)
        z_historical = torch.randn(4, 6, 256, 512)

        z_pred = baseline.predict(z_context, horizon=6, z_historical=z_historical)

        assert z_pred.shape == (4, 6, 256, 512)
        assert torch.allclose(z_pred, z_historical)

    def test_seasonal_requires_historical(self):
        """Seasonal baseline raises error without historical data"""
        baseline = SeasonalBaseline()

        z_context = torch.randn(256, 512)

        with pytest.raises(ValueError, match="requires z_historical"):
            baseline.predict(z_context, horizon=6, z_historical=None)

    def test_seasonal_horizon_mismatch(self):
        """Seasonal baseline validates horizon matches historical data"""
        baseline = SeasonalBaseline()

        z_context = torch.randn(256, 512)
        z_historical = torch.randn(3, 256, 512)  # Only 3 months

        with pytest.raises(AssertionError):
            baseline.predict(z_context, horizon=6, z_historical=z_historical)

    def test_seasonal_with_encoder(self):
        """Seasonal baseline can encode raw observations"""
        # Mock encoder
        class MockEncoder:
            def __call__(self, x):
                # Return dummy latents with correct shape
                if x.ndim == 4:
                    # [H, 8, 256, 256] -> [H, 256, 512]
                    H = x.shape[0]
                    return torch.randn(H, 256, 512)
                else:
                    # [B*H, 8, 256, 256] -> [B*H, 256, 512]
                    BH = x.shape[0]
                    return torch.randn(BH, 256, 512)

        encoder = MockEncoder()
        baseline = SeasonalBaseline(encoder=encoder)

        x_historical = torch.randn(6, 8, 256, 256)
        z_pred = baseline.predict_from_observations(x_historical, horizon=6)

        assert z_pred.shape == (6, 256, 512)

    def test_seasonal_encoder_batched(self):
        """Seasonal baseline handles batched observations"""
        class MockEncoder:
            def __call__(self, x):
                BH = x.shape[0]
                return torch.randn(BH, 256, 512)

        encoder = MockEncoder()
        baseline = SeasonalBaseline(encoder=encoder)

        x_historical = torch.randn(4, 6, 8, 256, 256)
        z_pred = baseline.predict_from_observations(x_historical, horizon=6)

        assert z_pred.shape == (4, 6, 256, 512)


class TestLinearExtrapolationBaseline:
    """Test linear extrapolation baseline"""

    def test_linear_with_history(self):
        """Linear baseline extrapolates trend from history"""
        baseline = LinearExtrapolationBaseline(history_length=3)

        # Create synthetic trend: increasing embeddings
        z_history = torch.stack([
            torch.ones(256, 512) * 1.0,
            torch.ones(256, 512) * 2.0,
            torch.ones(256, 512) * 3.0,
        ])  # [3, 256, 512]

        z_context = torch.ones(256, 512) * 4.0  # Continue trend

        z_pred = baseline.predict(z_context, horizon=6, z_history=z_history)

        # Output shape
        assert z_pred.shape == (6, 256, 512)

        # Predictions should continue linear trend
        # Slope = (4.0 - 1.0) / 3 = 1.0
        # So z_pred[0] should be ~5.0, z_pred[1] ~6.0, etc.
        for t in range(6):
            expected_value = 4.0 + (t + 1) * 1.0
            actual_value = z_pred[t].mean().item()
            assert abs(actual_value - expected_value) < 0.01, \
                f"Timestep {t}: expected {expected_value}, got {actual_value}"

    def test_linear_batched(self):
        """Linear baseline works with batched inputs"""
        baseline = LinearExtrapolationBaseline(history_length=2)

        z_history = torch.randn(4, 2, 256, 512)
        z_context = torch.randn(4, 256, 512)

        z_pred = baseline.predict(z_context, horizon=6, z_history=z_history)

        assert z_pred.shape == (4, 6, 256, 512)

    def test_linear_fallback_to_persistence(self):
        """Linear baseline falls back to persistence without history"""
        baseline = LinearExtrapolationBaseline(history_length=3)

        z_context = torch.randn(256, 512)
        z_pred = baseline.predict(z_context, horizon=6, z_history=None)

        # Should fall back to persistence
        assert z_pred.shape == (6, 256, 512)
        for t in range(6):
            assert torch.allclose(z_pred[t], z_context), \
                f"Without history, should use persistence at timestep {t}"

    def test_linear_insufficient_history(self):
        """Linear baseline falls back to persistence with insufficient history"""
        baseline = LinearExtrapolationBaseline(history_length=3)

        z_context = torch.randn(256, 512)
        z_history = torch.randn(1, 256, 512)  # Only 1 month (< 2 required)

        z_pred = baseline.predict(z_context, horizon=6, z_history=z_history)

        # Should fall back to persistence
        for t in range(6):
            assert torch.allclose(z_pred[t], z_context)

    def test_linear_deterministic(self):
        """Linear baseline is deterministic"""
        baseline = LinearExtrapolationBaseline(history_length=3)

        z_history = torch.randn(3, 256, 512)
        z_context = torch.randn(256, 512)

        z_pred1 = baseline.predict(z_context, horizon=6, z_history=z_history)
        z_pred2 = baseline.predict(z_context, horizon=6, z_history=z_history)

        assert torch.allclose(z_pred1, z_pred2)

    def test_linear_custom_history_length(self):
        """Linear baseline supports custom history length"""
        for K in [2, 3, 5]:
            baseline = LinearExtrapolationBaseline(history_length=K)

            z_history = torch.randn(K, 256, 512)
            z_context = torch.randn(256, 512)

            z_pred = baseline.predict(z_context, horizon=6, z_history=z_history)
            assert z_pred.shape == (6, 256, 512)


class TestBaselineComparison:
    """Test baseline comparison utilities"""

    def test_compare_baseline_residuals(self):
        """Compare world model vs baseline residuals"""
        # Create synthetic predictions
        z_pred_wm = torch.randn(6, 256, 512)
        z_pred_baseline = torch.randn(6, 256, 512)
        z_actual = torch.randn(6, 256, 512)

        result = compare_baseline_residuals(
            z_pred_wm,
            z_pred_baseline,
            z_actual,
            baseline_name="persistence"
        )

        # Check result structure
        assert 'residual_wm' in result
        assert 'residual_baseline' in result
        assert 'improvement' in result
        assert 'mean_improvement' in result
        assert 'outperforms' in result
        assert 'baseline_name' in result

        # Check shapes
        assert len(result['residual_wm']) == 6
        assert len(result['residual_baseline']) == 6
        assert len(result['improvement']) == 6

        # Check values are reasonable
        assert all(r >= 0 for r in result['residual_wm'])
        assert all(r >= 0 for r in result['residual_baseline'])
        assert isinstance(result['outperforms'], bool)

    def test_compare_batched(self):
        """Comparison works with batched inputs"""
        z_pred_wm = torch.randn(4, 6, 256, 512)
        z_pred_baseline = torch.randn(4, 6, 256, 512)
        z_actual = torch.randn(4, 6, 256, 512)

        result = compare_baseline_residuals(
            z_pred_wm,
            z_pred_baseline,
            z_actual
        )

        assert len(result['residual_wm']) == 6

    def test_compare_shape_mismatch(self):
        """Comparison raises error on shape mismatch"""
        z_pred_wm = torch.randn(6, 256, 512)
        z_pred_baseline = torch.randn(3, 256, 512)  # Wrong horizon
        z_actual = torch.randn(6, 256, 512)

        with pytest.raises(AssertionError, match="Shape mismatch"):
            compare_baseline_residuals(z_pred_wm, z_pred_baseline, z_actual)

    def test_compute_baseline_scores(self):
        """Compute tile scores for baseline predictions"""
        z_pred_baseline = torch.randn(6, 256, 512)
        z_actual = torch.randn(6, 256, 512)

        scores = compute_baseline_scores(z_pred_baseline, z_actual, top_k_pct=0.10)

        # Check shape and values
        assert scores.shape == (6,)
        assert all(s >= 0 for s in scores)

    def test_compute_scores_batched(self):
        """Baseline scores work with batched inputs"""
        z_pred_baseline = torch.randn(4, 6, 256, 512)
        z_actual = torch.randn(4, 6, 256, 512)

        scores = compute_baseline_scores(z_pred_baseline, z_actual)

        assert scores.shape == (6,)


class TestBaselineFactory:
    """Test baseline factory function"""

    def test_create_persistence(self):
        """Factory creates persistence baseline"""
        baseline = create_baseline_predictor("persistence")
        assert isinstance(baseline, PersistenceBaseline)

    def test_create_seasonal(self):
        """Factory creates seasonal baseline"""
        baseline = create_baseline_predictor("seasonal")
        assert isinstance(baseline, SeasonalBaseline)

    def test_create_linear(self):
        """Factory creates linear baseline"""
        baseline = create_baseline_predictor("linear")
        assert isinstance(baseline, LinearExtrapolationBaseline)

    def test_create_linear_custom_history(self):
        """Factory respects custom history length"""
        baseline = create_baseline_predictor("linear", history_length=5)
        assert isinstance(baseline, LinearExtrapolationBaseline)
        assert baseline.history_length == 5

    def test_create_unknown_type(self):
        """Factory raises error for unknown baseline type"""
        with pytest.raises(ValueError, match="Unknown baseline_type"):
            create_baseline_predictor("unknown")


class TestBaselineIntegration:
    """Integration tests combining multiple baselines"""

    def test_all_baselines_same_input(self):
        """All baselines produce valid outputs for same input"""
        z_context = torch.randn(256, 512)
        z_history = torch.randn(3, 256, 512)
        z_historical = torch.randn(6, 256, 512)

        # Persistence
        persistence = PersistenceBaseline()
        z_pred_pers = persistence.predict(z_context, horizon=6)
        assert z_pred_pers.shape == (6, 256, 512)

        # Seasonal
        seasonal = SeasonalBaseline()
        z_pred_seas = seasonal.predict(z_context, horizon=6, z_historical=z_historical)
        assert z_pred_seas.shape == (6, 256, 512)

        # Linear
        linear = LinearExtrapolationBaseline(history_length=3)
        z_pred_lin = linear.predict(z_context, horizon=6, z_history=z_history)
        assert z_pred_lin.shape == (6, 256, 512)

    def test_baseline_diversity(self):
        """Different baselines produce different predictions"""
        # Create trend data
        z_history = torch.stack([
            torch.ones(256, 512) * 1.0,
            torch.ones(256, 512) * 2.0,
            torch.ones(256, 512) * 3.0,
        ])
        z_context = torch.ones(256, 512) * 4.0
        z_historical = torch.ones(6, 256, 512) * 10.0  # Different values

        persistence = PersistenceBaseline()
        seasonal = SeasonalBaseline()
        linear = LinearExtrapolationBaseline(history_length=3)

        z_pred_pers = persistence.predict(z_context, horizon=6)
        z_pred_seas = seasonal.predict(z_context, horizon=6, z_historical=z_historical)
        z_pred_lin = linear.predict(z_context, horizon=6, z_history=z_history)

        # All should be different
        assert not torch.allclose(z_pred_pers, z_pred_seas)
        assert not torch.allclose(z_pred_pers, z_pred_lin)
        assert not torch.allclose(z_pred_seas, z_pred_lin)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
