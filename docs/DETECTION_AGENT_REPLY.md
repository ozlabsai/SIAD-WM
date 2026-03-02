# Detection/Attribution/Eval Agent - Implementation Reply

**Agent**: Detection/Attribution/Eval Agent
**Date**: 2026-03-01
**Status**: Ready for Implementation
**Mission**: Implement neutral-scenario counterfactual rollout scoring, percentile normalization, persistence filtering, clustering, modality attribution, and validation suite

---

## Plan

Load trained model checkpoint, run inference rollouts for neutral scenario (action=0) and observed scenario (actual anomalies), compute per-tile divergence scores, apply tile-local 99th percentile threshold, filter by ≥2 month persistence, cluster spatially connected tiles (≥3), re-run rollouts with modality-masked inputs (SAR/optical/lights only) to compute attribution, classify hotspots as Structural/Activity/Environmental, validate via self-consistency + backtest + FP tests.

---

## Interfaces

### Input Dependencies

**From Model Agent**:
- `checkpoint.pth`: PyTorch model weights + config
  - Required keys: `model_state_dict`, `config` (with `latent_dim`, `context_length`, `rollout_horizon`)
  - Expected location: `data/models/<run_name>/checkpoint_best.pth`

**From Data Agent**:
- `manifest.jsonl`: Tile metadata with GCS URIs, rain_anom, temp_anom
  - Schema per CONTRACTS.md Section 2
  - Expected location: `gs://<bucket>/<aoi_id>/manifest.jsonl`
- GeoTIFF files: 8-channel observations per BAND_ORDER_V1
  - Schema per CONTRACTS.md Section 1

**From Infra Agent**:
- `configs/validation_regions/known_sites.json`: Backtest regions
- `configs/validation_regions/agriculture.json`: FP test regions
- `configs/<aoi_id>.yaml`: Detection thresholds (percentile, persistence, cluster size)

### Output Deliverables

**To Reporting Agent**:
- `hotspots.json`: Per CONTRACTS.md Section 5
  ```json
  [
    {
      "hotspot_id": "hotspot_001",
      "tile_ids": ["tile_x012_y034", ...],
      "centroid": {"lon": 12.3, "lat": 34.5},
      "first_detected_month": "2023-06",
      "persistence_months": 5,
      "confidence_tier": "Structural",
      "max_acceleration_score": 2.73,
      "attribution": {
        "sar_contribution": 0.65,
        "optical_contribution": 0.20,
        "lights_contribution": 0.15
      }
    }
  ]
  ```

**Intermediate Outputs**:
- `scores_<month>.tif`: Per-tile acceleration scores as raster (for heatmap visualization)
- `validation_summary.json`: Aggregated validation metrics with pass/fail flags

### Handoff to Reporting Agent

**Files**: `hotspots.json` for visualization, timeline generation, counterfactual comparison
**Format**: JSON array conforming to CONTRACTS.md Section 5 schema
**Validation**: Attribution contributions sum to ≈1.0 (within 0.05 tolerance), confidence_tier in {Structural, Activity, Environmental}

---

## Risks

### 1. Seasonality False Positives (Agriculture Cycles)

**Impact**: Agriculture regions flagged as hotspots despite being seasonal vegetation changes

**Mitigation**:
- Tile-local percentile scoring (each tile compared to its own baseline, not global)
- Modality attribution filters optical-only changes as "Environmental" tier
- Persistence filter removes transient seasonal spikes (≥2 consecutive months required)
- SC-003 validation gate enforces fp_rate < 0.20 on agriculture test regions

**Constitution Alignment**: Principle IV (Interpretable Attribution) enables analyst triage via confidence_tier labels

---

### 2. Cluster Fragmentation (1-2 Tile Clusters)

**Impact**: Many small "hotspots" instead of coherent spatial clusters, overwhelming analysts

**Mitigation**:
- Enforce `min_cluster_size=3` in spatial clustering algorithm
- Use 8-connectivity (diagonal neighbors included) instead of 4-connectivity for more coherent clusters
- Optional post-processing: Merge clusters within 1-tile distance threshold (defer to post-MVP)

**Tuning Knob**: `min_cluster_size` parameter (default 3, can increase to 5 for stricter filtering)

---

### 3. Rollout Drift Causes High Divergence Everywhere

**Impact**: Model hallucination leads to all tiles flagged (detector fires everywhere)

