#!/usr/bin/env python3
"""Upload trained SIAD model to Hugging Face Hub

Uploads model checkpoint with naming convention: {model_name}-{size}
Example: siad-tiny, siad-medium, siad-large

Usage:
    python scripts/upload_to_hf.py \
        --checkpoint checkpoints/checkpoint_final.pth \
        --model-size tiny \
        --model-name siad \
        --hf-username your-username
"""

import argparse
import json
import yaml
from pathlib import Path
import torch
from huggingface_hub import HfApi, create_repo
from datetime import datetime

from siad.model import WorldModel


def create_model_card(
    model_name: str,
    model_size: str,
    model_config: dict,
    training_info: dict,
    checkpoint_path: Path
) -> str:
    """Generate model card markdown"""
    repo_name = f"{model_name}-{model_size}"

    # Count parameters
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        **model_config
    )
    total_params = sum(p.numel() for p in model.parameters())

    card = f"""---
language: en
license: apache-2.0
tags:
  - world-model
  - satellite-imagery
  - earth-observation
  - geospatial
  - time-series-prediction
  - pytorch
datasets:
  - sentinel-2
  - sentinel-1
  - viirs-nightlights
metrics:
  - mse
  - cosine-similarity
library_name: pytorch
pipeline_tag: image-to-image
---

# {repo_name.upper()}: SIAD World Model ({model_size.capitalize()})

**Satellite Imagery Anticipatory Dynamics (SIAD)** - A world model for predicting future satellite observations.

## Model Description

This is the **{model_size}** variant of the SIAD world model, trained to predict future satellite imagery based on:
- Current satellite observations (Sentinel-2, Sentinel-1, VIIRS nightlights)
- Climate action variables (rainfall and temperature anomalies)

The model uses a **JEPA (Joint Embedding Predictive Architecture)** to learn spatial-temporal dynamics in the latent space.

### Model Architecture

- **Type**: Token-based world model with EMA target encoder
- **Size**: {total_params:,} parameters ({total_params / 1e6:.1f}M)
- **Latent Dimension**: {model_config['latent_dim']}
- **Encoder**: {model_config['encoder_blocks']} transformer blocks, {model_config['encoder_heads']} heads
- **Transition Model**: {model_config['transition_blocks']} transformer blocks, {model_config['transition_heads']} heads
- **Spatial Tokens**: 256 tokens (16×16 grid)
- **Input Channels**: 8 (Sentinel-2: B2,B3,B4,B8 | Sentinel-1: VV,VH | VIIRS | Valid mask)
- **Output**: 6-month rollout predictions

### Training Details

- **Epochs**: {training_info.get('epochs', 'N/A')}
- **Best Validation Loss**: {training_info.get('best_val_loss', 'N/A'):.4f}
- **Training Date**: {training_info.get('date', datetime.now().strftime('%Y-%m-%d'))}

## Usage

```python
import torch
from huggingface_hub import hf_hub_download

# Download model
checkpoint_path = hf_hub_download(
    repo_id="{model_name}-{model_size}",
    filename="model.pth"
)

# Load checkpoint
checkpoint = torch.load(checkpoint_path, map_location="cpu")

# Create model
from siad.model import WorldModel

model = WorldModel(
    in_channels=8,
    action_dim=2,
    latent_dim={model_config['latent_dim']},
    encoder_blocks={model_config['encoder_blocks']},
    encoder_heads={model_config['encoder_heads']},
    encoder_mlp_dim={model_config['encoder_mlp_dim']},
    transition_blocks={model_config['transition_blocks']},
    transition_heads={model_config['transition_heads']},
    transition_mlp_dim={model_config['transition_mlp_dim']},
    dropout={model_config['dropout']}
)

model.load_state_dict(checkpoint['model_state_dict'])
model.to('cuda' if torch.cuda.is_available() else 'cpu')
model.inference_mode()

# Run inference
with torch.no_grad():
    # x_context: [B, C=8, H=256, W=256] - current observation
    # actions: [B, H=6, 2] - 6-month climate actions
    z0 = model.encode(x_context)
    z_pred = model.rollout(z0, actions, H=6)
    x_pred = model.decode(z_pred)  # [B, H=6, C=8, H=256, W=256]
```

## Intended Use

- **Primary**: Research in satellite imagery prediction and world modeling
- **Applications**: Climate change prediction, agricultural monitoring, urban development forecasting

## Limitations

- Trained on limited geographic coverage
- Single-month context window
- Requires external climate forecasts
- Output resolution: 256×256 pixels at 10m/pixel (2.56km × 2.56km)
"""
    return card


def upload_model(
    checkpoint_path: str,
    model_size: str,
    model_name: str = "siad",
    hf_username: str = None,
    private: bool = False,
    training_info: dict = None
):
    """Upload model to Hugging Face Hub"""
    if not hf_username:
        raise ValueError("Must provide --hf-username")

    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    if model_size not in model_configs:
        raise ValueError(f"Invalid model size: {model_size}")

    model_config = model_configs[model_size]

    # Load checkpoint
    print(f"Loading checkpoint: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    if training_info is None:
        training_info = {}

    # Extract info from checkpoint
    if 'epoch' in checkpoint:
        training_info['epochs'] = checkpoint['epoch']
    if 'best_val_loss' in checkpoint:
        training_info['best_val_loss'] = checkpoint['best_val_loss']

    # Create repo
    repo_id = f"{hf_username}/{model_name}-{model_size}"

    print(f"\nUploading to: {repo_id}")

    api = HfApi()
    create_repo(repo_id=repo_id, repo_type="model", private=private, exist_ok=True)

    # Create temp upload directory
    upload_dir = Path("tmp_hf_upload")
    upload_dir.mkdir(exist_ok=True)

    try:
        import shutil
        
        # Copy model
        model_path = upload_dir / "model.pth"
        shutil.copy(checkpoint_path, model_path)

        # Save config
        config_json = upload_dir / "config.json"
        with open(config_json, 'w') as f:
            json.dump({
                "model_type": "siad-world-model",
                "model_size": model_size,
                "architecture": model_config,
                "input_channels": 8,
                "action_dim": 2,
            }, f, indent=2)

        # Create model card
        card_path = upload_dir / "README.md"
        with open(card_path, 'w') as f:
            f.write(create_model_card(
                model_name, model_size, model_config,
                training_info, checkpoint_path
            ))

        # Upload
        api.upload_folder(
            folder_path=str(upload_dir),
            repo_id=repo_id,
            repo_type="model",
        )

        print(f"\n✓ Uploaded to: https://huggingface.co/{repo_id}")

    finally:
        import shutil
        if upload_dir.exists():
            shutil.rmtree(upload_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--model-size", required=True,
                       choices=["tiny", "small", "medium", "large", "xlarge"])
    parser.add_argument("--model-name", default="siad")
    parser.add_argument("--hf-username", required=True)
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    upload_model(
        checkpoint_path=args.checkpoint,
        model_size=args.model_size,
        model_name=args.model_name,
        hf_username=args.hf_username,
        private=args.private
    )


if __name__ == "__main__":
    main()
