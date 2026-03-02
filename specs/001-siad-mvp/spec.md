# Feature Specification: SIAD MVP - Infrastructure Acceleration Detection

**Feature Branch**: `001-siad-mvp`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "Full SIAD MVP: multi-modal satellite data collection, preprocessing, world model training with counterfactual rollouts, acceleration detection with modality attribution, and visualization outputs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect Infrastructure Acceleration in Region (Priority: P1)

An analyst wants to identify locations within a 50×50 km region where infrastructure development or activity has accelerated beyond normal seasonal patterns over the past 3 years, distinguishing genuine structural changes from weather-driven vegetation cycles.

**Why this priority**: This is the core value proposition - detecting persistent structural deviations is the primary use case. Without this, there is no product.

**Independent Test**: Can be fully tested by providing historical satellite imagery for a region with known construction events (e.g., port expansion, industrial park development) and verifying that the system flags these locations with "Structural" or "Activity" confidence tiers while not flagging agricultural regions with seasonal cycles.

**Acceptance Scenarios**:

1. **Given** 36 months of satellite imagery for a 50×50 km area, **When** the analyst runs acceleration detection, **Then** the system produces a spatial heatmap showing acceleration scores for each 2.56 km tile
2. **Given** a detected hotspot cluster, **When** the analyst views the hotspot details, **Then** the system shows before/after satellite thumbnails (radar, optical, nighttime lights), the month when acceleration began, and a confidence tier (Structural/Activity/Environmental)
3. **Given** a region dominated by seasonal agriculture, **When** the analyst runs acceleration detection, **Then** the system labels these changes as "Environmental" rather than "Structural" to reduce false positives
4. **Given** cloud-covered optical imagery, **When** the system processes the data, **Then** radar (SAR) data compensates for missing optical data and the valid pixel fraction is tracked to maintain detection reliability

---

### User Story 2 - Compare Counterfactual Scenarios (Priority: P2)

An analyst wants to understand whether detected changes would still appear unusual under different weather scenarios (neutral, observed, or extreme rainfall/heat conditions) to separate infrastructure acceleration from environmental responses.

**Why this priority**: Counterfactual reasoning is critical for reducing false positives and providing defensible attribution, but requires the base detection system (P1) to exist first.

**Independent Test**: Can be tested independently by providing historical data for a region, running counterfactual rollouts with neutral weather (rain_anom=0, temp_anom=0) versus observed weather, and verifying that infrastructure changes remain flagged while vegetation/water changes reduce under neutral scenarios.

**Acceptance Scenarios**:

1. **Given** a detected hotspot, **When** the analyst toggles between "neutral weather", "observed weather", and "extreme rain" scenarios, **Then** the system shows predicted rollout trajectories and divergence heatmaps for each scenario
2. **Given** a vegetation change driven by rainfall, **When** the analyst runs a neutral weather counterfactual, **Then** the divergence from neutral baseline is low, indicating the change is weather-explained rather than structural
3. **Given** a construction site, **When** the analyst runs counterfactual scenarios with varying weather, **Then** the acceleration score remains high across all scenarios because infrastructure changes are weather-independent

---

### User Story 3 - Review Temporal Timeline of Acceleration (Priority: P3)

An analyst wants to see when acceleration began for each hotspot and how the deviation from expected baseline evolved over time to assess the pace and persistence of changes.

**Why this priority**: Timeline visualization adds analytical depth and helps distinguish one-time events from sustained acceleration, but requires both detection (P1) and counterfactual baselines (P2) to be meaningful.

**Independent Test**: Can be tested by examining a region with known construction start date and verifying that the timeline shows residual scores increasing from that month forward with persistence indicators.

**Acceptance Scenarios**:

1. **Given** a flagged hotspot cluster, **When** the analyst views the timeline, **Then** the system displays residual scores over time with the persistence window highlighted and estimated start date marked
2. **Given** multiple hotspots, **When** the analyst sorts by "start date", **Then** hotspots are ranked chronologically showing which accelerations began earliest
3. **Given** a transient change (e.g., temporary flooding), **When** the analyst views the timeline, **Then** the residual score spikes briefly but does not meet the 2-month persistence threshold, filtering it out of final hotspot rankings

