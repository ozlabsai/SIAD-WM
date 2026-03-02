# SIAD Training Scripts

This directory contains all scripts needed to train SIAD world models on A100 GPUs.

## Quick Start

```bash
# Standard training (50 epochs)
./scripts/train_a100.sh data/manifest.jsonl

# Quick test (10 epochs)
EPOCHS=10 ./scripts/train_a100.sh data/manifest.jsonl

# Production training (100 epochs)
EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

## Available Scripts

### Main Training Scripts

**`train_a100.sh`** - Primary training launcher
- Validates GPU, CUDA, and data setup
- Configurable via environment variables
- Optimized for A100 80GB
- Includes comprehensive error checking

**`train.py`** - Core training implementation
- Loads data from manifest.jsonl
- Creates model with configurable size
- Runs training loop with JEPA loss
- Saves checkpoints every 5 epochs
- Integrated wandb monitoring

**`train_presets.sh`** - Convenient training presets
- `train_quick` - 10 epochs, no wandb (~2-3 min)
- `train_standard` - 50 epochs (~12-15 min)
- `train_production` - 100 epochs (~25-30 min)
- `train_long` - 200 epochs (~50-60 min)
- `train_large_batch` - batch=64 (~8-10 min)
- `train_tiny` - tiny model, 10 epochs (~1 min)

### Supporting Scripts

**`check_training_data.py`** - Data validation
- Verifies manifest format
- Checks GeoTIFF files exist
- Validates data structure

**`quick_setup.sh`** - Environment setup
- Installs dependencies
- Configures Python environment
- Sets up UV package manager

## Configuration Options

All training parameters can be configured via environment variables:

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `EPOCHS` | `50` | Number of training epochs | `EPOCHS=100` |
| `BATCH_SIZE` | `32` | Training batch size | `BATCH_SIZE=64` |
| `MODEL_SIZE` | `tiny` | Model size (tiny/small/medium/large/xlarge) | `MODEL_SIZE=small` |
| `LR` | `1e-4` | Learning rate | `LR=5e-5` |
| `NUM_WORKERS` | `16` | DataLoader worker processes | `NUM_WORKERS=8` |
| `USE_WANDB` | `true` | Enable Weights & Biases logging | `USE_WANDB=false` |
| `WANDB_PROJECT` | `siad-world-model` | Wandb project name | `WANDB_PROJECT=my-project` |

## Usage Examples

### Using Presets (Recommended)

```bash
# Load preset functions
source scripts/train_presets.sh

# Quick test
train_quick data/manifest.jsonl

# Production training
train_production data/manifest.jsonl

# View all presets
./scripts/train_presets.sh
```

### Using Environment Variables

```bash
# Different epoch counts
EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl

# Different model sizes
MODEL_SIZE=small EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
MODEL_SIZE=medium EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl

# Combine multiple settings
MODEL_SIZE=small BATCH_SIZE=48 EPOCHS=150 LR=5e-5 \
  ./scripts/train_a100.sh data/manifest.jsonl

# Disable wandb
USE_WANDB=false EPOCHS=10 ./scripts/train_a100.sh data/manifest.jsonl
```

### Direct Python Script

```bash
# Full control over all parameters
uv run python scripts/train.py \
    --manifest data/manifest.jsonl \
    --data-root data/geotiffs \
    --model-size tiny \
    --batch-size 32 \
    --epochs 100 \
    --lr 1e-4 \
    --num-workers 16 \
    --checkpoint-dir checkpoints \
    --wandb \
    --wandb-project siad-world-model \
    --wandb-name "experiment-1"
```

## Epoch Configuration Guide

### Development

- **10 epochs**: Quick validation, debugging (~2-3 min)
- **25 epochs**: Short experiments (~6-7 min)
- **50 epochs**: Standard development (~12-15 min)

### Production

- **100 epochs**: Standard production (~25-30 min)
- **150 epochs**: High-quality models (~37-45 min)
- **200 epochs**: Maximum quality (~50-60 min)
- **300+ epochs**: Research-grade results (~75+ min)

### Choosing Epoch Count

**Consider these factors:**
1. **Model size**: Larger models need more epochs to converge
2. **Dataset size**: More data may need fewer epochs
3. **Learning rate**: Lower LR benefits from more epochs
4. **Time constraints**: Match epochs to available GPU time

**General guidelines:**
- Start with 50 epochs for baseline
- Monitor validation loss curve in wandb
- Increase to 100-200 if still improving
- Stop early if loss plateaus

## Model Sizes

From `configs/model_sizes.yaml`:

| Size | Parameters | Memory (fp32) | Batch Size | Recommended Epochs |
|------|-----------|---------------|------------|-------------------|
| tiny | 54M | ~1GB | 32-128 | 50-100 |
| small | ~150M | ~2.5GB | 16-64 | 100-150 |
| medium | ~400M | ~6GB | 8-32 | 100-200 |
| large | ~1B | ~15GB | 4-16 | 150-300 |
| xlarge | ~2.5B | ~35GB | 1-8 | 200-500 |

## Training Workflow

### Step 1: Prepare Data

```bash
# Verify manifest exists
ls -lh data/manifest.jsonl

