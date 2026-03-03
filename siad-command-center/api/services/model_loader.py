"""Model loading and management service"""

import torch
import yaml
from pathlib import Path
from typing import Optional

# Add parent directory to path to import siad
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from siad.model import WorldModel
from siad.model.decoder import SpatialDecoder


class ModelService:
    """Service for loading and managing the SIAD World Model"""

    def __init__(self):
        self.model: Optional[WorldModel] = None
        self.decoder: Optional[SpatialDecoder] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_config = None

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.decoder is not None

    async def load_model(
        self,
        checkpoint_path: str,
        decoder_path: str,
        model_size: str = "medium"
    ):
        """Load model and decoder from checkpoints

        Args:
            checkpoint_path: Path to trained model checkpoint
            decoder_path: Path to trained decoder checkpoint
            model_size: Model size (tiny/small/medium/large/xlarge)
        """
        # Load model config
        config_path = Path(__file__).parent.parent.parent.parent / "configs" / "model_sizes.yaml"
        with open(config_path) as f:
            model_configs = yaml.safe_load(f)

        if model_size not in model_configs:
            raise ValueError(f"Invalid model size: {model_size}")

        self.model_config = model_configs[model_size]

        # Create model with decoder enabled
        self.model = WorldModel(
            in_channels=8,
            action_dim=2,
            use_decoder=True,  # Enable decoder
            **self.model_config
        )

        # Load model checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'], strict=False)

        # Load decoder checkpoint separately
        decoder_checkpoint = torch.load(decoder_path, map_location=self.device)
        self.model.decoder.load_state_dict(decoder_checkpoint['decoder_state_dict'])

        # Move to device and set to inference mode
        self.model.to(self.device)
        self.model.train(False)  # Evaluation mode

        print(f"Model loaded: {model_size}")
        print(f"  Parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        print(f"  Device: {self.device}")

    def get_model(self) -> WorldModel:
        """Get the loaded model"""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        return self.model

    @torch.no_grad()
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode observation to latent tokens"""
        return self.get_model().encode(x)

    @torch.no_grad()
    def rollout(
        self,
        z0: torch.Tensor,
        actions: torch.Tensor,
        horizon: int = 6
    ) -> torch.Tensor:
        """Multi-step rollout"""
        return self.get_model().rollout(z0, actions, horizon)

    @torch.no_grad()
    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent tokens to pixel space"""
        return self.get_model().decode(z)

    @torch.no_grad()
    def full_inference(
        self,
        x_context: torch.Tensor,
        actions: torch.Tensor,
        horizon: int = 6
    ) -> dict:
        """Complete inference pipeline: encode → rollout → decode

        Args:
            x_context: [B, 8, 256, 256] context observation
            actions: [B, H, 2] action sequence
            horizon: Rollout horizon (default: 6 months)

        Returns:
            dict with:
                - z0: Initial latent tokens
                - z_pred: Predicted latent sequence
                - x_pred: Decoded predictions [B, H, 8, 256, 256]
        """
        model = self.get_model()

        # Encode context
        z0 = model.encode(x_context)  # [B, 256, D]

        # Rollout in latent space
        z_pred = model.rollout(z0, actions, horizon)  # [B, H, 256, D]

        # Decode to pixel space
        x_pred = model.decode(z_pred)  # [B, H, 8, 256, 256]

        return {
            'z0': z0,
            'z_pred': z_pred,
            'x_pred': x_pred
        }
