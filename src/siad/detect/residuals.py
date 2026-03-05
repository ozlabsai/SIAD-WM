"""Latent Residual Computation Module

Computes token-level residuals between predicted and observed latent representations.
Core detection mechanism for SIAD v2.0 (no decoder needed).

Key Functions:
- compute_residuals: Token-wise cosine distance
- aggregate_tile_score: Top-K token aggregation
- detect_persistence: Sustained vs burst alerts
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ResidualResult:
    """Container for residual computation results"""
    tile_id: str
    months: List[str]  # ISO dates (YYYY-MM)
    residuals: np.ndarray  # [T, 256] - token residuals per month
    tile_scores: np.ndarray  # [T] - aggregated scores
    weather_normalized: bool
    metadata: Dict


def cosine_distance(z_pred: torch.Tensor, z_obs: torch.Tensor) -> torch.Tensor:
    """Compute cosine distance between predicted and observed latents

    Args:
        z_pred: Predicted latents [B, N, D] or [N, D]
        z_obs: Observed latents [B, N, D] or [N, D]

    Returns:
        distance: 1 - cosine_similarity, shape [B, N] or [N]
    """
    # Ensure both tensors are on same device
    if z_pred.device != z_obs.device:
        z_obs = z_obs.to(z_pred.device)

    # Normalize to unit vectors
    z_pred_norm = F.normalize(z_pred, p=2, dim=-1)
    z_obs_norm = F.normalize(z_obs, p=2, dim=-1)

    # Compute cosine similarity
    cosine_sim = (z_pred_norm * z_obs_norm).sum(dim=-1)

    # Convert to distance (1 - similarity)
    distance = 1.0 - cosine_sim

    return distance


def compute_residuals(
    z_pred: torch.Tensor,
    z_obs: torch.Tensor,
    tile_id: str,
    months: List[str],
    weather_normalized: bool = True
) -> ResidualResult:
    """Compute token-level residuals for a tile

    Args:
        z_pred: Predicted latents [T, 256, 512] (T months)
        z_obs: Observed latents [T, 256, 512]
        tile_id: Tile identifier
        months: List of month strings (ISO format YYYY-MM)
        weather_normalized: Whether prediction used neutral weather

    Returns:
        ResidualResult with token residuals and tile scores
    """
    assert z_pred.shape == z_obs.shape, f"Shape mismatch: {z_pred.shape} vs {z_obs.shape}"
    assert z_pred.shape[0] == len(months), f"Mismatch: {z_pred.shape[0]} timesteps vs {len(months)} months"

    T, N, D = z_pred.shape
    assert N == 256, f"Expected 256 tokens, got {N}"
    assert D == 512, f"Expected 512 dims, got {D}"

    # Compute token-wise cosine distance for each month
    residuals = []
    for t in range(T):
        dist_t = cosine_distance(z_pred[t], z_obs[t])  # [256]
        residuals.append(dist_t.cpu().numpy())

    residuals = np.array(residuals)  # [T, 256]

    # Aggregate to tile scores (top 10% tokens)
    tile_scores = aggregate_tile_scores(residuals, top_k_pct=0.10)

    metadata = {
        'num_tokens': N,
        'latent_dim': D,
        'num_months': T,
        'mean_residual': float(np.mean(residuals)),
        'std_residual': float(np.std(residuals)),
        'max_residual': float(np.max(residuals)),
        'min_residual': float(np.min(residuals))
    }

    return ResidualResult(
        tile_id=tile_id,
        months=months,
        residuals=residuals,
        tile_scores=tile_scores,
        weather_normalized=weather_normalized,
        metadata=metadata
    )


def aggregate_tile_scores(
    residuals: np.ndarray,
    top_k_pct: float = 0.10
) -> np.ndarray:
    """Aggregate token residuals to tile-level scores

    Strategy: Mean of top K% tokens (reduces global shift sensitivity)

    Args:
        residuals: Token residuals [T, 256]
        top_k_pct: Percentile threshold (0.10 = top 10%)

    Returns:
        tile_scores: [T] aggregated scores per month
    """
    T, N = residuals.shape
    k = int(N * top_k_pct)
    k = max(k, 1)  # At least 1 token

    tile_scores = []
    for t in range(T):
        # Get top-k tokens for this month
        top_k_values = np.partition(residuals[t], -k)[-k:]
        score = np.mean(top_k_values)
        tile_scores.append(score)

    return np.array(tile_scores)


def detect_persistence(
    tile_scores: np.ndarray,
    threshold: float = 0.5,
    sustained_months: int = 3,
    burst_percentile: float = 95.0,
    all_scores: Optional[np.ndarray] = None
) -> Dict[str, any]:
    """Detect persistence patterns in tile scores

    Two alert types:
    - Sustained: Score above threshold for ≥ sustained_months
    - Burst: Short-lived spike above burst_percentile

    Args:
        tile_scores: [T] scores for this tile
        threshold: Minimum score for sustained alert
        sustained_months: Consecutive months required
        burst_percentile: Percentile for burst detection
        all_scores: Optional [M] all tile scores (for percentile)

    Returns:
        Detection result with alert type and metadata
    """
    # Sustained alert: consecutive months above threshold
    above_threshold = tile_scores >= threshold
    consecutive_runs = []
    current_run = 0

    for above in above_threshold:
        if above:
            current_run += 1
        else:
            if current_run > 0:
                consecutive_runs.append(current_run)
            current_run = 0

    if current_run > 0:
        consecutive_runs.append(current_run)

    max_consecutive = max(consecutive_runs) if consecutive_runs else 0
    sustained = max_consecutive >= sustained_months

    # Burst alert: spike above percentile
    if all_scores is not None:
        burst_threshold = np.percentile(all_scores, burst_percentile)
    else:
        # Fallback: use this tile's own distribution
        burst_threshold = np.percentile(tile_scores, burst_percentile)

    max_score = np.max(tile_scores)
    burst = max_score > burst_threshold and max_consecutive < sustained_months

    # Determine alert type
    if sustained:
        alert_type = "structural_acceleration"
    elif burst:
        alert_type = "activity_surge"
    else:
        alert_type = None

    # Compute confidence
    if sustained:
        # Confidence based on consistency and magnitude
        score_std = np.std(tile_scores[above_threshold])
        score_mean = np.mean(tile_scores[above_threshold])

        if score_mean > 0.7 and score_std < 0.1:
            confidence = "high"
        elif score_mean > 0.5:
            confidence = "medium"
        else:
            confidence = "low"
    elif burst:
        # Confidence based on spike magnitude
        if max_score > burst_threshold * 1.2:
            confidence = "high"
        elif max_score > burst_threshold * 1.1:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = None

    return {
        'has_alert': alert_type is not None,
        'alert_type': alert_type,
        'confidence': confidence,
        'sustained': sustained,
        'burst': burst,
        'max_consecutive_months': int(max_consecutive),
        'max_score': float(max_score),
        'mean_score': float(np.mean(tile_scores)),
        'onset_month_idx': int(np.argmax(tile_scores >= threshold)) if sustained else None,
        'peak_month_idx': int(np.argmax(tile_scores))
    }


def compare_with_baseline(
    residual_wm: float,
    residual_baseline: float,
    baseline_name: str = "persistence"
) -> Dict[str, float]:
    """Compare world model residual with baseline

    Args:
        residual_wm: World model residual
        residual_baseline: Baseline residual (persistence or seasonal)
        baseline_name: Name of baseline for logging

    Returns:
        Comparison metrics
    """
    # Improvement = (baseline - wm) / baseline
    # Positive means world model is better (lower residual)
    if residual_baseline > 0:
        improvement = (residual_baseline - residual_wm) / residual_baseline
    else:
        improvement = 0.0

    return {
        'world_model': float(residual_wm),
        'baseline': float(residual_baseline),
        'baseline_name': baseline_name,
        'improvement': float(improvement),
        'improvement_pct': float(improvement * 100),
        'outperforms': improvement > 0
    }


def spatial_coherence_score(residuals_2d: np.ndarray) -> float:
    """Compute spatial coherence of residual map

    Measures clustering vs random noise using autocorrelation.

    Args:
        residuals_2d: [16, 16] residual grid

    Returns:
        coherence: 0-1, higher = more spatially clustered
    """
    assert residuals_2d.shape == (16, 16), f"Expected (16,16), got {residuals_2d.shape}"

    # Compute local autocorrelation (neighbors)
    # For each cell, compute correlation with 4-neighbors
    autocorr_scores = []

    for i in range(1, 15):  # Skip edges
        for j in range(1, 15):
            center = residuals_2d[i, j]
            neighbors = [
                residuals_2d[i-1, j],
                residuals_2d[i+1, j],
                residuals_2d[i, j-1],
                residuals_2d[i, j+1]
            ]

            # Correlation with neighbors
            neighbor_mean = np.mean(neighbors)
            autocorr = abs(center - neighbor_mean)
            autocorr_scores.append(autocorr)

    # Low autocorr error = high coherence
    mean_autocorr_error = np.mean(autocorr_scores)

    # Normalize to 0-1 (lower error = higher coherence)
    # Empirically, random noise has autocorr_error ~ 0.3
    coherence = max(0, 1.0 - (mean_autocorr_error / 0.3))

    return float(coherence)


def reshape_to_grid(residuals: np.ndarray) -> np.ndarray:
    """Reshape 256-token vector to 16×16 grid

    Args:
        residuals: [256] token residuals

    Returns:
        grid: [16, 16] spatial grid
    """
    assert residuals.shape == (256,), f"Expected (256,), got {residuals.shape}"
    return residuals.reshape(16, 16)


def modality_attribution(
    residuals: np.ndarray,
    tile_id: str,
    channel_groups: Dict[str, List[int]] = None
) -> Dict[str, float]:
    """Attribute residual to dominant modality (SAR vs optical vs VIIRS)

    NOTE: This requires access to band-wise gradients or attention maps.
    For MVP, we'll use a heuristic based on spatial patterns.

    Args:
        residuals: [16, 16] residual grid
        tile_id: Tile identifier
        channel_groups: Optional mapping of modality to channel indices

    Returns:
        Attribution scores for each modality
    """
    # Placeholder implementation
    # In full version, this would use attention weights or gradients

    # Heuristic: SAR tends to have high-frequency patterns,
    # optical has smoother gradients, VIIRS has sparse hotspots

    grid = reshape_to_grid(residuals) if residuals.shape == (256,) else residuals

    # Compute frequency content (simple proxy)
    grad_x = np.gradient(grid, axis=0)
    grad_y = np.gradient(grid, axis=1)
    high_freq = np.mean(np.abs(grad_x) + np.abs(grad_y))

    # Compute sparsity
    sparsity = np.sum(grid > np.percentile(grid, 90)) / grid.size

    # Heuristic attribution
    if high_freq > 0.3:
        dominant = "SAR"
    elif sparsity > 0.2:
        dominant = "VIIRS"
    else:
        dominant = "Optical"

    return {
        'dominant_modality': dominant,
        'high_freq_score': float(high_freq),
        'sparsity_score': float(sparsity),
        'note': 'Heuristic attribution - requires attention maps for accuracy'
    }
