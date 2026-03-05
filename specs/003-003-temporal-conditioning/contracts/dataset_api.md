# Dataset API Contract

**Feature**: 003-temporal-conditioning | **Version**: v2

## Purpose

Define the contract for dataset loading with temporal features, ensuring backward compatibility and version-aware behavior.

---

## Contract: Dataset.\_\_getitem\_\_()

### Signature

```python
def __getitem__(self, idx: int) -> dict:
    """Load a single training sample with temporal features.

    Args:
        idx: Sample index in [0, len(dataset))

    Returns:
        Dictionary with:
        - obs_context: [C, H, W] context observation
        - obs_targets: [horizon, C, H, W] rollout target observations
        - actions_rollout: [horizon, A] action sequence (A=4 for v2, A=2 for v1)
        - timestamps: [horizon+1] datetime64 array (v2 only, None for v1)
    """
```

### Input Constraints

- **idx**: int ∈ [0, len(dataset))
- **Precondition**: Dataset file exists and is readable
- **Precondition**: HDF5 file has valid `preprocessing_version` attribute (or defaults to v1)

### Output Guarantees

**Schema V1** (backward compatibility):
```python
{
    "obs_context": np.ndarray,     # shape: [C, H, W], dtype: float32
    "obs_targets": np.ndarray,     # shape: [horizon, C, H, W], dtype: float32
    "actions_rollout": np.ndarray, # shape: [horizon, 2], dtype: float32
    "timestamps": None             # not available in v1
}
```

**Schema V2** (temporal features):
```python
{
    "obs_context": np.ndarray,     # shape: [C, H, W], dtype: float32
    "obs_targets": np.ndarray,     # shape: [horizon, C, H, W], dtype: float32
    "actions_rollout": np.ndarray, # shape: [horizon, 4], dtype: float32
    "timestamps": np.ndarray       # shape: [horizon+1], dtype: datetime64
}
```

### Invariants

1. **Temporal feature validity** (v2 only):
   ```python
   month_sin = actions_rollout[:, 2]
   month_cos = actions_rollout[:, 3]
   assert np.all((month_sin ** 2 + month_cos ** 2) > 0.99)
   assert np.all((month_sin ** 2 + month_cos ** 2) < 1.01)
   ```

2. **Shape consistency**:
   ```python
   assert obs_targets.shape[0] == actions_rollout.shape[0]  # same horizon
   if timestamps is not None:
       assert timestamps.shape[0] == actions_rollout.shape[0] + 1  # context + rollout
   ```

3. **Action dimension**:
   ```python
   if preprocessing_version == "v1":
       assert actions_rollout.shape[1] == 2
   elif preprocessing_version == "v2":
       assert actions_rollout.shape[1] == 4
   ```

### Error Conditions

- **FileNotFoundError**: Dataset file does not exist
- **ValueError**: Invalid preprocessing_version attribute (not "v1" or "v2")
- **KeyError**: Missing required dataset (e.g., /actions, /observations)
- **IndexError**: idx out of range
- **AssertionError**: Temporal feature unit circle violation (debugging only)

---

## Contract: Dataset.collate_fn()

### Purpose

Batch multiple samples into model-ready tensors, padding if necessary.

### Signature

```python
@staticmethod
def collate_fn(batch: List[dict]) -> dict:
    """Collate batch of samples into tensors.

    Args:
        batch: List of dictionaries from __getitem__()

    Returns:
        Dictionary with batched tensors:
        - obs_context: [B, C, H, W]
        - obs_targets: [B, horizon, C, H, W]
        - actions_rollout: [B, horizon, A]  # A=4 for v2, A=2 for v1
        - timestamps: [B, horizon+1] or None
    """
```

### Input Constraints

- **batch**: List of dicts, all with same schema (v1 or v2)
- **len(batch)**: ≥ 1 (non-empty batch)
- **Precondition**: All samples have same action_dim (cannot mix v1 and v2 in same batch)

### Output Guarantees

```python
{
    "obs_context": torch.Tensor,      # [B, C, H, W], dtype: float32
    "obs_targets": torch.Tensor,      # [B, horizon, C, H, W], dtype: float32
    "actions_rollout": torch.Tensor,  # [B, horizon, A], dtype: float32
    "timestamps": np.ndarray or None  # [B, horizon+1], dtype: datetime64
}
```

### Invariants

1. **Batch size**: `B = len(batch)`
2. **Action dimension consistency**:
   ```python
   A = batch[0]["actions_rollout"].shape[1]
   for sample in batch:
       assert sample["actions_rollout"].shape[1] == A
   ```

