# Quickstart: Temporal Conditioning

**Feature**: 003-temporal-conditioning | **Goal**: Add seasonal context to world model in 30 minutes

## Prerequisites

- Existing SIAD installation with UV (`uv --version`)
- Dataset with timestamp metadata (v1 or new)
- Git branch: `003-003-temporal-conditioning`

---

## Step 1: Update Configuration (2 minutes)

Create new training config with temporal features enabled:

```bash
# Copy baseline config
cp configs/train-baseline.yaml configs/train-temporal-v2.yaml
```

Edit `configs/train-temporal-v2.yaml`:

```yaml
# Model configuration
model:
  encoder:
    in_channels: 8
    latent_dim: 512
  transition:
    latent_dim: 512
    action_dim: 4  # CHANGED FROM 2 → temporal features enabled
    hidden_dim: 64
    num_blocks: 4

# Loss configuration
train:
  loss:
    type: cosine
    anti_collapse:
      gamma: 1.0
      alpha: 25.0

# Dataset configuration
data:
  dataset_path: dataset_v2.h5  # or dataset_v1.h5 (backward compatible)
  preprocessing_version: v2     # NEW: enable temporal feature extraction
  batch_size: 8
  num_workers: 4

# Metadata
version: v2
created: 2026-03-05
```

**Key changes**:
- `model.transition.action_dim: 2 → 4`
- `data.preprocessing_version: v2`

---

## Step 2: Preprocess Data with Temporal Features (10 minutes)

### Option A: Reprocess from Raw Tiles (Recommended)

```bash
# Preprocess with temporal features
uv run siad preprocess \
  --input raw_tiles/ \
  --output dataset_v2.h5 \
  --preprocessing-version v2 \
  --horizon 6 \
  --verbose

# Output:
# Processing 1000 tiles...
# Extracting temporal features (month_sin/cos)...
# [██████████████████] 100% | ETA: 00:00
# Saved to dataset_v2.h5 (preprocessing_version='v2')
```

**What this does**:
- Extracts month from timestamps for each sample
- Computes `month_sin = sin(2π*month/12)`, `month_cos = cos(2π*month/12)`
- Adds temporal features to action vectors: [B, H, 2] → [B, H, 4]
- Sets HDF5 attribute `preprocessing_version='v2'`

### Option B: Upgrade Existing V1 Dataset (Quick Test)

```python
# Quick upgrade script (for testing only)
import h5py
import numpy as np

with h5py.File('dataset_v1.h5', 'r') as f_old, \
     h5py.File('dataset_v2.h5', 'w') as f_new:

    # Copy observations (unchanged)
    f_new.create_dataset('/observations', data=f_old['/observations'][:])

    # Read old actions [N, H, 2]
    actions_v1 = f_old['/actions'][:]
    timestamps = f_old['/timestamps'][:]

    # Compute temporal features [N, H, 2]
    temporal = []
    for ts_seq in timestamps:
        temp_seq = []
        for ts in ts_seq[1:]:  # Skip context
            month = ts.astype('datetime64[M]').astype(int) % 12 + 1
            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            temp_seq.append([month_sin, month_cos])
        temporal.append(temp_seq)
    temporal = np.array(temporal, dtype=np.float32)

    # Concatenate [N, H, 4]
    actions_v2 = np.concatenate([actions_v1, temporal], axis=-1)
    f_new.create_dataset('/actions', data=actions_v2)

    # Copy timestamps
    f_new.create_dataset('/timestamps', data=timestamps)

    # Set v2 metadata
    f_new.attrs['preprocessing_version'] = 'v2'
    f_new.attrs['action_dim'] = 4
```

Run: `uv run python upgrade_dataset.py`

---

## Step 3: Train Model with Temporal Features (15 minutes)

### Option A: Train from Scratch (Ablation Test)

```bash
# Baseline model (no temporal features)
uv run siad train \
  --config configs/train-baseline.yaml \
  --output checkpoints/baseline_v1.pth \
  --epochs 50

# Temporal model (with temporal features)
uv run siad train \
  --config configs/train-temporal-v2.yaml \
  --output checkpoints/temporal_v2.pth \
  --epochs 50 \
  --wandb-project siad-temporal-ablation
```

**Expected outcome**:
- Baseline: ~10 min/epoch
- Temporal: ~10 min/epoch (<5% overhead)
- Final loss: Temporal ≤ Baseline (seasonal context helps)

### Option B: Upgrade Existing V1 Checkpoint (Continue Training)

```bash
# Load v1 checkpoint, train with v2 data
uv run siad train \
  --config configs/train-temporal-v2.yaml \
  --resume checkpoints/baseline_v1.pth \
  --output checkpoints/temporal_v2_finetuned.pth \
  --epochs 10

# Output:
# [ActionEncoder] Upgraded checkpoint: 2→4 dims (temporal features zero-initialized)
# Epoch 1/10: loss=0.234 (temporal weights learning...)
# ...
```

**What happens**:
- Old checkpoint loads successfully
- Temporal feature weights start from zero (neutral)
- After ~1 epoch, temporal weights learn to use seasonal context
- Loss should decrease compared to v1 baseline

---

## Step 4: Validate Temporal Features (3 minutes)

### Check Dataset

```python
# Verify temporal features in dataset
import h5py

with h5py.File('dataset_v2.h5', 'r') as f:
    print(f"Version: {f.attrs['preprocessing_version']}")  # v2
    print(f"Action dim: {f.attrs['action_dim']}")           # 4

    actions = f['/actions'][0, :, :]  # [H, 4]
    print("Sample actions:")
    print(f"  Rain anom: {actions[:, 0]}")
    print(f"  Temp anom: {actions[:, 1]}")
    print(f"  Month sin: {actions[:, 2]}")  # Should be in [-1, 1]
    print(f"  Month cos: {actions[:, 3]}")  # Should be in [-1, 1]

    # Check unit circle property
    month_sin_sq = actions[:, 2] ** 2
    month_cos_sq = actions[:, 3] ** 2
    unit_circle = month_sin_sq + month_cos_sq
    print(f"  Unit circle check: {unit_circle}")  # Should be ~1.0
```

