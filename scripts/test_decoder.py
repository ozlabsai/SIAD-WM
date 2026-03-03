#!/usr/bin/env python3
"""Test decoder by generating sample predictions

Loads encoder + decoder and generates RGB visualizations.
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from siad.model import WorldModel
from siad.train.dataset import SIADDataset


def create_rgb_composite(bands: np.ndarray) -> np.ndarray:
    """Create RGB from 8-band satellite image"""
    rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]

    for i in range(3):
        channel = rgb[:, :, i]
        vmin, vmax = np.percentile(channel, [2, 98])
        rgb[:, :, i] = np.clip((channel - vmin) / (vmax - vmin + 1e-8), 0, 1)

    return rgb


def test_decoder(
    encoder_checkpoint: str,
    decoder_checkpoint: str,
    model_size: str,
    manifest: str,
    data_root: str,
    output_dir: str = "decoder_test_outputs",
    num_samples: int = 3
):
    """Test decoder on sample tiles"""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    model_config = model_configs[model_size]

    # Create model with decoder
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=True,
        **model_config
    )

    # Load checkpoints
    print("Loading model...")
    checkpoint = torch.load(encoder_checkpoint, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)

    decoder_ckpt = torch.load(decoder_checkpoint, map_location=device)
    model.decoder.load_state_dict(decoder_ckpt['decoder_state_dict'])

    model.to(device)
    model.train(False)

    print(f"Model loaded: {model_size}")
    print(f"  Decoder val loss: {decoder_ckpt.get('val_loss', 'N/A')}")

    # Load dataset
    dataset = SIADDataset(
        manifest_path=manifest,
        context_length=1,
        rollout_horizon=1,
        normalize=True,
        data_root=data_root
    )

    # Test on samples
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"\nTesting decoder on {num_samples} samples...")

    for idx in range(min(num_samples, len(dataset))):
        sample = dataset[idx]
        tile_id = sample['tile_id']

        print(f"\n  Sample {idx + 1}/{num_samples}: {tile_id}")

        # Get context
        x = sample['obs_context'].unsqueeze(0).to(device)  # [1, 8, 256, 256]

        with torch.no_grad():
            # Encode
            z = model.encode(x)  # [1, 256, D]

            # Decode
            x_recon = model.decode(z)  # [1, 8, 256, 256]

        # Convert to numpy
        x_np = x[0].cpu().numpy()  # [8, 256, 256]
        x_recon_np = x_recon[0].cpu().numpy()  # [8, 256, 256]

        # Create RGB composites
        rgb_original = create_rgb_composite(x_np)
        rgb_recon = create_rgb_composite(x_recon_np)

        # Compute error
        mse = np.mean((x_np - x_recon_np) ** 2)

        # Visualize
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        axes[0].imshow(rgb_original)
        axes[0].set_title(f"Original\n{tile_id}", fontsize=12, fontweight='bold')
        axes[0].axis('off')

        axes[1].imshow(rgb_recon)
        axes[1].set_title(f"Reconstructed\nMSE: {mse:.6f}", fontsize=12)
        axes[1].axis('off')

        # Difference
        diff = np.abs(rgb_original - rgb_recon)
        axes[2].imshow(diff, cmap='hot')
        axes[2].set_title("Abs Difference", fontsize=12)
        axes[2].axis('off')

        plt.tight_layout()

        save_path = output_path / f"{tile_id}_decoder_test.png"
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"    MSE: {mse:.6f}")
        print(f"    Saved: {save_path}")

    print(f"\n✓ Decoder test complete! Outputs in: {output_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--encoder-checkpoint", required=True)
    parser.add_argument("--decoder-checkpoint", required=True)
    parser.add_argument("--model-size", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output-dir", default="decoder_test_outputs")
    parser.add_argument("--num-samples", type=int, default=3)

    args = parser.parse_args()

    test_decoder(
        encoder_checkpoint=args.encoder_checkpoint,
        decoder_checkpoint=args.decoder_checkpoint,
        model_size=args.model_size,
        manifest=args.manifest,
        data_root=args.data_root,
        output_dir=args.output_dir,
        num_samples=args.num_samples
    )
