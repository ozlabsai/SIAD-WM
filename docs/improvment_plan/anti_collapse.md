# Anti-Collapse + EMA Stability (Detailed, Executable)

## Objective

Make JEPA training **provably non-collapsing** and **EMA-stable**, with explicit loss terms, logging, and acceptance tests. 

---

## M3.1 Anti-collapse regularizer: choose + specify

### Decision

Implement **VC-Reg (VICReg-style Variance + Covariance)** as the mandatory anti-collapse term.

### Apply to

* **Always:** encoder outputs `Z_t = fθ(X_t)` with shape `[B, N, D]` 
* **Optional later:** `Z_pred[1]` once training is stable (guarded by a config toggle)

### Definition (precise)

Flatten over batch×tokens:

* `X = reshape(Z, [B*N, D])`

**Variance floor**

* `L_var = mean_j ReLU(γ - std(X[:,j]))`
* defaults: `γ=1.0`, `eps=1e-4`

**Covariance penalty**

* `C = cov(X)` over samples
* `L_cov = (sum_{i≠j} C[i,j]^2) / D`

**Anti-collapse loss**

* `L_ac = α·L_var + β·L_cov`
* defaults: `α=25`, `β=1`

**Total**

* `L_total = L_jepa + λ·L_ac` 
* default: `λ=1.0` (tune via protocol below)

### Config diff (add)

```yaml
train:
  loss:
    anti_collapse:
      type: "vcreg"
      gamma: 1.0
      alpha: 25.0
      beta: 1.0
      lambda: 1.0
      apply_to: ["z_t"]   # optional later: ["z_t","z_pred_1"]
```

---

## M3.2 Tuning protocol (fast loop)

Run a short training (1k–5k steps) and watch:

* `mean(std_j)` and `min(std_j)` over dims of `Z_t`
* “dead dims fraction” (`std_j < 0.05`)
* `L_jepa` trend (should decrease)
* `L_ac` should be non-zero early, not dominate

Adjust:

* collapse → increase `λ` (or `α`)
* JEPA stalls / bland reps → decrease `λ`

---

## M3.3 Acceptance tests (add to spec)

Add these tests alongside existing A–E. 

**F) Representation variance floor**

* compute `std_j` on `Z_t` over `B*N`
* assert:

  * `mean(std_j) > threshold_mean`
  * `fraction(std_j < threshold_dead) < threshold_frac`
    (choose initial thresholds conservatively; refine after baseline run)

**G) Constant-embedding check**

* take 16 different tiles
* mean-pool tokens → `[16, D]`
* assert average pairwise cosine similarity is not ~1.0

**H) Regression test**

* verify that with `λ=0` these tests are much more likely to fail (so the tests are meaningful)

---

# M3.4 EMA Stability Checklist (add to M3)

Anti-collapse isn’t enough if the EMA target encoder is unstable. Your spec defines τ schedule and warmup. 
M3 makes EMA stability operational.

## M3.4.1 EMA schedule (must implement exactly)

* Start `τ = tau_start` (e.g., 0.99) 
* Ramp to `tau_end` (e.g., 0.995–0.999) over `warmup_steps` 
* After warmup: keep τ high and stable

**Rule:** τ must be **monotonic non-decreasing**.

## M3.4.2 Update timing (must be consistent)

Per training step:

1. forward + loss
2. optimizer step (update θ)
3. EMA update (update θ̄ from θ)

(Do not EMA-update before the optimizer step.)

## M3.4.3 What to log (so you catch drift early)

Log every N steps:

* `tau_current`
* `||θ||`, `||θ̄||` norms (or a proxy per module)
* `delta_ema = mean(|θ̄ - θ|)` per module group (encoder stem / token transformer)
* cosine similarity between `Z_t` and `Z_star` distributions on a fixed mini-batch
* (optional) “EMA lag”: moving average of `delta_ema`

## M3.4.4 EMA failure modes + actions

* **EMA too fast (τ too low):** targets chase the online encoder → instability
  → increase τ / extend warmup
* **EMA too slow (τ too high too early):** targets stale → slow learning
  → lower `tau_start` slightly, ramp more gently
* **Mismatch spikes:** `delta_ema` suddenly jumps
  → check optimizer LR spikes, mixed precision overflow, or update order

---

## M3.5 EMA acceptance tests (add to spec)

You already have “EMA update test” sanity. 
Strengthen it:

**I) EMA monotonic schedule test**

* ensure τ ramps correctly and never decreases

**J) EMA update-order test**

* verify EMA update happens after optimizer step (can be checked with a mocked parameter)

**K) EMA stability on fixed batch**

* run a short training loop (e.g., 200 steps) on a tiny dataset
* assert `delta_ema` stays within a sane band (no explosions)
* assert `Z_star` changes smoothly (no sudden distribution collapse)

---

## M3 Deliverables

1. VC-Reg loss implemented + wired into training
2. EMA ramp + update order enforced
3. Logging dashboard for collapse + EMA drift
4. New acceptance tests F–K integrated into CI/smoke runs