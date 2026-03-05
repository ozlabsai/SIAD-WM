# SIAD Earth Engine Export Guide

This guide explains how to export large-scale satellite imagery datasets from Google Earth Engine for training the SIAD world model.

## Overview

The SIAD export system uses Google Earth Engine to collect multi-modal satellite data:
- **Sentinel-1**: SAR imagery (all-weather, day/night)
- **Sentinel-2**: Optical imagery (10m resolution)
- **VIIRS**: Nighttime lights (human activity proxy)
- **CHIRPS**: Precipitation data (environmental context)

## Available Export Configurations

We have three pre-configured export scales:

### 1. Test Export (~10k samples)
**Config**: `configs/test-export.yaml`
- **Area**: San Francisco Bay Area (36km × 36km)
- **Tiles**: 196 (14×14 grid)
- **Time range**: 2021-01 to 2024-12 (48 months)
- **Total samples**: 9,408 tile-months
- **Storage**: ~38 GB
- **Export time**: ~2-4 hours
- **Use for**: Testing pipeline, debugging, quick experiments

### 2. Large Export (~40k samples) ⭐ RECOMMENDED
**Config**: `configs/large-export-10k.yaml`
- **Area**: Extended Bay Area (72km × 72km)
- **Tiles**: 784 (28×28 grid)
- **Time range**: 2021-01 to 2024-12 (48 months)
- **Total samples**: 37,632 tile-months
- **Storage**: ~150 GB
- **Export time**: ~8-12 hours
- **Use for**: Serious model training, good geographic diversity

### 3. Massive Export (~558k samples)
**Config**: `configs/large-export-100k.yaml`
- **Area**: Northern California (220km × 220km)
- **Tiles**: 7,744 (88×88 grid)
- **Time range**: 2019-01 to 2024-12 (72 months)
- **Total samples**: 557,568 tile-months
- **Storage**: ~2 TB
- **Export time**: Several days
- **Use for**: Production-scale world model, maximum diversity

## Prerequisites

### 1. Google Cloud Platform Setup

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project siad-earth-engine

# Create GCS bucket (if not exists)
gcloud storage buckets create gs://siad-exports --location=us-central1
```

### 2. Earth Engine Authentication

```bash
# Install Earth Engine
uv add earthengine-api

# Authenticate (opens browser)
uv run earthengine authenticate

# Initialize with project
uv run python -c "import ee; ee.Initialize(project='siad-earth-engine')"
```

### 3. Verify Setup

```bash
# Dry run to validate configuration
cd /path/to/SIAD
uv run siad export --config configs/test-export.yaml --dry-run
```

## Running an Export

### Option 1: Test Export (Recommended First)

```bash
# Navigate to SIAD root
cd /Users/guynachshon/Documents/ozlabs/labs/SIAD

# Run test export
uv run siad export --config configs/test-export.yaml

# Monitor tasks at: https://code.earthengine.google.com/tasks
```

### Option 2: Large Export (10k-40k samples)

```bash
uv run siad export --config configs/large-export-10k.yaml
```

### Option 3: Massive Export (100k+ samples)

⚠️ **WARNING**: This will submit thousands of Earth Engine tasks and require ~2TB storage.

```bash
# Only run this after successful test and large exports
uv run siad export --config configs/large-export-100k.yaml
```

## Monitoring Export Progress

### Check Earth Engine Tasks
Visit: https://code.earthengine.google.com/tasks

You'll see:
- Task status (READY, RUNNING, COMPLETED, FAILED)
- Progress bars
- Error messages if any

### Check GCS Storage

```bash
# List exported tiles
gcloud storage ls gs://siad-exports/siad/large-export-10k/

# Check storage usage
gcloud storage du gs://siad-exports --summarize
```

### View Manifest

Each export creates a `manifest.jsonl` file with metadata:

```bash
# Download manifest
gcloud storage cp gs://siad-exports/siad/large-export-10k/manifest.jsonl .

# View first few entries
head -n 5 manifest.jsonl
```

## What Gets Exported

For each tile and each month, the system exports:

1. **GeoTIFF file**: Multi-band raster with:
   - Sentinel-2 bands: B2, B3, B4, B8 (blue, green, red, NIR)
   - Sentinel-1 bands: VV, VH (SAR backscatter)
   - VIIRS band: avg_rad (nighttime lights)
   - Valid pixel mask (cloud/data quality)

2. **Manifest entry**: JSON with:
   - tile_id, month, gcs_uri
   - rain_anom (precipitation anomaly)
   - s2_valid_frac (% cloud-free pixels)
   - quality_flags

## Troubleshooting

### Error: "Earth Engine quota exceeded"

Earth Engine has export limits:
- **Free tier**: 3,000 tasks/day
- **Paid tier**: Contact Google for higher limits

**Solution**: Run exports in batches, monitor queue, retry failed tasks.

### Error: "GCS permission denied"

```bash
# Verify bucket access
gcloud storage buckets describe gs://siad-exports

# Grant Earth Engine service account access
# Get service account email from https://console.cloud.google.com/iam-admin/serviceaccounts
gsutil iam ch serviceAccount:YOUR_EE_ACCOUNT@gmail.com:roles/storage.admin gs://siad-exports
```

### Export tasks stuck in READY

This usually means:
1. Too many concurrent tasks (EE throttling)
2. Account quota reached
3. GCS bucket permissions issue

**Solution**: Wait, check quotas, verify permissions.

## Next Steps After Export

### 1. Verify Data Integrity

```bash
# Run validation script
cd /Users/guynachshon/Documents/ozlabs/labs/SIAD
uv run python scripts/validate_export.py --manifest gs://siad-exports/siad/large-export-10k/manifest.jsonl
```

### 2. Download Data (Optional)

For local training:

```bash
# Download all tiles to local disk
gcloud storage rsync -r gs://siad-exports/siad/large-export-10k/ ./data/exports/large-10k/
```

### 3. Start Training

```bash
# Train world model on exported data
uv run siad train --config configs/train_a100.yaml --data-path gs://siad-exports/siad/large-export-10k/
```

## Cost Estimates

### Earth Engine
- Free tier: 3,000 exports/day
- Typical cost: $0.02-$0.05 per export task
- **10k export**: ~$15-$40
- **100k export**: ~$115-$280

### Google Cloud Storage
- Storage: $0.020/GB/month
- **10k export**: ~$3/month (150 GB)
- **100k export**: ~$40/month (2 TB)

### Total Budget
- **Test + Large (10k) export**: ~$20-$50 one-time + $3/month storage
- **Massive (100k) export**: ~$150-$350 one-time + $40/month storage

## Tips for Success

1. **Start small**: Always run test-export first to validate the pipeline
2. **Monitor closely**: Watch Earth Engine tasks for failures
3. **Batch processing**: For 100k+ exports, consider regional batches
4. **Storage planning**: Ensure GCS bucket has sufficient quota
5. **Retry logic**: The system auto-retries transient failures
6. **Incremental exports**: You can export additional months/tiles later

## Summary

```bash
# Quick start (recommended path):

# 1. Test export (2-4 hours, ~10k samples)
uv run siad export --config configs/test-export.yaml

# 2. Large export (8-12 hours, ~40k samples)
uv run siad export --config configs/large-export-10k.yaml

# 3. Train model
uv run siad train --config configs/train_a100.yaml
```

For questions or issues, check:
- Earth Engine tasks: https://code.earthengine.google.com/tasks
- SIAD documentation: `COLLECTION-RECIPE.md`
- Export orchestrator code: `src/siad/data/export_orchestrator.py`
