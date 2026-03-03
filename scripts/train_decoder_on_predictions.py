#!/usr/bin/env python3
"""Retrain decoder on predicted latents (not just context)

The original decoder was trained only on context encodings.
This script trains it on PREDICTED latent tokens from the transition model,
ensuring the decoder works on the actual distribution it will see at inference.

Strategy:
1. Freeze encoder + transition model
2. For each sample:
   - Encode context
   - Rollout predictions in latent space (6 months)
   - Decode predictions to pixels
   - Compute loss against ground truth targets
3. Update only decoder weights

This fixes the issue where decoder generalizes poorly to predicted latents.

Usage:
    uv run python scripts/train_decoder_on_predictions.py \
        --encoder-checkpoint checkpoints/checkpoint_best.pth \
        --decoder-checkpoint checkpoints/decoder_best.pth \
        --manifest data/manifest_22tiles_train.jsonl \
        --val-manifest data/manifest_22tiles_val.jsonl \
        --epochs 20 \
        --output checkpoints/decoder_predictions.pth
"""

import argparse
import torch
import torch.nn as nn
from pathlib import Path
from tqdm import tqdm
import yaml

from siad.model import WorldModel
from siad.model.decoder import create_decoder_with_loss
from siad.train.dataset import SIADDataset


def load_frozen_model(checkpoint_path: str, model_size: str, device: str = "cuda"):
    """Load encoder + transition model and freeze them

    Returns model with frozen encoder/transition, unfrozen decoder
    """
    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    if model_size not in model_configs:
        raise ValueError(f"Invalid model size: {model_size}")

    model_config = model_configs[model_size]

    # Create model WITH decoder
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=True,
        **model_config
    )

    # Load encoder + transition weights
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)
    model.to(device)

    # Freeze encoder and transition model
    for param in model.context_encoder.parameters():
        param.requires_grad = False
    for param in model.transition_model.parameters():
        param.requires_grad = False

    # Keep encoder + transition in eval mode (no dropout)
    model.context_encoder.train(False)
    model.transition_model.train(False)

    # Decoder stays trainable
    for param in model.decoder.parameters():
        param.requires_grad = True

    print(f"Loaded frozen encoder+transition from: {checkpoint_path}")
    print(f"  Model size: {model_size}")
    print(f"  Latent dim: {model_config['latent_dim']}")
    print(f"  Encoder frozen: {not any(p.requires_grad for p in model.context_encoder.parameters())}")
    print(f"  Transition frozen: {not any(p.requires_grad for p in model.transition_model.parameters())}")
    print(f"  Decoder trainable: {any(p.requires_grad for p in model.decoder.parameters())}")

    return model