---

### Edge Cases

- **What happens when satellite imagery has extensive cloud cover for multiple consecutive months?** System tracks valid pixel fraction and relies more heavily on cloud-proof SAR data; tiles with insufficient valid coverage are flagged with reduced confidence
- **How does system handle regions with mixed land use (urban + agriculture)?** Tile-level scoring (2.56 km) may blend signals; modality attribution separates SAR (structural) from optical (vegetation) contributions to enable analysts to distinguish patterns
- **What happens when an AOI straddles different climate zones?** Rainfall/temperature anomalies are computed per-AOI using tile-local percentile scoring, so each tile is compared against its own historical baseline
- **How does system handle very recent changes (< 6 months)?** System requires 6 months of context (L=6) plus 6 months rollout horizon (H=6) minimum; changes within the final 6 months appear in rolling predictions but full validation requires waiting for the rollout period to complete

## Requirements *(mandatory)*

### Functional Requirements

#### Data Collection & Preprocessing

- **FR-001**: System MUST collect monthly satellite imagery for a user-specified Area of Interest (AOI) spanning 36 months of history
- **FR-002**: System MUST acquire Sentinel-1 SAR data (VV and VH bands) with monthly median composites
- **FR-003**: System MUST acquire Sentinel-2 optical data (Blue, Green, Red, NIR bands) with cloud-masked monthly median composites and valid pixel fraction tracking
- **FR-004**: System MUST acquire VIIRS nighttime lights monthly composite data
- **FR-005**: System MUST acquire rainfall anomaly data from CHIRPS or ERA5 precipitation datasets
- **FR-006**: System MUST acquire temperature anomaly data from ERA5 2-meter temperature datasets (optional enhancement)
- **FR-007**: System MUST resample all data sources to a common spatial grid at 10-meter resolution using a fixed projection
- **FR-008**: System MUST align all data sources to calendar month boundaries for temporal consistency
- **FR-009**: System MUST divide the AOI into 256×256 pixel tiles (approximately 2.56 km squares at 10m resolution)
- **FR-010**: System MUST normalize rainfall and temperature data to anomalies using AOI-specific monthly mean and standard deviation baselines

#### Model Training & Prediction

- **FR-011**: System MUST train a world model that learns baseline spatiotemporal dynamics from 6-month context windows and predicts 6-month future rollouts
- **FR-012**: System MUST support counterfactual rollouts conditioned on scenario-specific rainfall and temperature anomaly values
- **FR-013**: System MUST compute multi-step rollout predictions recursively for k=1 to k=6 months ahead
- **FR-014**: System MUST use consistent encoder representations for observed data and EMA-stabilized target representations for training

#### Acceleration Detection

- **FR-015**: System MUST compute acceleration scores by measuring divergence between neutral counterfactual rollouts (rain_anom=0, temp_anom=0) and observed reality
- **FR-016**: System MUST flag tiles where acceleration score exceeds the tile's own 99th historical percentile
- **FR-017**: System MUST require flagged tiles to persist for at least 2 consecutive months before inclusion in final hotspot list
- **FR-018**: System MUST cluster spatially connected tiles (minimum 3 tiles) to form coherent hotspot regions
- **FR-019**: System MUST recompute acceleration scores using SAR-only, optical-only, and lights-only inputs to enable modality attribution
- **FR-020**: System MUST classify each hotspot as "Structural" (SAR + lights dominant), "Activity" (lights-dominant), or "Environmental" (optical NDVI-like) based on modality attribution

#### Validation & Quality Assurance

- **FR-021**: System MUST perform self-consistency validation by verifying that neutral scenario rollouts match typical seasonal evolution better than random action sequences
- **FR-022**: System MUST support backtesting mode where analysts can validate detections against known construction events in selected AOIs
- **FR-023**: System MUST measure false-positive rates in regions dominated by agriculture, monsoons, or seasonal rivers
- **FR-024**: System MUST report persistence threshold effectiveness and modality-attribution stability metrics during validation

#### Outputs & Visualization

