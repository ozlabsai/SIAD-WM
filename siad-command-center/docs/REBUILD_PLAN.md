# SIAD Command Center - Complete Rebuild Plan
## Anduril Lattice-Style Interface

**Date**: 2026-03-04
**Status**: Master Plan - Awaiting Approval
**Lead**: Planning Agent
**Context**: Rebuilding demo with professional Lattice-style UI, no pixel decoder

---

## Visual Story (8 Bullets - What User Sees)

1. **Map-First Interface**: Dark HUD with San Francisco Bay Area base map, hotspots displayed as polygons with red/yellow/green intensity overlays showing unexpected change magnitude.

2. **Right Rail Sidebar**: Ranked list of top 10 hotspots sorted by AccelerationScore, showing tile name, score, persistence duration, onset date, and dominant modality (SAR/Optical/VIIRS) with visual indicators.

3. **Hotspot Selection**: Click any hotspot on map or in list to load detailed panel at bottom; map zooms to location and highlights selected polygon.

4. **Three-Panel Comparison**: Bottom panel shows side-by-side: (Left) "Expected Evolution" from world model prediction, (Center) "Observed Reality" from actual imagery, (Right) "Unexpected Change" residual heatmap with 16x16 token grid overlay.

5. **Timeline Scrubber**: Bottom timeline shows 36-month span with residual score line chart and vertical markers for onset/peak; scrub to any month to update all three panels to that timestamp.

6. **Baseline Toggle**: Switch between "World Model", "Persistence Baseline", "Seasonal Baseline" detection modes to compare reduction in agricultural/seasonal noise.

7. **Environmental Normalization View**: Toggle showing "Observed Conditions" vs "Neutral Environment" (rain_anom=0) rollout to visualize environmental vs human-caused change attribution.

8. **Modality Attribution**: Pie chart or bar graph showing signal contribution breakdown (e.g., SAR 64%, Optical 23%, VIIRS 13%) with tooltip explaining what changed in each modality.

---

## Task Board

### M1: Data Contracts + Backend Skeleton (Priority 1)
**Owner**: Backend Agent
**Duration**: 2 days
**Dependencies**: None

- [ ] Define API contract schema (TypeScript types + FastAPI Pydantic models)
  - `TileMetadata`: tile_id, region, lat, lon, bounds
  - `TileScores`: tile_id, timestamps[], scores[], onset_month, persistence
  - `ResidualHeatmap`: tile_id, month_idx, values[16][16], timestamp
  - `BaselineComparison`: tile_id, world_model[], persistence[], seasonal[]
  - `HotspotSummary`: tile_id, score, persistence, onset, modality_breakdown, region
  - `ModalityAttribution`: sar_pct, optical_pct, viirs_pct, dominant_signal

- [ ] Create FastAPI skeleton structure
  - `/api/detect/hotspots` (GET) - returns ranked list of top N hotspots
  - `/api/detect/tile/{tile_id}` (GET) - returns full tile detail
  - `/api/detect/tile/{tile_id}/heatmap?month={idx}` (GET) - returns 16x16 residual map
  - `/api/detect/tile/{tile_id}/baseline` (GET) - returns baseline comparison
  - `/api/detect/tile/{tile_id}/attribution` (GET) - returns modality breakdown

- [ ] Implement HDF5 storage service abstraction
  - `ResidualStorageService` class wrapping `residuals_test.h5`
  - Methods: `list_tiles()`, `get_tile_metadata()`, `get_tile_scores()`, `get_residual_heatmap()`, `get_baseline_comparison()`, `get_hotspots()`

- [ ] Add CORS middleware for local frontend development

- [ ] Create smoke test script to validate all endpoints return valid JSON

**Acceptance Criteria**:
- All 5 endpoints return valid JSON responses
- HDF5 file loads successfully without errors
- CORS headers allow localhost:3000 requests
- Smoke test passes with 200 status codes

---

### M2: Precompute Pipeline (Priority 1 - Parallel with M1)
**Owner**: Data Agent
**Duration**: 3 days
**Dependencies**: None (works on existing `residuals_test.h5`)

- [ ] Validate existing HDF5 structure
  - Verify tile groups have attributes: region, lat, lon, onset_month
  - Verify datasets: timestamps, scores, residual_maps[T,16,16], baseline_persistence, baseline_seasonal

- [ ] Compute hotspot ranking
  - For each tile, compute AccelerationScore = Persistence × MeanResidual
  - Persistence = count of months where score > threshold
  - MeanResidual = mean of top 10% token residuals
  - Store in `/hotspots` group with sorted list

