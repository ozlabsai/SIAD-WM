# Reporting/UI Agent Design Document

**Agent**: Reporting/UI
**Version**: 1.0.0
**Date**: 2026-03-01
**Owner**: Reporting/UI Agent

---

## 1. Overview

The Reporting/UI Agent generates briefing-grade HTML reports for SIAD hotspot detection results. Reports are self-contained, analyst-ready documents featuring AOI overview maps, hotspot rankings with before/after imagery, temporal timelines, and scenario comparison visualizations.

### 1.1 Design Philosophy

**Principle: Briefing-Grade Self-Containment**
- All visualizations embedded as base64-encoded images (no external dependencies)
- Report viewable in any modern browser without internet connection
- Optimized for export to PDF for sharing with non-technical stakeholders
- Maximum file size target: 50 MB (with 512px thumbnail compression)

**Principle: Analyst-Driven Workflow**
- Hotspots ranked by confidence tier (Structural > Activity > Environmental)
- Before/after panels enable rapid visual verification
- Timeline plots show persistence evidence (not just peak scores)
- Scenario comparison enables counterfactual reasoning

---

## 2. Input Contracts

### 2.1 Primary Input: hotspots.json

**File**: `data/outputs/<aoi_id>/hotspots.json`
**Schema**: See CONTRACTS.md Section 5

**Key Fields Used**:
- `hotspot_id`: Report section anchor IDs
- `centroid`: Map marker placement
- `first_detected_month`: Before/after temporal windows
- `persistence_months`: Timeline plot shading
- `confidence_tier`: Sorting and visual styling
- `max_acceleration_score`: Hotspot ranking
- `attribution`: Modality contribution bar charts

### 2.2 Secondary Inputs

**Manifest**: `manifest.jsonl` (for GeoTIFF path lookup)
- Used to locate raw tiles for before/after thumbnail extraction
- Maps `(tile_id, month)` → `gcs_uri` or local file path

**Config**: `configs/<aoi_id>.yaml`
- AOI bounds for overview map extent
- Projection settings (EPSG:3857)
- Tile grid dimensions

**Detection Outputs**: `data/outputs/<aoi_id>/scores_<month>.tif` (optional)
- Per-tile acceleration scores for heatmap overlays
- Used for scenario comparison heatmaps

---

## 3. Report Structure

### 3.1 HTML Template (Jinja2)

**File**: `src/siad/report/template.html`

**Sections**:
1. **Header**: AOI ID, date range, scenario metadata
2. **Executive Summary**: Total hotspots by confidence tier (table)
3. **AOI Overview Map**: Basemap with tile grid + hotspot markers (color-coded by tier)
4. **Hotspot Catalog**: Ranked list with cards (thumbnail + metadata)
5. **Timeline Analysis**: Per-hotspot residual score plots
6. **Scenario Comparison**: Neutral vs Observed heatmap side-by-side
7. **Appendix**: Attribution details, methodology notes

**Template Placeholders**:
```html
<div class="aoi-map">
  <img src="data:image/png;base64,{{ aoi_map_base64 }}" />
</div>

{% for hotspot in hotspots_ranked %}
<div class="hotspot-card" id="{{ hotspot.hotspot_id }}">
  <h3>{{ hotspot.hotspot_id }} ({{ hotspot.confidence_tier }})</h3>
  <div class="before-after">
    <img src="data:image/png;base64,{{ hotspot.thumbnails.s1_before_b64 }}" />
    <img src="data:image/png;base64,{{ hotspot.thumbnails.s1_after_b64 }}" />
  </div>
  <div class="timeline">
    <img src="data:image/png;base64,{{ hotspot.timeline_plot_b64 }}" />
  </div>
</div>
{% endfor %}
```

### 3.2 CSS Styling

**Approach**: Embedded `<style>` block (no external CSS files)

