Below is a **revised PRD for the SIAD Demo** that explicitly incorporates the guidance of the committee you convened. I’ll structure it so that the **decisions and design choices are clearly linked to each persona’s advice**, but the final PRD is cohesive and implementable.

This PRD assumes:

* **Model:** JEPA-style world model (no decoder)
* **Data:** Sentinel-1, Sentinel-2, VIIRS, rain anomaly
* **AOI:** San Francisco Bay Area
* **Goal:** Demonstrate **expectation-based change detection**, not generic anomaly detection.

---

# SIAD Demo PRD (Committee-Reviewed)

Version: 0.3
Status: Demo Specification
AOI: San Francisco Bay Area
Audience: Defense analysts, investors, ML experts

---

# 1. Executive Concept

SIAD demonstrates a **world-model approach to satellite monitoring**.

Instead of detecting raw change, SIAD highlights:

> Locations where observed evolution diverges from the model’s predicted evolution under environmental normalization.

The demo must clearly show three things:

1. **Prediction** – what the model expected to happen
2. **Observation** – what actually happened
3. **Unexpected change** – where they differ

This triad is the core narrative.

*(LeCun + Feynman recommendation)*

---

# 2. Core User Story

An analyst monitoring the San Francisco Bay Area wants to identify infrastructure developments or activity surges without manually scanning hundreds of tiles.

SIAD surfaces **ranked hotspots** where:

* change is unexpected
* change persists
* change is structurally coherent

The system provides:

* prioritized locations
* explanation of signals
* evidence imagery
* baseline comparison

*(Karp + Palantir Product recommendation)*

---

# 3. System Overview

The demo system consists of three layers:

### 1. World Model Engine

Learns expected evolution of the AOI.

Inputs:

* Sentinel-2 (RGB + NIR)
* Sentinel-1 VV/VH
* VIIRS nightlights
* rainfall anomaly

Outputs:

* predicted next-month latent representation
* residual map between prediction and observation

---

### 2. Detection Engine

Transforms residual maps into:

* hotspot polygons
* unexpected change score
* persistence metrics
* modality attribution

---

### 3. Analyst Interface

Displays:

* ranked hotspots
* imagery evidence
* timeline spikes
* baseline comparison
* environmental normalization

---

# 4. Detection Pipeline

## Step 1 — Latent Encoding

For month t:

```
Z_t = Encoder(X_t)
Z*_t+1 = EMAEncoder(X_t+1)
```

---

## Step 2 — Expected Evolution

Predict next month under neutral environmental conditions:

```
Ẑ_t+1 = Transition(Z_t, neutral_actions)
```

Neutral actions:

```
rain_anomaly = 0
temp_anomaly = 0
```

Label in UI:

**Environmental Normalization**

*(Andrew Ng suggestion: clear practical framing)*

---

## Step 3 — Residual Map

For each token i:

```
Residual_i = 1 − cosine(Ẑ_t+1_i , Z*_t+1_i)
```

Produces a **16×16 unexpected change map**.

Interpretation:

| Value  | Meaning             |
| ------ | ------------------- |
| Low    | evolution predicted |
| Medium | moderate deviation  |
| High   | unexpected change   |

---

## Step 4 — Tile Score

Aggregate residuals:

```
TileScore = mean(top 10% residual tokens)
```

This emphasizes localized structural changes.

---

## Step 5 — Persistence Detection

Hotspots must meet either:

### Sustained change

Residual above threshold for ≥3 months

### Burst change

Single large spike (95th percentile)

---

## Step 6 — Spatial Clustering

Connected high-residual tokens are merged into hotspot polygons.

Each hotspot stores:

* location
* onset month
* persistence duration
* dominant modality
* unexpected change score

---

# 5. Hotspot Ranking

Score formula:

```
AccelerationScore = Persistence × MeanResidual
```

Hotspots ranked within AOI.

Top 10 displayed in dashboard.

