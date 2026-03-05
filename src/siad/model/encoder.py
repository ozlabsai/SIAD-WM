"""Context Encoder for SIAD World Model

Implements MODEL.md Section 4.1: CNN stem + token transformer encoder
Produces spatial token grid [B, 256, 512] preserving geographic structure.

Architecture per MODEL.md:
- CNN stem: 3 conv layers → 128×128 feature map
- Patchify: 8×8 patches → 16×16 = 256 tokens
- Projection: flatten patches → D=512
- Token transformer: 4 blocks, 8 heads, FFN=2048
"""

import torch
import torch.nn as nn
from typing import Dict
import math


class CNNStem(nn.Module):
    """CNN stem per MODEL.md Section 4.1.1

    Input: [B, C, 256, 256]
    Output: [B, 128, 128, 128]

    Architecture:
    - Conv1: 3×3, stride=1, out=64 + GroupNorm + SiLU
    - Conv2: 3×3, stride=2, out=128 + GroupNorm + SiLU
    - Conv3: 3×3, stride=1, out=128 + GroupNorm + SiLU
    """

    def __init__(self, in_channels: int = 8, dropout: float = 0.0):
        super().__init__()

        # Conv1: 3×3, stride=1, out_ch=64
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.norm1 = nn.GroupNorm(num_groups=8, num_channels=64)
        self.act1 = nn.SiLU()

        # Conv2: 3×3, stride=2, out_ch=128
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False)
        self.norm2 = nn.GroupNorm(num_groups=16, num_channels=128)
        self.act2 = nn.SiLU()

        # Conv3: 3×3, stride=1, out_ch=128
        self.conv3 = nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1, bias=False)
        self.norm3 = nn.GroupNorm(num_groups=16, num_channels=128)
        self.act3 = nn.SiLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, C, 256, 256] input observations

        Returns:
            features: [B, 128, 128, 128] stem features
        """
        # Conv1: 256×256 → 256×256
        x = self.conv1(x)
        x = self.norm1(x)
        x = self.act1(x)

        # Conv2: 256×256 → 128×128
        x = self.conv2(x)
        x = self.norm2(x)
        x = self.act2(x)

        # Conv3: 128×128 → 128×128
        x = self.conv3(x)
        x = self.norm3(x)
        x = self.act3(x)

        return x


class Patchify(nn.Module):
    """Patchify + projection per MODEL.md Section 4.1.2

    Input: [B, 128, 128, 128] stem features
    Output: [B, 256, 512] spatial tokens

    Architecture:
    - Extract 8×8 patches from 128×128 feature map → 16×16 grid
    - Flatten each patch: 8×8×128 = 8192
    - Project to D=512 via Linear
    - Add learned 2D positional embeddings
    """

    def __init__(self, latent_dim: int = 512, stem_channels: int = 128, patch_size: int = 8):
        super().__init__()
        self.latent_dim = latent_dim
        self.stem_channels = stem_channels
        self.patch_size = patch_size

        # Patch dimension: patch_size^2 * stem_channels
        patch_dim = patch_size * patch_size * stem_channels

        # Linear projection to latent dim
        self.proj = nn.Linear(patch_dim, latent_dim)

        # Learned 2D positional embeddings for 16×16 grid
        self.pos_embed = nn.Parameter(torch.randn(1, 256, latent_dim) * 0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, 128, 128, 128] stem features

        Returns:
            tokens: [B, 256, 512] spatial tokens with positional embeddings
        """
        B, C, H, W = x.shape
        assert H == 128 and W == 128, f"Expected 128×128, got {H}×{W}"
        assert C == self.stem_channels, f"Expected {self.stem_channels} channels, got {C}"

        # Extract 8×8 patches using unfold
        # Unfold: [B, C, H, W] → [B, C, num_patches_h, num_patches_w, patch_h, patch_w]
        patches = x.unfold(2, self.patch_size, self.patch_size).unfold(3, self.patch_size, self.patch_size)
        # patches shape: [B, 128, 16, 16, 8, 8]

        # Reshape to [B, num_patches, patch_dim]
        patches = patches.contiguous().view(B, C, 16, 16, self.patch_size * self.patch_size)
        patches = patches.permute(0, 2, 3, 1, 4)  # [B, 16, 16, 128, 64]
        patches = patches.reshape(B, 256, -1)  # [B, 256, 128*64=8192]

        # Project to latent dimension
        tokens = self.proj(patches)  # [B, 256, 512]

        # Add positional embeddings
        tokens = tokens + self.pos_embed

        return tokens


