# Data Model: SIAD MVP - Infrastructure Acceleration Detection

**Feature**: 001-siad-mvp
**Date**: 2026-02-28
**Source**: Entities extracted from spec.md

## Entity Descriptions

### Area of Interest (AOI)

**Purpose**: Defines the geographic bounding box for analysis

**Fields**:
- `aoi_id`: Unique identifier (string, e.g., "port-expansion-2023")
- `bounds`: Geographic coordinates defining the bounding box
  - `min_lon`: Minimum longitude (decimal degrees)
  - `max_lon`: Maximum longitude (decimal degrees)
  - `min_lat`: Minimum latitude (decimal degrees)
  - `max_lat`: Maximum latitude (decimal degrees)
- `projection`: Target spatial reference system (string, default "EPSG:3857")
- `resolution_m`: Target resolution in meters (integer, default 10)
- `description`: Human-readable description (string, optional)

**Validation Rules**:
- `min_lon` < `max_lon` and `min_lat` < `max_lat`
- Bounding box area should approximate 50×50 km (2500 km² ± 20%) per spec assumption
- Projection must be valid EPSG code
- Resolution must be positive integer

**Relationships**:
- AOI contains multiple Tiles (spatial decomposition)
- AOI has multiple Timesteps (temporal coverage)

**State Transitions**: Immutable once defined (AOI does not change during analysis)

---

### Tile

**Purpose**: Atomic spatial unit for acceleration scoring (256×256 pixels at 10m resolution)

**Fields**:
- `tile_id`: Unique identifier combining AOI and spatial index (string, e.g., "port-expansion-2023_x012_y034")
- `aoi_id`: Foreign key to parent AOI (string)
- `grid_x`: Grid column index (integer, 0-based)
- `grid_y`: Grid row index (integer, 0-based)
- `bounds`: Tile-specific geographic bounds (derived from AOI + grid indices)
  - `min_lon`, `max_lon`, `min_lat`, `max_lat`: decimal degrees
- `pixel_size`: 256×256 (constant per spec FR-009)
- `resolution_m`: 10 meters (inherited from AOI)

**Validation Rules**:
- `grid_x` and `grid_y` must be non-negative integers
- Tile bounds must fall within parent AOI bounds
- Approximate tile size: 2.56 km × 2.56 km (256 pixels × 10m resolution)

**Relationships**:
- Tile belongs to one AOI
- Tile has multiple Observations (one per Timestep)
- Tile has one Acceleration Score per analysis run
- Tiles may cluster to form Hotspots

**State Transitions**: Immutable spatial grid (no state changes)

---

### Timestep

**Purpose**: Monthly temporal unit aligned to calendar month boundaries

**Fields**:
- `timestep_id`: Unique identifier (string, ISO 8601 month format "YYYY-MM")
- `year`: Calendar year (integer)
- `month`: Calendar month (integer, 1-12)
- `start_date`: First day of month (datetime)
- `end_date`: Last day of month (datetime)

**Validation Rules**:
- Month must be 1-12
- start_date and end_date must align with calendar month boundaries per spec FR-008
- Timestep sequence must be contiguous (no gaps) for valid analysis

**Relationships**:
- Timestep contains multiple Observations (one per Tile in AOI)
- Timestep has associated Actions (rainfall/temperature anomalies)
- Timesteps are ordered chronologically for rollout predictions

**State Transitions**: Immutable temporal index (no state changes)

---

### Observation

**Purpose**: Multi-modal satellite measurement for a specific Tile at a specific Timestep

**Fields**:
- `observation_id`: Unique identifier combining tile_id + timestep_id (string)
- `tile_id`: Foreign key to Tile (string)
- `timestep_id`: Foreign key to Timestep (string)
- `channels`: 8-channel tensor [C=8, H=256, W=256] containing:
  - `s2_blue`: Sentinel-2 Blue band (channel 0, float32, normalized 0-1)
  - `s2_green`: Sentinel-2 Green band (channel 1, float32, normalized 0-1)
  - `s2_red`: Sentinel-2 Red band (channel 2, float32, normalized 0-1)
  - `s2_nir`: Sentinel-2 NIR band (channel 3, float32, normalized 0-1)
  - `s1_vv`: Sentinel-1 VV polarization (channel 4, float32, dB scale)
  - `s1_vh`: Sentinel-1 VH polarization (channel 5, float32, dB scale)
  - `viirs_lights`: VIIRS nighttime lights (channel 6, float32, radiance units)
  - `s2_valid_fraction`: Valid pixel fraction mask (channel 7, float32, 0-1 indicating cloud-free coverage)
- `metadata`: Additional metadata (dict)
  - `source_images`: List of source Earth Engine image IDs used in median composite
  - `cloud_cover_pct`: Percentage of cloudy pixels in S2 composite (float, 0-100)

