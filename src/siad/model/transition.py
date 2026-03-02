"""Transition Model for SIAD World Model

Implements MODEL.md Section 4.4: Markov transition F_ψ
Predicts next latent state from current state and action.

Architecture per MODEL.md:
- Input: Z_t [B, 256, 512] + u_t [B, 128]
- Output: Z_{t+1} [B, 256, 512]
- Conditioning: Action token + FiLM per block
- Transformer: 6 blocks, 8 heads, FFN=2048
"""

import torch
import torch.nn as nn
from typing import Optional


class FiLMLayer(nn.Module):
    """FiLM (Feature-wise Linear Modulation) layer
    
    Per MODEL.md Section 4.4.1:
    - Compute (γ, β) from action embedding u_t
    - Apply: x = (1 + γ) * x + β
    """
    
    def __init__(self, action_dim: int = 128, latent_dim: int = 512):
        super().__init__()
        # MLP to produce scale (γ) and shift (β) params
        self.mlp = nn.Linear(action_dim, 2 * latent_dim)
    
    def forward(self, x: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, N, D] tokens
            u: [B, 128] action embedding
        
        Returns:
            modulated: [B, N, D] FiLM-modulated tokens
        """
        # Compute γ and β: [B, 2*D]
        film_params = self.mlp(u)
        gamma, beta = torch.chunk(film_params, 2, dim=-1)  # Each [B, D]
        
        # Broadcast to token dimension: [B, 1, D] to match [B, N, D]
        gamma = gamma.unsqueeze(1)
        beta = beta.unsqueeze(1)
        
        # FiLM modulation: x = (1 + γ) * x + β
        modulated = (1 + gamma) * x + beta
        
        return modulated


class TransitionTransformerBlock(nn.Module):
    """Single transformer block with FiLM conditioning
    
    Architecture per MODEL.md Section 4.4.2:
    - Pre-LayerNorm + Multi-head attention
    - FiLM conditioning after LayerNorm
    - Pre-LayerNorm + FFN
    """
    
    def __init__(
        self,
        dim: int = 512,
        num_heads: int = 8,
        mlp_dim: int = 2048,
        action_dim: int = 128,
        dropout: float = 0.0,
        use_film: bool = True
    ):
        super().__init__()
        self.use_film = use_film
        
        # Self-attention
        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)
        
        # FiLM conditioning
        if use_film:
            self.film = FiLMLayer(action_dim=action_dim, latent_dim=dim)
        
        # FFN
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_dim, dim),
            nn.Dropout(dropout)
        )
    
    def forward(self, x: torch.Tensor, u: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: [B, N, D] tokens (N=257 with action token, or 256 without)
            u: [B, 128] action embedding (for FiLM)
        
        Returns:
            x: [B, N, D] transformed tokens
        """
        # Self-attention with pre-norm
        x_norm = self.norm1(x)
        
        # Apply FiLM conditioning if enabled and action provided
        if self.use_film and u is not None:
            x_norm = self.film(x_norm, u)
        
        attn_out, _ = self.attn(x_norm, x_norm, x_norm, need_weights=False)
        x = x + attn_out
        
        # FFN with pre-norm
        x = x + self.mlp(self.norm2(x))
        
        return x


class TransitionModel(nn.Module):
    """Markov transition model per MODEL.md Section 4.4
    
    Input: Z_t [B, 256, 512] + u_t [B, 128]
    Output: Z_{t+1} [B, 256, 512]
    
    Conditioning per MODEL.md Section 4.4.1:
    1. Action token: project u_t → [B, 512], append to sequence
    2. FiLM: apply per-block conditioning
    
    Architecture per MODEL.md Section 4.4.2:
    - 6 transformer blocks
    - D=512, heads=8, FFN=2048
    - Learned positional embeddings
    """
    
    def __init__(
        self,
        latent_dim: int = 512,
        action_dim: int = 128,
        num_blocks: int = 6,
        num_heads: int = 8,
        mlp_dim: int = 2048,
        dropout: float = 0.0,
        use_film: bool = True,
        use_action_token: bool = True
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.action_dim = action_dim
        self.use_film = use_film
        self.use_action_token = use_action_token
        
        # Action token projection: 128 → 512
        if use_action_token:
            self.action_proj = nn.Linear(action_dim, latent_dim)
            # Learned position embedding for action token
            self.action_pos_embed = nn.Parameter(torch.randn(1, 1, latent_dim) * 0.02)
        
        # Learned 2D positional embeddings for 16×16 spatial tokens
        self.pos_embed = nn.Parameter(torch.randn(1, 256, latent_dim) * 0.02)
        
        # Transformer blocks
        self.blocks = nn.ModuleList([
            TransitionTransformerBlock(
                dim=latent_dim,
                num_heads=num_heads,
                mlp_dim=mlp_dim,
                action_dim=action_dim,
                dropout=dropout,
                use_film=use_film
            )
            for _ in range(num_blocks)
        ])
        
        # Final layer norm
        self.norm = nn.LayerNorm(latent_dim)
    
    def forward(self, z: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z: [B, 256, 512] current latent tokens
            u: [B, 128] action embedding
        
        Returns:
            z_next: [B, 256, 512] predicted next tokens
        """
        B = z.shape[0]
        
        # Add positional embeddings to spatial tokens
        tokens = z + self.pos_embed
        
        # Append action token if enabled
        if self.use_action_token:
            # Project action to latent dim: [B, 128] → [B, 512]
            action_token = self.action_proj(u).unsqueeze(1)  # [B, 1, 512]
            action_token = action_token + self.action_pos_embed
            
            # Concatenate: [B, 256, 512] + [B, 1, 512] → [B, 257, 512]
            tokens = torch.cat([tokens, action_token], dim=1)
        
        # Transformer blocks with FiLM conditioning
        for block in self.blocks:
            tokens = block(tokens, u=u if self.use_film else None)
        
        # Final norm
        tokens = self.norm(tokens)
        
        # Drop action token, return only spatial tokens
        if self.use_action_token:
            tokens = tokens[:, :256, :]  # [B, 256, 512]
        
        return tokens
