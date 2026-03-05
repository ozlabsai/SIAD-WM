# Temporal Conditioning Feature Specification

**Feature ID**: 003-temporal-conditioning
**Branch**: `003-003-temporal-conditioning`
**Status**: Planning
**Priority**: High
**Created**: 2026-03-05

## Problem Statement

The current SIAD world model transition is strictly Markov: `Z_{t+1} = F(Z_t, a_t)`, which means it cannot easily capture **strong annual periodicity** in Earth observation data. This leads to:

1. **False anomaly spikes** at seasonal transitions (e.g., summer→autumn vegetation changes flagged as anomalies)
2. **Unstable multi-step rollouts** when crossing seasonal boundaries
3. **Poor modeling** of predictable seasonal dynamics (vegetation cycles, snow cover, lighting changes)

The model treats normal seasonal changes as anomalies because it lacks explicit temporal context beyond the single latent state Z_t.

## User Scenarios & Testing

### User Story 1 - Seasonal Transition Accuracy (Priority: P1)

**As a** satellite imagery analyst  
**I want** the model to not flag normal seasonal vegetation changes as anomalies  
**So that** I can focus on actual infrastructure changes

**Why this priority**: Core value proposition - reduces false positives that waste analyst time

**Independent Test**: Run model on summer→autumn transition pairs, verify residual heatmaps show low values for unchanged infrastructure

**Acceptance Scenarios**:

1. **Given** a tile with stable infrastructure but changing vegetation (summer→autumn)  
   **When** the model predicts the autumn state from summer  
   **Then** residual heatmap shows low values (<0.3) in infrastructure regions

2. **Given** seasonal transition samples (winter→spring, summer→autumn)  
   **When** comparing baseline model vs temporal-conditioned model  
   **Then** temporal model shows >20% reduction in false anomaly flags

### User Story 2 - Multi-Step Rollout Stability (Priority: P2)

**As a** researcher running long-horizon predictions  
**I want** the model to maintain prediction quality across seasonal boundaries  
**So that** I can trust 6-month forecasts

**Why this priority**: Enables longer prediction horizons, critical for planning applications

**Independent Test**: Run 6-step rollouts crossing seasonal boundaries, measure rollout error degradation

**Acceptance Scenarios**:

1. **Given** a starting state in November  
   **When** rolling out 6 months (Nov→Apr, crossing winter)  
   **Then** rollout error at step 6 is <15% higher than step 1 (vs >30% for baseline)

2. **Given** rollouts crossing all seasonal transitions  
   **When** measuring per-step error accumulation  
   **Then** temporal model shows smoother error growth curve

### User Story 3 - Training Efficiency (Priority: P3)

**As a** model trainer  
**I want** to add temporal features without increasing training time  
**So that** iteration speed remains fast

**Why this priority**: Operational constraint - ensures feature doesn't slow down research

**Independent Test**: Measure training throughput (samples/sec) before and after temporal features

**Acceptance Scenarios**:

1. **Given** baseline training configuration  
   **When** adding temporal features (month_sin/cos)  
   **Then** training throughput decreases by <5%

2. **Given** model parameter count  
   **When** adding temporal conditioning  
   **Then** parameter count remains unchanged (temporal features reuse existing action encoder)

### Edge Cases

- **December→January transitions**: Cyclical encoding (sin/cos) should handle year boundary smoothly
- **Missing timestamp metadata**: System should fail fast with clear error if month cannot be extracted
- **Equatorial regions with minimal seasonality**: Temporal features should not hurt performance (model learns to ignore)
- **Multi-year rollouts**: Month encoding repeats cyclically (expected behavior)

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract month from timestamp metadata for each sample
- **FR-002**: System MUST compute month_sin = sin(2π * month / 12) and month_cos = cos(2π * month / 12)
- **FR-003**: System MUST extend action vector from [rain_anom, temp_anom] to [rain_anom, temp_anom, month_sin, month_cos]
- **FR-004**: System MUST update action encoder input dimension from 2 to 4
- **FR-005**: System MUST preserve existing action conditioning pathways (action token + FiLM modulation)
- **FR-006**: System MUST handle rollout sequences where each step has its own month encoding
- **FR-007**: System MUST bump preprocessing_version to "v2" to track schema change
- **FR-008**: System MUST maintain backward compatibility (load old checkpoints with action_dim=2)

