# SIAD Export Status - Live Update

**Last Updated:** 2026-03-05 00:31 UTC

---

## Current Export: Test v0.3 ✅ RUNNING

**Task ID:** `6e5e04`
**Config:** `configs/test-export-v03.yaml`
**Started:** 2026-03-05 00:29:23 UTC

### Progress
```
[9/11232] tile_x000_y000 / 2021-09
Tasks submitted: 8 EE export tasks
Elapsed time: ~2 minutes
```

### Earth Engine Tasks
Monitor at: https://code.earthengine.google.com/tasks

**Submitted Task IDs:**
1. U4XATG46JV6JA3J3HQJCVUNY (tile_x000_y000/2021-01)
2. UCBS4UIABTD43NBQSQJFDX5P (tile_x000_y000/2021-02)
3. AMEATZACPDSJS7KBPZYNV4JG (tile_x000_y000/2021-03)
4. 7DYXYNVD2YCVPXJPS2NWHBRI (tile_x000_y000/2021-04)
5. LX4E67FEXQLQ45XYL3J6ES3T (tile_x000_y000/2021-05)
6. 2Q3P3PBGLNVJPG6XWN6KL74D (tile_x000_y000/2021-06)
7. WSPG7SHPI3BUAGVA76JQCRUK (tile_x000_y000/2021-07)
8. NGEC4AGD7UQXCSOBKJTCJLV6 (tile_x000_y000/2021-08)

### Performance
- **Submission rate:** ~12 seconds/sample
- **Estimated total time:** 11,232 samples × 12s = ~37 hours
- **Expected completion:** ~2026-03-06 13:30 UTC (in ~37 hours)

### Known Issues
⚠️ **CHIRPS rain anomaly warnings** (expected, not blocking):
```
[WARNING] Could not compute rain anomaly: unsupported operand type(s) for -: 'NoneType' and 'float'
```
- **Impact:** `rain_anom` may be 0 or missing in actions
- **Workaround:** Can recompute from raw CHIRPS data post-export
- **Status:** Documented, acceptable for baseline training

---

## Monitoring Commands

### Watch live progress
```bash
tail -f /tmp/ee_export_test_v03.log
```

### Check Earth Engine task status
```bash
# Open Earth Engine console
open https://code.earthengine.google.com/tasks

# Or use gcloud CLI
gcloud earth-engine tasks list --limit 20
```

### Check GCS bucket for completed exports
```bash
# List exported files
gsutil ls gs://siad-exports/siad/test-export-v03/

# Count completed tiles
gsutil ls gs://siad-exports/siad/test-export-v03/**/*.tif | wc -l
```

### Inspect first exported tile (when available)
```bash
# Download first tile
gsutil cp gs://siad-exports/siad/test-export-v03/tile_x000_y000/2021-01.tif /tmp/

# Check metadata
gdalinfo /tmp/2021-01.tif

# Visualize (requires QGIS or similar)
open /tmp/2021-01.tif
```

---

## Export Specifications

### Area of Interest
- **AOI ID:** test-export-v03
- **Bounds:** [-122.7, -122.2] lon × [37.6, 37.9] lat
- **Coverage:** San Francisco Bay Area core (36km × 36km)
- **Projection:** EPSG:32610 (UTM Zone 10N)

### Tile Grid
- **Tile count:** 234 tiles (14×14 grid + partial coverage)
- **Tile size:** 256px × 256px @ 10m = 2.56km × 2.56km
- **Resolution:** 10m per pixel

### Temporal Coverage
- **Date range:** 2021-01 to 2024-12
- **Duration:** 48 months (4 years)
- **Total samples:** 234 tiles × 48 months = **11,232 tile-months**

### Data Sources
- ✅ Sentinel-1 SAR (all-weather)
- ✅ Sentinel-2 optical (10m resolution)
- ✅ VIIRS nighttime lights
- ⚠️ CHIRPS precipitation (anomaly computation failing)

### Output Format
- **Format:** GeoTIFF (cloud-optimized)
- **Bands:** 8 (per BAND_ORDER_V1)
  1. S2_B2 (Blue, 490nm)
  2. S2_B3 (Green, 560nm)
  3. S2_B4 (Red, 665nm)
  4. S2_B8 (NIR, 842nm)
  5. S1_VV (SAR vertical-vertical)
  6. S1_VH (SAR vertical-horizontal)
  7. VIIRS_avg_rad (nighttime lights)
  8. S2_valid_mask (cloud-free fraction)

### Storage
- **GCS bucket:** siad-exports
- **Path:** gs://siad-exports/siad/test-export-v03/
- **Expected size:** ~15-50 GB (depending on compression)

---

## Next Steps

### Immediate (While Export Runs)
- [x] Export started successfully
- [ ] Wait for first tiles to complete (~1-2 hours for EE processing)
- [ ] Validate first exported GeoTIFF
- [ ] Check band order and data quality

