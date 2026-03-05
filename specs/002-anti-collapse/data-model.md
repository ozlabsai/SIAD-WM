# Data Model: Anti-Collapse Training Stability

**Feature**: 002-anti-collapse | **Date**: 2026-03-04

## Overview

This feature does not introduce new data entities but modifies existing training data structures and adds configuration schema for anti-collapse mechanisms.

## Configuration Schema

### AntiCollapseConfig

**Description**: Configuration for VC-Reg anti-collapse regularization

**Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `str` | Yes | `"vcreg"` | Anti-collapse method (currently only "vcreg") |
| `gamma` | `float` | No | `1.0` | Variance floor threshold (target std per dimension) |
| `alpha` | `float` | No | `25.0` | Variance loss weight |
| `beta` | `float` | No | `1.0` | Covariance loss weight |
| `lambda` | `float` | No | `1.0` | Total anti-collapse loss weight |
| `apply_to` | `List[str]` | No | `["z_t"]` | Where to apply: `["z_t"]` or `["z_t", "z_pred_1"]` |

**Validation Rules**:
- `type` must be `"vcreg"` (only supported method)
- `gamma > 0` (variance floor must be positive)
- `alpha >= 0` and `beta >= 0` (weights must be non-negative)
- `lambda >= 0` (total weight must be non-negative)
- `apply_to` must be non-empty list containing valid targets

**Example YAML**:
```yaml
train:
  loss:
    anti_collapse:
      type: "vcreg"
      gamma: 1.0
      alpha: 25.0
      beta: 1.0
      lambda: 1.0
      apply_to: ["z_t"]
```

### EMAConfig (Enhanced)

**Description**: EMA target encoder configuration (existing structure with enhanced validation)

**Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tau_start` | `float` | No | `0.99` | Initial EMA coefficient |
| `tau_end` | `float` | No | `0.995` | Final EMA coefficient after warmup |
| `warmup_steps` | `int` | No | `2000` | Number of steps to ramp from tau_start to tau_end |

**Validation Rules** (NEW):
- `0 < tau_start <= tau_end < 1.0` (tau must be monotonic and in valid range)
- `warmup_steps > 0` (must have positive warmup period)
- `tau_start` should typically be >= 0.9 (ensure stability)

**Example YAML**:
```yaml
model:
  ema:
    tau_start: 0.99
    tau_end: 0.995
    warmup_steps: 2000
```

## Runtime Data Structures

### Loss Components

**Description**: Loss metrics returned by loss functions

**Structure**:
```python
{
    # Existing JEPA losses
    "loss/total": float,           # Original total loss
    "loss/step_mean": float,       # Mean loss across prediction steps
    "loss/step_1": float,          # Loss for first prediction step
    # ... (other steps)

    # NEW: Anti-collapse metrics
    "ac/var_loss": float,          # Variance floor penalty
    "ac/cov_loss": float,          # Covariance penalty
    "ac/total": float,             # Total anti-collapse loss (alpha*var + beta*cov)
    "ac/std_mean": float,          # Mean std across dimensions
    "ac/std_min": float,           # Minimum std (detect dead dimensions)
    "ac/std_max": float,           # Maximum std
    "ac/dead_dims_frac": float,    # Fraction of dimensions with std < 0.05

    # Combined loss
    "loss/total_combined": float,  # JEPA + lambda*anti_collapse
}
```

### EMA Monitoring Metrics

**Description**: EMA health metrics logged during training

**Structure**:
```python
{
    # NEW: EMA monitoring
    "ema/tau": float,              # Current EMA coefficient
    "ema/encoder_norm": float,     # ||θ|| - online encoder parameter norm
    "ema/target_norm": float,      # ||θ̄|| - target encoder parameter norm
    "ema/delta_stem": float,       # mean(|θ̄ - θ|) for CNN stem
    "ema/delta_transformer": float,# mean(|θ̄ - θ|) for token transformer
    "ema/z_cosine_sim": float,     # Cosine sim between Z_t and Z_star distributions
}
```

## State Transitions

### EMA Update Lifecycle

```
[Training Step Start]
    ↓
[Forward Pass: compute Z_t, Z_star, Z_pred]
    ↓
[Loss Computation: L_jepa + L_ac]
    ↓
[Backward Pass: compute gradients]
    ↓
[Optimizer Step: update θ] ← Online encoder updated
    ↓
[EMA Update: θ̄ ← τ θ̄ + (1-τ) θ] ← Target encoder updated
    ↓
[Log Metrics: including EMA health]
    ↓
[Training Step End]
```

**Invariant**: EMA update MUST occur after optimizer step

### Anti-Collapse Detection Lifecycle

```
[Model Forward]
    ↓
[Compute Z_t from encoder]
    ↓
[Compute VC-Reg loss on Z_t]
    ↓
    ├─ Variance Floor: measure std per dimension
    │   └─ If std_j < gamma: add penalty
    └─ Covariance: measure off-diagonal correlations
        └─ Add penalty proportional to correlation strength
    ↓
[Backprop includes anti-collapse gradients]
    ↓
[Encoder learns to spread variance and decorrelate]
```

## Relationships

### Configuration Hierarchy

```
SIADConfig
  └─ train: TrainConfig
      └─ loss: LossConfig
          └─ anti_collapse: AntiCollapseConfig (NEW)

SIADConfig
  └─ model: ModelConfig
      └─ ema: EMAConfig (ENHANCED)
```

### Component Dependencies

```
Trainer
  ├─ uses → WorldModel
  │   ├─ contains → ContextEncoder (θ)
  │   └─ contains → TargetEncoderEMA (θ̄)
  └─ uses → JEPAWorldModelLoss
      └─ computes → VC-Reg anti-collapse loss
```

## Migration Notes

**Backward Compatibility**:
- All new config fields have defaults, so existing configs work without changes
- If `anti_collapse` section missing, defaults to current behavior (simple variance floor)
- Existing checkpoints can be loaded - EMA state is part of model state_dict

**Breaking Changes**:
- None. This is a backward-compatible enhancement.
