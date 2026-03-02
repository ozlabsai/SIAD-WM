Below is a **buildable MVP spec** for the **Strategic Infrastructure Acceleration Detector (SIAD)** as a **full world model** (multi-step rollouts + scenario “actions”), optimized for **high VFM + wow + fast time-to-results**.

---

# SIAD MVP Spec (World Model Version)

## 0) One-sentence product definition

A **spatio-temporal world model** trained on multi-modal satellite time series that can **roll out counterfactual futures** under exogenous stressor scenarios (rain/heat) and flags **persistent, structural deviations** consistent with accelerated infrastructure/activity changes.

---

# 1) Scope and deliverables

## MVP scope

* **1 AOI** (Area of Interest), ~50×50 km (smaller is fine)
* **Monthly cadence**
* **36 months** history (minimum 24; 36 is better)
* **Prediction horizon**: 6 months rollout
* **Outputs**:

  1. **Acceleration heatmap** (spatial)
  2. **Hotspot ranking** with thumbnails (before/after)
  3. **Timeline** per hotspot (when acceleration begins)
  4. **Counterfactual rollouts** under scenario knobs (rain/heat)

## What you will not do in MVP

* Global model
* Weekly cadence
* “Detect bases”
* Claim causality from actions
* Pixel-level generation / photoreal prediction

---

# 2) Data needed (Earth Engine catalog friendly)

## A) State (observations) per month

**(Required) Sentinel-1 SAR**

* Bands: VV, VH
* Monthly composite: median
* Reason: cloud-proof structural anchor

**(Required) Sentinel-2 optical**

* Bands: B2 (Blue), B3 (Green), B4 (Red), B8 (NIR)
* Optional band: B11 (SWIR1) if you want better bare soil / construction separation
* Monthly composite: median of cloud-masked pixels
* Also store: “valid pixel fraction” mask channel (very important)

**(Required) Nighttime lights**

* VIIRS DNB monthly (or monthly composite product)
* Reason: operational/activity signal

## B) Actions / context (scenario knobs)

Pick **two** (keep minimal):

**(Required) Rainfall anomaly**

* CHIRPS monthly precipitation (or ERA5 monthly precipitation)
* Convert to anomaly:
  [
  a^\text{rain}*t = \frac{P_t - \mu*{month}}{\sigma_{month} + \epsilon}
  ]
  where (\mu_{month}) and (\sigma_{month}) computed over the 3-year baseline for that AOI.

**(Optional but great) Temperature anomaly**

* ERA5 monthly 2m temperature anomaly (same normalization idea)

> These “actions” are used for **counterfactual conditioning** and to explain away weather-driven vegetation/water changes. Do not pitch them as causal levers for construction.

## C) Optional “sanity helpers” (use if you see false positives)

* SRTM DEM (static) to suppress terrain artifacts
* Global Surface Water (optional) to help interpret flood-driven anomalies

---

# 3) Preprocessing spec (this is make-or-break)

## Spatial

* Choose a fixed projection (e.g., EPSG:3857) and resample all inputs.
* Target resolution:

  * **10m** for S2 and S1 (S1 effectively ~10m scale; resampling OK)
  * VIIRS is coarser → upsample to match tile grid

## Temporal

* Monthly windows: calendar month boundaries
* For each month:

  * S2 cloud mask + median composite
  * S1 median composite (consistent orbit direction if possible)
  * VIIRS monthly composite

## Channels per timestep (recommended)

Let (x_t) be a tensor [C, H, W] for each tile, with:

* S2: B2, B3, B4, B8  (4 channels)
* S1: VV, VH           (2 channels)
* VIIRS: lights         (1 channel)
* S2_valid: valid fraction (1 channel, broadcast or pixel mask)
  Total state channels: **8**

Actions/context per timestep (a_t) (tile-level scalars, broadcast to [1,H,W] or kept separate):

* rain_anom (1)
* temp_anom (1, optional)

---

# 4) Tiling & dataset construction

## AOI tiling

* Tile size: **256×256** at 10m ≈ 2.56 km square
* Stride: 256 (non-overlapping) for speed; optionally 128 for more samples

## Sequence sampling

Define:

* Context length (L = 6) months
* Rollout horizon (H = 6) months

Each training sample:

* Input: (x_{t-L+1:t}), actions (a_{t:t+H-1})
* Targets: (x_{t+1:t+H})

Minimum samples:
tiles × (T - (L+H)) where T ≈ 36 months.

---

# 5) World model architecture (full WM)

## Encoders

* Observation encoder (f_\theta(x_t) \to z_t)

  * A small ConvNet or ViT-like patch encoder (keep it light for MVP)
* Target encoder (f_{\bar{\theta}}(x_t) \to \tilde{z}_t)

  * EMA/momentum updated version of encoder (JEPA-style stabilization)
* Action encoder (h_\phi(a_t) \to u_t)

  * MLP from action scalars (rain/temp) to latent action embedding

## Dynamics / predictor

* Transition model (F_\psi(z_t, u_t) \to \hat{z}_{t+1})

  * Transformer block or GRU in latent space
  * For MVP, a small transformer is fine

