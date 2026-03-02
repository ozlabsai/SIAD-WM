# Actions/Context Module

## Overview

This module computes rainfall and temperature anomalies using month-of-year climatology baselines and injects them into manifest.jsonl for counterfactual scenario rollouts.

**Agent**: Actions/Context Agent
**Tasks**: T014-T015 (extended), T019 (anomaly computation)
**Constitution**: Principle II (Counterfactual Reasoning)

## Module Structure

```
src/siad/actions/
├── __init__.py               # Public API exports
├── anomaly_computer.py       # Month-of-year baseline + z-score computation
├── manifest_injector.py      # Update manifest.jsonl with anomalies
├── chirps_aggregator.py      # Fetch CHIRPS monthly precipitation from Earth Engine
├── era5_aggregator.py        # Fetch ERA5 monthly temperature from Earth Engine
├── visualization.py          # Sanity plots for validation
└── README.md                 # This file
```

## Quick Start

### 1. Compute Anomalies from Scratch

```bash
# Fetch CHIRPS/ERA5, compute anomalies, inject into manifest
uv run scripts/compute_anomalies.py \
  --config configs/quickstart-demo.yaml \
  --manifest data/raw/manifest.jsonl \
  --output data/preprocessed/manifest_with_anomalies.jsonl \
  --baseline-years 3
```

### 2. Use as Library

```python
from siad.actions import compute_month_of_year_anomalies, inject_anomalies_to_manifest
from siad.actions.chirps_aggregator import aggregate_chirps_monthly

# Fetch CHIRPS data
aoi_bounds = {
    "min_lon": 12.0, "max_lon": 12.5,
    "min_lat": 34.0, "max_lat": 34.5
}
rain_values = aggregate_chirps_monthly(
    aoi_bounds=aoi_bounds,
    start_month="2023-01",
    end_month="2023-12"
)

# Compute anomalies
rain_anomalies = compute_month_of_year_anomalies(
    values=rain_values,
    baseline_years=3
)

# Inject into manifest
inject_anomalies_to_manifest(
    manifest_path="data/raw/manifest.jsonl",
    rain_anomalies=rain_anomalies,
    output_path="data/preprocessed/manifest_with_anomalies.jsonl"
)
```

### 3. Generate Validation Plots

```python
from siad.actions.visualization import generate_validation_plots

generate_validation_plots(
    rain_anomalies=rain_anomalies,
    temp_anomalies=temp_anomalies,
    output_dir="data/outputs"
)
# Saves: anomaly_timeseries.png, anomaly_histogram.png
```

## Contracts

### Input (from Data/GEE Agent)

**manifest.jsonl** with placeholder anomalies:
```json
{
  "aoi_id": "quickstart-demo",
  "tile_id": "tile_x000_y000",
  "month": "2023-01",
  "gcs_uri": "gs://...",
  "rain_anom": 0.0,  // Placeholder
  "temp_anom": 0.0,  // Placeholder
  "s2_valid_frac": 0.87,
  "band_order_version": "v1",
  "preprocessing_version": "20260228"
}
```

### Output (for World Model/Training Agent)

**manifest.jsonl** with filled anomalies:
```json
{
  ...,
  "rain_anom": -0.35,  // Z-score using month-of-year baseline
  "temp_anom": 0.12,   // Z-score using month-of-year baseline
  ...
}
```

**Action Vector** (per timestep during dataset loading):
```python
action_t = np.array([rain_anom, temp_anom], dtype=np.float32)  # Shape: (2,)
```

**Neutral Scenario** (for counterfactual detection):
```python
neutral_action = np.array([0.0, 0.0], dtype=np.float32)
```

## Algorithm

### Month-of-Year Climatology

1. Group values by month-of-year (1-12)
2. For each month M, compute mean and std across all M's in baseline period (last 3 years)
3. Z-score for month M in year Y: `(value_Y_M - mean_M) / (std_M + epsilon)`

