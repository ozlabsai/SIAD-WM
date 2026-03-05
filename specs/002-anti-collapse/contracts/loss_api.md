# Loss API Contract

**Feature**: 002-anti-collapse | **Version**: 1.0.0

## Overview

This contract defines the public API for anti-collapse loss computation and the enhanced JEPA world model loss.

## Functions

### `vcreg_loss()`

**Purpose**: Compute VC-Reg anti-collapse loss on encoder outputs

**Signature**:
```python
def vcreg_loss(
    z: torch.Tensor,
    gamma: float = 1.0,
    alpha: float = 25.0,
    beta: float = 1.0,
    eps: float = 1e-4
) -> Tuple[torch.Tensor, Dict[str, float]]
```

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `z` | `torch.Tensor` | Yes | Encoder outputs, shape `[B, N, D]` |
| `gamma` | `float` | No | Variance floor threshold (default: 1.0) |
| `alpha` | `float` | No | Variance loss weight (default: 25.0) |
| `beta` | `float` | No | Covariance loss weight (default: 1.0) |
| `eps` | `float` | No | Numerical stability epsilon (default: 1e-4) |

**Returns**:
| Type | Description |
|------|-------------|
| `torch.Tensor` | Scalar anti-collapse loss value |
| `Dict[str, float]` | Metrics dictionary with keys: `var_loss`, `cov_loss`, `std_mean`, `std_min`, `std_max`, `dead_dims_frac` |

**Behavior**:
1. Flatten `z` from `[B, N, D]` to `[B*N, D]`
2. Compute per-dimension standard deviation
3. Variance loss: `L_var = mean_j ReLU(gamma - std_j)`
4. Covariance matrix: `C = cov(X)` over batch×token samples
5. Covariance loss: `L_cov = (sum_{i≠j} C[i,j]^2) / D`
6. Return `alpha * L_var + beta * L_cov` and metrics

**Constraints**:
- `z.ndim == 3` (must be `[B, N, D]`)
- `gamma > 0`
- `alpha >= 0` and `beta >= 0`
- Input is not modified (pure function)

**Example**:
```python
from siad.train.losses import vcreg_loss
import torch

z_t = model.encoder(x_context)  # [4, 256, 512]
loss, metrics = vcreg_loss(z_t, gamma=1.0, alpha=25.0, beta=1.0)

print(f"Anti-collapse loss: {loss.item():.4f}")
print(f"Mean std: {metrics['std_mean']:.4f}")
print(f"Dead dimensions: {metrics['dead_dims_frac']:.2%}")
```

---

### `anti_collapse_regularizer()` (DEPRECATED)

**Status**: Maintained for backward compatibility but deprecated in favor of `vcreg_loss()`

**Migration**:
```python
# Old API (simple variance floor)
reg_loss, metrics = anti_collapse_regularizer(z_pred, min_std=0.1)

# New API (VC-Reg)
reg_loss, metrics = vcreg_loss(z_t, gamma=1.0, alpha=25.0, beta=1.0)
```

**Note**: Old API applies to predictions `z_pred`, new API applies to encoder outputs `z_t` as per spec.

---

### `compute_jepa_world_model_loss()` (ENHANCED)

**Purpose**: Compute combined JEPA + anti-collapse loss

**Signature**:
```python
def compute_jepa_world_model_loss(
    z_pred: torch.Tensor,
    z_target: torch.Tensor,
    z_t: Optional[torch.Tensor] = None,  # NEW
    loss_type: str = "cosine",
    step_weights: Optional[torch.Tensor] = None,
    anti_collapse: bool = True,
    anti_collapse_config: Optional[Dict] = None,  # NEW
    # Old params deprecated but maintained
    anti_collapse_weight: float = 0.1,
    min_std: float = 0.1
) -> Tuple[torch.Tensor, Dict[str, float]]
```

**Changes**:
- **NEW**: `z_t` parameter - encoder outputs for VC-Reg computation
- **NEW**: `anti_collapse_config` - dictionary with `gamma`, `alpha`, `beta`, `lambda` keys
- **DEPRECATED**: `anti_collapse_weight`, `min_std` - use `anti_collapse_config` instead

