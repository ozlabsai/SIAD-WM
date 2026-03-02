# SIAD Model Spec (JEPA World Model) — Single Source of Truth

**Version:** 0.2  
**Status:** Canonical model contract for implementation  
**Owner:** Model Team  
**Scope:** Model architecture, inputs/outputs, configs, acceptance tests

---

## 1) Purpose

SIAD trains a **JEPA-centered, action-conditioned, full world model** on monthly satellite tiles.  
It learns predictive dynamics in **token latent space** and supports **multi-step rollouts** and **counterfactual scenarios**.

Key properties:
- **JEPA objective:** predict future **representations** (embeddings), not pixels
- **Target encoder:** EMA/momentum copy provides stable targets
- **Full world model:** recursive multi-step rollout (H months), not just 1-step
- **Spatial tokens:** latent grid preserves spatial structure for heatmaps/hotspots
- **Action-conditioned:** exogenous scenario knobs (rain/temp anomalies)

---

## 2) Data Contracts (Inputs / Outputs)

### 2.1 Observation tensor `X_t`
Per tile, per month:

- Shape: `[B, C, 256, 256]`
- Default channels: `C=8`
- **Band order is fixed and must be consistent end-to-end**:

| Index | Channel name |
|------:|--------------|
| 0 | `S2_B2` |
| 1 | `S2_B3` |
| 2 | `S2_B4` |
| 3 | `S2_B8` |
| 4 | `S1_VV_db_norm` |
| 5 | `S1_VH_db_norm` |
| 6 | `VIIRS_avg_rad_norm` |
| 7 | `S2_valid_mask` (pixel-level 0/1) |

Optional later:
- Add `S2_B11` as channel 8 (C=9) only via config version bump.

### 2.2 Action vector `a_t`
Per tile, per month:

- Shape: `[B, A]` where `A ∈ {1,2}`
- Content:
  - `a_t[0] = rain_anom` (required)
  - `a_t[1] = temp_anom` (optional)

Actions are **scenario inputs** / exogenous context (not agent actions).

### 2.3 Latent token grid `Z_t`
Encoder output:

- Shape: `[B, N, D]`
- Defaults:
  - `N = 256` tokens (16×16 spatial grid)
  - `D = 512` latent dimension

### 2.4 Rollout output `Z_pred`
World model rollout output:

- Shape: `[B, H, N, D]`
- Default `H=6` months

---

## 3) Tokenization Specification

### 3.1 Spatial token geometry
- Input tile: 256×256 pixels
- Token grid: 16×16
- Tokens per tile: `N = 256`
- Each token corresponds to a 16×16 pixel region (≈160m at 10m resolution).

### 3.2 Positional embeddings
- Learned 2D positional embeddings:
  - `pos_2d`: `[N, D]` added to spatial tokens
- Action token uses its own learned position embedding or zeros.

No temporal embeddings are required in the transition because transition is Markovian (single-step).

---

## 4) Architecture (Canonical)

Model consists of:
1) Context Encoder `fθ` (trainable)
2) Target Encoder `fθ̄` (EMA, stop-grad)
3) Action Encoder `hφ`
4) Transition Model `Fψ` (Markov token transformer, action-conditioned)

### 4.1 Context Encoder `fθ` (CNN stem + token transformer)
**Input:** `X_t` `[B,C,256,256]`  
**Output:** `Z_t` `[B,256,512]`

#### 4.1.1 CNN Stem (light, detail-preserving)
- Conv1: kernel 3×3, stride 1, out_ch 64 + GroupNorm + SiLU
- Conv2: kernel 3×3, stride 2, out_ch 128 + GroupNorm + SiLU
- Conv3: kernel 3×3, stride 1, out_ch 128 + GroupNorm + SiLU

Stem output spatial size: 128×128.

#### 4.1.2 Patchify + Projection
- Patchify stem feature map (128×128×128) into 16×16 tokens:
  - patch size on stem feature map: 8×8
  - yields 16×16 = 256 patches/tokens
- Flatten each patch (8×8×128) and project via Linear → D=512.

Add learned `pos_2d`.

