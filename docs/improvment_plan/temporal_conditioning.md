# Temporal Conditioning (Detailed Plan)

## Objective

Provide the transition model with **explicit seasonal context** so that predictable seasonal changes (vegetation cycles, snow cover, lighting changes, etc.) are **modeled as normal dynamics rather than anomalies**.

Currently the transition is strictly Markov:

[
Z_{t+1} = F(Z_t, a_t)
]

But Earth observation data contains **strong annual periodicity**, which the model cannot easily infer from a single latent state.

The goal of M1 is to introduce **minimal temporal context** without breaking the architecture or rollout assumptions. 

---

# 1. Temporal Feature Design

## 1.1 Month-of-year encoding

Add two deterministic features:

```
month_sin = sin(2π * month / 12)
month_cos = cos(2π * month / 12)
```

Example values:

| Month | sin | cos   |
| ----- | --- | ----- |
| Jan   | 0.5 | 0.866 |
| Apr   | 1.0 | 0     |
| Jul   | 0   | -1    |
| Oct   | -1  | 0     |

These encode **annual cyclic structure** without discontinuities between December and January.

---

## 1.2 Temporal feature vector

Extend the action vector:

Current spec:

```
a_t = [rain_anom, temp_anom]
```

New schema:

```
a_t = [
  rain_anom,
  temp_anom,
  month_sin,
  month_cos
]
```

So:

```
A = 4
```

instead of `A ∈ {1,2}` in the original spec. 

Update config:

```yaml
actions:
  dim_input: 4
```

---

# 2. Integration with Architecture

The temporal features are treated as **exogenous context**, exactly like weather anomalies.

They enter through the existing **Action Encoder `hφ`**, meaning **no architectural change** is required.

---

## 2.1 Action encoder input

Current:

```
Input: a_t [B, A]
Output: u_t [B,128]
```

Now:

```
Input: a_t [B,4]
Output: u_t [B,128]
```

Architecture unchanged:

```
Linear(A → 64) + SiLU
Linear(64 → 128) + SiLU
```

---

## 2.2 Conditioning pathways

Temporal features propagate through **both conditioning mechanisms already defined**.

### Pathway 1 — Action token

```
u_proj = Linear(128 → 512)
append token to sequence
```

Transformer attention can explicitly attend to **time-of-year**.

---

### Pathway 2 — FiLM modulation

For each transformer block:

```
(γℓ, βℓ) = MLP(u_t)
x = (1 + γℓ) * x + βℓ
```

This allows seasonal effects to **globally modulate dynamics**.

Examples:

* vegetation growth amplitude
* snow reflectance
* night light seasonal variance.

---

# 3. Data Pipeline Changes

## 3.1 Month extraction

From each timestamp:

```
month = datetime.month
```

Then compute:

```
month_sin = sin(2π * month / 12)
month_cos = cos(2π * month / 12)
```

These values are stored with each training sample.

---

## 3.2 Dataset schema change

Before:

```
(X_t, X_{t+1}, rain_anom, temp_anom)
```

After:

```
(X_t, X_{t+1}, rain_anom, temp_anom, month_sin, month_cos)
```

---

## 3.3 Rollout sequences

For rollout horizon `H`:

```
a_seq = [
  a_t,
  a_{t+1},
  ...
  a_{t+H-1}
]
```

Each step includes its **own month encoding**.

Example:

```
Nov → Dec → Jan → Feb → Mar → Apr
```

---

# 4. Configuration Changes

Update model config:

```yaml
actions:
  input_dim: 4
  encoded_dim: 128
  film: true
  action_token: true
```

Update dataset preprocessing version.

Also bump:

```
preprocessing_version = "v2"
```

since the conditioning schema changed. 

---

# 5. Training Strategy

No change to JEPA objective.

Training flow remains:

```
Z0 = encoder(X_t)

Z_pred = rollout(Z0, a_seq, H)

Z_star = target_encoder(X_{t+1..t+H})

Loss = distance(Z_pred, Z_star)
```

Temporal features simply make the prediction **better conditioned**.

---

# 6. Acceptance Tests

## 6.1 Shape contract

Action vector shape:

```
Input: [B,4]
Output: [B,128]
```

Rollout:

```
a_seq shape = [B,H,4]
```

---

## 6.2 Seasonal stability test

Create evaluation pairs:

```
summer → autumn
winter → spring
```

Expected result:

Residual heatmaps should **not spike** solely due to seasonal vegetation shifts.

---

## 6.3 Ablation test

Run two models:

| Model    | Temporal Features |
| -------- | ----------------- |
| baseline | no                |
| M1       | yes               |

Measure:

* rollout error
* seasonal residual spikes

Expected outcome:

```
M1 residual variance across seasons ↓
```

---

# 7. Risk Assessment

### Low risk

* does not change model architecture
* uses deterministic features
* extremely common technique in time-series models.

### Possible minor risk

If the model overfits month encoding, it may:

```
learn “July always looks like X”
```

But this is unlikely because spatial tokens dominate the representation.

---

# 8. Expected Impact

Benefits:

1. Reduced **false anomaly spikes** at seasonal transitions
2. More stable **multi-step rollouts**
3. Better modeling of vegetation and lighting cycles
4. No increase in model size or compute.

---

# Deliverables for M1

1. Data pipeline update with `month_sin/cos`
2. Updated dataset schema
3. Updated action dimension in config
4. Training run with ablation comparison
5. Version bump in preprocessing manifest. 