# EMA API Contract

**Feature**: 002-anti-collapse | **Version**: 1.0.0

## Overview

This contract defines the enhanced EMA (Exponential Moving Average) target encoder interface with strengthened stability guarantees.

## Class: `TargetEncoderEMA`

**Purpose**: Target encoder with EMA updates and stability monitoring

**Location**: `src/siad/model/encoder.py`

---

### Constructor

**Signature**:
```python
class TargetEncoderEMA(nn.Module):
    def __init__(
        self,
        in_channels: int = 8,
        latent_dim: int = 512,
        num_blocks: int = 4,
        num_heads: int = 8,
        mlp_dim: int = 2048,
        dropout: float = 0.0,
        tau_start: float = 0.99,
        tau_end: float = 0.995,
        warmup_steps: int = 2000
    )
```

**Arguments**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `in_channels` | `int` | `8` | Number of input channels |
| `latent_dim` | `int` | `512` | Token embedding dimension |
| `num_blocks` | `int` | `4` | Number of transformer blocks |
| `num_heads` | `int` | `8` | Number of attention heads |
| `mlp_dim` | `int` | `2048` | FFN hidden dimension |
| `dropout` | `float` | `0.0` | Dropout rate |
| `tau_start` | `float` | `0.99` | Initial EMA coefficient |
| `tau_end` | `float` | `0.995` | Final EMA coefficient (after warmup) |
| `warmup_steps` | `int` | `2000` | Number of steps to ramp from tau_start to tau_end |

**Constraints**:
- `0 < tau_start <= tau_end < 1.0` - Enforces monotonic τ schedule
- `warmup_steps > 0` - Must have positive warmup
- Architecture params must match `ContextEncoder`

**Example**:
```python
from siad.model.encoder import TargetEncoderEMA

target_encoder = TargetEncoderEMA(
    in_channels=8,
    latent_dim=512,
    tau_start=0.99,
    tau_end=0.995,
    warmup_steps=2000
)
```

---

### `forward()`

**Signature**:
```python
def forward(self, x: torch.Tensor) -> torch.Tensor
```

**Arguments**:
| Name | Type | Description |
|------|------|-------------|
| `x` | `torch.Tensor` | Input observations, shape `[B, C, H, W]` |

**Returns**:
| Type | Description |
|------|-------------|
| `torch.Tensor` | Target tokens `z_star`, shape `[B, N, D]`, **no gradients** |

**Behavior**:
- Runs forward pass through internal encoder
- All computations under `torch.no_grad()`
- Returns stable target representations for JEPA loss

**Example**:
```python
with torch.no_grad():
    z_star = target_encoder(x_targets)  # [B, 256, 512]
```

---

### `update_from_encoder()` (ENHANCED)

**Signature**:
```python
@torch.no_grad()
def update_from_encoder(
    self,
    context_encoder: ContextEncoder,
    step: Optional[int] = None
) -> Dict[str, float]  # NEW: returns metrics
```

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `context_encoder` | `ContextEncoder` | Yes | Online encoder to copy parameters from |
| `step` | `int` | No | Current training step (for schedule) |

**Returns** (NEW):
| Type | Description |
|------|-------------|
| `Dict[str, float]` | EMA metrics: `tau`, `delta_stem`, `delta_transformer`, `encoder_norm`, `target_norm` |

**Behavior**:
1. Compute current `tau` based on step and warmup schedule
2. **ENFORCE**: `tau >= self.last_tau` (monotonicity check)
3. Update parameters: `θ̄ ← τ θ̄ + (1-τ) θ`
4. Compute and return monitoring metrics

**Constraints**:
- MUST be called after optimizer step (not before)
- `tau` MUST be monotonic non-decreasing
- All parameters of `context_encoder` must match `self.encoder` structure

**Example**:
```python
# In training loop - AFTER optimizer.step()
ema_metrics = model.target_encoder.update_from_encoder(
    context_encoder=model.encoder,
    step=global_step
)

# Log metrics
wandb.log({
    "ema/tau": ema_metrics["tau"],
    "ema/delta_stem": ema_metrics["delta_stem"],
    "ema/delta_transformer": ema_metrics["delta_transformer"],
})
```

---

### `get_tau()` (NEW)

**Signature**:
```python
def get_tau(self, step: Optional[int] = None) -> float
```

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `step` | `int` | No | Training step (uses `self.current_step` if not provided) |

**Returns**:
| Type | Description |
|------|-------------|
| `float` | Current EMA coefficient τ |

