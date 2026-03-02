# Actions/Context Agent Design Note

**Agent**: Actions/Context Agent
**Version**: 1.0
**Date**: 2026-03-01
**Tasks**: T014-T015 (extended), T019 (anomaly computation)
**Constitution Compliance**: Principle II (Counterfactual Reasoning)

## Mission

Compute rainfall and temperature anomalies using month-of-year climatology baselines and inject these anomalies into manifest.jsonl to enable counterfactual scenario rollouts for infrastructure detection.

## Module API

### Public Functions

#### 1. CHIRPS Aggregator (`src/siad/actions/chirps_aggregator.py`)

```python
def aggregate_chirps_monthly(
    aoi_bounds: dict,  # {"min_lon": float, "max_lon": float, "min_lat": float, "max_lat": float}
    start_month: str,  # "YYYY-MM"
    end_month: str,    # "YYYY-MM"
    ee_authenticated: bool = True
) -> dict[str, float]:
    """
    Fetch CHIRPS monthly precipitation from Earth Engine and compute spatial mean over AOI.

    Returns:
        Dictionary mapping "YYYY-MM" -> precipitation value in mm/month

    Example:
        {"2023-01": 45.2, "2023-02": 32.8, ...}
    """
```

**Implementation Strategy**:
- Use `ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")`
- Filter to date range and AOI bounds
- Aggregate daily to monthly using `.sum()` for each calendar month
- Compute spatial mean using `reduceRegion(ee.Reducer.mean())`
- Return dictionary keyed by month string

#### 2. ERA5 Aggregator (`src/siad/actions/era5_aggregator.py`)

```python
def aggregate_era5_monthly(
    aoi_bounds: dict,
    start_month: str,
    end_month: str,
    ee_authenticated: bool = True
) -> dict[str, float]:
    """
    Fetch ERA5 2m temperature from Earth Engine and compute spatial mean over AOI.

    Returns:
        Dictionary mapping "YYYY-MM" -> temperature value in Kelvin

    Example:
        {"2023-01": 285.3, "2023-02": 287.1, ...}
    """
```

**Implementation Strategy**:
- Use `ee.ImageCollection("ECMWF/ERA5/MONTHLY")`
- Extract `mean_2m_air_temperature` band
- Filter to date range and AOI bounds
- Compute spatial mean using `reduceRegion(ee.Reducer.mean())`
- Return dictionary keyed by month string

#### 3. Anomaly Computer (`src/siad/actions/anomaly_computer.py`)

```python
def compute_month_of_year_anomalies(
    values: dict[str, float],     # {"2023-01": 45.2, "2023-02": 32.8, ...}
    baseline_years: int = 3,      # Number of years for climatology baseline
    epsilon: float = 1e-6         # Small constant to avoid division by zero
) -> dict[str, float]:
    """
    Compute z-score anomalies using month-of-year climatology baselines.

    Algorithm:
        1. Extract month-of-year (1-12) from each date
        2. For each month M, compute mean and std across all M's in baseline period
        3. Z-score for month M in year Y: (value_Y_M - mean_M) / (std_M + epsilon)

    Returns:
        Dictionary mapping "YYYY-MM" -> z-score anomaly

    Example:
        {"2023-01": -0.35, "2023-02": 0.12, ...}
    """
```

**Implementation Details**:

