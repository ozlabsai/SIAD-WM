# SIAD MVP - Interface Contracts

**Version**: 1.0
**Date**: 2026-02-28
**Purpose**: Define data schemas and APIs between agent modules

## 1. State Tensor Band Order (GLOBAL CONTRACT)

**Version**: `band_order_v1`
**Owner**: Data/GEE Pipeline Agent
**Consumers**: World Model, Detection, Reporting

```python
BAND_ORDER_V1 = [
    "S2_B2",          # Index 0: Sentinel-2 Blue (10m resolution)
    "S2_B3",          # Index 1: Sentinel-2 Green (10m)
    "S2_B4",          # Index 2: Sentinel-2 Red (10m)
    "S2_B8",          # Index 3: Sentinel-2 NIR (10m)
    "S1_VV",          # Index 4: Sentinel-1 SAR VV polarization
    "S1_VH",          # Index 5: Sentinel-1 SAR VH polarization
    "VIIRS_avg_rad",  # Index 6: VIIRS nighttime lights (monthly avg radiance)
    "S2_valid_mask"   # Index 7: Sentinel-2 cloud-free pixel fraction [0.0-1.0]
]
# Optional 9th band (defer to post-MVP): S2_B11 (SWIR1)
```

**GeoTIFF File Format**:
- Bands: 8 (indices 0-7 above)
- Data type: Float32
- Projection: EPSG:3857 (Web Mercator)
- Resolution: 10m
- Tile size: 256×256 pixels (2.56 km square)
- NoData value: -9999.0

---

## 2. Manifest Schema (Data → Actions → Model)

**Owner**: Data/GEE Pipeline Agent
**Extended by**: Actions/Context Agent
**Consumed by**: World Model/Training Agent

**File**: `gs://<bucket>/siad/<aoi_id>/manifest.jsonl` (JSONL format, one object per line)

**Schema**:
```json
{
  "aoi_id": "string",               // AOI identifier (e.g., "quickstart-demo")
  "tile_id": "string",              // Tile identifier (e.g., "tile_x012_y034")
  "month": "string",                // ISO 8601 month (e.g., "2023-01")
  "gcs_uri": "string",              // Full GCS path to .tif file
  "rain_anom": "float",             // Rainfall z-score anomaly (required)
  "temp_anom": "float|null",        // Temperature z-score anomaly (optional)
  "s2_valid_frac": "float",         // Sentinel-2 valid pixel fraction [0.0-1.0]
  "band_order_version": "string",   // "v1" (references BAND_ORDER_V1)
  "preprocessing_version": "string" // Date-based version (e.g., "20260228")
}
```

**Validation Rules**:
- `aoi_id` and `tile_id` must be non-empty strings
- `month` must match `YYYY-MM` format
- `gcs_uri` must start with `gs://` and end with `.tif`
- `rain_anom` must be finite float (typically in range [-3, +3] for z-scores)
- `temp_anom` can be null if ERA5 data unavailable
- `s2_valid_frac` must be in [0.0, 1.0]
- `band_order_version` must be "v1"

**Example Row**:
```json
{"aoi_id":"quickstart-demo","tile_id":"tile_x000_y000","month":"2023-01","gcs_uri":"gs://siad-exports/siad/quickstart-demo/tile_x000_y000/2023-01.tif","rain_anom":-0.35,"temp_anom":0.12,"s2_valid_frac":0.87,"band_order_version":"v1","preprocessing_version":"20260228"}
```

---

## 3. Action Vector Schema (Actions → Model)

**Owner**: Actions/Context Agent
**Consumer**: World Model/Training Agent

**Format**: Extracted from manifest.jsonl during dataset loading

**Structure**:
```python
# Per-timestep action vector (1D array)
action_t = np.array([rain_anom, temp_anom], dtype=np.float32)  # Shape: (2,)
```

