#!/usr/bin/env python3
"""Complete training script for SIAD on A100

This script ties everything together:
- Loads data from manifest
- Creates model
- Initializes trainer
- Starts training
"""

import torch
from torch.utils.data import DataLoader
from pathlib import Path
import argparse

from siad.model import WorldModel
from siad.train.dataset import SIADDataset
from siad.train.trainer import Trainer


def main():
    parser = argparse.ArgumentParser(description="Train SIAD World Model")
    parser.add_argument("--manifest", type=str, required=True, help="Path to manifest.jsonl")
    parser.add_argument("--data-root", type=str, default=None, help="Root directory for data files")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--num-workers", type=int, default=16, help="DataLoader workers")
    args = parser.parse_args()

    print("="*60)
    print("SIAD World Model Training")
    print("="*60)

    # Check GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.cuda.is_available():
        print(f"\nGPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("\n⚠️  No GPU detected, training will be slow!")

    # Load dataset
    print(f"\nLoading dataset from: {args.manifest}")
    dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=6,
        rollout_horizon=6,
        data_root=args.data_root,
        normalize=True
    )

    # Split train/val (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )

    print(f"  Train samples: {len(train_dataset)}")
    print(f"  Val samples: {len(val_dataset)}")

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True
    )

    # Create model
    print("\nCreating model...")
    model = WorldModel(
        in_channels=8,
        latent_dim=512,
        action_dim=2,  # rain + temp anomalies
        encoder_blocks=4,
        encoder_heads=8,
        encoder_mlp_dim=2048,
        transition_blocks=6,
        transition_heads=8,
        transition_mlp_dim=2048,
        dropout=0.1
    )

    params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {params:,}")
    print(f"  Size: {params * 4 / 1024**3:.2f} GB (fp32)")

    # Create trainer
    print("\nInitializing trainer...")
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config={
            "learning_rate": args.lr,
            "weight_decay": 1e-5,
            "epochs": args.epochs,
            "grad_clip_norm": 1.0,
            "save_every": 5,
            "seed": 42,
            "rollout_horizon": 6,
        },
        checkpoint_dir=args.checkpoint_dir,
        device=device
    )

    # Train!
    print("\n" + "="*60)
    print("Starting Training")
    print("="*60)

    history = trainer.train()

    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    print(f"Best validation loss: {history['best_val_loss']:.4f}")
    print(f"Final checkpoint: {args.checkpoint_dir}/checkpoint_final.pth")


if __name__ == "__main__":
    main()
