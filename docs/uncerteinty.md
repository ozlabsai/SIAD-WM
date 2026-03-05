
# Uncertainty as First-Class Output (Detailed Plan)

## Objective

Augment the world model so it outputs:

* **predicted next-state tokens** (as before), and
* a **per-token uncertainty estimate** that tells you *when the model is not confident*.

This unlocks:

* lower false positives (clouds, rare terrains, sensor artifacts)
* confidence-aware scoring (“high residual but high uncertainty → don’t alert”)
* more honest rollouts (uncertainty grows with horizon)

You already have this as “Stochastic Dynamics (Optional Phase 2)” in the spec. M4 is: **make it real and wire it end-to-end**. 

---

# 1) Model change: deterministic → stochastic transition

## 1.1 What to predict

Instead of predicting `Z_{t+1}` directly, the transition predicts Gaussian parameters:

* `mu` : `[B, N, D]`
* `log_sigma` : `[B, N, D]` (diagonal Gaussian), clamped to a safe range 

Then sample:

[
Z_{t+1} = \mu + \exp(\log \sigma) \odot \epsilon,\quad \epsilon \sim \mathcal{N}(0, I)
]

## 1.2 Where this goes

In `Fψ` (the transition transformer output head):

Current output head:

* transformer → tokens `[B,256,512]`

New output head:

* transformer → shared trunk `[B,256,512]`
* two linear heads:

  * `head_mu: 512 → 512`
  * `head_log_sigma: 512 → 512`

Clamp `log_sigma` to spec bounds (e.g. `[-5, 2]`). 

---

# 2) Training objective: keep JEPA, add stochastic likelihood

You have two clean options. Both keep the core “predict representations” goal.

## Option A (simplest, works well): **sampled JEPA distance**

* Sample `Z_{t+1}` once (or a small K times).
* Compute your existing cosine distance to the EMA target embeddings `Z_star` 

Loss per step k:

[
L_k = \text{weighted_mean}*i\left(d\left(Z^{(sample)}*{pred}[k,i], Z^* [k,i]\right)\right)
]

Pros: minimal change to current training.
Cons: uncertainty can be a bit “loose” unless regularized.

## Option B (more principled): **Gaussian NLL in latent space**

Treat target embedding as a sample from the predicted Gaussian:

[
\mathcal{L}*{NLL} = \frac{1}{2}\sum*{d}\left(\frac{(z^*_d-\mu_d)^2}{\sigma_d^2} + 2\log\sigma_d\right)
]

Pros: uncertainty becomes calibrated and meaningful.
Cons: you lose the cosine geometry unless you normalize carefully.

### Recommendation

Start with **Option A** for stability (especially since you’re already using cosine), then add an NLL-style auxiliary term later if needed.

---

# 3) Regularizing uncertainty (prevent collapse/blow-up)

Without constraints, `sigma` can:

* collapse to near-zero everywhere (overconfidence)
* blow up everywhere (model “gives up”)

Your spec suggests a sigma stability penalty. 

## 3.1 Add a sigma stability loss

Two simple and effective regularizers:

**A) Penalize extreme sigmas**

* Encourage `log_sigma` to stay near a reasonable prior mean, e.g. `log_sigma0 = -2`:

[
L_{\sigma} = \text{mean}((\log\sigma - \log\sigma_0)^2)
]

**B) Penalize spatially uniform “give up”**

* If sigma is high everywhere, punish it by a small weight on mean sigma:

[
L_{\text{mean}\sigma} = \text{mean}(\exp(\log\sigma))
]

Final:
[
L = L_{JEPA} + \lambda_{\sigma} L_{\sigma} + \lambda_{m} L_{\text{mean}\sigma}
]

Keep lambdas small (start tiny; tune after you see behavior).

---

# 4) Rollout API changes (still compatible)

Your rollout currently returns:

* `Z_pred` `[B,H,N,D]` 

M4 adds uncertainty outputs:

* `mu_seq` `[B,H,N,D]`
* `log_sigma_seq` `[B,H,N,D]`
* optionally `z_sample_seq` `[B,H,N,D]`

### Recommended interface

* `rollout(..., return_dist=True)` returns a struct:

  * `mu`, `log_sigma`, `z_sample`
* Keep default behavior returning deterministic prediction if needed (e.g., use `mu` as the deterministic path for backward compat).

---

# 5) How uncertainty is consumed downstream

## 5.1 Token uncertainty map

From `log_sigma` (per token, per latent dimension), compute a scalar uncertainty per token:

**Recommended reduction:**

* `u_{k,i} = mean_d exp(log_sigma_{k,i,d})`

This yields a `[B,H,N]` uncertainty map.

Then reshape to `16×16` per step for visualization, same as residuals. 

## 5.2 Confidence-aware residual scoring

You already compute residuals:

* `r_{k,i} = d(Z_pred[k,i], Z_star[k,i])` 

Now also compute an uncertainty-adjusted residual:

Two safe choices:

**A) Gate residuals by uncertainty**

* only consider tokens where `u_{k,i} <= u_max`

**B) Soft downweight**

* `r̃_{k,i} = r_{k,i} / (u_{k,i} + eps)`
  (or `r̃ = r * exp(-α u)`)

This ensures “model confused” doesn’t become “model screams anomaly.”

This combines beautifully with M2 quality weights:

* low quality → high uncertainty → lower alert confidence
* high residual + low uncertainty + good quality → strong alert candidate

---

# 6) Training schedule / curriculum (important)

## 6.1 Start deterministic, then turn on stochastic

Your spec recommends deterministic first. 
Do:

1. Train deterministic until loss stabilizes and rollouts are sane
2. Switch `stochastic.enabled=true`
3. Warm-start:

   * initialize `head_mu` from deterministic head weights (if same shape)
   * initialize `log_sigma` head bias to a small value (e.g., `-2`)

## 6.2 Keep rollout curriculum

Continue your H curriculum (`H=1 → 3 → 6`)  because uncertainty will naturally grow with horizon and you don’t want it to explode early.

---

# 7) Config changes (canonical)

Add to config (matches spec section 5): 

```yaml
model:
  stochastic:
    enabled: true
    log_sigma_min: -5
    log_sigma_max: 2
train:
  loss:
    stochastic_mode: "sampled_jepa"   # or "nll"
    sigma_reg:
      enabled: true
      log_sigma0: -2.0
      lambda_sigma: 0.01
      lambda_mean_sigma: 0.001
```

(Values are starting points; tune after observing maps.)

---

# 8) Acceptance tests (must add)

## 8.1 Determinism test update

Your spec has a determinism test when stochastic is disabled. 
Extend it:

* When `stochastic.enabled=false`: exact same outputs
* When `stochastic.enabled=true`:

  * `mu` must be deterministic
  * `z_sample` changes between runs unless you fix RNG seed

## 8.2 Uncertainty sanity tests

1. **Cloud/quality correlation test**

* On cloud-heavy samples, mean uncertainty should be higher than clear samples (paired with M2 quality channel/weights).

2. **Horizon growth test**

* `mean(u)` should increase with k (rollout step), at least slightly.

3. **False positive suppression**

* Compare alert scores with and without uncertainty weighting; cloud-driven “alerts” should drop.

---

# Deliverables for M4

1. Transition head outputs `(mu, log_sigma)` per token
2. Sampling implemented + toggled by config
3. Sigma regularization losses
4. Rollout returns uncertainty maps
5. Confidence-aware scoring recipe (uncertainty gating/downweighting)
6. Added acceptance tests listed above
