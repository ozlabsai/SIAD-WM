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
import yaml

from siad.model import WorldModel
from siad.train.dataset import SIADDataset
from siad.train.trainer import Trainer


def main():
    parser = argparse.ArgumentParser(description="Train SIAD World Model")
    parser.add_argument("--manifest", type=str, required=True, help="Path to manifest.jsonl")
    parser.add_argument("--data-root", type=str, default=None, help="Root directory for data files")
    parser.add_argument("--model-size", type=str, default="tiny",
                       choices=["tiny", "small", "medium", "large", "xlarge"],
                       help="Model size from configs/model_sizes.yaml")
    parser.add_argument("--context-length", type=int, default=1, choices=[1, 3, 6],
                       help="Context length in months (1, 3, or 6). Memory usage: "
                            "1 month=32 batch, 3 months=24 batch, 6 months=16 batch")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--num-workers", type=int, default=16, help="DataLoader workers")
    parser.add_argument("--augment", action="store_true", help="Enable data augmentation (flips, rotations, brightness)")
    parser.add_argument("--wandb", action="store_true", help="Enable Weights & Biases logging")
    parser.add_argument("--wandb-project", type=str, default="siad-world-model", help="Wandb project name")
    parser.add_argument("--wandb-name", type=str, default=None, help="Wandb run name")
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
    print(f"Context length: {args.context_length} month(s)")

    # Recommend batch size based on context length (memory usage guidance)
    recommended_batch_sizes = {1: 32, 3: 24, 6: 16}
    if args.batch_size == 32 and args.context_length in recommended_batch_sizes:
        recommended = recommended_batch_sizes[args.context_length]
        if args.batch_size != recommended:
            print(f"NOTE: For context_length={args.context_length}, recommended batch_size={recommended}")
            print(f"      (you are using batch_size={args.batch_size})")

    # Create training dataset with augmentation (if enabled)
    train_dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=args.context_length,
        rollout_horizon=6,
        data_root=args.data_root,
        normalize=True,
        augment=args.augment
    )

    # Create validation dataset WITHOUT augmentation
    val_dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=args.context_length,
        rollout_horizon=6,
        data_root=args.data_root,
        normalize=True,
        augment=False  # Never augment validation data
    )

    # Split train/val (80/20) using indices
    train_size = int(0.8 * len(train_dataset))
    val_size = len(train_dataset) - train_size

    indices = torch.randperm(len(train_dataset)).tolist()
    train_indices = indices[:train_size]
    val_indices = indices[train_size:]

    train_dataset = torch.utils.data.Subset(train_dataset, train_indices)
    val_dataset = torch.utils.data.Subset(val_dataset, val_indices)

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

    # Load model configuration
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    model_config = model_configs[args.model_size]
    print(f"\nCreating '{args.model_size}' model...")
    print(f"  Config: {config_path}")

    # Create model from config
    model = WorldModel(
        in_channels=8,
        action_dim=2,  # rain + temp anomalies
        **model_config
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
        device=device,
        use_wandb=args.wandb,
        wandb_project=args.wandb_project,
        wandb_name=args.wandb_name
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