3. **Temporal features** (if v2):
   ```python
   if A == 4:
       month_sin = actions_rollout[:, :, 2]
       month_cos = actions_rollout[:, :, 3]
       assert torch.all((month_sin ** 2 + month_cos ** 2) > 0.99)
   ```

### Error Conditions

- **ValueError**: Mixed v1/v2 samples in same batch (inconsistent action_dim)
- **RuntimeError**: Tensor shape mismatch during stacking

---

## Contract: compute_temporal_features()

### Purpose

Compute cyclical temporal features from timestamp.

### Signature

```python
def compute_temporal_features(timestamp: datetime) -> tuple[float, float]:
    """Compute (month_sin, month_cos) from timestamp.

    Args:
        timestamp: datetime object with month field

    Returns:
        (month_sin, month_cos) tuple, each ∈ [-1, 1]
    """
```

### Input Constraints

- **timestamp**: datetime or datetime64 with valid month field
- **Precondition**: timestamp.month ∈ [1, 12]

### Output Guarantees

```python
month_sin, month_cos = compute_temporal_features(timestamp)

# Range constraints
assert -1 <= month_sin <= 1
assert -1 <= month_cos <= 1

# Unit circle property
assert 0.99 <= (month_sin ** 2 + month_cos ** 2) <= 1.01
```

### Derivation

```python
month = timestamp.month  # 1-12
angle = 2 * np.pi * month / 12
month_sin = np.sin(angle)
month_cos = np.cos(angle)
return month_sin, month_cos
```

### Error Conditions

- **AttributeError**: timestamp does not have month attribute
- **ValueError**: timestamp.month not in [1, 12]

---

## Backward Compatibility Guarantees

### V1 Datasets in V2 Loader

**Scenario**: User loads old v1 dataset (action_dim=2) in v2 codebase.

**Guarantee**: Dataset loads successfully, returns action_dim=2.

**Behavior**:
```python
# In __getitem__()
preprocessing_version = f.attrs.get('preprocessing_version', 'v1')  # default v1
if preprocessing_version == 'v1':
    actions = f['/actions'][idx]  # [horizon, 2]
    timestamps = None  # not available in v1
elif preprocessing_version == 'v2':
    actions = f['/actions'][idx]  # [horizon, 4]
    timestamps = f['/timestamps'][idx]
```

**Model Handling**: If model expects action_dim=4 but dataset provides action_dim=2, model's checkpoint loading handles padding (see checkpoint_api.md).

### V2 Datasets in V1 Loader

**Scenario**: User accidentally loads v2 dataset in old v1 codebase.

**Guarantee**: Fails fast with clear error message.

**Behavior**:
```python
# Old v1 loader expects action_dim=2 hardcoded
actions = f['/actions'][idx]  # [horizon, 4]
assert actions.shape[1] == 2, f"Expected action_dim=2, got {actions.shape[1]}"
# → AssertionError: Expected action_dim=2, got 4
```

**Error Message** (recommended):
```
ValueError: Dataset preprocessing version 'v2' is not compatible with this model version.
Please upgrade model to support temporal features, or reprocess dataset with --preprocessing-version=v1
```

---

## Testing Contract

### Unit Tests Required

1. **test_v1_dataset_loading**: Load v1 dataset, verify action_dim=2, timestamps=None
2. **test_v2_dataset_loading**: Load v2 dataset, verify action_dim=4, temporal feature validity
3. **test_temporal_feature_computation**: Verify sin²+cos²≈1 for all months
4. **test_year_boundary**: Verify Dec→Jan distance < 0.6
5. **test_collate_batch_consistency**: Verify batched actions match individual samples
6. **test_mixed_version_error**: Verify error when mixing v1/v2 in same batch

### Integration Tests Required

1. **test_full_training_loop_v2**: Train for 10 steps with v2 dataset, verify no errors
2. **test_backward_compat_checkpoint_v1_data**: Load v1 data + v2 checkpoint (padded)
3. **test_ablation_v1_vs_v2**: Compare baseline (v1) vs temporal (v2) on same data

---

## Summary

**Key Contracts**:
1. `__getitem__()`: Version-aware loading, returns dict with action_dim ∈ {2, 4}
2. `collate_fn()`: Batches samples, enforces action_dim consistency
3. `compute_temporal_features()`: Deterministic sin/cos from timestamp, unit circle property

**Backward Compatibility**: V1 datasets load in V2 code (action_dim=2 with timestamps=None). V2 datasets fail fast in V1 code with clear error.

**Testing**: 6 unit tests + 3 integration tests required.