**Validation Rules**:
- All channel values must be finite (no NaN/Inf except where masked)
- `s2_valid_fraction` must be in [0, 1] range
- `cloud_cover_pct` should correlate inversely with `s2_valid_fraction`
- Channels 0-7 tensor shape must be exactly [8, 256, 256]

**Relationships**:
- Observation belongs to one Tile and one Timestep
- Observations are inputs to world model encoders (FR-011)
- Observations are compared against Rollout predictions for acceleration scoring

**State Transitions**: Immutable once preprocessed (no state changes)

---

### Action (Scenario Context)

**Purpose**: Rainfall and temperature anomaly scalars conditioning counterfactual rollouts

**Fields**:
- `action_id`: Unique identifier combining timestep_id + scenario_name (string)
- `timestep_id`: Foreign key to Timestep (string)
- `scenario_name`: Scenario identifier (string, e.g., "neutral", "observed", "extreme_rain")
- `rain_anom`: Rainfall anomaly (float, normalized z-score per spec FR-010)
- `temp_anom`: Temperature anomaly (float, normalized z-score per spec FR-006, optional)

**Validation Rules**:
- `rain_anom` and `temp_anom` should be z-scores (typically in range [-3, +3] for normal distributions)
- Neutral scenario must have `rain_anom = 0` and `temp_anom = 0` per spec FR-015
- Observed scenario must use actual CHIRPS/ERA5 data anomalies
- Extreme scenarios can define custom anomaly values (e.g., `rain_anom = +2.5` for heavy rainfall)

**Relationships**:
- Actions are associated with Timesteps
- Actions condition Rollout predictions (FR-012)
- Multiple Action scenarios exist per Timestep (neutral, observed, custom)

**State Transitions**: Immutable once computed (no state changes)

---

### Rollout

**Purpose**: Sequence of 6-month-ahead predicted observations conditioned on an Action scenario

**Fields**:
- `rollout_id`: Unique identifier combining tile_id + start_timestep_id + scenario_name (string)
- `tile_id`: Foreign key to Tile (string)
- `start_timestep_id`: Timestep at which rollout begins (string)
- `scenario_name`: Scenario identifier for conditioning Actions (string)
- `horizon`: Number of months predicted ahead (integer, constant 6 per spec FR-013)
- `predictions`: List of 6 predicted latent representations (or reconstructed observations)
  - Each element: latent vector z_hat (tensor, shape depends on encoder output dim)
  - Index k=0 corresponds to start_timestep + 1 month, k=5 to start_timestep + 6 months
- `divergences`: List of 6 divergence scores comparing predictions to actual observations
  - Each element: scalar divergence d(z_hat, z_tilde) per spec FR-015
  - Computed using cosine distance or MSE in latent space (research.md notes)

**Validation Rules**:
- `horizon` must equal 6 (per spec FR-013)
- `predictions` list length must equal `horizon`
- `divergences` list length must equal `horizon`
- All divergence scores must be non-negative

**Relationships**:
- Rollout belongs to one Tile and starts from one Timestep
- Rollout is conditioned on a sequence of Actions (one per predicted month)
- Rollouts are used to compute Acceleration Scores (FR-015)

**State Transitions**:
1. `predicted` → rollout computation complete
2. `divergence_computed` → divergences calculated against actual observations

---

### Hotspot

**Purpose**: Spatially coherent cluster of flagged tiles exceeding acceleration thresholds with persistence

**Fields**:
- `hotspot_id`: Unique identifier (string, e.g., "hotspot_001")
- `tile_ids`: List of Tile IDs forming the cluster (list of strings, minimum 3 per spec FR-018)
- `centroid`: Geographic center of cluster (lon, lat in decimal degrees)
- `first_detected_month`: Timestep when acceleration first exceeded threshold (string, ISO 8601 month)
- `persistence_months`: Number of consecutive months exceeding threshold (integer, minimum 2 per spec FR-017)
- `confidence_tier`: Modality attribution label (enum: "Structural", "Activity", "Environmental" per spec FR-020)
- `max_acceleration_score`: Peak acceleration score across all tiles in cluster (float)
- `thumbnails`: Before/after imagery paths (dict)
  - `s1_before`: Path to SAR thumbnail at first_detected_month - 6
  - `s1_after`: Path to SAR thumbnail at first_detected_month + persistence_months
  - `s2_before`, `s2_after`, `viirs_before`, `viirs_after`: Similar paths for optical and lights

