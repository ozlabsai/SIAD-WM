"""SIAD World Model - Main integration module

Combines encoders and dynamics into action-conditioned world model for multi-step rollouts.
"""

import torch
import torch.nn as nn
from typing import Dict, Tuple, Optional

from .encoders import ObsEncoder, TargetEncoder, ActionEncoder
from .dynamics import TransitionModel


class WorldModel(nn.Module):
    """Action-conditioned world model for SIAD

    Architecture:
        - Observation encoder: x_t → z_t (ResNet18-based)
        - Target encoder: x_t → z̃_t (EMA-stabilized, no gradient)
        - Action encoder: a_t → u_t (2-layer MLP)
        - Dynamics: (z_t, u_t) → z_{t+1} (Transformer)

    Training:
        - Multi-step recursive rollout (H=6 months)
        - Loss: Σ_{k=1}^{H} w_k × cosine_distance(ẑ_{t+k}, z̃_{t+k})

    Usage:
        model = WorldModel(latent_dim=256)
        loss = model.compute_rollout_loss(obs_context, actions_rollout, obs_targets)

    Reference: See docs/model-design.md
    """

    def __init__(
        self,
        latent_dim: int = 256,
        in_channels: int = 8,
        action_dim: int = 2,
        use_transformer: bool = True,
        dropout: float = 0.1
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.in_channels = in_channels
        self.action_dim = action_dim

        # Initialize encoders
        self.obs_encoder = ObsEncoder(in_channels, latent_dim, dropout)
        self.target_encoder = TargetEncoder(in_channels, latent_dim, dropout)
        self.action_encoder = ActionEncoder(action_dim, latent_dim, dropout=dropout)

        # Initialize dynamics model
        self.dynamics = TransitionModel(latent_dim, use_transformer=use_transformer, dropout=dropout)

    def forward(
        self,
        obs_context: torch.Tensor,
        actions_rollout: torch.Tensor
    ) -> torch.Tensor:
        """Recursive multi-step rollout prediction

        Args:
            obs_context: [B, L, C, H, W] context observations (L=6 months)
            actions_rollout: [B, H, action_dim] rollout actions (H=6 months)

        Returns:
            z_pred: [B, H, latent_dim] predicted latent rollout
        """
        B, L, C, H, W = obs_context.shape
        _, horizon, _ = actions_rollout.shape

        # Encode last context frame as initial state
        x_t = obs_context[:, -1, :, :, :]  # [B, C, H, W]
        z_t = self.obs_encoder(x_t)         # [B, latent_dim]

        # Recursive rollout
        z_predictions = []
        for k in range(horizon):
            # Encode action
            u_t = self.action_encoder(actions_rollout[:, k, :])  # [B, latent_dim]

            # Predict next state
            z_t = self.dynamics(z_t, u_t)  # [B, latent_dim]
            z_predictions.append(z_t)

        # Stack predictions: [H, B, latent_dim] → [B, H, latent_dim]
        z_pred = torch.stack(z_predictions, dim=1)

        return z_pred

    def encode_targets(self, obs_targets: torch.Tensor) -> torch.Tensor:
        """Encode target observations with stable target encoder (no gradient)

        Args:
            obs_targets: [B, H, C, H, W] target observations

        Returns:
            z_tilde: [B, H, latent_dim] stable target latents
        """
        B, horizon, C, H, W = obs_targets.shape

        # Flatten batch and time dimensions
        obs_flat = obs_targets.view(B * horizon, C, H, W)

        # Encode with target encoder (no gradient)
        z_tilde_flat = self.target_encoder(obs_flat)  # [B*H, latent_dim]

        # Reshape back to [B, H, latent_dim]
        z_tilde = z_tilde_flat.view(B, horizon, self.latent_dim)

        return z_tilde

    def compute_rollout_loss(
        self,
        obs_context: torch.Tensor,
        actions_rollout: torch.Tensor,
        obs_targets: torch.Tensor,
        loss_weights: Optional[torch.Tensor] = None,
        loss_type: str = "cosine"
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Compute multi-step rollout loss

        Args:
            obs_context: [B, L=6, C=8, H=256, W=256] context observations
            actions_rollout: [B, H=6, 2] rollout actions
            obs_targets: [B, H=6, C=8, H=256, W=256] target observations
            loss_weights: [H] optional per-step weights (default: uniform)
            loss_type: "cosine" or "mse" (default: cosine)

        Returns:
            loss: Scalar total loss
            metrics: Dict with per-step losses and diagnostics
        """
        B, horizon = actions_rollout.shape[0], actions_rollout.shape[1]

        # Forward rollout: predict latent states
        z_pred = self.forward(obs_context, actions_rollout)  # [B, H, latent_dim]

        # Encode targets with stable target encoder
        z_tilde = self.encode_targets(obs_targets)  # [B, H, latent_dim]

        # Compute per-step loss
        if loss_type == "cosine":
            # Cosine distance: 1 - cos_similarity(z_pred, z_tilde)
            cos_sim = nn.functional.cosine_similarity(z_pred, z_tilde, dim=-1)  # [B, H]
            step_losses = 1 - cos_sim  # [B, H]
        elif loss_type == "mse":
            # Mean squared error
            step_losses = ((z_pred - z_tilde) ** 2).mean(dim=-1)  # [B, H]
        else:
            raise ValueError(f"Unknown loss_type: {loss_type}")

        # Apply per-step weights (default: uniform)
        if loss_weights is None:
            loss_weights = torch.ones(horizon, device=step_losses.device)

        weighted_losses = step_losses * loss_weights.unsqueeze(0)  # [B, H]

        # Total loss: mean over batch and horizon
        total_loss = weighted_losses.mean()

        # Metrics for logging
        metrics = {
            "loss/total": total_loss.item(),
            "loss/step_mean": step_losses.mean().item(),
        }
        for k in range(horizon):
            metrics[f"loss/step_{k+1}"] = step_losses[:, k].mean().item()

        return total_loss, metrics

    def update_target_encoder(self, momentum: float = 0.996):
        """Update target encoder via EMA from observation encoder

        Call after optimizer.step() in training loop.

        Args:
            momentum: EMA momentum (0.996 default, higher = slower update)
        """
        self.target_encoder.update_from_encoder(self.obs_encoder, momentum)

    def get_config(self) -> Dict:
        """Return model configuration for checkpoint saving"""
        return {
            "latent_dim": self.latent_dim,
            "in_channels": self.in_channels,
            "action_dim": self.action_dim,
            "use_transformer": self.dynamics.use_transformer,
            "model_architecture": {
                "obs_encoder": "ResNet18",
                "dynamics": "Transformer" if self.dynamics.use_transformer else "GRU"
            }
        }