Expected output:
```
Version: v2
Action dim: 4
Sample actions:
  Rain anom: [ 2.3, -1.1,  0.5, ...]
  Temp anom: [-0.8,  1.2, -0.3, ...]
  Month sin: [ 0.50,  0.87,  1.00, ...]
  Month cos: [ 0.87,  0.50,  0.00, ...]
  Unit circle check: [1.0, 1.0, 1.0, ...]
```

### Check Model

```python
# Verify model action_dim
import torch
from siad.model import WorldModel

model = WorldModel.from_config('configs/train-temporal-v2.yaml')
print(f"Action encoder input dim: {model.action_encoder.action_dim}")  # 4

# Test forward pass
batch = torch.randn(8, 6, 4)  # [B, H, 4]
z0 = torch.randn(8, 256, 512)
z_pred = model.rollout(z0, batch, H=6)
print(f"Rollout output shape: {z_pred.shape}")  # [8, 6, 256, 512]
```

---

## Step 5: Run Seasonal Stability Test (Optional, 5 minutes)

Compare baseline vs temporal on seasonal transitions:

```bash
# Evaluate on summer→autumn transitions
uv run siad eval \
  --model checkpoints/baseline_v1.pth \
  --dataset test_seasonal_transitions.h5 \
  --output results/baseline_seasonal.json

uv run siad eval \
  --model checkpoints/temporal_v2.pth \
  --dataset test_seasonal_transitions.h5 \
  --output results/temporal_seasonal.json

# Compare residuals
uv run python scripts/compare_seasonal_residuals.py \
  --baseline results/baseline_seasonal.json \
  --temporal results/temporal_seasonal.json
```

Expected output:
```
Seasonal Stability Comparison:
  Baseline mean residual: 0.45 ± 0.12
  Temporal mean residual: 0.36 ± 0.08  (↓20% reduction)

  False anomaly rate:
    Baseline: 15.2%
    Temporal: 12.1%  (↓20% reduction)

  p-value (t-test): 0.003  (statistically significant)
```

---

## Common Issues & Solutions

### Issue: "Dataset has action_dim=2 but model expects action_dim=4"

**Cause**: Using v1 dataset with v2 model config.

**Solution**:
```bash
# Option 1: Reprocess dataset with v2
uv run siad preprocess --preprocessing-version v2 ...

# Option 2: Use backward-compatible loading (model handles padding)
# No action needed - model auto-pads v1 data to v2
```

### Issue: "Cannot load checkpoint with action_dim=4 into model with action_dim=2"

**Cause**: Trying to load v2 checkpoint in old v1 model.

**Solution**:
```yaml
# Update model config to support v2
model:
  transition:
    action_dim: 4  # Was 2
```

### Issue: "Temporal features are all zeros"

**Cause**: Dataset preprocessing didn't extract timestamps correctly.

**Debug**:
```python
import h5py
with h5py.File('dataset_v2.h5', 'r') as f:
    timestamps = f['/timestamps'][0]
    print(timestamps)  # Should be datetime64, not NaT or zeros
```

**Solution**: Re-run preprocessing with `--verbose` to debug timestamp extraction.

### Issue: "Training loss not improving with temporal features"

**Cause**: Model may need more epochs to learn temporal patterns, or temporal features may not help for your AOI (e.g., equatorial regions with minimal seasonality).

**Debug**:
```python
# Check if temporal weights are learning
model = torch.load('checkpoint.pth')
temporal_weights = model['action_encoder.mlp.0.weight'][:, 2:4]
print(f"Temporal weight mean: {temporal_weights.mean()}")
print(f"Temporal weight std: {temporal_weights.std()}")

# If mean ≈ 0 and std ≈ 0 after 10+ epochs, temporal features may not help
```

---

## Success Criteria Checklist

- [ ] Dataset has `preprocessing_version='v2'` attribute
- [ ] Actions have shape [B, H, 4] with valid month_sin/cos values
- [ ] Model config has `action_dim=4`
- [ ] Training runs without errors
- [ ] Old v1 checkpoints load successfully (with upgrade message)
- [ ] Temporal model achieves ≤baseline loss on validation set
- [ ] Seasonal stability test shows ≥10% reduction in residuals

---

## Next Steps

After completing quickstart:

1. **Ablation study**: Compare v1 vs v2 on full test set (see `integration/test_seasonal_stability.py`)
2. **Hyperparameter tuning**: Adjust action encoder hidden_dim if needed
3. **Production deployment**: Use v2 model for inference with `preprocessing_version='v2'`
4. **Monitor metrics**: Track `ac/std_mean`, `ema/tau` in Weights & Biases for training stability

---

## Summary

**30-minute workflow**:
1. Update config: `action_dim: 4`, `preprocessing_version: v2` (2 min)
2. Preprocess data: `uv run siad preprocess --preprocessing-version v2` (10 min)
3. Train model: `uv run siad train --config train-temporal-v2.yaml` (15 min)
4. Validate: Check dataset + model shapes (3 min)

**Expected improvements**:
- ↓20% reduction in false anomalies during seasonal transitions
- ↓10% reduction in rollout error at step 6
- <5% increase in training time (negligible overhead)

**Backward compatibility**:
- Old v1 datasets work with v2 model (auto-padded to action_dim=4)
- Old v1 checkpoints work with v2 model (zero-initialized temporal weights)
