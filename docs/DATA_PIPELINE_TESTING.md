# Data Pipeline Testing Guide

**Purpose**: Test the complete data collection and preprocessing pipeline on CPU before GPU training.

This validates that Earth Engine data collection, preprocessing, and manifest generation work correctly without needing expensive GPU resources.

---

## Quick Start

### 1. Prerequisites

```bash
# Install dependencies
uv sync

# Authenticate with Earth Engine
export GOOGLE_CLOUD_PROJECT=your-ee-project-id
earthengine authenticate --project $GOOGLE_CLOUD_PROJECT

# Verify authentication
python -c "import ee; ee.Initialize(project='$GOOGLE_CLOUD_PROJECT'); print('✓ EE Ready')"
```

### 2. Run Tests

#### Tiny Test (Recommended First Run)
**Runtime**: ~2-5 minutes
**Data**: 1 tile × 3 months (~3 km² AOI)

```bash
uv run python scripts/test_data_pipeline.py --aoi-size tiny
```

**What it tests**:
- Earth Engine authentication
- S1/S2/VIIRS/CHIRPS data availability
- Data collection for tiny AOI
- Preprocessing and band stacking
- Climate anomaly computation
- Manifest generation
- Dataset loading validation

#### Small Test (More Thorough)
**Runtime**: ~10-15 minutes
**Data**: 4 tiles × 6 months (~36 km² AOI)

```bash
uv run python scripts/test_data_pipeline.py --aoi-size small
```

#### Medium Test (Full Validation)
**Runtime**: ~30-45 minutes
**Data**: 16 tiles × 12 months (~144 km² AOI)

```bash
uv run python scripts/test_data_pipeline.py --aoi-size medium
```

### 3. Check Results

```bash
# View output
ls -lh data/pipeline_test/

# Inspect manifest
head data/pipeline_test/manifest.jsonl

# Check logs
tail -f logs/data_pipeline_test.log
```

---

## Test Stages

### Stage 1: Earth Engine Authentication ✅

Validates EE credentials and project access.

**What it checks**:
- `earthengine authenticate` ran successfully
- Project ID is set via `GOOGLE_CLOUD_PROJECT` env var
- Can access Earth Engine API
- Can query asset roots

**Common Issues**:
```bash
# Issue: "EE authentication failed"
# Fix: Run authentication
earthengine authenticate --project YOUR_PROJECT_ID

# Issue: "GOOGLE_CLOUD_PROJECT not set"
# Fix: Export project ID
export GOOGLE_CLOUD_PROJECT=your-ee-project-id

# Verify
echo $GOOGLE_CLOUD_PROJECT
```

---

### Stage 2: Satellite Data Collection ✅

Downloads S1, S2, VIIRS, CHIRPS for test AOI.

**What it tests**:
- Tile grid generation (256×256 pixels at 10m resolution)
- Sentinel-1 SAR (VV/VH polarizations)
- Sentinel-2 Optical (B2/B3/B4/B8 bands)
- VIIRS Nighttime Lights (avg_rad)
- CHIRPS Rainfall (precipitation)

**Output**:
```
✓ S1 (SAR): {'available': True, 'count': 12}
✓ S2 (Optical): {'available': True, 'count': 8, 'cloud_cover': 15.3}
✓ VIIRS (Lights): {'available': True, 'count': 1}
✓ CHIRPS (Rainfall): {'available': True, 'count': 30}
```

**Common Issues**:
```bash
# Issue: "S2 data not available"
# Cause: High cloud cover or no S2 passes in time window
# Fix: Choose different AOI bounds or time period
#      Sicily (14.0-14.1, 37.5-37.6) has good data availability

# Issue: "Request quota exceeded"
# Cause: Too many EE API calls
# Fix: Wait a few minutes, or reduce --aoi-size
```

---

### Stage 3: Preprocessing & Band Stacking ✅

Reprojects, tiles, and stacks bands per BAND_ORDER_V1.

**What it tests**:
- Reprojection to EPSG:3857 at 10m resolution
- Band stacking in correct order:
  ```python
  BAND_ORDER_V1 = [
      "S2_B2",      # Blue
      "S2_B3",      # Green
      "S2_B4",      # Red
      "S2_B8",      # NIR
      "S1_VV",      # SAR VV
      "S1_VH",      # SAR VH
      "VIIRS_avg_rad",  # Lights
      "S2_valid_mask"   # Cloud mask
  ]
  ```
- Band order validation (contract compliance)

