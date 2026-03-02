# CLI Interface Contracts

**Feature**: 001-siad-mvp
**Date**: 2026-02-28
**Purpose**: Define public CLI commands per constitution Principle V (Reproducible Pipelines)

## Overview

SIAD MVP exposes 6 CLI commands corresponding to pipeline stages. All commands follow the pattern:

```
command [OPTIONS] [INPUTS] > stdout 2> stderr
EXIT_CODE: 0 (success) | 1-255 (failure)
```

Per constitution Principle V, all commands must:
- Accept inputs via `stdin`, `args`, or file paths
- Output primary results to `stdout` (or specified output file)
- Output errors/logs to `stderr`
- Return deterministic results for identical inputs
- Support `--help` flag for usage documentation
- Support `--dry-run` flag to validate inputs without execution

---

## Command 1: `siad-collect`

**Purpose**: Download satellite imagery from Earth Engine for specified AOI and time range

**Usage**:
```bash
siad-collect --aoi CONFIG_PATH --start YYYY-MM --end YYYY-MM --output OUTPUT_DIR [OPTIONS]
```

**Required Arguments**:
- `--aoi PATH`: Path to AOI config JSON (see data-model.md AOI entity)
- `--start YYYY-MM`: Start month (ISO 8601)
- `--end YYYY-MM`: End month (ISO 8601, inclusive)
- `--output DIR`: Output directory for downloaded GeoTIFFs

**Optional Arguments**:
- `--sources LIST`: Comma-separated list of data sources (default: "s1,s2,viirs,chirps,era5")
- `--ee-project ID`: Google Earth Engine project ID for authentication
- `--dry-run`: Validate inputs and print download plan without executing
- `--verbose`: Enable detailed logging to stderr

**Outputs (to OUTPUT_DIR)**:
- `{source}_{YYYY-MM}.tif`: GeoTIFF per source per month (e.g., `s1_2023-01.tif`)
- `metadata.json`: Download metadata (source image IDs, cloud cover stats, bounds)
- `download.log`: Execution log (also echoed to stderr if --verbose)

**Exit Codes**:
- 0: Success
- 1: Invalid AOI config or date range
- 2: Earth Engine authentication failure
- 3: Download failure (network error, quota exceeded)

**Example**:
```bash
siad-collect \
  --aoi configs/aoi_examples/port-expansion.json \
  --start 2021-01 \
  --end 2023-12 \
  --output data/raw/port-expansion \
  --ee-project my-ee-project
```

**Contract Tests**:
- Verify `--dry-run` prints expected file list without creating files
- Verify invalid date range (end < start) exits with code 1
- Verify missing --aoi exits with code 1 and prints usage to stderr
- Verify output directory structure matches spec

---

## Command 2: `siad-preprocess`

**Purpose**: Reproject, tile, normalize, and composite downloaded data into model-ready tensors

**Usage**:
```bash
siad-preprocess --input INPUT_DIR --aoi CONFIG_PATH --output OUTPUT_DIR [OPTIONS]
```

**Required Arguments**:
- `--input DIR`: Directory containing raw GeoTIFFs from `siad-collect`
- `--aoi PATH`: Path to AOI config JSON (defines projection, resolution, tiling)
- `--output DIR`: Output directory for preprocessed HDF5 datasets

**Optional Arguments**:
- `--tile-size INT`: Tile size in pixels (default: 256 per spec FR-009)
- `--resolution-m INT`: Target resolution in meters (default: 10)
- `--projection EPSG`: Target projection (default: "EPSG:3857")
- `--dry-run`: Validate inputs and print preprocessing plan
- `--verbose`: Enable detailed logging to stderr

**Outputs (to OUTPUT_DIR)**:
- `observations.h5`: HDF5 dataset [N_tiles, N_timesteps, C=8, H=256, W=256]
- `actions.csv`: CSV with columns [timestep_id, rain_anom, temp_anom]
- `tiles.json`: Tile metadata (tile_id, grid_x, grid_y, bounds)
- `timesteps.json`: Timestep metadata (timestep_id, year, month)
- `preprocessing.log`: Execution log

**Exit Codes**:
- 0: Success
- 1: Invalid input directory or missing source files
- 2: Reprojection/tiling failure
- 3: Normalization failure (insufficient baseline data)

**Example**:
```bash
siad-preprocess \
  --input data/raw/port-expansion \
  --aoi configs/aoi_examples/port-expansion.json \
  --output data/preprocessed/port-expansion
```

**Contract Tests**:
- Verify output HDF5 shape matches [N_tiles, N_timesteps, 8, 256, 256]
- Verify tiles.json count matches first dimension of HDF5
- Verify timesteps.json count matches second dimension of HDF5
- Verify actions.csv has rain_anom and temp_anom columns with z-score normalized values

---

## Command 3: `siad-train`

**Purpose**: Train world model on preprocessed data with multi-step rollout objective

