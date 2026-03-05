"""Loss Functions for SIAD World Model Training

Implements MODEL.md Section 7: Training objective
- Cosine JEPA rollout loss
- Anti-collapse regularizer
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple


def cosine_rollout_loss(
    z_pred: torch.Tensor,
    z_target: torch.Tensor,
    weights: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """Cosine distance rollout loss per MODEL.md Section 7.3
    
    Token-wise cosine distance summed over rollout steps.
    Loss = Σ_{k=1..H} w_k × mean_tokens(1 - cos(z_pred[k], z_target[k]))
    
    Args:
        z_pred: [B, H, N, D] predicted tokens
        z_target: [B, H, N, D] target tokens (from EMA encoder)
        weights: [H] optional per-step weights (default: uniform)
    
    Returns:
        loss: Scalar total loss
        metrics: Dict with per-step losses
    """
    B, H, N, D = z_pred.shape
    
    # L2 normalize along D dimension for cosine similarity
    z_pred_norm = F.normalize(z_pred, p=2, dim=-1)  # [B, H, N, D]
    z_target_norm = F.normalize(z_target, p=2, dim=-1)  # [B, H, N, D]
    
    # Cosine similarity per token: [B, H, N]
    cos_sim = (z_pred_norm * z_target_norm).sum(dim=-1)
    
    # Cosine distance: 1 - cos_similarity
    cos_dist = 1 - cos_sim  # [B, H, N]
    
    # Mean over tokens: [B, H]
    step_losses = cos_dist.mean(dim=-1)
    
    # Apply per-step weights (default: uniform)
    if weights is None:
        weights = torch.ones(H, device=z_pred.device)
    
    weighted_losses = step_losses * weights.unsqueeze(0)  # [B, H]
    
    # Total loss: mean over batch and horizon
    total_loss = weighted_losses.mean()
    
    # Metrics for logging
    metrics = {
        "loss/total": total_loss.item(),
        "loss/step_mean": step_losses.mean().item(),
    }
    for k in range(H):
        metrics[f"loss/step_{k+1}"] = step_losses[:, k].mean().item()
    
    return total_loss, metrics


def vcreg_loss(
    z: torch.Tensor,
    gamma: float = 1.0,
    alpha: float = 25.0,
    beta: float = 1.0,
    eps: float = 1e-4
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """VC-Reg anti-collapse loss (VICReg-style Variance + Covariance penalties)

    Per research.md Q1 and contracts/loss_api.md.
    Prevents representation collapse by:
    1. Enforcing variance floor across dimensions (variance penalty)
    2. Decorrelating dimensions (covariance penalty)

    Args:
        z: [B, N, D] encoder outputs (flattened to [B*N, D] internally)
        gamma: Variance floor threshold (target std per dimension)
        alpha: Variance loss weight
        beta: Covariance loss weight
        eps: Numerical stability epsilon

    Returns:
        loss: Combined anti-collapse loss (alpha * var_loss + beta * cov_loss)
        metrics: Dict with variance and covariance metrics
    """
    # Handle both [B, N, D] and [B, H, N, D] inputs
    if z.ndim == 4:
        B, H, N, D = z.shape
        X = z.reshape(B * H * N, D)  # Flatten batch×horizon×tokens
    elif z.ndim == 3:
        B, N, D = z.shape
        X = z.reshape(B * N, D)  # Flatten batch×tokens
    else:
        raise ValueError(f"Expected z to be 3D [B,N,D] or 4D [B,H,N,D], got {z.ndim}D")

    num_samples = X.shape[0]

    # ============================================================
    # Variance Floor Penalty (T006)
    # ============================================================
    # Compute per-dimension standard deviation
    std_per_dim = torch.sqrt(X.var(dim=0) + eps)  # [D]

    # Variance loss: penalize dimensions with std < gamma
    var_loss = torch.relu(gamma - std_per_dim).mean()

    # Track variance statistics
    std_mean = std_per_dim.mean()
    std_min = std_per_dim.min()
    std_max = std_per_dim.max()

    # Dead dimensions: proportion with std < 0.05
    dead_dims_frac = (std_per_dim < 0.05).float().mean()

    # ============================================================
    # Covariance Penalty (T007)
    # ============================================================
    # Center the data
    X_centered = X - X.mean(dim=0, keepdim=True)

    # Compute covariance matrix: [D, D]
    cov = (X_centered.T @ X_centered) / (num_samples - 1)

    # Zero out diagonal (we only penalize off-diagonal correlations)
    cov_off_diag = cov.clone()
    cov_off_diag.fill_diagonal_(0)

    # Covariance loss: sum of squared off-diagonal terms, normalized by D
    cov_loss = (cov_off_diag ** 2).sum() / D

    # ============================================================
    # Combined Loss (T008)
    # ============================================================
    total_loss = alpha * var_loss + beta * cov_loss

    # Metrics dictionary (all converted to Python floats)
    metrics = {
        "ac/var_loss": var_loss.item(),
        "ac/cov_loss": cov_loss.item(),
        "ac/total": total_loss.item(),
        "ac/std_mean": std_mean.item(),
        "ac/std_min": std_min.item(),
        "ac/std_max": std_max.item(),
        "ac/dead_dims_frac": dead_dims_frac.item(),
    }

    return total_loss, metrics


def anti_collapse_regularizer(
    z_pred: torch.Tensor,
    min_std: float = 0.1
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """Anti-collapse regularizer per MODEL.md Section 7.4

    DEPRECATED: Use vcreg_loss() instead for VC-Reg anti-collapse.
    This function is maintained for backward compatibility.

    Prevents representation collapse by enforcing minimum variance
    across batch × tokens.

    Args:
        z_pred: [B, H, N, D] predicted tokens
        min_std: Minimum standard deviation threshold

    Returns:
        reg_loss: Regularization penalty
        metrics: Dict with variance statistics
    """
    B, H, N, D = z_pred.shape

    # Flatten batch, horizon, and tokens: [B*H*N, D]
    z_flat = z_pred.reshape(-1, D)

    # Compute std deviation per dimension
    std_per_dim = z_flat.std(dim=0)  # [D]

    # Mean std across dimensions
    mean_std = std_per_dim.mean()

    # Penalize if std falls below threshold
    # Loss = ReLU(min_std - mean_std)
    reg_loss = F.relu(min_std - mean_std)

    # Metrics
    metrics = {
        "reg/std_mean": mean_std.item(),
        "reg/std_min": std_per_dim.min().item(),
        "reg/std_max": std_per_dim.max().item(),
        "reg/collapse_penalty": reg_loss.item()
    }

    return reg_loss, metrics


def compute_jepa_world_model_loss(
    z_pred: torch.Tensor,
    z_target: torch.Tensor,
    z_t: Optional[torch.Tensor] = None,  # NEW: encoder outputs for VC-Reg
    loss_type: str = "cosine",
    step_weights: Optional[torch.Tensor] = None,
    anti_collapse: bool = True,
    anti_collapse_config: Optional[Dict] = None,  # NEW: VC-Reg configuration
    # Deprecated parameters (kept for backward compatibility)
    anti_collapse_weight: float = 0.1,
    min_std: float = 0.1
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """Complete JEPA world model loss per MODEL.md Section 7

    Combines:
    - Cosine rollout loss (primary)
    - Anti-collapse regularizer (VC-Reg or legacy)

    Args:
        z_pred: [B, H, N, D] predicted tokens
        z_target: [B, H, N, D] target tokens
        z_t: [B, N, D] encoder outputs for VC-Reg (optional, NEW)
        loss_type: "cosine" or "mse" (default: cosine per MODEL.md)
        step_weights: [H] optional per-step weights
        anti_collapse: Enable anti-collapse regularizer
        anti_collapse_config: VC-Reg config dict with gamma, alpha, beta, lambda (NEW)
        anti_collapse_weight: DEPRECATED - use anti_collapse_config['lambda'] instead
        min_std: DEPRECATED - use anti_collapse_config['gamma'] instead

    Returns:
        total_loss: Combined loss
        metrics: Dict with all loss components
    """
    metrics = {}

    # Primary loss
    if loss_type == "cosine":
        primary_loss, primary_metrics = cosine_rollout_loss(z_pred, z_target, step_weights)
        metrics.update(primary_metrics)
    elif loss_type == "mse":
        # MSE fallback (not recommended per MODEL.md)
        mse_loss = F.mse_loss(z_pred, z_target)
        primary_loss = mse_loss
        metrics["loss/mse"] = mse_loss.item()
    else:
        raise ValueError(f"Unknown loss_type: {loss_type}")

    total_loss = primary_loss

    # Anti-collapse regularizer (T011)
    if anti_collapse:
        if z_t is not None and anti_collapse_config is not None:
            # NEW PATH: Use VC-Reg on encoder outputs
            gamma = anti_collapse_config.get("gamma", 1.0)
            alpha = anti_collapse_config.get("alpha", 25.0)
            beta = anti_collapse_config.get("beta", 1.0)
            lambda_ = anti_collapse_config.get("lambda", 1.0)

            ac_loss, ac_metrics = vcreg_loss(z_t, gamma=gamma, alpha=alpha, beta=beta)
            total_loss = total_loss + lambda_ * ac_loss
            metrics.update(ac_metrics)
        else:
            # OLD PATH: Use legacy anti_collapse_regularizer on predictions (backward compatibility)
            reg_loss, reg_metrics = anti_collapse_regularizer(z_pred, min_std=min_std)
            total_loss = total_loss + anti_collapse_weight * reg_loss
            metrics.update(reg_metrics)

    metrics["loss/total_combined"] = total_loss.item()

    return total_loss, metrics


class JEPAWorldModelLoss(nn.Module):
    """JEPA World Model Loss Module

    Wraps loss functions in nn.Module for easy integration with training loops.
    """

    def __init__(
        self,
        loss_type: str = "cosine",
        anti_collapse: bool = True,
        anti_collapse_config: Optional[Dict] = None,  # NEW: VC-Reg configuration
        # Deprecated parameters (kept for backward compatibility)
        anti_collapse_weight: float = 0.1,
        min_std: float = 0.1
    ):
        super().__init__()
        self.loss_type = loss_type
        self.anti_collapse = anti_collapse
        self.anti_collapse_config = anti_collapse_config  # NEW
        self.anti_collapse_weight = anti_collapse_weight  # DEPRECATED
        self.min_std = min_std  # DEPRECATED

    def forward(
        self,
        z_pred: torch.Tensor,
        z_target: torch.Tensor,
        z_t: Optional[torch.Tensor] = None,  # NEW: encoder outputs
        step_weights: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Args:
            z_pred: [B, H, N, D] predicted tokens
            z_target: [B, H, N, D] target tokens
            z_t: [B, N, D] encoder outputs (optional, for VC-Reg)
            step_weights: [H] optional per-step weights

        Returns:
            loss: Total loss
            metrics: Dict with loss components
        """
        return compute_jepa_world_model_loss(
            z_pred=z_pred,
            z_target=z_target,
            z_t=z_t,  # NEW
            loss_type=self.loss_type,
            step_weights=step_weights,
            anti_collapse=self.anti_collapse,
            anti_collapse_config=self.anti_collapse_config,  # NEW
            anti_collapse_weight=self.anti_collapse_weight,  # DEPRECATED
            min_std=self.min_std  # DEPRECATED
        )