**Output**:
```
✓ Band order validated
✓ Image ready for export
  Stacked bands: ['S2_B2', 'S2_B3', 'S2_B4', 'S2_B8', 'S1_VV', 'S1_VH', 'VIIRS_avg_rad', 'S2_valid_mask']
```

---

### Stage 4: Climate Anomaly Computation ✅

Computes rainfall (and optional temperature) z-score anomalies.

**What it tests**:
- CHIRPS monthly aggregation
- Month-of-year climatology baseline (2000-2020)
- Z-score normalization: `(value - mean) / std`
- Anomaly range validation (typically [-3, +3] sigma)

**Output**:
```
  Rain anomaly (z-score): -0.342
  ✓ Anomaly within expected range
  Temperature anomaly: None (ERA5 integration pending)
```

**Interpretation**:
- **rain_anom = -0.34**: Slightly below average rainfall (0.34 std deviations)
- **rain_anom = +2.1**: Well above average (2.1 std deviations - wet month)
- **rain_anom = -2.8**: Well below average (2.8 std deviations - dry month)

---

### Stage 5: Manifest Generation ✅

Creates `manifest.jsonl` with all tile-month metadata.

**What it tests**:
- JSONL format (one JSON object per line)
- Required fields present:
  - `aoi_id`, `tile_id`, `month`
  - `gcs_uri` (GCS path to GeoTIFF)
  - `rain_anom`, `temp_anom`, `s2_valid_frac`
  - `band_order_version` (must be "v1")
  - `preprocessing_version` (date stamp)
- Schema validation per CONTRACTS.md

**Output**:
```json
{
  "aoi_id": "test-tiny",
  "tile_id": "tile_x000_y000",
  "month": "2023-06",
  "gcs_uri": "gs://siad-test/siad/test-tiny/tile_x000_y000/2023-06.tif",
  "rain_anom": -0.342,
  "temp_anom": null,
  "s2_valid_frac": 0.85,
  "band_order_version": "v1",
  "preprocessing_version": "20260301"
}
```

**File Location**: `data/pipeline_test/manifest.jsonl`

---

### Stage 6: Dataset Loading Validation ✅

Validates that manifest can be consumed by PyTorch training.

**What it tests**:
- Manifest parsing (JSONL format)
- Schema validation (all required fields)
- Dataset structure:
  - Tiles grouped correctly
  - Months per tile count
  - Sufficient context (≥12 months for 6-context + 6-rollout)
- Memory requirements estimate

**Output**:
```
  Dataset structure:
    Tiles: 1
    Months per tile: 3
    Total tile-months: 3
  ⚠ Only 3 months per tile (need 12 for training)
    Add more months to aoi_config for real training
```

**For Real Training**:
- **Minimum**: 12 months per tile (6 context + 6 rollout)
- **Recommended**: 24-36 months (allows multiple train/val splits)

---

## Output Files

After running the test, check `data/pipeline_test/`:

```bash
data/pipeline_test/
├── manifest.jsonl          # Manifest with tile-month metadata
└── (future: sample_tile.tif)  # Optional GeoTIFF export for inspection
```

---

## Common Issues & Solutions

### 1. Earth Engine Authentication Failed

**Error**:
```
✗ Authentication failed: Please authenticate to Earth Engine
```

**Solution**:
```bash
# Authenticate
earthengine authenticate --project YOUR_PROJECT_ID

# Set project ID
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID

# Verify
python -c "import ee; ee.Initialize(project='$GOOGLE_CLOUD_PROJECT'); print('Success')"
```

---

### 2. No Data Available for AOI

**Error**:
```
✗ Required data (S1/S2) not available for this AOI/time period
```

**Solution**:
- **Try different time period**: Some months have high cloud cover or no S2 passes
- **Try different location**: Sicily (14.0-14.1, 37.5-37.6) has excellent data availability
- **Check Sentinel-2 coverage map**: https://s2maps.eu/

**Good Test Locations** (low cloud, high data availability):
- **Sicily, Italy**: `{min_lon: 14.0, max_lon: 14.1, min_lat: 37.5, max_lat: 37.6}`
- **Dubai, UAE**: `{min_lon: 55.2, max_lon: 55.3, min_lat: 25.1, max_lat: 25.2}`
- **Arizona, USA**: `{min_lon: -111.0, max_lon: -110.9, min_lat: 33.0, max_lat: 33.1}`

---

### 3. Request Quota Exceeded

**Error**:
```
✗ Data collection failed: Earth Engine quota exceeded
```

