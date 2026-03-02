#!/bin/bash
# Clean up old checkpoint files to free disk space
#
# Keeps only:
#   - checkpoint_best.pth (lowest validation loss)
#   - checkpoint_latest.pth (most recent epoch)
#   - checkpoint_final.pth (last epoch)
#
# Removes all checkpoint_epoch_*.pth files

set -e

CHECKPOINT_DIR="${1:-checkpoints}"

if [ ! -d "$CHECKPOINT_DIR" ]; then
    echo "Error: Checkpoint directory not found: $CHECKPOINT_DIR"
    exit 1
fi

echo "Cleaning up checkpoints in: $CHECKPOINT_DIR"
echo ""

# Count old checkpoints
OLD_COUNT=$(find "$CHECKPOINT_DIR" -name "checkpoint_epoch_*.pth" | wc -l)

if [ "$OLD_COUNT" -eq 0 ]; then
    echo "No old checkpoints to clean up."
    exit 0
fi

# Calculate disk space to free
SPACE_BEFORE=$(du -sh "$CHECKPOINT_DIR" | awk '{print $1}')
echo "Current size: $SPACE_BEFORE"
echo "Found $OLD_COUNT epoch checkpoints to remove"
echo ""

# Show what will be removed
echo "Will remove:"
find "$CHECKPOINT_DIR" -name "checkpoint_epoch_*.pth" -exec basename {} \; | head -10
if [ "$OLD_COUNT" -gt 10 ]; then
    echo "... and $((OLD_COUNT - 10)) more"
fi
echo ""

# Ask for confirmation
read -p "Proceed with cleanup? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Remove old checkpoints
echo "Removing old checkpoints..."
find "$CHECKPOINT_DIR" -name "checkpoint_epoch_*.pth" -delete

# Show results
SPACE_AFTER=$(du -sh "$CHECKPOINT_DIR" | awk '{print $1}')
echo ""
echo "Cleanup complete!"
echo "  Before: $SPACE_BEFORE"
echo "  After: $SPACE_AFTER"
echo ""
echo "Kept checkpoints:"
ls -lh "$CHECKPOINT_DIR"/checkpoint_*.pth 2>/dev/null || echo "  (none found)"
