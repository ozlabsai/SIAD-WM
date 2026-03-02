#!/bin/bash
# Quick start training script for A100 80GB

set -e  # Exit on error

echo "========================================="
echo "SIAD Training on A100 80GB"
echo "========================================="

# Check GPU
echo -e "\n1. Checking GPU..."
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
if [ $? -ne 0 ]; then
    echo "ERROR: nvidia-smi failed. Check NVIDIA driver installation."
    exit 1
fi

# Set environment
echo -e "\n2. Setting environment..."
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-siad-earth-engine}"
export NVIDIA_TF32_OVERRIDE=1  # Enable TF32 for A100 speedup

echo "  GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
echo "  NVIDIA_TF32_OVERRIDE=$NVIDIA_TF32_OVERRIDE"

# Check Python/UV
echo -e "\n3. Checking Python environment..."
if ! command -v uv &> /dev/null; then
    echo "ERROR: UV not found. Install with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Verify CUDA
echo -e "\n4. Verifying CUDA..."
uv run python -c "import torch; assert torch.cuda.is_available(), 'CUDA not available'; print(f'✓ PyTorch CUDA: {torch.version.cuda}')"
uv run python -c "import torch; print(f'✓ GPU: {torch.cuda.get_device_name(0)}')"
uv run python -c "import torch; print(f'✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')"

# Check data access
echo -e "\n5. Checking data access..."
uv run python -c "from google.cloud import storage; client = storage.Client(); print('✓ GCS authenticated')"

# Parse arguments
MANIFEST="${1:-data/manifest.jsonl}"
BATCH_SIZE="${BATCH_SIZE:-32}"
EPOCHS="${EPOCHS:-50}"
LR="${LR:-1e-4}"
NUM_WORKERS="${NUM_WORKERS:-16}"

echo -e "\n6. Training configuration:"
echo "  Manifest:    $MANIFEST"
echo "  Batch size:  $BATCH_SIZE"
echo "  Epochs:      $EPOCHS"
echo "  Learning rate: $LR"
echo "  Workers:     $NUM_WORKERS"

# Check training data
echo -e "\n7. Checking training data..."
if [ -f "$MANIFEST" ]; then
    uv run python scripts/check_training_data.py --manifest "$MANIFEST"
else
    echo "⚠️  Warning: Manifest not found at $MANIFEST"
    echo "   Specify manifest path as first argument"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Training cancelled."
        exit 0
    fi
fi

# Start training
echo -e "\n8. Starting training..."
echo "========================================="

uv run python scripts/train.py \
    --manifest "$MANIFEST" \
    --batch-size "$BATCH_SIZE" \
    --epochs "$EPOCHS" \
    --lr "$LR" \
    --num-workers "$NUM_WORKERS" \
    --checkpoint-dir checkpoints

echo ""
echo "========================================="
echo "Training complete!"
echo "Checkpoints saved to: checkpoints/"
echo "========================================="
