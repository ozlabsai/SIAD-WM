# A100 80GB Setup Guide

Quick setup for training SIAD on A100 80GB SXM.

## 1. Install CUDA Toolkit

```bash
# Check NVIDIA driver
nvidia-smi

# Should show:
# - Driver Version: 525.x or higher
# - CUDA Version: 12.x

# If missing, install CUDA 12.1
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run
```

## 2. Clone and Install SIAD

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repo
git clone <your-repo-url>
cd SIAD

# Install dependencies
uv sync

# Install PyTorch for CUDA 12.1
uv pip uninstall torch torchvision
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## 3. Verify GPU Setup

```bash
# Check CUDA available
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
uv run python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"

# Should output:
# CUDA available: True
# GPU: NVIDIA A100-SXM4-80GB
```

## 4. Configure Google Cloud Access

```bash
# Set environment variables (add to ~/.bashrc)
export GOOGLE_CLOUD_PROJECT="siad-earth-engine"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Or use gcloud auth
gcloud auth application-default login
```

## 5. Run Setup Verification

```bash
uv run python scripts/verify_setup.py
```

Should show all checks passing.

## 6. Optimize for A100

### A. Enable TensorFloat-32 (TF32)

TF32 gives you ~5x speedup on A100 with no code changes:

```bash
# Add to training script or config
export NVIDIA_TF32_OVERRIDE=1
```

Or in Python:
```python
import torch
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
```

### B. Set Optimal Batch Size

The A100 80GB can handle very large batches:

```bash
# Start with batch_size=32, increase if GPU utilization < 80%
uv run nvidia-smi dmon -s um
```

### C. Multi-threading for Data Loading

```yaml
# In your config
num_workers: 16  # A100 servers typically have 32+ CPU cores
pin_memory: true
persistent_workers: true
```

## 7. Training Commands

### Quick Test (1 epoch)

```bash
export GOOGLE_CLOUD_PROJECT=siad-earth-engine
uv run siad train \
  --config configs/train.yaml \
  --batch_size 32 \
  --epochs 1 \
  --checkpoint_dir checkpoints/test
```

### Full Training Run

```bash
export GOOGLE_CLOUD_PROJECT=siad-earth-engine
uv run siad train \
  --config configs/train.yaml \
  --batch_size 32 \
  --epochs 50 \
  --checkpoint_dir checkpoints/run_001
```

### Monitor GPU Usage

```bash
# In separate terminal
watch -n 1 nvidia-smi
```

## 8. Expected Performance

With A100 80GB SXM:

- **Batch size**: 32-64 (sweet spot)
- **Training speed**: ~500-600 samples/sec
- **Time per epoch**: 12-20 seconds (depends on dataset size)
- **Full training (50 epochs)**: 10-20 minutes
- **GPU utilization**: 70-90%
- **VRAM usage**: 2-4 GB (barely scratching the surface!)

## 9. Advanced: Multi-GPU (if available)

If you have multiple A100s:

```bash
# Check number of GPUs
nvidia-smi -L

# Use DDP (Distributed Data Parallel)
torchrun --nproc_per_node=4 \
  -m siad.train.train \
  --config configs/train.yaml \
  --batch_size 128  # 32 per GPU × 4 GPUs
```

## 10. Troubleshooting

### "CUDA out of memory"
```bash
# Reduce batch size
--batch_size 16
```

### "Slow data loading"
```bash
# Increase workers
--num_workers 32

# Check GCS bandwidth
gsutil -m cp gs://siad-training-data/test.tfrecord .
```

### "Low GPU utilization"
```bash
# Increase batch size
--batch_size 64

# Enable TF32
export NVIDIA_TF32_OVERRIDE=1
```

## 11. Monitoring Training

### WandB (recommended)

```bash
# Install
uv pip install wandb

# Login
wandb login

# Training will auto-log to wandb
```

### TensorBoard

```bash
# Start tensorboard
tensorboard --logdir checkpoints/run_001/logs

# Open http://localhost:6006
```

## 12. Cost Savings Tips

Since A100 time is valuable:

1. **Test on small data first** - Verify pipeline works before full training
2. **Use checkpointing** - Resume if interrupted
3. **Monitor closely** - Don't waste GPU time on bad hyperparameters
4. **Batch experiments** - Run multiple configs sequentially

## Quick Reference

```bash
# Single command to start training
export GOOGLE_CLOUD_PROJECT=siad-earth-engine && \
export NVIDIA_TF32_OVERRIDE=1 && \
uv run siad train --config configs/train.yaml --batch_size 32
```

## Support

- GPU issues: Check `nvidia-smi`, driver version
- Data issues: Check `GOOGLE_CLOUD_PROJECT` env var
- Model issues: Run `uv run pytest tests/model/ -v`