**Validation Rules**:
- `tile_ids` must contain at least 3 tiles (spec FR-018)
- `persistence_months` must be at least 2 (spec FR-017)
- `confidence_tier` must be one of {"Structural", "Activity", "Environmental"}
- All tiles in `tile_ids` must be spatially connected (8-connectivity or rook's case)

**Relationships**:
- Hotspot aggregates multiple Tiles
- Hotspot is derived from Acceleration Scores across Tiles
- Hotspot has associated Modality Attribution decomposition

**State Transitions**:
1. `candidate` → flagged but not yet meeting persistence threshold
2. `confirmed` → meets persistence and spatial clustering criteria
3. `attributed` → modality attribution (SAR/optical/lights) computed

---

### Acceleration Score

**Purpose**: Tile-specific metric quantifying persistent divergence from neutral counterfactual baseline

**Fields**:
- `score_id`: Unique identifier combining tile_id + analysis_run_id (string)
- `tile_id`: Foreign key to Tile (string)
- `analysis_run_id`: Identifier for this analysis run (string, timestamp-based)
- `score_value`: Acceleration score (float, computed per spec FR-015 formula)
  - EMA(average divergence over 6-month horizon) + lambda * slope(last 3 months)
- `percentile_rank`: Tile's score percentile within its own historical distribution (float, 0-100 per spec FR-016)
- `threshold_exceeded`: Boolean flag indicating score > 99th percentile (boolean)
- `neutral_rollout_id`: Foreign key to Rollout used for neutral baseline (string)
- `observed_rollout_id`: Foreign key to Rollout using observed weather (string, for validation)

**Validation Rules**:
- `score_value` must be non-negative (divergence-based)
- `percentile_rank` must be in [0, 100] range
- `threshold_exceeded` must be True if `percentile_rank > 99` per spec FR-016
- `neutral_rollout_id` must reference a rollout with scenario_name = "neutral"

**Relationships**:
- Acceleration Score belongs to one Tile
- Acceleration Score is computed from Rollouts (neutral vs. observed)
- Multiple Acceleration Scores with `threshold_exceeded = True` and spatial proximity form Hotspots

**State Transitions**:
1. `computed` → score_value and percentile_rank calculated
2. `flagged` → threshold_exceeded = True (percentile > 99)
3. `persistent` → flagged for ≥2 consecutive months (feeds into Hotspot formation)

---

### Modality Attribution

**Purpose**: Decomposition of acceleration score into SAR/optical/lights contributions for hotspot classification

**Fields**:
- `attribution_id`: Unique identifier combining hotspot_id (string)
- `hotspot_id`: Foreign key to Hotspot (string)
- `sar_contribution`: Acceleration score recomputed using SAR-only channels (float, 0-1 normalized)
- `optical_contribution`: Acceleration score recomputed using optical-only channels (float, 0-1 normalized)
- `lights_contribution`: Acceleration score recomputed using lights-only channel (float, 0-1 normalized)
- `dominant_modality`: Primary contributor (enum: "SAR", "Optical", "Lights")
- `classification_logic`: Decision rule applied (string, e.g., "SAR + Lights → Structural")
- `confidence_tier`: Final label (enum: "Structural", "Activity", "Environmental" per spec FR-020)

**Validation Rules**:
- Sum of normalized contributions should approximate 1.0 (within numerical precision)
- Classification logic must follow spec FR-020 rules:
  - Structural: SAR dominant + lights present
  - Activity: Lights dominant + SAR weak
  - Environmental: Optical dominant + SAR/lights weak
- `confidence_tier` must be one of {"Structural", "Activity", "Environmental"}

**Relationships**:
- Modality Attribution belongs to one Hotspot
- Attribution is computed by re-running acceleration scoring with masked encoder inputs (spec FR-019)

**State Transitions**:
1. `sar_scored` → SAR-only acceleration computed
2. `optical_scored` → Optical-only acceleration computed
3. `lights_scored` → Lights-only acceleration computed
4. `classified` → confidence_tier assigned based on dominant modality

---

## Entity Relationship Diagram (Text-Based)

```
AOI (1) ----< Tile (N)
Tile (1) ----< Observation (N) >---- (N) Timestep
Timestep (1) ----< Action (N) [multiple scenarios]
Tile (1) ----< Rollout (N) [per scenario]
Rollout (*) ---- Action (*) [6-month sequence]
Tile (1) ---- (1) Acceleration Score
Acceleration Score (N) >---- (1) Hotspot [clustering]
Hotspot (1) ---- (1) Modality Attribution
```

## Storage Implementation Notes

Per research.md decisions:

- **AOI, Tile, Timestep metadata**: JSON config files in `configs/` directory
- **Observations**: HDF5 datasets with shape [N_tiles, N_timesteps, C=8, H=256, W=256], memory-mapped for efficient loading
- **Actions**: CSV or JSON per scenario (timestep_id, rain_anom, temp_anom columns)
- **Rollouts**: HDF5 datasets with shape [N_tiles, N_scenarios, horizon=6, latent_dim], or separate files per scenario
- **Acceleration Scores**: CSV with columns [tile_id, score_value, percentile_rank, threshold_exceeded, neutral_rollout_id]
- **Hotspots**: JSON array with hotspot objects containing tile_ids, confidence_tier, thumbnails paths
- **Modality Attribution**: JSON nested within Hotspot objects or separate CSV

All file formats adhere to constitution Principle V (deterministic I/O for auditability).
