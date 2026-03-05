# DEM Integration Plan for SIAD

## Overview

Add Digital Elevation Model (DEM) as a 9th input band to SIAD's multi-modal satellite data pipeline. This follows AlphaEarth Foundations' approach of including topographic context for improved geospatial modeling.

---

## Motivation

### Why DEM Matters for Infrastructure Anomaly Detection

1. **Topographic Context:**
   - Infrastructure strongly correlates with terrain (roads follow contours, buildings on flat areas)
   - Elevation changes can indicate construction/excavation
   - Slope and aspect influence infrastructure placement

2. **Terrain-Aware Anomalies:**
   - Unexpected elevation changes could indicate:
     - Construction/demolition activity
     - Mining/excavation
     - Landslides affecting infrastructure
   - Model can learn terrain-conditional infrastructure patterns

3. **Validated Approach:**
   - AlphaEarth Foundations includes Copernicus DEM GLO-30
   - Proven valuable for general geospatial modeling
   - Free and globally available

---

## Data Source

### Copernicus DEM GLO-30

**Earth Engine Asset:** `COPERNICUS/DEM/GLO30`

**Specifications:**
- **Resolution:** 30 meters native (will be resampled to 10m to match SIAD tiles)
- **Coverage:** Global (90°N to 56°S)
- **Vertical Accuracy:** ±4 meters (absolute), ±2 meters (relative)
- **Format:** Single-band raster, elevation in meters above sea level
- **Provider:** European Space Agency (ESA)
- **License:** Free and open (Copernicus data policy)

**Availability in Bay Area:**
- ✅ Full coverage of San Francisco Bay Area
- ✅ Available through Earth Engine without quota limits
- ✅ Pre-processed and analysis-ready

---

## Implementation Plan

### Phase 1: Data Pipeline (Estimated: 2 hours)

#### 1.1 Update Band Configuration

**File:** `src/siad/data/preprocessing/reprojection.py`

**Changes:**
```python
# Update BAND_ORDER_V1 constant (line 16-25)
BAND_ORDER_V1 = [
    "S2_B2",          # Index 0: Sentinel-2 Blue
    "S2_B3",          # Index 1: Sentinel-2 Green
    "S2_B4",          # Index 2: Sentinel-2 Red
    "S2_B8",          # Index 3: Sentinel-2 NIR
    "S1_VV",          # Index 4: Sentinel-1 SAR VV
    "S1_VH",          # Index 5: Sentinel-1 SAR VH
    "VIIRS_avg_rad",  # Index 6: VIIRS nighttime lights
    "S2_valid_mask",  # Index 7: Sentinel-2 valid pixel fraction
    "DEM_elevation"   # Index 8: Copernicus DEM elevation (NEW)
]

# Note: Increment version to BAND_ORDER_V2 or keep V1 with breaking change
```

#### 1.2 Add DEM Collection Function

**File:** `src/siad/data/preprocessing/dem.py` (NEW)

**Contents:**
```python
"""
DEM data collection and preprocessing for SIAD.
"""
import ee
from typing import Optional


def get_dem_image(tile_geom: ee.Geometry) -> ee.Image:
    """
    Get Copernicus DEM GLO-30 elevation data for a tile.

    Args:
        tile_geom: The tile geometry to clip to

    Returns:
        Single-band ee.Image with elevation in meters
    """
    # Load Copernicus DEM GLO-30
    dem = ee.ImageCollection('COPERNICUS/DEM/GLO30') \
        .select('DEM') \
        .mosaic() \
        .clip(tile_geom)

    # DEM is static (no temporal dimension)
    # Same elevation used for all months

    return dem


def preprocess_dem(
    dem_image: ee.Image,
    tile_geom: ee.Geometry,
    fill_value: float = -9999.0
) -> ee.Image:
    """
    Preprocess DEM for SIAD pipeline.

    Args:
        dem_image: Raw DEM image
        tile_geom: Tile geometry
        fill_value: Value for missing/invalid elevations

    Returns:
        Preprocessed DEM image
    """
    # Clip to tile
    dem = dem_image.clip(tile_geom)

    # Convert to float
    dem = dem.toFloat()

    # Fill missing values (oceans, voids)
    dem = dem.unmask(fill_value)

    # Optional: Normalize elevation to [0, 1] range
    # (Can be done in PyTorch dataset instead)

    return dem.rename('DEM_elevation')
```

