# SIAD Command Center - 2-Minute Demo Script

**Total Time: 2 minutes**

This script walks through a complete demonstration of the SIAD Command Center, showcasing its core capabilities for detecting and analyzing satellite-based infrastructure anomalies.

---

## Setup (Before Demo)

1. **Backend**: Ensure API is running at `http://localhost:8001`
   ```bash
   cd api && uv run uvicorn api.main:app --reload --port 8001
   ```

2. **Frontend**: Ensure frontend is running at `http://localhost:3000`
   ```bash
   cd frontend && npm run dev
   ```

3. **Browser**: Open `http://localhost:3000` in Chrome/Firefox
4. **Window**: Maximize browser window for best viewing experience

---

## Demo Flow

### Part 1: Introduction & Overview (0:00 - 0:20)

**What to say:**
> "This is the SIAD Command Center - a Satellite Intelligence Anomaly Detection system designed to identify infrastructure changes from space. It analyzes multi-modal satellite data (SAR, optical, thermal) using a world model to detect anomalies that indicate construction, urban development, or infrastructure changes."

**What to show:**
- Point to the main interface: Map on left, detection rail on right
- Highlight the header showing AOI name and hotspot count
- Note the professional Lattice-style dark UI design

**Key metrics visible:**
- 9 hotspots detected
- 2 tiles analyzed
- 6 months of data (Month 1-6)

---

### Part 2: Hotspot Detection Overview (0:20 - 0:45)

**What to say:**
> "The detection rail shows our top hotspots, ranked by anomaly score. Each hotspot represents a significant deviation from the model's predictions, indicating potential real-world change."

**What to show:**
1. **Scroll through detection rail**
   - Point out hotspot cards showing:
     - Tile IDs (tile 1, tile 2)
     - Anomaly scores (ranging from 0.946 down to 0.311)
     - Change types (urban_construction, infrastructure)
     - Severity badges (Critical, High, Elevated)

2. **Highlight top hotspot**
   - **Tile 1, Month 3**
   - **Score: 0.946** (highest anomaly)
   - **Type: Urban Construction**
   - **Severity: Critical**

---

### Part 3: Deep Dive - Tile Analysis (0:45 - 1:30)

**What to say:**
> "Let's investigate our highest-scoring hotspot. Click on the top card to see detailed analytics."

**What to show:**

1. **Click top hotspot card** (Tile 1, Month 3, Score: 0.946)

2. **Modal opens showing:**

   a. **Timeline Chart (10 seconds)**
   - Shows anomaly scores across all months (1-6)
   - Point out the spike in Month 3 (onset detection)
   - "The model detected a significant structural change starting in Month 3, with sustained elevated scores indicating persistent development."

   b. **Satellite Imagery Comparison (15 seconds)**
   - Show side-by-side comparison:
     - **Actual imagery**: What satellites captured
     - **Predicted imagery**: What the model expected
     - **Residual heatmap**: Highlighting differences
   - "The residual heatmap shows concentrated red regions - these are areas where actual observations deviated most from model predictions, indicating construction or infrastructure development."

   c. **Modality Attribution (10 seconds)**
   - Show which sensor detected the anomaly:
     - SAR (Synthetic Aperture Radar): Structural changes
     - Optical: Visual changes
     - Thermal: Heat signature changes
   - "SAR data was particularly informative here, detecting structural changes that optical sensors might miss due to cloud cover."

   d. **Metadata Summary (5 seconds)**
   - Location: 49.18°N, -130.95°W
   - Change Type: Urban Construction
   - Region: Temperate
   - Onset: Month 4

3. **Close modal**

---

### Part 4: Filtering & Search (1:30 - 1:50)

**What to say:**
> "The system includes powerful filtering to focus on specific anomalies."

**What to show:**

1. **Adjust Score Threshold** (10 seconds)
   - Move minimum score slider from 0.5 to 0.8
   - Hotspot count drops (only high-confidence detections remain)
   - "By raising the threshold, we filter out lower-confidence detections to focus on the most significant changes."

2. **Search by Tile ID** (10 seconds)
   - Type "tile 2" in search box
   - Only Tile 2 hotspots remain
   - Show infrastructure change type
   - "We can quickly locate specific tiles of interest."