**Design Guidelines**:
- Clean, minimal style (avoid "AI-generated" aesthetic)
- Color scheme: Neutral grays with tier-specific accents
  - Structural: Red (#D32F2F)
  - Activity: Orange (#F57C00)
  - Environmental: Blue (#1976D2)
- Print-friendly layout (A4 page breaks between hotspots)
- Responsive grid for before/after panels (flexbox)

---

## 4. Component Design

### 4.1 AOI Overview Map Generator

**Module**: `src/siad/report/map_generator.py`

**Function**: `generate_aoi_map(aoi_bounds, hotspots, output_size=(1200, 800))`

**Implementation**:
- Use **matplotlib** (not folium) for static basemap generation
- Basemap: Light gray canvas with AOI bounding box rectangle
- Tile grid overlay: Faint grid lines at 2.56 km spacing (256px tiles at 10m)
- Hotspot markers: Scatter plot at centroids, color-coded by confidence_tier
- Legend: Color key for Structural/Activity/Environmental
- Output: PNG bytes → base64 encoding

**Rationale**: matplotlib avoids external API dependencies (Mapbox, OSM tile servers) and produces consistent output for PDF export. No interactive pan/zoom needed for briefing reports.

**Failure Mode**: If AOI bounds are malformed, fallback to world extent with warning annotation.

### 4.2 Hotspot Card Generator

**Module**: `src/siad/report/hotspot_cards.py`

**Function**: `generate_hotspot_card(hotspot, manifest, config)`

**Panel Layout** (6 images per hotspot):
```
┌─────────────┬─────────────┐
│ SAR Before  │ SAR After   │
├─────────────┼─────────────┤
│ Opt Before  │ Opt After   │
├─────────────┼─────────────┤
│ Lights Bef  │ Lights Aft  │
└─────────────┴─────────────┘
```

**Before/After Temporal Windows**:
- Before: `first_detected_month - 6` months (baseline period)
- After: `first_detected_month + persistence_months` (change established)

**Image Extraction Workflow**:
1. Lookup tile_id in manifest to find GeoTIFF paths for target months
2. Load GeoTIFF bands using rasterio
3. Extract tile subset corresponding to hotspot cluster centroid (512x512 px crop)
4. Apply band-specific rendering:
   - **SAR (S1_VV)**: Linear stretch to [0, 255], gray colormap
   - **Optical (S2_B4/B3/B2)**: RGB composite, 2% stretch
   - **Lights (VIIRS_avg_rad)**: Log stretch, yellow-orange colormap
5. Resize to 512x512 px max (preserve aspect ratio)
6. Encode to JPEG (quality=85) → base64

**Fallback**: If before/after month missing (manifest gap), show "N/A" placeholder with gray background + text annotation.

### 4.3 Timeline Plotter

**Module**: `src/siad/report/timeline.py`

**Function**: `generate_timeline_plot(hotspot_id, residuals_timeseries, first_detected_month, persistence_months)`

**Plot Elements**:
- **X-axis**: Time (months as YYYY-MM tick labels)
- **Y-axis**: Residual score (0.0 to max observed score)
- **Line plot**: Residual scores over full time range (36 months)
- **Shaded region**: Persistence window (first_detected to first_detected + persistence_months), semi-transparent red
- **Vertical line**: `first_detected_month` marker (dashed line)
- **Annotations**: Label persistence months count, max score value

**Data Source**: Extract from `data/outputs/<aoi_id>/residuals_timeseries.csv` (generated by Detection agent during scoring)
- Expected format: `tile_id, month, residual_score`
- Aggregate across all tiles in hotspot cluster (median or mean)

**Styling**:
- Figure size: 10" x 4" (wide aspect for embedding)
- Grid: Light gray, minor ticks enabled
- Title: `Hotspot {hotspot_id} - Acceleration Timeline`

**Failure Mode**: If residuals_timeseries.csv missing, generate empty plot with "Data unavailable" annotation.

### 4.4 Scenario Comparison Generator

**Module**: `src/siad/report/scenario_comparison.py`

**Function**: `generate_scenario_comparison(aoi_id, scenarios=['neutral', 'observed'])`

**Layout**: 2-column heatmap grid
```
┌────────────────┬────────────────┐
│ Neutral        │ Observed       │
│ Scenario       │ Scenario       │
│ (rain/temp=0)  │ (actual data)  │
└────────────────┴────────────────┘
```

**Heatmap Generation**:
1. Load acceleration score GeoTIFFs for each scenario:
   - `data/outputs/<aoi_id>/scores_neutral_<month>.tif`
   - `data/outputs/<aoi_id>/scores_observed_<month>.tif`
2. Aggregate scores across time (max or 90th percentile per tile)
3. Render as spatial heatmap (matplotlib `imshow` with colormap)
4. Overlay AOI bounds rectangle
5. Colorbar: Shared scale across both scenarios (0 to max score)

**Month Selection**: Use latest month in detection range (typically last month of rollout)

**Failure Mode**: If scenario outputs missing, show single-scenario heatmap with warning annotation.

---

## 5. Report Builder Orchestration

**Module**: `src/siad/report/report_builder.py`

**Function**: `build_report(hotspots_json_path, manifest_path, config_path, output_html_path)`

**Workflow**:
1. **Load inputs**:
   - Parse `hotspots.json` (validate schema)
   - Load manifest.jsonl into dict `{(tile_id, month): gcs_uri}`
   - Load config YAML for AOI bounds
2. **Rank hotspots**:
   - Sort by `confidence_tier` (Structural first), then by `max_acceleration_score` descending
3. **Generate visualizations**:
   - AOI map (once, all hotspots on single map)
   - For each hotspot:
     - Before/after thumbnails (6 images)
     - Timeline plot
   - Scenario comparison heatmaps (once, for all scenarios)
4. **Render template**:
   - Jinja2 template with all base64-encoded images
   - Embed CSS inline
   - Generate TOC with anchor links to hotspot cards
5. **Write output**:
   - Single HTML file to `output_html_path`
   - Optional: Write companion metadata JSON with file size, hotspot count, generation timestamp

**Performance Optimization**:
- Parallelize thumbnail extraction across hotspots (multiprocessing pool)
- Cache base64 encoding in memory (avoid redundant encoding)
- Skip timeline generation if `--skip-timelines` flag set

**Error Handling**:
- If hotspots.json empty (no detections), generate minimal report with "No hotspots detected" message
- If GeoTIFF tiles missing for >50% of hotspots, log warning but continue with partial thumbnails
- If template rendering fails, dump intermediate data to debug JSON

---

## 6. CLI Interface

**Script**: `scripts/generate_report.py`

**Usage**:
```bash
python scripts/generate_report.py \
  --hotspots data/outputs/quickstart-demo/hotspots.json \
  --manifest data/outputs/quickstart-demo/manifest.jsonl \
  --config configs/quickstart-demo.yaml \
  --output data/outputs/quickstart-demo/report.html \
  --scenarios neutral,observed \
  --skip-timelines  # Optional: omit timeline plots for faster generation
```

**Flags**:
- `--hotspots`: Path to hotspots.json (required)
- `--manifest`: Path to manifest.jsonl (required)
- `--config`: Path to AOI config YAML (required)
- `--output`: Output HTML file path (required)
- `--scenarios`: Comma-separated scenario names (default: `neutral,observed`)
- `--skip-timelines`: Boolean flag (omit timeline generation)
- `--dry-run`: Validate inputs without generating report
- `--verbose`: Print debug logs to stderr

**Exit Codes**:
- 0: Success
- 1: Invalid input files (missing or malformed)
- 2: Template rendering error
- 3: Thumbnail extraction error

---

## 7. Dependencies

**Python Packages**:
- `matplotlib>=3.8` (plotting, basemap generation)
- `rasterio>=1.3` (GeoTIFF I/O)
- `numpy>=1.24` (array operations)
- `Jinja2>=3.1` (HTML template rendering)
- `Pillow>=10.0` (image resizing, JPEG encoding)
- `PyYAML>=6.0` (config loading)

**Optional**:
- `folium>=0.15` (if interactive maps needed post-MVP)
- `plotly>=5.0` (if interactive timelines requested)

---

## 8. Testing Strategy

### 8.1 Smoke Test

**File**: `tests/smoke/test_reporting_smoke.py`

**Test Case**: Generate report for single mock hotspot
- Input: 1 hotspot with synthetic `first_detected_month` and `persistence_months`
- Mock manifest with 2 timesteps (before/after)
- Mock GeoTIFF tiles (random noise arrays)
- Output: Validate HTML file size < 5 MB, contains expected sections

**Runtime**: < 10 seconds

### 8.2 Integration Test

**File**: `tests/integration/test_reporting_integration.py`

**Test Case**: Generate report from real Detection agent output
- Input: `hotspots.json` from Detection agent (T037 output)
- Real manifest from Data agent (T027 output)
- Output: Validate HTML contains N hotspot cards (N from hotspots.json)

**Runtime**: < 30 seconds (depends on hotspot count)

### 8.3 Visual Regression Test (Optional)

**Tool**: pytest-mpl (matplotlib figure comparison)
- Capture reference PNG for AOI map, timeline plot
- Compare pixel-wise differences on each test run
- Threshold: 95% similarity (allow minor rendering variations)

---

## 9. Failure Modes and Mitigations

### 9.1 Large File Size

**Symptom**: HTML file exceeds 100 MB (browser rendering lag)

**Mitigations**:
1. Resize all thumbnails to 512x512 px max (currently implemented)
2. Use JPEG quality=75 instead of 85 (trade-off: slight quality loss)
3. Generate external PNG files for timelines instead of base64 embedding
4. Add `--max-hotspots` flag to limit report to top N hotspots

### 9.2 Missing GeoTIFF Tiles

**Symptom**: Before/after months not in manifest (data collection gaps)

**Mitigations**:
1. Fallback to closest available month within ±3 month window
2. If no data within window, show "N/A" placeholder image
3. Annotate card with "Data gap: showing {actual_month} instead of {target_month}"

### 9.3 Broken Basemap

**Symptom**: matplotlib crashes on basemap rendering (memory error)

**Mitigations**:
1. Reduce map resolution (DPI=72 instead of 150)
2. Simplify tile grid overlay (show only AOI bounds, omit grid lines)
3. Fallback: Generate text-only report without AOI map

### 9.4 Template Rendering Error

**Symptom**: Jinja2 template exception (missing variable, syntax error)

**Mitigations**:
1. Validate all template variables before rendering (assert non-None)
2. Use Jinja2 `{% if var %}` guards for optional fields
3. Catch TemplateError and dump intermediate data to `report_debug.json`

---

## 10. Post-MVP Enhancements

**Optional Web Viewer** (deferred):
- Leaflet map with hotspot GeoJSON overlay (clickable markers)
- Timeline plots as interactive Plotly charts
- Scenario toggle buttons (HTMX or vanilla JS)
- Deploy as static site (no backend needed)

**PDF Export**:
- Use `weasyprint` or `pdfkit` to convert HTML → PDF
- Optimize for A4 print layout (page breaks between hotspots)
- Include TOC bookmarks for navigation

**Analyst Annotations**:
- Editable text fields for hotspot notes (localStorage persistence)
- Export annotations to JSON for sharing with team

---

## 11. Constitution Compliance

**Principle IV (Interpretable Attribution)**:
- Report makes modality attribution visible via thumbnail panels (SAR/optical/lights separated)
- Confidence tier labels (Structural/Activity/Environmental) surface in hotspot cards
- Attribution bar charts show `sar_contribution`, `optical_contribution`, `lights_contribution` percentages

**Principle V (Reproducible Pipelines)**:
- CLI script is deterministic (same inputs → same HTML output)
- All visualization parameters configurable via flags (no hardcoded paths)
- Logs to stderr (generation progress, warnings)
- Outputs to stdout (HTML file path on success)

---

## 12. Open Questions

1. **Basemap choice**: matplotlib (static) vs folium (interactive)?
   - **Decision**: matplotlib for MVP (briefing PDF export priority)
   - **Rationale**: Interactive maps deferred until web viewer requested

2. **Timeline data source**: Extract from Detection agent output or recompute?
   - **Decision**: Detection agent generates `residuals_timeseries.csv` as output (T047)
   - **Rationale**: Avoid duplicating residual computation logic

3. **Scenario comparison**: Show all scenarios or user-selected subset?
   - **Decision**: CLI `--scenarios` flag controls which scenarios included
   - **Default**: neutral,observed (most common comparison)

---

**Status**: Design complete - ready for code skeleton implementation

**Next Steps**:
1. Create directory structure: `src/siad/report/`
2. Implement Jinja2 template with placeholders
3. Build map_generator.py (matplotlib basemap)
4. Build hotspot_cards.py (thumbnail extraction)
5. Build timeline.py (residual plot)
6. Build report_builder.py (orchestration)
7. Build scripts/generate_report.py (CLI wrapper)
8. Smoke test with 1 mock hotspot
