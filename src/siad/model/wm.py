"""SIAD World Model Main Module

Implements MODEL.md Section 10: Required interfaces
Integrates encoder, target encoder, action encoder, and transition model.

Required interfaces:
- encode(x) → z
- transition(z, a) → z_next
- rollout(z0, a_seq, H) → z_pred
"""

import torch
import torch.nn as nn
from typing import Dict, Optional

from .encoder import ContextEncoder, TargetEncoderEMA
from .actions import ActionEncoder
from .transition import TransitionModel
from .decoder import SpatialDecoder


class WorldModel(nn.Module):
    """SIAD World Model per MODEL.md
    
    Complete JEPA-centered world model with:
    - Context encoder f_θ
    - Target encoder f_θ̄ (EMA)
    - Action encoder h_φ
    - Transition model F_ψ
    
    Supports multi-step rollout for H months (default H=6).
    """
    
    def __init__(
        self,
        # Input/output config
        in_channels: int = 8,
        latent_dim: int = 512,
        action_dim: int = 1,

        # Encoder config
        encoder_blocks: int = 4,
        encoder_heads: int = 8,
        encoder_mlp_dim: int = 2048,

        # Transition config
        transition_blocks: int = 6,
        transition_heads: int = 8,
        transition_mlp_dim: int = 2048,

        # EMA config
        tau_start: float = 0.99,
        tau_end: float = 0.995,
        warmup_steps: int = 2000,

        # Conditioning config
        use_film: bool = True,
        use_action_token: bool = True,

        # Decoder config (optional, for visualization/demo)
        use_decoder: bool = False,
        decoder_hidden_dims: tuple = (256, 128, 64, 32),

        # Regularization
        dropout: float = 0.0
    ):
        super().__init__()

        self.in_channels = in_channels
        self.latent_dim = latent_dim
        self.action_dim = action_dim
        self.use_decoder = use_decoder
        
        # Context encoder
        self.context_encoder = ContextEncoder(
            in_channels=in_channels,
            latent_dim=latent_dim,
            num_blocks=encoder_blocks,
            num_heads=encoder_heads,
            mlp_dim=encoder_mlp_dim,
            dropout=dropout
        )
        
        # Target encoder (EMA)
        self.target_encoder = TargetEncoderEMA(
            in_channels=in_channels,
            latent_dim=latent_dim,
            num_blocks=encoder_blocks,
            num_heads=encoder_heads,
            mlp_dim=encoder_mlp_dim,
            dropout=dropout,
            tau_start=tau_start,
            tau_end=tau_end,
            warmup_steps=warmup_steps
        )
        
        # Action encoder
        self.action_encoder = ActionEncoder(
            action_dim=action_dim,
            hidden_dim=64,
            output_dim=128
        )
        
        # Transition model
        self.transition_model = TransitionModel(
            latent_dim=latent_dim,
            action_dim=128,  # Action encoder output dim
            num_blocks=transition_blocks,
            num_heads=transition_heads,
            mlp_dim=transition_mlp_dim,
            dropout=dropout,
            use_film=use_film,
            use_action_token=use_action_token
        )

        # Decoder (optional, for pixel-space visualization)
        if use_decoder:
            self.decoder = SpatialDecoder(
                latent_dim=latent_dim,
                out_channels=in_channels,
                hidden_dims=decoder_hidden_dims,
                use_batch_norm=True,
                dropout=dropout
            )
        else:
            self.decoder = None
    
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode observation to latent tokens
        
        Per MODEL.md Section 10 interface requirement.
        
        Args:
            x: [B, C, 256, 256] observations
        
        Returns:
            z: [B, 256, 512] latent tokens
        """
        return self.context_encoder(x)
    
    def transition(self, z: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        """Predict next latent state from current state and action
        
        Per MODEL.md Section 10 interface requirement.
        
        Args:
            z: [B, 256, 512] current tokens
            a: [B, A] raw actions (will be encoded internally)
        
        Returns:
            z_next: [B, 256, 512] predicted next tokens
        """
        # Encode actions: [B, A] → [B, 128]
        u = self.action_encoder(a)
        
        # Transition: [B, 256, 512] + [B, 128] → [B, 256, 512]
        z_next = self.transition_model(z, u)
        
        return z_next
    
    def rollout(
        self,
        z0: torch.Tensor,
        a_seq: torch.Tensor,
        H: int
    ) -> torch.Tensor:
        """Multi-step Markov rollout
        
        Per MODEL.md Section 6.1 and Section 10 interface requirement.
        
        Recursively applies transition for H steps:
        Z_{t+k} = F(Z_{t+k-1}, u_{t+k-1}) for k=1..H
        
        Args:
            z0: [B, 256, 512] initial tokens
            a_seq: [B, H, A] action sequence
            H: rollout horizon (number of steps)
        
        Returns:
            z_pred: [B, H, 256, 512] predicted token sequence
        """
        B = z0.shape[0]
        assert a_seq.shape[1] == H, f"Action sequence length {a_seq.shape[1]} != horizon {H}"
        
        z_predictions = []
        z_t = z0
        
        for k in range(H):
            # Get action at step k: [B, A]
            a_t = a_seq[:, k, :]
            
            # Encode action: [B, A] → [B, 128]
            u_t = self.action_encoder(a_t)
            
            # Predict next state: [B, 256, 512]
            z_t = self.transition_model(z_t, u_t)
            
            z_predictions.append(z_t)
        
        # Stack predictions: [H, B, 256, 512] → [B, H, 256, 512]
        z_pred = torch.stack(z_predictions, dim=1)
        
        return z_pred
    
    def encode_targets(self, x: torch.Tensor) -> torch.Tensor:
        """Encode targets with stable target encoder (no gradient)

        Args:
            x: [B, C, 256, 256] target observations

        Returns:
            z_target: [B, 256, 512] stable target tokens
        """
        return self.target_encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent tokens to pixel-space imagery

        Requires decoder to be enabled (use_decoder=True).

        Args:
            z: Latent tokens [B, 256, D] or [B, H, 256, D]

        Returns:
            x_recon: Reconstructed imagery [B, 8, 256, 256] or [B, H, 8, 256, 256]

        Raises:
            RuntimeError: If decoder is not enabled
        """
        if self.decoder is None:
            raise RuntimeError(
                "Decoder not available. Create model with use_decoder=True "
                "to enable pixel-space decoding for visualization."
            )

        return self.decoder(z)
    
    def update_target_encoder(self, step: Optional[int] = None):
        """Update target encoder via EMA
        
        Should be called after optimizer.step() in training loop.
        
        Args:
            step: Current training step for EMA schedule
        """
        self.target_encoder.update_from_encoder(self.context_encoder, step=step)
    
    def get_config(self) -> Dict:
        """Return model configuration for checkpointing"""
        return {
            "in_channels": self.in_channels,
            "latent_dim": self.latent_dim,
            "action_dim": self.action_dim,
            "model_spec_version": "0.2",
            "architecture": "jepa_token_world_model"
        }


