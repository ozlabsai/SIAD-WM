"""HuggingFace-compatible SIAD World Model

Wraps the core WorldModel with HF PreTrainedModel interface for:
- Proper model hub integration
- save_pretrained() / from_pretrained()
- Model card generation
- Compatible with HF ecosystem
"""

from typing import Optional, Dict, Any
import torch
import torch.nn as nn
from transformers import PreTrainedModel, PretrainedConfig
from transformers.modeling_outputs import ModelOutput
from dataclasses import dataclass

from .wm import WorldModel


@dataclass
class WorldModelOutput(ModelOutput):
    """Output of SIAD World Model forward pass
    
    Compatible with HuggingFace ModelOutput interface.
    """
    loss: Optional[torch.Tensor] = None
    predictions: Optional[torch.Tensor] = None
    latent_predictions: Optional[torch.Tensor] = None
    latent_targets: Optional[torch.Tensor] = None
    metrics: Optional[Dict[str, float]] = None


class SIADConfig(PretrainedConfig):
    """Configuration for SIAD World Model
    
    Compatible with HuggingFace PretrainedConfig.
    """
    model_type = "siad-world-model"
    
    def __init__(
        self,
        in_channels: int = 8,
        latent_dim: int = 512,
        action_dim: int = 2,
        encoder_blocks: int = 4,
        encoder_heads: int = 8,
        encoder_mlp_dim: int = 2048,
        transition_blocks: int = 6,
        transition_heads: int = 8,
        transition_mlp_dim: int = 2048,
        dropout: float = 0.1,
        ema_decay: float = 0.996,
        ema_warmup_steps: int = 1000,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.in_channels = in_channels
        self.latent_dim = latent_dim
        self.action_dim = action_dim
        self.encoder_blocks = encoder_blocks
        self.encoder_heads = encoder_heads
        self.encoder_mlp_dim = encoder_mlp_dim
        self.transition_blocks = transition_blocks
        self.transition_heads = transition_heads
        self.transition_mlp_dim = transition_mlp_dim
        self.dropout = dropout
        self.ema_decay = ema_decay
        self.ema_warmup_steps = ema_warmup_steps


class SIADWorldModel(PreTrainedModel):
    """HuggingFace-compatible SIAD World Model
    
    Wraps the core WorldModel with HF interface for proper model hub integration.
    
    Usage:
        # Load from HF Hub
        model = SIADWorldModel.from_pretrained("username/siad-tiny")
        
        # Save to HF Hub
        model.save_pretrained("./local_dir")
        model.push_to_hub("username/siad-tiny")
    """
    config_class = SIADConfig
    
    def __init__(self, config: SIADConfig):
        super().__init__(config)
        
        # Create core WorldModel
        # Note: WorldModel handles EMA internally, doesn't take ema_* params in __init__
        self.model = WorldModel(
            in_channels=config.in_channels,
            latent_dim=config.latent_dim,
            action_dim=config.action_dim,
            encoder_blocks=config.encoder_blocks,
            encoder_heads=config.encoder_heads,
            encoder_mlp_dim=config.encoder_mlp_dim,
            transition_blocks=config.transition_blocks,
            transition_heads=config.transition_heads,
            transition_mlp_dim=config.transition_mlp_dim,
            dropout=config.dropout
        )
        
        # For HF compatibility
        self.config = config
    
    def forward(
        self,
        obs_context: torch.Tensor,
        actions_rollout: torch.Tensor,
        obs_targets: Optional[torch.Tensor] = None,
        return_dict: bool = True
    ) -> WorldModelOutput:
        """Forward pass
        
        Args:
            obs_context: [B, C, H, W] context observations
            actions_rollout: [B, H, action_dim] action sequence
            obs_targets: Optional [B, H, C, H, W] target observations for loss
            return_dict: Whether to return ModelOutput dict
            
        Returns:
            WorldModelOutput with predictions and optional loss
        """
        # Encode context
        z0 = self.model.encode(obs_context)
        
        # Rollout predictions
        H = actions_rollout.shape[1]
        z_pred = self.model.rollout(z0, actions_rollout, H=H)
        
        # Decode predictions
        x_pred = self.model.decode(z_pred)
        
        # Compute loss if targets provided
        loss = None
        metrics = None
        z_target = None
        
        if obs_targets is not None:
            # Encode targets
            B, H_batch, C, Hp, Wp = obs_targets.shape
            x_targets_flat = obs_targets.view(B * H_batch, C, Hp, Wp)
            z_target_flat = self.model.encode_targets(x_targets_flat)
            z_target = z_target_flat.view(B, H_batch, 256, self.config.latent_dim)
            
            # Compute JEPA loss
            from ..train.losses import compute_jepa_world_model_loss
            loss, metrics = compute_jepa_world_model_loss(z_pred, z_target)
        
        if return_dict:
            return WorldModelOutput(
                loss=loss,
                predictions=x_pred,
                latent_predictions=z_pred,
                latent_targets=z_target,
                metrics=metrics
            )
        
        return (loss, x_pred, z_pred, z_target, metrics)
    
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode observations to latent tokens"""
        return self.model.encode(x)
    
    def rollout(self, z0: torch.Tensor, actions: torch.Tensor, H: int) -> torch.Tensor:
        """Rollout latent predictions"""
        return self.model.rollout(z0, actions, H=H)
    
    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent tokens to observations"""
        return self.model.decode(z)
    
    def inference_mode(self):
        """Switch to inference mode (freeze target encoder)"""
        self.model.inference_mode()
    
    def update_target_encoder(self, step: int):
        """Update EMA target encoder"""
        self.model.update_target_encoder(step=step)
    
    @classmethod
    def from_checkpoint(cls, checkpoint_path: str, config: SIADConfig = None):
        """Load from training checkpoint
        
        Args:
            checkpoint_path: Path to .pth checkpoint file
            config: Optional config (will be inferred if not provided)
            
        Returns:
            SIADWorldModel instance with loaded weights
        """
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        
        # Infer config from checkpoint if not provided
        if config is None:
            state_dict = checkpoint['model_state_dict']
            
            # Infer latent_dim from encoder.pos_embed shape
            pos_embed_shape = state_dict['encoder.pos_embed'].shape
            latent_dim = pos_embed_shape[-1]
            
            # Use default config with inferred latent_dim
            config = SIADConfig(latent_dim=latent_dim)
        
        # Create model
        model = cls(config)
        
        # Load weights
        model.model.load_state_dict(checkpoint['model_state_dict'])
        
        return model


# Register with HuggingFace AutoModel
from transformers import AutoModel, AutoConfig

AutoConfig.register("siad-world-model", SIADConfig)
AutoModel.register(SIADConfig, SIADWorldModel)