class TransformerBlock(nn.Module):
    """Single transformer block with pre-LayerNorm

    Architecture per MODEL.md Section 4.1.3:
    - Pre-LN
    - Multi-head self-attention (8 heads)
    - Pre-LN
    - FFN (D → 2048 → D)
    """

    def __init__(self, dim: int = 512, num_heads: int = 8, mlp_dim: int = 2048, dropout: float = 0.0):
        super().__init__()

        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)

        self.norm2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_dim, dim),
            nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, N, D] tokens

        Returns:
            x: [B, N, D] transformed tokens
        """
        # Self-attention with pre-norm
        x_norm = self.norm1(x)
        attn_out, _ = self.attn(x_norm, x_norm, x_norm, need_weights=False)
        x = x + attn_out

        # FFN with pre-norm
        x = x + self.mlp(self.norm2(x))

        return x


class ContextEncoder(nn.Module):
    """Context Encoder per MODEL.md Section 4.1

    Full encoder: CNN stem + patchify + token transformer

    Input: [B, 8, 256, 256]
    Output: [B, 256, 512]
    """

    def __init__(
        self,
        in_channels: int = 8,
        latent_dim: int = 512,
        num_blocks: int = 4,
        num_heads: int = 8,
        mlp_dim: int = 2048,
        dropout: float = 0.0
    ):
        super().__init__()
        self.in_channels = in_channels
        self.latent_dim = latent_dim

        # CNN stem: [B, C, 256, 256] → [B, 128, 128, 128]
        self.stem = CNNStem(in_channels=in_channels, dropout=dropout)

        # Patchify + projection: [B, 128, 128, 128] → [B, 256, 512]
        self.patchify = Patchify(latent_dim=latent_dim, stem_channels=128, patch_size=8)

        # Token encoder transformer: 4 blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(dim=latent_dim, num_heads=num_heads, mlp_dim=mlp_dim, dropout=dropout)
            for _ in range(num_blocks)
        ])

        # Final layer norm
        self.norm = nn.LayerNorm(latent_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, 8, 256, 256] observation tensor

        Returns:
            z: [B, 256, 512] spatial token grid
        """
        # CNN stem
        features = self.stem(x)  # [B, 128, 128, 128]

        # Patchify + project
        tokens = self.patchify(features)  # [B, 256, 512]

        # Transformer blocks
        for block in self.blocks:
            tokens = block(tokens)

        # Final norm
        tokens = self.norm(tokens)

        return tokens

    def get_config(self) -> Dict:
        """Return configuration for checkpointing"""
        return {
            "in_channels": self.in_channels,
            "latent_dim": self.latent_dim,
            "architecture": "cnn_stem_token_transformer",
            "model_spec_version": "0.2"
        }


