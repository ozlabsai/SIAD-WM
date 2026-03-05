# Research: Temporal Conditioning

**Feature**: 003-temporal-conditioning | **Date**: 2026-03-05

## Research Questions

### Q1: Cyclical Time Encoding Best Practices

**Question**: What is the standard approach for encoding time-of-year in time-series ML models to handle December→January transitions?

**Decision**: Use **sine-cosine encoding** with annual period:
```python
month_sin = sin(2π * month / 12)
month_cos = cos(2π * month / 12)
```

**Rationale**:
1. **Cyclic continuity**: December (month=12) and January (month=1) are numerically close:
   - Dec: sin(2π*12/12)=0, cos(2π*12/12)=1
   - Jan: sin(2π*1/12)≈0.5, cos(2π*1/12)≈0.866
   - Euclidean distance: ~0.5 (vs 11 for raw month values)

2. **Smooth transitions**: Sin/cos provide smooth gradients for gradient-based learning (vs hard boundaries with one-hot encoding)

3. **Low dimensionality**: 2 features encode full annual cycle (vs 12 for one-hot)

4. **Standard practice**: Used in transformer temporal embeddings (Vaswani et al.), weather forecasting (WeatherBench), and time-series analysis

**Alternatives Considered**:
- **One-hot encoding (12 dims)**: Rejected - wastes dimensions, no continuity between Dec/Jan
- **Raw month value (1 dim)**: Rejected - creates artificial ordering (July not "more" than January), no cyclic structure
- **Learnable month embeddings**: Rejected - adds parameters (violates "no parameter increase" constraint), less interpretable

**References**:
- Vaswani et al. (2017) "Attention is All You Need" - positional encoding with sin/cos
- Rasp et al. (2020) "WeatherBench" - uses cyclical time encoding for seasonal forecasting
- Standard practice in Earth observation: ESA Climate Change Initiative uses sin/cos for seasonal decomposition

---

### Q2: Backward Compatibility for Model Input Dimension Changes

**Question**: How to load old checkpoints (action_dim=2) when new model expects action_dim=4?

**Decision**: **Automatic dimension padding** in checkpoint loading:

```python
# In WorldModel.load_state_dict()
def load_state_dict(self, state_dict, strict=False):
    # Check if action encoder has dimension mismatch
    current_action_dim = self.action_encoder.action_dim
    checkpoint_action_dim = infer_action_dim_from_state_dict(state_dict)

    if checkpoint_action_dim < current_action_dim:
        # Pad old Linear(2→64) weights to Linear(4→64)
        old_weight = state_dict['action_encoder.mlp.0.weight']  # [64, 2]
        new_weight = torch.zeros(64, current_action_dim)
        new_weight[:, :checkpoint_action_dim] = old_weight
        # Zero-initialize new temporal feature weights (month_sin/cos → neutral)
        state_dict['action_encoder.mlp.0.weight'] = new_weight

        print(f"Upgraded action encoder: {checkpoint_action_dim}→{current_action_dim} dims")

    super().load_state_dict(state_dict, strict=strict)
```

**Rationale**:
1. **Graceful degradation**: Old checkpoints load successfully, new temporal features start from zero (neutral conditioning)
2. **No manual intervention**: Users don't need to retrain from scratch or manually modify checkpoints
3. **Explicit logging**: Dimension upgrade is logged for transparency
4. **Standard practice**: PyTorch Lightning, Hugging Face Transformers use similar strategies for model evolution

**Alternatives Considered**:
- **Require full retraining**: Rejected - wastes compute, breaks existing workflows
- **Separate model versions**: Rejected - creates maintenance burden, confuses users
- **Configuration-based**: Rejected - forces users to maintain two configs (action_dim=2 for old, action_dim=4 for new)

**Implementation Note**: Use `strict=False` in `load_state_dict()` to allow missing/extra keys, then manually handle dimension mismatch before calling `super().load_state_dict()`.

---

###Q3: Dataset Schema Versioning Patterns

**Question**: How to track dataset preprocessing changes (v1: A=2 vs v2: A=4) for reproducibility?

**Decision**: **Explicit preprocessing_version field** in dataset metadata + manifest files:

```python
# In dataset HDF5 files
dataset.attrs['preprocessing_version'] = 'v2'
dataset.attrs['temporal_features'] = 'month_sin,month_cos'
dataset.attrs['created_at'] = '2026-03-05T12:00:00Z'

# In preprocessing manifest (JSON)
{
  "version": "v2",
  "changes": [
    "Added temporal features: month_sin, month_cos",
    "Action vector shape: [B, H, 2] → [B, H, 4]"
  ],
  "backward_compatible": true,
  "upgrade_path": "Reprocess with --version=v2 flag"
}
```

**Rationale**:
1. **Explicit tracking**: Version string in dataset attributes enables automatic compatibility checks
2. **Self-documenting**: Metadata describes what changed between versions
3. **Reproducibility**: Users can recreate exact preprocessing with `--version=v2` flag
4. **Error prevention**: Training code checks dataset version matches config expectation

**Alternatives Considered**:
- **Implicit versioning (filename)**: Rejected - fragile, doesn't survive copying/renaming
- **Hash-based versioning**: Rejected - opaque, doesn't describe what changed
- **No versioning**: Rejected - violates Constitution Principle V (Reproducible Pipelines)

