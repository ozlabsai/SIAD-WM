#!/usr/bin/env python3
"""Visualize SIAD model predictions vs ground truth

Creates side-by-side comparisons of predicted and actual satellite imagery
across the 6-month rollout horizon.

Usage:
    python scripts/visualize_predictions.py demo_outputs/demo_tile_x001_y001.npz
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def create_rgb_composite(bands: np.ndarray, indices=(2, 1, 0)) -> np.ndarray:
    """Create RGB composite from multi-band satellite image
    
    Args:
        bands: [C, H, W] array with C channels
        indices: Which channels to use for RGB (default: B4, B3, B2 = natural color)
        
    Returns:
        rgb: [H, W, 3] RGB image normalized to [0, 1]
    """
    rgb = bands[list(indices)].transpose(1, 2, 0)  # [H, W, 3]
    
    # Normalize each channel to [0, 1]
    for i in range(3):
        channel = rgb[:, :, i]
        vmin, vmax = np.percentile(channel, [2, 98])  # Clip outliers
        rgb[:, :, i] = np.clip((channel - vmin) / (vmax - vmin + 1e-8), 0, 1)
    
    return rgb


def visualize_rollout(
    predictions: np.ndarray,
    targets: np.ndarray,
    context: np.ndarray,
    actions: np.ndarray,
    output_path: Path
):
    """Create visualization comparing predictions vs targets
    
    Args:
        predictions: [1, H, C, H, W] predicted images
        targets: [1, H, C, H, W] ground truth images
        context: [C, H, W] context image
        actions: [1, H, 2] action vectors
        output_path: Where to save visualization
    """
    # Squeeze batch dimension
    predictions = predictions[0]  # [H, C, H, W]
    targets = targets[0]
    actions = actions[0]  # [H, 2]
    
    H = predictions.shape[0]  # Rollout horizon
    
    # Create figure: context + H months × 2 rows (pred + target)
    fig, axes = plt.subplots(3, H + 1, figsize=(4 * (H + 1), 12))
    
    # Row 0: Context image
    context_rgb = create_rgb_composite(context)
    axes[0, 0].imshow(context_rgb)
    axes[0, 0].set_title("Context\n(Month 0)", fontsize=12, fontweight='bold')
    axes[0, 0].axis('off')
    
    # Hide remaining cells in first row
    for col in range(1, H + 1):
        axes[0, col].axis('off')
    
    # Rows 1-2: Predictions and targets
    for t in range(H):
        pred_rgb = create_rgb_composite(predictions[t])
        target_rgb = create_rgb_composite(targets[t])
        
        # Row 1: Predictions
        axes[1, t + 1].imshow(pred_rgb)
        action_str = f"R:{actions[t, 0]:.2f}\nT:{actions[t, 1]:.2f}"
        axes[1, t + 1].set_title(f"Predicted\nMonth {t+1}\n{action_str}", 
                                  fontsize=10)
        axes[1, t + 1].axis('off')
        
        # Row 2: Ground truth
        axes[2, t + 1].imshow(target_rgb)
        axes[2, t + 1].set_title(f"Ground Truth\nMonth {t+1}", fontsize=10)
        axes[2, t + 1].axis('off')
    
    # Hide first column in rows 1-2
    axes[1, 0].axis('off')
    axes[2, 0].axis('off')
    
    # Add row labels
    fig.text(0.02, 0.75, 'Input', ha='center', va='center', 
             rotation=90, fontsize=14, fontweight='bold')
    fig.text(0.02, 0.50, 'Predicted', ha='center', va='center',
             rotation=90, fontsize=14, fontweight='bold')
    fig.text(0.02, 0.25, 'Actual', ha='center', va='center',
             rotation=90, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved visualization to: {output_path}")
    
    return fig


def plot_metrics_over_time(predictions: np.ndarray, targets: np.ndarray, output_path: Path):
    """Plot per-timestep metrics
    
    Args:
        predictions: [1, H, C, H, W]
        targets: [1, H, C, H, W]
        output_path: Where to save plot
    """
    predictions = predictions[0]
    targets = targets[0]
    H = predictions.shape[0]
    
    # Compute MSE per timestep
    mse_per_step = []
    for t in range(H):
        mse = np.mean((predictions[t] - targets[t]) ** 2)
        mse_per_step.append(mse)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(1, H + 1), mse_per_step, marker='o', linewidth=2, markersize=8)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Mean Squared Error', fontsize=12)
    ax.set_title('Prediction Error Over Rollout Horizon', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(range(1, H + 1))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved metrics plot to: {output_path}")
    
    return fig


def main():
    parser = argparse.ArgumentParser(description="Visualize SIAD predictions")
    parser.add_argument("input", type=str, help="Path to .npz file from demo_model.py")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Output directory (default: same as input)")
    parser.add_argument("--show", action="store_true", help="Show plots interactively")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_path.parent
    output_dir.mkdir(exist_ok=True)
    
    # Load data
    print(f"Loading: {input_path}")
    data = np.load(input_path)
    
    predictions = data['predictions']
    targets = data['targets']
    context = data['context']
    actions = data['actions']
    
    print(f"  Predictions: {predictions.shape}")
    print(f"  Targets: {targets.shape}")
    print(f"  Context: {context.shape}")
    print(f"  Actions: {actions.shape}")
    
    # Print metrics if available
    if 'metrics' in data.files:
        metrics = data['metrics'].item()
        print(f"\nMetrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f}")
    
    # Create visualizations
    print("\nCreating visualizations...")
    
    # 1. Rollout comparison
    stem = input_path.stem
    rollout_path = output_dir / f"{stem}_rollout.png"
    visualize_rollout(predictions, targets, context, actions, rollout_path)
    
    # 2. Metrics over time
    metrics_path = output_dir / f"{stem}_metrics.png"
    plot_metrics_over_time(predictions, targets, metrics_path)
    
    print(f"\n{'='*60}")
    print(f"✓ Visualization complete!")
    print(f"{'='*60}")
    
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
