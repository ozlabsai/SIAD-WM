# SIAD Experiment Runner Guide

High-level experiment runner for running comprehensive training experiments with different model sizes, context lengths, and hyperparameters.

## Quick Start

```bash
# Run baseline validation
uv run scripts/run_experiments.py --suite baseline

# Run model scaling experiments
uv run scripts/run_experiments.py --suite scaling

# Run temporal context experiments
uv run scripts/run_experiments.py --suite temporal

# Resume interrupted experiments
uv run scripts/run_experiments.py --suite scaling --resume

# Preview commands without running
uv run scripts/run_experiments.py --suite baseline --dry-run
```

## Available Experiment Suites

### 1. Baseline
**Purpose**: Validate current working configuration
**Duration**: ~9 minutes
**Experiments**: 1

Runs a single experiment with the current baseline configuration (tiny model, single-month context, 50 epochs). Use this to verify your setup works before running larger experiments.

```bash
uv run scripts/run_experiments.py --suite baseline --manifest data/manifest.jsonl
```

### 2. Scaling
**Purpose**: Compare model capacity scaling
**Duration**: ~74 minutes (~1.2 hours)
**Experiments**: 3

Tests three model sizes (tiny, small, medium) with identical training settings to understand how model capacity affects performance.

```bash
uv run scripts/run_experiments.py --suite scaling --manifest data/manifest.jsonl
```

**What it tests**:
- Tiny (54M params): 9 min, 1GB VRAM
- Small (150M params): 20 min, 3GB VRAM
- Medium (400M params): 45 min, 8GB VRAM

**Expected results**:
- Larger models should achieve lower validation loss
- Diminishing returns as model size increases
- Memory usage scales with model size

### 3. Temporal
**Purpose**: Compare temporal context lengths
**Duration**: ~157 minutes (~2.6 hours)
**Experiments**: 3

Tests different context lengths (1, 3, 6 months) to understand how temporal context affects prediction quality.

```bash
uv run scripts/run_experiments.py --suite temporal --manifest data/manifest.jsonl
```

**What it tests**:
- 1-month context: Baseline
- 3-month context: Moderate history
- 6-month context: Full seasonal history

**Expected results**:
- Longer context should improve seasonal pattern prediction
- Memory usage increases with context length
- Training time increases 25% per additional context month

### 4. Production
**Purpose**: Production-quality training
**Duration**: ~180 minutes (~3 hours)
**Experiments**: 1

Trains a medium model with 3-month context for 100 epochs using production-quality hyperparameters.

```bash
uv run scripts/run_experiments.py --suite production --manifest data/manifest.jsonl
```

**Configuration**:
- Model: medium (400M params)
- Context: 3 months
- Epochs: 100
- Learning rate: 5e-5 (lower for longer training)

**Use case**: Final model for deployment or evaluation

### 5. Ablation
**Purpose**: Systematic hyperparameter sweep
**Duration**: ~360 minutes (~6 hours)
**Experiments**: 9

Comprehensive ablation study testing:
- Learning rates: 5e-4, 1e-4, 5e-5
- Batch sizes: 16, 32, 64
- Context lengths: 1, 3, 6
- Epoch counts: 50, 100, 200

```bash
uv run scripts/run_experiments.py --suite ablation --manifest data/manifest.jsonl
```

**Use case**: Understanding hyperparameter sensitivity and finding optimal settings

### 6. Quick Test
**Purpose**: Fast debugging iteration
**Duration**: ~2 minutes
**Experiments**: 1

Minimal 10-epoch run for testing changes to training code or data pipeline.

```bash
uv run scripts/run_experiments.py --suite quick_test --manifest data/manifest.jsonl
```

### 7. Full Sweep
**Purpose**: Comprehensive grid search
**Duration**: ~1500 minutes (~25 hours)
**Experiments**: 14

**WARNING**: Very long runtime! Only run if you need exhaustive coverage.

Full grid across:
- All model sizes (tiny, small, medium)
- All context lengths (1, 3, 6)
- All epoch counts (50, 100, 200)

```bash
# Not recommended unless you have time and compute budget
uv run scripts/run_experiments.py --suite full_sweep --manifest data/manifest.jsonl
```

## Advanced Features

### Resume Interrupted Experiments

If experiments are interrupted (power outage, manual stop, etc.), use `--resume` to skip already-completed experiments:

```bash
uv run scripts/run_experiments.py --suite scaling --resume
```

**How it works**:
- Checks for `checkpoint_final.pth` in each experiment's checkpoint directory
- Skips experiments that already have a final checkpoint
- Continues with remaining experiments

**State tracking**:
- Experiment state saved to `experiment_results/experiment_state.json`
- Tracks completed, failed, and in-progress experiments
- Safe to interrupt and resume at any time

### Custom Experiment Configs

Create your own experiment configuration YAML:

