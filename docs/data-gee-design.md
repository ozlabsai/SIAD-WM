# Data/GEE Pipeline - Design Document

**Version**: 1.0.0
**Date**: 2026-03-01
**Owner**: Data/GEE Pipeline Agent
**Status**: Implementation Ready

## 1. Overview

The Data/GEE Pipeline is responsible for collecting multi-modal satellite imagery from Google Earth Engine, performing monthly compositing, tiling, reprojection, and exporting to Google Cloud Storage (GCS) with metadata manifests. This pipeline enforces the BAND_ORDER_V1 contract and provides the foundational data layer for the SIAD MVP.

## 2. Earth Engine Collection Recipes

### 2.1 Sentinel-1 SAR (VV/VH Bands)

**Collection**: `COPERNICUS/S1_GRD`

**Recipe**:
```python
def collect_sentinel1(aoi_bounds, start_date, end_date):
    """
    Collect Sentinel-1 SAR VV/VH bands for monthly compositing.

    Args:
        aoi_bounds: ee.Geometry representing AOI
        start_date: ISO string "YYYY-MM-DD"
        end_date: ISO string "YYYY-MM-DD"

    Returns:
        ee.Image with bands ['VV', 'VH']
    """
    s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
        .filterBounds(aoi_bounds) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
        .filter(ee.Filter.eq('instrumentMode', 'IW')) \
        .select(['VV', 'VH'])

    # Monthly median composite (robust to outliers)
    composite = s1.median()

    return composite
```

**Rationale**:
- Median aggregation reduces speckle noise
- IW (Interferometric Wide) mode is standard for land monitoring
- VV/VH polarizations capture structural properties

### 2.2 Sentinel-2 Optical (B2/B3/B4/B8 + Cloud Masking)

**Collection**: `COPERNICUS/S2_SR_HARMONIZED`

**Recipe**:
```python
def collect_sentinel2(aoi_bounds, start_date, end_date):
    """
    Collect Sentinel-2 optical bands with cloud masking.

    Args:
        aoi_bounds: ee.Geometry
        start_date: ISO string "YYYY-MM-DD"
        end_date: ISO string "YYYY-MM-DD"

    Returns:
        ee.Image with bands ['B2', 'B3', 'B4', 'B8', 'valid_mask']
    """
    def mask_clouds(image):
        # Use SCL (Scene Classification Layer) to mask clouds/shadows
        scl = image.select('SCL')
        # Keep vegetation(4), bare soil(5), water(6), snow(11)
        # Mask clouds(8,9), cloud shadows(3), saturated(1)
        valid_mask = scl.neq(1).And(scl.neq(3)) \
                        .And(scl.neq(8).And(scl.neq(9).And(scl.neq(10))))
        return image.updateMask(valid_mask)

    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi_bounds) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 80)) \
        .map(mask_clouds) \
        .select(['B2', 'B3', 'B4', 'B8'])

    # Monthly median composite
    composite = s2.median()

    # Compute valid pixel fraction
    valid_count = s2.count().select('B2')
    total_count = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi_bounds) \
        .filterDate(start_date, end_date) \
        .count().select('B2')

    valid_frac = valid_count.divide(total_count.max(1))  # Avoid div by zero

    return composite.addBands(valid_frac.rename('valid_mask'))
```

**Rationale**:
- SCL provides robust cloud/shadow masking
- Median reduces cloud remnants and sensor noise
- Valid pixel fraction enables filtering low-quality tiles

### 2.3 VIIRS Nighttime Lights

**Collection**: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`

**Recipe**:
```python
def collect_viirs(aoi_bounds, start_date, end_date):
    """
    Collect VIIRS monthly nighttime lights.

    Args:
        aoi_bounds: ee.Geometry
        start_date: ISO string "YYYY-MM-DD"
        end_date: ISO string "YYYY-MM-DD"

    Returns:
        ee.Image with band ['avg_rad']
    """
    viirs = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG') \
        .filterBounds(aoi_bounds) \
        .filterDate(start_date, end_date) \
        .select('avg_rad')

    # Mean (lights don't need median, already monthly product)
    composite = viirs.mean()

    return composite
