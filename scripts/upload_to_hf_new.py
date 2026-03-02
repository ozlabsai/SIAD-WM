#!/usr/bin/env python3
"""Upload SIAD model to HuggingFace Hub using proper HF format

This creates a proper HuggingFace model repository with:
- Transformers-compatible model architecture
- save_pretrained() / from_pretrained() support
- Proper model cards and metadata
- Compatible with HF AutoModel

Usage:
    uv run python scripts/upload_to_hf_new.py \
        --checkpoint checkpoints/checkpoint_final.pth \
        --model-size tiny \
        --repo-id username/siad-tiny
"""

import argparse
import yaml
from pathlib import Path
import torch

from siad.model import SIADWorldModel, SIADConfig


def upload_to_hub(
    checkpoint_path: str,
    model_size: str,
    repo_id: str,
    private: bool = False,
    commit_message: str = None
):
    """Upload model to HuggingFace Hub using proper HF format
    
    Args:
        checkpoint_path: Path to training checkpoint (.pth)
        model_size: Model size (tiny/small/medium/large/xlarge)
        repo_id: HF repo ID (username/model-name)
        private: Whether to make repo private
        commit_message: Optional commit message
    """
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    # Load model size config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)
    
    if model_size not in model_configs:
        raise ValueError(f"Invalid model size: {model_size}")
    
    model_config_dict = model_configs[model_size]
    
    print(f"\n{'='*60}")
    print(f"Uploading SIAD Model to HuggingFace Hub")
    print(f"{'='*60}")
    print(f"Checkpoint: {checkpoint_path}")
    print(f"Model size: {model_size}")
    print(f"Repository: {repo_id}")
    print(f"Config: {model_config_dict}")
    print(f"{'='*60}\n")
    
    # 1. Create HF config
    print("1. Creating HuggingFace config...")
    config = SIADConfig(
        in_channels=8,
        action_dim=2,
        **model_config_dict
    )
    print(f"   ✓ Config created")
    
    # 2. Load model from checkpoint
    print("\n2. Loading model from checkpoint...")
    model = SIADWorldModel.from_checkpoint(checkpoint_path, config=config)
    print(f"   ✓ Model loaded")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Total parameters: {total_params:,} ({total_params / 1e6:.1f}M)")
    
    # 3. Create model card
    print("\n3. Generating model card...")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    
    model_card = f"""---
license: apache-2.0
tags:
  - world-model
  - satellite-imagery
  - earth-observation
  - pytorch
  - transformers
library_name: transformers
pipeline_tag: image-to-image
---

# SIAD World Model ({model_size.capitalize()})

**Satellite Imagery Anticipatory Dynamics** - A transformer-based world model for predicting future satellite observations.

## Model Description

This model predicts future satellite imagery based on:
- Current satellite observations (Sentinel-2, Sentinel-1, VIIRS nightlights)
- Climate action variables (rainfall and temperature anomalies)

Uses **JEPA (Joint Embedding Predictive Architecture)** with token-based spatial representations.

### Architecture

- **Size**: {total_params:,} parameters ({total_params / 1e6:.1f}M)
- **Type**: {model_size} variant
- **Latent Dimension**: {config.latent_dim}
- **Encoder**: {config.encoder_blocks} transformer blocks, {config.encoder_heads} heads
- **Transition Model**: {config.transition_blocks} transformer blocks, {config.transition_heads} heads
- **Spatial Tokens**: 256 tokens (16×16 grid)
- **Input Channels**: 8 (Sentinel-2: B2,B3,B4,B8 | Sentinel-1: VV,VH | VIIRS | mask)
- **Rollout Horizon**: 6 months

### Training

- **Best Val Loss**: {checkpoint.get('best_val_loss', 'N/A'):.4f}
- **Epochs**: {checkpoint.get('epoch', 'N/A')}

## Quick Start

```python
from transformers import AutoModel
import torch

# Load model from HuggingFace Hub
model = AutoModel.from_pretrained("{repo_id}", trust_remote_code=True)
model.inference_mode()

# Prepare inputs
obs_context = torch.randn(1, 8, 256, 256)  # Current observation
actions = torch.randn(1, 6, 2)  # 6-month climate actions

# Run prediction
with torch.no_grad():
    z0 = model.encode(obs_context)
    z_pred = model.rollout(z0, actions, H=6)
    x_pred = model.decode(z_pred)  # [1, 6, 8, 256, 256]

print(f"Predicted 6 months: {{x_pred.shape}}")
```

## Advanced Usage

```python
# Full forward pass with loss computation
outputs = model(
    obs_context=obs_context,
    actions_rollout=actions,
    obs_targets=targets,  # Ground truth for loss
    return_dict=True
)

print(f"Loss: {{outputs.loss}}")
print(f"Predictions: {{outputs.predictions.shape}}")
print(f"Metrics: {{outputs.metrics}}")
```

## Model Configuration

This is the **{model_size}** configuration:

```yaml
latent_dim: {config.latent_dim}
encoder_blocks: {config.encoder_blocks}
encoder_heads: {config.encoder_heads}
encoder_mlp_dim: {config.encoder_mlp_dim}
transition_blocks: {config.transition_blocks}
transition_heads: {config.transition_heads}
transition_mlp_dim: {config.transition_mlp_dim}
dropout: {config.dropout}
```

## Citation

```bibtex
@misc{{siad_world_model,
    title={{SIAD: Satellite Imagery Anticipatory Dynamics}},
    author={{OzLabs.ai}},
    year={{2025}},
    howpublished={{\\url{{https://huggingface.co/{repo_id}}}}},
}}
```

## Links

- [GitHub Repository](https://github.com/ozlabsai/SIAD-WM)
- [Model Documentation](https://github.com/ozlabsai/SIAD-WM/blob/main/docs/MODEL.md)
"""
    
    print(f"   ✓ Model card generated")
    
    # 4. Push to Hub
    print(f"\n4. Pushing to HuggingFace Hub: {repo_id}")
    
    if commit_message is None:
        commit_message = f"Upload SIAD {model_size} model ({total_params / 1e6:.1f}M params)"
    
    model.push_to_hub(
        repo_id=repo_id,
        commit_message=commit_message,
        private=private,
        create_pr=False,
        # Models use safetensors by default in newer transformers
    )
    
    # Also push config and model card
    config.push_to_hub(
        repo_id=repo_id,
        commit_message="Add model configuration"
    )
    
    # Upload model card
    from huggingface_hub import upload_file, HfApi
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(model_card)
        temp_path = f.name
    
    try:
        api = HfApi()
        api.upload_file(
            path_or_fileobj=temp_path,
            path_in_repo="README.md",
            repo_id=repo_id,
            commit_message="Add model card"
        )
    finally:
        Path(temp_path).unlink()
    
    print(f"\n{'='*60}")
    print(f"✓ Upload complete!")
    print(f"{'='*60}")
    print(f"View your model at:")
    print(f"  https://huggingface.co/{repo_id}")
    print(f"\nLoad with:")
    print(f"  from transformers import AutoModel")
    print(f"  model = AutoModel.from_pretrained('{repo_id}', trust_remote_code=True)")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Upload SIAD model to HuggingFace Hub (proper HF format)"
    )
    parser.add_argument("--checkpoint", required=True, help="Path to checkpoint .pth file")
    parser.add_argument("--model-size", required=True,
                       choices=["tiny", "small", "medium", "large", "xlarge"],
                       help="Model size")
    parser.add_argument("--repo-id", required=True,
                       help="HuggingFace repo ID (username/model-name)")
    parser.add_argument("--private", action="store_true",
                       help="Make repository private")
    parser.add_argument("--commit-message", type=str,
                       help="Custom commit message")
    
    args = parser.parse_args()
    
    upload_to_hub(
        checkpoint_path=args.checkpoint,
        model_size=args.model_size,
        repo_id=args.repo_id,
        private=args.private,
        commit_message=args.commit_message
    )


if __name__ == "__main__":
    main()
