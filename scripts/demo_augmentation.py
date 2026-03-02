#!/usr/bin/env python3
"""Demo script to visualize data augmentation effects

Shows side-by-side comparison of:
- Original sample
- Augmented sample (same data with random transforms)
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from siad.train.dataset import SIADDataset


def visualize_augmentation(manifest_path: str, data_root: str = None, sample_idx: int = 0):
    """Visualize original vs augmented samples"""

    print("Creating datasets...")
    # Dataset without augmentation
    dataset_no_aug = SIADDataset(
        manifest_path=manifest_path,
        context_length=1,
        rollout_horizon=6,
        data_root=data_root,
        normalize=True,
        augment=False
    )

    # Dataset with augmentation
    dataset_aug = SIADDataset(
        manifest_path=manifest_path,
        context_length=1,
        rollout_horizon=6,
        data_root=data_root,
        normalize=True,
        augment=True
    )

    print(f"\nLoading sample {sample_idx}...")
    # Get same sample from both datasets
    sample_orig = dataset_no_aug[sample_idx]
    sample_aug1 = dataset_aug[sample_idx]
    sample_aug2 = dataset_aug[sample_idx]  # Different augmentation

    # Extract context frames [8, 256, 256]
    context_orig = sample_orig["obs_context"].numpy()
    context_aug1 = sample_aug1["obs_context"].numpy()
    context_aug2 = sample_aug2["obs_context"].numpy()

    # Create RGB composite (using bands 2, 1, 0 -> R, G, B)
    # Channels: [B2, B3, B4, B8, VV, VH, lights, valid]
    # Use B4 (red), B3 (green), B2 (blue) for natural color
    def make_rgb(img):
        rgb = np.stack([img[2], img[1], img[0]], axis=-1)  # [H, W, 3]
        # Enhance contrast
        rgb = np.clip(rgb * 1.5, 0, 1)
        return rgb

    rgb_orig = make_rgb(context_orig)
    rgb_aug1 = make_rgb(context_aug1)
    rgb_aug2 = make_rgb(context_aug2)

    # Plot comparison
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(rgb_orig)
    axes[0].set_title("Original", fontsize=14, fontweight='bold')
    axes[0].axis('off')

    axes[1].imshow(rgb_aug1)
    axes[1].set_title("Augmented #1", fontsize=14, fontweight='bold')
    axes[1].axis('off')

    axes[2].imshow(rgb_aug2)
    axes[2].set_title("Augmented #2", fontsize=14, fontweight='bold')
    axes[2].axis('off')

    plt.suptitle(
        f"Data Augmentation Comparison - Tile: {sample_orig['tile_id']}\n"
        f"Transforms: Random flips, rotations (±10°), brightness jitter (±10%)",
        fontsize=12
    )
    plt.tight_layout()

    # Save figure
    output_path = Path(__file__).parent.parent / "augmentation_demo.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved visualization to: {output_path}")

    # Show statistics
    print("\nAugmentation Statistics:")
    print(f"  Original range: [{context_orig.min():.3f}, {context_orig.max():.3f}]")
    print(f"  Augmented #1 range: [{context_aug1.min():.3f}, {context_aug1.max():.3f}]")
    print(f"  Augmented #2 range: [{context_aug2.min():.3f}, {context_aug2.max():.3f}]")

    print("\nAugmentation Effects:")
    print(f"  Mean difference (orig vs aug1): {np.abs(context_orig - context_aug1).mean():.4f}")
    print(f"  Mean difference (orig vs aug2): {np.abs(context_orig - context_aug2).mean():.4f}")
    print(f"  Mean difference (aug1 vs aug2): {np.abs(context_aug1 - context_aug2).mean():.4f}")

    # Show first target frame difference
    target_orig = sample_orig["obs_targets"][0].numpy()
    target_aug1 = sample_aug1["obs_targets"][0].numpy()

    print(f"\nTarget frame consistency (first rollout step):")
    print(f"  Mean difference: {np.abs(target_orig - target_aug1).mean():.4f}")

    plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Visualize data augmentation")
    parser.add_argument("--manifest", type=str, required=True, help="Path to manifest.jsonl")
    parser.add_argument("--data-root", type=str, default=None, help="Data root directory")
    parser.add_argument("--sample-idx", type=int, default=0, help="Sample index to visualize")
    args = parser.parse_args()

    visualize_augmentation(args.manifest, args.data_root, args.sample_idx)
