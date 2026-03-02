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
MODEL_SIZE="${MODEL_SIZE:-tiny}"
CONTEXT_LENGTH="${CONTEXT_LENGTH:-1}"
BATCH_SIZE="${BATCH_SIZE:-32}"
EPOCHS="${EPOCHS:-50}"
LR="${LR:-1e-4}"
NUM_WORKERS="${NUM_WORKERS:-16}"
USE_WANDB="${USE_WANDB:-true}"
WANDB_PROJECT="${WANDB_PROJECT:-siad-world-model}"

echo -e "\n6. Training configuration:"
echo "  Manifest:        $MANIFEST"
echo "  Model size:      $MODEL_SIZE"
echo "  Context length:  $CONTEXT_LENGTH month(s)"
echo "  Batch size:      $BATCH_SIZE"
echo "  Epochs:          $EPOCHS"
echo "  Learning rate:   $LR"
echo "  Workers:         $NUM_WORKERS"
echo "  Wandb:           $USE_WANDB"
if [ "$USE_WANDB" = "true" ]; then
    echo "  Wandb project:   $WANDB_PROJECT"
fi

# Provide batch size recommendations based on context length
if [ "$CONTEXT_LENGTH" -eq 1 ] && [ "$BATCH_SIZE" -ne 32 ]; then
    echo ""
    echo "  NOTE: For context_length=1, recommended batch_size=32 (memory efficient)"
elif [ "$CONTEXT_LENGTH" -eq 3 ] && [ "$BATCH_SIZE" -gt 24 ]; then
    echo ""
    echo "  WARNING: For context_length=3, recommended batch_size=24 or lower (memory usage)"
elif [ "$CONTEXT_LENGTH" -eq 6 ] && [ "$BATCH_SIZE" -gt 16 ]; then
    echo ""
    echo "  WARNING: For context_length=6, recommended batch_size=16 or lower (high memory usage)"
fi

# Check training data
echo -e "\n7. Checking training data..."
if [ -f "$MANIFEST" ]; then
    uv run python scripts/check_training_data.py --manifest "$MANIFEST" --data-root data/geotiffs
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

# Build training command
TRAIN_CMD="uv run python scripts/train.py \
    --manifest \"$MANIFEST\" \
    --data-root data/geotiffs \
    --model-size $MODEL_SIZE \
    --context-length $CONTEXT_LENGTH \
    --batch-size $BATCH_SIZE \
    --epochs $EPOCHS \
    --lr $LR \
    --num-workers $NUM_WORKERS \
    --checkpoint-dir checkpoints"

# Add wandb flags if enabled
if [ "$USE_WANDB" = "true" ]; then
    TRAIN_CMD="$TRAIN_CMD --wandb --wandb-project \"$WANDB_PROJECT\""
fi

# Execute training
eval $TRAIN_CMD

echo ""
echo "========================================="
echo "Training complete!"
echo "Checkpoints saved to: checkpoints/"
echo "========================================="