```python
# Pseudocode for month-of-year baseline computation
from collections import defaultdict
import numpy as np

def compute_month_of_year_anomalies(values, baseline_years=3, epsilon=1e-6):
    # Group values by month-of-year (1-12)
    month_groups = defaultdict(list)
    for date_str, value in values.items():
        year, month = date_str.split("-")
        month_of_year = int(month)  # 1-12
        month_groups[month_of_year].append(value)

    # Compute climatology (mean, std) for each month-of-year
    climatology = {}
    for month_of_year in range(1, 13):
        month_values = month_groups[month_of_year]

        # Use last N years for baseline (rolling window)
        if len(month_values) > baseline_years:
            month_values = month_values[-baseline_years:]

        if len(month_values) == 0:
            # Cold-start: no baseline available
            climatology[month_of_year] = {"mean": 0.0, "std": 1.0}
        elif len(month_values) == 1:
            # Single sample: use value as mean, std = 1.0
            climatology[month_of_year] = {"mean": month_values[0], "std": 1.0}
        else:
            # Normal case: compute mean and std
            climatology[month_of_year] = {
                "mean": np.mean(month_values),
                "std": np.std(month_values) + epsilon
            }

    # Compute z-scores
    anomalies = {}
    for date_str, value in values.items():
        year, month = date_str.split("-")
        month_of_year = int(month)

        mean = climatology[month_of_year]["mean"]
        std = climatology[month_of_year]["std"]

        z_score = (value - mean) / std
        anomalies[date_str] = z_score

    return anomalies
```

#### 4. Manifest Injector (`src/siad/actions/manifest_injector.py`)

```python
def inject_anomalies_to_manifest(
    manifest_path: str,           # Path to input manifest.jsonl
    rain_anomalies: dict[str, float],  # {"2023-01": -0.35, ...}
    temp_anomalies: dict[str, float] | None,  # Optional, can be None
    output_path: str | None = None  # If None, overwrites input
) -> None:
    """
    Read manifest.jsonl, add rain_anom and temp_anom fields, write back.

    Algorithm:
        1. Read manifest.jsonl line by line
        2. For each row, extract "month" field
        3. Lookup rain_anom and temp_anom from dictionaries
        4. Update row with anomaly values
        5. Write updated row to output
    """
```

**Implementation Details**:

```python
import json

def inject_anomalies_to_manifest(manifest_path, rain_anomalies, temp_anomalies=None, output_path=None):
    if output_path is None:
        output_path = manifest_path

    updated_rows = []

    with open(manifest_path, 'r') as f:
        for line in f:
            row = json.loads(line)
            month = row["month"]  # "2023-01"

            # Inject rain anomaly (required)
            row["rain_anom"] = rain_anomalies.get(month, 0.0)

            # Inject temp anomaly (optional)
            if temp_anomalies is not None:
                row["temp_anom"] = temp_anomalies.get(month, 0.0)
            else:
                row["temp_anom"] = None  # ERA5 unavailable

            updated_rows.append(row)

    # Write atomically: write to temp file, then rename
    temp_path = output_path + ".tmp"
    with open(temp_path, 'w') as f:
        for row in updated_rows:
            f.write(json.dumps(row) + '\n')

    import os
    os.rename(temp_path, output_path)
```

### CLI Script (`scripts/compute_anomalies.py`)

```python
"""
CLI script to compute anomalies and inject into manifest.

Usage:
    uv run scripts/compute_anomalies.py \
        --config configs/quickstart-demo.yaml \
        --manifest data/raw/manifest.jsonl \
        --output data/preprocessed/manifest_with_anomalies.jsonl \
        --baseline-years 3 \
        --skip-era5  # Optional: skip temperature anomalies
"""
```

## Dependencies

### Upstream (Consume From)

**From Data/GEE Pipeline Agent**:
- `manifest.jsonl` with schema:
  ```json
  {
    "aoi_id": "quickstart-demo",
    "tile_id": "tile_x000_y000",
    "month": "2023-01",
    "gcs_uri": "gs://...",
    "rain_anom": 0.0,  // ← Placeholder, we will update this
    "temp_anom": 0.0,  // ← Placeholder, we will update this
    ...
  }
  ```
- AOI bounds from `configs/<aoi_id>.yaml`
- Date range (start_month, end_month) from config

**From Earth Engine**:
- CHIRPS daily precipitation: `UCSB-CHG/CHIRPS/DAILY`
- ERA5 monthly temperature: `ECMWF/ERA5/MONTHLY`

### Downstream (Produce For)

