#!/usr/bin/env python3
"""
Check Earth Engine task status to see how many exports have completed.
"""

import ee
from collections import Counter
import sys

try:
    # Try to initialize EE (will use existing auth)
    ee.Initialize(project='siad-earth-engine')

    print("=" * 60)
    print("EARTH ENGINE TASK STATUS")
    print("=" * 60)
    print()

    # Get all tasks for this project
    print("Fetching tasks from Earth Engine...")
    tasks = ee.data.getTaskList()

    # Filter for SIAD export tasks
    siad_tasks = [t for t in tasks if 'siad_' in t.get('description', '').lower()]

    if not siad_tasks:
        print("⚠️  No SIAD export tasks found")
        print("   Tasks may not have started yet, or completed and been cleared")
        sys.exit(0)

    # Count by status
    status_counts = Counter(t['state'] for t in siad_tasks)

    print(f"Found {len(siad_tasks)} SIAD export tasks:")
    print()

    for status in ['READY', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED']:
        count = status_counts.get(status, 0)
        if count > 0:
            emoji = {
                'READY': '⏸️ ',
                'RUNNING': '🔄',
                'COMPLETED': '✅',
                'FAILED': '❌',
                'CANCELLED': '🚫'
            }.get(status, '  ')
            print(f"  {emoji} {status:12s}: {count:>5,}")

    print()
    print("=" * 60)

    # Show completion percentage
    completed = status_counts.get('COMPLETED', 0)
    total_expected = 11232  # From test-export-v03.yaml

    if completed > 0:
        percent = (completed / total_expected) * 100
        print(f"📊 Completion: {completed:,} / {total_expected:,} ({percent:.1f}%)")
        print()
        print(f"✓ {completed:,} GeoTIFF files are ready to use in GCS")
    else:
        print("⏳ No tasks completed yet")
        print("   Files will appear in GCS as tasks finish")

    print()

    # Show recent failures if any
    failed_tasks = [t for t in siad_tasks if t['state'] == 'FAILED']
    if failed_tasks:
        print(f"⚠️  {len(failed_tasks)} tasks failed:")
        for task in failed_tasks[:5]:  # Show first 5
            print(f"   - {task.get('description', 'unknown')}")
            if 'error_message' in task:
                print(f"     Error: {task['error_message'][:100]}")
        if len(failed_tasks) > 5:
            print(f"   ... and {len(failed_tasks) - 5} more")

    print()
    print("Monitor at: https://code.earthengine.google.com/tasks")

except Exception as e:
    print(f"Error: {e}")
    print()
    print("Make sure Earth Engine is authenticated:")
    print("  earthengine authenticate")
    sys.exit(1)