#### 4.1.3 Token Encoder Transformer (spatial)
- 4 transformer blocks (pre-LN)
- Hidden size D=512
- Heads=8
- FFN=2048
- Dropout: 0.0–0.1 configurable

Output `Z_t`.

### 4.2 Target Encoder `fθ̄` (EMA)
- Same architecture as context encoder.
- Updated by EMA:
  - `θ̄ ← τ θ̄ + (1-τ) θ`
- Stop-grad (no backprop).

EMA schedule:
- Start: `τ=0.99`
- After warmup: `τ=0.995–0.999` (configurable ramp)

### 4.3 Action Encoder `hφ`
**Input:** `a_t` `[B,A]`  
**Output:** `u_t` `[B,128]`

MLP:
- Linear(A→64) + SiLU
- Linear(64→128) + SiLU

### 4.4 Transition Model `Fψ` (Markov World Model)
**Input:** `Z_t` `[B,256,512]`, `u_t` `[B,128]`  
**Output:** `Z_{t+1}` `[B,256,512]`

#### 4.4.1 Conditioning (must implement BOTH)
1) **Action token**
   - Project `u_t` to D=512: `u_proj` `[B,512]`
   - Append as one token → sequence length becomes 257

2) **FiLM conditioning per transformer block**
   - For each block ℓ, compute `(γℓ, βℓ)` from `u_t`:
     - MLP: 128 → 2×512
   - Apply FiLM after LayerNorm:
     - `x = (1 + γℓ) * x + βℓ`

#### 4.4.2 Transition transformer stack
- 6 transformer blocks (pre-LN)
- D=512, heads=8, FFN=2048
- Add learned `pos_2d` to spatial tokens each step.
- Action token uses separate learned embedding or zeros.

Drop action token at output; return only spatial tokens.

---

## 5) Stochastic Dynamics (Optional Phase 2)

### 5.1 Deterministic baseline (required)
Transition outputs `Z_{t+1}` directly.

### 5.2 Stochastic extension (recommended)
Predict per-token diagonal Gaussian params:
- `mu` `[B,256,512]`
- `log_sigma` `[B,256,512]` (clamped to [-5,2])

Sample:
- `Z_{t+1} = mu + exp(log_sigma) * eps`, eps ~ N(0,1)

Regularize:
- sigma stability penalty (avoid collapse/blow-up).

Curriculum:
- Train deterministic first; enable stochastic sampling later via config.

---

## 6) Rollout API (Full World Model)

### 6.1 Markov rollout
Given initial tokens `Z_t` and action sequence `u_{t:t+H-1}`:

For k=1..H:
- `Z_{t+k} = F(Z_{t+k-1}, u_{t+k-1})`

Return:
- `Z_pred` `[B,H,256,512]`

---

## 7) Training Objective (JEPA + multi-step rollout)

### 7.1 Targets
Compute targets from EMA encoder:
- `Z_star_{t+k} = TargetEncoder(X_{t+k})` → `[B,256,512]`

### 7.2 Prediction
Initialize:
- `Z0 = ContextEncoder(X_t)` (or last month in window; data pipeline decides)

Rollout H steps:
- `Z_pred = rollout(Z0, u_seq, H)`

### 7.3 Loss
Token-wise distance, summed over rollout steps:

Default distance:
- cosine distance per token:
  - L2-normalize on D
  - `d = 1 - cos(z_pred, z_star)`

Loss:
- `L = Σ_{k=1..H} w_k * mean_tokens(d(Z_pred[k], Z_star[k]))`
- Default `w_k=1`.

### 7.4 Anti-collapse regularizer (required)
Include a representation diversity regularizer (variance / std floor) across batch×tokens.
This is mandatory to prevent collapse.

---

## 8) Inference Outputs for Detection

### 8.1 Neutral scenario
Set actions to neutral:
- rain_anom=0
- temp_anom=0 (if present)

Roll out H steps to produce `Z_pred_neutral`.

### 8.2 Residual heatmaps
For each k:
- residual per token:
  - `r_{k,i} = d(Z_pred_neutral[k,i], Z_star[k,i])`

Reshape residual tokens to 16×16 heatmap per month.

