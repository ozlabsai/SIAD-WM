# SIAD Report Generation Module

Generates briefing-grade HTML reports from hotspot detection outputs.

## Quick Start

```python
from siad.report import build_report

build_report(
    hotspots_json_path="data/outputs/quickstart-demo/hotspots.json",
    manifest_path="data/outputs/quickstart-demo/manifest.jsonl",
    config_path="configs/quickstart-demo.yaml",
    output_html_path="data/outputs/quickstart-demo/report.html",
    scenarios=["neutral", "observed"],
    residuals_csv_path="data/outputs/quickstart-demo/residuals_timeseries.csv"
)
```

Or via CLI:

```bash
python scripts/generate_report.py \
    --hotspots data/outputs/quickstart-demo/hotspots.json \
    --manifest data/outputs/quickstart-demo/manifest.jsonl \
    --config configs/quickstart-demo.yaml \
    --output data/outputs/quickstart-demo/report.html \
    --scenarios neutral,observed
```

## Module Structure

```
report/
├── __init__.py                  # Module exports
├── template.html                # Jinja2 HTML template
├── map_generator.py             # AOI overview map with hotspot markers
├── hotspot_cards.py             # Before/after thumbnail extraction
├── timeline.py                  # Temporal residual score plots
├── scenario_comparison.py       # Counterfactual heatmap comparisons
└── report_builder.py            # Orchestration logic
```

## Component Responsibilities

### map_generator.py

Generates static matplotlib basemap showing:
- AOI bounding box
- Tile grid overlay (2.56 km spacing)
- Hotspot markers (color-coded by confidence tier)
- Legend with tier counts

**Key Function**: `generate_aoi_map(aoi_bounds, hotspots) → base64_png`

### hotspot_cards.py

Extracts before/after thumbnails from GeoTIFF tiles:
- SAR (Sentinel-1 VV band, grayscale)
- Optical (Sentinel-2 RGB composite)
- Nighttime Lights (VIIRS, yellow-orange colormap)

**Temporal Windows**:
- Before: `first_detected_month - 6 months`
- After: `first_detected_month + persistence_months`

**Key Function**: `generate_hotspot_thumbnails(hotspot, manifest) → dict[str, base64_jpeg]`

### timeline.py

Generates residual score timeline plots showing:
- Line plot of residual scores over time
- Shaded persistence window
- Vertical marker at first_detected_month

**Key Function**: `generate_timeline_plot(hotspot_id, residuals_timeseries, ...) → base64_png`

### scenario_comparison.py

Generates side-by-side heatmaps comparing:
- Neutral scenario (rain/temp anomalies = 0)
- Observed scenario (actual weather conditions)
- Custom scenarios (if provided)

**Key Function**: `generate_scenario_comparison(aoi_id, scenarios, ...) → list[dict]`

### report_builder.py

Orchestrates all components:
1. Load inputs (hotspots.json, manifest, config)
2. Rank hotspots by confidence tier and score
3. Generate visualizations (map, thumbnails, timelines, scenarios)
4. Render Jinja2 template with base64-encoded images
5. Write self-contained HTML file

**Key Function**: `build_report(hotspots_json_path, manifest_path, config_path, output_html_path, ...)`

## Report Structure

The generated HTML contains:

1. **Header**: AOI ID, time range, generation timestamp
2. **Executive Summary**: Hotspot counts by confidence tier
3. **AOI Overview Map**: Basemap with all hotspots marked
4. **Hotspot Catalog**: Ranked cards with:
   - Metadata (location, first detected, persistence, score)
   - Before/after panels (SAR, optical, lights)
   - Timeline plot (residual scores over time)
   - Attribution breakdown (modality contributions)
5. **Scenario Comparison**: Heatmap grid (neutral vs observed)
6. **Appendix**: Methodology notes

## Confidence Tier Color Scheme

- **Structural** (Red #D32F2F): SAR + lights changes (construction-like)
- **Activity** (Orange #F57C00): Lights changes, minimal SAR (operational activity)
- **Environmental** (Blue #1976D2): Optical-dominated (vegetation/water)

## Design Principles

### Self-Containment

All visualizations embedded as base64-encoded images:
- No external dependencies (works offline)
- No API calls (Mapbox, OSM)
- Single HTML file (easy to share)

### Briefing-Grade

Optimized for analyst workflow:
- Clean, minimal design (no "AI-generated" aesthetic)
- Print-friendly layout (A4 page breaks)
- PDF export ready (via browser print or weasyprint)

### Performance

Target file size: <50 MB
- Thumbnails resized to 512px max
- JPEG compression (quality=85)
- Optional `--skip-timelines` for faster generation

## Testing

### Smoke Test

```bash
python tests/smoke/test_reporting_smoke.py
```

Validates:
- HTML file created
- File size reasonable (<10 MB for 1 hotspot)
- Required sections present

### Integration Test (Post-MVP)

Requires real Detection agent outputs:
- hotspots.json with multiple hotspots
- manifest.jsonl with full tile coverage
- residuals_timeseries.csv for timeline plots

## Dependencies

**Required**:
- `matplotlib>=3.8` (plotting, basemap)
- `Jinja2>=3.1` (template rendering)
- `Pillow>=10.0` (image resizing, JPEG encoding)
- `PyYAML>=6.0` (config loading)
- `python-dateutil>=2.8` (date arithmetic)
- `scipy>=1.11` (Gaussian filter for scenario heatmaps)

**Optional** (full implementation):
- `rasterio>=1.3` (GeoTIFF I/O)
- `pandas>=2.0` (CSV parsing)

## Development Notes

### Current Status (v1.0.0 Skeleton)

**Implemented**:
- Complete HTML template with embedded CSS
- All visualization generators (map, cards, timeline, scenarios)
- Full orchestration pipeline
- CLI script with argument parsing
- Smoke test with mock data

**Deferred to Full Implementation**:
- GeoTIFF tile extraction (currently returns mock noise)
- Band-specific rendering (SAR grayscale, RGB composite, lights colormap)
- CSV parsing for residuals (currently returns mock timeline)

### Next Steps (Tasks T038-T040)

1. Integrate rasterio for GeoTIFF loading
2. Implement band-specific rendering:
   - SAR: Linear stretch to [0, 255], gray colormap
   - Optical: RGB composite (B4/B3/B2), 2% stretch
   - Lights: Log stretch, yellow-orange colormap
3. Parse residuals_timeseries.csv (pandas or csv module)
4. Integration test with real Detection outputs

## Failure Modes

See `docs/reporting-design.md` Section 9 for detailed mitigation strategies:
- Large file size (>100 MB)
- Missing GeoTIFF tiles (data gaps)
- Basemap rendering errors
- Template rendering exceptions

## Constitution Compliance

**Principle IV (Interpretable Attribution)**:
- Modality attribution visible in hotspot cards
- Confidence tier labels surface detection logic
- Before/after panels enable visual verification

**Principle V (Reproducible Pipelines)**:
- Deterministic CLI (same inputs → same output)
- All parameters configurable via flags
- Logs to stderr, output path to stdout
- Exit codes distinguish error types

---

**Maintainer**: Reporting/UI Agent
**Last Updated**: 2026-03-01
**Version**: 1.0.0