```

**Rationale**:
- VIIRS is already monthly composite product
- Mean is appropriate (lights are stable, no outliers like clouds)

### 2.4 CHIRPS Rainfall

**Collection**: `UCSB-CHG/CHIRPS/DAILY`

**Recipe**:
```python
def collect_chirps(aoi_bounds, start_date, end_date, baseline_stats):
    """
    Collect CHIRPS rainfall and compute z-score anomaly.

    Args:
        aoi_bounds: ee.Geometry
        start_date: ISO string "YYYY-MM-DD"
        end_date: ISO string "YYYY-MM-DD"
        baseline_stats: dict with {month: {mean, std}} for 1-12

    Returns:
        ee.Image with band ['precipitation']
        float: rain_anom (z-score for manifest)
    """
    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
        .filterBounds(aoi_bounds) \
        .filterDate(start_date, end_date) \
        .select('precipitation')

    # Monthly sum
    monthly_precip = chirps.sum()

    # Compute spatial mean over AOI
    mean_val = monthly_precip.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi_bounds,
        scale=5000,  # 5km for rainfall (coarse)
        maxPixels=1e9
    ).get('precipitation')

    # Convert to z-score using baseline
    month = int(start_date.split('-')[1])
    baseline_mean = baseline_stats[month]['mean']
    baseline_std = baseline_stats[month]['std']

    rain_anom = (mean_val - baseline_mean) / (baseline_std + 1e-6)

    return monthly_precip, rain_anom
```

**Rationale**:
- CHIRPS daily data aggregated to monthly sum
- Z-score computed per month-of-year (accounts for seasonality)
- Spatial mean over AOI becomes scalar action for manifest

### 2.5 ERA5 Temperature (Optional)

**Collection**: `ECMWF/ERA5/MONTHLY`

**Recipe**:
```python
def collect_era5(aoi_bounds, start_date, end_date, baseline_stats):
    """
    Collect ERA5 2m temperature and compute z-score anomaly.

    Args:
        aoi_bounds: ee.Geometry
        start_date: ISO string "YYYY-MM-DD"
        end_date: ISO string "YYYY-MM-DD"
        baseline_stats: dict with {month: {mean, std}}

    Returns:
        float: temp_anom (z-score for manifest)
    """
    era5 = ee.ImageCollection('ECMWF/ERA5/MONTHLY') \
        .filterBounds(aoi_bounds) \
        .filterDate(start_date, end_date) \
        .select('mean_2m_air_temperature')

    monthly_temp = era5.first()

    # Spatial mean over AOI
    mean_val = monthly_temp.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi_bounds,
        scale=10000,  # 10km for ERA5
        maxPixels=1e9
    ).get('mean_2m_air_temperature')

    # Convert to z-score
    month = int(start_date.split('-')[1])
    baseline_mean = baseline_stats[month]['mean']
    baseline_std = baseline_stats[month]['std']

    temp_anom = (mean_val - baseline_mean) / (baseline_std + 1e-6)

    return temp_anom