**Usage**:
```bash
siad-train --data DATA_DIR --output MODEL_DIR [OPTIONS]
```

**Required Arguments**:
- `--data DIR`: Directory containing preprocessed HDF5 from `siad-preprocess`
- `--output DIR`: Output directory for model checkpoints and training logs

**Optional Arguments**:
- `--context-length INT`: Number of months for context window (default: 6 per spec FR-011)
- `--horizon INT`: Number of months for rollout prediction (default: 6 per spec FR-013)
- `--epochs INT`: Number of training epochs (default: 50)
- `--batch-size INT`: Batch size (default: 32)
- `--lr FLOAT`: Learning rate (default: 1e-4)
- `--checkpoint PATH`: Resume from checkpoint
- `--dry-run`: Validate data loading and print model architecture
- `--verbose`: Enable detailed logging to stderr

**Outputs (to OUTPUT_DIR)**:
- `model_latest.pth`: Latest model checkpoint (PyTorch state dict)
- `model_best.pth`: Best model by validation loss
- `config.json`: Training configuration (hyperparameters, data paths)
- `metrics.csv`: Training/validation loss per epoch
- `training.log`: Execution log

**Exit Codes**:
- 0: Success
- 1: Invalid data directory or corrupted HDF5
- 2: Training failure (NaN loss, GPU OOM)
- 3: Checkpoint save failure

**Example**:
```bash
siad-train \
  --data data/preprocessed/port-expansion \
  --output data/models/port-expansion-v1 \
  --epochs 50 \
  --batch-size 16
```

**Contract Tests**:
- Verify checkpoint files are created and loadable
- Verify metrics.csv has epoch, train_loss, val_loss columns
- Verify --dry-run prints model architecture without training
- Verify training stops gracefully on KeyboardInterrupt and saves checkpoint

---

## Command 4: `siad-detect`

**Purpose**: Run inference and acceleration detection on trained model

**Usage**:
```bash
siad-detect --model MODEL_DIR --data DATA_DIR --output OUTPUT_DIR [OPTIONS]
```

**Required Arguments**:
- `--model DIR`: Directory containing trained model from `siad-train`
- `--data DIR`: Directory containing preprocessed data from `siad-preprocess`
- `--output DIR`: Output directory for detection results

**Optional Arguments**:
- `--scenarios LIST`: Comma-separated scenario names (default: "neutral,observed")
- `--percentile-threshold FLOAT`: Threshold percentile for flagging (default: 99 per spec FR-016)
- `--persistence-months INT`: Minimum persistence for hotspots (default: 2 per spec FR-017)
- `--min-cluster-size INT`: Minimum tiles per hotspot (default: 3 per spec FR-018)
- `--dry-run`: Load model and print inference plan without execution
- `--verbose`: Enable detailed logging to stderr

**Outputs (to OUTPUT_DIR)**:
- `acceleration_scores.csv`: CSV with columns [tile_id, score_value, percentile_rank, threshold_exceeded]
- `hotspots.json`: JSON array of hotspot objects (see data-model.md Hotspot entity)
- `rollouts/`: Directory containing rollout predictions per scenario (HDF5 or NPZ)
- `detection.log`: Execution log

**Exit Codes**:
- 0: Success
- 1: Invalid model or data directory
- 2: Inference failure (GPU OOM, corrupted checkpoint)
- 3: Detection postprocessing failure (clustering, thresholding)

**Example**:
```bash
siad-detect \
  --model data/models/port-expansion-v1 \
  --data data/preprocessed/port-expansion \
  --output data/outputs/port-expansion-detection \
  --scenarios neutral,observed,extreme_rain
```

**Contract Tests**:
- Verify acceleration_scores.csv has correct schema
- Verify hotspots.json contains only clusters meeting persistence and size thresholds
- Verify rollouts/ directory contains files for each scenario
- Verify --dry-run loads model without running inference

---

## Command 5: `siad-validate`

**Purpose**: Run three-gate validation suite (self-consistency, backtesting, false-positives)

**Usage**:
```bash
siad-validate --detection DETECTION_DIR --config VALIDATION_CONFIG [OPTIONS]
```

**Required Arguments**:
- `--detection DIR`: Directory containing detection results from `siad-detect`
- `--config PATH`: Path to validation config JSON (defines backtest regions, FP test regions)

**Optional Arguments**:
- `--gates LIST`: Comma-separated gate names to run (default: "all" = self-consistency,backtest,false-positive)
- `--output DIR`: Output directory for validation reports (default: DETECTION_DIR/validation)
- `--dry-run`: Validate config and print test plan
- `--verbose`: Enable detailed logging to stderr

**Outputs (to OUTPUT_DIR)**:
- `self_consistency_report.json`: Neutral vs random scenario comparison
- `backtest_report.json`: Hit rate on known construction regions
- `false_positive_report.json`: FP rate on agriculture/monsoon regions
- `summary.json`: Aggregate validation metrics matching spec SC-002, SC-003, SC-004
- `validation.log`: Execution log

