# Detection/Attribution/Eval Design

**Agent**: Detection/Attribution/Eval Agent
**Version**: 1.0.0
**Date**: 2026-03-01
**Owner**: Detection/Attribution/Eval Agent
**Dependencies**: Model Agent (checkpoint.pth), Data Agent (manifest.jsonl)

---

## 1. Overview

This module implements the core acceleration detection system for SIAD MVP. It takes a trained world model checkpoint and observed satellite data, then produces a ranked list of "hotspots" where infrastructure acceleration is detected through counterfactual reasoning.

**Key Innovation**: Instead of naive change detection, we use **neutral scenario counterfactual rollouts** as the baseline. By comparing observed reality to what the model predicts under neutral weather conditions (rain_anom=0, temp_anom=0), we isolate persistent structural changes from seasonal/environmental variability.

---

## 2. Architecture Components

### 2.1 Rollout Engine (`src/siad/detect/rollout_engine.py`)

**Purpose**: Load trained model checkpoint and run multi-step predictions conditioned on action sequences.

**Key Functions**:
```python
class RolloutEngine:
    def __init__(self, checkpoint_path: str):
        """Load model from checkpoint, set to eval mode."""

    def rollout(
        self,
        context_obs: np.ndarray,        # [L=6, C=8, H=256, W=256]
        actions: np.ndarray,            # [H=6, 2] (rain_anom, temp_anom)
        return_latents: bool = True
    ) -> dict:
        """
        Run 6-month rollout conditioned on actions.

        Returns:
            {
                "predicted_latents": [H=6, latent_dim],  # z_hat sequence
                "divergences": [H=6],                     # Optional: per-step loss if target obs provided
            }
        """
```

**Algorithm**:
1. Encode context observations into initial latent state: `z_0 = obs_encoder(context_obs[-1])`
2. For each rollout step k=1..6:
   - Encode action: `u_k = action_encoder(actions[k])`
   - Predict next latent: `z_hat_k = dynamics(z_{k-1}, u_k)`
   - Store predicted latent
3. Return sequence of predicted latents

**Model Loading**:
```python
checkpoint = torch.load(checkpoint_path, map_location=device)
config = checkpoint["config"]
latent_dim = config["latent_dim"]

# Reconstruct model architecture
obs_encoder = ObservationEncoder(in_channels=8, latent_dim=latent_dim)
action_encoder = ActionEncoder(action_dim=2, latent_dim=latent_dim)
dynamics = TransitionModel(latent_dim=latent_dim)

# Load weights
obs_encoder.load_state_dict(checkpoint["model_state_dict"]["obs_encoder"])
action_encoder.load_state_dict(checkpoint["model_state_dict"]["action_encoder"])
dynamics.load_state_dict(checkpoint["model_state_dict"]["dynamics"])
```

---

### 2.2 Acceleration Score Computation (`src/siad/detect/scoring.py`)

**Purpose**: Compute per-tile acceleration scores by comparing observed reality to neutral scenario predictions.

**Formula** (per PRD Section 6):
```
For each tile at time t:

1. Neutral rollout:
   z_hat_neutral[1..6] = rollout(context_obs, actions=zeros(6, 2))

2. Encode observed future:
   z_observed[1..6] = target_encoder(future_obs[1..6])

3. Divergence per step:
   divergence_k = cosine_distance(z_hat_neutral[k], z_observed[k])

4. Acceleration score:
   S_t = EMA(mean(divergence[1..6])) + lambda * slope(divergence[t-W:t])

   where:
   - EMA decay alpha = 0.2
   - lambda (slope weight) = 0.5
   - W (trend window) = 3 months
```

**Key Functions**:
```python
def compute_acceleration_scores(
    rollout_engine: RolloutEngine,
    tile_timeseries: dict,          # tile_id -> {obs: [T, 8, 256, 256], actions: [T, 2]}
    target_encoder: torch.nn.Module,
    ema_alpha: float = 0.2,
    slope_weight: float = 0.5,
    trend_window: int = 3
) -> dict:
    """
    Returns:
        {
            tile_id: {
                "scores": [T],              # Acceleration score per month
                "divergences": [T, H=6],    # Divergence matrix
                "percentile_99": float       # Tile-local 99th percentile
            }
        }
    """
```

