"""Baseline Module Demo

Demonstrates how to use the three baseline predictors:
1. Persistence baseline
2. Seasonal baseline
3. Linear extrapolation baseline

Usage:
    uv run python examples/baseline_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
from siad.detect.baselines import (
    PersistenceBaseline,
    SeasonalBaseline,
    LinearExtrapolationBaseline,
    compare_baseline_residuals,
    create_baseline_predictor
)


def demo_persistence():
    """Demo: Persistence baseline"""
    print("\n" + "=" * 60)
    print("DEMO 1: Persistence Baseline")
    print("=" * 60)
    print("Strategy: Predict no change (Z_t+1 = Z_t)")

    # Create baseline
    baseline = PersistenceBaseline()

    # Create mock context
    z_context = torch.randn(256, 512)
    print(f"\nContext shape: {z_context.shape}")

    # Predict 6 months ahead
    z_pred = baseline.predict(z_context, horizon=6)
    print(f"Prediction shape: {z_pred.shape}")

    # Verify all predictions are identical
    all_same = all(torch.allclose(z_pred[t], z_context) for t in range(6))
    print(f"All predictions identical to context: {all_same}")

    print("\nResult: Persistence baseline simply repeats the current state.")


def demo_seasonal():
    """Demo: Seasonal baseline"""
    print("\n" + "=" * 60)
    print("DEMO 2: Seasonal Baseline")
    print("=" * 60)
    print("Strategy: Predict same as last year (Z_t+1 = Z_t-12)")

    # Create baseline
    baseline = SeasonalBaseline()

    # Create mock historical data (from 12 months ago)
    z_context = torch.randn(256, 512)  # Current month (not used)
    z_historical = torch.randn(6, 256, 512)  # Data from 12 months ago
    print(f"\nHistorical data shape: {z_historical.shape}")

    # Predict using historical data
    z_pred = baseline.predict(z_context, horizon=6, z_historical=z_historical)
    print(f"Prediction shape: {z_pred.shape}")

    # Verify predictions match historical data
    matches = torch.allclose(z_pred, z_historical)
    print(f"Predictions match historical data: {matches}")

    print("\nResult: Seasonal baseline uses last year's observations.")


def demo_linear():
    """Demo: Linear extrapolation baseline"""
    print("\n" + "=" * 60)
    print("DEMO 3: Linear Extrapolation Baseline")
    print("=" * 60)
    print("Strategy: Extrapolate linear trend from recent months")

    # Create baseline with 3-month history
    baseline = LinearExtrapolationBaseline(history_length=3)

    # Create synthetic increasing trend
    print("\nCreating synthetic trend: 1.0 -> 2.0 -> 3.0 -> 4.0")
    z_history = torch.stack([
        torch.ones(256, 512) * 1.0,
        torch.ones(256, 512) * 2.0,
        torch.ones(256, 512) * 3.0,
    ])
    z_context = torch.ones(256, 512) * 4.0

    # Predict extrapolation
    z_pred = baseline.predict(z_context, horizon=6, z_history=z_history)
    print(f"Prediction shape: {z_pred.shape}")

    # Show predicted values
    print("\nExtrapolated values:")
    for t in range(6):
        mean_val = z_pred[t].mean().item()
        expected = 4.0 + (t + 1) * 1.0  # Slope = 1.0 per month
        print(f"  Month {t+1}: {mean_val:.2f} (expected: {expected:.2f})")

    print("\nResult: Linear baseline extrapolates the trend forward.")


def demo_comparison():
    """Demo: Compare baselines against world model"""
    print("\n" + "=" * 60)
    print("DEMO 4: Baseline Comparison")
    print("=" * 60)
    print("Compare world model predictions vs baselines")

    # Create mock predictions
    z_pred_wm = torch.randn(6, 256, 512)  # World model prediction
    z_pred_baseline = torch.randn(6, 256, 512)  # Baseline prediction
    z_actual = torch.randn(6, 256, 512)  # Actual observation

    # Compare
    result = compare_baseline_residuals(
        z_pred_wm,
        z_pred_baseline,
        z_actual,
        baseline_name="persistence"
    )

    print(f"\nComparison results:")
    print(f"  Baseline: {result['baseline_name']}")
    print(f"  Horizon: {result['horizon']} months")
    print(f"  Mean improvement: {result['improvement_pct']:.1f}%")
    print(f"  World model outperforms: {result['outperforms']}")

    print("\nPer-timestep residuals:")
    for t in range(result['horizon']):
        wm = result['residual_wm'][t]
        bl = result['residual_baseline'][t]
        imp = result['improvement'][t] * 100
        print(f"  Month {t+1}: WM={wm:.3f}, Baseline={bl:.3f}, Improvement={imp:+.1f}%")

    print("\nResult: Comparison shows which predictor performs better.")


def demo_factory():
    """Demo: Factory function for creating baselines"""
    print("\n" + "=" * 60)
    print("DEMO 5: Factory Pattern")
    print("=" * 60)
    print("Use factory function to create baselines")

    # Create different baselines using factory
    baseline_types = ["persistence", "seasonal", "linear"]

    for baseline_type in baseline_types:
        baseline = create_baseline_predictor(baseline_type)
        print(f"\nCreated {baseline_type} baseline: {type(baseline).__name__}")

    print("\nResult: Factory simplifies baseline creation.")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("SIAD BASELINE MODULE DEMO")
    print("=" * 60)
    print("\nThis demo shows how to use the three baseline predictors:")
    print("1. Persistence: Predict no change")
    print("2. Seasonal: Predict same as last year")
    print("3. Linear: Extrapolate linear trend")

    demo_persistence()
    demo_seasonal()
    demo_linear()
    demo_comparison()
    demo_factory()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("- Use baselines to compare world model performance")
    print("- Store baseline residuals in HDF5 (see Task 2)")
    print("- Integrate with detection pipeline (see Task 3)")


if __name__ == "__main__":
    main()
