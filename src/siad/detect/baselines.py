"""Baseline Comparison Module

Implements three baseline predictors for comparing world model performance:
1. Persistence baseline: Predict no change (Z_t+1 = Z_t)
2. Seasonal baseline: Predict same as last year (Z_t+1 = Z_t-12)
3. Linear extrapolation baseline: Extrapolate linear trend from recent history

These baselines provide context for evaluating world model prediction quality.
Per AGENT_1_ARCHITECTURE.md Task 1.
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
from abc import ABC, abstractmethod


class BaselinePredictor(ABC):
    """Abstract interface for baseline predictors

    All baselines implement predict() to return predicted latents.
    """

    @abstractmethod
    def predict(
        self,
        z_context: torch.Tensor,
        horizon: int = 6
    ) -> torch.Tensor:
        """Return predicted latents

        Args:
            z_context: Context latents [B, 256, 512] or [256, 512]
            horizon: Number of months to predict

        Returns:
            z_pred: Predicted latents [B, H, 256, 512] or [H, 256, 512]
        """
        pass


class PersistenceBaseline(BaselinePredictor):
    """Persistence baseline: Predict no change

    Strategy: Z_t+k = Z_t for all k in [1..H]
    Simply repeats the last observation for all future timesteps.

    This is the simplest baseline - assumes the landscape doesn't change.
    """

    def predict(
        self,
        z_context: torch.Tensor,
        horizon: int = 6
    ) -> torch.Tensor:
        """Predict no change: Z_pred = Z_context repeated

        Args:
            z_context: Context latents [B, 256, 512] or [256, 512]
            horizon: Number of months to predict

        Returns:
            z_pred: Predicted latents [B, H, 256, 512] or [H, 256, 512]
        """
        # Handle both batched and single inputs
        if z_context.ndim == 2:
            # Single sample [256, 512]
            z_pred = z_context.unsqueeze(0).repeat(horizon, 1, 1)  # [H, 256, 512]
        elif z_context.ndim == 3:
            # Batched [B, 256, 512]
            B = z_context.shape[0]
            z_pred = z_context.unsqueeze(1).repeat(1, horizon, 1, 1)  # [B, H, 256, 512]
        else:
            raise ValueError(
                f"Expected z_context shape [256, 512] or [B, 256, 512], "
                f"got {z_context.shape}"
            )

        return z_pred


class SeasonalBaseline(BaselinePredictor):
    """Seasonal baseline: Predict same as last year

    Strategy: Z_t+k = Z_{t+k-12}
    Uses observation from 12 months ago as prediction.

    Requires access to historical data from the same month in previous year.
    """

    def __init__(self, encoder=None, data_loader=None):
        """Initialize seasonal baseline

        Args:
            encoder: Optional encoder model for encoding historical observations
            data_loader: Optional data loader for fetching historical tiles
        """
        self.encoder = encoder
        self.data_loader = data_loader

    def predict(
        self,
        z_context: torch.Tensor,
        horizon: int = 6,
        z_historical: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Predict same as last year: Z_pred = Z_{t-12}

        Args:
            z_context: Context latents [B, 256, 512] or [256, 512] (not used directly)
            horizon: Number of months to predict
            z_historical: Pre-encoded historical latents [B, H, 256, 512] or [H, 256, 512]
                         These should be from 12 months ago

        Returns:
            z_pred: Predicted latents [B, H, 256, 512] or [H, 256, 512]
        """
        if z_historical is None:
            raise ValueError(
                "Seasonal baseline requires z_historical (observations from 12 months ago). "
                "Either provide pre-encoded latents or set encoder + data_loader."
            )

        # Validate historical data has correct horizon
        if z_historical.ndim == 3:
            # [H, 256, 512]
            assert z_historical.shape[0] == horizon, \
                f"z_historical has {z_historical.shape[0]} timesteps, need {horizon}"
            return z_historical
        elif z_historical.ndim == 4:
            # [B, H, 256, 512]
            assert z_historical.shape[1] == horizon, \
                f"z_historical has {z_historical.shape[1]} timesteps, need {horizon}"
            return z_historical
        else:
            raise ValueError(
                f"Expected z_historical shape [H, 256, 512] or [B, H, 256, 512], "
                f"got {z_historical.shape}"
            )

    def predict_from_observations(
        self,
        x_historical: torch.Tensor,
        horizon: int = 6
    ) -> torch.Tensor:
        """Predict from raw historical observations

        Requires encoder to be set during initialization.

        Args:
            x_historical: Historical observations [B, H, 8, 256, 256] or [H, 8, 256, 256]
            horizon: Number of months to predict

        Returns:
            z_pred: Predicted latents [B, H, 256, 512] or [H, 256, 512]
        """
        if self.encoder is None:
            raise RuntimeError(
                "Encoder not set. Either provide z_historical to predict() "
                "or set encoder in __init__."
            )

        with torch.no_grad():
            if x_historical.ndim == 4:
                # [H, 8, 256, 256]
                z_pred = self.encoder(x_historical)  # [H, 256, 512]
            elif x_historical.ndim == 5:
                # [B, H, 8, 256, 256]
                B, H, C, Hp, Wp = x_historical.shape
                x_flat = x_historical.view(B * H, C, Hp, Wp)
                z_flat = self.encoder(x_flat)
                z_pred = z_flat.view(B, H, 256, 512)
            else:
                raise ValueError(
                    f"Expected x_historical shape [H, 8, 256, 256] or [B, H, 8, 256, 256], "
                    f"got {x_historical.shape}"
                )

        return z_pred


