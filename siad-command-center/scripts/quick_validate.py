"""Quick validation for SIAD demo data."""

import json
from pathlib import Path
import h5py

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "aoi_sf_seed"

def main():
    print("\n" + "="*60)
    print("SIAD COMMAND CENTER - QUICK VALIDATION")
    print("="*60)

    errors = []

    # Check HDF5
    hdf5_path = DATA_DIR / "residuals_test.h5"
    if hdf5_path.exists():
        print(f"✓ HDF5 file exists: {hdf5_path}")
        try:
            with h5py.File(hdf5_path, 'r') as f:
                tile_count = len(list(f.keys()))
                print(f"  - Contains {tile_count} tiles")
        except Exception as e:
            errors.append(f"HDF5 file corrupted: {e}")
    else:
        errors.append("HDF5 file missing")

    # Check hotspots JSON
    hotspots_path = SEED_DIR / "hotspots_ranked.json"
    if hotspots_path.exists():
        with open(hotspots_path) as f:
            data = json.load(f)
            hotspot_count = len(data.get("hotspots", []))
            print(f"✓ Hotspots JSON exists: {hotspot_count} hotspots")
    else:
        errors.append("Hotspots JSON missing")

    # Check metadata JSON
    metadata_path = SEED_DIR / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            data = json.load(f)
            tile_count = len(data.get("tiles", []))
            print(f"✓ Metadata JSON exists: {tile_count} tiles")
    else:
        errors.append("Metadata JSON missing")

    # Check months JSON
    months_path = SEED_DIR / "months.json"
    if months_path.exists():
        with open(months_path) as f:
            data = json.load(f)
            month_count = len(data.get("months", []))
            print(f"✓ Months JSON exists: {month_count} months")
    else:
        errors.append("Months JSON missing")

    # Check tiles directory
    tiles_dir = SEED_DIR / "tiles"
    if tiles_dir.exists():
        tile_dirs = list(tiles_dir.iterdir())
        print(f"✓ Tiles directory exists: {len(tile_dirs)} tile subdirs")
    else:
        errors.append("Tiles directory missing")

    print("\n" + "="*60)
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    else:
        print("✓ VALIDATION PASSED - All required files present")
        return 0

if __name__ == "__main__":
    exit(main())
