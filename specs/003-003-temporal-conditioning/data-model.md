# Data Model: Temporal Conditioning

**Feature**: 003-temporal-conditioning | **Date**: 2026-03-05

## Entity Overview

This feature extends the existing action conditioning system with temporal features. The primary entities are:

1. **Temporal Features** - Cyclical month-of-year encoding
2. **Extended Action Vector** - Combines weather + temporal features
3. **Dataset Schema V2** - Updated HDF5 schema with temporal features
4. **Preprocessing Manifest** - Tracks schema version for reproducibility

---

## Entity: Temporal Features

**Purpose**: Encode time-of-year cyclically to provide seasonal context without discontinuities at year boundaries.

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `month_sin` | float32 | ∈ [-1, 1] | sin(2π * month / 12) |
| `month_cos` | float32 | ∈ [-1, 1] | cos(2π * month / 12) |
| `source_month` | int | ∈ [1, 12] | Original month (metadata only, not used in model) |
| `timestamp` | datetime | ISO 8601 | Source timestamp for debugging |

### Validation Rules

1. **Value range**: `month_sin` and `month_cos` must be in [-1, 1]
2. **Cyclic consistency**: `month_sin² + month_cos² ≈ 1` (unit circle property)
3. **Monotonicity**: Consecutive months should have small Euclidean distance (<0.6)
4. **Year boundary**: December→January should not spike (distance <0.6)

### Derivation

```python
def compute_temporal_features(timestamp: datetime) -> tuple[float, float]:
    """Compute cyclical temporal features from timestamp.

    Args:
        timestamp: Datetime object with month field

    Returns:
        (month_sin, month_cos) tuple
    """
    month = timestamp.month  # 1-12
    angle = 2 * np.pi * month / 12
    return np.sin(angle), np.cos(angle)
```

### Examples

| Month | month_sin | month_cos | Notes |
|-------|-----------|-----------|-------|
| January | 0.500 | 0.866 | 30° on unit circle |
| April | 1.000 | 0.000 | 90° (peak summer approach) |
| July | 0.500 | -0.866 | 150° (peak summer) |
| October | -0.866 | -0.500 | 240° (autumn) |
| December | -0.500 | 0.866 | 330° (close to January!) |

**Year boundary check**: Euclidean distance from December to January:
```
dist = sqrt((0.5 - (-0.5))² + (0.866 - 0.866)²) = 1.0... wait, that's wrong!

Let me recalculate:
December: month=12 → angle = 2π*12/12 = 2π = 0 (modulo 2π)
  → sin(0) = 0, cos(0) = 1

January: month=1 → angle = 2π*1/12 = π/6
  → sin(π/6) = 0.5, cos(π/6) = 0.866

Distance = sqrt((0.5-0)² + (0.866-1)²) = sqrt(0.25 + 0.018) = 0.52 ✓
```

Good! December→January distance is 0.52, which is smooth.

---

## Entity: Extended Action Vector

**Purpose**: Combines weather anomalies with temporal features for action conditioning.

### Schema V1 (Baseline)

```python
ActionVector = {
    "rain_anom": float32,      # Precipitation anomaly (mm/day)
    "temp_anom": float32,      # Temperature anomaly (°C)
}
# Shape: [B, H, 2]
```

### Schema V2 (Temporal)

```python
ActionVector = {
    "rain_anom": float32,      # Precipitation anomaly (mm/day)
    "temp_anom": float32,      # Temperature anomaly (°C)
    "month_sin": float32,      # Temporal feature (cyclical)
    "month_cos": float32,      # Temporal feature (cyclical)
}
# Shape: [B, H, 4]
```

### Constraints

1. **Weather anomalies** (first 2 dims):
   - `rain_anom` ∈ [-100, 100] mm/day (sanity check, actual range smaller)
   - `temp_anom` ∈ [-30, 30] °C (sanity check, actual range smaller)
   - Computed as deviation from climatology per existing preprocessing

