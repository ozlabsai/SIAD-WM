# SIAD Setup Guide

Quick setup guide for running SIAD World Model on a new machine.

## Prerequisites

- Git
- Internet connection
- Google Cloud account with access to `siad-earth-engine` project

## Setup Steps

### 1. Install UV (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

UV will automatically manage Python versions and dependencies.

### 2. Clone Repository

```bash
git clone <your-repo-url>
cd SIAD
```

### 3. Install Dependencies

```bash
# UV automatically:
# - Installs Python 3.9
# - Creates virtual environment
# - Installs all packages from pyproject.toml
uv sync
```

### 4. Configure Google Cloud Access

**Option A: Service Account (for GPU/Cloud machines)**

1. Create service account in GCP Console
2. Download JSON key file
3. Grant permissions: Storage Admin, Earth Engine permissions
4. Set environment variables:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="siad-earth-engine"
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

**Option B: User Credentials (for development)**

```bash
# Install gcloud CLI first
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="siad-earth-engine"
```

### 5. Verify Setup

```bash
uv run python scripts/verify_setup.py
```

This checks:
- Python version (3.9)
- Dependencies (PyTorch, GCS, Earth Engine)
- Model imports
- GCP credentials
- Data access

## Quick Test

### Test Model Import

```bash
uv run python -c "from siad.model import WorldModel; print('✓ Model imported successfully')"
```

### Run Unit Tests

```bash
uv run pytest tests/model/ -v
```

Should see: `20 passed`

## Data Access

### Check Available Data

```bash
export GOOGLE_CLOUD_PROJECT=siad-earth-engine
uv run python scripts/check_gcs_data.py
```

### Export New Data (if needed)

```bash
export GOOGLE_CLOUD_PROJECT=siad-earth-engine
uv run siad export --config configs/test-export.yaml
```

Monitor at: https://code.earthengine.google.com/tasks

## Training

### Basic Training Run

```bash
# Coming soon - trainer.py needs updating to use new MODEL.md interfaces
# Will use: uv run siad train --config configs/train.yaml
```

## GPU Setup

### For CUDA GPUs

UV will automatically install the CPU version of PyTorch. For GPU:

```bash
# Uninstall CPU torch
uv pip uninstall torch torchvision

# Install GPU version (CUDA 11.8 example)
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

Verify GPU:
```bash
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Common Issues

### "GOOGLE_CLOUD_PROJECT not set"
```bash
export GOOGLE_CLOUD_PROJECT="siad-earth-engine"
```

### "Permission denied" on GCS
- Check service account has Storage Admin role
- Verify credentials file exists and path is correct

### "ModuleNotFoundError"
```bash
uv sync  # Re-sync dependencies
```

### NumPy version conflicts
```bash
uv pip install "numpy<2"  # Downgrade to 1.x if needed
```

## Project Structure

```
SIAD/
├── src/siad/
│   ├── model/          # World model (encoder, transition, losses)
│   ├── data/           # Data loading and preprocessing
│   ├── train/          # Training loops
│   └── eval/           # Evaluation and metrics
├── tests/              # Unit tests
├── configs/            # YAML configuration files
├── scripts/            # Utility scripts
└── docs/               # Documentation
```

## Next Steps

1. Run `scripts/verify_setup.py` to confirm everything works
2. Check data availability with `scripts/check_gcs_data.py`
3. Review `MODEL.md` for architecture details
4. Run tests: `uv run pytest tests/model/ -v`

## Support

- Architecture spec: `MODEL.md`
- Data collection: `DATA.md`
- Issues: Check logs in `logs/` directory
