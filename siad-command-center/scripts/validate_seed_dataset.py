#!/usr/bin/env python
"""
Validate seed dataset and compute statistics.

Verifies all required files are present and computes summary statistics.
"""

import json
from pathlib import Path


def format_size(bytes_size: int) -> str:
    """Format byte size as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def validate_tile_month(
    tile_dir: Path,
    tile_id: int,
    month: int
) -> dict:
    """
    Validate all files for one tile/month combination.

    Returns dictionary with validation results.
    """
    month_dir = tile_dir / f"month_{month:02d}"
    overlay_dir = month_dir / "overlays"

    required_files = [
        month_dir / "actual.png",
        month_dir / "predicted.png",
        month_dir / "residual.png",
        overlay_dir / f"2024-{month:02d}_wm_residual.png",
        overlay_dir / f"2024-{month:02d}_persist_baseline.png",
        overlay_dir / f"2024-{month:02d}_seasonal_baseline.png",
        overlay_dir / f"2024-{month:02d}_wm_hotspots.geojson",
    ]

    validation = {
        "tile_id": tile_id,
        "month": month,
        "missing": [],
        "present": 0,
        "total_size": 0
    }

    for file_path in required_files:
        if file_path.exists():
            validation["present"] += 1
            validation["total_size"] += file_path.stat().st_size
        else:
            validation["missing"].append(str(file_path.relative_to(tile_dir.parent.parent)))

    return validation


def validate_seed_dataset(data_dir: Path) -> dict:
    """
    Validate complete seed dataset.

    Returns validation report dictionary.
    """
    # Load metadata
    metadata_path = data_dir / "metadata.json"
    months_path = data_dir / "months.json"
    hotspots_path = data_dir / "hotspots_ranked.json"

    if not metadata_path.exists():
        return {"error": "metadata.json not found"}

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Initialize report
    report = {
        "dataset": {
            "num_tiles": len(metadata["tiles"]),
            "num_months": metadata["num_months"],
            "tile_ids": [t["tile_id"] for t in metadata["tiles"]],
            "change_types": list(metadata["change_types"].keys())
        },
        "files": {
            "metadata": metadata_path.exists(),
            "months": months_path.exists(),
            "hotspots_ranked": hotspots_path.exists()
        },
        "tiles": [],
        "summary": {
            "total_files": 0,
            "missing_files": 0,
            "total_size": 0
        }
    }

    # Validate each tile
    tiles_dir = data_dir / "tiles"

    for tile in metadata["tiles"]:
        tile_id = tile["tile_id"]
        tile_dir = tiles_dir / f"tile_{tile_id:03d}"

        # Check timeseries
        timeseries_path = tile_dir / "timeseries.json"
        timeseries_exists = timeseries_path.exists()

        if timeseries_exists:
            with open(timeseries_path) as f:
                timeseries = json.load(f)
        else:
            timeseries = {}

        tile_report = {
            "tile_id": tile_id,
            "change_type": tile["change_type"],
            "timeseries": timeseries_exists,
            "onset_month": timeseries.get("analysis", {}).get("onset_month", -1),
            "months": [],
            "total_files": 0,
            "missing_files": 0,
            "total_size": 0
        }

        # Validate each month
        for month in range(1, metadata["num_months"] + 1):
            month_validation = validate_tile_month(tile_dir, tile_id, month)

            tile_report["months"].append(month_validation)
            tile_report["total_files"] += month_validation["present"]
            tile_report["missing_files"] += len(month_validation["missing"])
            tile_report["total_size"] += month_validation["total_size"]

        # Add timeseries size
        if timeseries_exists:
            tile_report["total_size"] += timeseries_path.stat().st_size
            tile_report["total_files"] += 1

        report["tiles"].append(tile_report)

        # Update summary
        report["summary"]["total_files"] += tile_report["total_files"]
        report["summary"]["missing_files"] += tile_report["missing_files"]
        report["summary"]["total_size"] += tile_report["total_size"]

    # Add metadata file sizes
    for path in [metadata_path, months_path, hotspots_path]:
        if path.exists():
            report["summary"]["total_size"] += path.stat().st_size

    return report


def print_validation_report(report: dict):
    """Print formatted validation report."""
    if "error" in report:
        print(f"ERROR: {report['error']}")
        return

    print("=" * 60)
    print("SEED DATASET VALIDATION REPORT")
    print("=" * 60)

    # Dataset overview
    ds = report["dataset"]
    print(f"\nDataset Overview:")
    print(f"  Tiles: {ds['num_tiles']} {ds['tile_ids']}")
    print(f"  Months: {ds['num_months']}")
    print(f"  Change Types: {', '.join(ds['change_types'])}")

    # Metadata files
    print(f"\nMetadata Files:")
    for name, exists in report["files"].items():
        status = "✓" if exists else "✗"
        print(f"  {status} {name}.json")

    # Per-tile summary
    print(f"\nTile Summary:")
    for tile in report["tiles"]:
        status = "✓" if tile["missing_files"] == 0 else "✗"
        print(f"  {status} Tile {tile['tile_id']} ({tile['change_type']})")
        print(f"      Files: {tile['total_files']} present, {tile['missing_files']} missing")
        print(f"      Size: {format_size(tile['total_size'])}")
        print(f"      Onset: month {tile['onset_month']}")
        print(f"      Timeseries: {'✓' if tile['timeseries'] else '✗'}")

        # List missing files if any
        if tile["missing_files"] > 0:
            for month_data in tile["months"]:
                if month_data["missing"]:
                    print(f"      Missing in month {month_data['month']}:")
                    for missing in month_data["missing"]:
                        print(f"        - {missing}")

    # Overall summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total Files: {report['summary']['total_files']}")
    print(f"  Missing Files: {report['summary']['missing_files']}")
    print(f"  Total Size: {format_size(report['summary']['total_size'])}")
    print(f"  Status: {'PASS' if report['summary']['missing_files'] == 0 else 'FAIL'}")
    print(f"{'=' * 60}")


def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "aoi_sf_seed"

    print(f"Validating dataset: {data_dir}\n")

    report = validate_seed_dataset(data_dir)
    print_validation_report(report)

    # Save report
    report_path = data_dir / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    main()
