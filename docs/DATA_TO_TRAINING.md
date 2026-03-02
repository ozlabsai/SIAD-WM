# From Data Export to Training

Complete workflow for going from Earth Engine exports to training on A100.

## Current Status: Export Running (75% Complete)

Your Earth Engine export is creating:
- **20 tiles** × **36 months** = **720 tile-months**
- **690 Earth Engine tasks** submitted
- **Progress**: 521 completed, 169 remaining

**Estimated completion**: 1-2 hours

---

## Step 1: Monitor Export Progress

### Check Earth Engine Dashboard

Visit: https://code.earthengine.google.com/tasks

Look for:
- ✅ Green checkmarks = completed
- 🔄 Spinning = running
- ⏸️ Gray = queued

### Or Check Programmatically

```bash
GOOGLE_CLOUD_PROJECT=siad-earth-engine uv run python << 'PYEOF'
import ee
ee.Initialize()

tasks = ee.batch.Task.list()
active = [t for t in tasks if t.state in ['READY', 'RUNNING']]
completed = [t for t in tasks if t.state == 'COMPLETED']
failed = [t for t in tasks if t.state == 'FAILED']

print(f"\n✅ COMPLETED: {len(completed)}")
print(f"⏳ ACTIVE: {len(active)}")
print(f"❌ FAILED: {len(failed)}")

if len(active) == 0 and len(failed) == 0:
    print("\n✓ Export complete! Ready for Step 2.")
elif len(failed) > 0:
    print(f"\n⚠️  {len(failed)} tasks failed. Check Earth Engine console.")
else:
    print(f"\n⏳ Still processing... {len(active)} tasks remaining")
PYEOF
```

---

## Step 2: Download GeoTIFFs from GCS

Once export completes, download files to your A100 pod:

```bash
# On A100 pod
cd /workspace/SIAD-WM

# Create data directory
mkdir -p data/geotiffs

# Download from GCS bucket (adjust bucket name if different)
gsutil -m rsync -r gs://siad-exports/test-export data/geotiffs/

# Verify downloads
ls -lh data/geotiffs/*.tif | wc -l
# Should show ~690-700 files (some months may be skipped due to missing data)
```

**File format:** `tile_x000_y001_2023-05.tif`
- Each file is a 256×256px GeoTIFF with 8 bands
- Bands: [B2, B3, B4, B8, VV, VH, lights, valid_mask]

---

## Step 3: Create Manifest

The manifest.jsonl file tells the trainer which files to load:

```bash
# On A100 pod
uv run python scripts/create_manifest.py \
    --data-dir data/geotiffs \
    --output data/manifest.jsonl \
    --min-months 12
```

This creates `data/manifest.jsonl` with entries like:

```json
{
  "tile_id": "tile_x000_y000",
  "months": ["2021-01", "2021-02", ..., "2023-12"],
  "observations": ["data/geotiffs/tile_x000_y000_2021-01.tif", ...],
  "actions": [[0.0, 0.0], [0.0, 0.0], ...]
}
```

**What you'll see:**
```
====================================================================
Manifest created: data/manifest.jsonl
============================================================
✓ Valid tiles: 20
  Total tile-months: 690

📋 Sample entry:
  Tile: tile_x000_y000
  Months: 35 (2021-01 to 2023-12)
  First observation: data/geotiffs/tile_x000_y000_2021-01.tif

============================================================
Ready to train!
  ./scripts/train_a100.sh data/manifest.jsonl
============================================================
```

---

## Step 4: Verify Data

Quick check that everything is valid:

```bash
uv run python scripts/check_training_data.py --manifest data/manifest.jsonl
```

You should see:
```
✓ Manifest found: data/manifest.jsonl
✓ Parsed 20 samples from manifest

📋 Sample structure:
  tile_id: tile_x000_y000
  months: 35 months
  observations: 35 files
  actions: 35 action vectors

📁 Checking first GeoTIFF:
  Path: data/geotiffs/tile_x000_y000_2021-01.tif
  ✓ File exists
  Size: 1.2 MB
  Bands: 8
  Shape: 256 × 256
  ✓ Valid GeoTIFF

============================================================
✓ Training data ready!
  Samples: 20
  Context needed: 1 month
  Rollout needed: 6 months
  Min length per sample: 7 months
============================================================
```

