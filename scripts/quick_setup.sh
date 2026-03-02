#!/bin/bash
# Quick setup script for GPU pod - copy-paste this entire file

set -e

echo "=========================================="
echo "SIAD Quick Setup on GPU Pod"
echo "=========================================="

# 1. Check GPU
echo -e "\n1. Checking GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo "❌ GPU not found"

# 2. Check environment
echo -e "\n2. Checking Python environment..."
python3 --version
which python3

# 3. Install UV if not present
echo -e "\n3. Checking UV..."
if ! command -v uv &> /dev/null; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
uv --version

# 4. Clone repo if not already present
echo -e "\n4. Setting up repository..."
if [ ! -d ".git" ]; then
    echo "Not in a git repo. Please clone your SIAD repository first:"
    echo "  git clone <your-repo-url> ~/SIAD"
    echo "  cd ~/SIAD"
    exit 1
fi

# 5. Install dependencies
echo -e "\n5. Installing dependencies..."
uv sync

# 6. Install PyTorch for CUDA
echo -e "\n6. Installing PyTorch for CUDA..."
uv pip uninstall torch torchvision -y || true
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 7. Verify CUDA
echo -e "\n7. Verifying CUDA setup..."
uv run python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
uv run python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
uv run python3 -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')" || echo "❌ CUDA not available"

# 8. Check GCS access
echo -e "\n8. Checking GCS access..."
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-siad-earth-engine}"
echo "GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"

# 9. Test model import
echo -e "\n9. Testing SIAD model import..."
uv run python3 -c "from siad.model import WorldModel; print('✓ WorldModel imported')"

# 10. Run tests
echo -e "\n10. Running model tests..."
uv run pytest tests/model/ -v --tb=short

echo -e "\n=========================================="
echo "✓ Setup complete! Ready to train."
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Set GCS credentials if needed"
echo "  2. Start training with: ./scripts/train_a100.sh"
echo ""