```yaml
# my_experiments.yaml
my_custom_suite:
  description: "Custom experiment suite"
  total_estimated_time_minutes: 120
  experiments:
    - name: "custom_1"
      model_size: medium
      context_length: 3
      batch_size: 20
      epochs: 75
      learning_rate: 7.5e-5
      num_workers: 16
      wandb_project: my-project

    - name: "custom_2"
      model_size: large
      context_length: 6
      batch_size: 12
      epochs: 100
      learning_rate: 5e-5
      num_workers: 16
      wandb_project: my-project
```

Run with:
```bash
uv run scripts/run_experiments.py --config my_experiments.yaml --manifest data/manifest.jsonl
```

### Parallel Execution (TODO)

**Note**: Parallel execution not yet implemented. Will fall back to sequential.

Future feature for running experiments in parallel across multiple GPUs:

```bash
# Will be supported in future version
uv run scripts/run_experiments.py --suite scaling --parallel --gpus 0,1,2,3
```

## Results and Tracking

### Weights & Biases

All experiments automatically log to Weights & Biases with:
- Unique experiment names including timestamp
- Suite-specific project names (e.g., `siad-scaling`, `siad-temporal`)
- Full hyperparameter tracking
- Real-time metrics (loss, gradients, GPU usage)

**Project naming**:
- Baseline: `siad-baseline`
- Scaling: `siad-scaling`
- Temporal: `siad-temporal`
- Production: `siad-production`
- Ablation: `siad-ablation`

### Local Results

Experiment results saved to `experiment_results/`:

```
experiment_results/
├── experiment_state.json    # Resume state
└── results.json             # Final results summary
```

**results.json structure**:
```json
{
  "timestamp": "2026-03-02T10:30:00",
  "total_experiments": 3,
  "successful": 2,
  "failed": 1,
  "skipped": 0,
  "experiments": [
    {
      "name": "tiny_ctx1_e50_bs32_20260302_103000",
      "status": "success",
      "elapsed_minutes": 9.2,
      "config": {...}
    }
  ]
}
```

### Checkpoints

Each experiment saves checkpoints to:
```
checkpoints/<experiment_name>/
├── checkpoint_best.pth      # Best validation loss
├── checkpoint_latest.pth    # Latest epoch (rolling)
└── checkpoint_final.pth     # Final epoch
```

**Checkpoint naming**:
```
<model_size>_ctx<context>_e<epochs>_bs<batch_size>_<timestamp>/
```

Example: `medium_ctx3_e100_bs20_20260302_103000/`

## Time Estimates

All times assume A100 GPU. Scale proportionally for other GPUs:
- V100: ~1.5x longer
- RTX 3090: ~2x longer
- T4: ~3x longer

### Per-Suite Estimates (A100)

| Suite | Experiments | Time | Notes |
|-------|-------------|------|-------|
| baseline | 1 | 9 min | Quick validation |
| scaling | 3 | 74 min | Model capacity |
| temporal | 3 | 157 min | Context length |
| production | 1 | 180 min | Best config, 100 epochs |
| ablation | 9 | 360 min | Comprehensive sweep |
| quick_test | 1 | 2 min | Fast debugging |
| full_sweep | 14 | 1500 min | Exhaustive (25 hrs) |

### Per-Model Estimates (50 epochs, context=1)

| Model Size | Params | VRAM | Time |
|------------|--------|------|------|
| tiny | 54M | ~1GB | 9 min |
| small | 150M | ~3GB | 20 min |
| medium | 400M | ~8GB | 45 min |
| large | 1.2B | ~20GB | 120 min |
| xlarge | 3B+ | ~40GB | 360 min |

### Context Length Scaling

Context length increases training time by ~25% per additional month:
- Context=1: 1.0x base time
- Context=3: 1.5x base time
- Context=6: 2.25x base time

Example: Medium model with context=6 takes ~101 min vs 45 min for context=1

## Best Practices

### 1. Start Small
```bash
# Always start with baseline to validate setup
uv run scripts/run_experiments.py --suite baseline

# Then run quick_test to verify changes
uv run scripts/run_experiments.py --suite quick_test
```

### 2. Use Resume for Long Runs
```bash
# For long experiments, use --resume in case of interruption
uv run scripts/run_experiments.py --suite ablation --resume
```

### 3. Preview Before Running
```bash
# Use --dry-run to see what will be executed
uv run scripts/run_experiments.py --suite scaling --dry-run
```

### 4. Monitor with Wandb
Check Weights & Biases dashboard during training:
- Loss curves across experiments
- Comparative metrics
- GPU utilization

### 5. Organize Checkpoints
Checkpoints can consume significant disk space. Clean up after experiments:
```bash
# Keep only best checkpoints
find checkpoints -name "checkpoint_latest.pth" -delete
```

## Troubleshooting

### Out of Memory (OOM)

If you get CUDA OOM errors:

