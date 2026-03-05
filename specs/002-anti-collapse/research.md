# Research: Anti-Collapse Training Stability

**Feature**: 002-anti-collapse | **Date**: 2026-03-04

## Research Questions

### Q1: VC-Reg Implementation Details

**Question**: How should VC-Reg variance and covariance losses be computed efficiently for large batch×token dimensions?

**Decision**: Implement VC-Reg with flattened batch×token computation

**Rationale**:
- Per spec, flatten `[B, N, D]` → `[B*N, D]` before computing statistics
- Variance floor: `L_var = mean_j ReLU(γ - std(X[:,j]))` where `γ=1.0`
- Covariance penalty: `L_cov = (sum_{i≠j} C[i,j]^2) / D` where `C = cov(X)`
- PyTorch's `torch.std(X, dim=0)` computes per-dimension std efficiently
- For covariance, use `torch.cov(X.T)` then zero diagonal and sum squared off-diagonal terms

**Alternatives Considered**:
- **Barlow Twins**: Cross-correlation matrix normalization → Rejected: More complex, VC-Reg is proven in VICReg paper
- **SimCLR variance**: Only variance component → Rejected: Covariance penalty crucial for preventing correlated collapse
- **Per-batch computation**: Compute separately per batch → Rejected: Loses statistical power, spec requires batch×token pooling

**Implementation Notes**:
```python
def vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4):
    # z: [B, N, D] encoder outputs
    B, N, D = z.shape
    X = z.reshape(B*N, D)  # Flatten batch×tokens

    # Variance floor penalty
    std_per_dim = torch.sqrt(X.var(dim=0) + eps)  # [D]
    var_loss = torch.relu(gamma - std_per_dim).mean()

    # Covariance penalty
    X_centered = X - X.mean(dim=0, keepdim=True)
    cov = (X_centered.T @ X_centered) / (B*N - 1)  # [D, D]
    cov_diag_zeroed = cov.fill_diagonal_(0)
    cov_loss = (cov_diag_zeroed ** 2).sum() / D

    return alpha * var_loss + beta * cov_loss
```

### Q2: Apply Anti-Collapse to Encoder Outputs vs Predictions

**Question**: Should VC-Reg apply to encoder outputs `z_t`, predictor outputs `z_pred`, or both?

**Decision**: Apply to encoder outputs `z_t` ONLY (mandatory), optionally to `z_pred[1]` later

**Rationale**:
- Spec states "Always: encoder outputs `Z_t = fθ(X_t)`"
- Encoder collapse is the primary failure mode - if encoder collapses, predictions are meaningless
- Predictor collapse is secondary and may not manifest if encoder is stable
- Adding to predictor increases compute and may interfere with JEPA learning dynamics

**Alternatives Considered**:
- **Apply to all prediction steps**: → Rejected: Spec says "optional later" and only for `z_pred[1]`
- **Apply only to predictor**: → Rejected: Doesn't prevent encoder collapse
- **Apply to both immediately**: → Rejected: Conservative approach is encoder-only first

**Configuration**:
```yaml
train:
  loss:
    anti_collapse:
      apply_to: ["z_t"]  # Start with encoder only
      # Later: ["z_t", "z_pred_1"] if needed
```

### Q3: EMA Update Order and Timing

**Question**: When exactly should EMA update happen relative to optimizer step and gradient computation?

**Decision**: EMA update MUST happen after optimizer step

**Rationale**:
- Standard EMA practice: update target from latest online parameters
- Per spec M3.4.2: "1. forward + loss, 2. optimizer step (update θ), 3. EMA update (update θ̄ from θ)"
- If EMA updates before optimizer step, target encoder gets stale parameters from previous iteration
- This causes EMA lag and potential instability

**Current Implementation Check**:
Existing `TargetEncoderEMA.update_from_encoder()` is called manually - need to verify trainer.py calls it after optimizer.step()

**Verification Strategy**:
- Add assertion in test that mocks parameter updates and verifies order
- Add logging of `delta_ema` to detect if update order is incorrect (would show sudden jumps)

**Alternatives Considered**:
- **Update before optimizer step**: → Rejected: Creates lag, violates standard EMA practice
- **Update during forward pass**: → Rejected: Would update multiple times per step if forward called multiple times

