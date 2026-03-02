Great — here’s the **Earth Engine “collection recipe”** and an **export strategy** written for **Python (ee API)**, designed to be dropped into a multi-agent build pipeline. I’m giving you:

* Exact dataset IDs
* Exact filters
* Monthly compositing pseudocode (near-code, but still readable)
* A robust tiling scheme
* Per-tile/per-month export plan (Cloud Storage recommended) + manifest
* Notes on gotchas (S2 masking, S1 angle/orbit consistency, VIIRS normalization)

I’ll keep it “implementation ready” but not lock you into one coding style.

---

# A) Python Earth Engine Setup

### Dependencies

* `earthengine-api`
* `geemap` (optional, convenient for debugging)
* `shapely`, `geojson`, `pyproj` (optional for AOI/tiling locally)

### Initialization

* Use service account or interactive auth
* Set a project (recommended)

Pseudocode:

```python
import ee
ee.Initialize(project='YOUR_GCP_PROJECT_ID')  # or ee.Authenticate() then ee.Initialize()
```

---

# B) Dataset IDs and band contracts

## Core state

* Sentinel-1: `COPERNICUS/S1_GRD` bands: `VV`, `VH` (+ optional `angle`)
* Sentinel-2 SR: `COPERNICUS/S2_SR` bands: `B2 B3 B4 B8` (+ optional `B11`)
* S2 cloud prob: `COPERNICUS/S2_CLOUD_PROBABILITY` band: `probability`
* VIIRS monthly: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG` band: `avg_rad`

## Actions/context

* CHIRPS daily: `UCSB-CHG/CHIRPS/DAILY` band: `precipitation`
* ERA5 monthly (optional): `ECMWF/ERA5/MONTHLY` var: `mean_2m_air_temperature`

Optional helpers:

* DEM: `USGS/SRTMGL1_003`

---

# C) AOI tiling recipe (Python + EE)

## C1) Inputs

* AOI polygon (GeoJSON)
* Tile size in meters (recommend 2560m ≈ 256px * 10m)
* Stride (same as tile for non-overlap; half for overlap)

## C2) Tiling strategy

Two good options:

### Option 1: EE-native grid using bounds + stepping in projected coords

* Reproject AOI bounds to EPSG:3857
* Build a list of rectangles

### Option 2 (simpler): use an H3/S2 grid externally and convert to EE polygons

For MVP, Option 1 is easiest.

**EE-native pseudocode approach:**

1. `aoi = ee.Geometry.Polygon(...)`
2. `bounds = aoi.bounds(1)`
3. Create a feature collection of tiles via a sequence of x/y steps.

> Implementation note: EE doesn’t have a “for loop” in Python; you usually generate lists client-side and map them into EE geometries, or use `ee.List.sequence` + `map`. For large AOIs, client-side generation is fine (few thousand tiles max).

**Tile feature schema:**

* `tile_id` (string)
* `geom` (Polygon)
* `x_idx`, `y_idx` for reproducibility

---

# D) Monthly time index recipe

Define:

* `start_date` (YYYY-MM-01)
* `end_date` (exclusive)
* generate months: `[(y,m) ...]`

In EE, you can:

* create an `ee.List` of month starts
* map a function over the list

For MVP, generating month list in Python and iterating exports is practical.

---

# E) Preprocessing functions (EE recipes)

## E1) Sentinel-2: cloud mask + monthly median composite + valid mask

### Join S2_SR with cloud probability

**Key idea:** join by `system:index`

Recipe:

1. `s2 = ee.ImageCollection('COPERNICUS/S2_SR')`
2. `s2cp = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')`
3. Join collections on `system:index`
4. For each joined image, mask pixels where cloud prob > threshold

**Mask threshold:** start with 50. Tune.

**Outputs per image:**

* masked reflectance bands
* `s2_valid_mask` band: 1 for valid pixels else 0

**Monthly composite:**

* median of masked reflectance
* `valid_frac` = mean of valid mask within tile (reduceRegion)

**Scaling:** S2 SR scale factor is typically 1e4; divide to get [0,1] reflectance.

---

## E2) Sentinel-1: filter + to dB + clamp + monthly median composite

**Filters:**

* instrumentMode == "IW"
* polarization contains "VV" and "VH"
* resolution_meters == 10 (or just accept GRD and resample)
* orbit pass choose one: "ASCENDING" or "DESCENDING" (recommended)
* optionally filter `transmitterReceiverPolarisation`

**Transform:**

* Convert linear backscatter to dB:

  * `10 * log10(x)`
* Clamp to e.g. [-25, 0] then normalize to [0,1]:

  * `norm = (db - (-25)) / (0 - (-25))`

**Monthly composite:**

* median

---

## E3) VIIRS: monthly avg_rad + clip/log + normalize

**Collection:**

* `NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG`
* band `avg_rad`

**Transform:**

* Optional: `log1p(avg_rad)` (helps dynamic range)
* Normalize using AOI-level robust stats:

  * For MVP: clamp to [p1, p99] across time (compute once per AOI)
  * Then scale to [0,1]

Since EE export is per month, you can:

* precompute global clamp thresholds from a multi-year collection reduced over AOI
* store them in Python
* apply per month

---

## E4) CHIRPS: monthly precipitation + anomaly per tile

**Collection:**

* daily `UCSB-CHG/CHIRPS/DAILY`, band `precipitation`

**Monthly precipitation:**

* sum across days in month → `P_t` (mm)

