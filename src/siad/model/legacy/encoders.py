"""Encoders for SIAD World Model

Components:
    - ObsEncoder: Observation encoder (8-channel GeoTIFF → latent z_t) using ResNet18
    - TargetEncoder: EMA-stabilized target encoder (8-channel → z̃_t) for JEPA-style training
    - ActionEncoder: Action encoder ([rain_anom, temp_anom] → latent u_t) using MLP
"""

import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights
from typing import Optional


class ObsEncoder(nn.Module):
    """Observation encoder: 8-channel GeoTIFF → latent representation

    Architecture: Modified ResNet18 with 8-channel input adaptation
    - Input: [B, 8, 256, 256] (S2: B2/B3/B4/B8, S1: VV/VH, VIIRS: lights, S2_valid: mask)
    - Output: [B, latent_dim]

    Reference: See docs/model-design.md Section 1
    """

    def __init__(self, in_channels: int = 8, latent_dim: int = 256, dropout: float = 0.1):
        super().__init__()
        self.in_channels = in_channels
        self.latent_dim = latent_dim

        # Load pretrained ResNet18 and modify first conv for 8 channels
        resnet = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

        # Adapt first conv layer for 8-channel input
        # Original: Conv2d(3, 64, kernel_size=7, stride=2, padding=3)
        # New: Conv2d(8, 64, ...) with Xavier initialization
        original_conv = resnet.conv1
        self.conv1 = nn.Conv2d(
            in_channels,
            original_conv.out_channels,
            kernel_size=original_conv.kernel_size,
            stride=original_conv.stride,
            padding=original_conv.padding,
            bias=False
        )
        # Initialize new channels with Xavier
        nn.init.xavier_uniform_(self.conv1.weight)

        # Copy ResNet layers (excluding first conv and final FC)
        self.bn1 = resnet.bn1
        self.relu = resnet.relu
        self.maxpool = resnet.maxpool
        self.layer1 = resnet.layer1
        self.layer2 = resnet.layer2
        self.layer3 = resnet.layer3
        self.layer4 = resnet.layer4
        self.avgpool = resnet.avgpool

        # Replace final FC with projection to latent_dim
        # ResNet18 final feature dim: 512
        self.fc = nn.Sequential(
            nn.Linear(512, latent_dim),
            nn.BatchNorm1d(latent_dim),
            nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, 8, 256, 256] observation tensor

        Returns:
            z: [B, latent_dim] latent representation
        """
        # ResNet backbone
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        # Global average pooling
        x = self.avgpool(x)
        x = torch.flatten(x, 1)  # [B, 512]

        # Project to latent space
        z = self.fc(x)  # [B, latent_dim]

        return z


class TargetEncoder(nn.Module):
    """EMA-stabilized target encoder for JEPA-style training

    Architecture: Exact copy of ObsEncoder, updated via exponential moving average
    - No gradient flow (parameters updated via EMA, not backprop)
    - Provides stable targets z̃_t for consistency loss

    EMA Update (performed in training loop):
        θ̄ ← momentum × θ̄ + (1 - momentum) × θ
        where momentum ∈ [0.99, 0.999], default 0.996

    Reference: See docs/model-design.md Section 2
    """

    def __init__(self, in_channels: int = 8, latent_dim: int = 256, dropout: float = 0.1):
        super().__init__()
        # Create identical architecture to ObsEncoder
        self.encoder = ObsEncoder(in_channels, latent_dim, dropout)

        # Disable gradient tracking for EMA parameters
        for param in self.encoder.parameters():
            param.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, 8, 256, 256] observation tensor

        Returns:
            z_tilde: [B, latent_dim] stable target latent (no gradient)
        """
        with torch.no_grad():
            z_tilde = self.encoder(x)
        return z_tilde

    @torch.no_grad()
    def update_from_encoder(self, obs_encoder: ObsEncoder, momentum: float = 0.996):
        """Update target encoder parameters via EMA from observation encoder

        Called after optimizer.step() in training loop.

        Args:
            obs_encoder: Source observation encoder with updated parameters
            momentum: EMA momentum (higher = slower update), default 0.996
        """
        for target_param, source_param in zip(
            self.encoder.parameters(), obs_encoder.parameters()
        ):
            target_param.data.mul_(momentum).add_(source_param.data, alpha=1 - momentum)


class ActionEncoder(nn.Module):
    """Action encoder: [rain_anom, temp_anom] → latent action embedding

    Architecture: 2-layer MLP with ReLU activation
    - Input: [B, 2] (rainfall anomaly, temperature anomaly)
    - Output: [B, latent_dim]

    Reference: See docs/model-design.md Section 3
    """

    def __init__(self, action_dim: int = 2, latent_dim: int = 256, hidden_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.action_dim = action_dim
        self.latent_dim = latent_dim

        self.mlp = nn.Sequential(
            nn.Linear(action_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, latent_dim)
        )

    def forward(self, a: torch.Tensor) -> torch.Tensor:
        """
        Args:
            a: [B, 2] action vector [rain_anom, temp_anom]

        Returns:
            u: [B, latent_dim] action embedding
        """
        u = self.mlp(a)
        return u
