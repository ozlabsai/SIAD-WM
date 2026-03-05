#!/usr/bin/env python3
"""Comprehensive artifact diagnosis for SIAD decoder

Analyzes multiple potential causes of visual artifacts:
1. Decoder architecture (checkerboard artifacts from ConvTranspose)
2. Distribution shift (context vs predicted latents)
3. RGB normalization issues
4. Channel-wise reconstruction quality
5. Frequency domain analysis

Usage:
    uv run python scripts/diagnose_artifacts_comprehensive.py \
        --checkpoint checkpoints/checkpoint_best.pth \
        --decoder-checkpoint checkpoints/decoder_best.pth \
        --manifest data/manifest_22tiles_val.jsonl \
        --model-size medium \
        --data-root /path/to/data \
        --output diagnostics/artifacts
"""

import argparse
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import yaml
from tqdm import tqdm

from siad.model import WorldModel
from siad.train.dataset import SIADDataset


def analyze_checkerboard_artifacts(x_pred: np.ndarray, x_target: np.ndarray) -> dict:
    """Detect checkerboard patterns using FFT

    Checkerboard artifacts show up as high-frequency peaks in Fourier domain
    """
    # Work on first RGB channel
    pred_gray = x_pred[0]  # Just use first channel
    target_gray = x_target[0]

    # Compute 2D FFT
    pred_fft = np.fft.fft2(pred_gray)
    target_fft = np.fft.fft2(target_gray)

    # Compute power spectrum
    pred_power = np.abs(pred_fft) ** 2
    target_power = np.abs(target_fft) ** 2

    # Compute ratio of high-frequency to low-frequency power
    h, w = pred_power.shape
    center_h, center_w = h // 2, w // 2

    # Low freq: center 25%
    low_freq_region = pred_power[center_h-h//8:center_h+h//8, center_w-w//8:center_w+w//8]
    pred_low_power = np.mean(low_freq_region)

    # High freq: corners
    high_freq_mask = np.ones_like(pred_power, dtype=bool)
    high_freq_mask[center_h-h//4:center_h+h//4, center_w-w//4:center_w+w//4] = False
    pred_high_power = np.mean(pred_power[high_freq_mask])

    # Same for target
    low_freq_region_target = target_power[center_h-h//8:center_h+h//8, center_w-w//8:center_w+w//8]
    target_low_power = np.mean(low_freq_region_target)
    target_high_power = np.mean(target_power[high_freq_mask])

    # Checkerboard score: excess high-frequency power compared to target
    pred_hf_ratio = pred_high_power / (pred_low_power + 1e-8)
    target_hf_ratio = target_high_power / (target_low_power + 1e-8)

    checkerboard_score = pred_hf_ratio / (target_hf_ratio + 1e-8)

    return {
        'checkerboard_score': float(checkerboard_score),
        'pred_hf_ratio': float(pred_hf_ratio),
        'target_hf_ratio': float(target_hf_ratio),
        'has_checkerboard': checkerboard_score > 1.5  # Threshold
    }


def analyze_distribution_shift(z_context, z_predicted, model):
    """Compare statistics of context vs predicted latent distributions"""

    # Compute statistics
    context_mean = z_context.mean(dim=(0, 1)).cpu().numpy()
    context_std = z_context.std(dim=(0, 1)).cpu().numpy()

    pred_mean = z_predicted.mean(dim=(0, 1, 2)).cpu().numpy()
    pred_std = z_predicted.std(dim=(0, 1, 2)).cpu().numpy()

    # KL-divergence approximation (assuming Gaussian)
    # KL(P||Q) = log(σ_Q/σ_P) + (σ_P^2 + (μ_P - μ_Q)^2) / (2σ_Q^2) - 1/2
    mean_diff = np.mean((context_mean - pred_mean) ** 2)
    std_ratio = np.mean(pred_std / (context_std + 1e-8))

    return {
        'mean_shift': float(mean_diff),
        'std_ratio': float(std_ratio),
        'context_mean_norm': float(np.linalg.norm(context_mean)),
        'pred_mean_norm': float(np.linalg.norm(pred_mean)),
        'has_distribution_shift': mean_diff > 0.1 or abs(std_ratio - 1.0) > 0.3
    }


def analyze_channel_reconstruction(x_pred: np.ndarray, x_target: np.ndarray) -> dict:
    """Analyze per-channel reconstruction quality"""

    # Compute MSE per channel
    channel_mse = []
    for c in range(x_pred.shape[0]):
        mse_c = np.mean((x_pred[c] - x_target[c]) ** 2)
        channel_mse.append(float(mse_c))

    # Compute correlation per channel
    channel_corr = []
    for c in range(x_pred.shape[0]):
        pred_flat = x_pred[c].flatten()
        target_flat = x_target[c].flatten()
        corr = np.corrcoef(pred_flat, target_flat)[0, 1]
        channel_corr.append(float(corr))

    return {
        'channel_mse': channel_mse,
        'channel_corr': channel_corr,
        'worst_channel': int(np.argmax(channel_mse)),
        'best_channel': int(np.argmin(channel_mse))
    }


def analyze_rgb_normalization(bands: np.ndarray) -> dict:
    """Analyze RGB normalization artifacts"""

    # Get RGB channels (assuming BAND_ORDER_V1: B, G, R, NIR, ...)
    rgb = bands[[2, 1, 0]]  # R, G, B

    # Compute percentiles for each channel
    percentiles = {}
    for i, name in enumerate(['R', 'G', 'B']):
        channel = rgb[i]
        p2, p98 = np.percentile(channel, [2, 98])
        percentiles[f'{name}_p2'] = float(p2)
        percentiles[f'{name}_p98'] = float(p98)
        percentiles[f'{name}_range'] = float(p98 - p2)

    # Check for extreme normalization
    max_range = max(percentiles['R_range'], percentiles['G_range'], percentiles['B_range'])
    min_range = min(percentiles['R_range'], percentiles['G_range'], percentiles['B_range'])

    return {
        **percentiles,
        'range_ratio': float(max_range / (min_range + 1e-8)),
        'has_extreme_normalization': max_range / (min_range + 1e-8) > 3.0
    }


def visualize_diagnostics(sample_results: dict, output_path: Path):
    """Create comprehensive diagnostic visualization"""

    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(4, 5, figure=fig, hspace=0.3, wspace=0.3)

    # Row 1: Context, Pred, Target, Diff for RGB
    context_rgb = sample_results['context_rgb']
    pred_rgb = sample_results['pred_rgb']
    target_rgb = sample_results['target_rgb']

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(context_rgb)
    ax1.set_title('Context (RGB)')
    ax1.axis('off')

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(pred_rgb)
    ax2.set_title('Prediction (RGB)')
    ax2.axis('off')

    ax3 = fig.add_subplot(gs[0, 2])
    ax3.imshow(target_rgb)
    ax3.set_title('Target (RGB)')
    ax3.axis('off')

    ax4 = fig.add_subplot(gs[0, 3])
    diff = np.abs(pred_rgb - target_rgb)
    ax4.imshow(diff, vmin=0, vmax=0.5, cmap='hot')
    ax4.set_title(f"Diff (MSE={sample_results['mse']:.4f})")
    ax4.axis('off')

    # Row 2: FFT analysis
    ax5 = fig.add_subplot(gs[1, 0])
    pred_fft = np.fft.fft2(sample_results['pred_bands'][0])
    pred_power = np.log1p(np.abs(np.fft.fftshift(pred_fft)))
    ax5.imshow(pred_power, cmap='viridis')
    ax5.set_title('Pred FFT (Band 0)')
    ax5.axis('off')

    ax6 = fig.add_subplot(gs[1, 1])
    target_fft = np.fft.fft2(sample_results['target_bands'][0])
    target_power = np.log1p(np.abs(np.fft.fftshift(target_fft)))
    ax6.imshow(target_power, cmap='viridis')
    ax6.set_title('Target FFT (Band 0)')
    ax6.axis('off')

    # Checkerboard score
    ax7 = fig.add_subplot(gs[1, 2])
    checkerboard = sample_results['checkerboard_analysis']
    ax7.text(0.1, 0.8, f"Checkerboard Score: {checkerboard['checkerboard_score']:.2f}", fontsize=10)
    ax7.text(0.1, 0.6, f"Pred HF Ratio: {checkerboard['pred_hf_ratio']:.4f}", fontsize=10)
    ax7.text(0.1, 0.4, f"Target HF Ratio: {checkerboard['target_hf_ratio']:.4f}", fontsize=10)
    ax7.text(0.1, 0.2, f"Has Checkerboard: {checkerboard['has_checkerboard']}", fontsize=10,
             color='red' if checkerboard['has_checkerboard'] else 'green')
    ax7.set_xlim(0, 1)
    ax7.set_ylim(0, 1)
    ax7.axis('off')
    ax7.set_title('Checkerboard Analysis')

    # Row 3: Channel-wise analysis
    ax8 = fig.add_subplot(gs[2, :2])
    channel_metrics = sample_results['channel_analysis']
    x_channels = np.arange(8)
    ax8.bar(x_channels - 0.2, channel_metrics['channel_mse'], width=0.4, label='MSE', alpha=0.7)
    ax8.set_xlabel('Channel')
    ax8.set_ylabel('MSE')
    ax8.set_title('Per-Channel MSE')
    ax8.legend()
    ax8.grid(True, alpha=0.3)

    ax9 = fig.add_subplot(gs[2, 2:4])
    ax9.bar(x_channels, channel_metrics['channel_corr'], alpha=0.7, color='green')
    ax9.set_xlabel('Channel')
    ax9.set_ylabel('Correlation')
    ax9.set_title('Per-Channel Correlation')
    ax9.set_ylim([0, 1])
    ax9.grid(True, alpha=0.3)

    # Row 4: Distribution shift
    ax10 = fig.add_subplot(gs[3, :2])
    dist_shift = sample_results['distribution_shift']
    metrics_names = ['Mean Shift', 'Std Ratio', 'Context Mean Norm', 'Pred Mean Norm']
    metrics_values = [
        dist_shift['mean_shift'],
        dist_shift['std_ratio'],
        dist_shift['context_mean_norm'] / 100,  # Scale for visibility
        dist_shift['pred_mean_norm'] / 100
    ]
    ax10.bar(metrics_names, metrics_values, alpha=0.7)
    ax10.set_title('Distribution Shift Metrics')
    ax10.set_ylabel('Value')
    ax10.tick_params(axis='x', rotation=45)
    ax10.grid(True, alpha=0.3)

    # RGB normalization
    ax11 = fig.add_subplot(gs[3, 2:4])
    rgb_norm = sample_results['rgb_normalization']
    rgb_names = ['R_range', 'G_range', 'B_range']
    rgb_values = [rgb_norm[k] for k in rgb_names]
    ax11.bar(rgb_names, rgb_values, alpha=0.7, color=['red', 'green', 'blue'])
    ax11.set_title(f"RGB Normalization (Ratio={rgb_norm['range_ratio']:.2f})")
    ax11.set_ylabel('Range (p98 - p2)')
    ax11.grid(True, alpha=0.3)

    plt.suptitle('SIAD Decoder Artifact Diagnostics', fontsize=16, fontweight='bold')
    plt.savefig(output_path / 'diagnostics_visualization.png', dpi=150, bbox_inches='tight')
    plt.close()


def run_diagnostics(
    checkpoint_path: str,
    decoder_checkpoint_path: str,
    manifest_path: str,
    model_size: str,
    data_root: str,
    output_dir: str,
    num_samples: int = 5
):
    """Run comprehensive diagnostics"""

    device = "cuda" if torch.cuda.is_available() else "cpu"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("SIAD Artifact Diagnostics")
    print("="*60)

    # Load model
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    model_config = model_configs[model_size]

    model = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=True,
        **model_config
    )

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)

    decoder_ckpt = torch.load(decoder_checkpoint_path, map_location=device)
    model.decoder.load_state_dict(decoder_ckpt['decoder_state_dict'])

    model.to(device)
    model.train(False)

    print(f"✓ Model loaded: {model_size}")

    # Load dataset
    dataset = SIADDataset(
        manifest_path=manifest_path,
        context_length=1,
        rollout_horizon=6,
        normalize=True,
        data_root=data_root
    )

    print(f"✓ Dataset loaded: {len(dataset)} samples")
    print(f"\nAnalyzing {num_samples} samples...\n")

    # Run diagnostics on multiple samples
    all_results = []

    for idx in tqdm(range(min(num_samples, len(dataset)))):
        sample = dataset[idx]

        x_context = sample['obs_context'].unsqueeze(0).to(device)
        actions = sample['actions_rollout'].unsqueeze(0).to(device)
        x_target = sample['obs_targets'][0].unsqueeze(0).to(device)  # Just first timestep

        with torch.no_grad():
            # Encode context
            z_context = model.encode(x_context)

            # Single-step prediction
            z_pred = model.rollout(z_context, actions[:, :1], H=1)

            # Decode
            x_pred = model.decode(z_pred[:, 0])

        # Convert to numpy
        x_context_np = x_context[0].cpu().numpy()
        x_pred_np = x_pred[0].cpu().numpy()
        x_target_np = x_target[0].cpu().numpy()

        # Run analyses
        checkerboard = analyze_checkerboard_artifacts(x_pred_np, x_target_np)
        dist_shift = analyze_distribution_shift(z_context, z_pred, model)
        channel_analysis = analyze_channel_reconstruction(x_pred_np, x_target_np)
        rgb_norm_pred = analyze_rgb_normalization(x_pred_np)
        rgb_norm_target = analyze_rgb_normalization(x_target_np)

        # Create RGB composites for visualization
        context_rgb = create_rgb_composite(x_context_np)
        pred_rgb = create_rgb_composite(x_pred_np)
        target_rgb = create_rgb_composite(x_target_np)

        mse = np.mean((x_pred_np - x_target_np) ** 2)

        result = {
            'tile_id': sample['tile_id'],
            'mse': float(mse),
            'checkerboard_analysis': checkerboard,
            'distribution_shift': dist_shift,
            'channel_analysis': channel_analysis,
            'rgb_normalization': rgb_norm_pred,
            'context_rgb': context_rgb,
            'pred_rgb': pred_rgb,
            'target_rgb': target_rgb,
            'pred_bands': x_pred_np,
            'target_bands': x_target_np
        }

        all_results.append(result)

        # Visualize first sample
        if idx == 0:
            visualize_diagnostics(result, output_path)

    # Aggregate statistics
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)

    # Checkerboard statistics
    checkerboard_scores = [r['checkerboard_analysis']['checkerboard_score'] for r in all_results]
    num_checkerboard = sum([r['checkerboard_analysis']['has_checkerboard'] for r in all_results])

    print(f"\n1. CHECKERBOARD ARTIFACTS:")
    print(f"   Avg Score: {np.mean(checkerboard_scores):.2f}")
    print(f"   Samples with checkerboard: {num_checkerboard}/{len(all_results)}")
    print(f"   Diagnosis: {'⚠️  LIKELY CAUSE' if num_checkerboard > len(all_results)//2 else '✓ OK'}")

    # Distribution shift statistics
    mean_shifts = [r['distribution_shift']['mean_shift'] for r in all_results]
    std_ratios = [r['distribution_shift']['std_ratio'] for r in all_results]
    num_shifts = sum([r['distribution_shift']['has_distribution_shift'] for r in all_results])

    print(f"\n2. DISTRIBUTION SHIFT:")
    print(f"   Avg Mean Shift: {np.mean(mean_shifts):.4f}")
    print(f"   Avg Std Ratio: {np.mean(std_ratios):.4f}")
    print(f"   Samples with shift: {num_shifts}/{len(all_results)}")
    print(f"   Diagnosis: {'⚠️  LIKELY CAUSE' if num_shifts > len(all_results)//2 else '✓ OK'}")

    # Channel analysis
    all_channel_mse = np.array([r['channel_analysis']['channel_mse'] for r in all_results])
    avg_channel_mse = np.mean(all_channel_mse, axis=0)

    print(f"\n3. CHANNEL RECONSTRUCTION:")
    print(f"   Best channel: {np.argmin(avg_channel_mse)} (MSE={np.min(avg_channel_mse):.6f})")
    print(f"   Worst channel: {np.argmax(avg_channel_mse)} (MSE={np.max(avg_channel_mse):.6f})")
    print(f"   Channel MSE range: {np.max(avg_channel_mse) / np.min(avg_channel_mse):.2f}x")

    # RGB normalization
    range_ratios = [r['rgb_normalization']['range_ratio'] for r in all_results]
    num_extreme = sum([r['rgb_normalization']['has_extreme_normalization'] for r in all_results])

    print(f"\n4. RGB NORMALIZATION:")
    print(f"   Avg Range Ratio: {np.mean(range_ratios):.2f}")
    print(f"   Samples with extreme normalization: {num_extreme}/{len(all_results)}")
    print(f"   Diagnosis: {'⚠️  LIKELY CAUSE' if num_extreme > len(all_results)//2 else '✓ OK'}")

    print(f"\n{'='*60}")
    print("RECOMMENDATIONS:")
    print("="*60)

    if num_checkerboard > len(all_results) // 2:
        print("\n⚠️  Fix checkerboard artifacts:")
        print("   - Replace ConvTranspose2d with Upsample + Conv2d")
        print("   - Or use kernel_size=3, stride=1 after upsampling")
        print("   - Add residual connections in decoder")

    if num_shifts > len(all_results) // 2:
        print("\n⚠️  Fix distribution shift:")
        print("   - Retrain decoder on PREDICTED latents (not just context)")
        print("   - Use train_decoder_on_predictions.py")
        print("   - Add latent normalization layer before decoder")

    if num_extreme > len(all_results) // 2:
        print("\n⚠️  Fix RGB normalization:")
        print("   - Use global normalization statistics (dataset-wide)")
        print("   - Or normalize each channel consistently")
        print("   - Consider linear stretch instead of percentile")

    if np.max(avg_channel_mse) / np.min(avg_channel_mse) > 3.0:
        print(f"\n⚠️  Channel {np.argmax(avg_channel_mse)} is poorly reconstructed:")
        print("   - Check if this channel is used during training")
        print("   - Consider per-channel loss weighting")

    print(f"\n✓ Diagnostics saved to: {output_path}")
    print("="*60)


def create_rgb_composite(bands: np.ndarray) -> np.ndarray:
    """Create RGB from 8-band satellite image"""
    rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]

    for i in range(3):
        channel = rgb[:, :, i]
        vmin, vmax = np.percentile(channel, [2, 98])
        rgb[:, :, i] = np.clip((channel - vmin) / (vmax - vmin + 1e-8), 0, 1)

    return rgb


def main():
    parser = argparse.ArgumentParser(description="Comprehensive artifact diagnostics")
    parser.add_argument("--checkpoint", required=True, help="Path to encoder checkpoint")
    parser.add_argument("--decoder-checkpoint", required=True, help="Path to decoder checkpoint")
    parser.add_argument("--manifest", required=True, help="Path to validation manifest")
    parser.add_argument("--model-size", default="medium", choices=["tiny", "small", "medium", "large", "xlarge"])
    parser.add_argument("--data-root", required=True, help="Data root directory")
    parser.add_argument("--output", default="diagnostics/artifacts", help="Output directory")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples to analyze")

    args = parser.parse_args()

    run_diagnostics(
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
