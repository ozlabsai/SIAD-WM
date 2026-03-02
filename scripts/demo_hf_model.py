#!/usr/bin/env python3
"""Demo SIAD model from HuggingFace Hub using AutoModel

Usage:
    # From HuggingFace Hub:
    python scripts/demo_hf_model.py \
        --repo-id username/siad-tiny \
        --sample data/manifest.jsonl
    
    # From local directory:
    python scripts/demo_hf_model.py \
        --local-path ./saved_model \
        --sample data/manifest.jsonl
"""

import argparse
import numpy as np
import torch
from pathlib import Path
from transformers import AutoModel, AutoConfig

from siad.train.dataset import SIADDataset


def load_model_from_hub(repo_id: str, device: str = "cuda"):
    """Load SIAD model from HuggingFace Hub
    
    Args:
        repo_id: HF repo ID (e.g., "username/siad-tiny")
        device: Device to load on
        
    Returns:
        model: Loaded SIADWorldModel
        config: Model configuration
    """
    print(f"Loading from HuggingFace Hub: {repo_id}")
    
    # Load config
    config = AutoConfig.from_pretrained(repo_id, trust_remote_code=True)
    print(f"  Model type: {config.model_type}")
    print(f"  Latent dim: {config.latent_dim}")
    
    # Load model
    model = AutoModel.from_pretrained(
        repo_id,
        config=config,
        trust_remote_code=True
    )
    
    model.to(device)
    model.inference_mode()
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {total_params:,} ({total_params / 1e6:.1f}M)")
    print(f"  ✓ Model loaded successfully")
    
    return model, config


def load_model_from_local(local_path: str, device: str = "cuda"):
    """Load SIAD model from local directory
    
    Args:
        local_path: Path to saved model directory
        device: Device to load on
        
    Returns:
        model: Loaded SIADWorldModel
        config: Model configuration
    """
    print(f"Loading from local path: {local_path}")
    
    config = AutoConfig.from_pretrained(local_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        local_path,
        config=config,
        trust_remote_code=True
    )
    
    model.to(device)
    model.inference_mode()
    
    print(f"  ✓ Model loaded successfully")
    
    return model, config


def run_inference(model, sample_data: dict, device: str = "cuda"):
    """Run inference on a sample
    
    Args:
        model: SIADWorldModel instance
        sample_data: Dict with obs_context, actions_rollout, obs_targets
        device: Device to run on
        
    Returns:
        predictions: Model predictions
        targets: Ground truth
        metrics: Evaluation metrics
    """
    print("\nRunning inference...")
    
    # Prepare inputs
    obs_context = sample_data['obs_context'].unsqueeze(0).to(device)
    actions = sample_data['actions_rollout'].unsqueeze(0).to(device)
    obs_targets = sample_data['obs_targets'].unsqueeze(0).to(device)
    
    print(f"  Context: {obs_context.shape}")
    print(f"  Actions: {actions.shape}")
    print(f"  Targets: {obs_targets.shape}")
    
    with torch.no_grad():
        # Use full forward pass with return_dict
        outputs = model(
            obs_context=obs_context,
            actions_rollout=actions,
            obs_targets=obs_targets,
            return_dict=True
        )
        
        print(f"  Predictions: {outputs.predictions.shape}")
        print(f"  Loss: {outputs.loss.item():.4f}")
        
        if outputs.metrics:
            print(f"  Metrics:")
            for key, val in outputs.metrics.items():
                print(f"    {key}: {val:.4f}")
    
    return outputs.predictions.cpu(), obs_targets.cpu(), outputs.metrics


def main():
    parser = argparse.ArgumentParser(description="Demo SIAD model from HuggingFace")
    
    # Model source
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo-id", help="HF repo ID (username/model-name)")
    source.add_argument("--local-path", help="Local model directory")
    
    # Data
    parser.add_argument("--sample", required=True, help="Path to manifest.jsonl")
    parser.add_argument("--sample-idx", type=int, default=0, help="Sample index")
    
    # Device
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    
    # Output
    parser.add_argument("--output-dir", default="demo_outputs", help="Output directory")
    
    args = parser.parse_args()
    
    print("="*60)
    print("SIAD Model Demo (HuggingFace Format)")
    print("="*60)
    
    # Load model
    if args.repo_id:
        model, config = load_model_from_hub(args.repo_id, device=args.device)
    else:
        model, config = load_model_from_local(args.local_path, device=args.device)
    
    # Load sample
    print(f"\nLoading sample from: {args.sample}")
    dataset = SIADDataset(
        manifest_path=args.sample,
        context_length=1,
        rollout_horizon=6,
        normalize=True
    )
    
    sample = dataset[args.sample_idx]
    print(f"  Tile: {sample['tile_id']}")
    print(f"  Context: {sample['months_context']}")
    print(f"  Rollout: {sample['months_rollout']}")
    
    # Run inference
    predictions, targets, metrics = run_inference(model, sample, device=args.device)
    
    # Save outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"demo_hf_{sample['tile_id']}.npz"
    np.savez(
        output_file,
        predictions=predictions.numpy(),
        targets=targets.numpy(),
        context=sample['obs_context'].numpy(),
        actions=sample['actions_rollout'].numpy(),
        metrics=metrics
    )
    
    print(f"\n✓ Saved to: {output_file}")
    print(f"\nVisualize with:")
    print(f"  python scripts/visualize_predictions.py {output_file}")
    print("="*60)


if __name__ == "__main__":
    main()
