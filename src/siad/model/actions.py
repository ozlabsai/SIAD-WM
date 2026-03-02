"""Action Encoder for SIAD World Model

Implements MODEL.md Section 4.3: Action encoder h_φ
Encodes action vectors (rain/temp anomalies) to latent space.

Architecture per MODEL.md:
- Input: [B, A] where A ∈ {1, 2}
- Output: [B, 128]
- MLP: Linear(A→64) + SiLU, Linear(64→128) + SiLU
"""

import torch
import torch.nn as nn


class ActionEncoder(nn.Module):
    """Action encoder per MODEL.md Section 4.3
    
    Input: [B, A] action vector
    Output: [B, 128] action embedding
    
    Architecture:
    - Linear(A→64) + SiLU
    - Linear(64→128) + SiLU
    """
    
    def __init__(self, action_dim: int = 1, hidden_dim: int = 64, output_dim: int = 128):
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
            a: [B, A] action vector (rain_anom, optional temp_anom)
        
        Returns:
            u: [B, 128] action embedding
        """
        u = self.mlp(a)
        return u
