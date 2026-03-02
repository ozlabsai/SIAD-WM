# Quickstart Guide: SIAD MVP

**Feature**: 001-siad-mvp
**Date**: 2026-02-28
**Purpose**: Get started with SIAD infrastructure acceleration detection in 15 minutes

## Prerequisites

- Python 3.13+ installed
- UV package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Google Earth Engine account with project ID
- Cloud GPU access (single A100 or equivalent) for training
- Linux environment (tested on Ubuntu 22.04, should work on macOS with minor adjustments)

## Installation

```bash
# Clone repository
git clone https://github.com/your-org/SIAD.git
cd SIAD

# Create environment and install dependencies with UV
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Authenticate with Earth Engine
earthengine authenticate --project YOUR_EE_PROJECT_ID
```

## Quick Start: Run Full Pipeline on Example AOI

This example analyzes a 50×50 km region with 36 months of data to detect infrastructure acceleration.

### Step 1: Collect Satellite Data (10-30 minutes)

```bash
# Download satellite imagery for example port expansion region
siad-collect \
  --aoi configs/aoi_examples/quickstart-demo.json \
  --start 2021-01 \
  --end 2023-12 \
  --output data/raw/quickstart-demo \
  --ee-project YOUR_EE_PROJECT_ID \
  --verbose

# Expected output:
# ✓ Downloading Sentinel-1 SAR (36 months)...
# ✓ Downloading Sentinel-2 Optical (36 months)...
# ✓ Downloading VIIRS Nighttime Lights (36 months)...
# ✓ Downloading CHIRPS Rainfall (36 months)...
# ✓ Downloading ERA5 Temperature (36 months)...
# Success: 180 GeoTIFFs downloaded to data/raw/quickstart-demo/
```

**Outputs**: `data/raw/quickstart-demo/` contains:
- `s1_2021-01.tif` through `s1_2023-12.tif` (Sentinel-1 SAR)
- `s2_2021-01.tif` through `s2_2023-12.tif` (Sentinel-2 optical)
- `viirs_2021-01.tif` through `viirs_2023-12.tif` (nighttime lights)
- `chirps_2021-01.tif` through `chirps_2023-12.tif` (rainfall)
- `era5_2021-01.tif` through `era5_2023-12.tif` (temperature)
- `metadata.json` (download metadata)

### Step 2: Preprocess Data (5-10 minutes)

```bash
# Reproject, tile, and normalize data into model-ready tensors
siad-preprocess \
  --input data/raw/quickstart-demo \
  --aoi configs/aoi_examples/quickstart-demo.json \
  --output data/preprocessed/quickstart-demo \
  --verbose

# Expected output:
# ✓ Reprojecting to EPSG:3857 at 10m resolution...
# ✓ Tiling into 256×256 pixel tiles (approx. 400 tiles)...
# ✓ Computing monthly composites (median)...
# ✓ Normalizing rainfall/temperature to anomalies...
# Success: HDF5 dataset created at data/preprocessed/quickstart-demo/observations.h5
# Shape: [400 tiles, 36 timesteps, 8 channels, 256, 256]
```

**Outputs**: `data/preprocessed/quickstart-demo/` contains:
- `observations.h5` (14,400 tile-months in HDF5 format)
- `actions.csv` (rainfall/temperature anomalies per month)
- `tiles.json` (tile metadata: IDs, grid indices, bounds)
- `timesteps.json` (timestep metadata: IDs, dates)

### Step 3: Train World Model (2-4 hours on A100)

```bash
# Train world model with 6-month context and 6-month rollout
siad-train \
  --data data/preprocessed/quickstart-demo \
  --output data/models/quickstart-demo-v1 \
  --epochs 50 \
  --batch-size 16 \
  --verbose

# Expected output:
# Epoch 1/50: train_loss=0.245, val_loss=0.312
# Epoch 2/50: train_loss=0.198, val_loss=0.276
# ...
# Epoch 50/50: train_loss=0.042, val_loss=0.051
# ✓ Best model saved to data/models/quickstart-demo-v1/model_best.pth
# Success: Training complete (val_loss improved from 0.312 → 0.051)
```

**Outputs**: `data/models/quickstart-demo-v1/` contains:
- `model_best.pth` (PyTorch checkpoint with lowest validation loss)
- `model_latest.pth` (checkpoint from final epoch)
- `config.json` (training hyperparameters)
- `metrics.csv` (loss curves)