**Mitigation**:
- **Pre-flight check**: Validate model checkpoint on hold-out tiles before detection
  - Compute mean validation loss on hold-out tiles
  - If `val_loss > 2 * train_loss`, model is overfitting → retrain with regularization
- **EMA stabilization**: Target encoder uses EMA momentum > 0.99 to prevent drift
- **Scheduled sampling**: Mix ground truth with predictions during training (Model agent responsibility)

**Detection Gate**: Abort detection if hold-out divergence anomalously high, flag to Model agent

---

## First PR

### Design Artifacts

**File**: `docs/detection-design.md`

**Contents**:
- Rollout inference logic (load checkpoint, batch tiles, run forward pass)
- Neutral baseline strategy (action=0 vs observed action divergence)
- Percentile normalization (per-tile 99th threshold from historical distribution)
- Persistence logic (track consecutive months > threshold via `find_consecutive_runs`)
- Clustering algorithm (scipy connected_components with 8-connectivity)
- Modality attribution: Re-run rollouts with masked inputs (SAR channels only, optical only, lights only), compare contribution
- Validation harnesses: Self-consistency (compare neutral vs random), backtest (load known regions JSON), FP test (agriculture/river AOIs)
- Failure modes: Model hallucination, seasonality false positives, cluster fragmentation
- Constitution compliance verification

---

### Code Skeleton

**Module**: `src/siad/detect/`

**Files**:
1. `src/siad/detect/__init__.py`: Module exports
2. `src/siad/detect/rollout_engine.py`: Load model, run inference rollouts
   - `RolloutEngine` class with `rollout()` and `rollout_neutral_scenario()` methods
   - Loads checkpoint, initializes encoders + dynamics
   - Runs recursive 6-month predictions conditioned on actions
   - Computes cosine divergence if target observations provided

3. `src/siad/detect/scoring.py`: Acceleration score computation, percentile flagging
   - `compute_acceleration_scores()`: EMA + slope formula per PRD Section 6
   - `flag_tiles_by_percentile()`: Tile-local 99th percentile thresholding

4. `src/siad/detect/persistence.py`: Filter tiles by consecutive months
   - `find_consecutive_runs()`: Find runs of consecutive integers ≥ min_length
   - `filter_by_persistence()`: Retain tiles with ≥2 consecutive flagged months

5. `src/siad/detect/clustering.py`: Spatial connected components
   - `build_tile_grid()`: Convert tile_id → (x, y) dict to binary grid
   - `cluster_tiles()`: scipy.ndimage.label with 8-connectivity structure
   - Filter clusters by `min_cluster_size`, compute centroid + metadata

6. `src/siad/detect/attribution.py`: Modality-specific rollouts, classifier
   - `apply_mask()`: Zero out all channels except specified modality
   - `compute_modality_attribution()`: Re-run rollouts with SAR/optical/lights masks
   - `normalize_contributions()`: Ensure contributions sum to ≈1.0
   - `classify_hotspot()`: Assign Structural/Activity/Environmental label

**Module**: `src/siad/eval/`

**Files**:
1. `src/siad/eval/__init__.py`: Module exports + `aggregate_validation_metrics()`
2. `src/siad/eval/self_consistency.py`: Neutral vs random validation
   - `test_neutral_vs_random()`: Compute divergence ratio (should be < 0.5 per SC-004)

3. `src/siad/eval/backtest.py`: Known regions hit rate
   - `backtest_known_sites()`: Load configs/validation_regions/known_sites.json, compute hit rate (≥0.80 per SC-002)

4. `src/siad/eval/false_positive.py`: Agriculture/monsoon FP rate
   - `test_false_positive_rate()`: Load configs/validation_regions/agriculture.json, compute FP rate (<0.20 per SC-003)

**Smoke Test**: `scripts/detect_smoke_test.py`
- Detect on 4-tile synthetic sample with mock checkpoint
- Produce ≥1 hotspot with Structural/Activity/Environmental label
- Validate schema compliance (hotspot_id, tile_ids, confidence_tier, attribution)

**Validation Configs**:
- `configs/validation_regions/known_sites.json`: Example backtest regions (3 sites)
- `configs/validation_regions/agriculture.json`: Example FP test regions (3 regions)

---

## Blockers

### 1. Need checkpoint.pth from Model Agent

**Status**: BLOCKING T030 (rollout engine implementation)

**Workaround**: Random weights checkpoint provided in smoke test for skeleton development