**Implementation Notes**:
- Use `torch.nn.functional.cosine_similarity()` for divergence computation
- EMA implementation: `ema_t = alpha * value_t + (1 - alpha) * ema_{t-1}`
- Slope via linear regression on last W months: `np.polyfit(range(W), divergences[-W:], deg=1)[0]`
- Percentile computed over tile's own history (not global): `np.percentile(tile_scores, 99)`

---

### 2.3 Percentile Flagging (`src/siad/detect/scoring.py`)

**Purpose**: Flag tiles where acceleration score exceeds their own historical 99th percentile.

**Algorithm**:
```python
def flag_tiles_by_percentile(
    tile_scores: dict,              # tile_id -> {"scores": [T], "percentile_99": float}
    threshold_percentile: float = 99.0
) -> dict:
    """
    Returns:
        {
            tile_id: {
                "flagged_months": [month_indices],  # Indices where score > percentile
                "max_score": float
            }
        }
    """
```

**Rationale**: Tile-local percentile (vs global threshold) accounts for baseline variability across different land cover types. Urban tiles may have higher baseline scores than desert tiles.

---

### 2.4 Persistence Filter (`src/siad/detect/persistence.py`)

**Purpose**: Retain only tiles with ≥2 consecutive months above threshold (reduces transient noise).

**Algorithm**:
```python
def filter_by_persistence(
    flagged_tiles: dict,            # tile_id -> {"flagged_months": [indices]}
    min_consecutive: int = 2
) -> dict:
    """
    Returns:
        {
            tile_id: {
                "persistent_spans": [(start_idx, end_idx), ...],  # Consecutive month ranges
                "persistence_count": int
            }
        }
    """
```

**Implementation**:
```python
def find_consecutive_runs(indices: list, min_length: int) -> list:
    """Find runs of consecutive integers >= min_length."""
    if not indices:
        return []

    runs = []
    current_run = [indices[0]]

    for idx in indices[1:]:
        if idx == current_run[-1] + 1:
            current_run.append(idx)
        else:
            if len(current_run) >= min_length:
                runs.append((current_run[0], current_run[-1]))
            current_run = [idx]

    if len(current_run) >= min_length:
        runs.append((current_run[0], current_run[-1]))

    return runs
```

---

### 2.5 Spatial Clustering (`src/siad/detect/clustering.py`)

**Purpose**: Group ≥3 spatially connected tiles into hotspots (prevents 1-2 tile noise).

**Algorithm**:
```python
def cluster_tiles(
    persistent_tiles: dict,         # tile_id -> {"persistent_spans": [...]}
    tile_coords: dict,              # tile_id -> (x_idx, y_idx)
    min_cluster_size: int = 3,
    connectivity: str = "8"         # "8" for 8-connectivity, "4" for rook's case
) -> list:
    """
    Returns:
        [
            {
                "hotspot_id": "hotspot_001",
                "tile_ids": ["tile_x012_y034", ...],
                "centroid": {"lon": 12.3, "lat": 34.5},
                "first_detected_month": "2023-06",
                "persistence_months": 5
            },
            ...
        ]
    """
```

**Implementation Strategy**:
1. Build adjacency graph of persistent tiles (8-connectivity = diagonal neighbors included)
2. Run connected components via BFS/DFS or `scipy.ndimage.label`
3. Filter clusters with size < `min_cluster_size`
4. Compute cluster metadata:
   - `centroid`: Mean of tile center coordinates
   - `first_detected_month`: Earliest month across all tiles in cluster
   - `persistence_months`: Maximum persistence count across tiles

**Connected Components (8-connectivity)**:
```python
from scipy.ndimage import label

def build_tile_grid(tile_coords: dict) -> np.ndarray:
    """Convert tile_id -> (x, y) dict to binary grid."""
    max_x = max(coords[0] for coords in tile_coords.values())
    max_y = max(coords[1] for coords in tile_coords.values())
    grid = np.zeros((max_x + 1, max_y + 1), dtype=np.int32)

    for tile_id, (x, y) in tile_coords.items():
        grid[x, y] = 1

    return grid

# Use scipy's label with 8-connectivity structure
structure = np.ones((3, 3), dtype=int)  # 8-connectivity
labeled_grid, num_clusters = label(tile_grid, structure=structure)
```

---

### 2.6 Modality Attribution (`src/siad/detect/attribution.py`)

