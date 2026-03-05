# M1B Data Pipeline - Quick Start Guide

## Prerequisites

- UV installed (for Python dependency management)
- Python 3.13+ with dependencies: h5py, numpy, scipy, Pillow
- Existing data files:
  - `data/satellite_imagery/` (75 tiles × 12 months)
  - `data/residuals_test.h5` (world model predictions)

## Run Complete Pipeline

Execute all scripts in sequence:

```bash
cd /Users/guynachshon/Documents/ozlabs/labs/SIAD/siad-command-center

# 1. Create seed dataset (2 tiles × 6 months)
uv run python scripts/create_seed_dataset.py

# 2. Generate residual overlays
uv run python scripts/generate_residual_overlays.py

# 3. Generate baseline overlays
uv run python scripts/create_baseline_overlays.py

# 4. Generate hotspot GeoJSON
uv run python scripts/generate_hotspots.py

# 5. Generate timeline JSON
uv run python scripts/generate_timelines.py

# 6. Validate outputs
uv run python scripts/validate_seed_dataset.py
```

**Total runtime:** ~3 seconds

## Output Location

```
data/aoi_sf_seed/
├── tiles/
│   ├── tile_001/      # 43 files
│   └── tile_002/      # 43 files
├── metadata.json
├── months.json
├── hotspots_ranked.json
└── validation_report.json
```

**Total size:** 1.3 MB (90 files)

## Verify Success

Expected output from validation:

```
============================================================
SEED DATASET VALIDATION REPORT
============================================================

Dataset Overview:
  Tiles: 2 [1, 2]
  Months: 6
  Change Types: urban_construction, infrastructure

Tile Summary:
  ✓ Tile 1 (urban_construction)
      Files: 43 present, 0 missing
      Size: 574.66 KB
      Onset: month 3
      Timeseries: ✓
  ✓ Tile 2 (infrastructure)
      Files: 43 present, 0 missing
      Size: 542.48 KB
      Onset: month 3
      Timeseries: ✓

SUMMARY
  Total Files: 86
  Missing Files: 0
  Total Size: 1.09 MB
  Status: PASS
============================================================
```

## Generated Artifacts

### Per Tile/Month
- `actual.png` - Satellite imagery
- `predicted.png` - World model prediction
- `residual.png` - Pixel-level residual
- `overlays/2024-XX_wm_residual.png` - Color-mapped overlay
- `overlays/2024-XX_persist_baseline.png` - Persistence baseline
- `overlays/2024-XX_seasonal_baseline.png` - Seasonal baseline
- `overlays/2024-XX_wm_hotspots.geojson` - Anomaly polygons

### Per Tile
- `timeseries.json` - Monthly scores and onset detection

### Global
- `metadata.json` - Tile metadata (lat/lon, change types)
- `months.json` - Month labels
- `hotspots_ranked.json` - All hotspots ranked by severity

## Key Results

### Tile 1 (Urban Construction)
- **Location:** 49.18°N, 130.95°W
- **Onset:** Month 3 (March 2024)
- **Peak Score:** 0.898 (89.8% confidence)
- **Hotspots:** 6 detected (2 critical)

### Tile 2 (Infrastructure)
- **Location:** 11.93°S, 101.75°W
- **Onset:** Month 3 (March 2024)
- **Peak Score:** 0.766 (76.6% confidence)
- **Hotspots:** 3 detected (1 critical)

## Troubleshooting

### "HDF5 file not found"
Ensure `data/residuals_test.h5` exists:
```bash
ls -lh data/residuals_test.h5
```

### "Source imagery not found"
Verify satellite imagery directory:
```bash
ls data/satellite_imagery/tiles/tile_000/month_01/
```

### "Missing dependencies"
Install dependencies with UV:
```bash
uv pip install h5py numpy scipy pillow
```

## Next Steps

1. **Backend Integration:** Update API to serve from `data/aoi_sf_seed/`
2. **Frontend Development:** Use seed dataset for rapid prototyping
3. **Production Scaling:** Extend pipeline to full 75 tiles × 12 months

## Documentation

- **Implementation Report:** `M1B_IMPLEMENTATION_REPORT.md`
- **Scripts README:** `scripts/README.md`
- **Validation Report:** `data/aoi_sf_seed/validation_report.json`

---

**Pipeline Status:** ✅ COMPLETE
**Last Updated:** 2026-03-04
