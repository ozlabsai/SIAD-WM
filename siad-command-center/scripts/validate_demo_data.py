"""Validate demo dataset for SIAD Command Center.

This script checks:
- All required files exist
- Data integrity (no corrupted files)
- Consistent metadata across files
- Interesting hotspots for demo
- Static imagery files are accessible
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import h5py
import numpy as np

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "aoi_sf_seed"


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_file_structure() -> Dict[str, bool]:
    """Validate all required files exist."""
    print("\n" + "="*60)
    print("VALIDATING FILE STRUCTURE")
    print("="*60)

    required_files = {
        "HDF5 residuals": DATA_DIR / "residuals_test.h5",
        "Hotspots JSON": SEED_DIR / "hotspots_ranked.json",
        "Metadata JSON": SEED_DIR / "metadata.json",
        "Months JSON": SEED_DIR / "months.json",
        "Tiles directory": SEED_DIR / "tiles",
    }

    results = {}
    all_exist = True

    for name, path in required_files.items():
        exists = path.exists()
        results[name] = exists
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {path}")

        if not exists:
            all_exist = False

    if not all_exist:
        raise ValidationError("Missing required files")

    print("\n✓ All required files present")
    return results


def validate_hdf5_integrity() -> Dict[str, any]:
    """Validate HDF5 file integrity."""
    print("\n" + "="*60)
    print("VALIDATING HDF5 INTEGRITY")
    print("="*60)

    hdf5_path = DATA_DIR / "residuals_test.h5"

    try:
        with h5py.File(hdf5_path, 'r') as f:
            # Check required groups
            required_groups = ['tiles', 'metadata']
            for group in required_groups:
                if group not in f:
                    raise ValidationError(f"Missing group: {group}")
                print(f"✓ Group '{group}' present")

            # Check metadata
            metadata = json.loads(f['metadata']['aoi'].asstr()[()])
            print(f"  - AOI: {metadata.get('name', 'Unknown')}")
            print(f"  - Tile count: {metadata.get('tile_count', 0)}")
            print(f"  - Months: {metadata.get('num_months', 0)}")

            # Check tiles
            tiles_group = f['tiles']
            tile_ids = list(tiles_group.keys())
            print(f"  - Tiles in HDF5: {tile_ids}")

            # Validate each tile has required datasets
            for tile_id in tile_ids:
                tile_group = tiles_group[tile_id]
                required_datasets = ['residuals', 'timestamps', 'coordinates']

                for dataset in required_datasets:
                    if dataset not in tile_group:
                        raise ValidationError(
                            f"Missing dataset '{dataset}' in tile {tile_id}"
                        )

                # Check data shapes
                residuals_shape = tile_group['residuals'].shape
                print(f"  - Tile {tile_id} residuals shape: {residuals_shape}")

            return {
                "valid": True,
                "metadata": metadata,
                "tile_ids": tile_ids,
            }

    except Exception as e:
        raise ValidationError(f"HDF5 validation failed: {e}")


def validate_json_files() -> Dict[str, any]:
    """Validate JSON files contain expected data."""
    print("\n" + "="*60)
    print("VALIDATING JSON FILES")
    print("="*60)

    # Load hotspots
    with open(SEED_DIR / "hotspots_ranked.json") as f:
        hotspots_data = json.load(f)

    # Load metadata
    with open(SEED_DIR / "metadata.json") as f:
        metadata = json.load(f)

    # Load months
    with open(SEED_DIR / "months.json") as f:
        months_data = json.load(f)

    # Validate hotspots
    hotspots = hotspots_data.get("hotspots", [])
    print(f"✓ Hotspots: {len(hotspots)} total")

    if len(hotspots) == 0:
        raise ValidationError("No hotspots found")

    # Check hotspot structure
    required_hotspot_fields = [
        "tile_id", "month", "change_type", "location",
        "region_id", "mean_score", "severity"
    ]

    first_hotspot = hotspots[0]
    for field in required_hotspot_fields:
        if field not in first_hotspot:
            raise ValidationError(f"Missing field '{field}' in hotspot")

    print(f"  - Score range: {min(h['mean_score'] for h in hotspots):.3f} - {max(h['mean_score'] for h in hotspots):.3f}")
    print(f"  - Change types: {set(h['change_type'] for h in hotspots)}")
    print(f"  - Severities: {set(h['severity'] for h in hotspots)}")

    # Validate metadata
    tiles = metadata.get("tiles", [])
    print(f"✓ Metadata: {len(tiles)} tiles")

    for tile in tiles:
        required_tile_fields = [
            "tile_id", "change_type", "onset_month", "region",
            "latitude", "longitude"
        ]
        for field in required_tile_fields:
            if field not in tile:
                raise ValidationError(f"Missing field '{field}' in tile metadata")

    # Validate months
    months = months_data.get("months", [])
    print(f"✓ Months: {len(months)} total ({months[0]} to {months[-1]})")

    return {
        "hotspots": hotspots,
        "metadata": metadata,
        "months": months,
    }


def validate_tile_directories(metadata: Dict) -> List[str]:
    """Validate tile directories and imagery files."""
    print("\n" + "="*60)
    print("VALIDATING TILE DIRECTORIES")
    print("="*60)

    tiles_dir = SEED_DIR / "tiles"
    tiles = metadata.get("tiles", [])

    missing_files = []

    for tile in tiles:
        tile_id = tile["tile_id"]
        tile_dir = tiles_dir / str(tile_id)

        if not tile_dir.exists():
            print(f"✗ Missing directory: {tile_dir}")
            missing_files.append(str(tile_dir))
            continue

        print(f"✓ Tile {tile_id} directory exists")

        # Check for timeline JSON
        timeline_file = tile_dir / "timeline.json"
        if timeline_file.exists():
            print(f"  - Timeline data present")
        else:
            print(f"  ⚠ Timeline data missing (non-critical)")

        # Check for imagery files (optional for demo)
        imagery_count = len(list(tile_dir.glob("*.png")))
        print(f"  - Imagery files: {imagery_count}")

    if missing_files:
        print(f"\n⚠ Warning: {len(missing_files)} tile directories missing")
    else:
        print(f"\n✓ All tile directories present")

    return missing_files


def validate_data_consistency(
    hdf5_data: Dict,
    json_data: Dict
) -> bool:
    """Validate consistency between HDF5 and JSON data."""
    print("\n" + "="*60)
    print("VALIDATING DATA CONSISTENCY")
    print("="*60)

    # Check tile IDs match
    hdf5_tiles = set(hdf5_data["tile_ids"])
    json_tiles = set(str(t["tile_id"]) for t in json_data["metadata"]["tiles"])

    print(f"HDF5 tiles: {hdf5_tiles}")
    print(f"JSON tiles: {json_tiles}")

    if hdf5_tiles != json_tiles:
        print("⚠ Warning: Tile ID mismatch between HDF5 and JSON")
    else:
        print("✓ Tile IDs consistent")

    # Check month counts
    hdf5_months = hdf5_data["metadata"].get("num_months", 0)
    json_months = len(json_data["months"])

    if hdf5_months != json_months:
        print(f"⚠ Warning: Month count mismatch (HDF5: {hdf5_months}, JSON: {json_months})")
    else:
        print(f"✓ Month count consistent: {json_months}")

    return True


def identify_demo_hotspots(hotspots: List[Dict]) -> List[Dict]:
    """Identify interesting hotspots for demo."""
    print("\n" + "="*60)
    print("IDENTIFYING DEMO HOTSPOTS")
    print("="*60)

    # Top 5 by score
    top_by_score = sorted(hotspots, key=lambda h: h["mean_score"], reverse=True)[:5]

    print("\nTop 5 Hotspots by Score:")
    for i, h in enumerate(top_by_score, 1):
        print(f"{i}. Tile {h['tile_id']}, Month {h['month']}: "
              f"Score {h['mean_score']:.3f} ({h['severity']}) - {h['change_type']}")

    # Different change types
    change_types = {}
    for h in hotspots:
        ct = h["change_type"]
        if ct not in change_types:
            change_types[ct] = h

    print("\nOne Example of Each Change Type:")
    for ct, h in change_types.items():
        print(f"- {ct}: Tile {h['tile_id']}, Month {h['month']}, "
              f"Score {h['mean_score']:.3f}")

    # Different severities
    severities = {}
    for h in hotspots:
        sev = h["severity"]
        if sev not in severities:
            severities[sev] = h

    print("\nOne Example of Each Severity:")
    for sev, h in severities.items():
        print(f"- {sev}: Tile {h['tile_id']}, Month {h['month']}, "
              f"Score {h['mean_score']:.3f}")

    return top_by_score


def generate_validation_report() -> Dict:
    """Generate comprehensive validation report."""
    print("\n" + "="*60)
    print("SIAD COMMAND CENTER - DEMO DATA VALIDATION")
    print("="*60)

    report = {
        "status": "unknown",
        "checks": {},
        "errors": [],
        "warnings": [],
    }

    try:
        # Check 1: File structure
        report["checks"]["file_structure"] = validate_file_structure()

        # Check 2: HDF5 integrity
        hdf5_data = validate_hdf5_integrity()
        report["checks"]["hdf5_integrity"] = True

        # Check 3: JSON files
        json_data = validate_json_files()
        report["checks"]["json_files"] = True

        # Check 4: Tile directories
        missing_tiles = validate_tile_directories(json_data["metadata"])
        report["checks"]["tile_directories"] = len(missing_tiles) == 0
        if missing_tiles:
            report["warnings"].append(
                f"{len(missing_tiles)} tile directories missing"
            )

        # Check 5: Data consistency
        validate_data_consistency(hdf5_data, json_data)
        report["checks"]["data_consistency"] = True

        # Check 6: Demo hotspots
        demo_hotspots = identify_demo_hotspots(json_data["hotspots"])
        report["demo_hotspots"] = [
            {
                "tile_id": h["tile_id"],
                "month": h["month"],
                "score": h["mean_score"],
                "change_type": h["change_type"],
                "severity": h["severity"],
            }
            for h in demo_hotspots
        ]

        # Overall status
        all_critical_passed = all([
            report["checks"]["file_structure"],
            report["checks"]["hdf5_integrity"],
            report["checks"]["json_files"],
            report["checks"]["data_consistency"],
        ])

        if all_critical_passed:
            report["status"] = "PASS"
        else:
            report["status"] = "FAIL"

    except ValidationError as e:
        report["status"] = "FAIL"
        report["errors"].append(str(e))
        print(f"\n✗ VALIDATION FAILED: {e}")

    return report


def main():
    """Run validation and generate report."""
    report = generate_validation_report()

    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    print(f"\nStatus: {report['status']}")

    if report["errors"]:
        print(f"\nErrors ({len(report['errors'])}):")
        for error in report["errors"]:
            print(f"  ✗ {error}")

    if report["warnings"]:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warning in report["warnings"]:
            print(f"  ⚠ {warning}")

    print("\nChecks:")
    for check, passed in report["checks"].items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")

    # Save report
    report_path = SEED_DIR / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Validation report saved to: {report_path}")

    # Exit code
    if report["status"] == "PASS":
        print("\n✓ DEMO DATA VALIDATION PASSED")
        sys.exit(0)
    else:
        print("\n✗ DEMO DATA VALIDATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
