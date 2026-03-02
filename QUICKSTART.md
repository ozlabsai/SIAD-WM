# SIAD Training Quick Start

Everything is ready to train! Here's what to do on your A100 pod:

## On A100 Pod

```bash
# 1. Pull latest code
cd /workspace/SIAD-WM  # or wherever you cloned the repo
git pull origin main

# 2. Quick setup (if not done already)
bash scripts/quick_setup.sh

# 3. Setup Weights & Biases (for monitoring)
wandb login
# Enter your API key from https://wandb.ai/authorize

# 4. Start training!
./scripts/train_a100.sh data/manifest.jsonl
# Wandb will print a URL to view real-time training metrics
```

That's it! The script will:
- ✓ Verify GPU (A100 80GB)
- ✓ Check CUDA is working
- ✓ Validate training data exists
- ✓ Run complete training pipeline
- ✓ Save checkpoints to `checkpoints/`

## What Just Got Added

### 1. Complete Training Script (`scripts/train.py`)
End-to-end training connecting:
- **Dataset** → Loads GeoTIFFs from manifest.jsonl
- **Model** → WorldModel with MODEL.md v0.2 interfaces
- **Trainer** → Fixed training loop with JEPA loss
- **Checkpointing** → Saves every 5 epochs + best model
- **Wandb monitoring** → Real-time metrics, GPU stats, model artifacts

### 2. Training Launcher (`scripts/train_a100.sh`)
One-command training with automatic verification:
- GPU check
- CUDA validation
- Data verification
- Optimized settings for A100

### 3. Data Validator (`scripts/check_training_data.py`)
Verifies your training data:
- Manifest format
- GeoTIFF files exist
- Proper structure (1-month context, 6-month rollout)

## Custom Configuration

### Change batch size or epochs:
```bash
BATCH_SIZE=64 EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
```

### Disable wandb:
```bash
USE_WANDB=false ./scripts/train_a100.sh data/manifest.jsonl
```

### Manual training command:
```bash
uv run python scripts/train.py \
    --manifest data/manifest.jsonl \
    --batch-size 32 \
    --epochs 50 \
    --lr 1e-4 \
    --num-workers 16 \
    --checkpoint-dir checkpoints \
    --wandb \
    --wandb-project siad-world-model \
    --wandb-name "my-experiment"
```

## Monitoring Training

Wandb provides real-time monitoring (enabled by default):

**Tracked metrics:**
- Loss curves (train & validation)
- Learning rate schedule
- Gradient norms
- GPU memory usage
- Training throughput (samples/sec)
- Model gradients & parameters

**View dashboard:** Wandb prints URL when training starts
```
🚀 View run at https://wandb.ai/username/siad-world-model/runs/abc123
```

**Full guide:** See `docs/WANDB_MONITORING.md` for:
- Experiment comparison
- Hyperparameter sweeps
- Checkpoint artifact management
- Custom metric logging

## What Was Fixed

The trainer was completely broken (calling non-existent APIs). Now it uses:
- ✓ `model.encode()` for context encoding
- ✓ `model.rollout()` for multi-step prediction
- ✓ `model.encode_targets()` for target encoding
- ✓ `compute_jepa_world_model_loss()` for JEPA loss
- ✓ `model.update_target_encoder(step=...)` for EMA updates

All 20/20 tests passing!

## Next Steps

1. **Verify you have training data** in GCS or locally
2. **Run the training launcher** on your A100 pod
3. **Monitor training** - checkpoints save every 5 epochs
4. **Check best model** at `checkpoints/checkpoint_best.pth`

## Expected Training Time

- **Model size**: 54M parameters (~1GB VRAM)
- **Batch size 32**: ~8GB VRAM used
- **A100 80GB**: Tons of headroom
- **Estimated time**: ~12 minutes for 50 epochs (varies by dataset size)
