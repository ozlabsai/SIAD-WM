"""Action Encoder for SIAD World Model

Implements MODEL.md Section 4.3: Action encoder h_φ
Encodes action vectors (rain/temp anomalies + temporal features) to latent space.

Architecture per MODEL.md:
- Input: [B, A] where A ∈ {2, 4} (v1: weather only, v2: weather + temporal)
- Output: [B, 128]
- MLP: Linear(A→64) + SiLU, Linear(64→128) + SiLU

V2 Extension (temporal conditioning):
- action_dim=4: [rain_anom, temp_anom, month_sin, month_cos]
- Enables model to distinguish seasonal vegetation changes from infrastructure changes
"""

import torch
import torch.nn as nn


class ActionEncoder(nn.Module):
    """Action encoder per MODEL.md Section 4.3

    Input: [B, A] action vector where A=4 for v2 (weather + temporal)
    Output: [B, 128] action embedding

    Architecture:
    - Linear(A→64) + SiLU
    - Linear(64→128) + SiLU

    V2 Default: action_dim=4 for [rain_anom, temp_anom, month_sin, month_cos]
    """

    def __init__(self, action_dim: int = 4, hidden_dim: int = 64, output_dim: int = 128):
        super().__init__()
        self.action_dim = action_dim
        self.output_dim = output_dim
        
        # MLP layers per MODEL.md
        self.mlp = nn.Sequential(
            nn.Linear(action_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.SiLU()
        )
    
    def forward(self, a: torch.Tensor) -> torch.Tensor:
        """
        Args:
            a: [B, A] action vector
               V1: [rain_anom, temp_anom] (A=2)
               V2: [rain_anom, temp_anom, month_sin, month_cos] (A=4)

        Returns:
            u: [B, 128] action embedding
        """
        u = self.mlp(a)
        return u
