"""Environmental Normalization Module

Generates neutral weather conditions to isolate structural changes
from seasonal/environmental variability.

Key Concept:
- Rollout with neutral actions (rain_anom=0, temp_anom=0)
- Compare neutral prediction vs actual observation
- Deviations indicate structural changes, not weather effects
"""

import torch
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class NormalizationResult:
    """Container for environmental normalization results"""
    neutral_actions: torch.Tensor  # [H, action_dim] neutral scenario
    observed_actions: torch.Tensor  # [H, action_dim] actual weather
    neutral_latents: torch.Tensor  # [H, 256, 512] predicted under neutral
    observed_latents: torch.Tensor  # [H, 256, 512] predicted under observed
    actual_latents: torch.Tensor  # [H, 256, 512] encoded observations
    metadata: Dict


def generate_neutral_actions(
    horizon: int = 6,
    action_dim: int = 2,
    device: str = "cpu"
) -> torch.Tensor:
    """Generate neutral weather actions (all zeros)

    Args:
        horizon: Number of months to predict
        action_dim: Dimension of action space (2 for rain+temp)
        device: torch device

    Returns:
        actions: [horizon, action_dim] tensor of zeros
    """
    return torch.zeros(horizon, action_dim, device=device)


def generate_observed_actions(
    rain_anomalies: np.ndarray,
    temp_anomalies: np.ndarray,
    device: str = "cpu"
) -> torch.Tensor:
    """Convert observed weather anomalies to action tensor

    Args:
        rain_anomalies: [H] rainfall anomalies (σ units)
        temp_anomalies: [H] temperature anomalies (σ units)
        device: torch device

    Returns:
        actions: [H, 2] tensor with [rain, temp] per timestep
    """
    assert len(rain_anomalies) == len(temp_anomalies), \
        f"Mismatch: {len(rain_anomalies)} rain vs {len(temp_anomalies)} temp"

    actions = np.stack([rain_anomalies, temp_anomalies], axis=-1)  # [H, 2]
    return torch.from_numpy(actions).float().to(device)


def normalize_and_rollout(
    model,
    z_context: torch.Tensor,
    rain_anomalies: Optional[np.ndarray] = None,
    temp_anomalies: Optional[np.ndarray] = None,
    horizon: int = 6,
    device: str = "cpu"
) -> NormalizationResult:
    """Rollout with both neutral and observed weather conditions

    Args:
        model: World model with rollout() method
        z_context: [B, 256, 512] context latents
        rain_anomalies: [H] observed rain anomalies (optional)
        temp_anomalies: [H] observed temp anomalies (optional)
        horizon: Prediction horizon
        device: torch device

    Returns:
        NormalizationResult with predictions under both scenarios
    """
    # Generate neutral actions
    neutral_actions = generate_neutral_actions(horizon, action_dim=2, device=device)

    # Rollout with neutral weather
    with torch.no_grad():
        z_pred_neutral = model.rollout(z_context, neutral_actions, H=horizon)

    # If observed weather provided, also rollout with it
    if rain_anomalies is not None and temp_anomalies is not None:
        observed_actions = generate_observed_actions(
            rain_anomalies,
            temp_anomalies,
            device=device
        )

        with torch.no_grad():
            z_pred_observed = model.rollout(z_context, observed_actions, H=horizon)
    else:
        # No observed weather, use neutral for both
        observed_actions = neutral_actions
        z_pred_observed = z_pred_neutral

    metadata = {
        'horizon': horizon,
        'has_observed_weather': rain_anomalies is not None,
        'neutral_mean': float(neutral_actions.mean()),
        'observed_mean': float(observed_actions.mean()) if rain_anomalies is not None else 0.0
    }

    return NormalizationResult(
        neutral_actions=neutral_actions,
        observed_actions=observed_actions,
        neutral_latents=z_pred_neutral,
        observed_latents=z_pred_observed,
        actual_latents=None,  # Set later when encoding observations
        metadata=metadata
    )


def compare_scenarios(
    z_pred_neutral: torch.Tensor,
    z_pred_observed: torch.Tensor,
    z_actual: torch.Tensor
) -> Dict[str, np.ndarray]:
    """Compare neutral vs observed predictions against actual

    Args:
        z_pred_neutral: [B, H, 256, 512] prediction under neutral weather
        z_pred_observed: [B, H, 256, 512] prediction under observed weather
        z_actual: [B, H, 256, 512] actual observed latents

    Returns:
        Comparison metrics for each scenario
    """
    from .residuals import cosine_distance

    B, H, N, D = z_actual.shape

    # Compute residuals for both scenarios
    residuals_neutral = []
    residuals_observed = []

    for t in range(H):
        # Neutral scenario
        dist_neutral_t = cosine_distance(
            z_pred_neutral[:, t, :, :],
            z_actual[:, t, :, :]
        )  # [B, 256]
        residuals_neutral.append(dist_neutral_t.cpu().numpy())

        # Observed scenario
        dist_observed_t = cosine_distance(
            z_pred_observed[:, t, :, :],
            z_actual[:, t, :, :]
        )  # [B, 256]
        residuals_observed.append(dist_observed_t.cpu().numpy())

    residuals_neutral = np.array(residuals_neutral)  # [H, B, 256]
    residuals_observed = np.array(residuals_observed)  # [H, B, 256]

    # Aggregate to tile scores
    tile_score_neutral = np.mean(residuals_neutral, axis=2)  # [H, B]
    tile_score_observed = np.mean(residuals_observed, axis=2)  # [H, B]

    # Weather attribution: difference between scenarios
    weather_effect = residuals_observed - residuals_neutral

    return {
        'residuals_neutral': residuals_neutral,
        'residuals_observed': residuals_observed,
        'tile_score_neutral': tile_score_neutral,
        'tile_score_observed': tile_score_observed,
        'weather_effect': weather_effect,
        'mean_weather_effect': float(np.mean(weather_effect))
    }