def train_decoder_on_predictions(
    model,
    loss_fn,
    train_dataset,
    val_dataset,
    epochs: int = 20,
    batch_size: int = 4,  # Smaller because we do 6-month rollouts
    lr: float = 1e-4,
    device: str = "cuda",
    checkpoint_dir: Path = Path("checkpoints")
):
    """Train decoder on predicted latents

    Key difference from original: We decode PREDICTED tokens, not context tokens
    """
    optimizer = torch.optim.AdamW(model.decoder.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_loss = float('inf')

    for epoch in range(epochs):
        # Training
        model.decoder.train(True)  # Decoder in training mode
        train_losses = []

        print(f"\nEpoch {epoch + 1}/{epochs}")
        print("-" * 60)

        for idx in tqdm(range(len(train_dataset)), desc="Training"):
            sample = train_dataset[idx]

            # Get context, actions, and targets
            x_context = sample['obs_context'].unsqueeze(0).to(device)  # [1, 8, 256, 256]
            actions = sample['actions_rollout'].unsqueeze(0).to(device)  # [1, H, 2]
            x_targets = sample['obs_targets'].unsqueeze(0).to(device)  # [1, H, 8, 256, 256]

            H = x_targets.shape[1]  # Rollout horizon (usually 6)

            # Forward pass (no gradient for encoder/transition)
            with torch.no_grad():
                # Encode context to latent
                z0 = model.encode(x_context)  # [1, 256, D]

                # Rollout predictions in latent space
                z_pred = model.rollout(z0, actions, H=H)  # [1, H, 256, D]

            # Decode predictions to pixels (WITH gradient)
            x_pred = model.decode(z_pred)  # [1, H, 8, 256, 256]

            # Compute loss against ground truth
            # Note: loss_fn expects [B, C, H, W] per timestep
            total_loss = 0
            for t in range(H):
                loss_t = loss_fn(x_pred[:, t], x_targets[:, t])
                total_loss += loss_t

            loss = total_loss / H  # Average over timesteps

            # Backward pass
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

                # Encode + rollout + decode
                z0 = model.encode(x_context)
                z_pred = model.rollout(z0, actions, H=H)
                x_pred = model.decode(z_pred)

                # Compute loss
                total_loss = 0
                for t in range(H):
                    loss_t = loss_fn(x_pred[:, t], x_targets[:, t])
                    total_loss += loss_t

                loss = total_loss / H
                val_losses.append(loss.item())

        avg_val_loss = sum(val_losses) / len(val_losses)

        # Learning rate step
        scheduler.step()

        # Print metrics
        print(f"  Train Loss: {avg_train_loss:.6f}")
        print(f"  Val Loss: {avg_val_loss:.6f}")
        print(f"  LR: {scheduler.get_last_lr()[0]:.6f}")

        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            checkpoint_path = checkpoint_dir / "decoder_predictions_best.pth"
            torch.save({
                'decoder_state_dict': model.decoder.state_dict(),
                'epoch': epoch,
                'val_loss': avg_val_loss,
                'train_loss': avg_train_loss
            }, checkpoint_path)
            print(f"  ✓ Saved best decoder: {checkpoint_path}")

    # Save final model
    final_path = checkpoint_dir / "decoder_predictions_final.pth"
    torch.save({
        'decoder_state_dict': model.decoder.state_dict(),
        'epoch': epochs,
        'val_loss': avg_val_loss,
        'train_loss': avg_train_loss
    }, final_path)
    print(f"\n✓ Training complete! Final decoder: {final_path}")
    print(f"  Best validation loss: {best_val_loss:.6f}")


def main():
    parser = argparse.ArgumentParser(description="Train decoder on predicted latents")
    parser.add_argument("--encoder-checkpoint", required=True, help="Path to encoder checkpoint")
    parser.add_argument("--decoder-checkpoint", default=None, help="Optional: Initialize from existing decoder")
    parser.add_argument("--model-size", required=True, choices=["tiny", "small", "medium", "large", "xlarge"])
    parser.add_argument("--manifest", required=True, help="Training manifest path")
    parser.add_argument("--val-manifest", required=True, help="Validation manifest path")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--use-perceptual", action="store_true", help="Use perceptual loss")
    parser.add_argument("--perceptual-weight", type=float, default=0.1, help="Perceptual loss weight")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--data-root", type=str, default=None, help="Data root directory")

    args = parser.parse_args()

    print("="*60)
    print("SIAD Decoder Retraining on Predictions")
    print("="*60)
    print("Strategy: Train decoder on rollout predictions, not just context")

    # Load frozen encoder + transition
    model = load_frozen_model(args.encoder_checkpoint, args.model_size, args.device)

    # Optionally load existing decoder weights as initialization
    if args.decoder_checkpoint:
        print(f"\nInitializing decoder from: {args.decoder_checkpoint}")
        decoder_ckpt = torch.load(args.decoder_checkpoint, map_location=args.device)
        model.decoder.load_state_dict(decoder_ckpt['decoder_state_dict'])
        print("  ✓ Decoder initialized")

    # Create loss function
    _, loss_fn = create_decoder_with_loss(
        latent_dim=model.latent_dim,
        use_perceptual=args.use_perceptual,
        perceptual_weight=args.perceptual_weight
    )

    # Load datasets
    print(f"\nLoading datasets...")
    train_dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=1,
        rollout_horizon=6,  # Full 6-month rollout
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

    # Train decoder
    args.checkpoint_dir.mkdir(exist_ok=True)
    train_decoder_on_predictions(
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
