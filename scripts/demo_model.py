#!/usr/bin/env python3
"""Demo script to test SIAD models from Hugging Face or local checkpoints

Usage:
    # From Hugging Face:
    python scripts/demo_model.py --repo-id username/siad-tiny --sample data/manifest.jsonl
    
    # From local checkpoint:
    python scripts/demo_model.py --checkpoint checkpoints/checkpoint_final.pth --model-size tiny --sample data/manifest.jsonl
"""

import argparse
import json
import yaml
import torch
import numpy as np
from pathlib import Path
from huggingface_hub import hf_hub_download

from siad.model import WorldModel
from siad.train.dataset import SIADDataset


def load_model_from_hf(repo_id: str, device: str = "cuda"):
    """Load model from Hugging Face Hub
    
    Args:
        repo_id: HF repo ID (e.g., "username/siad-tiny")
        device: Device to load model on
        
    Returns:
        model: Loaded WorldModel
        config: Model configuration dict
    """
    print(f"Downloading from Hugging Face: {repo_id}")
    
    # Download config
    config_path = hf_hub_download(repo_id=repo_id, filename="config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    # Download model weights
    model_path = hf_hub_download(repo_id=repo_id, filename="model.pth")
    
    print(f"  Config: {config['model_size']}")
    print(f"  Architecture: {config['architecture']}")
    
    # Create model
    model = WorldModel(
        in_channels=config['input_channels'],
        action_dim=config['action_dim'],
        **config['architecture']
    )
    
    # Load weights
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.inference_mode()
    
    print(f"  ✓ Model loaded successfully")
    
    return model, config


def load_model_from_checkpoint(checkpoint_path: str, model_size: str, device: str = "cuda"):
    """Load model from local checkpoint
    
    Args:
        checkpoint_path: Path to .pth file
        model_size: Model size (tiny/small/medium/large/xlarge)
        device: Device to load model on
        
    Returns:
        model: Loaded WorldModel
        config: Model configuration dict
    """
    print(f"Loading from local checkpoint: {checkpoint_path}")
    
    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)
    
    if model_size not in model_configs:
        raise ValueError(f"Invalid model size: {model_size}")
    
    model_config = model_configs[model_size]
    
    # Create model
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        **model_config
    )
    
    # Load weights
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.inference_mode()
    
    print(f"  ✓ Model loaded successfully")
    
    config = {
        'model_size': model_size,
        'architecture': model_config,
        'input_channels': 8,
        'action_dim': 2
    }
    
    return model, config


def run_demo_inference(model, sample_data: dict, device: str = "cuda"):
    """Run demo inference on a sample
    
    Args:
        model: WorldModel instance
        sample_data: Dict with keys: obs_context, actions_rollout, obs_targets
        device: Device to run on
        
    Returns:
        predictions: Model predictions
        targets: Ground truth targets
        metrics: Evaluation metrics
    """
    print("\nRunning inference...")
    
    # Prepare inputs
    x_context = sample_data['obs_context'].unsqueeze(0).to(device)  # [1, C, H, W]
    actions = sample_data['actions_rollout'].unsqueeze(0).to(device)  # [1, H, 2]
    x_targets = sample_data['obs_targets'].to(device)  # [H, C, H, W]
    
    print(f"  Input shape: {x_context.shape}")
    print(f"  Actions shape: {actions.shape}")
    print(f"  Target shape: {x_targets.shape}")
    
    with torch.no_grad():
        # Encode context
        z0 = model.encode(x_context)  # [1, N=256, D]
        print(f"  Encoded shape: {z0.shape}")
        
        # Rollout predictions
        z_pred = model.rollout(z0, actions, H=actions.shape[1])  # [1, H, N, D]
        print(f"  Rollout shape: {z_pred.shape}")
        
        # Decode predictions
        x_pred = model.decode(z_pred)  # [1, H, C, H, W]
        print(f"  Decoded shape: {x_pred.shape}")
        
        # Encode targets for comparison
        B, H, C, Hp, Wp = 1, x_targets.shape[0], *x_targets.shape[1:]
        x_targets_batch = x_targets.unsqueeze(0)  # [1, H, C, H, W]
        x_targets_flat = x_targets_batch.view(B * H, C, Hp, Wp)
        z_target_flat = model.encode_targets(x_targets_flat)
        z_target = z_target_flat.view(B, H, 256, -1)
        
        # Compute metrics
        # MSE in pixel space
        mse_pixel = torch.nn.functional.mse_loss(x_pred, x_targets_batch)
        
        # Cosine similarity in latent space
        z_pred_norm = torch.nn.functional.normalize(z_pred, dim=-1)
        z_target_norm = torch.nn.functional.normalize(z_target, dim=-1)
        cos_sim = (z_pred_norm * z_target_norm).sum(dim=-1).mean()
        
        metrics = {
            'mse_pixel': mse_pixel.item(),
            'cosine_similarity': cos_sim.item()
        }
    
    print(f"\n  Metrics:")
    print(f"    MSE (pixel space): {metrics['mse_pixel']:.4f}")
    print(f"    Cosine similarity (latent): {metrics['cosine_similarity']:.4f}")
    
    return x_pred.cpu(), x_targets_batch.cpu(), metrics