- [ ] Generate modality attribution data
  - Compute per-modality residuals (SAR, Optical, VIIRS channels)
  - Store percentage breakdown in tile attributes: sar_pct, optical_pct, viirs_pct

- [ ] Create neutral scenario rollouts
  - For each tile, compute rollout with actions=[rain_anom=0, temp_anom=0]
  - Store neutral residuals in `/neutral_residuals` dataset
  - Compute difference: observed_residuals - neutral_residuals

- [ ] Add environmental context metadata
  - Rain anomaly values per month
  - Temperature anomaly values per month (if available)
  - Store in tile-level dataset `/actions[T,2]`

- [ ] Generate summary statistics
  - Total tiles, avg onset month, persistence distribution
  - Change type distribution (if labels exist)
  - Store in root-level attributes

**Acceptance Criteria**:
- HDF5 file contains all required datasets
- Hotspots ranked correctly by AccelerationScore
- Modality attribution sums to 100% per tile
- Neutral scenario data exists for all tiles
- Storage Service can read all new datasets

---

### M3: Lattice-Style UI Foundation (Priority 2)
**Owner**: Frontend Agent
**Duration**: 4 days
**Dependencies**: M1 (API contracts)

- [ ] Initialize Next.js 14+ project with TypeScript
  - App router structure
  - Tailwind CSS with dark theme base
  - Shadcn/ui component library

