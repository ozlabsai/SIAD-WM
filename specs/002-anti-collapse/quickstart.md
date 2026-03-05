# Quickstart: Anti-Collapse Training Stability

**Feature**: 002-anti-collapse | **Last Updated**: 2026-03-04

## TL;DR

Enhanced JEPA training with VC-Reg anti-collapse regularization and hardened EMA stability mechanisms. Prevents representation collapse and ensures stable target encoder updates throughout training.

## Prerequisites

- Existing SIAD world model training setup
- Python 3.13+ with PyTorch 2.x
- GPU with CUDA support (recommended)

## Configuration

### Minimal Config (Use Defaults)

```yaml
# No changes needed - defaults are conservative and stable
# Located in: configs/train-*.yaml
```

### Custom Anti-Collapse Settings

```yaml
# configs/train-custom.yaml
train:
  loss:
    anti_collapse:
      type: "vcreg"
      gamma: 1.0      # Variance floor target
      alpha: 25.0     # Variance loss weight
      beta: 1.0       # Covariance loss weight
      lambda: 1.0     # Total anti-collapse weight
      apply_to: ["z_t"]  # Apply to encoder outputs only

model:
  ema:
    tau_start: 0.99   # Initial EMA coefficient
    tau_end: 0.995    # Final EMA coefficient after warmup
    warmup_steps: 2000  # EMA warmup duration
```

## Basic Usage

### Training with Anti-Collapse

```bash
# Standard training (uses default anti-collapse settings)
uv run siad train --config configs/train-bay-area-v03.yaml

# Custom settings
uv run siad train --config configs/train-custom.yaml
```

### Monitoring Training Stability

```bash
# View W&B dashboard for real-time metrics:
# - ac/std_mean: Average std across dimensions (should stay > 0.3)
# - ac/dead_dims_frac: Fraction of collapsed dimensions (should be < 0.1)
# - ema/tau: EMA coefficient (should ramp smoothly from 0.99 → 0.995)
# - ema/delta_stem: Parameter drift (should stay in reasonable band)
```

### Running Acceptance Tests

```bash
# Run all anti-collapse tests
uv run pytest tests/unit/test_anti_collapse.py -v

# Run specific test
uv run pytest tests/unit/test_anti_collapse.py::test_variance_floor -v

# Run integration stability test (200-step training loop)
uv run pytest tests/integration/test_training_stability.py -v
```

## Common Scenarios

### Scenario 1: Detect Representation Collapse

**Symptoms**:
- `ac/std_mean` drops below 0.3
- `ac/dead_dims_frac` exceeds 0.1
- Model predictions become uniform/bland

**Solution**:
```yaml
# Increase anti-collapse strength
train:
  loss:
    anti_collapse:
      lambda: 2.0  # Double the anti-collapse weight
      alpha: 50.0  # Increase variance penalty
```

### Scenario 2: JEPA Loss Stalls (Over-Regularization)

**Symptoms**:
- `loss/total` stops decreasing
- Representations have high variance but poor prediction quality
- `ac/total` dominates combined loss

**Solution**:
```yaml
# Reduce anti-collapse weight
train:
  loss:
    anti_collapse:
      lambda: 0.5  # Halve the weight
```

### Scenario 3: EMA Instability (Rapid Drift)

**Symptoms**:
- `ema/delta_stem` or `ema/delta_transformer` spike unexpectedly
- `ema/z_cosine_sim` fluctuates wildly
- Training loss oscillates

**Solution**:
```yaml
# Slow down EMA updates
model:
  ema:
    tau_start: 0.995  # Start with higher tau
    tau_end: 0.999    # End with very high tau
    warmup_steps: 5000  # Longer warmup
```

### Scenario 4: Fast Tuning Loop (Validate Hyperparameters)

```bash
# Run short training to validate settings (1000 steps)
uv run siad train --config configs/train-custom.yaml --max-steps 1000

# Check metrics:
# - ac/std_mean should stabilize above 0.3 within first 500 steps
# - ema/tau should ramp smoothly from tau_start → tau_end
# - loss/total should decrease steadily
```

## Debugging

### Check Current Anti-Collapse Configuration

```python
# In Python REPL or script
from siad.config import load_config

config = load_config("configs/train-custom.yaml")
print(config.train.loss.anti_collapse)
# AntiCollapseConfig(type='vcreg', gamma=1.0, alpha=25.0, beta=1.0, lambda=1.0, apply_to=['z_t'])
```

### Inspect EMA State During Training

```python
# In trainer.py or debugging script
tau = model.target_encoder.get_tau()
delta_ema = compute_ema_delta(model.encoder, model.target_encoder)
print(f"Current tau: {tau:.4f}, EMA delta: {delta_ema:.6f}")
```

### Verify Anti-Collapse Loss Computation

```python
# Test loss computation manually
from siad.train.losses import vcreg_loss
import torch

# Mock encoder outputs
z_t = torch.randn(4, 256, 512)  # [B, N, D]

# Compute VC-Reg loss
loss_ac = vcreg_loss(z_t, gamma=1.0, alpha=25.0, beta=1.0)
print(f"Anti-collapse loss: {loss_ac:.4f}")
```

## Acceptance Test Reference

| Test | What It Checks | Pass Criteria |
|------|----------------|---------------|
| F: Variance Floor | Encoder doesn't collapse to zero variance | `mean(std_j) > 0.3`, `dead_dims_frac < 0.1` |
| G: Constant Embedding | Encoder doesn't map all inputs to same vector | Avg pairwise cosine sim < 0.95 |
| H: Regression Test | Anti-collapse is actually working | With `λ=0`, tests F and G fail |
| I: EMA Monotonic Schedule | τ never decreases during training | `tau[t+1] >= tau[t]` for all t |
| J: EMA Update Order | EMA updates after optimizer step | Mock test verifies correct ordering |
| K: EMA Stability | EMA doesn't explode or stagnate | `delta_ema` stays in sane band over 200 steps |

## Tuning Guidelines

| Metric | Healthy Range | Action if Outside Range |
|--------|---------------|------------------------|
| `ac/std_mean` | 0.3 - 2.0 | < 0.3: increase `lambda` or `alpha` |
| `ac/dead_dims_frac` | < 0.1 | > 0.1: increase `lambda` or `alpha` |
| `ac/total` | 0.01 - 0.5 | > 0.5: reduce `lambda` (over-regularizing) |
| `ema/tau` | 0.99 - 0.999 | Should ramp smoothly, adjust warmup if jumpy |
| `ema/delta_stem` | 0.001 - 0.1 | > 0.1: increase `tau` (too much drift) |
| `ema/z_cosine_sim` | 0.7 - 0.95 | < 0.7: EMA diverging; > 0.95: collapsing |

## Next Steps

1. **Validate on Existing Checkpoints**: Load pre-trained model and fine-tune with new anti-collapse settings
2. **Run Full Training**: Train from scratch with enhanced stability mechanisms
3. **Monitor Production**: Set up alerts for `ac/std_mean < 0.3` or `ac/dead_dims_frac > 0.1`
4. **Iterate on Thresholds**: After baseline run, refine test thresholds in `tests/unit/test_anti_collapse.py`

## References

- Feature Spec: [spec.md](./spec.md)
- Implementation Plan: [plan.md](./plan.md)
- Research: [research.md](./research.md)
- Data Model: [data-model.md](./data-model.md)