---

## Step 5: Setup Wandb (Optional but Recommended)

Enable training monitoring:

```bash
# One-time setup
wandb login
# Enter API key from https://wandb.ai/authorize
```

---

## Step 6: Start Training!

Everything is ready. Launch training:

```bash
./scripts/train_a100.sh data/manifest.jsonl
```

**What happens:**
1. ✓ Verifies GPU (A100 80GB)
2. ✓ Checks CUDA
3. ✓ Validates data
4. ✓ Loads dataset (20 tiles → 16 train, 4 val)
5. ✓ Creates WorldModel (54M params)
6. ✓ Starts training (50 epochs, batch_size=32)
7. ✓ Saves checkpoints every 5 epochs
8. ✓ Logs to wandb (real-time dashboard)

**Training output:**
```
============================================================
SIAD World Model Training
============================================================

GPU: NVIDIA A100-SXM4-80GB
VRAM: 79.2 GB

Loading dataset from: data/manifest.jsonl
Loaded 20 samples from data/manifest.jsonl
  Train samples: 16
  Val samples: 4

Creating model...
  Parameters: 54,123,456
  Size: 0.21 GB (fp32)

Initializing trainer...
  Wandb: run-abc123 (siad-world-model)

============================================================
Starting Training
============================================================

Epoch 1/50: 100%|████████| 1/1 [00:02<00:00, loss=0.6723]

Epoch 1/50:
  Train loss: 0.6723
  Val loss: 0.6145
  New best validation loss: 0.6145

Epoch 2/50: 100%|████████| 1/1 [00:02<00:00, loss=0.5892]
...
```

**View training dashboard:**
Wandb prints: `🚀 View run at https://wandb.ai/username/siad-world-model/runs/abc123`

---

## Expected Results

### Dataset Size
- **20 tiles** with **~35 months each** = **700 tile-months** total
- **Train set**: ~560 tile-months (80%)
- **Val set**: ~140 tile-months (20%)
- With context_length=1, rollout_horizon=6: Each sample uses 7 consecutive months

### Training Time
- **Batch size 32**: ~16 samples/batch (small dataset)
- **Epoch time**: ~10-30 seconds (depends on data loading)
- **Total time**: ~10-20 minutes for 50 epochs

### Checkpoints
Saved to `checkpoints/`:
- `checkpoint_epoch_5.pth`
- `checkpoint_epoch_10.pth`
- ...
- `checkpoint_best.pth` (lowest validation loss)
- `checkpoint_final.pth` (end of training)

### Wandb Metrics
- Loss curves (train vs val)
- Gradient norms
- Learning rate schedule
- GPU memory usage
- Training throughput

---

## Troubleshooting

### Export taking too long?

Earth Engine can be slow during peak hours. Check:
- https://status.earthengine.app/ (service status)
- Your export complexity (large areas take longer)
- Consider splitting into smaller regions

### Download failing?

```bash
# Install/update gsutil
pip install --upgrade gsutil

# Check bucket access
gsutil ls gs://siad-exports/test-export | head

# Resume partial download
gsutil -m rsync -r gs://siad-exports/test-export data/geotiffs/
```

### Not enough data?

If you only have ~10-15 tiles with 12+ months:
- Still valid for testing training pipeline
- For production, export larger AOI (more tiles)
- Or longer date range (more months)

### Training loss not decreasing?

With only 20 tiles, the model may overfit quickly:
- This is expected for a tiny dataset
- Use it to verify pipeline works end-to-end
- For real training, need hundreds/thousands of tiles

---

## Summary

**Current step:** Waiting for export to complete (75% done)

**Next steps:**
1. ⏳ Wait for export (1-2 hours)
2. 📥 Download GeoTIFFs from GCS
3. 📋 Create manifest.jsonl
4. ✅ Verify data
5. 🚀 Train!

**Total time from export complete to training:** ~10 minutes

Questions? Check:
- `docs/WANDB_MONITORING.md` - Training monitoring
- `QUICKSTART.md` - Training quick start
- `docs/A100_SETUP.md` - A100 optimization