```

## 3. Monthly Compositing Strategy

### 3.1 Aggregation Methods

| Source | Method | Rationale |
|--------|--------|-----------|
| Sentinel-1 | Median | Reduces speckle, robust to outliers |
| Sentinel-2 | Median (cloud-masked) | Removes cloud remnants |
| VIIRS | Mean | Already monthly, no outliers |
| CHIRPS | Sum | Accumulate daily rainfall |
| ERA5 | First (already monthly) | Native monthly product |

### 3.2 Temporal Windows

- **Calendar month boundaries**: 1st to last day of month
- **Date format**: ISO 8601 ("YYYY-MM-DD")
- **Time zone**: UTC (EE default)

### 3.3 Handling Missing Data

- **S2 valid fraction < 0.3**: Skip tile for that month (log warning)
- **S1 no data**: Skip month (SAR required for structural detection)
- **VIIRS no data**: Use 0.0 (lights can be absent in rural areas)
- **CHIRPS/ERA5 no data**: Use rain_anom=0.0, temp_anom=null

## 4. Tiling Algorithm

### 4.1 Grid Generation

**Input**: AOI bounding box `(min_lon, max_lon, min_lat, max_lat)`

**Process**:
```python
def generate_tile_grid(bounds, resolution_m=10, tile_size_px=256, projection='EPSG:3857'):
    """
    Generate non-overlapping tile grid for AOI.

    Args:
        bounds: dict with {min_lon, max_lon, min_lat, max_lat}
        resolution_m: meters per pixel (default 10m)
        tile_size_px: tile size in pixels (default 256)
        projection: target projection (default EPSG:3857)

    Returns:
        list of tile dicts: [{tile_id, bounds, geometry}]
    """
    # Convert bounds to target projection
    proj = ee.Projection(projection)
    aoi_geom = ee.Geometry.Rectangle([
        bounds['min_lon'], bounds['min_lat'],
        bounds['max_lon'], bounds['max_lat']
    ], proj='EPSG:4326').transform(proj, 1)

    # Get projected bounds
    aoi_bounds = aoi_geom.bounds().coordinates().get(0).getInfo()
    min_x, min_y = aoi_bounds[0]
    max_x, max_y = aoi_bounds[2]

    # Tile size in meters
    tile_size_m = tile_size_px * resolution_m  # 256 * 10 = 2560m

    # Generate grid
    tiles = []
    x = min_x
    ix = 0
    while x < max_x:
        y = min_y
        iy = 0
        while y < max_y:
            tile_id = f"tile_x{ix:03d}_y{iy:03d}"
            tile_bounds = ee.Geometry.Rectangle([x, y, x+tile_size_m, y+tile_size_m], proj=proj)
            tiles.append({
                'tile_id': tile_id,
                'bounds': [x, y, x+tile_size_m, y+tile_size_m],
                'geometry': tile_bounds
            })
            y += tile_size_m
            iy += 1
        x += tile_size_m
        ix += 1

    return tiles
```

### 4.2 Tile Properties

- **Size**: 256×256 pixels
- **Resolution**: 10m (2.56 km square)
- **Projection**: EPSG:3857 (Web Mercator)
- **Overlap**: None (stride = 256)
- **Naming**: `tile_x{ix:03d}_y{iy:03d}` (zero-padded)

## 5. Reprojection and Band Stacking

### 5.1 Reprojection Parameters

**Target**:
- **CRS**: EPSG:3857
- **Resolution**: 10m
- **Resampling**: Bilinear for continuous data, nearest for masks

**Implementation**:
```python
def reproject_and_stack(s1, s2, viirs, tile_geom):
    """
    Reproject all sources to EPSG:3857 at 10m and stack bands.

    Args:
        s1: ee.Image (VV, VH)
        s2: ee.Image (B2, B3, B4, B8, valid_mask)
        viirs: ee.Image (avg_rad)
        tile_geom: ee.Geometry (tile bounds)

    Returns:
        ee.Image with 8 bands in BAND_ORDER_V1
    """
    proj = ee.Projection('EPSG:3857').atScale(10)

    # Reproject each source
    s1_reproj = s1.reproject(proj).clip(tile_geom)
    s2_reproj = s2.reproject(proj).clip(tile_geom)
    viirs_reproj = viirs.reproject(proj).clip(tile_geom)

    # Stack bands in BAND_ORDER_V1
    stacked = ee.Image([
        s2_reproj.select('B2'),
        s2_reproj.select('B3'),
        s2_reproj.select('B4'),
        s2_reproj.select('B8'),
        s1_reproj.select('VV'),
        s1_reproj.select('VH'),
        viirs_reproj.select('avg_rad'),
        s2_reproj.select('valid_mask')
    ])

    # Rename to standard band names
    stacked = stacked.rename([
        'S2_B2', 'S2_B3', 'S2_B4', 'S2_B8',
        'S1_VV', 'S1_VH', 'VIIRS_avg_rad', 'S2_valid_mask'
    ])

    return stacked.toFloat()  # Ensure Float32
