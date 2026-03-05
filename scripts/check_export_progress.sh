#!/bin/bash
# Check SIAD export progress across submission and completion

echo "=========================================="
echo "SIAD Export Progress Monitor"
echo "=========================================="
echo ""

# 1. Count tasks submitted (from logs)
echo "📝 SUBMISSION STATUS (from orchestrator logs):"
if [ -f /tmp/ee_export_test_v03_retry.log ]; then
    submitted=$(grep -c "Export task started" /tmp/ee_export_test_v03_retry.log 2>/dev/null || echo "0")
    failed=$(grep -c "Queue full.*attempt 10/10" /tmp/ee_export_test_v03_retry.log 2>/dev/null || echo "0")
    processing=$(grep "\[.*/..*\] Processing" /tmp/ee_export_test_v03_retry.log 2>/dev/null | tail -1)

    echo "  ✓ Tasks submitted: $submitted / 11,232"
    echo "  ✗ Failed after retries: $failed"
    echo "  📍 Current: $processing"
else
    echo "  ⚠ Log file not found: /tmp/ee_export_test_v03_retry.log"
fi

echo ""

# 2. Count completed exports in GCS
echo "💾 COMPLETION STATUS (in Google Cloud Storage):"
completed=$(gsutil ls -r "gs://siad-exports/siad/test-export-v03/**/*.tif" 2>/dev/null | wc -l | tr -d ' ')
if [ "$completed" -eq 0 ]; then
    echo "  ⏳ No files completed yet (Earth Engine still processing)"
    echo "  ℹ️  Tasks are submitted but EE takes time to render GeoTIFFs"
else
    echo "  ✓ Completed files: $completed / 11,232 ($(echo "scale=1; $completed * 100 / 11232" | bc)%)"
fi

echo ""

# 3. Show retry activity (last 10 retries)
echo "🔄 RECENT RETRY ACTIVITY:"
if [ -f /tmp/ee_export_test_v03_retry.log ]; then
    retries=$(grep "Queue full" /tmp/ee_export_test_v03_retry.log 2>/dev/null | tail -5)
    if [ -z "$retries" ]; then
        echo "  ✓ No recent retries (queue has space)"
    else
        echo "$retries" | sed 's/^/  /'
    fi
else
    echo "  ⚠ Log file not found"
fi

echo ""

# 4. Estimate progress
echo "📊 ESTIMATED PROGRESS:"
if [ -f /tmp/ee_export_test_v03_retry.log ]; then
    last_line=$(grep "\[.*/..*\] Processing" /tmp/ee_export_test_v03_retry.log 2>/dev/null | tail -1)
    if [ -n "$last_line" ]; then
        current=$(echo "$last_line" | grep -oP '\[\K[0-9]+(?=/)')
        percent=$(echo "scale=1; $current * 100 / 11232" | bc)
        echo "  Processing: $current / 11,232 ($percent%)"

        # Estimate remaining time
        start_time=$(head -1 /tmp/ee_export_test_v03_retry.log | grep -oP '\[\K[0-9-]+ [0-9:]+')
        if [ -n "$start_time" ]; then
            start_epoch=$(date -j -f "%Y-%m-%d %H:%M:%S" "$start_time" "+%s" 2>/dev/null || echo "")
            if [ -n "$start_epoch" ]; then
                now_epoch=$(date +%s)
                elapsed=$((now_epoch - start_epoch))
                elapsed_hours=$(echo "scale=1; $elapsed / 3600" | bc)

                if [ "$current" -gt 0 ]; then
                    rate=$(echo "scale=2; $current / $elapsed" | bc)
                    remaining=$((11232 - current))
                    eta_seconds=$(echo "scale=0; $remaining / $rate" | bc)
                    eta_hours=$(echo "scale=1; $eta_seconds / 3600" | bc)

                    echo "  Elapsed: ${elapsed_hours}h"
                    echo "  Rate: $(echo "scale=1; $rate * 60" | bc) samples/min"
                    echo "  ETA: ${eta_hours}h remaining"
                fi
            fi
        fi
    fi
fi

echo ""

# 5. Quick commands
echo "📋 MONITORING COMMANDS:"
echo "  Live log:     tail -f /tmp/ee_export_test_v03_retry.log"
echo "  EE console:   open https://code.earthengine.google.com/tasks"
echo "  GCS browser:  open https://console.cloud.google.com/storage/browser/siad-exports/siad/test-export-v03"
echo "  This script:  bash scripts/check_export_progress.sh"

echo ""
echo "=========================================="
