"""
Modality attribution and hotspot classification.

Decomposes acceleration scores by SAR/optical/lights contribution
to assign confidence tiers (Structural/Activity/Environmental).
"""

from typing import List

import numpy as np

# Band order per CONTRACTS.md Section 1
BAND_ORDER_V1 = [
    "S2_B2",  # 0
    "S2_G",  # 1
    "S2_B4",  # 2
    "S2_B8",  # 3
    "S1_VV",  # 4
    "S1_VH",  # 5
    "VIIRS_avg_rad",  # 6
    "S2_valid_mask",  # 7
]

# Modality channel masks
MODALITY_MASKS = {
    "sar": [4, 5],  # S1_VV, S1_VH
    "optical": [0, 1, 2, 3],  # S2_B2, S2_B3, S2_B4, S2_B8
    "lights": [6],  # VIIRS_avg_rad
}


def apply_mask(obs: np.ndarray, mask_channels: List[int]) -> np.ndarray:
    """
    Zero out all channels except those in mask_channels.

    Args:
        obs: Observation array [T, C=8, H, W] or [C=8, H, W]
        mask_channels: List of channel indices to retain

    Returns:
        Masked observation with same shape
    """
    masked_obs = np.zeros_like(obs)

    # Handle both 3D and 4D arrays
    if obs.ndim == 4:
        masked_obs[:, mask_channels, :, :] = obs[:, mask_channels, :, :]
    elif obs.ndim == 3:
        masked_obs[mask_channels, :, :] = obs[mask_channels, :, :]
    else:
        raise ValueError(f"Unexpected obs shape: {obs.shape}")

    return masked_obs


def normalize_contributions(divergences: dict) -> dict:
    """
    Normalize contributions to sum to 1.0.

    Args:
        divergences: {modality: mean_divergence}

    Returns:
        {modality: normalized_contribution}
    """
    total = sum(divergences.values()) + 1e-8  # Avoid division by zero
    return {k: v / total for k, v in divergences.items()}


def classify_hotspot(attribution: dict) -> str:
    """
    Assign confidence tier based on dominant modality.

    Rules:
    - Structural: sar_contribution > 0.5 OR (sar > 0.3 AND lights > 0.2)
    - Activity: lights_contribution > 0.5 AND sar < 0.3
    - Environmental: optical_contribution > 0.5

    Args:
        attribution: {
            "sar_contribution": float,
            "optical_contribution": float,
            "lights_contribution": float
        }

    Returns:
        "Structural" | "Activity" | "Environmental"
    """
    sar = attribution["sar_contribution"]
    optical = attribution["optical_contribution"]
    lights = attribution["lights_contribution"]

    if sar > 0.5 or (sar > 0.3 and lights > 0.2):
        return "Structural"
    elif lights > 0.5 and sar < 0.3:
        return "Activity"
    else:
        return "Environmental"


def compute_modality_attribution(
    rollout_engine,
    tile_timeseries: dict,
    target_encoder,
    hotspots: List[dict],
) -> List[dict]:
    """
    Compute modality-specific attribution for each hotspot.

    Re-runs rollouts with masked inputs (SAR-only, optical-only, lights-only)
    and compares divergences to assign attribution contributions.

    Args:
        rollout_engine: RolloutEngine instance
        tile_timeseries: {tile_id: {"obs": [T, 8, H, W], "actions": [T, 2]}}
        target_encoder: EMA target encoder
        hotspots: List of hotspot dicts from clustering

    Returns:
        Updated hotspots with "attribution" and "confidence_tier" fields
    """
    updated_hotspots = []

    for hotspot in hotspots:
        tile_ids = hotspot["tile_ids"]

        # Aggregate divergences across tiles in hotspot
        modality_divergences = {"sar": 0.0, "optical": 0.0, "lights": 0.0}

        for tile_id in tile_ids:
            if tile_id not in tile_timeseries:
                continue

            data = tile_timeseries[tile_id]
            obs = data["obs"]
            actions = data["actions"]

            # Use middle timestep for rollout (TODO: make configurable)
            T = len(obs)
            t = T // 2
            context_length = rollout_engine.context_length
            rollout_horizon = rollout_engine.rollout_horizon

            if t < context_length or t + rollout_horizon >= T:
                continue

            context_obs = obs[t - context_length : t]
            future_obs = obs[t : t + rollout_horizon]

            # Run modality-specific rollouts
            for modality, channels in MODALITY_MASKS.items():
                masked_context = apply_mask(context_obs, channels)
                masked_future = apply_mask(future_obs, channels)

                # Run neutral scenario rollout with masked inputs
                rollout_result = rollout_engine.rollout_neutral_scenario(
                    context_obs=masked_context, target_obs=masked_future
                )

                mean_divergence = np.mean(rollout_result["divergences"])
                modality_divergences[modality] += mean_divergence

        # Normalize by number of tiles
        n_tiles = len(tile_ids)
        if n_tiles > 0:
            modality_divergences = {
                k: v / n_tiles for k, v in modality_divergences.items()
            }

        # Normalize contributions to sum to 1.0
        attribution = normalize_contributions(modality_divergences)

        # Classify hotspot
        confidence_tier = classify_hotspot(attribution)

        # Update hotspot
        hotspot["attribution"] = {
            "sar_contribution": attribution["sar"],
            "optical_contribution": attribution["optical"],
            "lights_contribution": attribution["lights"],
        }
        hotspot["confidence_tier"] = confidence_tier

        updated_hotspots.append(hotspot)

    return updated_hotspots