**For World Model/Training Agent**:
- Updated `manifest.jsonl` with filled anomalies:
  ```json
  {
    ...,
    "rain_anom": -0.35,  // ← Z-score using month-of-year baseline
    "temp_anom": 0.12,   // ← Z-score using month-of-year baseline
    ...
  }
  ```

**For Detection Agent** (during inference):
- Neutral scenario action vector: `[0.0, 0.0]` (no anomaly)
- Observed scenario action vector: `[rain_anom, temp_anom]` from manifest

## Failure Modes

### 1. Cold-Start Problem (First Year Has No Baseline)

**Symptom**: First 12 months have < 3 years of data for climatology

**Mitigation**:
- For months with < baseline_years samples, use available samples (1 or 2 years)
- If only 1 sample exists, use value as mean and std = 1.0 (anomaly = 0)
- If 0 samples exist (should not happen if manifest is complete), use mean = 0.0, std = 1.0

**Validation**: Sanity check that first year anomalies are reasonable (not all zeros)

### 2. Missing Months in CHIRPS/ERA5

**Symptom**: Earth Engine returns no data for certain months (rare but possible)

**Mitigation**:
- Log warning for missing months
- Interpolate from neighboring months (linear interpolation)
- Alternative: Use month-of-year climatology mean as fallback value

**Validation**: Check for NaN or missing values in aggregated dictionaries before computing anomalies

### 3. Extreme Outliers (Z-Score > 5)

**Symptom**: Anomaly computation produces z-scores outside reasonable range [-3, +3]

**Mitigation**:
- Clip z-scores to [-3, +3] range (optional, discuss with team)
- Alternative: Flag extreme outliers for manual review
- Log statistics: min, max, mean, std of computed anomalies

**Validation**: Sanity plot histogram of anomalies (should be roughly Gaussian centered at 0)

### 4. Division by Zero (Zero Variance Months)

**Symptom**: Month-of-year has identical values across all baseline years (e.g., desert with 0 rainfall every January)

**Mitigation**:
- Add epsilon (1e-6) to std before division
- Result: anomaly = (value - mean) / epsilon ≈ very large number if value != mean
- Alternative: If std < epsilon, set anomaly = 0.0 (no variation to detect)

**Validation**: Check climatology dict for zero std values, log warning if found

### 5. Manifest Corruption During Update

**Symptom**: Power failure or interruption during manifest write

**Mitigation**:
- Write to temporary file (.tmp suffix)
- Atomic rename after successful write
- If script crashes, .tmp file remains and original manifest is untouched

**Validation**: Verify output manifest has same number of lines as input manifest

## Testing Strategy

### Smoke Test (`tests/smoke/test_anomalies_smoke.py`)

**Purpose**: Minimal runnable example with synthetic data

**Test Case**:
1. Create synthetic CHIRPS data: 36 months with seasonal pattern (high in summer, low in winter)
2. Compute month-of-year anomalies using 3-year baseline
3. Verify:
   - Anomalies are centered around 0.0 (mean ≈ 0)
   - Seasonal pattern is removed (no correlation between month-of-year and anomaly)
   - Z-scores are in reasonable range [-3, +3]

**Runtime**: < 5 seconds (no Earth Engine calls, pure numpy)

**Example Code**:

```python
import pytest
import numpy as np
from siad.actions.anomaly_computer import compute_month_of_year_anomalies

def test_anomalies_smoke():
    # Create synthetic data: 3 years, seasonal pattern
    months = []
    values = {}
    for year in [2021, 2022, 2023]:
        for month in range(1, 13):
            date_str = f"{year}-{month:02d}"
            # Seasonal pattern: high in summer (June-Aug), low in winter (Dec-Feb)
            seasonal_value = 50 + 30 * np.sin(2 * np.pi * (month - 1) / 12)
            # Add small noise
            noise = np.random.normal(0, 5)
            values[date_str] = seasonal_value + noise
            months.append(date_str)

    # Compute anomalies
    anomalies = compute_month_of_year_anomalies(values, baseline_years=3)

    # Verify: mean ≈ 0, std ≈ 1
    anom_values = list(anomalies.values())
    assert abs(np.mean(anom_values)) < 0.3, "Anomalies should be centered at 0"
    assert 0.7 < np.std(anom_values) < 1.3, "Anomalies should have std ≈ 1"

    # Verify: all anomalies in reasonable range
    assert all(-3 <= a <= 3 for a in anom_values), "Anomalies should be in [-3, +3]"
```

