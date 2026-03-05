#!/usr/bin/env python3
"""
Recovery script for failed export.

Analyzes export logs to determine:
1. Which tiles were successfully submitted
2. Which tiles failed and need resubmission
3. Generates a recovery manifest for resuming export
"""

import re
import json
from pathlib import Path
from typing import Set, Tuple
from collections import defaultdict


def parse_export_log(log_path: str) -> Tuple[Set[str], Set[str], dict]:
    """
    Parse export log to extract success/failure information.

    Returns:
        (successful_tiles, failed_tiles, stats)
    """
    successful = set()  # (tile_id, month) tuples that were submitted
    failed = set()  # (tile_id, month) tuples that failed
    processed = set()  # All (tile_id, month) tuples that were processed

    stats = {
        'total_processed': 0,
        'successful_submissions': 0,
        'failed_submissions': 0,
        'skipped': 0
    }

    with open(log_path, 'r') as f:
        current_tile_month = None

        for line in f:
            # Match processing line: [N/11232] Processing tile_x000_y000 / 2021-01
            process_match = re.search(r'\[(\d+)/\d+\] Processing (tile_x\d+_y\d+) / (\d{4}-\d{2})', line)
            if process_match:
                tile_id = process_match.group(2)
                month = process_match.group(3)
                current_tile_month = (tile_id, month)
                processed.add(current_tile_month)
                stats['total_processed'] += 1

            # Match success: ✓ Export task started: TASK_ID
            if '✓ Export task started:' in line and current_tile_month:
                successful.add(current_tile_month)
                stats['successful_submissions'] += 1
                current_tile_month = None  # Reset

            # Match failure: ✗ Export task failed
            if '✗ Export task failed:' in line and current_tile_month:
                failed.add(current_tile_month)
                stats['failed_submissions'] += 1
                current_tile_month = None  # Reset

            # Match skipped
            if 'Skipped' in line:
                stats['skipped'] += 1

    return successful, failed, stats


def generate_recovery_config(
    successful_tiles: Set[Tuple[str, str]],
    failed_tiles: Set[Tuple[str, str]],
    original_config_path: str,
    output_path: str
):
    """
    Generate a recovery config that excludes already-successful tiles.

    For now, we'll create a simple text file listing failed tiles.
    A full implementation would modify the export orchestrator to accept
    a skip list.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Write failed tiles list
    with open(output, 'w') as f:
        f.write("# Failed tile-months that need resubmission\n")
        f.write(f"# Total: {len(failed_tiles)}\n\n")

        # Group by tile
        by_tile = defaultdict(list)
        for tile_id, month in sorted(failed_tiles):
            by_tile[tile_id].append(month)

        for tile_id in sorted(by_tile.keys()):
            months = sorted(by_tile[tile_id])
            f.write(f"\n# {tile_id} ({len(months)} months)\n")
            for month in months:
                f.write(f"{tile_id}\t{month}\n")

    print(f"✓ Recovery manifest written to: {output}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scripts/recover_export.py <log_file>")
        print("Example: python scripts/recover_export.py /tmp/ee_export_test_v03.log")
        sys.exit(1)

    log_path = sys.argv[1]

    if not Path(log_path).exists():
        print(f"Error: Log file not found: {log_path}")
        sys.exit(1)

    print("Analyzing export log...")
    successful, failed, stats = parse_export_log(log_path)

    # Print summary
    print("\n" + "=" * 60)
    print("EXPORT RECOVERY ANALYSIS")
    print("=" * 60)
    print(f"Total processed:          {stats['total_processed']:>6,}")
    print(f"Successful submissions:   {stats['successful_submissions']:>6,} ({stats['successful_submissions']/stats['total_processed']*100:.1f}%)")
    print(f"Failed submissions:       {stats['failed_submissions']:>6,} ({stats['failed_submissions']/stats['total_processed']*100:.1f}%)")
    print(f"Skipped (no data):        {stats['skipped']:>6,}")
    print("=" * 60)

    # Calculate what's missing
    processed_set = successful | failed
    total_expected = 11232  # From test-export-v03.yaml

    if stats['total_processed'] < total_expected:
        not_yet_processed = total_expected - stats['total_processed']
        print(f"\nNOTE: Export was interrupted at {stats['total_processed']}/{total_expected}")
        print(f"      {not_yet_processed:,} tile-months were never processed")

    # Generate recovery manifest
    output_path = "data/exports/recovery_manifest.txt"
    generate_recovery_config(successful, failed, None, output_path)

    print(f"\nTo resume export:")
    print(f"  1. Wait for currently running Earth Engine tasks to complete")
    print(f"  2. Check task status: https://code.earthengine.google.com/tasks")
    print(f"  3. Re-run export with fixed orchestrator (already done)")
    print(f"\nWith the fixed orchestrator:")
    print(f"  - Retry logic with exponential backoff (30s → 8 minutes)")
    print(f"  - Will wait for queue space instead of failing")
    print(f"  - Successfully submitted tiles: {len(successful):,}")
    print(f"  - Tiles needing resubmission: {len(failed):,}")


if __name__ == '__main__':
    main()