*(Andrew Ng: prioritize actionable ranking)*

---

# 6. Required Baselines

The system must compare the world model against simpler predictors.

### Baseline A — Persistence

```
Ẑ_t+1 = Z_t
```

### Baseline B — Seasonal

```
Ẑ_t+1 = Z_t-12
```

UI must allow toggling between:

```
Baseline detection
World model detection
```

*(Palantir product lead requirement)*

---

# 7. Explanation System

Each hotspot must answer four questions.

| Question | Method                                 |
| -------- | -------------------------------------- |
| Where    | residual map footprint                 |
| When     | timeline spike                         |
| What     | modality attribution                   |
| Why      | environmental normalization comparison |

---

## Modality Attribution

Residuals are computed per modality:

```
R_SAR
R_Optical
R_VIIRS
```

Contribution percentages determine dominant signal.

Example output:

```
Primary signal: SAR texture change (64%)
Secondary: optical surface change (23%)
Activity increase: VIIRS (13%)
```

---

# 8. Analyst Interface

## Dashboard

Map showing AOI with hotspots.

Right panel:

```
Top Unexpected Changes

1. Port of Oakland
Score: 0.21
Persistence: 4 months
Type: Structural acceleration

2. SFO Apron Expansion
Score: 0.17
Persistence: 2 months
Type: Structural burst
```

---

## Hotspot Detail View

### Panel A — Expectation vs Reality

Three-panel visualization:

```
Predicted evolution
Observed imagery
Unexpected change map
```

*(LeCun + Feynman requirement)*

---

### Panel B — Timeline

Chart:

```
Unexpected Change Score
Rain anomaly
Nightlights
```

Shows onset and persistence.

---

### Panel C — Evidence Imagery

Tabs:

* Sentinel-2 RGB
* Sentinel-1
* VIIRS

Month slider.

---

### Panel D — Environmental Normalization

Toggle:

```
Observed conditions
Neutral environment
```

Shows difference in residual map.

---

### Panel E — Baseline Comparison

Toggle:

```
Persistence baseline
Seasonal baseline
World model
```

Analyst can see reduction in noise.

---

# 9. Visual Design

*(Anduril design recommendation)*

Residual overlay uses **three discrete states**:

```
Green – expected evolution
Yellow – moderate deviation
Red – significant unexpected change
```

Hotspot polygons outlined clearly.

16×16 token grid hidden by default.

---

# 10. Demo Scenarios

Three categories must be shown.

### Structural Change

Example:

```
Port of Oakland yard expansion
```

Signals:

* SAR increase
* surface change

---

### Activity Surge

Example:

```
Increased port logistics activity
```

Signal:

* VIIRS spike

---

### False Positive Suppression

Example:

```
Seasonal vegetation cycles
```

Baseline flags change.

World model suppresses it.

---

# 11. Evaluation Gates

Demo must pass:

### Spatial Coherence

Residual maps show clustered patterns.

---

### Baseline Outperformance

World model produces cleaner hotspot localization.

---

### Known Change Detection

At least one SF infrastructure event detected.

---

### Agricultural Noise Suppression

Vegetation regions do not dominate hotspot list.

---

# 12. Demo Narrative

The presenter says:

> We trained a model to understand how San Francisco normally evolves.
> Each month it predicts what the city should look like next.
> When reality diverges from that expectation, the system highlights the difference.

Then show:

```
Prediction
Reality
Difference
```

This makes the concept intuitive.

*(Feynman simplification)*

---

# 13. Definition of Done

The demo is ready when:

* model trained on ≥36 months
* detection pipeline operational
* ranked hotspot list available
* baseline comparison working
* expectation-vs-reality visualization implemented
* at least one compelling SF example demonstrated

---

# Final Committee Consensus

The demo must prove:

```
Prediction → Observation → Unexpected Change
```

not merely:

```
Image → anomaly heatmap
```

If this distinction is visible, the demo succeeds.