**Implementation Pattern**:
```python
# In dataset loader
def load_dataset(path):
    with h5py.File(path, 'r') as f:
        version = f.attrs.get('preprocessing_version', 'v1')  # default v1 for old datasets
        if version == 'v1':
            # Load old schema: [rain_anom, temp_anom]
            actions = f['actions'][:]  # [B, H, 2]
        elif version == 'v2':
            # Load new schema: [rain_anom, temp_anom, month_sin, month_cos]
            actions = f['actions'][:]  # [B, H, 4]
        else:
            raise ValueError(f"Unknown preprocessing version: {version}")
    return actions
```

---

### Q4: Action Encoder Architecture Validation

**Question**: Does increasing input dimension from 2→4 require changing hidden layer sizes to maintain capacity?

**Decision**: **No architecture changes required** - keep hidden_dim=64, output_dim=128

**Rationale**:
1. **Sufficient capacity**: Linear(4→64) has 256 parameters (vs 128 for Linear(2→64))
   - Doubling input dims only adds 128 params, negligible vs total model size (~100M params)
   - Hidden layer (64 dims) can easily represent 4D input transformations

2. **Temporal features are simple**: Month_sin/cos are deterministic, periodic features
   - Not complex patterns requiring more capacity
   - Comparable to weather anomalies (also deterministic transformations)

3. **Empirical evidence**: Weather forecasting models (WeatherBench, Pangu-Weather) use similar action encoders with temporal features without capacity increases

4. **KISS principle**: Avoiding architectural changes reduces complexity, maintains backward compatibility

**Alternatives Considered**:
- **Increase hidden_dim to 128**: Rejected - doubles parameters for marginal benefit, violates "no parameter increase" constraint
- **Add extra MLP layer**: Rejected - unnecessary complexity, no evidence of capacity bottleneck
- **Separate encoders for weather vs temporal**: Rejected - over-engineered, temporal features are just another conditioning signal

**Validation Plan**: Monitor training loss - if temporal model shows higher loss than baseline despite convergence, revisit capacity question. Expected: no capacity issue.

---

### Q5: Seasonal Rollout Handling

**Question**: How to handle month encoding in multi-step rollouts crossing year boundaries (e.g., Nov→Dec→Jan)?

**Decision**: **Per-step month encoding** - each rollout step gets its own month_sin/cos based on target timestamp:

```python
# In dataset collation
def prepare_rollout_sequence(timestamps, weather_data, horizon=6):
    actions = []
    for t in range(horizon):
        target_month = timestamps[t].month
        month_sin = np.sin(2 * np.pi * target_month / 12)
        month_cos = np.cos(2 * np.pi * target_month / 12)

        action_t = np.array([
            weather_data[t]['rain_anom'],
            weather_data[t]['temp_anom'],
            month_sin,
            month_cos
        ])
        actions.append(action_t)

    return np.stack(actions)  # [H, 4]
```

**Rationale**:
1. **Matches reality**: Each prediction target has its own time-of-year context
2. **Handles year boundaries correctly**: Dec→Jan transition uses continuous sin/cos encoding
3. **Consistent with weather anomalies**: Weather also varies per step in rollout
4. **Enables "what-if" temporal scenarios**: Could explore "what if next 6 months were all summer?" by fixing month encoding

**Alternatives Considered**:
- **Single month for entire rollout**: Rejected - incorrect, loses temporal context for later steps
- **Relative month offset**: Rejected - breaks cyclic continuity, requires baseline month reference
- **Learnable progression**: Rejected - adds parameters, less interpretable

**Example**: Nov→Dec→Jan→Feb→Mar→Apr rollout:
```python
actions_rollout = [
    [rain_anom[0], temp_anom[0], sin(2π*11/12), cos(2π*11/12)],  # Nov
    [rain_anom[1], temp_anom[1], sin(2π*12/12), cos(2π*12/12)],  # Dec
    [rain_anom[2], temp_anom[2], sin(2π*1/12), cos(2π*1/12)],    # Jan (smooth transition!)
    [rain_anom[3], temp_anom[3], sin(2π*2/12), cos(2π*2/12)],    # Feb
    [rain_anom[4], temp_anom[4], sin(2π*3/12), cos(2π*3/12)],    # Mar
    [rain_anom[5], temp_anom[5], sin(2π*4/12), cos(2π*4/12)],    # Apr
]
```

---

## Summary of Decisions

1. **Temporal encoding**: Sine-cosine with annual period (2 dims)
2. **Backward compatibility**: Automatic weight padding in checkpoint loading
3. **Dataset versioning**: Explicit `preprocessing_version='v2'` in HDF5 attributes
4. **Architecture**: No changes to ActionEncoder hidden dims (capacity sufficient)
5. **Rollout handling**: Per-step month encoding based on target timestamps

**Implementation Confidence**: High - All decisions based on standard practices with strong theoretical foundations and empirical evidence from related domains (weather forecasting, time-series ML).

**Remaining Uncertainties**: None - All major design questions resolved. Ready for Phase 1 (data model + contracts).
