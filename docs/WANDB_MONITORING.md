# Weights & Biases Monitoring for SIAD

Complete guide to training monitoring, experiment tracking, and model artifact management using Weights & Biases (wandb).

## Quick Start

### 1. Setup Wandb Account

```bash
# On your A100 pod
wandb login
# Follow prompt to enter your API key from https://wandb.ai/authorize
```

### 2. Enable Wandb in Training

```bash
# Method 1: Using training launcher (wandb enabled by default)
./scripts/train_a100.sh data/manifest.jsonl

# Method 2: Using train.py directly
uv run python scripts/train.py \
    --manifest data/manifest.jsonl \
    --wandb \
    --wandb-project siad-world-model \
    --wandb-name "my-experiment-name"

# Disable wandb
USE_WANDB=false ./scripts/train_a100.sh data/manifest.jsonl
```

### 3. View Training Dashboard

After training starts, wandb will print a URL like:
```
🚀 View run at https://wandb.ai/your-username/siad-world-model/runs/abc123
```

Open this URL to see real-time training metrics!

## Tracked Metrics

### Training Metrics (logged every 10 steps)

| Metric | Description |
|--------|-------------|
| `train/loss` | Overall JEPA world model loss |
| `train/cosine_distance` | Token-wise cosine distance (main loss component) |
| `train/variance_penalty` | Anti-collapse regularizer |
| `train/grad_norm` | Gradient norm (after clipping) |
| `train/learning_rate` | Current learning rate (cosine schedule) |
| `train/batch_time` | Time per batch (seconds) |
| `train/samples_per_sec` | Training throughput |

### Validation Metrics (logged every epoch)

| Metric | Description |
|--------|-------------|
| `val/loss` | Validation loss |
| `val/cosine_distance` | Validation cosine distance |
| `val/variance_penalty` | Validation variance penalty |

### System Metrics (logged every 10 steps)

| Metric | Description |
|--------|-------------|
| `system/gpu_memory_allocated_gb` | GPU memory in use |
| `system/gpu_memory_reserved_gb` | GPU memory reserved |
| `system/total_training_time_min` | Total elapsed time |

### Epoch Summaries

| Metric | Description |
|--------|-------------|
| `train/epoch_loss` | Average training loss for epoch |
| `train/epoch_time_min` | Time to complete epoch |

### Model Configuration (logged at start)

- Model parameters (total & trainable)
- Hyperparameters (learning rate, weight decay, etc.)
- Dataset sizes (train/val samples)
- Batch size
- Device info

## Gradient & Parameter Tracking

Wandb automatically tracks (via `wandb.watch()`):
- **Gradients**: Distribution and norms for all parameters
- **Parameters**: Weight distributions over time
- **Log frequency**: Every 100 steps

View in dashboard: **System** tab → **Gradients** / **Parameters**

## Model Artifacts

Checkpoints are automatically saved as wandb artifacts:

### Artifact Types

1. **Latest checkpoint** (every 5 epochs)
   - Alias: `latest`
   - Contains: model, optimizer, scheduler states

2. **Best checkpoint** (when validation improves)
   - Alias: `best`
   - Automatically tagged for easy retrieval

3. **Final checkpoint** (end of training)
   - Alias: `latest`
   - Complete training state

### Download Checkpoints

```python
import wandb

# Download best checkpoint
api = wandb.Api()
artifact = api.artifact('your-username/siad-world-model/model-abc123:best')
artifact_dir = artifact.download()
print(f"Downloaded to: {artifact_dir}")

# Load checkpoint
import torch
checkpoint = torch.load(f"{artifact_dir}/checkpoint_best.pth")
```

## Experiment Comparison

### Compare Multiple Runs

1. Go to wandb project: https://wandb.ai/your-username/siad-world-model
2. Select multiple runs (checkboxes)
3. Click **Compare** button

### Useful Comparisons

- **Loss curves**: Which hyperparameters converge faster?
- **Throughput**: Which batch size is most efficient?
- **GPU utilization**: Are you bottlenecked on data loading?
- **Gradient norms**: Is training stable?

