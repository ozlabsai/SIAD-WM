#!/bin/bash
# Emergency disk cleanup when training fails with "No space left on device"
#
# Removes:
#   1. All old epoch checkpoints (checkpoint_epoch_*.pth)
#   2. Wandb staging files and old runs
#   3. UV cache
#   4. Python cache files
#
# Keeps:
#   - checkpoint_best.pth
#   - checkpoint_latest.pth
#   - checkpoint_final.pth
#   - Most recent wandb run

set -e

echo "=================================="
echo "Emergency Disk Space Cleanup"
echo "=================================="
echo ""

# Show disk usage before
echo "Disk usage BEFORE cleanup:"
df -h / | grep -v Filesystem
echo ""

FREED=0

# 1. Remove old checkpoint files
echo "1. Removing old epoch checkpoints..."
if [ -d "checkpoints" ]; then
    CHECKPOINT_COUNT=$(find checkpoints -name "checkpoint_epoch_*.pth" 2>/dev/null | wc -l || echo 0)
    if [ "$CHECKPOINT_COUNT" -gt 0 ]; then
        echo "   Found $CHECKPOINT_COUNT old checkpoints"
        find checkpoints -name "checkpoint_epoch_*.pth" -delete
        echo "   ✓ Removed $CHECKPOINT_COUNT epoch checkpoints"
    else
        echo "   No old checkpoints found"
    fi
fi

# 2. Clean wandb staging and old runs (keep latest)
echo ""
echo "2. Cleaning wandb files..."
if [ -d "wandb" ]; then
    # Remove staging files
    if [ -d "$HOME/.local/share/wandb/artifacts/staging" ]; then
        rm -rf "$HOME/.local/share/wandb/artifacts/staging"/*
        echo "   ✓ Cleared wandb staging area"
    fi
    
    # Keep only latest 2 runs
    RUN_COUNT=$(find wandb -maxdepth 1 -type d -name "run-*" 2>/dev/null | wc -l || echo 0)
    if [ "$RUN_COUNT" -gt 2 ]; then
        echo "   Found $RUN_COUNT wandb runs, keeping latest 2"
        find wandb -maxdepth 1 -type d -name "run-*" | sort | head -n -2 | xargs rm -rf
        echo "   ✓ Removed old wandb runs"
    fi
fi

# 3. Clean UV cache
echo ""
echo "3. Cleaning UV cache..."
if command -v uv &> /dev/null; then
    uv cache clean 2>/dev/null || true
    echo "   ✓ Cleared UV cache"
fi

# 4. Clean Python cache
echo ""
echo "4. Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "   ✓ Cleared Python cache"

# 5. Show what's left
echo ""
echo "=================================="
echo "Remaining checkpoints:"
ls -lh checkpoints/checkpoint_*.pth 2>/dev/null || echo "  (none found)"

echo ""
echo "Disk usage AFTER cleanup:"
df -h / | grep -v Filesystem

echo ""
echo "=================================="
echo "Cleanup complete!"
echo "=================================="