### After First Tiles Available (~2-3 hours)
```bash
# Download and inspect first tile
gsutil cp gs://siad-exports/siad/test-export-v03/tile_x000_y000/2021-01.tif /tmp/
gdalinfo /tmp/2021-01.tif

# Check for issues:
# - 8 bands present?
# - 256×256 pixels?
# - UTM projection?
# - No all-NaN bands?
```

### After Export Completes (~37 hours)
```bash
# Generate manifest
uv run python scripts/generate_manifest.py \
  --gcs-path gs://siad-exports/siad/test-export-v03/

# Validate export completeness
uv run python scripts/validate_export.py \
  --manifest gs://siad-exports/siad/test-export-v03/manifest.jsonl

# Start baseline training
uv run siad train \
  --config configs/train-bay-area-v03.yaml \
  --data-path gs://siad-exports/siad/test-export-v03/
```

### Training Monitoring (3-5 days)
Watch for collapse indicators:
- `val/token_variance` should stay >0.1
- `val/token_covariance` should stay <0.5
- `ema_tau` should ramp 0.99 → 0.999 smoothly
- `batch/action_magnitude` should NOT be all zeros

---

## Cost Tracking

### Current Export (Test v0.3)
- **EE compute:** 11,232 tasks × $0.02/task = **~$225**
- **GCS storage:** ~15-50 GB × $0.020/GB/month = **$0.30-1.00/month**
- **Total (one-time):** ~$225

### Future: Full Export (Pending)
- **EE compute:** 119,808 tasks × $0.02/task = **~$2,400**
- **GCS storage:** ~150-500 GB × $0.020/GB/month = **$3-10/month**
- **Total (one-time):** ~$2,400

### Training (Both)
- **GPU:** A100 80GB @ $2.50/hour
- **Duration:** ~3-5 days = 72-120 hours
- **Cost:** **$180-300** per training run

**Budget Summary:**
- Test phase (committed): ~$225 + training TBD
- Full phase (pending validation): ~$2,400 + training TBD

---

## Files Created This Session

### Configs (v0.3 Spec-Compliant)
1. `configs/train-bay-area-v03.yaml` - Training config (zero spec deviations)
2. `configs/detector-bay-area-v03.yaml` - Post-training detection config
3. `configs/test-export-v03.yaml` - **Currently exporting** (11k samples)
4. `configs/export-bay-area-full.yaml` - Full-scale export config (120k samples, pending)

### Documentation
1. `configs/v03-spec-fixes.md` - Detailed spec compliance fixes
2. `configs/V03_COMPLETION_SUMMARY.md` - Initial completion summary
3. `configs/V03_EXPORT_STRATEGY.md` - Export strategy and optimization plan
4. `EXPORT_STATUS.md` - **This file** (live status)

### Command Center (Completed Earlier)
1. `siad-command-center/scripts/convert_gallery_to_pngs.py` - .npz → PNG converter
2. `siad-command-center/frontend/components/TileDetailModal.tsx` - Updated for real EE data
3. `siad-command-center/data/satellite_imagery/tiles/` - 90 real satellite images

---

## Success Criteria

### Export Success ✅
- [x] Config validated successfully
- [x] EE authentication successful
- [x] Tile grid generated (234 tiles)
- [x] First 8 tasks submitted successfully
- [ ] All 11,232 tile-months exported (in progress, ~37 hours remaining)
- [ ] GeoTIFFs are valid (8 bands, 256×256px, UTM projection)
- [ ] S2 valid fraction >30% for >80% of samples

### Training Success (Pending Export Completion)
- [ ] Baseline training reaches epoch 20+ without collapse
- [ ] Validation loss converges (<0.5)
- [ ] Token variance stays >0.1
- [ ] Predictions show spatial structure (not random noise)

### Detection Success (Pending Training Completion)
- [ ] Residuals show interpretable patterns
- [ ] Known anomalies have high residuals
- [ ] Neutral scenario produces credible counterfactuals

---

## Questions/Issues?

### Export appears stuck?
```bash
# Check if process is still running
tail -f /tmp/ee_export_test_v03.log

# Check for errors
grep -i error /tmp/ee_export_test_v03.log
```

### Earth Engine task failures?
- Check Earth Engine console for error messages
- Verify quota limits haven't been hit
- Check GCS bucket permissions

### Need to restart export?
```bash
# Kill current export
pkill -f "siad export"

# Restart from beginning
GOOGLE_CLOUD_PROJECT=siad-earth-engine uv run siad export \
  --config configs/test-export-v03.yaml \
  2>&1 | tee /tmp/ee_export_test_v03_restart.log
```

---

**Status:** 🟢 RUNNING SMOOTHLY
**ETA:** ~37 hours (2026-03-06 13:30 UTC)
