#!/usr/bin/env python3
"""Evaluate SIAD model quality on validation set

Computes metrics and generates prediction visualizations to assess model quality.

Usage:
    uv run python scripts/evaluate_model.py \
        --checkpoint checkpoints/checkpoint_best.pth \
        --manifest data/manifest.jsonl \
        --num-samples 5
"""

import argparse
import torch
import numpy as np
import matplotlib.pyplot as plt
import yaml
from pathlib import Path
from tqdm import tqdm

from siad.model import WorldModel
from siad.train.dataset import SIADDataset
from siad.train.losses import compute_jepa_world_model_loss


def load_model_from_checkpoint(checkpoint_path: str, device: str = "cuda"):
    """Load model from checkpoint, inferring architecture from weights or config"""
    checkpoint = torch.load(checkpoint_path, map_location=device)
    state_dict = checkpoint['model_state_dict']

    # Try to get config from checkpoint first
    config = checkpoint.get('config', {})

    # If config has model parameters, use those
    if 'latent_dim' in config:
        latent_dim = config['latent_dim']
        print(f"Using latent_dim={latent_dim} from checkpoint config")
    else:
        # Infer latent_dim from encoder positional embeddings shape
        # encoder.pos_embed has shape [1, 256, latent_dim]
        if 'encoder.pos_embed' not in state_dict:
            raise ValueError(
                "Cannot infer model size: checkpoint has no 'config' with latent_dim "
                "and no 'encoder.pos_embed' in state_dict. "
                "This may be an old checkpoint format."
            )
        latent_dim = state_dict['encoder.pos_embed'].shape[-1]
        print(f"Inferred latent_dim={latent_dim} from encoder.pos_embed shape")

    # Load model size configurations
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    # Map latent_dim to model size
    size_map = {512: 'tiny', 768: 'small', 1024: 'medium', 1536: 'large', 2048: 'xlarge'}
    model_size = size_map.get(latent_dim)

    if not model_size or model_size not in model_configs:
        raise ValueError(
            f"Cannot infer model size from latent_dim={latent_dim}. "
            f"Expected one of {list(size_map.keys())}"
        )

    print(f"Detected model size: {model_size} (latent_dim={latent_dim})")

    # Create model with detected configuration
    model_config = model_configs[model_size]
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        **model_config
    )

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    return model, checkpoint


def evaluate_on_dataset(model, dataset, device: str = "cuda", num_samples: int = None):
    """Evaluate model on dataset samples"""
    
    if num_samples is None:
        num_samples = len(dataset)
    else:
        num_samples = min(num_samples, len(dataset))
    
    metrics_list = []
    
    print(f"\nEvaluating on {num_samples} samples...")
    
    for idx in tqdm(range(num_samples)):
        sample = dataset[idx]
        
        # Prepare batch
        obs_context = sample['obs_context'].unsqueeze(0).to(device)
        actions = sample['actions_rollout'].unsqueeze(0).to(device)
        obs_targets = sample['obs_targets'].unsqueeze(0).to(device)
        
        with torch.no_grad():
            # Forward pass
            z0 = model.encode(obs_context)
            z_pred = model.rollout(z0, actions, H=6)
            
            # Encode targets
            B, H, C, Hp, Wp = obs_targets.shape
            x_targets_flat = obs_targets.view(B * H, C, Hp, Wp)
            z_target_flat = model.encode_targets(x_targets_flat)
            z_target = z_target_flat.view(B, H, 256, model.latent_dim)
            
            # Compute loss
            loss, metrics = compute_jepa_world_model_loss(z_pred, z_target)
            
            metrics_list.append({
                'tile_id': sample['tile_id'],
                'loss': loss.item(),
                **{k: v.item() if torch.is_tensor(v) else v for k, v in metrics.items()}
            })
    
    return metrics_list