3. **Export Data** (optional, if time permits)
   - Click "GeoJSON" or "CSV" export button
   - "All filtered results can be exported for further analysis in GIS tools or spreadsheets."

---

### Part 5: Timeline Playback (1:50 - 2:00)

**What to say:**
> "Finally, let's watch how these anomalies evolved over time."

**What to show:**

1. **Clear filters** (reset to show all hotspots)

2. **Click Play button** on timeline player
   - Timeline advances month by month
   - Map updates to show hotspots for current month
   - Watch progression from Month 1 → Month 6

3. **Point out:**
   - "Notice how hotspots appear and intensify over time"
   - "Month 3 shows the highest concentration of anomalies"
   - "This temporal analysis helps identify when changes began"

4. **Pause at Month 3** (peak activity)
   - "Month 3 marks the onset of major urban construction activity"

---

## Closing (2:00)

**What to say:**
> "The SIAD Command Center provides real-time detection, multi-modal analysis, and temporal tracking of infrastructure changes from space - turning satellite data into actionable intelligence."

**Key Takeaways:**
1. ✅ **Automated Detection**: ML-powered anomaly detection from satellite data
2. ✅ **Multi-Modal Analysis**: Combines SAR, optical, and thermal sensors
3. ✅ **Temporal Tracking**: Monitors changes over time with onset detection
4. ✅ **Professional Interface**: Lattice-style UI designed for operations centers
5. ✅ **Actionable Intelligence**: Exportable data for downstream analysis

---

## Backup: Interesting Data Points to Highlight

If extra time or questions:

### High-Score Anomalies
- **Tile 1, Month 3, Region 16**: Score 0.946 (Critical severity)
- **Tile 1, Month 3, Region 10**: Score 0.943 (Critical severity)
- **Tile 1, Month 4, Region 6**: Score 0.825 (Critical severity)
- **Tile 2, Month 3, Region 17**: Score 0.807 (Infrastructure change)

### Change Type Distribution
- **Urban Construction**: Tile 1 (5 detections across 5 months)
- **Infrastructure**: Tile 2 (4 detections across 3 months)

### Regional Insights
- **Temperate Zone (Tile 1)**: Sustained urban development, onset Month 4
- **Polar Zone (Tile 2)**: Infrastructure expansion, onset Month 6

### Performance Metrics (if asked)
- **Detection Threshold**: 0.5 default (adjustable)
- **Spatial Resolution**: 128x128 pixel tiles
- **Temporal Resolution**: Monthly updates
- **Coverage**: 2 tiles, 6 months (demo dataset)
- **API Response Time**: <100ms for hotspot queries

---

## Troubleshooting During Demo

### If backend is not responding:
```bash
# Check backend health
curl http://localhost:8001/health

# Restart backend if needed
cd api && uv run uvicorn api.main:app --reload --port 8001
```

### If frontend is not loading:
```bash
# Check frontend is running
curl http://localhost:3000

# Restart frontend if needed
cd frontend && npm run dev
```

### If data is not showing:
```bash
# Verify data files exist
ls data/aoi_sf_seed/
# Should see: hotspots_ranked.json, metadata.json, tiles/

# Verify HDF5 file exists
ls data/residuals_test.h5
```

### If map is not rendering:
- Check browser console for Mapbox token errors
- Verify `.env.local` has `NEXT_PUBLIC_MAPBOX_TOKEN`
- Map will show but may not have basemap without token (hotspots still visible)

---

## Post-Demo Resources

**Documentation:**
- `README.md` - Setup and installation guide
- `ARCHITECTURE.md` - System design and data flow
- `TROUBLESHOOTING.md` - Common issues and solutions

**Code:**
- `api/` - FastAPI backend
- `frontend/` - Next.js frontend
- `scripts/` - Data generation and validation tools

**Tests:**
- `frontend/tests/e2e/` - Playwright E2E tests
- `tests/` - Backend integration and performance tests

---

**Demo Script Version:** 1.0
**Last Updated:** 2025-03-04
**Duration:** 2:00 minutes
**Presenter:** [Your Name]