- [ ] Implement Anduril Lattice design system
  - Color palette: dark grays (#0A0A0A, #1A1A1A, #2A2A2A), accent blue (#0EA5E9), warning yellow (#F59E0B), alert red (#EF4444)
  - Typography: Mono for metrics, Sans for labels
  - Grid system: 24px base unit
  - Borders: 1px cyan accent lines, subtle glows

- [ ] Create page layout structure
  - Top bar: SIAD logo, AOI selector (fixed to "SF Bay Area"), date range display
  - Left panel: Map container (70% width)
  - Right rail: Hotspot list sidebar (30% width, fixed position)
  - Bottom panel: Detail view (slides up, 40% height when open)

- [ ] Set up data fetching architecture
  - React Query for API calls
  - Auto-refresh every 30s for hotspot list
  - Error boundaries with Lattice-style error cards
  - Loading skeletons matching component structure

- [ ] Implement responsive breakpoints
  - Desktop: full 3-panel layout
  - Tablet: stacked map + collapsible sidebar
  - Mobile: single column, tabs for map/list/detail

**Acceptance Criteria**:
- Page loads with Lattice-style dark theme
- Layout matches 3-panel structure (map + rail + bottom)
- All components use design system tokens
- No console errors or hydration mismatches

---

### M4: Map + Hotspot List (Priority 2)
**Owner**: Frontend Agent
**Duration**: 3 days
**Dependencies**: M3 (UI foundation), M2 (hotspot data)

- [ ] Integrate Mapbox GL JS
  - Dark basemap style (Anduril-compatible theme)
  - Set bounds to SF Bay Area (37.2°N - 38.0°N, -122.6°W - -121.8°W)
  - Add zoom controls, scale bar

- [ ] Render hotspot polygons on map
  - Fetch `/api/detect/hotspots` on mount
  - Draw GeoJSON polygon layer with residual score color mapping:
    - Green (score < 0.5): expected evolution
    - Yellow (0.5-0.7): moderate deviation
    - Red (> 0.7): significant unexpected change
  - Add hover tooltips showing tile_id, score, onset

- [ ] Implement right rail hotspot list
  - Fetch same hotspot data
  - Card component per hotspot:
    - Header: Tile region name + AccelerationScore badge
    - Body: Onset date, Persistence (X months), Dominant modality icon
    - Footer: View detail button
  - Sort by score descending (pre-sorted by API)
  - Highlight selected hotspot in list

- [ ] Sync map + list selection
  - Click hotspot polygon → highlight in list + open detail panel
  - Click list item → zoom map to tile + highlight polygon
  - Active state styling: cyan border glow

- [ ] Add map interaction controls
  - Pan/zoom with mouse
  - Keyboard shortcuts (arrow keys for pan, +/- for zoom)
  - Reset view button to return to full AOI

**Acceptance Criteria**:
- All hotspots visible on map with correct color coding
- Right rail shows ranked list matching map data
- Click interactions sync map <-> list selection
- Hover tooltips display correct metadata
- No performance lag with 10-20 hotspots rendered

---

### M5: Detail Panel - Three-Panel Comparison (Priority 3)
**Owner**: Frontend Agent
**Duration**: 3 days
**Dependencies**: M4 (map selection working)

- [ ] Create bottom detail panel container
  - Slides up from bottom (animated transition)
  - Close button (X) in top-right corner
  - Header: Selected tile region + score + onset date
  - Body: Three-column grid layout (33% each)

- [ ] Implement three-panel imagery display
  - Left panel: "Expected Evolution"
    - Label + info icon tooltip explaining JEPA prediction
    - Image placeholder for predicted latent visualization (TBD - see note below)
    - Month indicator overlay
  - Center panel: "Observed Reality"
    - Label + month indicator
    - Fetch actual satellite imagery for selected month
    - Display RGB composite or false-color (B4/B3/B2)
  - Right panel: "Unexpected Change"
    - Label showing residual score for month
    - Fetch `/api/detect/tile/{tile_id}/heatmap?month={idx}`
    - Render 16x16 heatmap as colored grid overlay
    - Color scale: blue (low) → yellow → red (high)

- [ ] Add 16x16 token grid overlay toggle
  - Checkbox: "Show token boundaries"
  - When enabled, overlay 16x16 grid lines on all three panels
  - Grid lines: 1px dashed cyan, 50% opacity

- [ ] Handle imagery loading states
  - Skeleton loader for each panel
  - Error state: "Imagery unavailable for this month"
  - Retry button if fetch fails

**Acceptance Criteria**:
- Detail panel opens/closes smoothly
- Three panels display side-by-side with correct labels
- Heatmap renders with appropriate color scale
- Grid overlay toggles on/off correctly
- All panels sync to same selected month

**Note**: "Expected Evolution" visualization requires latent-to-RGB mapping. Options:
1. Use PCA projection to 3D RGB space (compute offline in M2)
2. Display mean pixel values from neutral rollout
3. Use simple smoothed version of actual imagery as placeholder
**Decision needed before M5 starts** → Recommend option 3 for demo simplicity

---

### M6: Timeline Scrubber (Priority 3)
**Owner**: Frontend Agent
**Duration**: 2 days
**Dependencies**: M5 (detail panel exists)

- [ ] Create timeline component at bottom of detail panel
  - Full-width chart container (padding 16px)
  - X-axis: Month labels (36 months shown, scrollable if needed)
  - Y-axis: Residual score (0.0 - 1.0)

- [ ] Render residual score line chart
  - Fetch `/api/detect/tile/{tile_id}` to get scores[] array
  - Line chart with gradient fill under curve
  - Color: cyan glow effect (#0EA5E9)
  - Data points as small circles on line

- [ ] Add onset/peak markers
  - Vertical dashed line at onset_month
  - Label: "Onset" above line
  - Red dot marker at peak score month

- [ ] Implement scrubber interaction
  - Draggable playhead (vertical line indicator)
  - Click anywhere on timeline to jump to month
  - Keyboard: left/right arrows to step through months
  - Auto-update all three panels when month changes

- [ ] Display environmental context (optional)
  - Secondary Y-axis for rain_anomaly
  - Faint overlay bars showing rain/temp anomalies
  - Toggle: "Show environmental data"

**Acceptance Criteria**:
- Timeline displays full score history
- Onset and peak markers visible and correctly positioned
- Scrubbing updates all three imagery panels in sync
- Smooth animation when changing months
- No lag when scrubbing quickly

---

### M7: Baseline Comparison Widget (Priority 3)
**Owner**: Frontend Agent
**Duration**: 2 days
**Dependencies**: M5 (detail panel), M2 (baseline data)

- [ ] Add baseline toggle control to detail panel header
  - Radio button group: "World Model" | "Persistence" | "Seasonal"
  - Styled as Lattice-style segmented control
  - Default: World Model selected

- [ ] Fetch baseline comparison data
  - Call `/api/detect/tile/{tile_id}/baseline`
  - Returns: {world_model: float[], persistence: float[], seasonal: float[]}
  - Store in component state

- [ ] Update timeline chart to show baseline
  - Add secondary line for selected baseline
  - Color: gray (#6B7280) for baseline, cyan for world model
  - Legend: "World Model" vs "{Baseline Name}"

- [ ] Update heatmap display for baseline mode
  - When "Persistence" or "Seasonal" selected:
    - Fetch corresponding residual data from API
    - Replace heatmap in right panel
  - Label updates: "World Model Residuals" vs "Persistence Residuals"

- [ ] Add comparison summary card
  - Display above timeline
  - Metrics: "False Positives Reduced: X%", "Mean Score Difference: ±X"
  - Computed from difference between world_model and baseline arrays
  - Green badge if world model performs better

**Acceptance Criteria**:
- Toggle switches between three baseline modes
- Timeline chart shows both lines correctly
- Heatmaps update when baseline changes
- Summary metrics are accurate
- No flickering when toggling

---

### M8: Environmental Normalization + Modality Attribution (Priority 4)
**Owner**: Frontend Agent
**Duration**: 2 days
**Dependencies**: M6 (timeline working), M2 (neutral scenario data)

- [ ] Add environmental normalization toggle
  - Checkbox in detail panel header: "Show Neutral Environment"
  - When enabled, replaces "Observed Reality" panel with "Neutral Scenario"
  - Tooltip: "Shows predicted evolution with rain_anom=0, temp_anom=0"

- [ ] Fetch neutral scenario data
  - Call `/api/detect/tile/{tile_id}/neutral` (new endpoint in M2)
  - Returns: {neutral_residuals: float[T][16][16], delta: float[T][16][16]}
  - Display delta heatmap (difference: observed - neutral)

- [ ] Update panel labels dynamically
  - When toggle ON:
    - Left: "Expected Evolution (Neutral)"
    - Center: "Neutral Scenario Rollout"
    - Right: "Environmental Attribution"
  - Heatmap shows what's explained by environment vs human activity

- [ ] Create modality attribution widget
  - Position: Top of detail panel, right side
  - Fetch `/api/detect/tile/{tile_id}/attribution`
  - Horizontal bar chart:
    - SAR (red bar): X%
    - Optical (green bar): Y%
    - VIIRS (blue bar): Z%
  - Tooltip on each bar explaining signal type

- [ ] Add modality icon to hotspot list
  - Determine dominant modality (>50% contribution)
  - Display icon next to tile name: radar icon (SAR), camera (Optical), bulb (VIIRS)

**Acceptance Criteria**:
- Environmental toggle switches between observed/neutral views
- Modality attribution bar chart sums to 100%
- Icons match dominant modality correctly
- Neutral scenario heatmap displays attribution delta
- Tooltips explain each modality's meaning

---

### M9: Polish + Demo Script + Tests (Priority 5)
**Owner**: QA Agent + All Agents
**Duration**: 3 days
**Dependencies**: M8 (all features complete)

- [ ] Performance optimization
  - Lazy load imagery tiles (only visible months)
  - Memoize expensive computations (heatmap rendering)
  - Add React Query cache with 5min TTL
  - Virtualize hotspot list if >50 items

- [ ] Accessibility audit
  - All interactive elements keyboard-navigable
  - ARIA labels on all icons/buttons
  - Focus indicators visible (cyan outline)
  - Screen reader tested with NVDA

- [ ] Create demo script document
  - "**Scene 1**: Overview - Show AOI map with hotspots"
  - "**Scene 2**: Selection - Click Port of Oakland hotspot"
  - "**Scene 3**: Evidence - Show Expected vs Observed vs Residual"
  - "**Scene 4**: Timeline - Scrub to onset month, show spike"
  - "**Scene 5**: Baseline - Toggle to Persistence, show noise reduction"
  - "**Scene 6**: Attribution - Explain SAR dominance, show modality chart"
  - Timing: 3 minutes total, rehearsed flow

- [ ] Write integration tests
  - E2E test: Load page → Select hotspot → Verify detail panel loads
  - API contract test: Validate all endpoints return expected schemas
  - Visual regression test: Screenshot baseline for key UI states
  - Performance test: Page load <2s, time-to-interactive <3s

- [ ] Create fallback data handling
  - If API fails, load static demo data from JSON file
  - "Demo Mode" banner at top
  - Graceful degradation: disable features if data missing

- [ ] Documentation
  - README with setup instructions (npm install, API URL config)
  - Architecture diagram showing data flow
  - Troubleshooting guide for common issues
  - Deployment checklist

**Acceptance Criteria**:
- Demo runs smoothly without errors
- All tests pass (integration + contract + visual)
- Demo script rehearsed and timing confirmed
- Documentation complete and accurate
- Fallback mode tested and working

---

## File Ownership (To Avoid Conflicts)

### Backend Agent
- `/api/` (all FastAPI routes and services)
- `/api/routes/detection.py` - Detection endpoints
- `/api/services/storage.py` - HDF5 storage service
- `/api/models/schemas.py` - Pydantic models
- `/api/main.py` - FastAPI app entry point
- `/scripts/test_api_endpoints.py` - API smoke tests

### Data Agent
- `/data/` (all HDF5 files and preprocessing)
- `/scripts/create_test_hdf5.py` - HDF5 generation
- `/scripts/precompute_hotspots.py` - Hotspot ranking (NEW)
- `/scripts/compute_modality_attribution.py` - Attribution analysis (NEW)
- `/scripts/generate_neutral_scenarios.py` - Counterfactual rollouts (NEW)
- `/scripts/validate_hdf5_structure.py` - Data validation (NEW)

### Frontend Agent
- `/frontend/` (all Next.js app code)
- `/frontend/app/` - App router pages
- `/frontend/components/` - React components
  - `/frontend/components/map/` - Map + hotspot layers
  - `/frontend/components/hotspot-list/` - Right rail sidebar
  - `/frontend/components/detail-panel/` - Bottom panel container
  - `/frontend/components/timeline/` - Scrubber component
  - `/frontend/components/imagery/` - Three-panel display
- `/frontend/lib/api.ts` - API client with typed endpoints
- `/frontend/lib/types.ts` - TypeScript interfaces (synced with API schemas)
- `/frontend/styles/` - Tailwind config + design tokens

### QA Agent
- `/tests/` - All test suites
- `/tests/integration/` - E2E tests (Playwright)
- `/tests/api/` - API contract tests
- `/tests/visual/` - Visual regression snapshots
- `/docs/DEMO_SCRIPT.md` - Presentation guide
- `/docs/TESTING_STRATEGY.md` - Test plan

### Shared Files (Coordinate Changes)
- `/docs/API_CONTRACT.md` - API spec (Backend + Frontend review required)
- `/docs/DATA_SCHEMA.md` - HDF5 structure (Data + Backend review required)
- `/README.md` - Project setup (All agents contribute)

---

## Blocking Dependencies

```
M1 (API Contracts) → M3 (UI Foundation) → M4 (Map + List)
M2 (Precompute) → M4 (Map needs hotspot data)
M4 → M5 (Detail Panel) → M6 (Timeline) → M7 (Baselines) → M8 (Attribution)
M8 → M9 (Polish + Tests)

Parallel Work Allowed:
- M1 and M2 can run simultaneously
- M3 can start once M1 defines schemas
- M5/M6/M7/M8 can have partial parallel work if coordinated
```

**Critical Path**: M1 → M3 → M4 → M5 → M6 → M9
**Estimated Total Duration**: 16 days with proper handoffs

---

## Key Technical Decisions

### 1. No Pixel Decoder
- **Decision**: World model uses latent residuals only, no RGB reconstruction
- **Impact**: "Expected Evolution" panel shows PCA-projected latents or smoothed imagery, not true predictions
- **Rationale**: JEPA architecture doesn't include decoder; focus on residual detection, not visualization

### 2. Precomputed Hotspots
- **Decision**: Hotspot ranking computed offline in HDF5, not real-time
- **Impact**: Fast API responses (<50ms), but can't change ranking algorithm without recomputing
- **Rationale**: Demo stability; real-time ranking adds complexity without demo value

### 3. Mapbox vs Leaflet
- **Decision**: Use Mapbox GL JS for map rendering
- **Impact**: Requires Mapbox API token (free tier: 50k loads/month)
- **Rationale**: Better performance with vector tiles, smoother animations, Anduril-compatible dark themes

### 4. Next.js App Router
- **Decision**: Use Next.js 14+ App Router (not Pages Router)
- **Impact**: Server components by default, file-based routing
- **Rationale**: Modern React patterns, better performance, future-proof

### 5. Static Data Fallback
- **Decision**: Bundle demo data as JSON fallback if API unavailable
- **Impact**: Adds ~500KB to bundle size
- **Rationale**: Demo reliability; can present without backend running

---

## Risk Mitigation

### Risk 1: HDF5 Data Incomplete
**Probability**: Medium
**Impact**: High (blocks M4-M8)
**Mitigation**:
- M2 starts immediately to validate existing data
- Create synthetic data generator as backup
- Define minimum viable dataset (10 tiles minimum)

### Risk 2: Latent Visualization Unclear
**Probability**: High
**Impact**: Medium (UX confusion)
**Mitigation**:
- Use smoothed actual imagery as "Expected Evolution" placeholder
- Add tooltip: "Visualization approximates model's internal representation"
- Focus demo narrative on residuals, not predictions

### Risk 3: Performance with Large Datasets
**Probability**: Low (only 75 tiles in test dataset)
**Impact**: Medium (slow UI)
**Mitigation**:
- Lazy load imagery (only render visible components)
- Paginate hotspot list if >20 items
- Use React Query caching aggressively

### Risk 4: Timeline Scrubbing Lag
**Probability**: Medium
**Impact**: Low (poor UX)
**Mitigation**:
- Debounce scrubber updates (100ms delay)
- Preload ±3 months of imagery when panel opens
- Use lower-resolution thumbnails for scrubbing

### Risk 5: Design Doesn't Match Anduril Lattice
**Probability**: Medium
**Impact**: High (wrong visual style)
**Mitigation**:
- Reference Anduril public materials/screenshots early
- Create design mockup before coding (Figma/whiteboard)
- Get stakeholder approval on visual style in M3

---

## Success Metrics

### Technical Metrics
- [ ] API response times <100ms (p95)
- [ ] Page load time <2s
- [ ] Time to interactive <3s
- [ ] Zero console errors in production build
- [ ] 100% TypeScript type coverage in frontend

### Functional Metrics
- [ ] All 10 hotspots display on map correctly
- [ ] Residual heatmaps match precomputed values
- [ ] Timeline scrubbing updates all panels in sync
- [ ] Baseline comparison shows expected noise reduction
- [ ] Modality attribution sums to 100% for all tiles

### Demo Metrics
- [ ] Demo script runs in <3 minutes
- [ ] No manual data loading required (automated)
- [ ] Clear visual distinction: Expected vs Observed vs Residual
- [ ] Audience can identify "prediction → observation → divergence" narrative
- [ ] At least one compelling SF infrastructure example shown

---

## Open Questions (Require Decision Before Start)

### Q1: "Expected Evolution" Visualization Approach
**Options**:
- A) Use PCA projection of predicted latents to RGB (requires offline compute)
- B) Display smoothed actual imagery as proxy (simple, less accurate)
- C) Show latent heatmap directly (abstract, harder to interpret)