**Behavior**:
- If `step < warmup_steps`: Linear ramp from `tau_start` to `tau_end`
- If `step >= warmup_steps`: Returns `tau_end` (constant)
- Formula: `tau = tau_start + (tau_end - tau_start) * min(step / warmup_steps, 1.0)`

**Example**:
```python
current_tau = model.target_encoder.get_tau(step=5000)
print(f"EMA coefficient: {current_tau:.4f}")
```

---

### `get_ema_metrics()` (NEW)

**Signature**:
```python
def get_ema_metrics(
    self,
    context_encoder: ContextEncoder
) -> Dict[str, float]
```

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `context_encoder` | `ContextEncoder` | Yes | Online encoder to compare against |

**Returns**:
| Type | Description |
|------|-------------|
| `Dict[str, float]` | Metrics: `delta_stem`, `delta_transformer`, `encoder_norm`, `target_norm` |

**Behavior**:
- Compute `delta_ema = mean(|θ̄ - θ|)` per module group
- Split metrics by CNN stem vs token transformer
- Compute parameter norms for both encoders

**Metrics Dictionary**:
| Key | Description |
|-----|-------------|
| `delta_stem` | Mean absolute parameter difference in CNN stem |
| `delta_transformer` | Mean absolute parameter difference in transformer blocks |
| `encoder_norm` | L2 norm of online encoder parameters |
| `target_norm` | L2 norm of target encoder parameters |

**Example**:
```python
metrics = model.target_encoder.get_ema_metrics(model.encoder)
print(f"EMA drift (stem): {metrics['delta_stem']:.6f}")
print(f"EMA drift (transformer): {metrics['delta_transformer']:.6f}")
```

---

## Update Timing Contract

**CRITICAL**: EMA update MUST occur in the following order:

```python
# Training step order (ENFORCED BY CONTRACT)
1. forward_pass()      # Compute outputs
2. loss.backward()     # Compute gradients
3. optimizer.step()    # Update online encoder θ
4. ema_update()        # Update target encoder θ̄ from θ ← MUST BE HERE
5. log_metrics()       # Log training metrics
```

**Violation Detection**:
- If EMA updates before optimizer step, `delta_ema` will be systematically higher
- Test J verifies correct update order using mocked parameters

---

## EMA Schedule Contract

**Guarantee**: τ is monotonic non-decreasing throughout training

**Schedule Phases**:

| Phase | Step Range | Behavior | Formula |
|-------|------------|----------|---------|
| Warmup | `0 ≤ step < warmup_steps` | Linear ramp | `τ = tau_start + (tau_end - tau_start) * (step / warmup_steps)` |
| Stable | `step ≥ warmup_steps` | Constant | `τ = tau_end` |

**Enforcement**:
```python
# In update_from_encoder()
assert new_tau >= self.last_tau, f"EMA tau decreased: {self.last_tau} → {new_tau}"
```

**Typical Values**:
- `tau_start = 0.99` (1% update per step initially)
- `tau_end = 0.995` (0.5% update per step after warmup)
- `warmup_steps = 2000` (ramp over 2000 steps)

---

## Monitoring Metrics Contract

**Required Logging**: EMA health metrics MUST be logged periodically

**Metrics**:
| Metric | Healthy Range | Warning Condition |
|--------|---------------|-------------------|
| `ema/tau` | `0.99 - 0.999` | Outside range → check config |
| `ema/delta_stem` | `0.001 - 0.1` | `> 0.1` → rapid drift, increase tau |
| `ema/delta_transformer` | `0.001 - 0.1` | `> 0.1` → rapid drift, increase tau |
| `ema/encoder_norm` | Model-dependent | Sudden spike → check optimizer |
| `ema/target_norm` | Model-dependent | Should track encoder norm closely |

**Logging Frequency**: Every 100 training steps (or configurable)

**Example**:
```python
# In trainer.py
if global_step % 100 == 0:
    ema_metrics = model.target_encoder.get_ema_metrics(model.encoder)
    wandb.log({
        "ema/tau": model.target_encoder.get_tau(),
        **ema_metrics
    }, step=global_step)
```

---

## Backward Compatibility

**Preserved**:
- All original constructor parameters have defaults
- `forward()` signature unchanged
- `update_from_encoder()` can be called without `step` (uses internal counter)

**Enhanced**:
- `update_from_encoder()` now returns metrics (previously returned None)
- New methods (`get_tau()`, `get_ema_metrics()`) are additive

**Breaking Changes**: None

---

## Versioning

- **Version 1.0.0**: Enhanced EMA with monitoring and monotonicity enforcement
- Compatible with: SIAD model spec v0.2, PyTorch 2.x
