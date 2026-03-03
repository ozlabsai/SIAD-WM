#!/usr/bin/env python3
"""Train decoder for SIAD World Model

Trains a lightweight decoder to map latent tokens back to pixel space.
Strategy: Freeze encoder as teacher, train decoder with MSE loss.

Usage:
    uv run python scripts/train_decoder.py \
        --encoder-checkpoint checkpoints/checkpoint_best.pth \
        --manifest data/manifest_22tiles_train.jsonl \
        --val-manifest data/manifest_22tiles_val.jsonl \
        --epochs 20 \
        --output checkpoints/decoder.pth
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


def load_frozen_encoder(checkpoint_path: str, model_size: str, device: str = "cuda"):
    """Load encoder from checkpoint and freeze it

    Args:
        checkpoint_path: Path to trained model checkpoint
        model_size: Model size (tiny/small/medium/large/xlarge)
        device: Device to load on

    Returns:
        encoder: Frozen WorldModel with context_encoder only
    """
    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    if model_size not in model_configs:
        raise ValueError(f"Invalid model size: {model_size}")

    model_config = model_configs[model_size]

    # Create model WITHOUT decoder initially
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=False,  # Don't load decoder from checkpoint
        **model_config
    )

    # Load checkpoint weights
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)
    model.to(device)

    # Freeze encoder
    for param in model.context_encoder.parameters():
        param.requires_grad = False

    # Set encoder to evaluation mode (no dropout, batchnorm in inference mode)
    model.context_encoder.train(False)

    print(f"Loaded frozen encoder from: {checkpoint_path}")
    print(f"  Model size: {model_size}")
    print(f"  Latent dim: {model_config['latent_dim']}")
    print(f"  Encoder frozen: {not any(p.requires_grad for p in model.context_encoder.parameters())}")

    return model


def train_decoder(
    encoder,
    decoder,
    loss_fn,
    train_dataset,
    val_dataset,
    epochs: int = 20,
    batch_size: int = 8,
    lr: float = 1e-4,
    device: str = "cuda",
    checkpoint_dir: Path = Path("checkpoints")
):
    """Train decoder with frozen encoder

    Args:
        encoder: Frozen WorldModel with context_encoder
        decoder: SpatialDecoder to train
        loss_fn: Loss function (MSE or combined)
        train_dataset: Training dataset
        val_dataset: Validation dataset
        epochs: Number of training epochs
        batch_size: Batch size
        lr: Learning rate
        device: Device to train on
        checkpoint_dir: Where to save checkpoints
    """
    decoder = decoder.to(device)
    optimizer = torch.optim.AdamW(decoder.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # Training loop
    best_val_loss = float('inf')

    for epoch in range(epochs):
        # Training
        decoder.train()
        train_losses = []

        print(f"\nEpoch {epoch + 1}/{epochs}")
        print("-" * 60)

        for idx in tqdm(range(len(train_dataset)), desc="Training"):
            sample = train_dataset[idx]

            # Get context observation
            x = sample['obs_context'].unsqueeze(0).to(device)  # [1, 8, 256, 256]

            # Encode to latent (no gradient)
            with torch.no_grad():
                z = encoder.encode(x)  # [1, 256, D]

            # Decode back to pixels
            x_recon = decoder(z)  # [1, 8, 256, 256]

            # Compute loss
            loss = loss_fn(x_recon, x)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(decoder.parameters(), 1.0)
            optimizer.step()

            train_losses.append(loss.item())

        avg_train_loss = sum(train_losses) / len(train_losses)

        # Validation
        decoder.train(False)  # Set to evaluation mode
        val_losses = []

        with torch.no_grad():
            for idx in range(len(val_dataset)):
                sample = val_dataset[idx]
                x = sample['obs_context'].unsqueeze(0).to(device)

                z = encoder.encode(x)
                x_recon = decoder(z)
                loss = loss_fn(x_recon, x)

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
            checkpoint_path = checkpoint_dir / "decoder_best.pth"
            torch.save({
                'decoder_state_dict': decoder.state_dict(),
                'epoch': epoch,
                'val_loss': avg_val_loss,
                'train_loss': avg_train_loss
            }, checkpoint_path)
            print(f"  ✓ Saved best decoder: {checkpoint_path}")

    # Save final model
    final_path = checkpoint_dir / "decoder_final.pth"
    torch.save({
        'decoder_state_dict': decoder.state_dict(),
        'epoch': epochs,
        'val_loss': avg_val_loss,
        'train_loss': avg_train_loss
    }, final_path)
    print(f"\n✓ Training complete! Final decoder: {final_path}")
    print(f"  Best validation loss: {best_val_loss:.6f}")


def main():
    parser = argparse.ArgumentParser(description="Train SIAD decoder")
    parser.add_argument("--encoder-checkpoint", required=True, help="Path to trained encoder checkpoint")
    parser.add_argument("--model-size", required=True, choices=["tiny", "small", "medium", "large", "xlarge"],
                        help="Model size")
    parser.add_argument("--manifest", required=True, help="Training manifest path")
    parser.add_argument("--val-manifest", required=True, help="Validation manifest path")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--use-perceptual", action="store_true", help="Use perceptual loss")
    parser.add_argument("--perceptual-weight", type=float, default=0.1, help="Perceptual loss weight")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--data-root", type=str, default=None, help="Data root directory")

    args = parser.parse_args()

    print("="*60)
    print("SIAD Decoder Training")
    print("="*60)

    # Load frozen encoder
    encoder = load_frozen_encoder(args.encoder_checkpoint, args.model_size, args.device)

    # Create decoder and loss
    decoder, loss_fn = create_decoder_with_loss(
        latent_dim=encoder.latent_dim,
        use_perceptual=args.use_perceptual,
        perceptual_weight=args.perceptual_weight
    )

    # Load datasets
    print(f"\nLoading datasets...")
    train_dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=1,
        rollout_horizon=0,  # Only need context, no rollout
        normalize=True,
        data_root=args.data_root
    )

    val_dataset = SIADDataset(
        manifest_path=args.val_manifest,
        context_length=1,
        rollout_horizon=0,
        normalize=True,
        data_root=args.data_root
    )

    print(f"  Train samples: {len(train_dataset)}")
    print(f"  Val samples: {len(val_dataset)}")

    # Train decoder
    args.checkpoint_dir.mkdir(exist_ok=True)
    train_decoder(
        encoder=encoder,
        decoder=decoder,
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