**Purpose**: Re-run rollouts with modality-masked inputs to decompose contribution from SAR/optical/lights.

**Rationale**: A hotspot flagged only by optical changes (NDVI) is likely agricultural/seasonal. A hotspot with strong SAR + lights changes is more likely structural/activity.

**Algorithm**:
```python
def compute_modality_attribution(
    rollout_engine: RolloutEngine,
    tile_timeseries: dict,          # tile_id -> {obs, actions}
    target_encoder: torch.nn.Module,
    hotspots: list                  # Cluster metadata from clustering step
) -> list:
    """
    For each hotspot, re-run rollouts with masked inputs:
    - SAR-only: Keep channels [4, 5] (S1_VV, S1_VH), zero others
    - Optical-only: Keep channels [0, 1, 2, 3] (S2 bands), zero others
    - Lights-only: Keep channel [6] (VIIRS), zero others

    Compute divergence for each modality rollout.

    Returns:
        Updated hotspots with "attribution" field:
        {
            "sar_contribution": float,      # Normalized divergence [0-1]
            "optical_contribution": float,
            "lights_contribution": float
        }
    """
```

**Modality Masks** (per BAND_ORDER_V1 from CONTRACTS.md):
```python
MODALITY_MASKS = {
    "sar": [4, 5],              # S1_VV, S1_VH
    "optical": [0, 1, 2, 3],    # S2_B2, S2_B3, S2_B4, S2_B8
    "lights": [6]               # VIIRS_avg_rad
}

def apply_mask(obs: np.ndarray, mask_channels: list) -> np.ndarray:
    """Zero out all channels except those in mask_channels."""
    masked_obs = np.zeros_like(obs)
    masked_obs[:, mask_channels, :, :] = obs[:, mask_channels, :, :]
    return masked_obs
```

**Contribution Normalization**:
```python
def normalize_contributions(divergences: dict) -> dict:
    """Ensure SAR + optical + lights ≈ 1.0."""
    total = sum(divergences.values()) + 1e-8  # Avoid div by zero
    return {k: v / total for k, v in divergences.items()}
```

---

### 2.7 Hotspot Classifier (`src/siad/detect/attribution.py`)

**Purpose**: Assign confidence tier based on dominant modality.

**Classification Rules**:
```python
def classify_hotspot(attribution: dict) -> str:
    """
    Assigns one of: "Structural" | "Activity" | "Environmental"

    Rules:
    - Structural: sar_contribution > 0.5 OR (sar_contribution > 0.3 AND lights_contribution > 0.2)
    - Activity: lights_contribution > 0.5 AND sar_contribution < 0.3
    - Environmental: optical_contribution > 0.5
    """

    sar = attribution["sar_contribution"]
    optical = attribution["optical_contribution"]
    lights = attribution["lights_contribution"]

    if sar > 0.5 or (sar > 0.3 and lights > 0.2):
        return "Structural"
    elif lights > 0.5 and sar < 0.3:
        return "Activity"
    else:
        return "Environmental"
```

**Rationale**:
- **Structural**: Persistent SAR changes indicate physical construction (buildings, roads, earthworks)
- **Activity**: Strong lights signal without SAR change suggests operational activity (existing infrastructure being used)
- **Environmental**: Optical-dominant changes are vegetation/water/seasonal (low priority for infrastructure detection)

---

## 3. Validation Suite

### 3.1 Self-Consistency (`src/siad/eval/self_consistency.py`)

**Purpose**: Verify that neutral scenario rollouts are more plausible than random actions (SC-004 from spec).

**Test**:
```python
def test_neutral_vs_random(
    rollout_engine: RolloutEngine,
    tile_timeseries: dict,
    target_encoder: torch.nn.Module,
    n_random_samples: int = 10
) -> dict:
    """
    For each tile:
    1. Compute divergence under neutral actions (zeros)
    2. Compute divergence under random actions (sampled from N(0, 1))
    3. Compare: neutral_divergence vs mean(random_divergences)

    Returns:
        {
            "neutral_vs_random_ratio": float,   # Should be < 0.5 per SC-004
            "per_tile_ratios": dict
        }
    """
```

**Success Criterion** (SC-004): `neutral_vs_random_ratio < 0.5`
(Neutral scenario should have lower divergence than random actions)

---

