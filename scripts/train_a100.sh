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
CONFIG="${1:-configs/train_a100.yaml}"
BATCH_SIZE="${2:-32}"
EPOCHS="${3:-50}"

echo -e "\n6. Training configuration:"
echo "  Config:     $CONFIG"
echo "  Batch size: $BATCH_SIZE"
echo "  Epochs:     $EPOCHS"

# Confirm
read -p "Start training? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Training cancelled."
    exit 0
fi

# Start training
echo -e "\n7. Starting training..."
echo "========================================="

# Run training (will be implemented when trainer.py is updated)
# For now, this is a placeholder
echo "Note: Training command will be available after trainer.py is updated to use new MODEL.md interfaces"
echo ""
echo "Command will be:"
echo "  uv run siad train --config $CONFIG --batch_size $BATCH_SIZE --epochs $EPOCHS"

# TODO: Uncomment when trainer is ready
# uv run siad train \
#   --config "$CONFIG" \
#   --batch_size "$BATCH_SIZE" \
#   --epochs "$EPOCHS"

echo ""
echo "========================================="
echo "Setup complete! GPU ready for training."
echo "========================================="