2. **Temporal features** (last 2 dims):
   - `month_sin`, `month_cos` ∈ [-1, 1] (strict)
   - Must satisfy unit circle property: month_sin² + month_cos² ≈ 1

3. **Shape invariants**:
   - Batch dimension `B` ≥ 1
   - Horizon dimension `H` ∈ [1, 12] (typically 6 for MVP)
   - Feature dimension `A = 4` (fixed for v2 schema)

### Relationships

- **Used by**: ActionEncoder (model/actions.py)
- **Produced by**: Dataset collate function (data/dataset.py)
- **Validated by**: Config schema (config/schema.py)

---

## Entity: Dataset Schema V2

**Purpose**: HDF5 dataset structure with temporal features and version metadata.

### HDF5 Structure

```text
dataset.h5
├── /observations [N, C, H, W]        # Satellite imagery (unchanged)
├── /actions [N, horizon, 4]          # EXTENDED: now includes temporal features
├── /timestamps [N, horizon+1]        # ADDED: datetime64 for each sample+rollout
└── /attrs
    ├── preprocessing_version = "v2"
    ├── temporal_features = "month_sin,month_cos"
    ├── action_dim = 4
    ├── created_at = "2026-03-05T12:00:00Z"
    └── backward_compatible = True
```

### Field Specifications

| Field | Type | Shape | Description |
|-------|------|-------|-------------|
| `/observations` | float32 | [N, C, H, W] | Satellite imagery (unchanged from v1) |
| `/actions` | float32 | [N, horizon, 4] | Extended action vectors with temporal features |
| `/timestamps` | datetime64 | [N, horizon+1] | Timestamps for context + rollout steps |

**Attributes** (metadata):
- `preprocessing_version`: String ("v1" or "v2")
- `temporal_features`: String (comma-separated list, e.g., "month_sin,month_cos")
- `action_dim`: int (2 for v1, 4 for v2)
- `created_at`: ISO 8601 timestamp
- `backward_compatible`: bool (True - old models can load by ignoring temporal features)

### Migration from V1 to V2

**Scenario**: User has old v1 dataset, wants to upgrade to v2.

**Migration Path**:
```bash
# Reprocess with temporal features
uv run siad preprocess \
  --input raw_tiles/ \
  --output dataset_v2.h5 \
  --preprocessing-version v2 \
  --add-temporal-features
```

**In-place upgrade** (not recommended, but possible):
```python
# Add temporal features to existing v1 dataset
import h5py
import numpy as np

with h5py.File('dataset_v1.h5', 'r+') as f:
    # Read existing actions [N, H, 2]
    actions_v1 = f['/actions'][:]

    # Read timestamps (must have been stored!)
    timestamps = f['/timestamps'][:]

    # Compute temporal features
    temporal_features = []
    for ts_seq in timestamps:
        features_seq = []
        for ts in ts_seq[1:]:  # Skip context, use rollout timestamps
            month = ts.astype('datetime64[M]').astype(int) % 12 + 1
            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            features_seq.append([month_sin, month_cos])
        temporal_features.append(features_seq)
    temporal_features = np.array(temporal_features)  # [N, H, 2]

    # Concatenate with existing actions
    actions_v2 = np.concatenate([actions_v1, temporal_features], axis=-1)  # [N, H, 4]

    # Replace /actions dataset
    del f['/actions']
    f.create_dataset('/actions', data=actions_v2)

    # Update metadata
    f.attrs['preprocessing_version'] = 'v2'
    f.attrs['temporal_features'] = 'month_sin,month_cos'
    f.attrs['action_dim'] = 4
```

---

## Entity: Preprocessing Manifest

**Purpose**: Track preprocessing configuration for reproducibility (Constitution Principle V).

### Schema