**Recommendation**: Option B for demo simplicity
**Decision Needed By**: Before M5 starts

### Q2: Real vs Synthetic Data
**Current State**: 75 synthetic tiles with realistic change patterns
**Options**:
- A) Use existing synthetic dataset (safe, complete)
- B) Mix synthetic + real SF satellite data (requires Sentinel download)
- C) Full real data only (high risk, data pipeline complexity)

**Recommendation**: Option A (synthetic only) for demo reliability
**Decision Needed By**: M2 start

### Q3: Environmental Normalization Complexity
**Question**: Should neutral scenario show:
- A) Full counterfactual rollout (complex, true to model)
- B) Simple delta visualization (easier to explain)
- C) Skip feature for v1 demo (reduce scope)

**Recommendation**: Option B (delta visualization)
**Decision Needed By**: M8 start

### Q4: Deployment Target
**Options**:
- A) Local development only (npm run dev + uvicorn)
- B) Docker container for portability
- C) Cloud deployment (Vercel frontend + AWS Lambda backend)

**Recommendation**: Option A for demo, Option B for distribution
**Decision Needed By**: M9 (deployment docs)

---

## Approval Request

**Ready to proceed with this plan?**

**Y/N**: _______

**Modifications Needed** (if N):
- [ ] Adjust milestone priorities?
- [ ] Change agent assignments?
- [ ] Revise technical decisions?
- [ ] Add/remove features?

**Approver Signature**: _______________
**Date**: _______________

---

## Next Steps After Approval

1. **Kick-off Meeting** (30 min)
   - All agents review plan
   - Clarify file ownership boundaries
   - Establish daily sync schedule (15 min standup)

2. **M1 + M2 Start Immediately** (Parallel)
   - Backend Agent: API skeleton + storage service
   - Data Agent: HDF5 validation + hotspot ranking

3. **Design Review** (Before M3)
   - Frontend Agent creates Figma mockup or wireframe
   - Stakeholder approval on Lattice visual style
   - Confirm color palette, typography, layout

4. **Weekly Checkpoints**
   - Monday: Review progress, unblock issues
   - Wednesday: Integration testing (cross-agent)
   - Friday: Demo rehearsal (after M8)

5. **Final Demo Dry Run** (Day 15)
   - Full end-to-end walkthrough
   - Timing confirmation (3 min target)
   - Backup plan if anything breaks

---

**End of Plan**