### Key Entities

- **Temporal Features**: (month_sin, month_cos) tuple representing time-of-year cyclically
- **Extended Action Vector**: [B, 4] tensor containing [weather_anomalies, temporal_features]
- **Action Encoding**: u_t [B, 128] representing conditioned action embedding (unchanged architecture)
- **Rollout Sequence**: a_seq [B, H, 4] containing temporal features for each future step

## Success Criteria

### M1: Temporal Feature Integration

**Measurable Outcomes**:

- **SC-001**: Action vector shape is [B, 4] in all data loader outputs
- **SC-002**: Rollout error on seasonal transition samples decreases by >10% vs baseline
- **SC-003**: False anomaly rate decreases by >20% during known seasonal transitions (spring equinox, fall equinox)
- **SC-004**: Training time per epoch increases by <5%
- **SC-005**: Model parameter count remains unchanged

**Acceptance Tests**:

1. **Shape Contract Test**: 
   - Input: batch with 8 samples, horizon 6
   - Expected: a_seq.shape == [8, 6, 4]
   - Expected: month_sin/cos values in valid range [-1, 1]

2. **Seasonal Stability Test**:
   - Input: 100 summer→autumn transition pairs
   - Baseline: Mean residual = 0.45
   - Temporal: Mean residual < 0.36 (20% reduction)

3. **Ablation Test**:
   - Train two models: baseline (A=2) vs temporal (A=4)
   - Measure: Rollout error at step 6 across seasons
   - Expected: Temporal model shows <50% of baseline's seasonal variance

### M2: Validation & Deployment

**Measurable Outcomes**:

- **SC-006**: All unit tests pass (shape contracts, encoder tests)
- **SC-007**: Integration test with 1k samples completes without errors
- **SC-008**: Configuration schema validates action_dim=4
- **SC-009**: Documentation includes temporal feature usage guide
- **SC-010**: Old checkpoints load successfully (backward compatibility)

## Technical Design

### 1. Temporal Feature Encoding

Add two deterministic features to encode month-of-year cyclically:

```python
month = datetime.month  # 1-12
month_sin = sin(2π * month / 12)
month_cos = cos(2π * month / 12)
```

**Rationale**: Encodes annual cyclic structure without discontinuities between December and January.

**Example values**:
| Month | sin | cos   |
|-------|-----|-------|
| Jan   | 0.5 | 0.866 |
| Apr   | 1.0 | 0     |
| Jul   | 0   | -1    |
| Oct   | -1  | 0     |

### 2. Action Vector Extension

**Current schema**:
```python
a_t = [rain_anom, temp_anom]  # A=2
```

**New schema**:
```python
a_t = [rain_anom, temp_anom, month_sin, month_cos]  # A=4
```

**Configuration update**:
```yaml
actions:
  input_dim: 4  # was 2
  encoded_dim: 128
  film: true
  action_token: true
```

### 3. Architecture Integration

**No architectural changes required**. Temporal features flow through existing Action Encoder `hφ`:

**Action Encoder**:
```
Input: a_t [B, 4]  # was [B, 2]
Architecture:
  Linear(4 → 64) + SiLU  # was Linear(2 → 64)
  Linear(64 → 128) + SiLU
Output: u_t [B, 128]
```

**Conditioning pathways** (unchanged):
1. **Action Token**: `u_proj = Linear(128 → 512)`, append to sequence
2. **FiLM Modulation**: For each transformer block: `(γℓ, βℓ) = MLP(u_t)`, then `x = (1 + γℓ) * x + βℓ`

### 4. Data Pipeline Changes