**Solution**:
```bash
# Wait 5-10 minutes for quota reset
# OR reduce AOI size
uv run python scripts/test_data_pipeline.py --aoi-size tiny

# Check EE quota status
earthengine task list
```

---

### 4. Insufficient Months for Training

**Warning**:
```
⚠ Only 3 months per tile (need 12 for training)
```

**Not an Error**: The test passes, but warns that you need more months for real training.

**Solution for Real Training**:
- Increase `months` in AOI config
- Recommended: 24-36 months history
- Update config in `configs/your-aoi.yaml`:
  ```yaml
  data:
    start_month: "2021-01"
    end_month: "2023-12"  # 36 months
  ```

---

## Next Steps After Successful Test

### 1. Create Your AOI Config

```bash
# Copy template
cp configs/quickstart-demo.yaml configs/my-aoi.yaml

# Edit with your bounds and time range
vim configs/my-aoi.yaml
```

Example config:
```yaml
aoi:
  aoi_id: "my-project"
  bounds:
    min_lon: 14.0
    max_lon: 14.5   # 50×50 km AOI
    min_lat: 37.5
    max_lat: 37.9
  projection: "EPSG:3857"
  resolution_m: 10
  tile_size_px: 256

data:
  gcs_bucket: "my-siad-bucket"
  start_month: "2021-01"
  end_month: "2023-12"   # 36 months
  sources: ["s1", "s2", "viirs", "chirps"]
```

### 2. Run Full Data Export

```bash
# Export to GCS (requires GCS bucket)
uv run siad export \
  --config configs/my-aoi.yaml \
  --dry-run  # Validate first

# Remove --dry-run to execute
uv run siad export --config configs/my-aoi.yaml
```

### 3. Train World Model

```bash
# Train on GPU
uv run siad train \
  --config configs/my-aoi.yaml \
  --manifest gs://my-siad-bucket/siad/my-project/manifest.jsonl \
  --output data/models/my-project-v1 \
  --epochs 50 \
  --batch-size 16
```

---

## Performance Benchmarks

On standard cloud VM (4 CPU cores, 16GB RAM):

| AOI Size | Tiles | Months | Runtime | Data Download |
|----------|-------|--------|---------|---------------|
| Tiny     | 1     | 3      | ~2 min  | ~50 MB        |
| Small    | 4     | 6      | ~10 min | ~200 MB       |
| Medium   | 16    | 12     | ~30 min | ~800 MB       |

**Note**: These are Earth Engine API calls, not GCS downloads. Actual GCS exports will be larger and slower.

---

## Troubleshooting

### Enable Debug Logging

```bash
# Set verbose logging
export SIAD_LOG_LEVEL=DEBUG

# Run test
uv run python scripts/test_data_pipeline.py --aoi-size tiny

# Check detailed logs
cat logs/data_pipeline_test.log
```

### Test Individual Components

```python
# Test just EE authentication
python -c "from siad.data.collectors.ee_auth import test_ee_connection; print(test_ee_connection())"

# Test just tile grid generation
python -c "
from siad.data.preprocessing.tiling import generate_tile_grid
tiles = generate_tile_grid(
    {'min_lon': 14.0, 'max_lon': 14.1, 'min_lat': 37.5, 'max_lat': 37.6},
    tile_size_px=256, resolution_m=10
)
print(f'{len(tiles)} tiles generated')
"
```

---

## FAQ

**Q: Do I need a GCS bucket for testing?**
A: No, the test script doesn't upload to GCS. It only validates data collection and preprocessing locally.

**Q: How much does Earth Engine API usage cost?**
A: Earth Engine is free for research and non-commercial use (subject to quota limits).

**Q: Can I test without Earth Engine authentication?**
A: Yes, use `--skip-download` to test only manifest generation and dataset loading:
```bash
uv run python scripts/test_data_pipeline.py --skip-download
```

**Q: What if my region has high cloud cover?**
A: Choose a different time period (summer months typically have less cloud) or a different location (deserts have minimal cloud cover).

**Q: How do I know if my AOI has good data coverage?**
A: Check Sentinel-2 coverage: https://s2maps.eu/
Green = good coverage, Orange/Red = sparse coverage

---

## Support

If the test fails:
1. Check logs: `logs/data_pipeline_test.log`
2. Review error messages in terminal output
3. Consult CONTRACTS.md for data schema requirements
4. Check Earth Engine status: https://status.earthengine.app/

**Constitution Compliance**: This test validates Principle I (Data-Driven Foundation) by ensuring consistent 10m resolution, EPSG:3857 projection, and BAND_ORDER_V1 contract enforcement.