```

### 5.2 Band Order Enforcement

**BAND_ORDER_V1** (index 0-7):
1. S2_B2 (Blue)
2. S2_B3 (Green)
3. S2_B4 (Red)
4. S2_B8 (NIR)
5. S1_VV (SAR)
6. S1_VH (SAR)
7. VIIRS_avg_rad (Lights)
8. S2_valid_mask (Quality)

This order is IMMUTABLE in MVP. Any changes require new band_order_v2.

## 6. GCS Export Strategy

### 6.1 Export Layout

```
gs://<bucket>/siad/<aoi_id>/<tile_id>/<YYYY-MM>.tif
gs://<bucket>/siad/<aoi_id>/manifest.jsonl
```

**Example**:
```
gs://siad-exports/siad/quickstart-demo/tile_x000_y000/2023-01.tif
gs://siad-exports/siad/quickstart-demo/tile_x000_y000/2023-02.tif
...
gs://siad-exports/siad/quickstart-demo/manifest.jsonl
```

### 6.2 Batching Strategy

**Problem**: Earth Engine has concurrent task limits (~300-3000 depending on quota)

**Solution**: Batch exports by month
```python
def export_month_batch(aoi_id, tiles, month, bucket, max_concurrent=100):
    """
    Export all tiles for a single month with concurrency control.

    Args:
        aoi_id: AOI identifier
        tiles: list of tile dicts
        month: "YYYY-MM"
        bucket: GCS bucket name
        max_concurrent: max concurrent EE tasks

    Returns:
        list of task IDs
    """
    tasks = []
    for tile in tiles:
        # Generate stacked image for tile
        image = collect_and_stack_tile(tile, month)

        # Export configuration
        task = ee.batch.Export.image.toCloudStorage(
            image=image,
            description=f"{aoi_id}_{tile['tile_id']}_{month}",
            bucket=bucket,
            fileNamePrefix=f"siad/{aoi_id}/{tile['tile_id']}/{month}",
            region=tile['geometry'],
            scale=10,
            crs='EPSG:3857',
            maxPixels=1e9,
            fileFormat='GeoTIFF',
            formatOptions={'cloudOptimized': True}
        )

        task.start()
        tasks.append(task)

        # Throttle if needed
        if len(tasks) % max_concurrent == 0:
            wait_for_tasks(tasks[-max_concurrent:])

    return tasks
```

### 6.3 Task Monitoring

```python
import time

def wait_for_tasks(tasks, check_interval=60):
    """
    Wait for EE tasks to complete.

    Args:
        tasks: list of ee.batch.Task
        check_interval: seconds between checks
    """
    while True:
        statuses = [t.status()['state'] for t in tasks]

        if all(s in ['COMPLETED', 'FAILED', 'CANCELLED'] for s in statuses):
            break

        running = sum(1 for s in statuses if s == 'RUNNING')
        pending = sum(1 for s in statuses if s in ['READY', 'PENDING'])
        completed = sum(1 for s in statuses if s == 'COMPLETED')
        failed = sum(1 for s in statuses if s == 'FAILED')

        print(f"Running: {running}, Pending: {pending}, "
              f"Completed: {completed}, Failed: {failed}")

        time.sleep(check_interval)

    # Log failures
    for task in tasks:
        status = task.status()
        if status['state'] == 'FAILED':
            print(f"FAILED: {status['description']} - {status.get('error_message')}")
