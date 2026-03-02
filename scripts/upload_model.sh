#!/bin/bash
# Upload SIAD model to HuggingFace Hub
#
# Usage:
#   ./scripts/upload_model.sh checkpoints/checkpoint_best.pth tiny username/siad-tiny
#   ./scripts/upload_model.sh checkpoints/checkpoint_best.pth small username/siad-small

set -e

CHECKPOINT="${1}"
MODEL_SIZE="${2}"
REPO_ID="${3}"

if [ -z "$CHECKPOINT" ] || [ -z "$MODEL_SIZE" ] || [ -z "$REPO_ID" ]; then
    echo "Usage: $0 <checkpoint> <model-size> <repo-id>"
    echo ""
    echo "Arguments:"
    echo "  checkpoint:  Path to checkpoint file (e.g., checkpoints/checkpoint_best.pth)"
    echo "  model-size:  Model size (tiny/small/medium/large/xlarge)"
    echo "  repo-id:     HuggingFace repo ID (username/model-name)"
    echo ""
    echo "Example:"
    echo "  $0 checkpoints/checkpoint_best.pth tiny OzLabs/siad-wm-tiny"
    exit 1
fi

if [ ! -f "$CHECKPOINT" ]; then
    echo "Error: Checkpoint file not found: $CHECKPOINT"
    exit 1
fi

echo "Uploading model to HuggingFace Hub..."
echo "  Checkpoint: $CHECKPOINT"
echo "  Model size: $MODEL_SIZE"
echo "  Repository: $REPO_ID"
echo ""

# Run upload with uv
uv run python scripts/upload_to_hf_new.py \
    --checkpoint "$CHECKPOINT" \
    --model-size "$MODEL_SIZE" \
    --repo-id "$REPO_ID"
