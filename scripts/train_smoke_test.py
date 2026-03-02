#!/usr/bin/env python3
"""Smoke test for SIAD world model training

Tests the full training pipeline on synthetic data (no real GeoTIFFs required).
Trains for 10 steps on 2 mock tiles × 12 months.

Usage:
    uv run scripts/train_smoke_test.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
import numpy as np
from torch.utils.data import DataLoader, Dataset
from siad.model import WorldModel
from siad.train import Trainer


class SyntheticDataset(Dataset):
    """Synthetic dataset for smoke testing (no GeoTIFF loading required)"""

    def __init__(self, num_samples: int = 10, context_length: int = 6, rollout_horizon: int = 6):
        self.num_samples = num_samples
        self.context_length = context_length
        self.rollout_horizon = rollout_horizon

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # Generate random observations: [L/H, C=8, H=256, W=256]
        obs_context = torch.randn(self.context_length, 8, 256, 256)
        obs_targets = torch.randn(self.rollout_horizon, 8, 256, 256)

        # Generate random actions: [H, 2]
        actions_rollout = torch.randn(self.rollout_horizon, 2)

        return {
            "obs_context": obs_context,
            "actions_rollout": actions_rollout,
            "obs_targets": obs_targets,
            "tile_id": f"synthetic_tile_{idx:03d}",
            "months_context": [f"2023-{m:02d}" for m in range(1, 7)],
            "months_rollout": [f"2023-{m:02d}" for m in range(7, 13)]
        }


def main():
    print("=" * 80)
    print("SIAD World Model - Smoke Test")
    print("=" * 80)

    # Configuration
    config = {
        "learning_rate": 1e-3,  # Higher LR for faster convergence on synthetic data
        "weight_decay": 1e-5,
        "epochs": 3,  # Just 3 epochs for smoke test
        "ema_momentum": 0.996,
        "grad_clip_norm": 1.0,
        "loss_type": "cosine",
        "save_every": 1,
        "seed": 42,
        "context_length": 6,
        "rollout_horizon": 6,
        "band_order_version": "v1"
    }

    # Create synthetic datasets
    print("\n1. Creating synthetic datasets...")
    train_dataset = SyntheticDataset(num_samples=20)  # 20 training samples
    val_dataset = SyntheticDataset(num_samples=5)     # 5 validation samples

    train_loader = DataLoader(
        train_dataset,
        batch_size=4,  # Small batch for smoke test
        shuffle=True,
        num_workers=0
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=4,
        shuffle=False,
        num_workers=0
    )

    print(f"  Training samples: {len(train_dataset)}")
    print(f"  Validation samples: {len(val_dataset)}")

    # Initialize model
    print("\n2. Initializing WorldModel...")
    model = WorldModel(
        latent_dim=256,
        in_channels=8,
        action_dim=2,
        use_transformer=True,
        dropout=0.1
    )

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")

    # Test forward pass
    print("\n3. Testing forward pass...")
    # Set model to inference mode to avoid BatchNorm issues with batch_size=1
    model.train(False)
    with torch.no_grad():
        sample = train_dataset[0]
        obs_context = sample["obs_context"].unsqueeze(0)  # [1, L, C, H, W]
        actions_rollout = sample["actions_rollout"].unsqueeze(0)  # [1, H, 2]
        obs_targets = sample["obs_targets"].unsqueeze(0)  # [1, H, C, H, W]

        # Forward pass
        z_pred = model(obs_context, actions_rollout)
        print(f"  Input obs_context shape: {obs_context.shape}")
        print(f"  Input actions_rollout shape: {actions_rollout.shape}")
        print(f"  Output z_pred shape: {z_pred.shape}")

        # Test loss computation
        loss, metrics = model.compute_rollout_loss(
            obs_context, actions_rollout, obs_targets
        )
        print(f"  Initial loss: {loss.item():.4f}")
        print(f"  Metrics: {metrics}")

    # Initialize trainer
    print("\n4. Initializing Trainer...")
    checkpoint_dir = Path(__file__).parent.parent / "data" / "smoke_test_checkpoints"
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        checkpoint_dir=str(checkpoint_dir),
        device=torch.device("cpu")  # Use CPU for smoke test
    )

    # Train
    print("\n5. Starting training...")
    print("-" * 80)
    history = trainer.train()

    # Summary
    print("\n" + "=" * 80)
    print("Smoke Test Summary")
    print("=" * 80)
    print(f"Training completed successfully!")
    print(f"  Final train loss: {history['train_losses'][-1]:.4f}")
    print(f"  Final val loss: {history['val_losses'][-1]:.4f}")
    print(f"  Best val loss: {history['best_val_loss']:.4f}")
    print(f"  Checkpoints saved to: {checkpoint_dir}")

    # Verify checkpoint loading
    print("\n6. Verifying checkpoint loading...")
    best_checkpoint = checkpoint_dir / "checkpoint_best.pth"
    if best_checkpoint.exists():
        checkpoint = torch.load(best_checkpoint, map_location="cpu")
        print(f"  Loaded checkpoint from epoch {checkpoint['epoch']}")
        print(f"  Config keys: {list(checkpoint['config'].keys())}")
        print("  Checkpoint verification: PASSED")
    else:
        print("  ERROR: Best checkpoint not found!")
        return 1

    print("\n" + "=" * 80)
    print("Smoke test PASSED - All components working correctly!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