**Training Tips**:
- Monitor GPU memory with `nvidia-smi` (expect ~30GB for batch_size=16)
- Use `--checkpoint` flag to resume interrupted training
- Reduce `--batch-size` if you encounter OOM errors

### Step 4: Detect Infrastructure Acceleration (10-15 minutes)

```bash
# Run inference and compute acceleration scores
siad-detect \
  --model data/models/quickstart-demo-v1 \
  --data data/preprocessed/quickstart-demo \
  --output data/outputs/quickstart-demo-detection \
  --scenarios neutral,observed,extreme_rain \
  --verbose

# Expected output:
# ✓ Loading model from data/models/quickstart-demo-v1/model_best.pth...
# ✓ Running rollouts for 3 scenarios × 400 tiles...
# ✓ Computing acceleration scores (neutral baseline divergence)...
# ✓ Flagging tiles exceeding 99th percentile threshold...
# ✓ Clustering spatially connected tiles (min 3 tiles, 2-month persistence)...
# ✓ Computing modality attribution (SAR/optical/lights decomposition)...
# Success: Found 12 hotspots (7 Structural, 3 Activity, 2 Environmental)
```

**Outputs**: `data/outputs/quickstart-demo-detection/` contains:
- `acceleration_scores.csv` (scores for all 400 tiles)
- `hotspots.json` (12 detected hotspots with metadata)
- `rollouts/neutral.h5`, `rollouts/observed.h5`, `rollouts/extreme_rain.h5`

### Step 5: Validate Results (5 minutes)

```bash
# Run three-gate validation suite
siad-validate \
  --detection data/outputs/quickstart-demo-detection \
  --config configs/validation_regions/quickstart-demo.json \
  --verbose

# Expected output:
# ✓ Gate 1 (Self-Consistency): Neutral scenario divergence 42% lower than random actions
# ✓ Gate 2 (Backtesting): Hit rate 85% (17/20 known construction sites flagged)
# ✓ Gate 3 (False-Positives): FP rate 14% (3/21 agricultural tiles flagged)
# Success: All validation gates passed (SC-002: 85% > 80%, SC-003: 14% < 20%)
```

**Outputs**: `data/outputs/quickstart-demo-detection/validation/` contains:
- `summary.json` (aggregate metrics matching success criteria SC-002, SC-003, SC-004)
- `self_consistency_report.json`, `backtest_report.json`, `false_positive_report.json`

### Step 6: Generate Visualizations (2 minutes)

```bash
# Create heatmaps, timelines, and counterfactual comparisons
siad-visualize \
  --detection data/outputs/quickstart-demo-detection \
  --output data/outputs/quickstart-demo-viz \
  --formats png,geojson \
  --dpi 300 \
  --verbose

# Expected output:
# ✓ Generating spatial heatmap (400 tiles)...
# ✓ Generating hotspot ranking visualization (12 hotspots)...
# ✓ Generating timelines (12 hotspot clusters)...
# ✓ Generating counterfactual comparison grid (3 scenarios)...
# ✓ Exporting GeoJSON for web mapping...
# Success: 16 PNG files + 1 GeoJSON created in data/outputs/quickstart-demo-viz/
```

**Outputs**: `data/outputs/quickstart-demo-viz/` contains:
- `heatmap.png` (spatial acceleration heatmap)
- `hotspots_ranked.png` (ranked list with thumbnails)
- `timelines/hotspot_001.png` through `hotspot_012.png` (temporal evolution per hotspot)
- `counterfactual_comparison.png` (neutral vs observed vs extreme scenarios)
- `hotspots.geojson` (GeoJSON for Leaflet/Mapbox integration)

## Viewing Results

### Heatmap
Open `data/outputs/quickstart-demo-viz/heatmap.png` to see the spatial distribution of acceleration scores. Red tiles indicate high acceleration (>99th percentile), while blue tiles show baseline behavior.

### Hotspot Details
Open `data/outputs/quickstart-demo-detection/hotspots.json` to inspect detected hotspots:
```json
{
  "hotspot_id": "hotspot_001",
  "tile_ids": ["tile_x012_y034", "tile_x013_y034", "tile_x012_y035"],
  "confidence_tier": "Structural",
  "first_detected_month": "2022-08",
  "persistence_months": 14,
  "max_acceleration_score": 2.73,
  "centroid": {"lon": 12.345, "lat": 34.567}
}
```