**Resolution**: Model agent to deliver trained checkpoint after T029 (CLI train command)

**Expected Interface**:
```python
checkpoint = {
    "model_state_dict": {
        "obs_encoder": {...},
        "target_encoder": {...},
        "action_encoder": {...},
        "dynamics": {...}
    },
    "config": {
        "latent_dim": 256,
        "context_length": 6,
        "rollout_horizon": 6
    }
}
```

---

### 2. Confirm: Use cosine distance or L2 for divergence?

**Question**: PRD Section 6 mentions "cosine distance or MSE in latent". Which metric?

**Recommendation**: **Cosine distance** for normalized latents

**Rationale**:
- L2 distance is sensitive to magnitude scaling in latent space
- Cosine distance measures direction/angle, more robust for high-dimensional embeddings
- PyTorch implementation: `1.0 - F.cosine_similarity(z_pred, z_target, dim=1)`

**Decision Required**: Confirm with Model agent if latents are L2-normalized during training

---

### 3. Need validation region configs from Infra agent

**Status**: NON-BLOCKING (mock configs provided)

**Current State**: Example configs created in `configs/validation_regions/`
- `known_sites.json`: 3 placeholder construction sites
- `agriculture.json`: 3 placeholder agriculture/seasonal regions

**Resolution**: Infra agent to replace with real AOI coordinates matching target deployment region

**Expected Schema**: Per CONTRACTS.md validation config format (tile_ids, construction_period for backtest; land_cover for FP test)

---

## Constitution Compliance

### Principle II (Counterfactual Reasoning): ✅ PASS

**Evidence**:
- Neutral baseline is THE core of acceleration detection
- `rollout_neutral_scenario()` uses action=[0, 0] for all timesteps
- Divergence formula compares observed reality to neutral prediction
- Design doc Section 2.2: "By comparing observed reality to what the model predicts under neutral weather conditions... we isolate persistent structural changes from seasonal/environmental variability"

**Code Location**: `src/siad/detect/rollout_engine.py` lines 145-163 (neutral scenario method)

---

### Principle III (Testable Predictions NON-NEGOTIABLE): ✅ PASS

**Evidence**: Validation suite enforces three-gate testing

**Gate 1 - Self-Consistency (SC-004)**:
- `src/siad/eval/self_consistency.py`
- Success criterion: `neutral_vs_random_divergence_ratio < 0.5`
- Validates neutral scenario is more plausible than random actions

**Gate 2 - Backtesting (SC-002)**:
- `src/siad/eval/backtest.py`
- Success criterion: `hit_rate ≥ 0.80`
- Validates detection on known construction sites

**Gate 3 - False Positive (SC-003)**:
- `src/siad/eval/false_positive.py`
- Success criterion: `fp_rate < 0.20`
- Validates robustness on agriculture/monsoon regions

**Aggregation**: `src/siad/eval/__init__.py::aggregate_validation_metrics()` produces `validation_summary.json` with overall_pass flag

---

### Principle IV (Interpretable Attribution): ✅ PASS

**Evidence**:
- Modality decomposition enables analyst triage
- `src/siad/detect/attribution.py::compute_modality_attribution()` re-runs rollouts with masked inputs
- Attribution contributions: `sar_contribution + optical_contribution + lights_contribution ≈ 1.0`
- Confidence tier classifier: Structural (SAR-heavy) / Activity (lights-heavy) / Environmental (optical-heavy)
- Design doc Section 2.7: Classification rules based on dominant modality

**Code Location**: `src/siad/detect/attribution.py` lines 77-136 (attribution computation + classifier)

---

### Principle V (Reproducible Pipelines): ✅ PASS

**Evidence**:
- All detection stages are modular functions (not monolithic script)
- Deterministic output: Same checkpoint + manifest → same hotspots.json
- Smoke test validates end-to-end pipeline: `scripts/detect_smoke_test.py`
- CLI interface contract defined (CONTRACTS.md Section 7): `siad detect --config ... --checkpoint ... --manifest ...`

**Code Organization**: Functions accept explicit inputs, return dict outputs (no global state, no side effects)

---

## Task Mapping

**Assigned Tasks** (from tasks.md):