### Q4: EMA Schedule Monotonicity and Warmup

**Question**: How should τ ramp from `tau_start` to `tau_end`, and how do we enforce monotonicity?

**Decision**: Linear warmup with explicit monotonicity check

**Rationale**:
- Existing implementation in `TargetEncoderEMA.update_from_encoder()` uses linear warmup
- `tau = tau_start + (tau_end - tau_start) * (step / warmup_steps)`
- After warmup: `tau = tau_end` (constant)
- Spec requires "τ must be monotonic non-decreasing"

**Strengthening**:
- Add assertion in `update_from_encoder()`: `assert new_tau >= self.last_tau`
- Track `self.last_tau` to enforce monotonicity
- Add test I to verify schedule never decreases

**Alternatives Considered**:
- **Exponential warmup**: `tau = tau_end - (tau_end - tau_start) * exp(-step/warmup_steps)` → Rejected: Linear is simpler and spec doesn't require exponential
- **Cosine schedule**: → Rejected: May decrease during cosine curve, violates monotonicity
- **No warmup**: → Rejected: Spec explicitly requires warmup from tau_start to tau_end

### Q5: Acceptance Test Thresholds

**Question**: What are appropriate thresholds for Tests F-K?

**Decision**: Conservative initial thresholds, refined after baseline run

**Rationale**:
- Test F (Variance Floor):
  - `threshold_mean = 0.3` (expect mean std > 0.3 after normalization)
  - `threshold_dead = 0.05` (dimensions with std < 0.05 considered dead)
  - `threshold_frac = 0.1` (allow up to 10% dead dimensions initially)
- Test G (Constant Embedding):
  - `threshold_cosine_sim = 0.95` (average pairwise similarity should be well below 1.0)
- Test H (Regression):
  - With `λ=0`, expect Tests F and G to have 50%+ failure rate

**Refinement Strategy**:
- Run baseline with current anti-collapse settings
- Measure actual variance statistics on training data
- Adjust thresholds to be strict but not brittle
- Document thresholds in test configuration

**Alternatives Considered**:
- **Fixed strict thresholds**: → Rejected: May be too brittle without empirical calibration
- **No thresholds (only relative checks)**: → Rejected: Spec requires explicit assertions
- **Per-layer thresholds**: → Rejected: Adds complexity, start with global thresholds

### Q6: Logging Infrastructure for EMA Monitoring

**Question**: What metrics need to be logged to detect EMA instability early?

**Decision**: Log τ, parameter norms, delta_ema, and Z distribution similarity

**Rationale**:
- Per spec M3.4.3, log every N steps:
  - `tau_current`: Current EMA coefficient
  - `||θ||`, `||θ̄||`: Online and target encoder norms (detect divergence)
  - `delta_ema = mean(|θ̄ - θ|)`: Per-module parameter difference
  - Cosine similarity between `Z_t` and `Z_star` distributions (detect collapse)
- Use Weights & Biases (already integrated in trainer.py)
- Log at same frequency as other training metrics (every 100 steps)

**Implementation**:
```python
# In trainer.py train_epoch()
if step % 100 == 0:
    metrics.update({
        "ema/tau": model.target_encoder.get_tau(),
        "ema/encoder_norm": encoder_param_norm,
        "ema/target_norm": target_encoder_param_norm,
        "ema/delta": delta_ema,
        "ema/z_cosine_sim": cosine_sim_between_distributions,
    })
```

**Alternatives Considered**:
- **Log every step**: → Rejected: Too verbose, 100-step frequency sufficient
- **Log only when anomalies detected**: → Rejected: Need full timeline to debug issues
- **Separate monitoring script**: → Rejected: Integrate into existing training loop for simplicity

## Summary

All research questions resolved. Key decisions:
1. VC-Reg with flattened batch×token computation
2. Apply to encoder outputs `z_t` only (initially)
3. EMA update strictly after optimizer step
4. Linear warmup with monotonicity enforcement
5. Conservative test thresholds (0.3 mean std, <10% dead dims, cosine < 0.95)
6. Log τ, norms, delta_ema, Z similarity every 100 steps

No blocking unknowns. Proceed to Phase 1 design.
