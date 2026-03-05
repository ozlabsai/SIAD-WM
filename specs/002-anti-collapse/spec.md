# Feature Specification: Anti-Collapse Training Stability

**Branch**: `002-anti-collapse` | **Date**: 2026-03-04
**Source**: `docs/improvment_plan/anti_collapse.md`

## Problem Statement

JEPA training is vulnerable to representation collapse where encoder outputs degenerate to constant or low-variance embeddings, and EMA target encoder instability can cause training divergence. Without explicit anti-collapse regularization and EMA stability mechanisms, the world model cannot learn meaningful spatiotemporal representations.

## Requirements

### M3.1: Anti-Collapse Regularizer

**Must Have:**
- Implement VC-Reg (VICReg-style Variance + Covariance) loss term
- Apply to encoder outputs `Z_t = fθ(X_t)` with shape `[B, N, D]`
- Variance floor penalty: `L_var = mean_j ReLU(γ - std(X[:,j]))` with `γ=1.0`, `eps=1e-4`
- Covariance penalty: `L_cov = (sum_{i≠j} C[i,j]^2) / D` where `C = cov(X)` over batch×token samples
- Combined loss: `L_ac = α·L_var + β·L_cov` with defaults `α=25`, `β=1`
- Total loss: `L_total = L_jepa + λ·L_ac` with default `λ=1.0`
- Configuration via YAML:
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

**Should Have:**
- Optional application to `Z_pred[1]` (predictor outputs) guarded by config toggle

**Won't Have:**
- Application to all timesteps (only encoder and optionally first prediction step)

### M3.2: Tuning Protocol

**Must Have:**
- Log per-dimension statistics of `Z_t`:
  - `mean(std_j)` - average standard deviation across dimensions
  - `min(std_j)` - minimum standard deviation (detect dead dimensions)
  - Dead dimension fraction (proportion where `std_j < 0.05`)
- Log `L_jepa` and `L_ac` trends during training
- Fast tuning loop: 1k-5k step runs to validate hyperparameters

**Guidance:**
- If collapse detected: increase `λ` or `α`
- If JEPA stalls / bland representations: decrease `λ`

### M3.3: Anti-Collapse Acceptance Tests

**Must Have:**

**Test F: Representation Variance Floor**
- Compute `std_j` on `Z_t` over batch×token dimension
- Assert `mean(std_j) > threshold_mean` (conservative threshold, refined after baseline)
- Assert `fraction(std_j < threshold_dead) < threshold_frac`

**Test G: Constant Embedding Check**
- Sample 16 different tiles
- Mean-pool tokens → `[16, D]`
- Assert average pairwise cosine similarity is NOT ~1.0

**Test H: Regression Test**
- Verify that with `λ=0` tests F and G are much more likely to fail
- Confirms tests are meaningful and anti-collapse mechanism works

### M3.4: EMA Stability Checklist

**M3.4.1: EMA Schedule (Must Implement Exactly)**
- Start `τ = tau_start` (e.g., 0.99)
- Ramp to `tau_end` (e.g., 0.995-0.999) over `warmup_steps`
- After warmup: keep τ high and stable
- **Rule**: τ must be monotonic non-decreasing

**M3.4.2: Update Timing (Must Be Consistent)**
Per training step:
1. Forward pass + loss computation
2. Optimizer step (update θ)
3. EMA update (update θ̄ from θ)

**M3.4.3: Logging Requirements**
Log every N steps:
- `tau_current`
- `||θ||`, `||θ̄||` parameter norms (or proxy per module)
- `delta_ema = mean(|θ̄ - θ|)` per module group (encoder stem / token transformer)
- Cosine similarity between `Z_t` and `Z_star` distributions on fixed mini-batch
- Optional: "EMA lag" (moving average of `delta_ema`)

**M3.4.4: EMA Failure Modes**
- **EMA too fast (τ too low)**: targets chase online encoder → instability → increase τ/extend warmup
- **EMA too slow (τ too high too early)**: targets stale → slow learning → lower `tau_start` slightly
- **Mismatch spikes**: `delta_ema` jumps → check optimizer LR spikes, mixed precision overflow, update order

### M3.5: EMA Acceptance Tests

**Must Have:**

**Test I: EMA Monotonic Schedule**
- Verify τ ramps correctly and never decreases throughout training

**Test J: EMA Update Order**
- Verify EMA update happens after optimizer step (mock parameter test)

**Test K: EMA Stability on Fixed Batch**
- Run 200-step training loop on tiny dataset
- Assert `delta_ema` stays within sane band (no explosions)
- Assert `Z_star` changes smoothly (no sudden distribution collapse)

## Success Criteria

1. VC-Reg loss implemented and integrated into training loop
2. EMA schedule properly configured with monotonic τ ramp
3. All acceptance tests F-K passing in CI
4. Logging dashboard showing:
   - Representation variance statistics
   - Dead dimension tracking
   - EMA drift metrics
   - Loss component trends
5. Short tuning runs (1k-5k steps) demonstrate stable training without collapse

## Non-Goals

- Global optimization of hyperparameters (use conservative defaults, tune if needed)
- Application of anti-collapse to all predictor timesteps (only encoder and optionally Z_pred[1])
- Alternative anti-collapse methods (Barlow Twins, SimCLR, etc.) - stick with VC-Reg

## Technical Notes

- This builds on existing JEPA training infrastructure
- Must preserve existing `L_jepa` computation
- EMA mechanism already exists in spec - this hardens the implementation
- Tests integrate into existing CI/smoke run framework
