"""Action Encoder for SIAD World Model

Implements MODEL.md Section 4.3: Action encoder h_φ
Encodes action vectors (rain/temp anomalies + temporal features) to latent space.

Architecture per MODEL.md:
- Input: [B, A] where A ∈ {2, 4} (v1: weather only, v2: weather + temporal)
- Output: [B, 128]
- MLP: Linear(A→64) + SiLU, Linear(64→128) + SiLU

V2 Schema (temporal conditioning):
- Input: [B, 4] action vector (rain_anom, temp_anom, month_sin, month_cos)
- No architecture changes needed - existing MLP handles variable action_dim
"""

import torch
import torch.nn as nn


class ActionEncoder(nn.Module):
    """Action encoder per MODEL.md Section 4.3

    Input: [B, A] action vector where A=action_dim
    Output: [B, 128] action embedding

    Architecture:
    - Linear(A→64) + SiLU
    - Linear(64→128) + SiLU

    V2 Extension:
    - Default action_dim=4 for temporal conditioning
    - Input: [B, 4] = [rain_anom, temp_anom, month_sin, month_cos]
    - Backward compatible: can load v1 checkpoints (action_dim=2) via padding
    """

    def __init__(self, action_dim: int = 4, hidden_dim: int = 64, output_dim: int = 128):
        """Initialize action encoder.

        Args:
            action_dim: Input dimension (4 for v2 with temporal, 2 for v1 baseline)
            hidden_dim: Hidden layer dimension (default 64)
            output_dim: Output embedding dimension (default 128)
        """
        super().__init__()
        self.action_dim = action_dim
        self.output_dim = output_dim

        # MLP layers per MODEL.md
        # V2: Linear(4→64) handles extended action vector with temporal features
        self.mlp = nn.Sequential(
            nn.Linear(action_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.SiLU()
        )

    def forward(self, a: torch.Tensor) -> torch.Tensor:
        """Encode action vector to latent space.

        Args:
            a: [B, A] action vector where A=action_dim
               V1: [B, 2] = [rain_anom, temp_anom]
               V2: [B, 4] = [rain_anom, temp_anom, month_sin, month_cos]

        Returns:
            u: [B, 128] action embedding
        """
        u = self.mlp(a)
        return u