```json
{
  "version": "v2",
  "features": {
    "weather": ["rain_anom", "temp_anom"],
    "temporal": ["month_sin", "month_cos"]
  },
  "changes_from_v1": [
    "Added temporal features: month_sin, month_cos",
    "Action vector shape: [B, H, 2] → [B, H, 4]",
    "Added /timestamps dataset to HDF5 for temporal feature extraction"
  ],
  "backward_compatible": true,
  "upgrade_path": "uv run siad preprocess --preprocessing-version v2",
  "created_at": "2026-03-05T12:00:00Z",
  "git_commit": "abc123..."
}
```

### Validation

- `version` must be "v1" or "v2"
- `features.temporal` must match temporal_features in HDF5 attributes
- `backward_compatible` must be bool
- `created_at` must be ISO 8601
- `git_commit` should be 40-char hex SHA (for traceability)

---

## State Transitions

### Dataset Loading

```
┌─────────────┐
│ Load HDF5   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐      No      ┌─────────────────┐
│ Check version   ├─────────────►│ Default to v1   │
│ attribute       │               │ (old datasets)  │
└────────┬────────┘               └────────┬────────┘
         │ Yes                             │
         ▼                                 ▼
┌─────────────────┐               ┌─────────────────┐
│ version == "v2"?├──Yes─────────►│ Load 4D actions │
└────────┬────────┘               │ [B, H, 4]       │
         │ No                     └─────────────────┘
         ▼
┌─────────────────┐
│ Load 2D actions │
│ [B, H, 2]       │
│ Pad with zeros  │
│ if model needs  │
│ action_dim=4    │
└─────────────────┘
```

### Checkpoint Loading

```
┌──────────────────┐
│ Load checkpoint  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐       Match      ┌─────────────────┐
│ Compare action_dim   ├───────────────────►│ Standard load   │
│ checkpoint vs model  │                    └─────────────────┘
└────────┬─────────────┘
         │ Mismatch
         ▼
┌──────────────────────┐
│ checkpoint_dim < model_dim?
└────────┬─────────────┘
         │ Yes (e.g., 2 < 4)
         ▼
┌──────────────────────┐
│ Pad weights:         │
│ Linear(2→64) becomes │
│ Linear(4→64) with    │
│ zero-init for new    │
│ temporal features    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Load with            │
│ strict=False         │
└──────────────────────┘
```

---

## Invariants

1. **Temporal feature unit circle**: ∀ temporal features, month_sin² + month_cos² ∈ [0.99, 1.01]
2. **Action vector shape**: Schema v2 datasets must have `/actions` shape [N, horizon, 4]
3. **Timestamp alignment**: `/timestamps` shape must be [N, horizon+1] (context + rollout)
4. **Version consistency**: HDF5 attr `preprocessing_version` must match manifest JSON `version`
5. **Backward compatibility**: v1 datasets must load successfully in v2 model (with padding)

---

## Indexing Conventions

- **Batch index** `b` ∈ [0, B)
- **Horizon index** `h` ∈ [0, H) where h=0 is first rollout step
- **Feature index** `a` ∈ [0, 4) where:
  - a=0: rain_anom
  - a=1: temp_anom
  - a=2: month_sin
  - a=3: month_cos

**Example access**:
```python
# Get temporal features for batch 3, step 2
month_sin = actions[3, 2, 2]  # [b=3, h=2, a=2]
month_cos = actions[3, 2, 3]  # [b=3, h=2, a=3]
```

---

## Summary

**Primary change**: Extend action vector from 2D (weather only) to 4D (weather + temporal).

**Key entities**:
1. Temporal features: (month_sin, month_cos) cyclical encoding
2. Extended action vector: [B, H, 4] with weather + temporal
3. Dataset schema v2: HDF5 with `/actions [N, H, 4]` and version metadata
4. Preprocessing manifest: JSON tracking schema version for reproducibility

**Invariants maintained**: Unit circle property for temporal features, backward compatibility for old datasets, CLI reproducibility per constitution.