### 3.2 Backtesting (`src/siad/eval/backtest.py`)

**Purpose**: Validate against known construction regions (SC-002: hit_rate ≥ 0.80).

**Input Config** (`configs/validation_regions/known_sites.json`):
```json
{
  "validation_regions": [
    {
      "site_name": "Industrial_Zone_Alpha",
      "construction_period": ["2023-03", "2023-08"],
      "tile_ids": ["tile_x012_y034", "tile_x013_y034"]
    },
    {
      "site_name": "Port_Expansion_Beta",
      "construction_period": ["2023-01", "2023-06"],
      "tile_ids": ["tile_x020_y045"]
    }
  ]
}
```

**Test**:
```python
def backtest_known_sites(
    hotspots: list,                 # Detected hotspots from clustering
    validation_config: dict,        # Loaded from configs/validation_regions/*.json
    temporal_tolerance_months: int = 2
) -> dict:
    """
    For each known site:
    1. Check if any detected hotspot overlaps with site's tile_ids
    2. Check if detection month is within ±temporal_tolerance of construction_period

    Returns:
        {
            "hit_rate": float,              # Fraction of known sites flagged
            "known_sites_flagged": int,
            "known_sites_total": int,
            "details": [...]                # Per-site hit/miss details
        }
    """
```

**Success Criterion** (SC-002): `hit_rate ≥ 0.80`

---

### 3.3 False Positive Testing (`src/siad/eval/false_positive.py`)

**Purpose**: Measure FP rate on agriculture/monsoon regions (SC-003: fp_rate < 0.20).

**Input Config** (`configs/validation_regions/agriculture.json`):
```json
{
  "false_positive_regions": [
    {
      "region_name": "Rice_Paddies_North",
      "land_cover": "agriculture",
      "tile_ids": ["tile_x005_y010", "tile_x006_y010", ...]
    },
    {
      "region_name": "Monsoon_Floodplain_East",
      "land_cover": "seasonal_water",
      "tile_ids": ["tile_x030_y020", ...]
    }
  ]
}
```

**Test**:
```python
def test_false_positive_rate(
    hotspots: list,
    fp_config: dict,
    acceptable_tiers: list = ["Environmental"]  # These are acceptable FPs
) -> dict:
    """
    For each FP region:
    1. Count hotspots that overlap with region's tile_ids
    2. Exclude hotspots with confidence_tier in acceptable_tiers
    3. Compute FP rate = flagged_tiles / total_tiles

    Returns:
        {
            "fp_rate": float,               # Should be < 0.20 per SC-003
            "agriculture_hotspots": int,
            "agriculture_tiles_total": int,
            "details": [...]
        }
    """
```

**Success Criterion** (SC-003): `fp_rate < 0.20` (excluding "Environmental" tier flags)

---

### 3.4 Metrics Aggregator (`src/siad/eval/__init__.py`)

**Purpose**: Combine validation results into single summary JSON.

**Output** (`validation_summary.json`):
```json
{
  "timestamp": "2026-03-01T10:00:00Z",
  "checkpoint_path": "data/models/quickstart-v1/checkpoint_best.pth",
  "self_consistency": {
    "neutral_vs_random_divergence_ratio": 0.42,
    "pass": true
  },
  "backtest": {
    "hit_rate": 0.85,
    "known_sites_flagged": 17,
    "known_sites_total": 20,
    "pass": true
  },
  "false_positive": {
    "fp_rate": 0.14,
    "agriculture_hotspots": 3,
    "agriculture_tiles_total": 21,
    "pass": true
  },
  "overall_pass": true
}
```

---

## 4. Smoke Test (`scripts/detect_smoke_test.py`)

**Purpose**: End-to-end sanity check on minimal dataset (2 tiles, 12 months, produce 1 hotspot).

**Test Data**:
- Mock checkpoint with random weights
- 2 tiles × 12 months of synthetic observations
- Neutral actions (zeros)
- Expected output: 1 hotspot with ≥3 tiles (requires synthetic adjacent tiles)

