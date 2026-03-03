"""SIAD Decoder Module

Lightweight ConvTranspose decoder for visualization and demo purposes.
Maps latent token representations back to pixel-space satellite imagery.

Architecture:
    Latent tokens [B, 256, D] → Unflatten [B, D, 16, 16] →
    → ConvTranspose layers → [B, 8, 256, 256] GeoTIFF

Training strategy:
    - Freeze encoder as teacher
    - MSE loss in pixel space
    - Optional perceptual loss (VGG features)
"""

import torch
import torch.nn as nn
from typing import Optional


class SpatialDecoder(nn.Module):
    """Decoder from latent tokens to pixel-space GeoTIFF

    Maps 16x16 spatial token grid back to 256x256 pixel imagery.
    Uses ConvTranspose2d with careful upsampling to avoid checkerboard artifacts.

    Architecture:
        Input: [B, 256, latent_dim] tokens
        → Reshape: [B, latent_dim, 16, 16]
        → Block 1: ConvTranspose(latent_dim → 256, k=4, s=2, p=1) → 32x32
        → Block 2: ConvTranspose(256 → 128, k=4, s=2, p=1) → 64x64
        → Block 3: ConvTranspose(128 → 64, k=4, s=2, p=1) → 128x128
        → Block 4: ConvTranspose(64 → 32, k=4, s=2, p=1) → 256x256
        → Output projection: Conv1x1(32 → 8 channels)
    """

    def __init__(
        self,
        latent_dim: int = 512,
        out_channels: int = 8,
        hidden_dims: tuple = (256, 128, 64, 32),
        use_batch_norm: bool = True,
        dropout: float = 0.0
    ):
        super().__init__()

        self.latent_dim = latent_dim
        self.out_channels = out_channels

        # Build decoder blocks
        layers = []
        in_dim = latent_dim

        for hidden_dim in hidden_dims:
            layers.append(self._make_decoder_block(
                in_dim,
                hidden_dim,
                use_batch_norm=use_batch_norm,
                dropout=dropout
            ))
            in_dim = hidden_dim

        self.decoder_blocks = nn.Sequential(*layers)

        # Final output projection (no activation, for regression)
        self.output_proj = nn.Conv2d(
            hidden_dims[-1],
            out_channels,
            kernel_size=1,
            padding=0
        )

    def _make_decoder_block(
        self,
        in_channels: int,
        out_channels: int,
        use_batch_norm: bool = True,
        dropout: float = 0.0
    ) -> nn.Module:
        """Create a single decoder block with upsampling

        Each block:
            1. ConvTranspose2d (2x upsampling)
            2. Optional BatchNorm
            3. GELU activation
            4. Optional Dropout
        """
        layers = [
            nn.ConvTranspose2d(
                in_channels,
                out_channels,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=not use_batch_norm
            )
        ]

        if use_batch_norm:
            layers.append(nn.BatchNorm2d(out_channels))

        layers.append(nn.GELU())

        if dropout > 0:
            layers.append(nn.Dropout2d(dropout))

        return nn.Sequential(*layers)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent tokens to pixel-space imagery

        Args:
            z: Latent tokens [B, 256, latent_dim] or [B, H, 256, latent_dim]

        Returns:
            x_recon: Reconstructed imagery [B, 8, 256, 256] or [B, H, 8, 256, 256]
        """
        # Handle both single and multi-step inputs
        original_shape = z.shape
        if len(z.shape) == 4:  # [B, H, N, D]
            B, H, N, D = z.shape
            z = z.reshape(B * H, N, D)  # Flatten temporal dimension
            unflatten_temporal = True
        else:  # [B, N, D]
            B, N, D = z.shape
            unflatten_temporal = False

        # Reshape tokens to spatial grid: [B, 256, D] → [B, D, 16, 16]
        z_spatial = z.transpose(1, 2)  # [B, D, 256]
        z_spatial = z_spatial.reshape(z_spatial.shape[0], D, 16, 16)  # [B, D, 16, 16]

        # Apply decoder blocks (16x16 → 32x32 → 64x64 → 128x128 → 256x256)
        features = self.decoder_blocks(z_spatial)  # [B, hidden_dims[-1], 256, 256]

        # Project to output channels
        x_recon = self.output_proj(features)  # [B, 8, 256, 256]

        # Reshape back to temporal if needed
        if unflatten_temporal:
            x_recon = x_recon.reshape(B, H, self.out_channels, 256, 256)

        return x_recon


class PerceptualLoss(nn.Module):
    """Perceptual loss using pretrained VGG features

    Helps decoder learn more realistic textures beyond pixel-level MSE.
    Uses early VGG16 layers (relu1_2, relu2_2, relu3_3).

    Note: Requires adapting 8-channel satellite input to 3-channel RGB.
    Uses channels [2, 1, 0] (Red, Green, Blue) for natural color.
    """

    def __init__(
        self,
        feature_layers: tuple = ('relu1_2', 'relu2_2', 'relu3_3'),
        weights: tuple = (1.0, 1.0, 1.0)
    ):
        super().__init__()

        try:
            from torchvision.models import vgg16, VGG16_Weights
            vgg = vgg16(weights=VGG16_Weights.IMAGENET1K_V1).features
        except ImportError:
            raise ImportError(
                "Perceptual loss requires torchvision. "
                "Install with: pip install torchvision"
            )

        # Extract feature layers
        self.feature_extractors = nn.ModuleDict()
        layer_map = {
            'relu1_2': 4,
            'relu2_2': 9,
            'relu3_3': 16,
            'relu4_3': 23
        }

        for name in feature_layers:
            if name not in layer_map:
                raise ValueError(f"Unknown layer: {name}")
            self.feature_extractors[name] = vgg[:layer_map[name] + 1]

        # Freeze VGG
        for param in self.parameters():
            param.requires_grad = False

        self.weights = weights
        self.feature_layers = feature_layers

    def extract_rgb(self, x: torch.Tensor) -> torch.Tensor:
        """Extract RGB channels from 8-band satellite imagery

        Args:
            x: [B, 8, H, W] GeoTIFF with bands in BAND_ORDER_V1

        Returns:
            rgb: [B, 3, H, W] normalized RGB for VGG
        """
        # Extract R, G, B channels (indices 2, 1, 0)
        rgb = x[:, [2, 1, 0], :, :]  # [B, 3, H, W]

        # Normalize to ImageNet stats (VGG expects this)
        mean = torch.tensor([0.485, 0.456, 0.406], device=x.device).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], device=x.device).view(1, 3, 1, 1)

        rgb = (rgb - mean) / std
        return rgb

    def forward(
        self,
        x_pred: torch.Tensor,
        x_target: torch.Tensor
    ) -> torch.Tensor:
        """Compute perceptual loss between prediction and target

        Args:
            x_pred: Predicted imagery [B, 8, H, W]
            x_target: Target imagery [B, 8, H, W]

        Returns:
            loss: Weighted perceptual loss (scalar)
        """
        # Extract RGB
        rgb_pred = self.extract_rgb(x_pred)
        rgb_target = self.extract_rgb(x_target)

        # Compute feature loss for each layer
        total_loss = 0.0
        for (name, extractor), weight in zip(self.feature_extractors.items(), self.weights):
            feat_pred = extractor(rgb_pred)
            feat_target = extractor(rgb_target)

            # L1 loss in feature space
            layer_loss = torch.nn.functional.l1_loss(feat_pred, feat_target)
            total_loss += weight * layer_loss

        return total_loss


def create_decoder_with_loss(
    latent_dim: int = 512,
    use_perceptual: bool = False,
    perceptual_weight: float = 0.1
) -> tuple:
    """Helper to create decoder + combined loss function

    Args:
        latent_dim: Latent token dimension
        use_perceptual: Whether to include perceptual loss
        perceptual_weight: Weight for perceptual term

    Returns:
        decoder: SpatialDecoder module
        loss_fn: Combined loss function
    """
    decoder = SpatialDecoder(latent_dim=latent_dim)

    if use_perceptual:
        perceptual = PerceptualLoss()

        def combined_loss(x_pred, x_target):
            mse = nn.functional.mse_loss(x_pred, x_target)
            percept = perceptual(x_pred, x_target)
            return mse + perceptual_weight * percept

        return decoder, combined_loss
    else:
        return decoder, nn.MSELoss()