#### 1.3 Update Reprojection Pipeline

**File:** `src/siad/data/preprocessing/reprojection.py`

**Function:** `reproject_and_stack()` (lines 94-118)

**Changes:**
```python
def reproject_and_stack(
    s1_image: ee.Image,
    s2_image: ee.Image,
    viirs_image: ee.Image,
    dem_image: ee.Image,  # NEW parameter
    tile_geom: ee.Geometry,
    target_crs: str = 'EPSG:3857',
    resolution_m: float = 10.0
) -> ee.Image:
    """
    Reproject and stack all data sources into single 9-band image.

    Args:
        s1_image: Sentinel-1 SAR image
        s2_image: Sentinel-2 optical image
        viirs_image: VIIRS nighttime lights image
        dem_image: Copernicus DEM elevation image (NEW)
        tile_geom: Target tile geometry
        target_crs: Target coordinate reference system
        resolution_m: Target resolution in meters

    Returns:
        Stacked 9-band image in target projection
    """
    # Reproject each source
    s1_reproj = reproject_image(s1_image, target_crs, resolution_m, tile_geom)
    s2_reproj = reproject_image(s2_image, target_crs, resolution_m, tile_geom)
    viirs_reproj = reproject_image(viirs_image, target_crs, resolution_m, tile_geom)
    dem_reproj = reproject_image(dem_image, target_crs, resolution_m, tile_geom)  # NEW

    # Stack bands in BAND_ORDER_V1 (now 9 bands)
    stacked = ee.Image([
        s2_reproj.select('B2'),         # Index 0: Blue
        s2_reproj.select('B3'),         # Index 1: Green
        s2_reproj.select('B4'),         # Index 2: Red
        s2_reproj.select('B8'),         # Index 3: NIR
        s1_reproj.select('VV'),         # Index 4: SAR VV
        s1_reproj.select('VH'),         # Index 5: SAR VH
        viirs_reproj.select('avg_rad'), # Index 6: Nighttime lights
        s2_reproj.select('valid_mask'), # Index 7: Cloud-free fraction
        dem_reproj.select('DEM')        # Index 8: Elevation (NEW)
    ])

    stacked = stacked.rename(BAND_ORDER_V1)
    stacked = stacked.toFloat()
    stacked = stacked.unmask(-9999.0)

    return stacked
```

#### 1.4 Update Export Orchestrator

**File:** `src/siad/data/export_orchestrator.py`

**Function:** `process_tile_month()` (lines ~320-370)

**Changes:**
```python
# Add DEM collection (one-time per tile, reuse across months)
from siad.data.preprocessing.dem import get_dem_image, preprocess_dem

# In __init__ or at tile level:
dem_raw = get_dem_image(tile.geometry)
dem_processed = preprocess_dem(dem_raw, tile.geometry)

# In per-month loop:
stacked = reproject_and_stack(
    s1_composite,
    s2_composite,
    viirs_composite,
    dem_processed,  # NEW: Same DEM for all months (static)
    tile.geometry,
    target_crs=f"EPSG:{tile.utm_zone}",
    resolution_m=self.aoi_config.get('resolution_m', 10)
)
```

