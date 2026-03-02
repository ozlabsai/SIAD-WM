# Research: SIAD MVP - Infrastructure Acceleration Detection

**Feature**: 001-siad-mvp
**Date**: 2026-02-28
**Purpose**: Resolve NEEDS CLARIFICATION items from Technical Context

## Research Questions

From Technical Context, we need to resolve:

1. Earth Engine Python client library for satellite data collection
2. Deep learning framework for world model (PyTorch vs JAX)
3. Geospatial processing library for reprojection/tiling (rasterio vs xarray)
4. Visualization library for heatmaps/timelines (matplotlib vs plotly)

## Research Findings

### 1. Earth Engine Python Client Library

**Decision**: `earthengine-api` (official Google Earth Engine Python API)

**Rationale**:
- Official API maintained by Google with consistent updates
- Direct access to Earth Engine catalog (Sentinel-1, Sentinel-2, VIIRS, CHIRPS, ERA5)
- Built-in support for temporal compositing (median, cloud masking) and reprojection
- Well-documented batch export to GeoTIFF/TFRecord for offline processing
- Authentication via service accounts enables automated pipeline execution
- Supports server-side processing to avoid downloading raw imagery before compositing

**Alternatives Considered**:
- **geemap**: Higher-level wrapper around earthengine-api with interactive visualization; rejected because we need CLI-driven batch processing, not Jupyter notebooks
- **eemont**: Extended earthengine-api with convenience methods; rejected as unnecessary abstraction layer for MVP (violates KISS principle)

**Implementation Notes**:
- Use `ee.ImageCollection().median()` for monthly composites
- Use `ee.Image.reproject()` to enforce EPSG:3857 at 10m
- Export via `ee.batch.Export.image.toDrive()` or `toCloudStorage()` for GeoTIFF tiles
- Cloud masking for Sentinel-2: `ee.Algorithms.Sentinel2.CDI()` or simple `QA60` band thresholding

---

### 2. Deep Learning Framework

**Decision**: **PyTorch 2.x** with `torch.compile()` for dynamics model