**Semantics**:
- `action_t[0]` = rain_anom (z-score, month-of-year baseline)
- `action_t[1]` = temp_anom (z-score, month-of-year baseline, or 0.0 if unavailable)

**Neutral Scenario** (for counterfactual detection):
```python
neutral_action = np.array([0.0, 0.0], dtype=np.float32)  # No anomaly
```

---

## 4. Model Checkpoint Schema (Model → Detection)

**Owner**: World Model/Training Agent
**Consumer**: Detection/Attribution/Eval Agent

**File**: `data/models/<run_name>/checkpoint_<epoch>.pth` (PyTorch checkpoint)

**Contents** (PyTorch state dict):
```python
{
    "epoch": int,
    "model_state_dict": {
        "obs_encoder": {...},      # Observation encoder weights
        "target_encoder": {...},   # EMA target encoder weights
        "action_encoder": {...},   # Action encoder weights
        "dynamics": {...}          # Transition model weights
    },
    "optimizer_state_dict": {...},
    "train_loss": float,
    "val_loss": float,
    "config": {
        "latent_dim": int,         # Latent space dimensionality
        "context_length": 6,       # L=6 months
        "rollout_horizon": 6,      # H=6 months
        "band_order_version": "v1"
    }
}
```

**Loading API** (Detection agent):
```python
checkpoint = torch.load("data/models/<run_name>/checkpoint_best.pth")
model.load_state_dict(checkpoint["model_state_dict"])
latent_dim = checkpoint["config"]["latent_dim"]
```

---

## 5. Hotspot JSON Schema (Detection → Reporting)

**Owner**: Detection/Attribution/Eval Agent
**Consumer**: Reporting/UI Agent

**File**: `data/outputs/<aoi_id>/hotspots.json` (JSON array)

**Schema**:
```json
[
  {
    "hotspot_id": "string",                   // "hotspot_001"
    "aoi_id": "string",                       // Parent AOI
    "tile_ids": ["string", ...],              // List of tile IDs in cluster (≥3)
    "centroid": {"lon": float, "lat": float}, // Geographic center
    "first_detected_month": "string",         // ISO 8601 month (e.g., "2023-06")
    "persistence_months": int,                // Consecutive months above threshold (≥2)
    "confidence_tier": "string",              // "Structural" | "Activity" | "Environmental"
    "max_acceleration_score": float,          // Peak score across cluster
    "attribution": {
      "sar_contribution": float,              // [0-1] normalized
      "optical_contribution": float,          // [0-1] normalized
      "lights_contribution": float            // [0-1] normalized
    },
    "thumbnails": {
      "s1_before": "string",                  // Path to SAR before thumbnail
      "s1_after": "string",                   // Path to SAR after thumbnail
      "s2_before": "string",                  // Path to optical before
      "s2_after": "string",                   // Path to optical after
      "viirs_before": "string",               // Path to lights before
      "viirs_after": "string"                 // Path to lights after
    }
  }
]
```

**Validation Rules**:
- `tile_ids` must have length ≥ 3
- `persistence_months` must be ≥ 2
- `confidence_tier` must be one of {"Structural", "Activity", "Environmental"}
- Attribution contributions should sum to ~1.0 (within 0.05 tolerance)

---

## 6. Config YAML Schema (Infra → All)

**Owner**: Infra/DevEx Agent
**Consumers**: All agents

**File**: `configs/<aoi_id>.yaml`

**Schema**:
```yaml
aoi:
  aoi_id: "quickstart-demo"
  bounds:
    min_lon: 12.0
    max_lon: 12.5
    min_lat: 34.0
    max_lat: 34.5
  projection: "EPSG:3857"
  resolution_m: 10
  tile_size_px: 256

data:
  gcs_bucket: "siad-exports"
  export_path: "gs://siad-exports/siad/{aoi_id}"
  start_month: "2021-01"
  end_month: "2023-12"
  sources: ["s1", "s2", "viirs", "chirps", "era5"]

model:
  latent_dim: 256
  context_length: 6
  rollout_horizon: 6
  batch_size: 16
  epochs: 50
  learning_rate: 1.0e-4

detection:
  percentile_threshold: 99.0
  persistence_months: 2
  min_cluster_size: 3
  scenarios: ["neutral", "observed", "extreme_rain"]

validation:
  backtest_regions: "configs/validation_regions/quickstart-demo.json"
  fp_test_regions: "configs/validation_regions/fp_agriculture.json"
```

