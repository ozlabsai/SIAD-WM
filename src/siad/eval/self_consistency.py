"""
Self-consistency validation.

Verifies that neutral scenario rollouts are more plausible than random actions.
Success criterion (SC-004): neutral_vs_random_ratio < 0.5
"""

import numpy as np


def test_neutral_vs_random(
    rollout_engine,
    tile_timeseries: dict,
    target_encoder,
    n_random_samples: int = 10,
    random_std: float = 1.0,
) -> dict:
    """
    Compare neutral scenario divergence vs random action divergence.

    For each tile:
    1. Compute divergence under neutral actions (zeros)
    2. Compute divergence under N random action sequences
    3. Compare: neutral_divergence / mean(random_divergences)

    Args:
        rollout_engine: RolloutEngine instance
        tile_timeseries: {tile_id: {"obs": [T, 8, H, W], "actions": [T, 2]}}
        target_encoder: EMA target encoder
        n_random_samples: Number of random action sequences per tile (default 10)
        random_std: Standard deviation for random actions (default 1.0)

    Returns:
        {
            "neutral_vs_random_divergence_ratio": float,  # Should be < 0.5
            "per_tile_ratios": {tile_id: ratio},
            "neutral_mean": float,
            "random_mean": float
        }
    """
    context_length = rollout_engine.context_length
    rollout_horizon = rollout_engine.rollout_horizon

    tile_ratios = {}
    all_neutral_divs = []
    all_random_divs = []

    for tile_id, data in tile_timeseries.items():
        obs = data["obs"]
        T = len(obs)

        if T < context_length + rollout_horizon:
            continue

        # Use middle timestep for test
        t = T // 2
        context_obs = obs[t - context_length : t]
        future_obs = obs[t : t + rollout_horizon]

        # Neutral scenario
        neutral_result = rollout_engine.rollout_neutral_scenario(
            context_obs=context_obs, target_obs=future_obs
        )
        neutral_div = np.mean(neutral_result["divergences"])
        all_neutral_divs.append(neutral_div)

        # Random scenarios
        random_divs = []
        for _ in range(n_random_samples):
            random_actions = np.random.normal(0, random_std, size=(rollout_horizon, 2))
            random_result = rollout_engine.rollout(
                context_obs=context_obs,
                actions=random_actions,
                target_obs=future_obs,
                return_latents=False,
            )
            random_div = np.mean(random_result["divergences"])
            random_divs.append(random_div)
            all_random_divs.append(random_div)

        # Compute ratio
        mean_random_div = np.mean(random_divs)
        ratio = neutral_div / (mean_random_div + 1e-8)
        tile_ratios[tile_id] = float(ratio)

    # Aggregate across tiles
    overall_neutral = np.mean(all_neutral_divs) if all_neutral_divs else 0.0
    overall_random = np.mean(all_random_divs) if all_random_divs else 0.0
    overall_ratio = overall_neutral / (overall_random + 1e-8)

    return {
        "neutral_vs_random_divergence_ratio": float(overall_ratio),
        "per_tile_ratios": tile_ratios,
        "neutral_mean": float(overall_neutral),
        "random_mean": float(overall_random),
    }