**Exit Codes**:
- 0: Success (all gates pass)
- 1: Invalid config or missing detection results
- 2: Validation gate failure (hit rate < 80%, FP rate > 20%)
- 3: Execution error (missing ground truth data)

**Example**:
```bash
siad-validate \
  --detection data/outputs/port-expansion-detection \
  --config configs/validation_regions/standard.json \
  --gates self-consistency,backtest
```

**Contract Tests**:
- Verify summary.json contains hit_rate, fp_rate, scenario_divergence_reduction fields
- Verify exit code 2 if hit_rate < 80% (per spec SC-002)
- Verify exit code 2 if fp_rate > 20% (per spec SC-003)
- Verify --dry-run prints test regions without executing validation

---

## Command 6: `siad-visualize`

**Purpose**: Generate heatmaps, timelines, and counterfactual comparison visualizations

**Usage**:
```bash
siad-visualize --detection DETECTION_DIR --output OUTPUT_DIR [OPTIONS]
```

**Required Arguments**:
- `--detection DIR`: Directory containing detection results from `siad-detect`
- `--output DIR`: Output directory for visualization files (PNG/PDF/GeoJSON)

**Optional Arguments**:
- `--formats LIST`: Comma-separated output formats (default: "png,geojson")
- `--dpi INT`: Image resolution for PNG (default: 300)
- `--tile-thumbnails BOOL`: Generate before/after thumbnails per hotspot (default: true)
- `--dry-run`: Validate inputs and print visualization plan
- `--verbose`: Enable detailed logging to stderr

**Outputs (to OUTPUT_DIR)**:
- `heatmap.png`: Spatial acceleration heatmap (spec FR-025)
- `hotspots_ranked.png`: Hotspot ranking visualization (spec FR-026)
- `timelines/`: Directory containing per-hotspot timeline PNGs (spec FR-027)
- `counterfactual_comparison.png`: Scenario comparison grid (spec FR-028)
- `hotspots.geojson`: GeoJSON export for web mapping (optional)
- `visualization.log`: Execution log

**Exit Codes**:
- 0: Success
- 1: Invalid detection directory or missing input files
- 2: Visualization rendering failure (matplotlib error)
- 3: File write failure (permissions, disk space)

**Example**:
```bash
siad-visualize \
  --detection data/outputs/port-expansion-detection \
  --output data/outputs/port-expansion-viz \
  --formats png,pdf,geojson \
  --dpi 300
```

**Contract Tests**:
- Verify heatmap.png exists and has correct dimensions
- Verify timelines/ contains one PNG per hotspot in hotspots.json
- Verify hotspots.geojson is valid GeoJSON FeatureCollection
- Verify --dry-run validates inputs without creating files

---

## Pipeline Composition Example

**Full end-to-end workflow**:
```bash
# 1. Collect data
siad-collect \
  --aoi configs/aoi_examples/port-expansion.json \
  --start 2021-01 --end 2023-12 \
  --output data/raw/port-expansion \
  --ee-project my-project

# 2. Preprocess
siad-preprocess \
  --input data/raw/port-expansion \
  --aoi configs/aoi_examples/port-expansion.json \
  --output data/preprocessed/port-expansion

# 3. Train model
siad-train \
  --data data/preprocessed/port-expansion \
  --output data/models/port-expansion-v1 \
  --epochs 50

# 4. Run detection
siad-detect \
  --model data/models/port-expansion-v1 \
  --data data/preprocessed/port-expansion \
  --output data/outputs/port-expansion-detection

# 5. Validate results
siad-validate \
  --detection data/outputs/port-expansion-detection \
  --config configs/validation_regions/standard.json

# 6. Generate visualizations
siad-visualize \
  --detection data/outputs/port-expansion-detection \
  --output data/outputs/port-expansion-viz
```

**Parallel composition** (data collection for multiple AOIs):
```bash
for aoi in port-expansion industrial-park border-region; do
  siad-collect --aoi configs/aoi_examples/${aoi}.json --start 2021-01 --end 2023-12 --output data/raw/${aoi} &
done
wait
```

---

## Contract Test Requirements

Per constitution Principle V and spec FR-024, all commands must have contract tests verifying:

1. **Help flag**: `--help` prints usage and exits with code 0
2. **Dry-run flag**: `--dry-run` validates inputs without side effects
3. **Error handling**: Invalid inputs exit with non-zero code and print error to stderr
4. **Determinism**: Identical inputs produce identical outputs (modulo non-deterministic GPU ops, which should be seeded)
5. **Schema compliance**: Output files match documented schemas (data-model.md entities)
6. **Exit codes**: Commands use documented exit codes (0=success, 1-3=specific failures)
7. **Logging**: `--verbose` flag controls stderr verbosity
8. **Interoperability**: Output of command N is valid input to command N+1

These contract tests live in `tests/contract/test_cli_*.py` and are executed via `pytest tests/contract/` before any release.
