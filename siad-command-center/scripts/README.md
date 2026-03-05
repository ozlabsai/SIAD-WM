# M1b Data Pipeline Scripts

Data generation scripts for SIAD Command Center seed dataset.

## Overview

These scripts extract a seed dataset (2 tiles × 6 months) from the full dataset and generate all precomputed artifacts needed for the frontend:

- Residual overlays with color mapping
- Baseline comparison overlays (persistence & seasonal)
- Hotspot GeoJSON polygons
- Timeline JSON with onset detection

## Scripts

### 1. `create_seed_dataset.py`

Extracts minimal dataset for rapid frontend development.

**Input:**
- `data/satellite_imagery/` (full dataset: 75 tiles × 12 months)
- `data/satellite_imagery/metadata.json`

**Output:**
- `data/aoi_sf_seed/tiles/` (2 tiles × 6 months)
- `data/aoi_sf_seed/metadata.json`
- `data/aoi_sf_seed/months.json`

**Selection criteria:**
- Tiles with onset months 4-6 (clear change events)
- Diverse change types (urban_construction, infrastructure)
- Months 1-6 (Jan-Jun 2024)

**Usage:**
```bash
uv run python scripts/create_seed_dataset.py
```

### 2. `generate_residual_overlays.py`

Generates color-mapped residual overlays from world model predictions.

**Input:**
- `data/residuals_test.h5` (256 residual scores per tile/month)
- `data/aoi_sf_seed/metadata.json`

**Output:**
- `tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_wm_residual.png`

**Color mapping:**
- Green (0.0-0.3): Normal
- Yellow (0.3-0.6): Elevated
- Orange (0.6-0.8): High
- Red (0.8-1.0): Critical

**Process:**
1. Reshape 256 tokens → 16×16 grid
2. Apply discrete color mapping
3. Upscale to 128×128 (match satellite imagery)
4. Save as RGBA PNG

**Usage:**
```bash
uv run python scripts/generate_residual_overlays.py
```

### 3. `generate_hotspots.py`

Detects hotspot regions and converts to GeoJSON polygons.

**Input:**
- `data/residuals_test.h5`
- `data/aoi_sf_seed/metadata.json`

**Output:**
- `tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_wm_hotspots.geojson`
- `data/aoi_sf_seed/hotspots_ranked.json`

**Algorithm:**
1. Threshold residual grid at 90th percentile
2. Find connected components (scipy.ndimage.label)
3. Calculate region statistics (size, mean score, max score)
4. Convert pixel coordinates to lat/lon polygons
5. Rank hotspots by severity

**GeoJSON properties:**
- `region_id`: Connected component ID
- `size_pixels`: Region size
- `mean_score`: Average residual in region
- `max_score`: Peak residual in region
- `severity`: critical (>0.8), high (>0.6), or elevated (>0.3)

**Usage:**
```bash
uv run python scripts/generate_hotspots.py
```

### 4. `create_baseline_overlays.py`

Generates uniform color overlays for tile-level baseline scores.

**Input:**
- `data/residuals_test.h5` (baseline scores: scalar per tile/month)
- `data/aoi_sf_seed/metadata.json`

**Output:**
- `tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_persist_baseline.png`
- `tiles/{tile_id}/month_{mm}/overlays/{YYYY-MM}_seasonal_baseline.png`

**Note:** Baselines are tile-level scores (not per-token), so overlays are uniform colors representing overall performance.

**Usage:**
```bash
uv run python scripts/create_baseline_overlays.py
```

### 5. `generate_timelines.py`

Generates timeline JSON with monthly scores and onset detection.

**Input:**
- `data/residuals_test.h5`
- `data/aoi_sf_seed/metadata.json`

**Output:**
- `tiles/{tile_id}/timeseries.json`

**Timeline structure:**
```json
{
  "tile_id": 1,
  "change_type": "urban_construction",
  "location": {"latitude": 49.18, "longitude": -130.95},
  "analysis": {
    "onset_month": 3,
    "persistence_duration": 2,
    "max_score": 0.898,
    "max_score_month": 3
  },
  "timeline": [
    {
      "month": 1,
      "label": "2024-01",
      "scores": {
        "world_model": 0.27,
        "persistence": 0.486,
        "seasonal": 0.432
      },
      "anomaly": false
    }
  ]
}
```

**Onset detection:** First month where mean residual exceeds 90th percentile.

**Usage:**
```bash
uv run python scripts/generate_timelines.py
```

### 6. `validate_seed_dataset.py`

Validates dataset completeness and generates statistics.

**Checks:**
- All required files present (imagery, overlays, GeoJSON, timelines)
- Metadata files exist
- File sizes and counts

**Output:**
- Console validation report
- `data/aoi_sf_seed/validation_report.json`

**Usage:**
```bash
uv run python scripts/validate_seed_dataset.py
```

## Full Pipeline Execution

Run all scripts in order:

```bash
# 1. Create seed dataset
uv run python scripts/create_seed_dataset.py

# 2. Generate all overlays
uv run python scripts/generate_residual_overlays.py
uv run python scripts/create_baseline_overlays.py

# 3. Generate hotspots and timelines
uv run python scripts/generate_hotspots.py
uv run python scripts/generate_timelines.py

# 4. Validate outputs
uv run python scripts/validate_seed_dataset.py
```

## Output Structure

```
data/aoi_sf_seed/
├── metadata.json           # Seed dataset metadata
├── months.json             # Month labels
├── hotspots_ranked.json    # All hotspots ranked by severity
├── validation_report.json  # Dataset validation report
└── tiles/
    ├── tile_001/
    │   ├── timeseries.json
    │   ├── month_01/
    │   │   ├── actual.png
    │   │   ├── predicted.png
    │   │   ├── residual.png
    │   │   └── overlays/
    │   │       ├── 2024-01_wm_residual.png
    │   │       ├── 2024-01_persist_baseline.png
    │   │       ├── 2024-01_seasonal_baseline.png
    │   │       └── 2024-01_wm_hotspots.geojson
    │   ├── month_02/
    │   └── ...
    └── tile_002/
        └── ...
```

## Dataset Statistics

**Seed Dataset:**
- Tiles: 2 (IDs: 1, 2)
- Months: 6 (Jan-Jun 2024)
- Change Types: urban_construction, infrastructure
- Total Files: 86
- Total Size: 1.09 MB

**Per Tile:**
- 6 months × 3 imagery files = 18 PNG files
- 6 months × 4 overlay files = 24 PNG + 6 GeoJSON
- 1 timeseries JSON
- Total: 43 files per tile

## Key Findings

**Tile 1 (urban_construction):**
- Onset: Month 3 (March 2024)
- Peak score: 0.898 (month 3)
- Persistence: 2 consecutive months above threshold
- Hotspots: 6 detected (2 critical, 1 high, 3 elevated)

**Tile 2 (infrastructure):**
- Onset: Month 3 (March 2024)
- Peak score: 0.766 (month 3)
- Persistence: 2 consecutive months above threshold
- Hotspots: 3 detected (1 critical, 2 elevated)

**Model Performance:**
- World model significantly outperforms baselines during change events
- Clear onset detection in month 3 for both tiles
- Persistence baseline fails during structural changes (scores > 1.0)
- Seasonal baseline performs better than persistence but still worse than world model

## Notes

- HDF5 tile mapping: `tile_x{x:03d}_y{y:03d}` where `x = tile_id % 5`, `y = tile_id // 5`
- Residuals are normalized to [0, 1] range
- Baseline scores can exceed 1.0 (indicating poor predictions)
- GeoJSON coordinates use (lon, lat) order per spec
- Overlay images use RGBA format for transparency support