**Example**:
- January 2021: 45.2 mm
- January 2022: 50.1 mm
- January 2023: 42.7 mm
- Climatology: mean = 46.0 mm, std = 3.8 mm
- Anomaly for Jan 2023: (42.7 - 46.0) / 3.8 = -0.87 (below average)

### Failure Modes

| Risk | Mitigation |
|------|-----------|
| Cold-start (< 3 years baseline) | Use available samples (1-2 years), fallback to mean=0 std=1 |
| Missing months (EE gaps) | Linear interpolation or month-of-year climatology mean |
| Extreme outliers (z > 5) | Log statistics, flag for review (no clipping) |
| Division by zero (std=0) | Add epsilon (1e-6) to std |
| Manifest corruption | Atomic write (temp file + rename) |

## Validation

### Smoke Test

```bash
# Run without Earth Engine (synthetic data)
uv run python tests/smoke/test_anomalies_smoke.py
```

**Expected output**:
```
END-TO-END SMOKE TEST PASSED
  Rain anomaly stats: {'min': -1.41, 'max': 1.40, 'mean': 0.0, 'std': 1.0}
  Temp anomaly stats: {'min': -1.40, 'max': 1.41, 'mean': 0.0, 'std': 1.0}
```

### Sanity Plots

After computing anomalies, generate validation plots:

```bash
uv run scripts/compute_anomalies.py --config configs/quickstart-demo.yaml ...
# Then generate plots manually or use visualization module
```

**Expected patterns**:
- **Time series**: Seasonal patterns removed, roughly centered at 0.0
- **Histogram**: Approximately Gaussian, centered at 0.0, most values in [-2, +2]

## Dependencies

- **numpy**: Anomaly computation (mean, std, z-scores)
- **earthengine-api**: Fetch CHIRPS and ERA5 data
- **matplotlib**: Validation plots
- **pyyaml**: Config file parsing

## Testing

### Unit Tests

```bash
# (Future) Run with pytest
pytest tests/unit/test_anomaly_computer.py
pytest tests/unit/test_manifest_injector.py
```

### Integration Test

```bash
# (Future) Test with real Earth Engine data (12 months, small AOI)
pytest tests/integration/test_actions_integration.py
```

## Handoff to Model Agent

**Action Vector Usage**:

During dataset loading (`src/siad/data/loaders/siad_dataset.py`):

```python
# Read manifest.jsonl
for row in manifest:
    month = row["month"]
    rain_anom = row["rain_anom"]
    temp_anom = row["temp_anom"]

    # Create action vector
    action_t = np.array([rain_anom, temp_anom], dtype=np.float32)

    # Pass to world model during training/inference
    latent_t1 = model.forward(obs_t, action_t)
```

**Neutral Scenario** (Detection agent):

```python
# Counterfactual rollout with no anomalies
neutral_action = np.array([0.0, 0.0], dtype=np.float32)
neutral_rollout = model.rollout(context, neutral_action, horizon=6)
```

## Design Decisions

1. **Month-of-year baseline** (not global mean/std): Removes seasonal patterns, enables month-specific anomalies
2. **3-year rolling window**: Adapts to climate drift over time
3. **Z-score normalization**: Standardizes values to common scale, removes units
4. **Atomic manifest write**: Prevents corruption during interruption
5. **Optional ERA5**: Allows rainfall-only workflow if temperature unavailable

## Constitution Compliance

**Principle II (Counterfactual Reasoning)**: This module enables neutral scenario rollouts by providing rain_anom/temp_anom action vectors. During detection, neutral scenario uses action = [0.0, 0.0], observed scenario uses action = [rain_anom, temp_anom] from manifest. This separation allows the world model to distinguish environmental changes (removed under neutral) from structural changes (persist under neutral).

## Future Enhancements (Post-MVP)

- [ ] Support for multiple AOIs in single run
- [ ] Caching of CHIRPS/ERA5 data to avoid re-fetching
- [ ] Parallel Earth Engine requests for faster aggregation
- [ ] Advanced interpolation methods for missing months
- [ ] Automated outlier detection and reporting
- [ ] Support for weekly or daily cadence (requires higher-resolution climatology)