**Assertions**:
```python
def test_detect_smoke():
    """Smoke test for detection pipeline."""

    # 1. Load mock checkpoint
    checkpoint = create_mock_checkpoint(latent_dim=64)
    engine = RolloutEngine(checkpoint_path="mock.pth")

    # 2. Generate synthetic tile timeseries
    tiles = generate_synthetic_tiles(n_tiles=4, n_months=12)

    # 3. Run detection pipeline
    scores = compute_acceleration_scores(engine, tiles, ...)
    flagged = flag_tiles_by_percentile(scores, threshold=95)  # Lower for smoke test
    persistent = filter_by_persistence(flagged, min_consecutive=2)
    hotspots = cluster_tiles(persistent, tile_coords, min_cluster_size=3)

    # 4. Assert output
    assert len(hotspots) >= 1, "Expected at least 1 hotspot"
    assert hotspots[0]["confidence_tier"] in ["Structural", "Activity", "Environmental"]
    assert len(hotspots[0]["tile_ids"]) >= 3

    print("✓ Smoke test passed: Detection pipeline functional")
```

---

## 5. Failure Modes & Mitigations

### 5.1 Model Hallucination (Rollout Drift)

**Symptom**: All tiles show high divergence (detector fires everywhere).

**Mitigation**:
1. Validate model checkpoint on hold-out tiles first: `val_loss < threshold`
2. Check EMA weight in target encoder is stabilizing (momentum > 0.99)
3. Use scheduled sampling during training if drift persists (mix ground truth with predictions)

**Detection Gate**: Before running detection, compute mean validation loss on hold-out tiles. If `val_loss > 2 * train_loss`, model is overfitting—retrain with regularization.

---

### 5.2 Seasonality False Positives

**Symptom**: Agriculture regions flagged as hotspots despite modality attribution.

**Mitigation**:
1. Tile-local percentile scoring (each tile compared to its own baseline, not global)
2. Modality attribution filters optical-only changes as "Environmental"
3. Persistence filter removes transient seasonal spikes (≥2 consecutive months)

**Validation**: SC-003 gate enforces `fp_rate < 0.20` on agriculture test regions.

---

### 5.3 Cluster Fragmentation

**Symptom**: Many 1-2 tile "hotspots" instead of coherent clusters.

**Mitigation**:
1. Enforce `min_cluster_size=3` in clustering
2. Use 8-connectivity (diagonal neighbors) instead of 4-connectivity
3. Optional: Merge clusters within distance threshold (e.g., ≤1 tile gap)

**Tuning Knob**: `min_cluster_size` parameter (default 3, can increase to 5 for stricter filtering).

---

### 5.4 Neutral Baseline Not Neutral

**Symptom**: Neutral scenario rollouts show unrealistic predictions (e.g., vegetation disappears).

**Root Cause**: Action encoder learned non-zero offset for "neutral" actions.

**Mitigation**:
1. Validate action encoder: `action_encoder(zeros(2)) ≈ zeros(latent_dim)`
2. Add regularization loss during training: `L_action = ||action_encoder(0) - 0||^2`
3. Re-check SC-004 gate: neutral scenario should have lower divergence than random

**Constitution Alignment**: Principle II (Counterfactual Reasoning) requires neutral baseline to be coherent.

---

## 6. Interfaces & Handoffs

### 6.1 Input Dependencies

**From Model Agent**:
- `checkpoint.pth` (PyTorch model weights + config)
- Expected keys: `model_state_dict`, `config` (with `latent_dim`, `context_length`, `rollout_horizon`)

**From Data Agent**:
- `manifest.jsonl` (tile metadata with GCS URIs, rain_anom, temp_anom)
- GeoTIFF files in `gs://<bucket>/<aoi_id>/*.tif` (8-channel observations per BAND_ORDER_V1)

**From Infra Agent**:
- `configs/validation_regions/known_sites.json` (backtest regions)
- `configs/validation_regions/agriculture.json` (FP test regions)
- `configs/<aoi_id>.yaml` (detection thresholds: percentile, persistence, cluster size)

---

### 6.2 Output Deliverables

**To Reporting Agent**:
- `hotspots.json` (per CONTRACTS.md Section 5):
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

---

## 7. CLI Interface

**Command**: `siad detect` (per CONTRACTS.md Section 7)

```bash
siad detect \
  --config configs/quickstart-demo.yaml \
  --checkpoint data/models/quickstart-v1/checkpoint_best.pth \
  --manifest gs://siad-exports/siad/quickstart-demo/manifest.jsonl \
  --output data/outputs/quickstart-demo \
  --scenarios neutral,observed \
  --dry-run
```