Aggregation guidelines:
- tile score: mean of top-q% tokens (default q=10%) averaged over k
- persistence: EMA over months in detection module
- clustering: handled outside model module

---

## 9) Config Keys and Defaults

### 9.1 Model config
```yaml
model:
  input:
    tile_px: 256
    channels: 8
    band_order_version: "v1"
  tokens:
    grid: [16, 16]
    num_tokens: 256
    dim: 512
  encoder:
    stem:
      type: "cnn"
      convs:
        - {k: 3, s: 1, out: 64}
        - {k: 3, s: 2, out: 128}
        - {k: 3, s: 1, out: 128}
      norm: "groupnorm"
      act: "silu"
    patchify:
      stem_patch: 8   # patch size on stem feature map (128x128 -> 16x16 tokens)
    transformer:
      layers: 4
      heads: 8
      mlp_dim: 2048
      dropout: 0.0
  actions:
    dim: 128
    film: true
    action_token: true
  transition:
    transformer:
      layers: 6
      heads: 8
      mlp_dim: 2048
      dropout: 0.0
  ema:
    tau_start: 0.99
    tau_end: 0.995
    warmup_steps: 2000
  rollout:
    H: 6
  stochastic:
    enabled: false
    log_sigma_min: -5
    log_sigma_max: 2
````

### 9.2 Training config

```yaml
train:
  optimizer: "adamw"
  lr: 1.0e-4
  weight_decay: 1.0e-2
  batch_size: 16
  curriculum:
    - {H: 1, frac_steps: 0.2}
    - {H: 3, frac_steps: 0.4}
    - {H: 6, frac_steps: 0.4}
  loss:
    type: "cosine"
    weights: "uniform"
    anti_collapse: true
```

---

## 10) Required Interfaces (Python)

### `WorldModel` class

Must provide:

* `encode(x: Tensor) -> Tensor`

  * x: `[B,C,256,256]`
  * returns: `[B,256,512]`

* `transition(z: Tensor, a: Tensor) -> Tensor`

  * z: `[B,256,512]`
  * a: `[B,A]` (raw actions) or `[B,128]` (encoded); choose one and document
  * returns: `[B,256,512]`

* `rollout(z0: Tensor, a_seq: Tensor, H: int) -> Tensor`

  * z0: `[B,256,512]`
  * a_seq: `[B,H,A]` or `[B,H,128]`
  * returns: `[B,H,256,512]`

### `TargetEncoderEMA` wrapper

* `forward(x) -> z_star`
* `update_ema()` called each train step

---

## 11) Acceptance Tests (Must Pass)

### A) Shape contract tests (unit)

1. Encoder shape:

* input `[2,8,256,256]` → output `[2,256,512]`

2. Transition shape:

* input `[2,256,512]` + actions `[2,1]` → output `[2,256,512]`

3. Rollout shape:

* input z0 `[2,256,512]`, a_seq `[2,6,1]` → output `[2,6,256,512]`

### B) Determinism test (when stochastic disabled)

* same input + same weights → identical outputs

### C) EMA update test

* after one update step, target weights change by EMA rule (sanity check)

### D) Training smoke test (integration)

On a tiny dataset (e.g., 2 tiles × 12 months):

* run 50–200 training steps
* assert loss decreases by a non-trivial margin (e.g., >5–10% relative)

### E) Neutral rollout residual map generation (integration)

* compute `Z_star` and `Z_pred_neutral` for H=1 on a sample
* compute residual map shape 16×16

---

## 12) Debug/Ablation Toggles (Required)

Config toggles must exist:

* `actions.film: true/false`
* `actions.action_token: true/false`
* `stochastic.enabled: true/false`
* `rollout.H` override for debugging (1,3,6)
* channel subset toggles for evaluation:

  * SAR-only
  * optical-only
  * VIIRS-only

---

## 13) Versioning

The following versions must be written to the manifest and logs:

* `band_order_version` (e.g., "v1")
* `preprocessing_version`
* `model_spec_version` (this document version)

Any change to:

* band order
* tile size
* token grid size
  requires a version bump and compatibility notes.