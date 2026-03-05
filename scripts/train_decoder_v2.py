#!/usr/bin/env python3
"""Train improved Decoder V2 on predicted latents

Trains the improved decoder architecture with:
- Checkerboard-free upsampling (Upsample + Conv instead of ConvTranspose)
- Latent normalization (handles distribution shift)
- Residual connections (better gradients)

Usage:
    uv run python scripts/train_decoder_v2.py \
        --checkpoint checkpoints/checkpoint_best.pth \
        --manifest data/manifest_22tiles_train.jsonl \
        --val-manifest data/manifest_22tiles_val.jsonl \
        --model-size medium \
        --data-root /path/to/data \
        --epochs 30 \
        --output checkpoints/decoder_v2_best.pth
"""

import argparse
import torch
import torch.nn as nn
from pathlib import Path
from tqdm import tqdm
import yaml

from siad.model import WorldModel
from siad.model.decoder_v2 import SpatialDecoderV2
from siad.train.dataset import SIADDataset


def train_decoder_v2(
    model,
    loss_fn,
    train_dataset,
    val_dataset,
    epochs: int = 30,
    batch_size: int = 4,
    lr: float = 1e-4,
    device: str = "cuda",
    checkpoint_dir: Path = Path("checkpoints")
):
    """Train improved decoder on predicted latents"""

    optimizer = torch.optim.AdamW(model.decoder.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_loss = float('inf')

    for epoch in range(epochs):
        # Training
        model.decoder.train(True)
        train_losses = []

        print(f"\nEpoch {epoch + 1}/{epochs}")
        print("-" * 60)

        for idx in tqdm(range(len(train_dataset)), desc="Training"):
            sample = train_dataset[idx]

            x_context = sample['obs_context'].unsqueeze(0).to(device)
            actions = sample['actions_rollout'].unsqueeze(0).to(device)
            x_targets = sample['obs_targets'].unsqueeze(0).to(device)

            H = x_targets.shape[1]

            # Forward pass (encoder/transition frozen)
            with torch.no_grad():
                z0 = model.encode(x_context)
                z_pred = model.rollout(z0, actions, H=H)

            # Decode predictions (with gradient)
            x_pred = model.decode(z_pred)

            # Compute loss
            total_loss = 0
            for t in range(H):
                loss_t = loss_fn(x_pred[:, t], x_targets[:, t])
                total_loss += loss_t

            loss = total_loss / H

            # Backward
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.decoder.parameters(), 1.0)
            optimizer.step()

            train_losses.append(loss.item())

        avg_train_loss = sum(train_losses) / len(train_losses)

        # Validation
        model.decoder.train(False)
        val_losses = []

        with torch.no_grad():
            for idx in range(len(val_dataset)):
                sample = val_dataset[idx]
                x_context = sample['obs_context'].unsqueeze(0).to(device)
                actions = sample['actions_rollout'].unsqueeze(0).to(device)
                x_targets = sample['obs_targets'].unsqueeze(0).to(device)

                H = x_targets.shape[1]

                z0 = model.encode(x_context)
                z_pred = model.rollout(z0, actions, H=H)
                x_pred = model.decode(z_pred)

                total_loss = 0
                for t in range(H):
                    loss_t = loss_fn(x_pred[:, t], x_targets[:, t])
                    total_loss += loss_t

                loss = total_loss / H
                val_losses.append(loss.item())

        avg_val_loss = sum(val_losses) / len(val_losses)

        scheduler.step()

        print(f"  Train Loss: {avg_train_loss:.6f}")
        print(f"  Val Loss: {avg_val_loss:.6f}")
        print(f"  LR: {scheduler.get_last_lr()[0]:.6f}")

        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            checkpoint_path = checkpoint_dir / "decoder_v2_best.pth"
            torch.save({
                'decoder_state_dict': model.decoder.state_dict(),
                'epoch': epoch,
                'val_loss': avg_val_loss,
                'train_loss': avg_train_loss,
                'decoder_version': 'v2'
            }, checkpoint_path)
            print(f"  ✓ Saved best decoder V2: {checkpoint_path}")

    # Save final model
    final_path = checkpoint_dir / "decoder_v2_final.pth"
    torch.save({
        'decoder_state_dict': model.decoder.state_dict(),
        'epoch': epochs,
        'val_loss': avg_val_loss,
        'train_loss': avg_train_loss,
        'decoder_version': 'v2'
    }, final_path)

    print(f"\n✓ Training complete! Final decoder V2: {final_path}")
    print(f"  Best validation loss: {best_val_loss:.6f}")


def main():
    parser = argparse.ArgumentParser(description="Train improved decoder V2")
    parser.add_argument("--checkpoint", required=True, help="Path to encoder checkpoint")
    parser.add_argument("--model-size", required=True, choices=["tiny", "small", "medium", "large", "xlarge"])
    parser.add_argument("--manifest", required=True, help="Training manifest")
    parser.add_argument("--val-manifest", required=True, help="Validation manifest")
    parser.add_argument("--data-root", required=True, help="Data root directory")
    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))

    args = parser.parse_args()

    print("="*60)
    print("Train Improved Decoder V2")
    print("="*60)
    print("Improvements:")
    print("  ✓ Checkerboard-free upsampling")
    print("  ✓ Latent normalization for distribution shift")
    print("  ✓ Residual connections")
    print("="*60)

    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    model_config = model_configs[args.model_size]

    # Create model with V2 decoder
    print("\nLoading model...")
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=False,  # We'll add decoder manually
        **model_config
    )

    # Load encoder weights
    checkpoint = torch.load(args.checkpoint, map_location=args.device)
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)

    # Add V2 decoder
    model.decoder = SpatialDecoderV2(
        latent_dim=model_config['latent_dim'],
        use_latent_norm=True,
        use_residual=True
    )

    model.to(args.device)

    # Freeze encoder and transition
    for param in model.context_encoder.parameters():
        param.requires_grad = False
    for param in model.transition_model.parameters():
        param.requires_grad = False

    model.context_encoder.train(False)
    model.transition_model.train(False)

    print(f"✓ Model loaded: {args.model_size}")
    print(f"  Encoder frozen: {not any(p.requires_grad for p in model.context_encoder.parameters())}")
    print(f"  Transition frozen: {not any(p.requires_grad for p in model.transition_model.parameters())}")
    print(f"  Decoder V2 trainable: {any(p.requires_grad for p in model.decoder.parameters())}")

    # Loss function
    loss_fn = nn.MSELoss()

    # Load datasets
    print("\nLoading datasets...")
    train_dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=1,
        rollout_horizon=6,
        normalize=True,
        data_root=args.data_root
    )

    val_dataset = SIADDataset(
        manifest_path=args.val_manifest,
        context_length=1,
        rollout_horizon=6,
        normalize=True,
        data_root=args.data_root
    )

    print(f"  Train samples: {len(train_dataset)}")
    print(f"  Val samples: {len(val_dataset)}")

    # Train
    args.checkpoint_dir.mkdir(exist_ok=True)
    train_decoder_v2(
        model=model,
        loss_fn=loss_fn,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
        checkpoint_dir=args.checkpoint_dir
    )


if __name__ == "__main__":
    main()