**Parameters**:
- `--config`: Path to AOI config YAML (detection thresholds)
- `--checkpoint`: Path to trained model checkpoint
- `--manifest`: Path to manifest.jsonl (tile metadata + actions)
- `--output`: Output directory for hotspots.json + score rasters
- `--scenarios`: Comma-separated scenario names (neutral, observed, custom)
- `--dry-run`: Validate inputs without running inference

**Outputs**:
- `{output}/hotspots.json`
- `{output}/scores_*.tif` (one raster per month)
- `{output}/attribution_debug.json` (optional: per-hotspot modality divergences)

---

## 8. Constitution Compliance

**Principle II (Counterfactual Reasoning)**: ✅
- Neutral scenario rollout (`action=[0, 0]`) is THE core baseline for acceleration detection
- Divergence computation compares observed reality to neutral prediction
- Attribution validates robustness across scenarios

**Principle III (Testable Predictions NON-NEGOTIABLE)**: ✅
- Self-consistency gate (SC-004): neutral vs random divergence ratio < 0.5
- Backtest gate (SC-002): hit_rate ≥ 0.80 on known construction sites
- False-positive gate (SC-003): fp_rate < 0.20 on agriculture regions
- All three gates enforced before deployment

**Principle IV (Interpretable Attribution)**: ✅
- Modality decomposition (SAR/optical/lights) enables analyst triage
- Confidence tier labels (Structural/Activity/Environmental) provide defensible classifications
- Attribution contributions sum to ≈1.0 per contract validation rule

**Principle V (Reproducible Pipelines)**: ✅
- All detection stages scriptable via CLI (rollout → scoring → clustering → attribution)
- Deterministic output (same checkpoint + manifest → same hotspots.json)
- Smoke test validates end-to-end pipeline on minimal dataset

---

## 9. Performance Considerations

**Inference Speed**:
- Single tile rollout (6 months): ~10ms on GPU (batch size 1)
- 400 tiles × 36 months: ~400 × 30 = 12,000 rollouts → ~2 minutes total
- Modality attribution adds 3× overhead (SAR/optical/lights masks) → ~6 minutes
- **Target**: Full detection pipeline < 10 minutes for 50×50km AOI

**Memory**:
- Model checkpoint: ~100 MB (ConvNet encoder + transformer dynamics)
- Tile observations in RAM: 400 tiles × 36 months × 8 channels × 256×256 × 4 bytes ≈ 9.5 GB
- **Mitigation**: Use HDF5 memory-mapped datasets (load on-demand per tile)

**GPU Utilization**:
- Batch rollouts across tiles (batch_size=16) for 10× speedup
- Use mixed precision (float16) if memory constrained

---

## 10. Open Questions & TODOs

### Blockers

**Q1**: Confirm divergence metric choice: cosine distance or L2?
**A**: **Cosine distance recommended** for normalized latents (per PRD Section 6). L2 is sensitive to magnitude, while cosine measures direction in latent space.

**Q2**: Need validation region configs from Infra agent.
**A**: **Mock configs provided** in `configs/validation_regions/` for skeleton. Infra agent to replace with real AOI coordinates.

**Q3**: Need trained checkpoint from Model agent.
**A**: **Random weights checkpoint provided** in smoke test for skeleton. Model agent to deliver trained checkpoint after T029 (CLI train command).

### Future Enhancements (Post-MVP)

- **Cluster merging**: Merge clusters within 1-tile distance threshold
- **Temporal smoothing**: Apply median filter to score timeseries before persistence filter
- **Multi-scenario attribution**: Compare neutral vs extreme_rain to isolate flood-driven changes
- **Confidence scores**: Bayesian uncertainty estimation via MC dropout during rollout

---

## 11. References

- **PRD.md Section 6**: Acceleration scoring formula (EMA + slope)
- **CONTRACTS.md Section 5**: Hotspot JSON schema
- **Constitution Principle II**: Counterfactual reasoning requirements
- **Constitution Principle III**: Testable predictions (validation gates)
- **Tasks T030-T036**: Implementation breakdown for detection modules
- **Tasks T051-T055**: Validation suite implementation

---

**Version**: 1.0.0
**Author**: Detection/Attribution/Eval Agent
**Review Status**: Ready for implementation
**Next Steps**: Implement code skeleton per Section 12