## Training objective (multi-step rollout)

Roll forward recursively:

* (\hat{z}_{t+1} = F(\hat{z}_t, u_t)) where (\hat{z}_t := z_t) initially
* Continue for k=1..H

Loss:
[
\mathcal{L} = \sum_{k=1}^{H} w_k \cdot d(\hat{z}*{t+k}, \tilde{z}*{t+k})
]

* (d): cosine distance or MSE in latent
* (w_k): optional decay weights (e.g., slightly smaller for later steps)

**This is the “full WM”**: it’s trained to stay coherent over rollouts.

---

# 6) Acceleration scoring (the detector)

You want *persistent deviation beyond what the WM expects under context/actions*.

For each tile and each month:

## A) Baseline rollout (expected)

Given last (L) months, roll forward (H) months using **observed** action sequence.

Compute rollout error:
[
r_{t+k} = d(\hat{z}*{t+k}, \tilde{z}*{t+k})
]

## B) Neutral counterfactual rollout

Roll forward using **neutral scenario** actions:

* rain_anom = 0
* temp_anom = 0

This gives counterfactual latents (\hat{z}^{(0)}).

Compute divergence of reality from neutral baseline:
[
r^{(0)}*{t+k} = d(\hat{z}^{(0)}*{t+k}, \tilde{z}_{t+k})
]

## C) Acceleration score

We want sustained, structural shifts, so define:

* Persistence: average over k=1..H
* Trend: slope over the last W months of residuals (W=3 is enough)
* Spatial coherence: cluster connected tiles

Example tile score:
[
S_t = \text{EMA}(\frac{1}{H}\sum_{k=1}^{H} r^{(0)}*{t+k}) + \lambda \cdot \text{slope}(r^{(0)}*{t-W:t})
]

Flag tiles where:

* (S_t) exceeds tile’s historical percentile (e.g., > 99th percentile of its own past)
* and persists for ≥ 2 consecutive months
* and forms clusters ≥ N tiles (e.g., N≥3)

---

# 7) Attribution layer (to reduce “scary false positives”)

When a hotspot triggers, compute modality-specific consistency checks:

* Recompute scoring using encoder inputs with:

  * SAR-only channels
  * Optical-only channels
  * Lights-only channel

You want “infrastructure-like” hotspots to show:

* SAR change + (often) lights change
* optical change consistent with clearing/paving

If only NDVI-like changes:

* mark as “environmental/seasonal likely”

This creates 3 labels for analysts:

* **Structural**
* **Activity**
* **Environmental**

(You don’t need perfect classification; you need credible triage.)

---

# 8) Evaluation protocol (even without labeled ground truth)

## A) Self-consistency checks

* Neutral scenario should match typical seasonal evolution better than random actions.
* Rain anomaly should change water/veg outcomes plausibly (sanity), not create roads.

## B) Backtesting on known “big build” regions

Pick an AOI with well-known public construction events (industrial expansion, port upgrade, etc.). You don’t need labels; you need “obvious” visual verification.

## C) False-positive set

Test on regions dominated by:

* agriculture cycles
* monsoon clouds
* seasonal rivers

Measure:

* hotspot rate per month
* persistence threshold effectiveness
* modality-attribution stability

---

# 9) Demo storyboard (what you show)

### Screen 1 — AOI map

* Tiles colored by acceleration score percentile

### Screen 2 — Hotspot list

For each hotspot:

* before/after thumbnails (S2, S1, lights)
* first-detected month
* confidence tier (Structural / Activity / Environmental)

### Screen 3 — Counterfactual

A toggle:

* “Neutral weather scenario”
* “Observed weather”
* “Extreme rain scenario”

Show:

* rollout trajectory in latent
* divergence heatmap overlay

### Screen 4 — Timeline

For a hotspot tile cluster:

* residual over time
* persistence window highlighted
* “start date” estimate

This is where the “wow” lives.

---

# 10) Red-team risks and hardening (explicit)

## Risk: “Actions don’t really control anything”

**Hardening:** demonstrate they control **veg/water dynamics** (where they should), and are weak on roads/buildings.

## Risk: “Cloud artifacts trigger alarms”

**Hardening:** include S2 valid mask channel + require SAR corroboration for “Structural” tier.

## Risk: “Seasonality floods the detector”

**Hardening:** tile-local percentile scoring + persistence + modality attribution.

## Risk: “Rollout drift”

**Hardening:** keep horizon H=6, add scheduled sampling if needed, prefer stable encoders.

## Risk: “It’s just change detection dressed up”

**Hardening:** emphasize **counterfactual baselining** + multi-step coherence:

* show that naive differencing generates many alarms in agriculture regions, while WM scoring is calmer.

---

# 11) What you can credibly claim (and what not)

**Credible claim:**

* “World model learns baseline spatio-temporal dynamics and flags persistent deviations; counterfactual rollouts provide scenario-based baselines that reduce false alarms.”

**Do not claim:**

* intent inference
* actor identification
* causal attribution from weather to construction
* tactical/real-time surveillance