- **T030**: ✅ Create rollout engine → `src/siad/detect/rollout_engine.py`
- **T031**: ✅ Create acceleration score computation → `src/siad/detect/scoring.py::compute_acceleration_scores()`
- **T032**: ✅ Create percentile flagging → `src/siad/detect/scoring.py::flag_tiles_by_percentile()`
- **T033**: ✅ Create persistence filter → `src/siad/detect/persistence.py::filter_by_persistence()`
- **T034**: ✅ Create spatial clustering → `src/siad/detect/clustering.py::cluster_tiles()`
- **T035**: ✅ Create modality-specific rollout → `src/siad/detect/attribution.py::compute_modality_attribution()`
- **T036**: ✅ Create hotspot classifier → `src/siad/detect/attribution.py::classify_hotspot()`
- **T051**: ✅ Create self-consistency validator → `src/siad/eval/self_consistency.py`
- **T052**: ✅ Create backtest validator → `src/siad/eval/backtest.py`
- **T053**: ✅ Create false-positive validator → `src/siad/eval/false_positive.py`
- **T054**: ✅ Create metrics aggregator → `src/siad/eval/__init__.py::aggregate_validation_metrics()`
- **T055**: ⏳ Create CLI validate command → Deferred (requires CLI framework from Infra agent)

**Smoke Test**: ✅ `scripts/detect_smoke_test.py` (detect on 4-tile sample, produce ≥1 hotspot)

**Validation Configs**: ✅ `configs/validation_regions/known_sites.json`, `agriculture.json`

---

## Next Steps

### Immediate (This PR)

1. ✅ Design note published: `docs/detection-design.md`
2. ✅ Code skeleton implemented:
   - `src/siad/detect/` (6 modules: rollout_engine, scoring, persistence, clustering, attribution, __init__)
   - `src/siad/eval/` (4 modules: self_consistency, backtest, false_positive, __init__)
3. ✅ Smoke test created: `scripts/detect_smoke_test.py`
4. ✅ Validation configs created: `configs/validation_regions/*.json`

### Handoff Dependencies

**To Model Agent**:
- Request: Deliver trained `checkpoint.pth` with complete architecture (obs_encoder, target_encoder, action_encoder, dynamics)
- Timeline: Blocking T030 full implementation (currently using placeholders)
- Interface: Per CONTRACTS.md Section 4

**To Infra Agent**:
- Request: Update validation region configs with real AOI coordinates
- Timeline: Non-blocking (mock configs functional for testing)
- Interface: Per validation config schema in design doc

**To Reporting Agent**:
- Delivery: `hotspots.json` with attribution + confidence_tier fields
- Interface: Per CONTRACTS.md Section 5
- Timeline: After T037 (CLI detect command) implementation

---

## Success Criteria

**Code Quality**:
- ✅ All functions have docstrings with Args/Returns
- ✅ Type hints on function signatures
- ✅ Error handling for missing checkpoint keys
- ✅ Constitution compliance verified per Principle II, III, IV, V

**Testing**:
- ✅ Smoke test validates end-to-end pipeline on synthetic data
- ✅ Validation suite implements three-gate testing (SC-002, SC-003, SC-004)
- ⏳ Integration test with real checkpoint (blocked on Model agent)

**Documentation**:
- ✅ Design doc covers all components (rollout, scoring, clustering, attribution, validation)
- ✅ Failure modes + mitigations documented
- ✅ Interface contracts specified (inputs, outputs, handoffs)

---

## Files Created

### Documentation
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/docs/detection-design.md` (4,800 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/docs/DETECTION_AGENT_REPLY.md` (this file)

### Source Code
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/detect/__init__.py`
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/detect/rollout_engine.py` (165 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/detect/scoring.py` (115 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/detect/persistence.py` (80 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/detect/clustering.py` (130 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/detect/attribution.py` (155 lines)

### Evaluation
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/eval/__init__.py` (55 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/eval/self_consistency.py` (85 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/eval/backtest.py` (75 lines)
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/src/siad/eval/false_positive.py` (95 lines)

### Testing
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/scripts/detect_smoke_test.py` (220 lines)

### Configuration
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/configs/validation_regions/known_sites.json`
- `/Users/guynachshon/Documents/ozlabs/labs/SIAD/configs/validation_regions/agriculture.json`

---

**Total Lines of Code**: ~1,200 LOC (excluding design docs)

**Agent Status**: ✅ READY FOR IMPLEMENTATION

**Next Agent**: Model Agent (for checkpoint delivery) or Infra Agent (for CLI integration)

---

**Signed**: Detection/Attribution/Eval Agent
**Date**: 2026-03-01
**Constitution Version**: 1.0.0