**Behavior**:
1. Compute JEPA rollout loss (cosine or MSE)
2. If `anti_collapse` and `z_t` provided:
   - Compute VC-Reg loss on `z_t` using `anti_collapse_config`
   - Add to total loss: `L_total = L_jepa + lambda * L_ac`
3. If `anti_collapse` but `z_t` not provided:
   - Fall back to old behavior (simple variance floor on `z_pred`)
4. Return combined loss and merged metrics

**Example (New API)**:
```python
from siad.train.losses import compute_jepa_world_model_loss

# Get model outputs
z_t = model.encode(x_context)
z_pred = model.rollout(z_t, actions)
z_target = model.encode_targets(x_targets)

# Compute loss with VC-Reg
ac_config = {"gamma": 1.0, "alpha": 25.0, "beta": 1.0, "lambda": 1.0}
loss, metrics = compute_jepa_world_model_loss(
    z_pred=z_pred,
    z_target=z_target,
    z_t=z_t,  # NEW: encoder outputs
    anti_collapse_config=ac_config  # NEW: VC-Reg config
)
```

**Example (Old API - Backward Compatible)**:
```python
# Old API still works (uses simple variance floor)
loss, metrics = compute_jepa_world_model_loss(
    z_pred=z_pred,
    z_target=z_target,
    anti_collapse_weight=0.1,
    min_std=0.1
)
```

---

## Metrics Dictionary Schema

**Anti-Collapse Metrics** (returned by `vcreg_loss` and merged into `compute_jepa_world_model_loss`):

| Key | Type | Description |
|-----|------|-------------|
| `ac/var_loss` | `float` | Variance floor penalty component |
| `ac/cov_loss` | `float` | Covariance penalty component |
| `ac/total` | `float` | Total anti-collapse loss (alpha*var + beta*cov) |
| `ac/std_mean` | `float` | Mean standard deviation across dimensions |
| `ac/std_min` | `float` | Minimum standard deviation (lowest dimension) |
| `ac/std_max` | `float` | Maximum standard deviation (highest dimension) |
| `ac/dead_dims_frac` | `float` | Fraction of dimensions with std < 0.05 |

**Combined Loss Metrics**:

| Key | Type | Description |
|-----|------|-------------|
| `loss/total` | `float` | JEPA loss only (without anti-collapse) |
| `loss/step_mean` | `float` | Mean loss across prediction steps |
| `loss/step_1`, `loss/step_2`, ... | `float` | Per-step prediction losses |
| `loss/total_combined` | `float` | **Final loss: JEPA + lambda*anti_collapse** |

---

## Configuration Schema Contract

**AntiCollapseConfig** (YAML):

```yaml
train:
  loss:
    anti_collapse:
      type: "vcreg"          # Required: "vcreg" (only supported type)
      gamma: 1.0             # Optional: variance floor threshold (default: 1.0)
      alpha: 25.0            # Optional: variance loss weight (default: 25.0)
      beta: 1.0              # Optional: covariance loss weight (default: 1.0)
      lambda: 1.0            # Optional: total anti-collapse weight (default: 1.0)
      apply_to: ["z_t"]      # Optional: where to apply (default: ["z_t"])
```

**Validation**:
- `type == "vcreg"` (enforced)
- `gamma > 0`
- `alpha >= 0`, `beta >= 0`, `lambda >= 0`
- `apply_to` in `[["z_t"], ["z_t", "z_pred_1"]]`

---

## Backward Compatibility Guarantees

1. **Old `anti_collapse_regularizer()` API**: Maintained, not removed
2. **Old `compute_jepa_world_model_loss()` signature**: All old parameters still work
3. **Checkpoint Format**: No changes to checkpoint structure
4. **Default Behavior**: If `z_t` not provided, falls back to old simple variance floor

## Breaking Changes

**None** - This is a fully backward-compatible enhancement.

## Versioning

- **Version 1.0.0**: Initial VC-Reg implementation
- Compatible with: SIAD model spec v0.2, PyTorch 2.x