### Unit Tests (Optional but Recommended)

**Test Cases**:
1. `test_chirps_aggregator`: Mock Earth Engine API, verify spatial mean computation
2. `test_era5_aggregator`: Mock Earth Engine API, verify temperature extraction
3. `test_anomaly_computer_cold_start`: Test with < 3 years of data
4. `test_anomaly_computer_zero_variance`: Test with identical values (division by zero)
5. `test_manifest_injector`: Create mock manifest, verify anomalies are injected correctly

### Integration Test (Post-Smoke)

**Purpose**: Test with real Earth Engine data (small AOI, 12 months)

**Test Case**:
1. Use quickstart AOI bounds
2. Fetch CHIRPS for 12 months
3. Compute anomalies
4. Verify Earth Engine API returns expected data
5. Generate sanity plot (time series + histogram)

**Runtime**: ~30 seconds (includes Earth Engine API calls)

## Validation Checks

### Sanity Plots

#### 1. Anomaly Time Series

**Plot**: Line plot of rain_anom and temp_anom over time

**Expected Pattern**:
- Seasonal patterns should be removed (no obvious Jan-Feb-Mar cyclicality)
- Occasional spikes/dips (drought/flood months)
- Roughly centered around 0.0

**Code**:

```python
import matplotlib.pyplot as plt

def plot_anomaly_timeseries(rain_anomalies, temp_anomalies, output_path):
    months = sorted(rain_anomalies.keys())
    rain_values = [rain_anomalies[m] for m in months]
    temp_values = [temp_anomalies[m] for m in months] if temp_anomalies else None

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    # Rain anomalies
    axes[0].plot(months, rain_values, marker='o', label='Rain Anomaly')
    axes[0].axhline(0, color='red', linestyle='--', alpha=0.5)
    axes[0].set_ylabel('Rain Z-Score')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Temp anomalies
    if temp_values:
        axes[1].plot(months, temp_values, marker='s', color='orange', label='Temp Anomaly')
        axes[1].axhline(0, color='red', linestyle='--', alpha=0.5)
    axes[1].set_ylabel('Temp Z-Score')
    axes[1].set_xlabel('Month')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    # Rotate x-axis labels
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
```

#### 2. Anomaly Histogram

**Plot**: Histogram of all computed anomalies

**Expected Pattern**:
- Approximately Gaussian distribution
- Centered at 0.0
- Most values in [-2, +2] range (95% confidence)

**Code**:

```python
def plot_anomaly_histogram(rain_anomalies, temp_anomalies, output_path):
    rain_values = list(rain_anomalies.values())
    temp_values = list(temp_anomalies.values()) if temp_anomalies else None

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Rain histogram
    axes[0].hist(rain_values, bins=20, alpha=0.7, color='blue', edgecolor='black')
    axes[0].axvline(0, color='red', linestyle='--', label='Mean = 0')
    axes[0].set_xlabel('Rain Anomaly Z-Score')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Rain Anomaly Distribution')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Temp histogram
    if temp_values:
        axes[1].hist(temp_values, bins=20, alpha=0.7, color='orange', edgecolor='black')
        axes[1].axvline(0, color='red', linestyle='--', label='Mean = 0')
    axes[1].set_xlabel('Temp Anomaly Z-Score')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Temp Anomaly Distribution')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
```

## Open Questions/Blockers

### Questions for Team

1. **Baseline Window**: Use 3-year rolling window or fixed 2021-2023 baseline?
   - **Recommendation**: Rolling window for datasets > 3 years (e.g., 2021-2026 data uses last 3 years per month)
   - **Reason**: Captures climate drift over time

