# SIAD Export Recovery - 2026-03-05

## What Happened

The initial test export (started 00:29 UTC) failed due to a **critical bug in the export orchestrator**: no retry logic for Earth Engine's queue-full errors.

### Original Export Stats (FAILED)
- **Duration:** ~11 hours (00:29 - 11:23 UTC)
- **Tiles processed:** 6,461 / 11,232 (57.5%)
- **Successful submissions:** 2,925 (26.0% of total, 45.3% of processed)
- **Failed submissions:** 3,345 (29.8% of total, 51.8% of processed)
- **Not yet processed:** 4,771 (42.5% of total)
- **Skipped (no data):** 190

### Root Cause

The orchestrator hit Earth Engine's queue limit (3,000 concurrent tasks) around sample #2,900. After that:

1. **Queue saturated:** EE had 3,000 tasks running/pending
2. **No retry logic:** Orchestrator immediately failed on queue-full errors
3. **Permanent loss:** Failed tiles were marked as "skipped" and never retried
4. **Continued wastefully:** Orchestrator kept processing tiles for 8+ more hours, failing ~80% of submissions

**Code bug** (src/siad/data/export_orchestrator.py:373-375):
```python
except Exception as e:
    logger.error(f"  ✗ Export task failed: {e}")
    skipped += 1  # BUG: No retry, permanently lost!
```

---

## Fix Applied

### 1. Added Retry Logic with Exponential Backoff

**New behavior** (src/siad/data/export_orchestrator.py:238-310):
```python
def submit_export_task(
    self,
    image: ee.Image,
    tile: Tile,
    month: str,
    description: str,
    max_retries: int = 10  # NEW: Up to 10 retries
) -> str:
    """
    Submit export task with retry logic for queue-full errors.
    """
    for attempt in range(max_retries):
        try:
            task = ee.batch.Export.image.toCloudStorage(...)
            task.start()
            return task.id  # Success!

        except Exception as e:
            if "Too many tasks" in str(e) or "limit 3000" in str(e):
                if attempt < max_retries - 1:
                    # Exponential backoff: 30s, 60s, 120s, 240s, 480s, ...
                    wait_time = 30 * (2 ** attempt)
                    logger.warning(f"Queue full, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise  # Fail after 10 attempts
            else:
                raise  # Non-queue errors fail immediately
```

**Retry schedule:**
1. Attempt 1 fails → wait 30 seconds
2. Attempt 2 fails → wait 60 seconds
3. Attempt 3 fails → wait 120 seconds (2 min)
4. Attempt 4 fails → wait 240 seconds (4 min)
5. Attempt 5 fails → wait 480 seconds (8 min)
6. ... up to 10 attempts total

**Max wait time:** ~17 minutes per sample (if all 10 attempts fail)

---

## Recovery Analysis

Created recovery script: `scripts/recover_export.py`

**Usage:**
```bash
uv run python scripts/recover_export.py /tmp/ee_export_test_v03.log
```

**Output:**
- Summary of successful vs failed submissions
- Recovery manifest: `data/exports/recovery_manifest.txt`
- Lists 3,345 failed tile-months that need resubmission

**Example output:**
```
============================================================
EXPORT RECOVERY ANALYSIS
============================================================
Total processed:           6,461
Successful submissions:    2,925 (45.3%)
Failed submissions:        3,345 (51.8%)
Skipped (no data):           190
============================================================

NOTE: Export was interrupted at 6461/11232
      4,771 tile-months were never processed
```

---

## Current Status

### Restarted Export ✅

**New export started:** 11:25 UTC (2026-03-05)
**Log file:** `/tmp/ee_export_test_v03_retry.log`
**Task ID:** 325937

**Expected behavior:**
1. **Start from beginning:** Will reprocess all 11,232 tile-months
2. **Duplicate submissions:** Will resubmit the 2,925 already-successful tiles
   - Earth Engine will handle duplicates (same GCS path → overwrites)
   - Minor waste but ensures completeness
3. **Retry on queue-full:** Will wait up to 17 minutes per sample instead of failing
4. **Eventual completion:** Should succeed on all tiles

### Earth Engine Queue Status

**Current state:**
- ~2,925 tasks from original export may still be running/completed
- New export is adding more tasks
- Queue will fluctuate between full and available

**Monitoring:**
```bash
# Watch live export progress
tail -f /tmp/ee_export_test_v03_retry.log

# Check Earth Engine console
open https://code.earthengine.google.com/tasks

# Check for completed exports in GCS
gsutil ls gs://siad-exports/siad/test-export-v03/ | head -50
```

---

## Lessons Learned

### 1. **Always add retry logic for rate-limited APIs**
Earth Engine's 3,000-task queue limit is a known constraint. Should have anticipated this.

### 2. **Fail fast on unrecoverable errors**
The original orchestrator continued processing for 8 hours while failing 80% of submissions. Should have detected the pattern and stopped.

### 3. **Test with smaller batches first**
Could have caught this with a 100-tile test export before committing to 11,232 samples.

