"""
Validation suite for SIAD MVP.

Implements three-gate validation per Constitution Principle III:
1. Self-consistency: Neutral vs random scenario validation
2. Backtest: Known construction regions hit rate
3. False-positive: Agriculture/monsoon regions FP rate
"""

from .self_consistency import test_neutral_vs_random
from .backtest import backtest_known_sites
from .false_positive import test_false_positive_rate

__all__ = [
    "test_neutral_vs_random",
    "backtest_known_sites",
    "test_false_positive_rate",
]


def aggregate_validation_metrics(
    self_consistency_result: dict,
    backtest_result: dict,
    false_positive_result: dict,
    checkpoint_path: str,
) -> dict:
    """
    Aggregate validation results into summary JSON.

    Args:
        self_consistency_result: Result from test_neutral_vs_random
        backtest_result: Result from backtest_known_sites
        false_positive_result: Result from test_false_positive_rate
        checkpoint_path: Path to model checkpoint being validated

    Returns:
        {
            "timestamp": ISO 8601 timestamp,
            "checkpoint_path": str,
            "self_consistency": {..., "pass": bool},
            "backtest": {..., "pass": bool},
            "false_positive": {..., "pass": bool},
            "overall_pass": bool
        }
    """
    from datetime import datetime

    # Success criteria per spec
    sc_pass = (
        self_consistency_result.get("neutral_vs_random_divergence_ratio", 1.0) < 0.5
    )
    backtest_pass = backtest_result.get("hit_rate", 0.0) >= 0.80
    fp_pass = false_positive_result.get("fp_rate", 1.0) < 0.20

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checkpoint_path": checkpoint_path,
        "self_consistency": {**self_consistency_result, "pass": sc_pass},
        "backtest": {**backtest_result, "pass": backtest_pass},
        "false_positive": {**false_positive_result, "pass": fp_pass},
        "overall_pass": sc_pass and backtest_pass and fp_pass,
    }
