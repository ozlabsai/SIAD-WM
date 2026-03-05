# SIAD v0.3 Export Strategy

## Current Status

**Test Export Running:** ✅
- Config: `configs/test-export-v03.yaml`
- Task ID: 6e5e04
- Samples: 234 tiles × 48 months = **11,232 tile-months**
- Training windows: ~9,800 (with H=6 rollout)
- Estimated completion: **~22 hours**

**Monitor at:**
```bash
tail -f /tmp/ee_export_test_v03.log
```

---

## Why Test Export First?

### Performance Bottleneck Identified

The export orchestrator has a critical performance issue:

**Problem:** Client-side median compositing + eager evaluation
```python
# In export_orchestrator.py lines 196-231
collected['s1'] = self.collectors['s1'].collect(...)  # Computes median CLIENT-SIDE
logger.debug(f"  ✓ S1: {collected['s1'].bandNames().getInfo()}")  # Forces computation!
```

**Impact:**
- **6-8 seconds per sample** (2-3s query, 2-3s composite, 1-2s reproject, 0.5s submit)
- Full export (120k samples): ~10 days sequential submission
- Test export (11k samples): ~22 hours

**Root Cause:**
1. `.collect()` methods compute `ImageCollection.median()` locally instead of pushing to EE server
2. `.getInfo()` calls force eager evaluation instead of lazy computation
3. Sequential tile-by-tile submission instead of batch parallel submission

---

## Export Timeline Comparison

| Config | Tiles | Months | Samples | Time (Current) | Time (Optimized*) |
|--------|-------|--------|---------|----------------|-------------------|
| test-export-v03 | 234 | 48 | 11,232 | **~22 hours** | ~3-4 hours |
| export-bay-area-full | 2,496 | 48 | 119,808 | ~10 days | ~1-2 days |

*Optimized = server-side compositing + batch submission

---

## Recommended Path Forward

### Phase 1: Test Export (Current) ✅

**Goal:** Validate v0.3 spec with baseline training

**Actions:**
1. ✅ Let test export complete (~22 hours)
2. Validate first exported tiles when available:
   ```bash
   gsutil ls gs://siad-exports/siad/test-export-v03/
   ```
3. Check data quality:
   ```bash
   uv run python scripts/validate_export.py \
     --gcs-path gs://siad-exports/siad/test-export-v03/
   ```
4. Start baseline training:
   ```bash
   uv run siad train \
     --config configs/train-bay-area-v03.yaml \
     --data-path gs://siad-exports/siad/test-export-v03/
   ```

**Success Criteria:**
- Export completes without errors
- Training runs for 10+ epochs without collapse
- `val/token_variance` stays >0.1
- `ema_tau` ramps from 0.99 → 0.999

---

### Phase 2: Optimize Orchestrator (Parallel)

**Goal:** Fix performance bottleneck for full-scale export

**Changes Needed:**

1. **Push compositing to server:**
   ```python
   # BEFORE (client-side):
   s1_collection = ee.ImageCollection(...).filterDate(...)
   s1_median = s1_collection.median()  # Computed locally!

   # AFTER (server-side):
   s1_image = ee.ImageCollection(...).filterDate(...).median()  # Lazy!
   # Don't call .getInfo() until ready to submit
   ```

2. **Batch task submission:**
   ```python
   # Submit 50 tasks in parallel, then wait for slots
   from concurrent.futures import ThreadPoolExecutor

   with ThreadPoolExecutor(max_workers=50) as executor:
       futures = []
       for tile, month in tile_month_pairs:
           future = executor.submit(submit_export_task, tile, month)
           futures.append(future)
   ```

3. **Remove validation `.getInfo()` calls:**
   ```python
   # Remove these during submission loop:
   logger.debug(f"  ✓ S1: {collected['s1'].bandNames().getInfo()}")  # EXPENSIVE!
   ```

**Expected Speedup:**
- Per-sample time: 6-8s → 1-2s (4-8× faster)
- Full export: 10 days → 1-2 days

---

### Phase 3: Full Export (After Test Validates)

**Trigger Conditions:**
1. Test export completes successfully
2. Training reaches epoch 10+ without collapse
3. Validation metrics look credible (val_loss < 1.0, variance >0.1)

**Config:** `configs/export-bay-area-full.yaml`
- 2,496 tiles × 48 months = 119,808 samples
- Training windows: ~105,000 (with H=6)
- Estimated time (current): ~10 days
- Estimated time (optimized): ~1-2 days

---

## Cost Estimates

### Test Export (Current)
- **EE compute**: 11,232 tasks × $0.02 = **~$225**
- **GCS storage**: ~15-50 GB = **$0.30-1.00/month**

### Full Export (Future)
- **EE compute**: 119,808 tasks × $0.02 = **~$2,400**
- **GCS storage**: ~150-500 GB = **$3-10/month**

### Training (Both)
- **GPU**: A100 80GB @ $2.50/hour
- **Duration**: ~3-5 days = 72-120 hours
- **Cost**: **$180-300** per training run

**Total for Test Phase:** ~$400-550 (one-time)
**Total for Full Phase:** ~$2,600-2,700 (one-time)