---

## 7. CLI Command Interface (Infra → All)

**Owner**: Infra/DevEx Agent
**Consumers**: All agents (via CLI wrappers)

### `siad export`

```bash
siad export \
  --config configs/quickstart-demo.yaml \
  --aoi-id quickstart-demo \
  --dry-run  # Optional: validate without executing
```

**Outputs**:
- GCS bucket populated with .tif files
- `manifest.jsonl` created

### `siad train`

```bash
siad train \
  --config configs/quickstart-demo.yaml \
  --manifest gs://siad-exports/siad/quickstart-demo/manifest.jsonl \
  --output data/models/quickstart-v1 \
  --epochs 50 \
  --dry-run
```

**Outputs**:
- `data/models/quickstart-v1/checkpoint_best.pth`
- `data/models/quickstart-v1/metrics.csv`

### `siad detect`

```bash
siad detect \
  --config configs/quickstart-demo.yaml \
  --checkpoint data/models/quickstart-v1/checkpoint_best.pth \
  --manifest gs://siad-exports/siad/quickstart-demo/manifest.jsonl \
  --output data/outputs/quickstart-demo \
  --scenarios neutral,observed \
  --dry-run
```

**Outputs**:
- `data/outputs/quickstart-demo/hotspots.json`
- `data/outputs/quickstart-demo/scores_<month>.tif` (per-tile rasters)

### `siad report`

```bash
siad report \
  --config configs/quickstart-demo.yaml \
  --hotspots data/outputs/quickstart-demo/hotspots.json \
  --output data/outputs/quickstart-demo/report.html \
  --dry-run
```

**Outputs**:
- `data/outputs/quickstart-demo/report.html`

---

## 8. Error Handling Contract (All Agents)

**Standard Error Format**:
```python
class SIADError(Exception):
    def __init__(self, agent: str, stage: str, details: str):
        self.agent = agent      # "Data/GEE" | "Actions" | "Model" | "Detection" | "Infra" | "Reporting"
        self.stage = stage      # "export" | "train" | "detect" | "report"
        self.details = details
        super().__init__(f"[{agent}] {stage}: {details}")
```

**Logging Contract**:
```python
import logging

# All agents must use module-level logger
logger = logging.getLogger(f"siad.{__name__}")

# Infra agent configures root logger with:
# - File handler: logs/siad_<timestamp>.log
# - Console handler: stderr with level INFO
# - Format: "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
```

---

## 9. Testing Contract (All Agents)

Each agent must provide:

### Smoke Test
**File**: `tests/smoke/test_<agent>_smoke.py`
**Purpose**: Minimal end-to-end test with tiny sample data
**Runtime**: < 30 seconds

### Unit Tests (Optional but Recommended)
**File**: `tests/unit/test_<module>.py`
**Coverage**: Key functions with edge cases

### Integration Test (Post-Smoke)
**File**: `tests/integration/test_<agent>_integration.py`
**Purpose**: Test with real (but small) data from upstream agents

---

## 10. Versioning Contract

**Band Order**: `band_order_v1` (frozen for MVP, increment only if schema changes)
**Preprocessing**: Date-based `YYYYMMDD` (e.g., `20260228`)
**Model**: Git commit SHA in checkpoint metadata (added by Infra agent)
**API**: Semantic versioning for post-MVP public APIs

---

**Change Log**:
- 2026-02-28: Initial version (v1.0)