```

## 7. Manifest Generation

### 7.1 Manifest Schema (JSONL)

Each line is a JSON object:
```json
{
  "aoi_id": "quickstart-demo",
  "tile_id": "tile_x000_y000",
  "month": "2023-01",
  "gcs_uri": "gs://siad-exports/siad/quickstart-demo/tile_x000_y000/2023-01.tif",
  "rain_anom": -0.35,
  "temp_anom": 0.12,
  "s2_valid_frac": 0.87,
  "band_order_version": "v1",
  "preprocessing_version": "20260228"
}
```

### 7.2 Generation Process

```python
import json

def generate_manifest(aoi_id, tiles, months, bucket, baseline_stats, output_path):
    """
    Generate manifest.jsonl for all exported tiles.

    Args:
        aoi_id: AOI identifier
        tiles: list of tile dicts
        months: list of "YYYY-MM" strings
        bucket: GCS bucket name
        baseline_stats: dict with CHIRPS/ERA5 baseline stats
        output_path: local path to manifest.jsonl (will upload to GCS)
    """
    with open(output_path, 'w') as f:
        for month in months:
            # Compute actions for month
            rain_anom = compute_rain_anomaly(aoi_id, month, baseline_stats)
            temp_anom = compute_temp_anomaly(aoi_id, month, baseline_stats)

            for tile in tiles:
                # Check if tile export succeeded
                gcs_uri = f"gs://{bucket}/siad/{aoi_id}/{tile['tile_id']}/{month}.tif"
                if not gcs_file_exists(gcs_uri):
                    continue  # Skip missing tiles

                # Compute S2 valid fraction
                s2_valid_frac = compute_s2_valid_fraction(tile, month)

                # Skip low-quality tiles
                if s2_valid_frac < 0.3:
                    print(f"Skipping {tile['tile_id']}/{month}: low valid fraction")
                    continue

                # Write manifest row
                row = {
                    'aoi_id': aoi_id,
                    'tile_id': tile['tile_id'],
                    'month': month,
                    'gcs_uri': gcs_uri,
                    'rain_anom': float(rain_anom),
                    'temp_anom': float(temp_anom) if temp_anom is not None else None,
                    's2_valid_frac': float(s2_valid_frac),
                    'band_order_version': 'v1',
                    'preprocessing_version': '20260228'
                }

                f.write(json.dumps(row) + '\n')

    # Upload to GCS
    upload_to_gcs(output_path, f"gs://{bucket}/siad/{aoi_id}/manifest.jsonl")
```

## 8. Failure Modes and Mitigations

### 8.1 Earth Engine Quota Exceeded

**Symptom**: Tasks stuck in PENDING, 429 errors

**Mitigation**:
1. Reduce `max_concurrent` to 50
2. Add exponential backoff between batches
3. Implement retry logic with jitter

**Code**:
```python
import random

