#!/bin/bash
# Training preset configurations for SIAD
# Usage: source scripts/train_presets.sh && train_quick data/manifest.jsonl

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Quick test training - for rapid iteration and debugging
train_quick() {
    echo "Running QUICK TEST training (10 epochs)..."
    EPOCHS=10 \
    BATCH_SIZE=32 \
    USE_WANDB=false \
    "${SCRIPT_DIR}/train_a100.sh" "$@"
}

# Standard training - balanced speed/quality for development
train_standard() {
    echo "Running STANDARD training (50 epochs)..."
    EPOCHS=50 \
    BATCH_SIZE=32 \
    "${SCRIPT_DIR}/train_a100.sh" "$@"
}

# Production training - high quality for final models
train_production() {
    echo "Running PRODUCTION training (100 epochs)..."
    EPOCHS=100 \
    BATCH_SIZE=32 \
    "${SCRIPT_DIR}/train_a100.sh" "$@"
}

# Long training - maximum quality, extended convergence
train_long() {
    echo "Running LONG training (200 epochs)..."
    EPOCHS=200 \
    BATCH_SIZE=32 \
    "${SCRIPT_DIR}/train_a100.sh" "$@"
}

# Large batch training - for A100 80GB with lots of headroom
train_large_batch() {
    echo "Running LARGE BATCH training (50 epochs, batch=64)..."
    EPOCHS=50 \
    BATCH_SIZE=64 \
    "${SCRIPT_DIR}/train_a100.sh" "$@"
}

# Small model quick test - tiny model for rapid prototyping
train_tiny() {
    echo "Running TINY MODEL quick test (10 epochs)..."
    EPOCHS=10 \
    MODEL_SIZE=tiny \
    BATCH_SIZE=64 \
    USE_WANDB=false \
    "${SCRIPT_DIR}/train_a100.sh" "$@"
}

# Help message
train_help() {
    cat << EOF
SIAD Training Presets
=====================

Available preset configurations:

  train_quick          Quick test (10 epochs, no wandb)
                       Use for: Rapid iteration, debugging, code validation
                       Time: ~2-3 minutes

  train_standard       Standard training (50 epochs)
                       Use for: Development, baseline experiments
                       Time: ~12-15 minutes

  train_production     Production training (100 epochs)
                       Use for: Final models, publication results
                       Time: ~25-30 minutes

  train_long           Long training (200 epochs)
                       Use for: Maximum quality, extended convergence
                       Time: ~50-60 minutes

  train_large_batch    Large batch (50 epochs, batch=64)
                       Use for: Faster training on A100 80GB
                       Time: ~8-10 minutes

  train_tiny           Tiny model quick test (10 epochs, tiny model)
                       Use for: Ultra-fast prototyping
                       Time: ~1 minute

Usage:
  # Source this file to load functions
  source scripts/train_presets.sh

  # Run a preset
  train_quick data/manifest.jsonl
  train_production data/manifest.jsonl

  # Or use environment variables directly
  EPOCHS=150 ./scripts/train_a100.sh data/manifest.jsonl

Custom Configuration:
  Override any setting by setting environment variables before the preset:

  WANDB_PROJECT=my-experiment train_production data/manifest.jsonl
  LR=5e-5 BATCH_SIZE=48 train_standard data/manifest.jsonl

Available Environment Variables:
  EPOCHS           Number of training epochs (default: 50)
  BATCH_SIZE       Batch size (default: 32)
  MODEL_SIZE       Model size: tiny/small/medium/large/xlarge (default: tiny)
  LR               Learning rate (default: 1e-4)
  NUM_WORKERS      DataLoader workers (default: 16)
  USE_WANDB        Enable Weights & Biases: true/false (default: true)
  WANDB_PROJECT    Wandb project name (default: siad-world-model)

EOF
}

# If script is executed directly (not sourced), show help
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    train_help
fi
