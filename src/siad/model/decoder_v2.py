"""SIAD Decoder V2 - Improved Architecture

Fixes for common decoder artifacts:
1. Replaces ConvTranspose2d with Upsample+Conv2d to eliminate checkerboard artifacts
2. Adds residual connections for better gradient flow
3. Adds latent normalization layer to handle distribution shift
4. Uses GroupNorm instead of BatchNorm for better stability

Architecture:
    Latent tokens [B, 256, D] → Unflatten [B, D, 16, 16] →
    → 4x Upsample+Conv+Residual blocks → [B, 8, 256, 256]
"""

import torch
import torch.nn as nn
from typing import Optional


class UpsampleBlock(nn.Module):
    """Improved upsampling block without checkerboard artifacts

    Uses bilinear upsampling + convolution instead of ConvTranspose2d
    to avoid checkerboard artifacts from overlapping kernels.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        use_residual: bool = True,
        dropout: float = 0.0
    ):
        super().__init__()
        self.use_residual = use_residual and (in_channels == out_channels)

        # Bilinear upsample (2x)
        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False)

        # 3x3 conv to reduce checkerboard (kernel_size=3 with stride=1)
        self.conv1 = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False
        )
        self.norm1 = nn.GroupNorm(num_groups=min(32, out_channels), num_channels=out_channels)
        self.act1 = nn.GELU()

        # Second conv for feature refinement
        self.conv2 = nn.Conv2d(
            out_channels,
            out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False
        )
        self.norm2 = nn.GroupNorm(num_groups=min(32, out_channels), num_channels=out_channels)
        self.act2 = nn.GELU()

        if dropout > 0:
            self.dropout = nn.Dropout2d(dropout)
        else:
            self.dropout = None

        # Residual connection (if dimensions match)
        if self.use_residual:
            self.residual_upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, in_channels, H, W]

        Returns:
            out: [B, out_channels, 2*H, 2*W]
        """
        # Save residual
        residual = x if self.use_residual else None

        # Upsample
        x = self.upsample(x)

        # First conv block
        x = self.conv1(x)
        x = self.norm1(x)
        x = self.act1(x)

        # Second conv block
        x = self.conv2(x)
        x = self.norm2(x)

        # Add residual if available
        if self.use_residual and residual is not None:
            residual = self.residual_upsample(residual)
            x = x + residual

        x = self.act2(x)

        if self.dropout is not None:
            x = self.dropout(x)

        return x


class LatentNormalization(nn.Module):
    """Normalize latent distribution to handle distribution shift

    Applies learned affine transformation to normalize latent tokens
    before decoding. Helps decoder generalize to predicted latents
    that may have different statistics than context latents.
    """

    def __init__(self, latent_dim: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps

        # Learnable affine parameters
        self.weight = nn.Parameter(torch.ones(1, 1, latent_dim))
        self.bias = nn.Parameter(torch.zeros(1, 1, latent_dim))

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z: [B, N, D] latent tokens

        Returns:
            z_norm: [B, N, D] normalized tokens
        """
        # Compute mean and std over spatial dimension
        mean = z.mean(dim=1, keepdim=True)  # [B, 1, D]
        var = z.var(dim=1, keepdim=True)  # [B, 1, D]
        std = torch.sqrt(var + self.eps)

        # Normalize
        z_norm = (z - mean) / std

        # Apply learnable affine transformation
        z_norm = z_norm * self.weight + self.bias

        return z_norm


class SpatialDecoderV2(nn.Module):
    """Improved decoder with checkerboard-free upsampling

    Improvements over V1:
    1. Upsample+Conv instead of ConvTranspose (fixes checkerboard)
    2. Residual connections (better gradients)
    3. Latent normalization (handles distribution shift)
    4. GroupNorm instead of BatchNorm (more stable)

    Architecture:
        Input: [B, 256, latent_dim] tokens
        → Latent Normalization
        → Reshape: [B, latent_dim, 16, 16]
        → 4x UpsampleBlock → [B, 8, 256, 256]
    """

    def __init__(
        self,
        latent_dim: int = 512,
        out_channels: int = 8,
        hidden_dims: tuple = (256, 128, 64, 32),
        use_latent_norm: bool = True,
        use_residual: bool = True,
        dropout: float = 0.0
    ):
        super().__init__()

        self.latent_dim = latent_dim
        self.out_channels = out_channels
        self.use_latent_norm = use_latent_norm

        # Latent normalization
        if use_latent_norm:
            self.latent_norm = LatentNormalization(latent_dim)

        # Build decoder blocks
        layers = []
        in_dim = latent_dim

        for i, hidden_dim in enumerate(hidden_dims):
            # Use residual connections except for first block (dimension change)
            use_res = use_residual and (i > 0 or in_dim == hidden_dim)

            layers.append(UpsampleBlock(
                in_dim,
                hidden_dim,
                use_residual=use_res,
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

        # Apply latent normalization if enabled
        if self.use_latent_norm:
            z = self.latent_norm(z)

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


def create_decoder_v2(
    latent_dim: int = 512,
    use_latent_norm: bool = True,
    use_residual: bool = True
) -> SpatialDecoderV2:
    """Helper to create improved decoder

    Args:
        latent_dim: Latent token dimension
        use_latent_norm: Whether to normalize latents (recommended for predicted latents)
        use_residual: Whether to use residual connections (recommended)

    Returns:
        decoder: SpatialDecoderV2 instance
    """
    return SpatialDecoderV2(
        latent_dim=latent_dim,
        out_channels=8,
        hidden_dims=(256, 128, 64, 32),
        use_latent_norm=use_latent_norm,
        use_residual=use_residual,
        dropout=0.0
    )


# Backward compatibility: export with old name
def create_improved_decoder(latent_dim: int = 512) -> SpatialDecoderV2:
    """Backward compatible wrapper"""
    return create_decoder_v2(latent_dim=latent_dim)