**Anomaly:**
Per tile and month-of-year:

* compute μ_m, σ_m over the full time window for that tile for that calendar month

Practical MVP approach:

* compute μ_m, σ_m at **AOI level** (not per tile) first (faster, still useful)
* later upgrade to per-tile baselines if needed

So:

* For each calendar month m (1..12):

  * collect all months in training window with month==m
  * compute AOI mean and std of precipitation
* anomaly = (P_t - μ_m) / (σ_m + eps)

This is a good compromise for VFM.

---

## E5) ERA5 monthly temperature anomaly (optional)

Same as CHIRPS:

* monthly mean temp
* AOI μ_m, σ_m by calendar month
* anomaly

---

# F) Build the per-month “state image” (the exported tensor)

For each month:

1. Compute:

* `S2_month`: 4–5 bands + `s2_valid_mask`
* `S1_month`: 2 bands
* `VIIRS_month`: 1 band

2. Reproject/resample to common scale (10m)
3. Concatenate into a single multi-band EE Image with a stable band order.

**Band order contract (example C=8):**

1. s2_b2
2. s2_b3
3. s2_b4
4. s2_b8
5. s1_vv
6. s1_vh
7. viirs
8. s2_valid_mask

---

# G) Export strategy (Python, scalable)

## Recommended: export to **Google Cloud Storage** (GCS)

Why:

* parallel exports
* bigger scale than Drive
* easier ingestion by ML pipeline

### Export granularity

Two options:

#### Option 1 (best VFM for multi-agent training): **per tile, per month GeoTIFF**

* Pros: simplest, modular
* Cons: many files

#### Option 2 (more ML-friendly): **per tile, multi-band multi-month TFRecord**

* Pros: fewer files, direct training
* Cons: more engineering

For MVP, do **Option 1**, plus a manifest.

### File naming convention

`gs://BUCKET/siad/{aoi_id}/{tile_id}/{YYYY-MM}.tif`

And actions/metadata manifest:
`gs://BUCKET/siad/{aoi_id}/manifest.jsonl`

Each manifest row:

* tile_id
* month
* gcs_uri
* rain_anom
* temp_anom (optional)
* s2_valid_frac
* quality flags

---

# H) Export recipe: per tile per month

For each tile polygon and month:

1. `state_img = build_state_image(aoi, month_start, month_end)`
2. `state_tile = state_img.clip(tile_geom)`
3. Export GeoTIFF with:

* scale: 10
* region: tile_geom
* maxPixels: large enough
* fileFormat: 'GeoTIFF'
* formatOptions: cloudOptimized True (optional)

Compute tile scalar metadata:

* `s2_valid_frac`: reduceRegion mean of s2_valid_mask
* `rain_anom`: compute using AOI monthly baseline method
* `temp_anom`: optional

Write a manifest entry in Python as exports are scheduled.

---

# I) Concrete EE pseudocode snippets (Python style)

## I1) Month boundaries

```python
import datetime as dt

def month_range(start: dt.date, end: dt.date):
    cur = dt.date(start.year, start.month, 1)
    while cur < end:
        nxt = dt.date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)
        yield cur, nxt
        cur = nxt
```

## I2) Sentinel-2 cloud masking (join)

Pseudocode:

* build join
* map to add cloud prob band and mask

Key join fields:

* `system:index`

## I3) Sentinel-1 filter

Pseudocode:

* filter by date
* filterBounds
* filter instrumentMode
* filter orbit pass
* select VV,VH
* map linear->dB->clamp->norm
* median

## I4) VIIRS monthly

Pseudocode:

* filter by date
* select avg_rad
* map clamp/log/normalize
* median (or first; it’s already monthly)

## I5) Stack bands

`state = s2_comp.addBands(s1_comp).addBands(viirs_comp).addBands(s2_valid_mask_comp)`

---

# J) Known gotchas and how to handle them

### J1) S2 valid coverage

Some months will have low clear pixels.

* Store `s2_valid_frac` and use it later as gating.
* Keep S1 always.

### J2) S1 incidence angle + terrain

If AOI is mountainous:

* add `angle` band
* or include DEM gating
  For MVP: pick flatter AOI.

### J3) VIIRS blooming / gas flares

* robust clip using percentiles
* optionally exclude known gas flare regions if they dominate

### J4) Export limits

Earth Engine export tasks have quotas and concurrency limits.

* Implement a task scheduler:

  * queue tasks
  * poll status
  * maintain backoff and retry only on transient failures
* Partition AOI if needed.

---

# K) What your multi-agent system should build (modules)

## Module 1: `aoi_tiles.py`

* input: AOI geojson, tile_size_m, stride_m
* output: list of {tile_id, ee.Geometry}

## Module 2: `collections.py`

* functions:

  * `get_s2_month(aoi, start, end, cloud_thresh)`
  * `get_s1_month(aoi, start, end, orbit_pass)`
  * `get_viirs_month(aoi, start, end)`
  * `get_chirps_month(aoi, start, end)`
  * `get_era5_month(aoi, start, end)` (optional)

## Module 3: `composite.py`

* `build_state_image(aoi, start, end, normalization_params) -> ee.Image`
* plus `compute_quality_metrics(tile_geom, state_img) -> dict`

## Module 4: `actions.py`

* compute AOI-level monthly climatology μ_m, σ_m
* compute anomalies for month

## Module 5: `exporter.py`

* schedule exports
* track tasks
* write manifest.jsonl