### Timelines
Open `data/outputs/quickstart-demo-viz/timelines/hotspot_001.png` to see when acceleration began and how it evolved over time.

### Counterfactual Scenarios
Open `data/outputs/quickstart-demo-viz/counterfactual_comparison.png` to compare how the same region appears under neutral weather vs observed weather vs extreme rainfall scenarios.

## Next Steps

### Analyze Your Own AOI

1. Create an AOI config JSON in `configs/aoi_examples/your-region.json`:
   ```json
   {
     "aoi_id": "your-region",
     "bounds": {
       "min_lon": 12.0,
       "max_lon": 12.5,
       "min_lat": 34.0,
       "max_lat": 34.5
     },
     "projection": "EPSG:3857",
     "resolution_m": 10,
     "description": "Your 50×50 km region of interest"
   }
   ```

2. Replace `quickstart-demo` with `your-region` in all commands above

3. Adjust date range (`--start`, `--end`) to your analysis period (minimum 24 months, recommended 36)

### Customize Scenarios

Define custom counterfactual scenarios in `configs/scenarios/custom-drought.json`:
```json
{
  "scenario_name": "custom-drought",
  "description": "Prolonged drought conditions",
  "actions": [
    {"timestep_id": "2023-01", "rain_anom": -2.5, "temp_anom": 1.5},
    {"timestep_id": "2023-02", "rain_anom": -2.5, "temp_anom": 1.5},
    ...
  ]
}
```

Then run detection with `--scenarios neutral,observed,custom-drought`.

### Backtest on Known Regions

Add known construction sites to `configs/validation_regions/your-backtest.json`:
```json
{
  "backtest_regions": [
    {
      "name": "Port Expansion 2022",
      "bounds": {"min_lon": 12.1, "max_lon": 12.2, "min_lat": 34.1, "max_lat": 34.2},
      "construction_start": "2022-03",
      "expected_confidence_tier": "Structural"
    }
  ]
}
```

Then run `siad-validate --config configs/validation_regions/your-backtest.json`.

## Troubleshooting

### Earth Engine Authentication Fails
```bash
# Re-authenticate
earthengine authenticate --project YOUR_EE_PROJECT_ID --force

# Verify credentials
python -c "import ee; ee.Initialize(project='YOUR_EE_PROJECT_ID'); print('Success')"
```

### GPU Out of Memory During Training
```bash
# Reduce batch size
siad-train ... --batch-size 8  # Instead of 16

# Or train on CPU (slower)
siad-train ... --device cpu
```

### Preprocessing Fails on Reprojection
```bash
# Check GDAL installation
gdalinfo --version  # Should be 3.x

# Re-install rasterio with GDAL bindings
uv pip install --force-reinstall rasterio
```

### No Hotspots Detected
```bash
# Lower percentile threshold (default 99 is very strict)
siad-detect ... --percentile-threshold 95

# Reduce persistence requirement (default 2 months)
siad-detect ... --persistence-months 1

# Reduce cluster size (default 3 tiles)
siad-detect ... --min-cluster-size 2
```

## Performance Benchmarks

On a single A100 GPU with the quickstart demo AOI (400 tiles, 36 months):

| Step | Time | CPU/GPU | Notes |
|------|------|---------|-------|
| siad-collect | 15 min | CPU | Network-bound (Earth Engine download) |
| siad-preprocess | 8 min | CPU | I/O-bound (GeoTIFF reprojection) |
| siad-train (50 epochs) | 3 hours | GPU | Compute-bound (batch_size=16) |
| siad-detect | 12 min | GPU | Inference + postprocessing |
| siad-validate | 5 min | CPU | Statistical tests |
| siad-visualize | 2 min | CPU | Matplotlib rendering |
| **Total** | **~4 hours** | | End-to-end pipeline |

For larger AOIs (e.g., 100×100 km ≈ 1600 tiles), expect ~12 hours training and ~40 min inference.

## Support

- **Documentation**: See `specs/001-siad-mvp/` for full specification, data model, and contracts
- **Issue Tracker**: Report bugs at `https://github.com/your-org/SIAD/issues`
- **Constitution**: Review project principles at `.specify/memory/constitution.md`

---

**Success!** You've now run the full SIAD MVP pipeline. The system detected infrastructure acceleration by learning baseline dynamics from satellite imagery and flagging persistent deviations that are robust to weather-driven changes. Review the visualizations in `data/outputs/quickstart-demo-viz/` to see the results.