def create_world_model_from_config(config: Dict) -> WorldModel:
    """Factory function to create world model from config dict
    
    Compatible with MODEL.md Section 9 config structure.
    
    Args:
        config: Configuration dict with model parameters
    
    Returns:
        WorldModel instance
    """
    # Extract config sections
    model_cfg = config.get("model", {})
    input_cfg = model_cfg.get("input", {})
    tokens_cfg = model_cfg.get("tokens", {})
    encoder_cfg = model_cfg.get("encoder", {}).get("transformer", {})
    transition_cfg = model_cfg.get("transition", {}).get("transformer", {})
    ema_cfg = model_cfg.get("ema", {})
    actions_cfg = model_cfg.get("actions", {})
    
    return WorldModel(
        # Input/output
        in_channels=input_cfg.get("channels", 8),
        latent_dim=tokens_cfg.get("dim", 512),
        action_dim=2,  # Default: rain + temp
        
        # Encoder
        encoder_blocks=encoder_cfg.get("layers", 4),
        encoder_heads=encoder_cfg.get("heads", 8),
        encoder_mlp_dim=encoder_cfg.get("mlp_dim", 2048),
        
        # Transition
        transition_blocks=transition_cfg.get("layers", 6),
        transition_heads=transition_cfg.get("heads", 8),
        transition_mlp_dim=transition_cfg.get("mlp_dim", 2048),
        
        # EMA
        tau_start=ema_cfg.get("tau_start", 0.99),
        tau_end=ema_cfg.get("tau_end", 0.995),
        warmup_steps=ema_cfg.get("warmup_steps", 2000),
        
        # Conditioning
        use_film=actions_cfg.get("film", True),
        use_action_token=actions_cfg.get("action_token", True),
        
        # Regularization
        dropout=encoder_cfg.get("dropout", 0.0)
    )