1. Reduce batch size in experiment config
2. Use smaller model size
3. Reduce context length
4. Enable gradient checkpointing (not yet implemented)

**Quick fix**: Edit `configs/experiments.yaml` and reduce batch_size by half

### Experiment Hangs

If training appears to hang:

1. Check GPU usage: `nvidia-smi`
2. Check wandb logs for last update
3. Kill process and use `--resume` to continue

### Disk Space

Each checkpoint is ~400MB-2GB depending on model size.

**Space needed per suite**:
- baseline: ~500MB
- scaling: ~4GB (3 models)
- temporal: ~4GB (3 models)
- ablation: ~12GB (9 models)

**Cleanup**:
```bash
# Remove all latest checkpoints (keep only best and final)
uv run scripts/cleanup_checkpoints.sh
```

### Wandb Issues

If wandb login fails:
```bash
wandb login
```

To disable wandb (not recommended):
- Edit experiment config and remove `wandb_project` field
- Or modify `scripts/train.py` to remove `--wandb` flag

## Example Workflows

### Workflow 1: Quick Validation
```bash
# 1. Validate baseline works (9 min)
uv run scripts/run_experiments.py --suite baseline

# 2. Test scaling with small models (29 min)
uv run scripts/run_experiments.py --suite scaling

# 3. If successful, run production config (180 min)
uv run scripts/run_experiments.py --suite production
```

### Workflow 2: Comprehensive Research
```bash
# 1. Quick test to validate (2 min)
uv run scripts/run_experiments.py --suite quick_test

# 2. Model scaling analysis (74 min)
uv run scripts/run_experiments.py --suite scaling

# 3. Temporal context analysis (157 min)
uv run scripts/run_experiments.py --suite temporal

# 4. Hyperparameter ablation (360 min)
uv run scripts/run_experiments.py --suite ablation

# 5. Final production run with best config (180 min)
uv run scripts/run_experiments.py --suite production
```

### Workflow 3: Iterative Development
```bash
# While developing new features:
uv run scripts/run_experiments.py --suite quick_test

# Once stable, validate with baseline:
uv run scripts/run_experiments.py --suite baseline

# Before merging, run full validation:
uv run scripts/run_experiments.py --suite scaling
```

## Configuration Reference

### Experiment Config Schema

```yaml
suite_name:
  description: "Human-readable description"
  total_estimated_time_minutes: 120
  experiments:
    - name: "experiment_identifier"          # Optional, auto-generated if omitted
      model_size: tiny|small|medium|large    # Required
      context_length: 1|3|6                  # Required
      batch_size: 16|20|24|32|64             # Required
      epochs: 10|50|100|200                  # Required
      learning_rate: 5e-5|1e-4|5e-4          # Required
      num_workers: 16                        # Optional, default: 16
      wandb_project: project-name            # Required for tracking
```

### Command Line Options

```
Required (one of):
  --suite SUITE        Predefined suite (baseline, scaling, temporal, etc.)
  --config CONFIG      Custom YAML config file

Optional:
  --manifest PATH      Path to manifest.jsonl (default: data/manifest.jsonl)
  --data-root PATH     Root directory for data files
  --checkpoint-dir DIR Base checkpoint directory (default: checkpoints)
  --resume             Skip completed experiments
  --dry-run            Preview commands without running
  --parallel           Run in parallel (not yet implemented)
  --gpus IDS           GPU IDs for parallel execution (e.g., "0,1,2,3")
```

## Integration with Existing Tools

### With evaluate_model.py

After experiments complete, evaluate best checkpoints:

```bash
# Run experiments
uv run scripts/run_experiments.py --suite scaling

# Evaluate best checkpoint from medium model
uv run scripts/evaluate_model.py \
  --checkpoint checkpoints/medium_ctx1_e50_bs24_*/checkpoint_best.pth \
  --manifest data/manifest.jsonl
```

### With upload_to_hf.py

Upload best production model to Hugging Face:

```bash
# Train production model
uv run scripts/run_experiments.py --suite production

# Upload to HF Hub
uv run scripts/upload_to_hf.py \
  --checkpoint checkpoints/medium_ctx3_e100_bs20_*/checkpoint_best.pth \
  --model-size medium \
  --repo-name myorg/siad-medium-production
```

### With visualize_predictions.py

Visualize predictions from experiment checkpoints:

```bash
uv run scripts/visualize_predictions.py \
  --checkpoint checkpoints/medium_ctx3_e100_bs20_*/checkpoint_best.pth \
  --manifest data/manifest.jsonl \
  --output-dir viz/production
```

## Next Steps

1. **Run baseline**: Validate your setup works
2. **Run scaling**: Understand model capacity vs performance
3. **Run temporal**: Find optimal context length
4. **Run ablation**: Tune hyperparameters
5. **Run production**: Train final deployment model

Happy experimenting!