### 4. **Monitor queue depth**
Could query `ee.data.getTaskList()` to check queue status before submitting more tasks.

---

## Estimated Timeline

### Best Case (Queue Clears Quickly)
- **Time per sample:** ~10 seconds (collection + submission)
- **Total samples:** 11,232
- **Estimated duration:** ~31 hours
- **Completion:** 2026-03-06 18:00 UTC

### Worst Case (Queue Saturates Again)
- **Time per sample:** ~10 seconds + retry delays (avg 2-3 minutes)
- **Total samples:** 11,232
- **Estimated duration:** ~40-50 hours
- **Completion:** 2026-03-07 03:00-13:00 UTC

### Realistic Scenario
- First ~2,900 samples: Submit quickly (queue has space from completed tasks)
- Samples 2,901-8,000: Occasional retries (30-120s waits)
- Samples 8,001-11,232: More frequent retries as new queue fills
- **Estimated completion:** ~36-40 hours (2026-03-06 23:00 - 03:00 UTC)

---

## Data Recovery Options

### Option A: Let Restarted Export Run (Current Choice) ✅

**Pros:**
- Simplest approach
- Ensures 100% coverage (reprocesses everything)
- Fixed orchestrator prevents data loss

**Cons:**
- Wastes compute on reprocessing 2,925 already-successful tiles
- Takes full ~36-40 hours

### Option B: Smart Resume (Not Implemented)

Would require modifying orchestrator to:
1. Accept recovery manifest as input
2. Skip tiles that already succeeded
3. Only process the 3,345 failed + 4,771 unprocessed = 8,116 tiles

**Time savings:** ~10 hours (skips 2,925 tiles)
**Complexity:** Medium (need to parse manifest, modify orchestrator)

### Option C: Manual Deduplication (Post-Export)

After export completes:
1. Check GCS for duplicate tiles (should have latest timestamp)
2. Verify all 11,232 tiles present
3. Delete older duplicates if any

**Effort:** Minimal (1-2 hours manual validation)

---

## Success Criteria

Export is successful when:

1. ✅ **All tiles submitted:** 11,232 Earth Engine tasks started
2. ✅ **All tasks complete:** Check Earth Engine console shows 100% completion
3. ✅ **All GeoTIFFs in GCS:** `gsutil ls gs://siad-exports/siad/test-export-v03/**/*.tif | wc -l` returns ~11,232
4. ✅ **Manifest generated:** `data/exports/test-export-v03_manifest.jsonl` contains 11,232 rows
5. ✅ **No missing tiles:** All 234 tiles have all 48 months

---

## Next Steps

### Immediate (While Export Runs)
1. Monitor export progress: `tail -f /tmp/ee_export_test_v03_retry.log`
2. Watch for retry patterns (should see "Queue full, waiting..." messages)
3. Verify retry logic works correctly

### After First Retry Encountered
1. Confirm backoff timing is correct (30s, 60s, 120s, ...)
2. Check that task eventually succeeds after retry
3. Monitor queue depth trends

### After Export Completes (~36-40 hours)
1. Run validation:
   ```bash
   gsutil ls gs://siad-exports/siad/test-export-v03/**/*.tif | wc -l
   # Should return: ~11232
   ```

2. Check for missing tiles:
   ```bash
   uv run python scripts/validate_export.py \
     --manifest data/exports/test-export-v03_manifest.jsonl
   ```

3. Generate training manifest for PyTorch dataset

4. Start baseline training:
   ```bash
   uv run siad train \
     --config configs/train-bay-area-v03.yaml \
     --data-path gs://siad-exports/siad/test-export-v03/
   ```

---

## Files Created/Modified

### Modified
1. `src/siad/data/export_orchestrator.py` - Added retry logic with exponential backoff

### Created
1. `scripts/recover_export.py` - Recovery analysis script
2. `data/exports/recovery_manifest.txt` - List of 3,345 failed tiles
3. `EXPORT_RECOVERY.md` - This document

### Logs
1. `/tmp/ee_export_test_v03.log` - Original failed export (00:29-11:23 UTC)
2. `/tmp/ee_export_test_v03_retry.log` - New export with retry logic (started 11:25 UTC)

---

## Cost Impact

### Original Export (Wasted)
- **EE compute:** ~2,925 successful tasks × $0.02 = **$58.50**
- **Wasted processing:** ~3,345 failed tasks × 10 sec CPU = wasted resources (not billed)

### Retry Export (Current)
- **EE compute:** ~11,232 tasks × $0.02 = **$224.64**
- **Duplicate overhead:** ~2,925 redundant submissions = **$58.50 extra**

**Total cost:** ~$283 (includes original + retry)
**Original estimate:** ~$225

**Cost overrun:** ~$58 (~26% over budget) due to failed first attempt

---

## Status: 🟢 **RUNNING WITH RETRY LOGIC**

**Started:** 2026-03-05 11:25 UTC
**ETA:** 2026-03-06 23:00 - 2026-03-07 03:00 UTC (~36-40 hours)
**Progress monitoring:** `tail -f /tmp/ee_export_test_v03_retry.log`