**Optimization Note:**
- DEM is static (doesn't change monthly)
- Fetch once per tile, reuse across all 48 months
- Saves 47 redundant DEM fetches per tile

---

### Phase 2: Model Architecture (Estimated: 30 minutes)

#### 2.1 Update Input Channels

**File:** `src/siad/model/world_model.py`

**Current:** `in_channels=8`
**New:** `in_channels=9`

**Changes:**
```python
# Line ~180
self.image_encoder = ImageEncoder(
    in_channels=9,  # Changed from 8
    patch_size=self.model_config.patch_size,
    embed_dim=self.model_config.encoder_dim,
    num_heads=self.model_config.encoder_heads,
    num_layers=self.model_config.encoder_layers,
    mlp_ratio=4.0
)
```

**File:** `src/siad/model/encoder.py`

**Function:** `__init__()` (line ~30)

```python
# Update PatchEmbed
self.patch_embed = nn.Conv2d(
    in_channels=9,  # Changed from 8
    out_channels=embed_dim,
    kernel_size=patch_size,
    stride=patch_size
)
```

#### 2.2 Update Normalization Statistics

**File:** `src/siad/data/transforms.py` or model config

**Action Required:**
- Compute mean/std for elevation band across Bay Area tiles
- Add to normalization constants

**Example:**
```python
BAND_STATS_V2 = {
    'mean': [
        0.1130,  # S2_B2 (Blue)
        0.1286,  # S2_B3 (Green)
        0.1375,  # S2_B4 (Red)
        0.2852,  # S2_B8 (NIR)
        -12.5,   # S1_VV (dB)
        -19.8,   # S1_VH (dB)
        0.85,    # VIIRS_avg_rad
        0.75,    # S2_valid_mask
        150.0    # DEM_elevation (meters) - TO BE COMPUTED
    ],
    'std': [
        0.0523,  # S2_B2
        0.0497,  # S2_B3
        0.0613,  # S2_B4
        0.1286,  # S2_B8
        3.2,     # S1_VV
        4.1,     # S1_VH
        2.3,     # VIIRS_avg_rad
        0.15,    # S2_valid_mask
        80.0     # DEM_elevation - TO BE COMPUTED
    ]
}
```

**Compute Script:**
```bash
# Run after first export batch completes
uv run python scripts/compute_band_stats.py \
  --manifest data/exports/test-export-v03_manifest.jsonl \
  --band-idx 8 \
  --output configs/band_stats_v2.json
```

---

### Phase 3: Configuration Updates (Estimated: 15 minutes)

#### 3.1 Update Export Configs

**Files:**
- `configs/test-export-v03.yaml`
- `configs/export-bay-area-full.yaml`

**Add Section:**
```yaml
data_sources:
  sentinel2: true
  sentinel1: true
  viirs: true
  chirps: true
  dem: true  # NEW

dem_config:
  source: "COPERNICUS/DEM/GLO30"
  band: "DEM"
  fill_value: -9999.0
  resample_method: "bilinear"  # Good for continuous elevation data
```

#### 3.2 Update Training Configs

**Files:**
- `configs/train-bay-area-v03.yaml`

**Changes:**
```yaml
data:
  num_bands: 9  # Changed from 8
  band_order_version: "v2"  # Increment version

model:
  in_channels: 9  # Changed from 8
```

---

### Phase 4: Testing & Validation (Estimated: 1 hour)

#### 4.1 Unit Tests

**File:** `tests/unit/test_dem_integration.py` (NEW)

**Test Cases:**
```python
def test_get_dem_image():
    """Test DEM collection from Earth Engine."""
    # Create test tile in Bay Area
    # Fetch DEM
    # Verify non-null elevation values

def test_dem_reprojection():
    """Test DEM resampling from 30m to 10m."""
    # Verify interpolation quality
    # Check for artifacts at tile boundaries

def test_9band_stacking():
    """Test stacking with DEM as 9th band."""
    # Verify band order
    # Verify dimensions (256x256x9)
    # Verify DEM in correct position (index 8)

def test_static_dem_reuse():
    """Test DEM is reused across months."""
    # Verify same DEM used for multiple months
    # Verify no redundant fetches
```

#### 4.2 Integration Test

**Export Single Tile:**
```bash
# Create minimal test config (1 tile, 2 months)
uv run siad export \
  --config configs/test-dem-integration.yaml \
  --tiles 1 \
  --months 2021-01,2021-02

# Verify output:
# - 2 GeoTIFF files created
# - Each has 9 bands
# - Band 8 has elevation values
# - Elevation is identical in both months (static)
```

#### 4.3 Validation Checks

```bash
# Check band count
gdalinfo gs://siad-exports/siad/test-dem/tile_x000_y000/2021-01.tif | grep "Band "

# Expected output:
# Band 1 Block=256x256 Type=Float32, ColorInterp=Gray  # S2_B2
# Band 2 Block=256x256 Type=Float32, ColorInterp=Undefined  # S2_B3
# ...
# Band 9 Block=256x256 Type=Float32, ColorInterp=Undefined  # DEM

# Visualize elevation band
uv run python scripts/visualize_dem.py \
  --geotiff gs://siad-exports/siad/test-dem/tile_x000_y000/2021-01.tif \
  --band 8 \
  --output /tmp/dem_viz.png
```

---

## Migration Strategy

### Option A: Non-Breaking (Recommended)

**Approach:** Run separate export with DEM, keep existing 8-band data

**Steps:**
1. Create new config: `configs/export-bay-area-v04-with-dem.yaml`
2. Export to new GCS path: `gs://siad-exports/siad/bay-area-v04/`
3. Train two models:
   - Baseline: 8-band (v03 data)
   - Enhanced: 9-band (v04 data)
4. Compare performance
5. If DEM improves results, use v04 going forward

**Pros:**
- No data loss
- Can compare with/without DEM
- Backwards compatible

**Cons:**
- Need to re-export all data (~6-8 days)
- Doubles storage costs temporarily

---

### Option B: In-Place Upgrade (Faster but Risky)

**Approach:** Add DEM as 9th band to existing export

**Steps:**
1. Wait for v03 export to complete (currently 25% done)
2. Re-export all 11,232 samples with DEM included
3. Overwrite existing v03 GeoTIFFs

**Pros:**
- Only one dataset to manage
- Faster to production

**Cons:**
- Lose existing 2,827 completed samples
- Cannot compare with/without DEM
- Must restart export from scratch

---

### Option C: Incremental (Best of Both)

**Approach:** Add DEM starting from next export batch

**Steps:**
1. Let current v03 export complete (6-8 days)
2. Train baseline model on 8-band v03 data
3. For next region/timeframe, export with DEM (9-band)
4. Fine-tune baseline model with new 9-band data

**Pros:**
- Immediate training with existing data
- Gradual migration
- Can quantify DEM contribution

**Cons:**
- Mixed dataset versions
- More complex data management

---

## Recommended Timeline

### Immediate (Now):
- ✅ Document this plan
- ✅ Create issue/task for DEM integration

### After v03 Export Completes (~March 12):
- ✅ Complete Phase 1-3 implementation (3 hours)
- ✅ Run integration tests (1 hour)
- ✅ Export single tile with DEM for validation

### After Baseline Training (TBD):
- ✅ Decide on migration strategy (A, B, or C)
- ✅ Export full dataset with DEM (if using Option A or B)
- ✅ Train enhanced model with 9-band input
- ✅ Compare performance: 8-band vs 9-band

---

## Performance Implications

### Computational Cost

**Export Time:**
- DEM fetch: ~0.5 seconds per tile (one-time)
- DEM reproject: ~0.3 seconds per month
- Total per 48-month tile: ~0.5 + (0.3 × 48) = ~15 seconds
- Impact: +15 sec / ~300 sec = **5% slower export**

**Storage:**
- 8-band GeoTIFF: ~2.6 MB per sample
- 9-band GeoTIFF: ~2.9 MB per sample (+12%)
- Total dataset: 11,232 × 2.9 MB = **~32 GB** (vs 29 GB)

**Training:**
- 8-band input: 256×256×8 = 524,288 values
- 9-band input: 256×256×9 = 589,824 values (+12%)
- GPU memory: +12% per batch
- Training time: +5-10% (more parameters, same architecture)

**Model Size:**
- Patch embedding: 9 channels × patch_size² × embed_dim
- Adds ~0.5-1 MB to model weights (negligible)

---

## Expected Benefits

### Quantitative (To Be Measured)

**Hypothesis:** DEM will improve anomaly detection by providing terrain context

**Metrics to Track:**
1. **Reconstruction loss:** Should decrease (model has more info)
2. **Anomaly detection F1:** May improve for terrain-related anomalies
3. **False positive rate:** May decrease (terrain explains some "anomalies")

### Qualitative Benefits

1. **Terrain-Aware Learning:**
   - Model learns that roads follow valleys
   - Buildings prefer flat areas
   - Infrastructure density varies with elevation

2. **Better Anomaly Attribution:**
   - Can distinguish: "building on steep slope" (anomalous) vs "building on flat land" (normal)
   - Elevation changes help identify excavation/construction

3. **Validated Approach:**
   - AlphaEarth uses DEM → proven valuable for geospatial modeling
   - Low risk, high potential upside

---

## Risks & Mitigations

### Risk 1: Elevation Noise

**Problem:** 30m DEM resampled to 10m may introduce interpolation artifacts

**Mitigation:**
- Use bilinear interpolation (smooth)
- Validate on test tiles first
- Compare with 10m DEM if available (TanDEM-X)

### Risk 2: Static Data Concerns

**Problem:** DEM is static, doesn't change monthly (unlike other bands)

**Mitigation:**
- This is actually a feature! Provides stable reference frame
- Model can learn to use elevation as "anchor" for other changing bands
- AlphaEarth uses static DEM successfully

### Risk 3: Bay Area Elevation Range

**Problem:** Bay Area has extreme elevation range (sea level to 1,200m peaks)

**Mitigation:**
- Normalize elevation by Bay Area statistics (not global)
- Compute percentile-based normalization if needed
- Consider elevation relative to tile mean (detrending)

---

## Success Criteria

DEM integration is successful if:

1. ✅ **Export Pipeline:**
   - 9-band GeoTIFFs generated correctly
   - Band 8 contains valid elevation values
   - No performance degradation (export time <10% slower)

2. ✅ **Model Training:**
   - Model trains successfully with 9 channels
   - Convergence as fast or faster than 8-band baseline
   - No gradient issues or NaN losses

3. ✅ **Performance Improvement:**
   - Reconstruction loss ≤ baseline (ideally lower)
   - Anomaly detection metrics ≥ baseline
   - Qualitative improvement in terrain-aware predictions

---

## Files to Create/Modify

### New Files:
1. `src/siad/data/preprocessing/dem.py` - DEM collection/preprocessing
2. `tests/unit/test_dem_integration.py` - Unit tests
3. `configs/test-dem-integration.yaml` - Test export config
4. `scripts/compute_band_stats.py` - Compute DEM normalization stats
5. `scripts/visualize_dem.py` - Visualization utility
6. `docs/DEM_INTEGRATION_PLAN.md` - This document

### Modified Files:
1. `src/siad/data/preprocessing/reprojection.py` - Add DEM to stacking
2. `src/siad/data/export_orchestrator.py` - Integrate DEM collection
3. `src/siad/model/world_model.py` - Update in_channels=9
4. `src/siad/model/encoder.py` - Update patch embedding
5. `configs/train-bay-area-v03.yaml` - Update for 9 bands
6. `configs/export-bay-area-full.yaml` - Add DEM config section

---

## References

1. **Copernicus DEM:**
   - Earth Engine: `COPERNICUS/DEM/GLO30`
   - Documentation: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30

2. **AlphaEarth Foundations:**
   - Paper: https://arxiv.org/abs/2507.22291
   - Uses DEM as core input alongside optical/SAR data

3. **SIAD v0.3 Spec:**
   - `docs/MODEL.md` - Current 8-band architecture
   - Will need update for 9-band version

---

## Status

**Current:** ⏸️ **PLANNED** (Not yet implemented)

**Next Action:** Wait for v03 export completion, then implement Phase 1-3

**Owner:** TBD

**Priority:** Medium (valuable but not blocking baseline training)

**Estimated Total Effort:** 4-5 hours implementation + 6-8 days re-export (if needed)
