#!/usr/bin/env python3
"""Compare original decoder vs improved decoder V2

Tests both architectures on the same samples to demonstrate improvement
in visual quality and artifact reduction.

Usage:
    uv run python scripts/compare_decoders.py \
        --checkpoint checkpoints/checkpoint_best.pth \
        --decoder-v1 checkpoints/decoder_best.pth \
        --decoder-v2 checkpoints/decoder_v2_best.pth \
        --manifest data/manifest_22tiles_val.jsonl \
        --model-size medium \
        --data-root /path/to/data \
        --output comparisons/
"""

import argparse
import numpy as np
import torch
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import yaml

from siad.model import WorldModel
from siad.model.decoder import SpatialDecoder
from siad.model.decoder_v2 import SpatialDecoderV2
from siad.train.dataset import SIADDataset


def create_rgb_composite(bands: np.ndarray) -> np.ndarray:
    """Create RGB from 8-band satellite image"""
    rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]

    for i in range(3):
        channel = rgb[:, :, i]
        vmin, vmax = np.percentile(channel, [2, 98])
        rgb[:, :, i] = np.clip((channel - vmin) / (vmax - vmin + 1e-8), 0, 1)

    return rgb


def compare_sample(
    model_v1,
    model_v2,
    sample,
    device,
    output_path: Path,
    sample_idx: int
):
    """Compare V1 vs V2 on a single sample"""

    x_context = sample['obs_context'].unsqueeze(0).to(device)
    actions = sample['actions_rollout'].unsqueeze(0).to(device)
    x_target = sample['obs_targets'][0].unsqueeze(0).to(device)

    with torch.no_grad():
        # Get latent encoding (same for both)
        z_context = model_v1.encode(x_context)
        z_pred = model_v1.rollout(z_context, actions[:, :1], H=1)

        # Decode with V1
        x_pred_v1 = model_v1.decode(z_pred[:, 0])

        # Decode with V2
        x_pred_v2 = model_v2.decode(z_pred[:, 0])

    # Convert to numpy
    x_context_np = x_context[0].cpu().numpy()
    x_pred_v1_np = x_pred_v1[0].cpu().numpy()
    x_pred_v2_np = x_pred_v2[0].cpu().numpy()
    x_target_np = x_target[0].cpu().numpy()

    # Create RGB composites
    context_rgb = create_rgb_composite(x_context_np)
    pred_v1_rgb = create_rgb_composite(x_pred_v1_np)
    pred_v2_rgb = create_rgb_composite(x_pred_v2_np)
    target_rgb = create_rgb_composite(x_target_np)

    # Compute metrics
    mse_v1 = np.mean((x_pred_v1_np - x_target_np) ** 2)
    mse_v2 = np.mean((x_pred_v2_np - x_target_np) ** 2)

    # Visualize
    fig = plt.figure(figsize=(20, 10))
    gs = GridSpec(2, 5, figure=fig, hspace=0.3, wspace=0.3)

    # Row 1: Images
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(context_rgb)
    ax1.set_title('Context')
    ax1.axis('off')

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(pred_v1_rgb)
    ax2.set_title(f'Decoder V1\nMSE: {mse_v1:.6f}')
    ax2.axis('off')

    ax3 = fig.add_subplot(gs[0, 2])
    ax3.imshow(pred_v2_rgb)
    ax3.set_title(f'Decoder V2 (Improved)\nMSE: {mse_v2:.6f}')
    ax3.axis('off')

    ax4 = fig.add_subplot(gs[0, 3])
    ax4.imshow(target_rgb)
    ax4.set_title('Target')
    ax4.axis('off')

    # Improvement
    improvement = ((mse_v1 - mse_v2) / mse_v1) * 100
    ax5 = fig.add_subplot(gs[0, 4])
    ax5.text(0.1, 0.7, f"MSE Improvement:", fontsize=14, fontweight='bold')
    ax5.text(0.1, 0.5, f"{improvement:.1f}%", fontsize=20,
             color='green' if improvement > 0 else 'red', fontweight='bold')
    ax5.text(0.1, 0.3, f"V1 MSE: {mse_v1:.6f}", fontsize=10)
    ax5.text(0.1, 0.2, f"V2 MSE: {mse_v2:.6f}", fontsize=10)
    ax5.set_xlim(0, 1)
    ax5.set_ylim(0, 1)
    ax5.axis('off')

    # Row 2: Difference maps
    ax6 = fig.add_subplot(gs[1, 0])
    diff_v1 = np.abs(pred_v1_rgb - target_rgb)
    ax6.imshow(diff_v1, vmin=0, vmax=0.5, cmap='hot')
    ax6.set_title('V1 Error Map')
    ax6.axis('off')

    ax7 = fig.add_subplot(gs[1, 1])
    diff_v2 = np.abs(pred_v2_rgb - target_rgb)
    ax7.imshow(diff_v2, vmin=0, vmax=0.5, cmap='hot')
    ax7.set_title('V2 Error Map')
    ax7.axis('off')

    # Zoom in on a region to see detail
    h, w = context_rgb.shape[:2]
    crop_h, crop_w = h // 4, w // 4
    crop_y, crop_x = h // 2 - crop_h // 2, w // 2 - crop_w // 2

    ax8 = fig.add_subplot(gs[1, 2])
    ax8.imshow(pred_v1_rgb[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w])
    ax8.set_title('V1 Detail (Center Crop)')
    ax8.axis('off')

    ax9 = fig.add_subplot(gs[1, 3])
    ax9.imshow(pred_v2_rgb[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w])
    ax9.set_title('V2 Detail (Center Crop)')
    ax9.axis('off')

    ax10 = fig.add_subplot(gs[1, 4])
    ax10.imshow(target_rgb[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w])
    ax10.set_title('Target Detail (Center Crop)')
    ax10.axis('off')

    plt.suptitle(f'Decoder Comparison - Sample {sample_idx}', fontsize=16, fontweight='bold')
    plt.savefig(output_path / f'comparison_sample_{sample_idx}.png', dpi=150, bbox_inches='tight')
    plt.close()

    return {
        'mse_v1': float(mse_v1),
        'mse_v2': float(mse_v2),
        'improvement_pct': float(improvement)
    }