- **FR-025**: System MUST generate a spatial heatmap showing acceleration score percentiles for all tiles in the AOI
- **FR-026**: System MUST provide a ranked list of hotspots with before/after thumbnails (SAR, optical, lights), first-detected month, and confidence tier
- **FR-027**: System MUST generate timeline visualizations for each hotspot showing residual scores over time with persistence windows highlighted
- **FR-028**: System MUST support interactive toggling between neutral weather, observed weather, and extreme scenario counterfactual rollouts
- **FR-029**: System MUST display rollout trajectory plots in latent space and divergence heatmap overlays for counterfactual scenarios

### Key Entities

- **Area of Interest (AOI)**: A geographic bounding box approximately 50×50 km containing the region to be analyzed; defined by corner coordinates
- **Tile**: A 256×256 pixel spatial grid cell at 10m resolution (~2.56 km square); the atomic unit for acceleration scoring
- **Timestep**: A monthly temporal unit aligned to calendar month boundaries; contains multi-modal satellite observations and climate context
- **Observation**: An 8-channel tensor per timestep per tile containing Sentinel-2 optical (4 channels), Sentinel-1 SAR (2 channels), VIIRS lights (1 channel), and valid pixel fraction (1 channel)
- **Action (Scenario Context)**: Rainfall and temperature anomaly scalars per timestep used for counterfactual conditioning
- **Rollout**: A sequence of predicted future observations spanning 6 months ahead, conditioned on a scenario's action sequence
- **Hotspot**: A spatially coherent cluster of tiles (≥3 connected tiles) that exceed acceleration thresholds with persistence (≥2 months)
- **Acceleration Score**: A tile-specific metric quantifying persistent divergence from neutral counterfactual baseline over a 6-month rollout horizon
- **Modality Attribution**: Decomposition of acceleration score into SAR-driven, optical-driven, and lights-driven components to classify hotspot type (Structural/Activity/Environmental)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Analysts can process a 50×50 km AOI with 36 months of history and produce acceleration heatmaps within a single analysis session
- **SC-002**: System correctly flags at least 80% of known infrastructure construction events (verified via visual inspection of before/after imagery) in backtesting regions
- **SC-003**: System maintains false-positive rate below 20% when tested on agriculture-dominated or monsoon-affected regions (measured as hotspots per month that are visually confirmed as environmental rather than structural)
- **SC-004**: Counterfactual rollouts demonstrate that neutral weather scenarios reduce divergence scores for vegetation/water changes by at least 50% compared to observed weather, while infrastructure changes remain within 10% across scenarios
- **SC-005**: Modality attribution correctly separates "Structural" hotspots (SAR + lights) from "Environmental" hotspots (optical-only) with 70% agreement against analyst visual inspection
- **SC-006**: Analysts can identify the month when acceleration began for each hotspot with ±1 month accuracy compared to visual inspection of satellite timeline
- **SC-007**: System produces all required outputs (heatmap, hotspot rankings, timelines, counterfactual comparisons) for a single AOI without manual intervention
- **SC-008**: Validation metrics (self-consistency, backtest success rate, false-positive rate) are automatically computed and reported for each analysis run

### Assumptions

- **Geographic Scope**: MVP targets a single AOI per analysis run; global coverage or multi-AOI batch processing is out of scope
- **Temporal Cadence**: Monthly resolution is sufficient for detecting infrastructure acceleration; sub-monthly (weekly/daily) monitoring is out of scope
- **Ground Truth**: Visual inspection by analysts serves as validation ground truth; automated ground-truth labeling or external construction databases are not required for MVP
- **Data Availability**: Earth Engine catalog provides consistent access to Sentinel-1, Sentinel-2, VIIRS, CHIRPS/ERA5 data for the past 36+ months in most regions; AOIs with insufficient coverage will be flagged during preprocessing
- **Claims Boundary**: System detects persistent deviations and provides scenario-based context; it does NOT infer intent, identify actors, attribute causality from weather to construction, or support tactical real-time surveillance
- **Compute Resources**: Model training and inference are performed on standard cloud GPU instances (e.g., single A100 or equivalent); distributed training across multiple nodes is not required for MVP scale
- **User Expertise**: Users are analysts with geospatial imagery interpretation skills; system does not need to teach satellite image analysis fundamentals