class LinearExtrapolationBaseline(BaselinePredictor):
    """Linear extrapolation baseline: Extrapolate linear trend

    Strategy: Fit linear trend to recent K months, then extrapolate forward.
    Z_t+k = Z_t + k * slope, where slope = (Z_t - Z_{t-K}) / K

    Default K=3 (use last 3 months to estimate trend).
    """

    def __init__(self, history_length: int = 3):
        """Initialize linear extrapolation baseline

        Args:
            history_length: Number of recent months to use for trend (default 3)
        """
        self.history_length = history_length

    def predict(
        self,
        z_context: torch.Tensor,
        horizon: int = 6,
        z_history: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Extrapolate linear trend from recent months

        Args:
            z_context: Most recent latent [B, 256, 512] or [256, 512]
            horizon: Number of months to predict
            z_history: Historical latents [B, K, 256, 512] or [K, 256, 512]
                      where K = history_length. If None, uses persistence.

        Returns:
            z_pred: Predicted latents [B, H, 256, 512] or [H, 256, 512]
        """
        # Handle batch dimensions
        if z_context.ndim == 2:
            batched = False
            z_context = z_context.unsqueeze(0)  # [1, 256, 512]
            if z_history is not None and z_history.ndim == 3:
                z_history = z_history.unsqueeze(0)  # [1, K, 256, 512]
        else:
            batched = True

        B, N, D = z_context.shape
        assert N == 256 and D == 512, f"Expected [B, 256, 512], got {z_context.shape}"

        # Compute linear trend
        if z_history is None or z_history.shape[1] < 2:
            # Not enough history, fall back to persistence
            z_pred = z_context.unsqueeze(1).repeat(1, horizon, 1, 1)  # [B, H, 256, 512]
        else:
            # Fit linear trend: slope = (z_t - z_{t-K}) / K
            # Use simple linear regression on token embeddings
            K = z_history.shape[1]

            # Append current context to history
            z_full = torch.cat([z_history, z_context.unsqueeze(1)], dim=1)  # [B, K+1, 256, 512]

            # Compute slope using least squares
            # For simplicity, use delta between first and last
            z_start = z_full[:, 0, :, :]  # [B, 256, 512]
            z_end = z_full[:, -1, :, :]   # [B, 256, 512]
            slope = (z_end - z_start) / K  # [B, 256, 512]

            # Extrapolate: z_pred[t+k] = z_t + (k+1) * slope
            z_pred = []
            for k in range(horizon):
                z_k = z_context + (k + 1) * slope  # [B, 256, 512]
                z_pred.append(z_k)

            z_pred = torch.stack(z_pred, dim=1)  # [B, H, 256, 512]

        # Remove batch dimension if input was unbatched
        if not batched:
            z_pred = z_pred.squeeze(0)  # [H, 256, 512]

        return z_pred


def compare_baseline_residuals(
    z_pred_wm: torch.Tensor,
    z_pred_baseline: torch.Tensor,
    z_actual: torch.Tensor,
    baseline_name: str = "persistence"
) -> Dict[str, Any]:
    """Compare world model predictions against baseline

    Computes residuals (cosine distance) for both world model and baseline,
    then reports which performs better.

    Args:
        z_pred_wm: World model predictions [B, H, 256, 512] or [H, 256, 512]
        z_pred_baseline: Baseline predictions [B, H, 256, 512] or [H, 256, 512]
        z_actual: Actual observations [B, H, 256, 512] or [H, 256, 512]
        baseline_name: Name of baseline for logging

    Returns:
        Comparison metrics dict with:
            - residual_wm: [H] mean residual per timestep for world model
            - residual_baseline: [H] mean residual per timestep for baseline
            - improvement: [H] fractional improvement over baseline
            - mean_improvement: Overall mean improvement
            - outperforms: Whether world model outperforms baseline
    """
    # Import here to avoid circular dependency
    from .residuals import cosine_distance

    # Ensure all tensors have same shape
    assert z_pred_wm.shape == z_pred_baseline.shape == z_actual.shape, \
        f"Shape mismatch: WM={z_pred_wm.shape}, Baseline={z_pred_baseline.shape}, Actual={z_actual.shape}"

    # Handle batch dimension
    if z_actual.ndim == 3:
        # [H, 256, 512] - add batch dim
        z_pred_wm = z_pred_wm.unsqueeze(0)
        z_pred_baseline = z_pred_baseline.unsqueeze(0)
        z_actual = z_actual.unsqueeze(0)

    B, H, N, D = z_actual.shape

    # Compute residuals for each timestep
    residuals_wm = []
    residuals_baseline = []

    for t in range(H):
        # World model residual
        dist_wm = cosine_distance(z_pred_wm[:, t, :, :], z_actual[:, t, :, :])  # [B, 256]
        residuals_wm.append(dist_wm.mean().item())

        # Baseline residual
        dist_baseline = cosine_distance(z_pred_baseline[:, t, :, :], z_actual[:, t, :, :])  # [B, 256]
        residuals_baseline.append(dist_baseline.mean().item())

    residuals_wm = np.array(residuals_wm)
    residuals_baseline = np.array(residuals_baseline)

    # Compute improvement: (baseline - wm) / baseline
    # Positive = world model is better (lower residual)
    improvement = np.where(
        residuals_baseline > 0,
        (residuals_baseline - residuals_wm) / residuals_baseline,
        0.0
    )

    mean_improvement = float(np.mean(improvement))
    outperforms = mean_improvement > 0

    return {
        'residual_wm': residuals_wm.tolist(),
        'residual_baseline': residuals_baseline.tolist(),
        'improvement': improvement.tolist(),
        'mean_improvement': mean_improvement,
        'improvement_pct': mean_improvement * 100,
        'outperforms': outperforms,
        'baseline_name': baseline_name,
        'horizon': H
    }


def compute_baseline_scores(
    z_pred_baseline: torch.Tensor,
    z_actual: torch.Tensor,
    top_k_pct: float = 0.10
) -> np.ndarray:
    """Compute tile scores for baseline predictions

    Uses same aggregation strategy as world model (top-k tokens).

    Args:
        z_pred_baseline: Baseline predictions [B, H, 256, 512] or [H, 256, 512]
        z_actual: Actual observations [B, H, 256, 512] or [H, 256, 512]
        top_k_pct: Percentile threshold for top-k aggregation (default 0.10 = 10%)

    Returns:
        tile_scores: [H] aggregated scores (mean of top-k tokens)
    """
    from .residuals import cosine_distance

    # Handle batch dimension
    if z_actual.ndim == 3:
        z_pred_baseline = z_pred_baseline.unsqueeze(0)
        z_actual = z_actual.unsqueeze(0)

    B, H, N, D = z_actual.shape
    k = int(N * top_k_pct)
    k = max(k, 1)

    tile_scores = []
    for t in range(H):
        # Compute token-wise residuals
        dist = cosine_distance(z_pred_baseline[:, t, :, :], z_actual[:, t, :, :])  # [B, 256]

        # Aggregate top-k tokens (averaged across batch)
        # For each sample in batch, get top-k
        batch_scores = []
        for b in range(B):
            # Use torch.topk instead of numpy partition to avoid numpy compatibility issues
            top_k_values, _ = torch.topk(dist[b], k=k, largest=True)
            batch_scores.append(top_k_values.mean().item())

        tile_scores.append(np.mean(batch_scores))

    return np.array(tile_scores)


def create_baseline_predictor(
    baseline_type: str,
    encoder=None,
    data_loader=None,
    history_length: int = 3
) -> BaselinePredictor:
    """Factory function to create baseline predictor

    Args:
        baseline_type: One of ["persistence", "seasonal", "linear"]
        encoder: Encoder model (for seasonal baseline)
        data_loader: Data loader (for seasonal baseline)
        history_length: History length for linear baseline (default 3)

    Returns:
        BaselinePredictor instance
    """
    if baseline_type == "persistence":
        return PersistenceBaseline()
    elif baseline_type == "seasonal":
        return SeasonalBaseline(encoder=encoder, data_loader=data_loader)
    elif baseline_type == "linear":
        return LinearExtrapolationBaseline(history_length=history_length)
    else:
        raise ValueError(
            f"Unknown baseline_type: {baseline_type}. "
            f"Choose from: persistence, seasonal, linear"
        )