def main():
    parser = argparse.ArgumentParser(description="Compare decoder architectures")
    parser.add_argument("--checkpoint", required=True, help="Path to encoder checkpoint")
    parser.add_argument("--decoder-v1", required=True, help="Path to V1 decoder checkpoint")
    parser.add_argument("--decoder-v2", required=True, help="Path to V2 decoder checkpoint")
    parser.add_argument("--manifest", required=True, help="Path to validation manifest")
    parser.add_argument("--model-size", default="medium", choices=["tiny", "small", "medium", "large", "xlarge"])
    parser.add_argument("--data-root", required=True, help="Data root directory")
    parser.add_argument("--output", default="comparisons/", help="Output directory")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples to compare")

    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Decoder Architecture Comparison")
    print("="*60)

    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    model_config = model_configs[args.model_size]

    # Create model V1 (with original decoder)
    print("\n1. Loading V1 model...")
    model_v1 = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=True,
        **model_config
    )

    checkpoint = torch.load(args.checkpoint, map_location=device)
    model_v1.load_state_dict(checkpoint['model_state_dict'], strict=False)

    decoder_v1_ckpt = torch.load(args.decoder_v1, map_location=device)
    model_v1.decoder.load_state_dict(decoder_v1_ckpt['decoder_state_dict'])

    model_v1.to(device)
    model_v1.train(False)

    print(f"   ✓ V1 loaded (val loss: {decoder_v1_ckpt.get('val_loss', 'N/A')})")

    # Create model V2 (with improved decoder)
    print("\n2. Loading V2 model...")
    model_v2 = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=True,
        **model_config
    )

    # Replace decoder with V2
    model_v2.decoder = SpatialDecoderV2(latent_dim=model_config['latent_dim'])

    # Load weights
    model_v2.load_state_dict(checkpoint['model_state_dict'], strict=False)

    decoder_v2_ckpt = torch.load(args.decoder_v2, map_location=device)
    model_v2.decoder.load_state_dict(decoder_v2_ckpt['decoder_state_dict'])

    model_v2.to(device)
    model_v2.train(False)

    print(f"   ✓ V2 loaded (val loss: {decoder_v2_ckpt.get('val_loss', 'N/A')})")

    # Load dataset
    print("\n3. Loading dataset...")
    dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=1,
        rollout_horizon=6,
        normalize=True,
        data_root=args.data_root
    )

    print(f"   ✓ Loaded {len(dataset)} samples")

    # Compare samples
    print(f"\n4. Comparing {args.num_samples} samples...")
    results = []

    for idx in range(min(args.num_samples, len(dataset))):
        sample = dataset[idx]
        print(f"\n   Sample {idx+1}/{args.num_samples}: {sample['tile_id']}")

        result = compare_sample(model_v1, model_v2, sample, device, output_path, idx)
        results.append(result)

        print(f"      V1 MSE: {result['mse_v1']:.6f}")
        print(f"      V2 MSE: {result['mse_v2']:.6f}")
        print(f"      Improvement: {result['improvement_pct']:.1f}%")

    # Summary statistics
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)

    avg_mse_v1 = np.mean([r['mse_v1'] for r in results])
    avg_mse_v2 = np.mean([r['mse_v2'] for r in results])
    avg_improvement = np.mean([r['improvement_pct'] for r in results])

    print(f"\nAverage MSE V1: {avg_mse_v1:.6f}")
    print(f"Average MSE V2: {avg_mse_v2:.6f}")
    print(f"Average Improvement: {avg_improvement:.1f}%")

    num_improved = sum([1 for r in results if r['improvement_pct'] > 0])
    print(f"\nSamples improved: {num_improved}/{len(results)}")

    print(f"\n✓ Comparisons saved to: {output_path}")
    print("="*60)


if __name__ == "__main__":
    main()