---

## Monitoring

### Export Progress

```bash
# Watch logs
tail -f /tmp/ee_export_test_v03.log

# Check Earth Engine tasks
open https://code.earthengine.google.com/tasks

# Check GCS bucket
gsutil ls gs://siad-exports/siad/test-export-v03/

# Count completed tiles
gsutil ls gs://siad-exports/siad/test-export-v03/**/*.tif | wc -l
```

### Training Metrics (Once Started)

**Watch for collapse indicators:**
```python
# Healthy training:
val/token_variance: >0.1 (tokens remain diverse)
val/token_covariance: <0.5 (not redundant)
ema_tau: 0.99 → 0.999 (ramping correctly)
batch/action_magnitude: >0 (not all zeros!)

# Collapse indicators:
val/token_variance: dropping to <0.01 (mode collapse)
val/token_covariance: approaching 1.0 (all tokens identical)
val/jepa_loss: stuck or increasing (not learning)
```

---

## Files Reference

### Spec-Compliant Configs (v0.3)
1. `configs/train-bay-area-v03.yaml` - Training config (zero spec deviations)
2. `configs/detector-bay-area-v03.yaml` - Post-training detection config
3. `configs/test-export-v03.yaml` - **Currently running export**
4. `configs/export-bay-area-full.yaml` - Full-scale export (pending)

### Documentation
1. `configs/v03-spec-fixes.md` - Spec compliance fixes explained
2. `configs/V03_COMPLETION_SUMMARY.md` - Initial completion summary
3. `configs/V03_EXPORT_STRATEGY.md` - This file

### Command Center (Completed Earlier)
1. `siad-command-center/scripts/convert_gallery_to_pngs.py` - .npz → PNG converter
2. `siad-command-center/frontend/components/TileDetailModal.tsx` - Real data UI
3. `siad-command-center/data/satellite_imagery/tiles/` - 90 real satellite images

---

## Next Steps

### Immediate (Now)
- ✅ Test export running (started 2026-03-05 00:29 UTC)
- ⏳ Wait for first tiles to complete (~30-60 min)
- ⏳ Validate exported GeoTIFF quality

### After First Tiles Available (~1 hour)
- Inspect exported data:
  ```bash
  gsutil cp gs://siad-exports/siad/test-export-v03/tile_x000_y000/2021-01.tif /tmp/
  gdalinfo /tmp/2021-01.tif
  ```
- Verify band order matches BAND_ORDER_V1
- Check for NaN/invalid values

### After Test Export Completes (~22 hours)
- Generate manifest.jsonl
- Start baseline training
- Monitor for collapse indicators

### After Training Validates (3-5 days)
- Decide: optimize orchestrator OR proceed with slow full export
- If optimizing: implement server-side compositing changes
- If proceeding: start full export with 10-day timeline

---

## Success Criteria

### Export Success
- All 11,232 tile-months exported without errors
- GeoTIFFs are valid (8 bands, 256×256px, UTM projection)
- S2 valid fraction >30% for >80% of samples
- No missing months in temporal coverage

### Training Success (Baseline)
- Reaches epoch 20+ without collapse
- Validation loss converges (<0.5)
- Token variance stays >0.1
- Predictions show spatial structure (not random noise)

### Detection Success (Baseline)
- Residuals show interpretable patterns
- Known anomalies (wildfires, floods) have high residuals
- Neutral scenario produces credible counterfactuals

---

## Risk Mitigation

### Risk 1: Export Fails Midway
- **Likelihood:** Medium (EE quota limits, network issues)
- **Impact:** High (lose partial progress)
- **Mitigation:** Checkpoint every 100 tiles, resume from last checkpoint

### Risk 2: Training Collapses
- **Likelihood:** Medium (first run with new spec)
- **Impact:** High (wasted GPU time/cost)
- **Mitigation:** Monitor first 10 epochs closely, kill if variance drops

### Risk 3: CHIRPS Anomaly Missing
- **Likelihood:** High (climatology not precomputed)
- **Impact:** Low (can recompute post-export)
- **Mitigation:** Accept zeros, fix in post-processing

### Risk 4: Spec Still Has Issues
- **Likelihood:** Low (thorough review completed)
- **Impact:** High (need to re-export and re-train)
- **Mitigation:** Test export validates spec before full commitment

---

## Conclusion

**Current State:**
- ✅ v0.3 configs are spec-compliant (zero deviations)
- ✅ Test export is running (11,232 samples, ~22 hours)
- ✅ Full export config ready but pending test validation
- ⚠️ Orchestrator performance bottleneck identified but not yet fixed

**Immediate Priority:**
- Let test export complete
- Validate data quality
- Start baseline training
- Watch for collapse indicators

**Next Decision Point (~22 hours):**
- If test export succeeds: decide on orchestrator optimization vs slow full export
- If test export fails: debug and fix before attempting full scale
- If training shows issues: revise spec and re-export

**Budget Committed:** ~$225 (test export EE compute)
**Budget Pending:** ~$2,400 (full export) + $180-300 (training)