2. **Outlier Clipping**: Should we clip z-scores to [-3, +3]?
   - **Recommendation**: No clipping for now, flag extreme values (> ±5) for review
   - **Reason**: Extreme events (drought, flood) may be real signal, not noise

3. **Missing Months**: Interpolate or skip?
   - **Recommendation**: Linear interpolation from neighbors
   - **Reason**: Avoids gaps in time series that break rollout continuity

### Blockers

1. **Need manifest.jsonl from Data agent**
   - **Status**: Can use mock manifest for smoke test
   - **Mock format**:
     ```json
     {"aoi_id":"quickstart-demo","tile_id":"tile_x000_y000","month":"2023-01","gcs_uri":"gs://...","rain_anom":0.0,"temp_anom":0.0,"s2_valid_frac":0.87,"band_order_version":"v1","preprocessing_version":"20260228"}
     ```

2. **Confirm AOI bounds format**
   - **Assumption**: `configs/<aoi_id>.yaml` contains:
     ```yaml
     aoi:
       aoi_id: "quickstart-demo"
       bounds:
         min_lon: 12.0
         max_lon: 12.5
         min_lat: 34.0
         max_lat: 34.5
     ```

3. **Earth Engine authentication**
   - **Assumption**: User has authenticated via `earthengine authenticate`
   - **Fallback**: Smoke test uses synthetic data (no EE required)

## Implementation Timeline

### Phase 1: Core Modules (Days 1-2)

- [ ] Implement `anomaly_computer.py` (month-of-year baseline logic)
- [ ] Implement `manifest_injector.py` (JSONL update logic)
- [ ] Write smoke test with synthetic data
- [ ] Validate anomaly computation with unit tests

### Phase 2: Earth Engine Integration (Days 3-4)

- [ ] Implement `chirps_aggregator.py` (EE API for CHIRPS)
- [ ] Implement `era5_aggregator.py` (EE API for ERA5)
- [ ] Write integration test with real EE data (12 months, small AOI)
- [ ] Generate sanity plots (time series + histogram)

### Phase 3: CLI Script (Day 5)

- [ ] Implement `scripts/compute_anomalies.py` (orchestration)
- [ ] Add argument parsing (--config, --manifest, --output, --baseline-years, --skip-era5)
- [ ] Test end-to-end: read config → fetch EE data → compute anomalies → update manifest
- [ ] Document usage in README

### Phase 4: Handoff (Day 6)

- [ ] Create example output: `data/preprocessed/manifest_with_anomalies.jsonl`
- [ ] Generate validation plots: `data/outputs/rain_anom_timeseries.png`, `data/outputs/anom_histogram.png`
- [ ] Write handoff note for Model agent: "Action vectors ready, use manifest rain_anom/temp_anom during dataset loading"

## Risk Mitigation Summary

| Risk | Mitigation | Validation |
|------|-----------|------------|
| Cold-start (< 3 years baseline) | Use available samples, fallback to mean=0 std=1 | Sanity check first year anomalies |
| Missing months (EE gaps) | Linear interpolation from neighbors | Check for NaN before computing anomalies |
| Extreme outliers (z > 5) | Log statistics, flag for review (no clipping) | Histogram plot shows distribution |
| Division by zero (std=0) | Add epsilon (1e-6) to std | Check climatology for zero variance |
| Manifest corruption | Atomic write (temp file + rename) | Verify output line count == input |

## Constitution Compliance

**Principle II (Counterfactual Reasoning)**: This module enables neutral scenario rollouts by providing rain_anom/temp_anom action vectors. During detection, neutral scenario uses action = [0.0, 0.0], observed scenario uses action = [rain_anom, temp_anom] from manifest. This separation allows the world model to distinguish environmental changes (removed under neutral) from structural changes (persist under neutral).

**Success Criteria**: Anomaly time series shows seasonal patterns removed, histogram is approximately Gaussian centered at 0, and manifest injection completes without errors.