def main():
    parser = argparse.ArgumentParser(description="Demo SIAD model inference")
    
    # Model source (HF or local)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-id", type=str, help="HuggingFace repo ID (e.g., username/siad-tiny)")
    source_group.add_argument("--checkpoint", type=str, help="Local checkpoint path")
    
    # Required for local checkpoint
    parser.add_argument("--model-size", type=str, 
                       choices=["tiny", "small", "medium", "large", "xlarge"],
                       help="Model size (required if using --checkpoint)")
    
    # Data
    parser.add_argument("--sample", type=str, required=True,
                       help="Path to manifest.jsonl or specific GeoTIFF")
    parser.add_argument("--sample-idx", type=int, default=0,
                       help="Sample index from manifest (default: 0)")
    
    # Device
    parser.add_argument("--device", type=str, 
                       default="cuda" if torch.cuda.is_available() else "cpu",
                       help="Device to use")
    
    # Output
    parser.add_argument("--output-dir", type=str, default="demo_outputs",
                       help="Directory to save visualizations")
    
    args = parser.parse_args()
    
    # Validate
    if args.checkpoint and not args.model_size:
        parser.error("--model-size is required when using --checkpoint")
    
    print("="*60)
    print("SIAD Model Demo")
    print("="*60)
    
    # Load model
    if args.repo_id:
        model, config = load_model_from_hf(args.repo_id, device=args.device)
    else:
        model, config = load_model_from_checkpoint(
            args.checkpoint, args.model_size, device=args.device
        )
    
    # Load sample data
    print(f"\nLoading sample from: {args.sample}")
    dataset = SIADDataset(
        manifest_path=args.sample,
        context_length=1,
        rollout_horizon=6,
        normalize=True
    )
    
    sample = dataset[args.sample_idx]
    print(f"  Sample: {sample['tile_id']}")
    print(f"  Context months: {sample['months_context']}")
    print(f"  Rollout months: {sample['months_rollout']}")
    
    # Run inference
    predictions, targets, metrics = run_demo_inference(model, sample, device=args.device)
    
    # Save outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"demo_{sample['tile_id']}.npz"
    np.savez(
        output_file,
        predictions=predictions.numpy(),
        targets=targets.numpy(),
        context=sample['obs_context'].numpy(),
        actions=sample['actions_rollout'].numpy(),
        metrics=metrics
    )
    
    print(f"\n✓ Saved outputs to: {output_file}")
    print(f"\nTo visualize, run:")
    print(f"  python scripts/visualize_predictions.py {output_file}")
    print("="*60)


if __name__ == "__main__":
    main()
