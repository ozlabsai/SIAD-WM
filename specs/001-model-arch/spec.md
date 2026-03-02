# Feature Specification: JEPA World Model Architecture

**Feature Branch**: `001-model-arch`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "Update SIAD World Model architecture to JEPA-centered token-based design with CNN stem, spatial tokens (16x16), transformer encoder/transition, EMA targets, and multi-step rollout"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Spatial Anomaly Detection with Heatmaps (Priority: P1)

Analysts need to identify **where** infrastructure changes are occurring within a geographic area, not just that changes happened somewhere in the tile. The updated model preserves spatial structure throughout prediction, enabling pixel-accurate anomaly heatmaps that show hotspots at 160m resolution.

**Why this priority**: Core value proposition - spatial localization is what differentiates this from simple change detection. Without spatial tokens, the model can only flag entire tiles, making it impossible to pinpoint construction sites within a 2.5km area.

**Independent Test**: Train model on synthetic data with known construction events at specific locations. Model must generate residual heatmaps showing elevated scores within 160m of ground truth locations, not uniform scores across entire tiles.

**Acceptance Scenarios**:

1. **Given** a tile with construction activity in northwest quadrant, **When** model generates anomaly heatmap, **Then** highest residual scores appear in northwest quadrant (within 160m accuracy)
2. **Given** multiple simultaneous construction sites in same tile, **When** model detects anomalies, **Then** heatmap shows distinct clusters at each site location
3. **Given** seasonal vegetation changes across entire tile, **When** model processes with neutral weather scenario, **Then** heatmap shows uniform low residuals (not flagged as anomalies)

---

### User Story 2 - Multi-Step Temporal Predictions (Priority: P1)

Analysts need to predict infrastructure evolution **6 months into the future** to anticipate accelerated development patterns. The model must maintain prediction accuracy across all 6 rollout steps, not just one month ahead.

**Why this priority**: Detection strategy depends on identifying **persistent** deviations over multiple months, which is the key signal for structural changes vs. transient events. Single-step prediction cannot capture acceleration patterns.

**Independent Test**: Train model on 24-month sequences. Withhold final 6 months. Evaluate prediction quality at each step (t+1 through t+6). Success = prediction accuracy degrades gracefully (not catastrophically) through t+6.

**Acceptance Scenarios**:

1. **Given** 6 months of historical context, **When** model rolls out 6-month prediction, **Then** prediction error at t+6 is within 2x of error at t+1
2. **Given** a gradual construction project spanning 4 months, **When** model predicts future states, **Then** predicted representations capture evolution trajectory (not sudden jumps)
3. **Given** stable infrastructure with no changes, **When** model predicts 6 months ahead, **Then** predicted states remain stable (low divergence from actual observations)

---

### User Story 3 - Counterfactual Weather Scenarios (Priority: P2)

Analysts need to separate **structural changes** (construction) from **environmental changes** (vegetation/water driven by weather). The model must support rolling out predictions under different weather scenarios (neutral, observed, extreme) to baseline expectations.

**Why this priority**: False positive reduction - without weather conditioning, drought-driven vegetation loss looks like anomalies. This enables attribution of changes to either structural or environmental causes.

**Independent Test**: Train model on region with known drought events. For tiles with only vegetation changes (no construction), run neutral vs. observed weather rollouts. Success = neutral rollout better predicts reality (lower residuals) than observed rollout with extreme drought actions.

**Acceptance Scenarios**:

