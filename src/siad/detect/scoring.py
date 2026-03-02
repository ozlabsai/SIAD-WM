"""
Acceleration score computation and percentile flagging.

Implements:
- Divergence-based acceleration scoring (EMA + slope formula)
- Tile-local percentile thresholding
"""

from typing import Optional

import numpy as np
import torch


def compute_acceleration_scores(
    rollout_engine,  # RolloutEngine instance
    tile_timeseries: dict,
    target_encoder: torch.nn.Module,
    ema_alpha: float = 0.2,
    slope_weight: float = 0.5,
    trend_window: int = 3,
) -> dict:
    """
    Compute per-tile acceleration scores via neutral scenario divergence.

    Formula:
        S_t = EMA(mean(divergence[1..6])) + lambda * slope(divergence[t-W:t])

    Args:
        rollout_engine: RolloutEngine for neutral scenario rollouts
        tile_timeseries: {
            tile_id: {
                "obs": [T, 8, 256, 256],  # Observations per month
                "actions": [T, 2]          # Actions per month
            }
        }
        target_encoder: EMA target encoder for observed latents
        ema_alpha: EMA decay parameter (default 0.2)
        slope_weight: Weight for slope term (lambda, default 0.5)
        trend_window: Window for slope computation (W, default 3 months)

    Returns:
        {
            tile_id: {
                "scores": [T],              # Acceleration score per month
                "divergences": [T, H=6],    # Divergence matrix
                "percentile_99": float       # Tile-local 99th percentile
            }
        }
    """
    rollout_horizon = rollout_engine.rollout_horizon
    context_length = rollout_engine.context_length

    results = {}

    for tile_id, data in tile_timeseries.items():
        obs = data["obs"]
        actions = data["actions"]
        T = len(obs)

        divergence_matrix = np.zeros((T, rollout_horizon), dtype=np.float32)
        scores = np.zeros(T, dtype=np.float32)

        # Compute divergences for each timestep
        for t in range(context_length, T - rollout_horizon):
            context_obs = obs[t - context_length : t]
            future_obs = obs[t : t + rollout_horizon]

            # Run neutral scenario rollout
            rollout_result = rollout_engine.rollout_neutral_scenario(
                context_obs=context_obs, target_obs=future_obs
            )

            divergence_matrix[t, :] = rollout_result["divergences"]

        # Compute acceleration scores
        for t in range(context_length + trend_window, T - rollout_horizon):
            # Mean divergence over rollout horizon
            mean_div = np.mean(divergence_matrix[t, :])

            # EMA of mean divergence
            if t == context_length + trend_window:
                ema_div = mean_div
            else:
                ema_div = ema_alpha * mean_div + (1 - ema_alpha) * scores[t - 1]

            # Slope of recent trend
            recent_divs = divergence_matrix[t - trend_window : t, :].mean(axis=1)
            slope = np.polyfit(range(trend_window), recent_divs, deg=1)[0]

            # Combined score
            scores[t] = ema_div + slope_weight * slope

        # Compute tile-local 99th percentile
        valid_scores = scores[scores > 0]  # Exclude zero-padded entries
        percentile_99 = (
            np.percentile(valid_scores, 99) if len(valid_scores) > 0 else 0.0
        )

        results[tile_id] = {
            "scores": scores,
            "divergences": divergence_matrix,
            "percentile_99": percentile_99,
        }

    return results


def flag_tiles_by_percentile(
    tile_scores: dict, threshold_percentile: float = 99.0
) -> dict:
    """
    Flag tiles where acceleration score exceeds tile-local percentile threshold.

    Args:
        tile_scores: {
            tile_id: {
                "scores": [T],
                "percentile_99": float
            }
        }
        threshold_percentile: Percentile threshold (default 99.0)

    Returns:
        {
            tile_id: {
                "flagged_months": [month_indices],
                "max_score": float
            }
        }
    """
    flagged = {}

    for tile_id, data in tile_scores.items():
        scores = data["scores"]
        threshold = data["percentile_99"]

        # Find months exceeding threshold
        flagged_indices = np.where(scores > threshold)[0].tolist()

        if flagged_indices:
            flagged[tile_id] = {
                "flagged_months": flagged_indices,
                "max_score": float(np.max(scores[flagged_indices])),
            }

    return flagged
