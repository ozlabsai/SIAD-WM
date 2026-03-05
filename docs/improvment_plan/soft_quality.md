
# Soft Quality / Cloud Signal (Detailed Plan)

## Objective

Prevent residual heatmaps from being dominated by:

* clouds / haze
* cloud shadows
* snow-like brightness shifts
* optical artifacts

…while still allowing the model to learn real ground dynamics using SAR + VIIRS as stable anchors. 

Key principle:

* **We do not train an anomaly classifier**
* We **weight learning and scoring** by data quality so the model isn’t punished for unpredictable optical noise.

---

# 1) What we’re adding (data)

## 1.1 Preferred: per-pixel soft quality channel(s)

Add at least one of these as a new channel:

**Option A (best): `S2_cloud_prob`**

* float in `[0,1]` (1 = cloudy)
* can be cloud probability, or “invalid probability”

**Option B: `S2_quality`**

* float in `[0,1]` (1 = high quality)

**Option C: include both cloud + shadow**

* `cloud_prob`, `shadow_prob`

### Contract decision

To keep things clean, define one canonical meaning:

* `Q_t(x,y) ∈ [0,1]` where **1 = good pixel**, 0 = unreliable pixel.

If your source gives cloud probability `p_cloud`, then:

* `Q = 1 - p_cloud`

---

## 1.2 If soft per-pixel isn’t available: derive a proxy

If you only have `S2_valid_mask` (0/1), you can still produce **soft** quality by smoothing / aggregation:

* compute token-level quality:

  * for each 16×16 pixel region (token), `q_token = mean(mask)`
* compute tile quality:

  * `q_tile = mean(mask)`

This is weaker than real cloud prob, but still helps.

---

# 2) Where quality enters the system

You have two good integration points. Do both (they reinforce each other):

## 2.1 As an input channel to the encoder (recommended)

Add the quality map as an additional input channel to `X_t`.

Current channels: `C=8` including `S2_valid_mask` 
M2 change:

* either **replace** `S2_valid_mask` with `S2_quality`
* or **add** `S2_quality` as a new channel and keep the binary mask too (for hard gating)

### Recommendation

* Keep `S2_valid_mask` (hard gate)
* Add `S2_quality` (soft confidence)

This increases channels:

* from `C=8` → `C=9` (requires config + version bump)

---

## 2.2 As a loss / scoring weight (critical)

Even if the model *sees* quality, it should also be **trained/evaluated** with quality weighting:

### Token weighting

You already compute residual per token `r_{k,i}` 

Define a quality weight per token `w_i ∈ [0,1]` (derived from `Q_t` and/or `Q_{t+k}`).

Then replace mean over tokens with weighted mean:

* **Training loss weighting** (recommended):

  * downweight unreliable tokens in the JEPA distance
* **Residual map weighting** (recommended):

  * downweight unreliable tokens in the detection score

This is the single biggest lever to prevent “cloud = anomaly.”

---

# 3) How to compute token quality weights

Your tokens correspond to 16×16 pixel blocks. 
So define:

```text
q_token(t, i) = mean_{pixels in token i} Q_t
```

For a rollout step k (comparing prediction at t+k to target at t+k):

We care about **quality at the target time** (because residual uses `Z_star_{t+k}`):

```text
w_{k,i} = clamp(q_token(t+k, i), 0, 1)
```

Optional: combine with source quality at t:

```text
w_{k,i} = sqrt(q_token(t, i) * q_token(t+k, i))
```

This penalizes sequences where either the starting observation is poor or the target is poor.

---

# 4) Update the JEPA loss to be quality-aware

Your spec loss:

* token-wise cosine distance, mean over tokens, summed over k 

M2 change: replace `mean_tokens` with `weighted_mean_tokens`.

So:

```text
L_k = sum_i w_{k,i} * d(z_pred[k,i], z_star[k,i]) / (sum_i w_{k,i} + eps)
L = Σ_k w_k * L_k
```

This does **not** teach the model anomalies — it teaches:

> “Don’t try to predict unobservable junk; focus on learnable ground state.”

---

# 5) Update residual maps + tile score to be quality-aware

## 5.1 Residual heatmap

You can keep the raw residual map for visualization, but compute a quality-adjusted residual:

```text
r̃_{k,i} = w_{k,i} * r_{k,i}
```

or keep `r` and attach `w` alongside it in the output.

## 5.2 Tile anomaly score (aggregation)

Your current guideline: mean of top-q% tokens over k 

M2 change: choose top-q% using **quality-adjusted residuals**, and require a minimum quality:

* only consider tokens where `w_{k,i} >= q_min` (e.g., 0.5)
* then take top-q% of those tokens

This avoids:

* clouds dominating “top residual tokens”

---

# 6) Config + versioning changes

## 6.1 Model config

If adding a new channel:

```yaml
model:
  input:
    channels: 9
    band_order_version: "v2"   # or preprocessing bump only, your call
```

If replacing mask with quality (still 8 channels), then bump preprocessing version but not channels.

## 6.2 Required toggles (add)

Add config toggles for ablation:

* `quality.enabled: true/false`
* `quality.use_as_channel: true/false`
* `quality.use_as_loss_weight: true/false`
* `quality.q_min_token: 0.5`
* `quality.weight_mode: target_only | source_target_sqrt`

---

# 7) Acceptance tests (must pass)

## 7.1 Shape tests

* Encoder still outputs `[B,256,512]` 
* If channels change: input `[B,9,256,256]` works

## 7.2 Cloud sensitivity test (new)

Construct a small set:

* same tile, different months
* one month is cloudy, one is clear (or heavy mask vs light mask)

Expected:

* residual hotspots should **not** strongly concentrate on cloudy regions after M2
* uncertainty (if M4 later) should be higher in cloudy regions

## 7.3 Ablation matrix

Run:

1. baseline (no quality channel, no weighting)
2. channel only
3. weighting only
4. channel + weighting (expected best)

---

# 8) Risks / failure modes

### Risk A: quality channel becomes a shortcut

Model might learn “if quality low, ignore everything.”

Mitigation:

* quality influences loss weighting (good)
* but **don’t** allow the transition to output trivial predictions; anti-collapse + diverse batch helps (you already did M3)

### Risk B: too aggressive masking

If `q_min` too high, you discard too much signal and the model won’t learn.

Mitigation:

* start with `q_min = 0.2` and tune upward.

---

# Deliverables for M2

1. New data artifact: `Q_t` map (or derived token qualities)
2. Updated dataset loader: emits quality and token weights
3. Quality-aware JEPA loss
4. Quality-aware tile scoring
5. Ablation report showing reduced cloud-driven residuals