def export_with_retry(task_fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            task = task_fn()
            task.start()
            return task
        except ee.EEException as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limited, retrying in {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                raise
```

### 8.2 Network Errors

**Symptom**: Connection timeouts, incomplete exports

**Mitigation**:
1. Use `ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')`
2. Implement task status polling with timeout
3. Re-export failed tiles only

### 8.3 Missing Data Months

**Symptom**: No Sentinel-2 data (heavy clouds), no SAR data (sensor gap)

**Mitigation**:
1. Track missing tiles per month in separate log file
2. Skip tiles with S2_valid_frac < 0.3
3. Require SAR presence (abort if no S1 data for >1 week in month)
4. Continue pipeline with partial tiles (log warnings)

### 8.4 GCS Upload Failures

**Symptom**: Tasks complete but files not in GCS

**Mitigation**:
1. Verify GCS bucket exists and has write permissions
2. Use EE service account with Storage Admin role
3. Poll GCS after task completion to confirm file presence
4. Re-run exports for missing files

## 9. Testing Plan

### 9.1 Smoke Test Scope

**Objective**: Verify end-to-end pipeline with minimal data

**Test Configuration**:
- AOI: 10×10 km (4×4 tiles = 16 tiles)
- Time range: 2 months (Jan-Feb 2023)
- Total exports: 32 GeoTIFFs

**Test Steps**:
1. Authenticate EE
2. Generate tile grid
3. Export all tiles for 2 months
4. Wait for tasks
5. Verify GCS files exist
6. Generate manifest.jsonl
7. Validate manifest schema
8. Spot-check 1 GeoTIFF:
   - 8 bands
   - 256×256 pixels
   - EPSG:3857
   - Float32 dtype
   - NoData = -9999.0

**Success Criteria**:
- All 32 exports COMPLETED
- manifest.jsonl has 32 rows
- No FAILED tasks
- Runtime < 10 minutes

### 9.2 Integration Test (Future)

- Full quickstart AOI (50×50 km, 36 months)
- Test all collectors (S1, S2, VIIRS, CHIRPS, ERA5)
- Validate action anomaly computation
- Test low-quality tile filtering

### 9.3 Unit Tests (Future)

- `test_tile_grid_generation()`: Verify grid bounds
- `test_band_stacking()`: Verify BAND_ORDER_V1
- `test_manifest_validation()`: Schema compliance
- `test_anomaly_computation()`: Z-score math

## 10. Performance Estimates

### 10.1 Export Time

**Variables**:
- Tile count: N_tiles
- Month count: N_months
- Concurrent tasks: C (default 100)

**Formula**:
```
Total tasks = N_tiles × N_months
Time per task ≈ 2-5 minutes (EE processing)
Total time ≈ (Total tasks / C) × 3 minutes
```

**Example** (quickstart):
- 50×50 km @ 2.56km tiles = ~20×20 = 400 tiles
- 36 months
- Total: 14,400 tasks
- Time: (14,400 / 100) × 3 = 432 minutes = 7.2 hours

**Optimization**:
- Use higher concurrency if quota allows (C=300 → 2.4 hours)
- Process months in parallel (separate workers)

### 10.2 Data Volume

**Per tile per month**:
- 8 bands × 256×256 pixels × 4 bytes (Float32) = 2 MB
- With GeoTIFF compression (~50%): 1 MB

**Full dataset**:
- 14,400 tiles × 1 MB = 14.4 GB

**GCS Costs** (us-central1):
- Storage: $0.02/GB/month → $0.29/month
- Egress (to Compute Engine): Free (same region)

## 11. Dependencies

### 11.1 Python Packages

```toml
[project.dependencies]
earthengine-api = ">=0.1.400"
google-cloud-storage = ">=2.14.0"
rasterio = ">=1.3.9"
numpy = ">=1.26.0"
```

### 11.2 External Services

- Earth Engine authenticated account
- GCS bucket with write permissions
- Service account with roles:
  - Earth Engine Resource Writer
  - Storage Object Admin

### 11.3 Configuration Files

- `configs/<aoi_id>.yaml`: AOI bounds, months, bucket
- `.ee/credentials`: EE authentication token

## 12. Open Questions

1. **GCS bucket name**: Need from Infra agent (config schema)
2. **EE quota limits**: Confirm max concurrent tasks for project
3. **Baseline statistics**: Who computes CHIRPS/ERA5 baselines? (Assume Actions agent provides)
4. **HDF5 vs GeoTIFF**: Tasks.md mentions HDF5 (T020), but CLI contract shows GeoTIFF exports. Clarify with Actions agent.

## 13. Next Steps

1. Create code skeleton (collectors, preprocessing modules)
2. Implement smoke test (1 tile × 2 months)
3. Coordinate with Infra agent on config schema
4. Coordinate with Actions agent on baseline stats handoff
5. Run smoke test and validate outputs
6. Document any deviations or issues

---

**Changelog**:
- 2026-03-01: Initial design document