**Rationale**:
- PyTorch dominates geospatial ML research (easier to find pretrained SAR/optical encoders if needed)
- Dynamic computation graph simplifies recursive rollout implementation (vs JAX's static compilation)
- EMA (Exponential Moving Average) for target encoder well-supported via `torch.optim.swa_utils.AveragedModel`
- `torch.nn.DataParallel` sufficient for single-GPU MVP (A100); multi-GPU not needed per spec assumptions
- `torch.compile()` in PyTorch 2.x provides JAX-like speedups without full rewrite
- Stronger ecosystem for geospatial data loaders (torchgeo library exists)

**Alternatives Considered**:
- **JAX + Flax**: Faster compilation and cleaner functional API, but steeper learning curve and less geospatial tooling; better for production scale-out (not MVP priority)
- **TensorFlow/Keras**: Legacy framework; PyTorch has overtaken in research; harder to implement custom rollout loops

**Implementation Notes**:
- Use `torchvision.models` ConvNet backbones (ResNet-18/50) as observation encoder baseline
- Implement transformer dynamics as `nn.TransformerEncoderLayer` (1-2 layers max per KISS)
- Use `torch.utils.data.Dataset` with memory-mapped HDF5 files for 14,400 tile-months (via `h5py` + caching)
- Training loop: standard PyTorch with `torch.optim.AdamW` and cosine LR schedule
- Checkpoint via `torch.save()` for reproducibility (constitution Principle V)

---

### 3. Geospatial Processing Library

**Decision**: **rasterio** for I/O + **numpy** for array operations (defer xarray unless needed)

**Rationale**:
- rasterio is industry-standard for GeoTIFF I/O with GDAL backend (handles EPSG transformations natively)
- Lightweight: read → numpy array → process → write pattern matches CLI pipeline philosophy
- Explicit control over windowing/tiling (`rasterio.windows`) avoids hidden complexity
- Direct integration with Earth Engine exports (GeoTIFF format)
- xarray adds lazy-loading and labeled dimensions but increases abstraction (YAGNI for MVP)

**Alternatives Considered**:
- **xarray + rioxarray**: Better for multi-dimensional labeled arrays (time × lat × lon), but adds dependency complexity and memory overhead; defer until global multi-AOI scaling (out of MVP scope)
- **GDAL Python bindings**: Lower-level than rasterio; harder to use correctly (more boilerplate)

**Implementation Notes**:
- Read with `rasterio.open(geotiff).read()` → numpy array
- Write with `rasterio.open(out_path, 'w', **profile)` using source profile for consistency
- Tiling: use `rasterio.windows.Window` to extract 256×256 pixel tiles
- Reprojection: `rasterio.warp.reproject(src, dst, src_crs=..., dst_crs='EPSG:3857', resampling=Resampling.bilinear)`
- Valid pixel fraction: compute per-tile as `np.sum(~np.isnan(tile)) / tile.size`

---

### 4. Visualization Library

**Decision**: **matplotlib** for static outputs + **GeoJSON** for interactive web overlays (optional P3 enhancement)

**Rationale**:
- matplotlib sufficient for heatmaps (`plt.imshow` + colorbar), timelines (`plt.plot`), and divergence plots
- Saves to PNG/PDF for reports (matches "single analysis session" success criterion SC-001)
- Low dependency footprint (already installed with numpy/scipy ecosystem)
- Plotly interactive dashboards are out of MVP scope (no web service requirement per spec assumptions)
- GeoJSON export enables optional Leaflet/Mapbox overlays for P3 timeline visualization without committing to full web stack

**Alternatives Considered**:
- **Plotly/Dash**: Interactive web dashboards; rejected because spec has no web UI requirement and adds Flask/React complexity
- **Holoviews/Bokeh**: Similar to Plotly but Python-native; still overkill for static PNG outputs
- **Seaborn**: Thin wrapper over matplotlib; unnecessary abstraction for domain-specific plots

**Implementation Notes**:
- Heatmaps: `plt.imshow(acceleration_scores, cmap='hot', extent=aoi_bbox)` + `plt.colorbar()` with percentile labels
- Timelines: `plt.plot(months, residuals)` + `plt.axvspan(start_month, end_month)` for persistence window
- Counterfactual comparison: `plt.subplot(1,3,n)` grid showing neutral/observed/extreme scenarios side-by-side
- Save via `plt.savefig(out_path, dpi=300, bbox_inches='tight')`
- Optional GeoJSON: export hotspot polygons with `geojson.dump({'type': 'Feature', 'geometry': {...}, 'properties': {'score': ...}})` for Leaflet integration

---

## Summary of Decisions

| Component | Choice | Key Rationale |
|-----------|--------|---------------|
| Earth Engine Client | `earthengine-api` | Official API, server-side compositing, batch export |
| DL Framework | PyTorch 2.x | Geospatial ecosystem, dynamic graphs, EMA support, `torch.compile()` |
| Geospatial Lib | rasterio + numpy | Industry-standard GeoTIFF I/O, explicit control, KISS compliance |
| Visualization | matplotlib + optional GeoJSON | Static outputs sufficient for MVP, low dependency footprint |

**Impact on Technical Context**:
- Primary Dependencies: `earthengine-api`, `pytorch>=2.0`, `rasterio`, `numpy`, `matplotlib`, `h5py` (dataset storage), `pytest`
- Storage: GeoTIFF (raw downloads), HDF5 (preprocessed tensors), PNG/PDF (visualizations), GeoJSON (optional)
- Performance validated: PyTorch 2.x + A100 should handle 14,400 tile-months comfortably within 24-hour session

**Remaining NEEDS CLARIFICATION**: None - all technical choices resolved

**Next Steps**: Proceed to Phase 1 (data-model.md, contracts/, quickstart.md)