def print_evaluation_summary(metrics_list, checkpoint_info):
    """Print evaluation summary"""
    
    print("\n" + "="*60)
    print("Model Evaluation Summary")
    print("="*60)
    
    # Checkpoint info
    print(f"\nCheckpoint Info:")
    print(f"  Epoch: {checkpoint_info.get('epoch', 'N/A')}")
    print(f"  Best Val Loss: {checkpoint_info.get('best_val_loss', 'N/A'):.4f}")
    
    # Aggregate metrics
    avg_loss = np.mean([m['loss'] for m in metrics_list])
    std_loss = np.std([m['loss'] for m in metrics_list])
    min_loss = np.min([m['loss'] for m in metrics_list])
    max_loss = np.max([m['loss'] for m in metrics_list])
    
    print(f"\nEvaluation Metrics ({len(metrics_list)} samples):")
    print(f"  Average Loss: {avg_loss:.4f} ± {std_loss:.4f}")
    print(f"  Min Loss: {min_loss:.4f}")
    print(f"  Max Loss: {max_loss:.4f}")
    
    # Check for other metrics
    if metrics_list and 'cosine_sim' in metrics_list[0]:
        avg_cos = np.mean([m['cosine_sim'] for m in metrics_list])
        print(f"  Avg Cosine Similarity: {avg_cos:.4f}")
    
    # Quality assessment
    print(f"\n{'='*60}")
    print("Quality Assessment:")
    print("="*60)
    
    if avg_loss < 0.05:
        print("  ✅ EXCELLENT - Loss < 0.05")
    elif avg_loss < 0.10:
        print("  ✅ GOOD - Loss < 0.10")
    elif avg_loss < 0.20:
        print("  ⚠️  FAIR - Loss 0.10-0.20")
    else:
        print("  ❌ POOR - Loss > 0.20")
    
    if std_loss < 0.02:
        print("  ✅ CONSISTENT - Low variance across samples")
    elif std_loss < 0.05:
        print("  ⚠️  MODERATE - Some variance across samples")
    else:
        print("  ❌ INCONSISTENT - High variance across samples")
    
    print("="*60)
    
    # Per-tile breakdown
    print(f"\nPer-Tile Performance:")
    print(f"{'Tile ID':<20} {'Loss':<10}")
    print("-" * 30)
    for m in sorted(metrics_list, key=lambda x: x['loss'])[:10]:
        print(f"{m['tile_id']:<20} {m['loss']:<10.4f}")
    
    if len(metrics_list) > 10:
        print(f"... and {len(metrics_list) - 10} more tiles")


def main():
    parser = argparse.ArgumentParser(description="Evaluate SIAD model quality")
    parser.add_argument("--checkpoint", required=True, help="Path to checkpoint")
    parser.add_argument("--manifest", required=True, help="Path to manifest.jsonl")
    parser.add_argument("--num-samples", type=int, default=None, 
                       help="Number of samples to evaluate (default: all)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--data-root", type=str, default=None,
                       help="Root directory for data files (if paths in manifest are relative)")
    
    args = parser.parse_args()
    
    print("="*60)
    print("SIAD Model Evaluation")
    print("="*60)
    
    # Load model
    print(f"\nLoading model from: {args.checkpoint}")
    model, checkpoint = load_model_from_checkpoint(args.checkpoint, device=args.device)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {total_params:,} ({total_params / 1e6:.1f}M)")
    
    # Load dataset
    print(f"\nLoading dataset: {args.manifest}")
    dataset = SIADDataset(
        manifest_path=args.manifest,
        context_length=1,
        rollout_horizon=6,
        normalize=True,
        data_root=args.data_root
    )
    print(f"  Total samples: {len(dataset)}")
    
    # Evaluate
    metrics = evaluate_on_dataset(
        model, dataset, 
        device=args.device,
        num_samples=args.num_samples
    )
    
    # Print summary
    print_evaluation_summary(metrics, checkpoint)


if __name__ == "__main__":
    main()