class TargetEncoderEMA(nn.Module):
    """Target encoder with EMA updates per MODEL.md Section 4.2

    Architecture: Exact copy of ContextEncoder
    Update rule: θ̄ ← τ θ̄ + (1-τ) θ

    EMA schedule per MODEL.md Section 9.1:
    - Start: τ=0.99
    - After warmup: τ=0.995 (or configurable)
    """

    def __init__(
        self,
        in_channels: int = 8,
        latent_dim: int = 512,
        num_blocks: int = 4,
        num_heads: int = 8,
        mlp_dim: int = 2048,
        dropout: float = 0.0,
        tau_start: float = 0.99,
        tau_end: float = 0.995,
        warmup_steps: int = 2000
    ):
        super().__init__()

        # Create encoder with same architecture as context encoder
        self.encoder = ContextEncoder(
            in_channels=in_channels,
            latent_dim=latent_dim,
            num_blocks=num_blocks,
            num_heads=num_heads,
            mlp_dim=mlp_dim,
            dropout=dropout
        )

        # Disable gradients for all parameters
        for param in self.encoder.parameters():
            param.requires_grad = False

        # EMA schedule parameters
        self.tau_start = tau_start
        self.tau_end = tau_end
        self.warmup_steps = warmup_steps
        self.current_step = 0

        # T019: Monotonicity tracking
        self.last_tau = tau_start  # Track last tau to enforce monotonicity

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, 8, 256, 256] observation tensor

        Returns:
            z_target: [B, 256, 512] stable target tokens (no gradient)
        """
        with torch.no_grad():
            z_target = self.encoder(x)
        return z_target

    def get_tau(self, step: int = None) -> float:
        """Get current EMA coefficient tau (T020)

        Per contracts/ema_api.md: Computes tau based on warmup schedule.

        Args:
            step: Training step (uses self.current_step if not provided)

        Returns:
            Current tau value
        """
        if step is None:
            step = self.current_step

        # Linear warmup schedule
        if step < self.warmup_steps:
            tau = self.tau_start + (self.tau_end - self.tau_start) * (step / self.warmup_steps)
        else:
            tau = self.tau_end

        return tau

    def get_ema_metrics(self, context_encoder: ContextEncoder) -> Dict:
        """Get EMA health metrics (T021)

        Per contracts/ema_api.md: Computes delta_ema and parameter norms.

        Args:
            context_encoder: Online encoder to compare against

        Returns:
            Dict with delta_stem, delta_transformer, encoder_norm, target_norm
        """
        metrics = {}

        # Compute parameter differences and norms per module group
        stem_deltas = []
        stem_encoder_params = []
        stem_target_params = []

        transformer_deltas = []
        transformer_encoder_params = []
        transformer_target_params = []

        for (name, target_param), (_, source_param) in zip(
            self.encoder.named_parameters(),
            context_encoder.named_parameters()
        ):
            # Absolute difference
            delta = (target_param.data - source_param.data).abs().mean().item()

            # Categorize by module (stem vs transformer)
            if "stem" in name:
                stem_deltas.append(delta)
                stem_encoder_params.append(source_param.data.norm().item())
                stem_target_params.append(target_param.data.norm().item())
            else:
                # Everything else is transformer (patchify, blocks, norm)
                transformer_deltas.append(delta)
                transformer_encoder_params.append(source_param.data.norm().item())
                transformer_target_params.append(target_param.data.norm().item())

        # Compute mean deltas
        metrics["delta_stem"] = sum(stem_deltas) / len(stem_deltas) if stem_deltas else 0.0
        metrics["delta_transformer"] = sum(transformer_deltas) / len(transformer_deltas) if transformer_deltas else 0.0

        # Compute total parameter norms
        metrics["encoder_norm"] = math.sqrt(sum(p ** 2 for p in stem_encoder_params + transformer_encoder_params))
        metrics["target_norm"] = math.sqrt(sum(p ** 2 for p in stem_target_params + transformer_target_params))

        return metrics

    @torch.no_grad()
    def update_from_encoder(self, context_encoder: ContextEncoder, step: int = None) -> Dict[str, float]:
        """Update target encoder via EMA from context encoder (T022: Enhanced)

        Per MODEL.md Section 4.2:
        θ̄ ← τ θ̄ + (1-τ) θ

        Enhanced per contracts/ema_api.md:
        - Enforces monotonic tau schedule
        - Returns EMA metrics

        Args:
            context_encoder: Source context encoder with updated parameters
            step: Current training step for EMA schedule (optional)

        Returns:
            Dict with tau and EMA health metrics
        """
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1

        # Compute current tau using get_tau() (T020)
        tau = self.get_tau(self.current_step)

        # T019: Enforce monotonicity
        assert tau >= self.last_tau, \
            f"EMA tau decreased: {self.last_tau:.6f} → {tau:.6f} (step {self.current_step})"

        self.last_tau = tau

        # EMA update: θ̄ ← τ θ̄ + (1-τ) θ
        for target_param, source_param in zip(
            self.encoder.parameters(),
            context_encoder.parameters()
        ):
            target_param.data.mul_(tau).add_(source_param.data, alpha=1 - tau)

        # T022: Return metrics (backward compatible - callers can ignore)
        metrics = self.get_ema_metrics(context_encoder)
        metrics["tau"] = tau

        return metrics