def classify_change_type(
    residual_neutral: float,
    residual_observed: float,
    threshold: float = 0.1
) -> str:
    """Classify change as structural vs environmental

    Logic:
    - If residual_neutral >> residual_observed: Change is weather-driven
    - If residual_neutral ≈ residual_observed: Change is structural
    - If both high: Mixed (structural + weather)

    Args:
        residual_neutral: Residual under neutral weather
        residual_observed: Residual under observed weather
        threshold: Difference threshold for classification

    Returns:
        change_type: "structural" | "environmental" | "mixed" | "none"
    """
    diff = abs(residual_neutral - residual_observed)

    # Both low: no significant change
    if residual_neutral < 0.3 and residual_observed < 0.3:
        return "none"

    # Neutral much higher: weather explains the change
    if residual_observed < residual_neutral - threshold:
        return "environmental"

    # Similar residuals: structural change
    if diff < threshold:
        # But only if residuals are actually high
        if residual_neutral > 0.5:
            return "structural"
        else:
            return "none"

    # Neutral much lower: unexpected (shouldn't happen often)
    # Might indicate model issues
    if residual_neutral < residual_observed - threshold:
        return "mixed"

    return "none"


def sensitivity_analysis(
    model,
    z_context: torch.Tensor,
    z_actual: torch.Tensor,
    rain_range: Tuple[float, float] = (-2.0, 2.0),
    temp_range: Tuple[float, float] = (-1.5, 1.5),
    num_samples: int = 5,
    horizon: int = 1,
    device: str = "cpu"
) -> Dict[str, np.ndarray]:
    """Analyze model sensitivity to weather conditions

    Sweeps rain/temp anomalies to measure impact on predictions.

    Args:
        model: World model
        z_context: [1, 256, 512] context latents
        z_actual: [1, 256, 512] actual future latent
        rain_range: (min, max) rain anomaly range
        temp_range: (min, max) temp anomaly range
        num_samples: Number of samples per dimension
        horizon: Prediction steps (usually 1 for sensitivity)
        device: torch device

    Returns:
        Sensitivity grid and metrics
    """
    from .residuals import cosine_distance

    rain_values = np.linspace(rain_range[0], rain_range[1], num_samples)
    temp_values = np.linspace(temp_range[0], temp_range[1], num_samples)

    residual_grid = np.zeros((num_samples, num_samples))

    for i, rain in enumerate(rain_values):
        for j, temp in enumerate(temp_values):
            # Create action
            action = torch.tensor([[rain, temp]], device=device).float()

            # Rollout
            with torch.no_grad():
                z_pred = model.rollout(z_context, action, H=1)

            # Compute residual
            dist = cosine_distance(z_pred[:, 0, :, :], z_actual)
            residual_grid[i, j] = float(dist.mean())

    return {
        'rain_values': rain_values,
        'temp_values': temp_values,
        'residual_grid': residual_grid,
        'max_residual': float(np.max(residual_grid)),
        'min_residual': float(np.min(residual_grid)),
        'sensitivity_range': float(np.max(residual_grid) - np.min(residual_grid))
    }


def weather_normalization_report(
    residual_neutral: float,
    residual_observed: float,
    rain_anom: float,
    temp_anom: float
) -> str:
    """Generate human-readable explanation of normalization results

    Args:
        residual_neutral: Residual under neutral weather
        residual_observed: Residual under observed weather
        rain_anom: Observed rain anomaly (σ units)
        temp_anom: Observed temp anomaly (σ units)

    Returns:
        Explanation string for UI display
    """
    change_type = classify_change_type(residual_neutral, residual_observed)

    if change_type == "structural":
        explanation = (
            f"Structural acceleration detected. "
            f"Change persists under neutral weather conditions "
            f"(residual={residual_neutral:.2f}), indicating it is NOT explained "
            f"by observed weather anomalies (rain={rain_anom:+.1f}σ, temp={temp_anom:+.1f}°C)."
        )
    elif change_type == "environmental":
        explanation = (
            f"Environmental variability detected. "
            f"Change is primarily explained by weather conditions "
            f"(rain={rain_anom:+.1f}σ, temp={temp_anom:+.1f}°C). "
            f"Neutral scenario residual={residual_neutral:.2f} vs "
            f"observed residual={residual_observed:.2f}."
        )
    elif change_type == "mixed":
        explanation = (
            f"Mixed change detected. "
            f"Both structural and environmental factors contribute. "
            f"Neutral residual={residual_neutral:.2f}, "
            f"observed residual={residual_observed:.2f}."
        )
    else:  # none
        explanation = (
            f"No significant change detected. "
            f"Residuals are low under both neutral ({residual_neutral:.2f}) "
            f"and observed ({residual_observed:.2f}) weather conditions."
        )

    return explanation