**Dataset schema change**:

**Before**:
```python
{
  "obs_context": [B, C, H, W],
  "obs_targets": [B, horizon, C, H, W],
  "actions_rollout": [B, horizon, 2]  # [rain_anom, temp_anom]
}
```

**After**:
```python
{
  "obs_context": [B, C, H, W],
  "obs_targets": [B, horizon, C, H, W],
  "actions_rollout": [B, horizon, 4],  # [rain_anom, temp_anom, month_sin, month_cos]
  "timestamps": [B, horizon+1]  # metadata for debugging
}
```

**Rollout sequences**: Each step includes its own month encoding:
```python
# Example: Nov→Dec→Jan→Feb→Mar→Apr
actions_rollout[0, :, 2:4] = [
  [sin(2π*11/12), cos(2π*11/12)],  # November
  [sin(2π*12/12), cos(2π*12/12)],  # December
  [sin(2π*1/12), cos(2π*1/12)],    # January
  [sin(2π*2/12), cos(2π*2/12)],    # February
  [sin(2π*3/12), cos(2π*3/12)],    # March
  [sin(2π*4/12), cos(2π*4/12)],    # April
]
```

### 5. Training Strategy

**No change to JEPA objective**:
```python
Z0 = encoder(X_t)
Z_pred = rollout(Z0, a_seq, H)
Z_star = target_encoder(X_{t+1..t+H})
Loss = distance(Z_pred, Z_star)
```

Temporal features simply make the prediction **better conditioned**.

## Implementation Phases

### Phase 1: Data Pipeline (M1.1)
- Extract month from timestamps in dataset preprocessing
- Compute month_sin/month_cos for each sample
- Update dataset collate function to include temporal features
- Bump preprocessing_version to "v2"
- Unit tests for temporal feature extraction

### Phase 2: Model Integration (M1.2)
- Update ActionEncoder input dimension to 4
- Update configuration schema (actions.input_dim)
- Verify shape contracts in forward pass
- Unit tests for action encoder with new input shape

### Phase 3: Testing & Validation (M1.3)
- Shape contract tests (action vector [B, H, 4])
- Seasonal stability tests (summer→autumn residuals)
- Ablation study (baseline vs temporal-conditioned)
- Integration test with full training loop

### Phase 4: Deployment (M2)
- Update documentation with temporal feature guide
- Configuration migration guide (v1→v2)
- Checkpoint compatibility verification
- Example training configs

## Risk Assessment

### Low Risk
- Does not change model architecture (only input dimension)
- Uses deterministic features (no added noise)
- Extremely common technique in time-series models
- Backward compatible (old checkpoints load, just ignore temporal features)

### Possible Minor Risk
If model overfits month encoding, it may learn "July always looks like X" instead of "July + spatial context → X". However, this is unlikely because:
- Spatial tokens (256 tokens × 512 dims = 131k dims) dominate representation
- Temporal features (4 dims in action encoding) are only 0.003% of representation
- Action encoding is shared across all spatial tokens (no per-token overfitting)

**Mitigation**: Monitor validation loss by season during training

## Expected Benefits

1. **Reduced false anomaly spikes** at seasonal transitions (target: >20% reduction)
2. **More stable multi-step rollouts** across seasons (target: <15% error growth at step 6)
3. **Better modeling** of vegetation and lighting cycles (qualitative improvement in residuals)
4. **No increase** in model size (0 new parameters) or compute cost (<5% training time increase)

## Dependencies

- Existing SIAD world model implementation (`src/siad/model/`)
- Dataset with timestamp metadata (`src/siad/data/dataset.py`)
- Configuration system (`src/siad/config/schema.py`)
- Training loop (`src/siad/train/trainer.py`)

## References

- Original improvement plan: `docs/improvment_plan/temporal_conditioning.md`
- Related: Seasonal baseline implementation in `src/siad/detect/baselines.py`
- Related: Action conditioning architecture in `src/siad/model/transition.py`
