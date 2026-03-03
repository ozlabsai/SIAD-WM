#!/usr/bin/env python3
"""Generate gallery of predictions for SIAD Command Center demo

Pre-computes predictions on all tiles and curates best/worst/average examples.
Saves results as compressed numpy arrays for fast demo loading.

Usage:
    uv run python scripts/generate_gallery.py \
        --checkpoint checkpoints/checkpoint_best.pth \
        --decoder-checkpoint checkpoints/decoder_best.pth \
        --manifest data/manifest_22tiles_val.jsonl \
        --output siad-command-center/data/gallery \
        --num-samples 15
"""

import argparse
import json
import numpy as np
import torch
from pathlib import Path
from tqdm import tqdm
import yaml

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


def generate_gallery(
    checkpoint_path: str,
    decoder_checkpoint_path: str,
    manifest_path: str,
    model_size: str,
    data_root: str,
    output_dir: str,
    num_samples: int = 15
):
    """Generate gallery of predictions"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("SIAD Gallery Generation")
    print("="*60)

    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    model_config = model_configs[model_size]

    # Create model with decoder
    print("\n1. Loading model...")
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=True,
        **model_config
    )

    # Load encoder
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)

    # Load decoder
    decoder_ckpt = torch.load(decoder_checkpoint_path, map_location=device)
    model.decoder.load_state_dict(decoder_ckpt['decoder_state_dict'])

    model.to(device)
    model.train(False)

    print(f"   ✓ Model loaded: {model_size}")
    print(f"   Encoder val loss: {checkpoint.get('best_val_loss', 'N/A')}")
    print(f"   Decoder val loss: {decoder_ckpt.get('val_loss', 'N/A')}")

    # Load dataset
    print("\n2. Loading dataset...")
    dataset = SIADDataset(
        manifest_path=manifest_path,
        context_length=1,
        rollout_horizon=6,
        normalize=True,
        data_root=data_root
    )
    print(f"   ✓ Loaded {len(dataset)} tiles")

    # Generate predictions
    print("\n3. Generating predictions...")
    results = []

    for idx in tqdm(range(min(num_samples, len(dataset))), desc="Processing tiles"):
        sample = dataset[idx]
        tile_id = sample['tile_id']

        # Get context and actions
        x_context = sample['obs_context'].unsqueeze(0).to(device)  # [1, 8, 256, 256]
        actions = sample['actions_rollout'].unsqueeze(0).to(device)  # [1, 6, 2]
        x_target = sample['obs_targets'].to(device)  # [6, 8, 256, 256]

        with torch.no_grad():
            # Encode context
            z0 = model.encode(x_context)  # [1, 256, D]

            # Rollout predictions
            z_pred = model.rollout(z0, actions, H=6)  # [1, 6, 256, D]

            # Decode to pixels
            x_pred = model.decode(z_pred)  # [1, 6, 8, 256, 256]

        # Compute MSE loss per timestep
        x_pred_np = x_pred[0].cpu().numpy()  # [6, 8, 256, 256]
        x_target_np = x_target.cpu().numpy()  # [6, 8, 256, 256]

        mse_per_step = []
        for t in range(6):
            mse = np.mean((x_pred_np[t] - x_target_np[t]) ** 2)
            mse_per_step.append(float(mse))

        avg_mse = np.mean(mse_per_step)

        # Create RGB composites for context and predictions
        context_rgb = create_rgb_composite(x_context[0].cpu().numpy())
        pred_rgbs = [create_rgb_composite(x_pred_np[t]) for t in range(6)]
        target_rgbs = [create_rgb_composite(x_target_np[t]) for t in range(6)]

        # Save result
        result = {
            'tile_id': tile_id,
            'mse_per_step': mse_per_step,
            'avg_mse': float(avg_mse),
            'context_rgb': context_rgb,
            'pred_rgbs': pred_rgbs,
            'target_rgbs': target_rgbs,
            'actions': actions[0].cpu().numpy().tolist()
        }
        results.append(result)

        # Save individual tile data
        tile_path = output_path / f"{tile_id}.npz"
        np.savez_compressed(
            tile_path,
            context_rgb=context_rgb,
            pred_rgbs=np.array(pred_rgbs),
            target_rgbs=np.array(target_rgbs),
            mse_per_step=np.array(mse_per_step),
            actions=actions[0].cpu().numpy()
        )

    # Sort results by average MSE
    results.sort(key=lambda x: x['avg_mse'])

    # Create gallery metadata
    gallery_meta = {
        'best': [results[i]['tile_id'] for i in range(min(5, len(results)))],
        'worst': [results[-(i+1)]['tile_id'] for i in range(min(5, len(results)))],
        'average': [results[len(results)//2 + i]['tile_id'] for i in range(-2, 3) if 0 <= len(results)//2 + i < len(results)]
    }

    # Save gallery metadata
    with open(output_path / "gallery.json", 'w') as f:
        json.dump(gallery_meta, f, indent=2)

    # Save statistics
    stats = {
        'num_tiles': len(results),
        'best_mse': results[0]['avg_mse'],
        'worst_mse': results[-1]['avg_mse'],
        'median_mse': results[len(results)//2]['avg_mse'],
        'mean_mse': float(np.mean([r['avg_mse'] for r in results]))
    }

    with open(output_path / "stats.json", 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\n{'='*60}")
    print("✓ Gallery generation complete!")
    print(f"{'='*60}")
    print(f"Output directory: {output_path}")
    print(f"Tiles processed: {len(results)}")
    print(f"Best MSE: {stats['best_mse']:.6f}")
    print(f"Worst MSE: {stats['worst_mse']:.6f}")
    print(f"Median MSE: {stats['median_mse']:.6f}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Generate SIAD demo gallery")
    parser.add_argument("--checkpoint", required=True, help="Path to encoder checkpoint")
    parser.add_argument("--decoder-checkpoint", required=True, help="Path to decoder checkpoint")
    parser.add_argument("--manifest", required=True, help="Path to validation manifest")
    parser.add_argument("--model-size", default="medium", choices=["tiny", "small", "medium", "large", "xlarge"])
    parser.add_argument("--data-root", required=True, help="Data root directory")
    parser.add_argument("--output", default="siad-command-center/data/gallery", help="Output directory")
    parser.add_argument("--num-samples", type=int, default=15, help="Number of tiles to process")

    args = parser.parse_args()

    generate_gallery(
        checkpoint_path=args.checkpoint,
        decoder_checkpoint_path=args.decoder_checkpoint,
        manifest_path=args.manifest,
        model_size=args.model_size,
        data_root=args.data_root,
        output_dir=args.output,
        num_samples=args.num_samples
    )


if __name__ == "__main__":
    main()
