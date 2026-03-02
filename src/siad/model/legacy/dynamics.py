"""Transition dynamics model for SIAD World Model

Component:
    - TransitionModel: Predicts next latent state from current state + action
      F_ψ: (z_t, u_t) → z_{t+1}
"""

import torch
import torch.nn as nn
from typing import Optional


class TransitionModel(nn.Module):
    """Transition dynamics: (z_t, u_t) → z_{t+1} prediction

    Architecture: 1-layer Transformer Encoder (recommended for multi-step rollouts)
    Alternative: GRU for faster training (set use_transformer=False)

    - Input: Concatenated [z_t, u_t] where z_t is latent state, u_t is action embedding
    - Output: z_{t+1} predicted latent state

    Multi-step usage (recursive rollout):
        z_hat_1 = F(z_0, u_0)
        z_hat_2 = F(z_hat_1, u_1)
        ...
        z_hat_H = F(z_hat_{H-1}, u_{H-1})

    Reference: See docs/model-design.md Section 4
    """

    def __init__(
        self,
        latent_dim: int = 256,
        use_transformer: bool = True,
        nhead: int = 8,
        dim_feedforward: int = 1024,
        dropout: float = 0.1
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.use_transformer = use_transformer

        # Input projection: [z_t, u_t] → latent_dim
        self.input_proj = nn.Linear(latent_dim * 2, latent_dim)

        if use_transformer:
            # Transformer-based dynamics (better for long-horizon rollouts)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=latent_dim,
                nhead=nhead,
                dim_feedforward=dim_feedforward,
                dropout=dropout,
                batch_first=True  # Input shape: [B, 1, latent_dim]
            )
            self.dynamics = nn.TransformerEncoder(encoder_layer, num_layers=1)
        else:
            # GRU-based dynamics (fallback for memory efficiency)
            self.dynamics = nn.GRU(
                input_size=latent_dim,
                hidden_size=latent_dim,
                num_layers=1,
                batch_first=True,
                dropout=0.0  # Single layer, no dropout
            )

        # Output projection
        self.output_proj = nn.Linear(latent_dim, latent_dim)

    def forward(self, z_t: torch.Tensor, u_t: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z_t: [B, latent_dim] current latent state
            u_t: [B, latent_dim] action embedding

        Returns:
            z_next: [B, latent_dim] predicted next latent state
        """
        # Concatenate state and action
        x = torch.cat([z_t, u_t], dim=-1)  # [B, latent_dim*2]

        # Project to latent space
        x = self.input_proj(x)  # [B, latent_dim]

        if self.use_transformer:
            # Add sequence dimension for transformer: [B, 1, latent_dim]
            x = x.unsqueeze(1)
            x = self.dynamics(x)  # [B, 1, latent_dim]
            x = x.squeeze(1)      # [B, latent_dim]
        else:
            # GRU expects [B, seq_len=1, latent_dim]
            x = x.unsqueeze(1)
            x, _ = self.dynamics(x)  # [B, 1, latent_dim], hidden
            x = x.squeeze(1)         # [B, latent_dim]

        # Output projection
        z_next = self.output_proj(x)  # [B, latent_dim]

        return z_next