## Hyperparameter Sweeps

Run multiple experiments with different hyperparameters:

```yaml
# wandb_sweep.yaml
program: scripts/train.py
method: bayes
metric:
  name: val/loss
  goal: minimize
parameters:
  manifest:
    value: data/manifest.jsonl
  lr:
    min: 0.00001
    max: 0.001
  batch-size:
    values: [16, 32, 64]
  wandb:
    value: true
```

```bash
# Create sweep
wandb sweep wandb_sweep.yaml

# Run sweep agent (prints: wandb agent username/project/sweep_id)
wandb agent username/siad-world-model/sweep_abc123
```

## Custom Logging

Add custom metrics to your training:

```python
import wandb

# Log custom visualization
wandb.log({
    "predictions/example": wandb.Image(prediction_image),
    "rollout/video": wandb.Video(rollout_video),
})

# Log tables
wandb.log({
    "results": wandb.Table(
        columns=["tile_id", "month", "loss"],
        data=[["tile_001", "2023-01", 0.42], ...]
    )
})
```

## Environment Variables

Control wandb behavior:

```bash
# Disable wandb for this run
WANDB_MODE=disabled ./scripts/train_a100.sh

# Change default project
export WANDB_PROJECT=my-custom-project

# Offline mode (sync later with `wandb sync`)
WANDB_MODE=offline ./scripts/train_a100.sh
```

## Best Practices

### 1. Meaningful Run Names

```bash
# Bad: random generated names
uv run python scripts/train.py --wandb

# Good: descriptive names
uv run python scripts/train.py --wandb \
    --wandb-name "baseline-lr1e4-bs32"
```

### 2. Tag Your Experiments

```python
# In your code
wandb.config.update({"tags": ["baseline", "production", "v0.2"]})
```

### 3. Log Representative Samples

Every few epochs, log:
- Input observations (sample GeoTIFFs)
- Predicted rollouts
- Target observations
- Residual heatmaps

This helps debug model behavior visually.

### 4. Monitor System Metrics

Watch for:
- **GPU memory plateau**: You can increase batch size
- **Low GPU utilization**: Data loading bottleneck (increase num_workers)
- **High gradient norms**: Training instability (decrease learning rate)

## Troubleshooting

### Wandb not logging

```bash
# Check wandb is installed
uv pip list | grep wandb

# Verify login
wandb login --relogin

# Check run status
wandb status
```

### Slow dashboard loading

- Reduce log frequency in trainer.py (change `batch_idx % 10` to `% 100`)
- Disable gradient tracking: comment out `wandb.watch()` line

### Offline pod without internet

```bash
# Train in offline mode
WANDB_MODE=offline ./scripts/train_a100.sh

# Later, sync logs
wandb sync wandb/offline-run-*
```

## Metrics Dashboard Layout

Recommended layout in wandb UI:

### Row 1: Loss Curves
- `train/loss` vs `val/loss` (primary metric)
- `train/cosine_distance` vs `val/cosine_distance`

### Row 2: Training Dynamics
- `train/learning_rate` (cosine schedule)
- `train/grad_norm` (stability check)
- `train/samples_per_sec` (throughput)

### Row 3: System Health
- `system/gpu_memory_allocated_gb`
- `train/batch_time`
- `train/epoch_time_min`

### Row 4: Components
- `train/variance_penalty` (anti-collapse)
- Any custom metrics you add

## Example Dashboard

After training completes, your dashboard will show:

1. **Training curves**: Smooth loss decrease from ~0.67 to ~0.15
2. **Learning rate**: Cosine decay from 1e-4 to near zero
3. **Throughput**: ~500-800 samples/sec on A100 80GB
4. **GPU memory**: ~8-10GB for batch_size=32
5. **Best checkpoint**: Automatically tagged at epoch with lowest val loss

## Next Steps

- Set up email/Slack alerts for training completion
- Create custom panels for JEPA-specific metrics
- Use wandb Reports to document experiments
- Share dashboard links with collaborators

For more: https://docs.wandb.ai/
