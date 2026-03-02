# Training Configuration Examples

Complete guide to training SIAD with different epoch configurations and settings.

## Table of Contents
- [Quick Start with Presets](#quick-start-with-presets)
- [Epoch Configuration Examples](#epoch-configuration-examples)
- [Model Size Experiments](#model-size-experiments)
- [Hyperparameter Tuning](#hyperparameter-tuning)
- [Best Practices](#best-practices)

## Quick Start with Presets

The easiest way to train with different epoch counts:

```bash
# Load preset functions
source scripts/train_presets.sh

# Quick test (10 epochs)
train_quick data/manifest.jsonl

# Standard training (50 epochs)
train_standard data/manifest.jsonl

# Production training (100 epochs)
train_production data/manifest.jsonl

# Long training (200 epochs)
train_long data/manifest.jsonl
```

## Epoch Configuration Examples

### Development & Testing

**Quick validation (10 epochs)**
```bash
# Fastest way to verify your setup works
EPOCHS=10 USE_WANDB=false ./scripts/train_a100.sh data/manifest.jsonl
```

**Short experiment (25 epochs)**
```bash
# Quick experiment with wandb logging
EPOCHS=25 ./scripts/train_a100.sh data/manifest.jsonl
```

### Production Training

**Standard production (100 epochs)**
```bash
# Recommended for most production use cases
EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

**Extended training (200 epochs)**
```bash
# Maximum quality, extended convergence
EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl
```

**Ultra-long training (500 epochs)**
```bash
# For research-quality results (2-2.5 hours)
EPOCHS=500 ./scripts/train_a100.sh data/manifest.jsonl
```

### Custom Epoch Counts

```bash
# Any custom value
EPOCHS=75 ./scripts/train_a100.sh data/manifest.jsonl
EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl
EPOCHS=300 ./scripts/train_a100.sh data/manifest.jsonl
```

## Model Size Experiments

### Tiny Model (54M params) - Default

```bash
# Quick iteration (10 epochs, ~2 min)
MODEL_SIZE=tiny EPOCHS=10 ./scripts/train_a100.sh data/manifest.jsonl

# Standard (50 epochs, ~12 min)
MODEL_SIZE=tiny EPOCHS=50 ./scripts/train_a100.sh data/manifest.jsonl

# Production (100 epochs, ~25 min)
MODEL_SIZE=tiny EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

### Small Model (~150M params)

```bash
# More capacity for complex patterns
MODEL_SIZE=small EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl

# Extended training for convergence
MODEL_SIZE=small EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl
```

### Medium Model (~400M params)

```bash
# Production-quality model
MODEL_SIZE=medium EPOCHS=100 BATCH_SIZE=16 ./scripts/train_a100.sh data/manifest.jsonl

# Reduce batch size if OOM
MODEL_SIZE=medium EPOCHS=150 BATCH_SIZE=8 ./scripts/train_a100.sh data/manifest.jsonl
```

### Large Model (~1B params)

```bash
# Maximum quality (requires A100 80GB)
MODEL_SIZE=large EPOCHS=100 BATCH_SIZE=8 ./scripts/train_a100.sh data/manifest.jsonl

# Extended training
MODEL_SIZE=large EPOCHS=200 BATCH_SIZE=4 ./scripts/train_a100.sh data/manifest.jsonl
```

## Hyperparameter Tuning

### Learning Rate Experiments

```bash
# Lower learning rate + more epochs
LR=5e-5 EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl

# Higher learning rate + fewer epochs
LR=2e-4 EPOCHS=50 ./scripts/train_a100.sh data/manifest.jsonl

# Very fine tuning
LR=1e-5 EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl
```

### Batch Size Experiments

```bash
# Larger batch (faster, more memory)
BATCH_SIZE=64 EPOCHS=50 ./scripts/train_a100.sh data/manifest.jsonl

# Very large batch (A100 80GB has headroom)
BATCH_SIZE=128 EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl

# Smaller batch (better generalization)
BATCH_SIZE=16 EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl

# Mini-batch (for large models)
BATCH_SIZE=8 MODEL_SIZE=large EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

### Combined Tuning

```bash
# Aggressive training
BATCH_SIZE=64 LR=2e-4 EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl

# Conservative training
BATCH_SIZE=16 LR=5e-5 EPOCHS=300 ./scripts/train_a100.sh data/manifest.jsonl

# Production recipe (balanced)
MODEL_SIZE=small BATCH_SIZE=32 LR=1e-4 EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl
```

## Best Practices

### Choosing Epoch Count

**For development:**
- 10-25 epochs: Code validation, debugging
- 50 epochs: Standard experiments, baseline comparisons

**For production:**
- 100 epochs: Most production use cases
- 150-200 epochs: High-quality models
- 300+ epochs: Research-quality results

### Training Time Guidelines

| Epochs | Tiny Model | Small Model | Medium Model | Large Model |
|--------|-----------|-------------|--------------|-------------|
| 10 | 2-3 min | 5-7 min | 10-15 min | 20-30 min |
| 50 | 12-15 min | 25-35 min | 50-75 min | 100-150 min |
| 100 | 25-30 min | 50-70 min | 100-150 min | 200-300 min |
| 200 | 50-60 min | 100-140 min | 200-300 min | 400-600 min |

*Times are approximate for A100 80GB and vary by dataset size*

### Convergence Tips

1. **Monitor validation loss**: Training should converge within 50-100 epochs for tiny model
2. **Use wandb**: Track loss curves to identify convergence
3. **Early stopping**: If val loss plateaus, consider stopping
4. **Checkpoint best model**: Script saves best checkpoint automatically

### Example Workflows

**Rapid prototyping:**
```bash
# 1. Quick test to verify setup
train_quick data/manifest.jsonl

# 2. Short run to check convergence
EPOCHS=25 ./scripts/train_a100.sh data/manifest.jsonl

# 3. Full training if results look good
train_production data/manifest.jsonl
```

**Hyperparameter sweep:**
```bash
# Try different learning rates with fixed epochs
for LR in 5e-5 1e-4 2e-4; do
  LR=$LR EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
done
```

**Model size comparison:**
```bash
# Compare different model sizes with same epochs
for SIZE in tiny small medium; do
  MODEL_SIZE=$SIZE EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
done
```

## Advanced Examples

### Resume Training

```bash
# Train for 100 epochs
EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl

# Resume from checkpoint and train 100 more
# (Manual implementation - modify train.py to load checkpoint)
```

### Multi-Stage Training

```bash
# Stage 1: Quick convergence with high LR
LR=2e-4 EPOCHS=50 ./scripts/train_a100.sh data/manifest.jsonl

# Stage 2: Fine-tune with low LR
# (Would need to load checkpoint and continue)
LR=5e-5 EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

### Distributed Training (Future)

```bash
# Single GPU (current)
EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl

# Multi-GPU (when implemented)
# GPUS=4 EPOCHS=200 ./scripts/train_distributed.sh data/manifest.jsonl
```

## Troubleshooting

### Out of Memory

```bash
# Reduce batch size
BATCH_SIZE=16 EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl

# Or use smaller model
MODEL_SIZE=tiny BATCH_SIZE=32 EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

### Training Too Slow

```bash
# Increase batch size (if memory allows)
BATCH_SIZE=64 EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl

# Reduce workers if CPU bottleneck
NUM_WORKERS=8 EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

### Not Converging

```bash
# Lower learning rate + more epochs
LR=5e-5 EPOCHS=200 ./scripts/train_a100.sh data/manifest.jsonl

# Or increase model capacity
MODEL_SIZE=small LR=5e-5 EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl
```

## Summary

**Quick reference:**

```bash
# Development
train_quick data/manifest.jsonl          # 10 epochs
EPOCHS=25 ./scripts/train_a100.sh        # 25 epochs

# Production
train_production data/manifest.jsonl     # 100 epochs
EPOCHS=200 ./scripts/train_a100.sh       # 200 epochs

# Custom
EPOCHS=150 ./scripts/train_a100.sh       # Any value

# With other settings
MODEL_SIZE=small BATCH_SIZE=48 EPOCHS=100 LR=5e-5 \
  ./scripts/train_a100.sh data/manifest.jsonl
```

For more details, see:
- [QUICKSTART.md](../QUICKSTART.md) - Basic training guide
- [WANDB_MONITORING.md](WANDB_MONITORING.md) - Monitoring training
- [MODEL.md](../MODEL.md) - Model architecture