1. **Given** a drought event causing vegetation loss, **When** model runs neutral (rain_anom=0) vs. drought (rain_anom=-2) scenarios, **Then** drought scenario predictions align better with observations
2. **Given** construction activity during normal weather, **When** comparing neutral vs. observed weather rollouts, **Then** both show high residuals (weather doesn't explain the change)
3. **Given** agricultural cycles with seasonal irrigation, **When** model uses neutral weather baseline, **Then** irrigation-driven changes are not flagged as anomalies

---

### User Story 4 - Representation Stability During Training (Priority: P2)

Training must produce stable, meaningful representations that don't collapse to trivial solutions (all zeros, all identical). The EMA target encoder prevents representation collapse during multi-step rollout training.

**Why this priority**: Model usability - collapsed representations make all predictions identical, rendering detection useless. Stable training is prerequisite for deployment.

**Independent Test**: Monitor representation variance across batch and tokens during training. Success = variance remains above threshold (>0.1) throughout training, and loss decreases steadily without sudden jumps.

**Acceptance Scenarios**:

1. **Given** training from random initialization, **When** model trains for 10K steps, **Then** representation std deviation stays above 0.1 across dimensions
2. **Given** multi-step rollout training (H=6), **When** monitoring loss curves, **Then** loss decreases monotonically without collapse spikes
3. **Given** trained model, **When** computing representations for diverse tiles, **Then** representations are distinct (cosine similarity <0.8 for unrelated locations)

---

### Edge Cases

- **What happens when satellite data has extensive cloud cover?** Model receives S2_valid_mask channel indicating pixel quality. Predictions must gracefully handle low-quality inputs without generating false anomalies.
- **How does model handle tiles with no historical changes?** Model should predict stable future states with low residuals. Success = minimal false positives on stable infrastructure regions.
- **What if actions (rain/temp) are extreme outliers?** Model training includes diverse weather scenarios. Predictions may degrade for never-seen extremes, but should not collapse or produce nonsensical outputs.
- **How does model perform at tile boundaries?** Each tile is processed independently. Boundary effects are handled by detection module's spatial clustering (outside model scope), but model should not produce artificial edge artifacts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Model MUST accept 8-channel satellite imagery tiles (256×256 pixels) with fixed band order: S2_B2, S2_B3, S2_B4, S2_B8, S1_VV, S1_VH, VIIRS, S2_valid_mask
- **FR-002**: Model MUST output spatial token grid of 16×16 (256 tokens) preserving geographic structure of input tile
- **FR-003**: Model MUST accept action vectors with rain anomaly (required) and temperature anomaly (optional) as scenario conditioning inputs
- **FR-004**: Model MUST perform multi-step rollout predictions for configurable horizon H (default H=6 months)
- **FR-005**: Model MUST provide stable target representations via exponential moving average (EMA) mechanism to prevent training collapse
- **FR-006**: Model MUST support deterministic predictions (no stochastic sampling) as baseline behavior
- **FR-007**: Model MUST generate per-token residual maps (16×16 grid) comparing predictions to observations for anomaly scoring
- **FR-008**: Model MUST support curriculum training with progressive horizon extension (e.g., H=1→3→6)
- **FR-009**: Model MUST maintain representation diversity across tokens and batch via anti-collapse regularization
- **FR-010**: Model MUST load hyperparameters from configuration files (no hardcoded architecture choices)
- **FR-011**: Model MUST provide encode(), transition(), and rollout() interfaces for training and inference workflows
- **FR-012**: Model MUST version input/output contracts (band order, token grid) to ensure data compatibility

### Key Entities

- **Observation Tile (X_t)**: Monthly satellite imagery composite for a 2.56km² geographic area, containing 8 spectral/structural channels at 10m resolution (256×256 pixels)

- **Spatial Token (z_i)**: 512-dimensional representation of a 16×16 pixel patch (≈160m²), preserving geographic position within tile. 256 tokens form 16×16 grid matching tile structure.

- **Action Vector (a_t)**: Monthly scenario conditioning inputs describing exogenous environmental stressors: rainfall anomaly (z-score) and optional temperature anomaly. Used for counterfactual rollouts.

- **Latent Token Grid (Z_t)**: 256 spatial tokens (16×16) at dimension 512, representing entire tile in latent space while preserving geographic structure for heatmap generation.

- **Rollout Sequence (Z_pred)**: Multi-step prediction of future latent token grids over H months, conditioned on action sequence. Used to establish expected evolution baseline.

- **Residual Map**: Per-token distance between predicted and observed latent representations, reshaped to 16×16 heatmap showing spatial anomaly scores at 160m resolution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Model generates anomaly heatmaps at 160m spatial resolution, enabling analysts to localize infrastructure changes within tiles (not just flag entire tiles)

- **SC-002**: Multi-step prediction accuracy degrades by less than 2x from step 1 to step 6, ensuring reliable 6-month rollout forecasts

- **SC-003**: Representation variance remains above 0.1 standard deviation throughout training, confirming stable learning without collapse

- **SC-004**: Weather-conditioned rollouts reduce false positives by 40% compared to unconditional predictions, measured on validation tiles with seasonal vegetation changes

- **SC-005**: Model training converges within 50K steps on 690 tiles × 36 months dataset, demonstrating computational feasibility

- **SC-006**: Trained model produces distinct representations (cosine similarity <0.8) for geographically unrelated tiles, confirming meaningful feature learning

- **SC-007**: All shape contract tests pass: encoder [B,8,256,256]→[B,256,512], transition [B,256,512]→[B,256,512], rollout outputs [B,H,256,512]

- **SC-008**: Deterministic forward pass produces identical outputs given same inputs and weights, ensuring reproducible predictions

## Assumptions *(mandatory)*

- Model operates on pre-processed tiles where satellite imagery is already composited to monthly cadence, cloud-masked, and normalized
- Training data contains at least 12 consecutive months per tile to support 6-month context + 6-month rollout sequences
- Action vectors (rain/temp anomalies) are pre-computed from climate data and provided as inputs, not generated by model
- Geographic coordinate transformations and tiling are handled upstream; model receives fixed 256×256 pixel inputs
- Model versioning and backward compatibility are managed via configuration version fields, not code branches
- Stochastic prediction capabilities are deferred to future phase; initial implementation is deterministic only
- Loss function uses cosine distance in latent space as default metric (configurable via settings)
- EMA momentum schedule (τ=0.99→0.995) follows JEPA best practices for representation learning stability
- Model does not perform pixel-level reconstruction or image generation; all predictions remain in latent space
- Spatial clustering for hotspot detection is handled by separate detection module, not model architecture

## Out of Scope *(mandatory)*

- Pixel-level reconstruction or generation of future satellite imagery (model predicts representations only)
- Real-time inference or streaming predictions (batch processing assumed)
- Global model training across multiple geographic regions (single AOI focus)
- Stochastic sampling and uncertainty quantification (deterministic baseline first)
- Temporal context beyond single-step Markov transition (no multi-month context encoders)
- Automatic hyperparameter tuning or neural architecture search (fixed architecture per MODEL.md)
- Integration with external APIs, data pipelines, or deployment infrastructure
- User interface or visualization tools for heatmaps (separate tooling)
- Model interpretability beyond residual heatmaps (no attention visualization, feature attribution)
- Transfer learning or pre-training on external satellite datasets

## Dependencies *(mandatory)*

- MODEL.md specification document defines authoritative architecture contract (version 0.2)
- Pre-processed satellite data export pipeline provides 690 tiles × 36 months training data in GCS bucket
- Configuration system supports YAML-based hyperparameter management
- Testing framework supports shape contracts, determinism checks, and training smoke tests
- PyTorch deep learning framework for model implementation (dependency requirement)
- Existing band order contract (BAND_ORDER_V1) must be preserved to maintain data compatibility

## Risks & Mitigations *(mandatory)*

**Risk**: Representation collapse during multi-step rollout training
**Impact**: Model produces identical predictions for all inputs, making detection useless
**Mitigation**: Mandatory anti-collapse regularizer (variance penalty) + EMA target encoder stabilization + monitor representation std deviation in training logs

**Risk**: Prediction accuracy degrades severely beyond t+3 rollout steps
**Impact**: Cannot reliably detect persistent 6-month acceleration patterns
**Mitigation**: Curriculum training (H=1→3→6 progressive extension) + cosine loss maintains angular separation better than MSE for long horizons

**Risk**: Model learns to rely on weather actions as primary signal instead of observations
**Impact**: Counterfactual scenarios become meaningless (neutral = observed predictions)
**Mitigation**: Design transition model with FiLM conditioning (multiplicative gating) + action token, ensuring actions modulate rather than replace observation features

**Risk**: Spatial token grid boundaries create artificial edge artifacts
**Impact**: Anomaly heatmaps show false positives at tile edges
**Mitigation**: Use positional embeddings at token level + evaluate edge vs. center token residual distributions during validation

**Risk**: Configuration complexity leads to mismatched hyperparameters
**Impact**: Training failures or suboptimal performance due to config errors
**Mitigation**: Single MODEL.md specification as source of truth + versioning system for config changes + automated shape contract tests catch mismatches early

**Risk**: Existing codebase has incompatible architecture (ResNet18 single-vector encoder)
**Impact**: Migration effort required to implement token-based architecture
**Mitigation**: Phased development (Phase 1: encoder, Phase 2: transition, Phase 3: loss, Phase 4: integration tests) + deprecate old model files cleanly

## Open Questions *(optional)*

*No open questions at this stage. All architectural decisions are specified in MODEL.md.*