# Check data quality
uv run python scripts/check_training_data.py --manifest data/manifest.jsonl
```

### Step 2: Choose Configuration

```bash
# Quick test first
source scripts/train_presets.sh
train_quick data/manifest.jsonl

# If successful, run full training
train_production data/manifest.jsonl
```

### Step 3: Monitor Training

```bash
# Training outputs wandb URL
🚀 View run at https://wandb.ai/username/siad-world-model/runs/abc123

# Watch metrics:
# - train/loss, val/loss
# - Learning rate schedule
# - GPU memory usage
# - Training throughput
```

### Step 4: Use Checkpoints

```bash
# Checkpoints saved to:
checkpoints/
├── checkpoint_best.pth      # Best validation loss
├── checkpoint_final.pth     # Final epoch
├── checkpoint_epoch_5.pth   # Every 5 epochs
├── checkpoint_epoch_10.pth
└── ...

# Load checkpoint in your code:
checkpoint = torch.load("checkpoints/checkpoint_best.pth")
model.load_state_dict(checkpoint["model_state_dict"])
```

## Troubleshooting

### Out of Memory

```bash
# Reduce batch size
BATCH_SIZE=16 ./scripts/train_a100.sh data/manifest.jsonl

# Or use smaller model
MODEL_SIZE=tiny ./scripts/train_a100.sh data/manifest.jsonl

# Or reduce workers
NUM_WORKERS=8 ./scripts/train_a100.sh data/manifest.jsonl
```

### Training Too Slow

```bash
# Increase batch size (if memory allows)
BATCH_SIZE=64 ./scripts/train_a100.sh data/manifest.jsonl

# Enable TF32 (should be automatic on A100)
export NVIDIA_TF32_OVERRIDE=1

# Use larger model with fewer epochs
MODEL_SIZE=small EPOCHS=50 ./scripts/train_a100.sh data/manifest.jsonl
```

### Not Converging

```bash
# Lower learning rate + more epochs
LR=5e-5 EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl

# Or increase model capacity
MODEL_SIZE=small EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl

# Check data quality
uv run python scripts/check_training_data.py --manifest data/manifest.jsonl
```

### CUDA Not Available

```bash
# Check GPU
nvidia-smi

# Verify PyTorch CUDA
uv run python -c "import torch; print(torch.cuda.is_available())"

# Check CUDA version
uv run python -c "import torch; print(torch.version.cuda)"
```

## Performance Tips

### A100 80GB Optimization

1. **Use larger batches**: A100 has plenty of memory
   ```bash
   BATCH_SIZE=64 ./scripts/train_a100.sh data/manifest.jsonl
   ```

2. **Enable TF32**: Automatic on A100, verify with:
   ```bash
   echo $NVIDIA_TF32_OVERRIDE  # Should be 1
   ```

3. **Use more workers**: A100 pods have many CPU cores
   ```bash
   NUM_WORKERS=32 ./scripts/train_a100.sh data/manifest.jsonl
   ```

4. **Pin memory**: Already enabled in train.py
   ```python
   pin_memory=True  # In DataLoader
   ```

### Training Speed Reference

On A100 80GB with batch_size=32:

| Model Size | Steps/sec | Epochs/min | 100 epochs |
|-----------|-----------|------------|------------|
| tiny | 250-300 | ~2 | ~50 min |
| small | 100-150 | ~0.8 | ~125 min |
| medium | 40-60 | ~0.3 | ~330 min |
| large | 15-25 | ~0.1 | ~1000 min |

*Times vary by dataset size*

## Additional Resources

- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [TRAINING_EXAMPLES.md](../docs/TRAINING_EXAMPLES.md) - Comprehensive examples
- [WANDB_MONITORING.md](../docs/WANDB_MONITORING.md) - Monitoring guide
- [MODEL.md](../MODEL.md) - Model architecture
- [configs/model_sizes.yaml](../configs/model_sizes.yaml) - Model configurations

## Getting Help

```bash
# View train.py options
uv run python scripts/train.py --help

# View preset options
./scripts/train_presets.sh

# Check training data
uv run python scripts/check_training_data.py --help
```
