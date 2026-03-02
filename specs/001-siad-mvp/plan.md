# Implementation Plan: SIAD MVP - Infrastructure Acceleration Detection

**Branch**: `001-siad-mvp` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-siad-mvp/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a geospatial ML pipeline that detects persistent infrastructure acceleration in satellite imagery by training a world model on multi-modal monthly time series (Sentinel-1 SAR, Sentinel-2 optical, VIIRS nighttime lights, CHIRPS/ERA5 climate data) and flagging tiles where observed changes diverge from neutral-weather counterfactual rollouts. The system produces spatial heatmaps, hotspot rankings with modality attribution (Structural/Activity/Environmental), and temporal timelines for a 50×50 km AOI over 36 months history with 6-month rollout predictions.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution requirement)
**Primary Dependencies**: `earthengine-api` (satellite data collection), PyTorch 2.x (world model training with `torch.compile()`), `rasterio` + `numpy` (geospatial I/O), `matplotlib` (visualization), `h5py` (dataset storage), `pytest` (testing)
**Storage**: File-based - GeoTIFF (Earth Engine downloads), HDF5 (preprocessed tensors via memory-mapped datasets), PNG/PDF (visualizations), optional GeoJSON (hotspot exports)
**Testing**: pytest with contract/integration/unit test hierarchy; CLI contract tests verify stdin/stdout behavior per Principle V
**Target Platform**: Linux cloud instances with GPU (single A100 or equivalent for MVP; CPU-only preprocessing acceptable for data pipeline)
**Project Type**: CLI-driven pipeline library (per constitution Principle V: stdin/args → stdout, errors → stderr)
**Performance Goals**: Process 50×50 km AOI (~400 tiles at 2.56km/tile) with 36 months history within single session (<24 hours end-to-end including data download); inference rollouts <5 min per scenario
**Constraints**: Single GPU memory limit (~40GB for A100); monthly temporal resolution (no real-time); deterministic pipeline execution for auditability
**Scale/Scope**: MVP targets single AOI per run (~400 tiles × 36 timesteps = 14,400 tile-months); 8-channel observations + 2 action scalars; world model latent dim and architecture resolved in research.md (ConvNet encoder + 1-2 layer transformer dynamics)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with SIAD Constitution (v1.0.0):

- **I. Data-Driven Foundation**: ✓ Spec FR-007 requires common spatial grid at 10m, FR-008 requires calendar month alignment, FR-010 requires documented anomaly normalization
- **II. Counterfactual Reasoning**: ✓ Spec FR-012 requires scenario conditioning on rain/temp anomalies; Assumptions section prohibits causal weather-to-construction claims
- **III. Testable Predictions (NON-NEGOTIABLE)**: ✓ Spec FR-021 (self-consistency), FR-022 (backtesting), FR-023 (false-positive testing) defined; SC-002/SC-003 set 80% hit rate and <20% FP targets
- **IV. Interpretable Attribution**: ✓ Spec FR-019/FR-020 require SAR/optical/lights decomposition producing Structural/Activity/Environmental labels; SC-005 sets 70% agreement target
- **V. Reproducible Pipelines**: ✓ Project type defined as CLI-driven pipeline library; pytest testing framework confirmed; file-based storage for deterministic I/O

**Technical Constraints**:
- Python 3.13+ with UV? ✓ (Language/Version confirmed)
- Earth Engine catalog sources? ✓ (Spec FR-002 Sentinel-1, FR-003 Sentinel-2, FR-004 VIIRS, FR-005 CHIRPS/ERA5)
- 10m resolution target? ✓ (Spec FR-007, Performance Goals confirmed)
- Monthly cadence minimum? ✓ (Spec FR-001 36 months, FR-008 calendar month boundaries)
- DRY and KISS adherence? ⚠️ **REQUIRES VIGILANCE** - World model architecture TBD in research; must avoid premature abstraction

**Development Workflow**:
- MVP-first scope (single AOI, 36mo, 6mo rollout)? ✓ (Spec Assumptions: single AOI per run, 36 months history, FR-011 6-month context + FR-013 6-month rollout)
- Validation gates defined (self-consistency → backtest → false-positive)? ✓ (FR-021 → FR-022 → FR-023 sequence matches constitution gate order)
- Claims boundary respected (no intent inference, actor ID, causal weather attribution)? ✓ (Spec Assumptions section explicitly prohibits all four)

**GATE STATUS**: ✅ **PASS** - Proceed to Phase 0 Research

**Notes**: One vigilance point on KISS (world model complexity) to be addressed in research phase by selecting minimal viable architecture (small ConvNet or ViT encoder, single-layer transformer dynamics per PRD Section 5 guidance).

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── data/                    # Data collection & preprocessing (FR-001 to FR-010)
│   ├── collectors/          # Earth Engine API wrappers per data source
│   ├── preprocessing/       # Reprojection, compositing, tiling, normalization
│   └── loaders/             # PyTorch/JAX dataset loaders for training
├── models/                  # World model architecture (FR-011 to FR-014)
│   ├── encoders/            # Observation encoder, target encoder (EMA), action encoder
│   ├── dynamics/            # Transition model (F_ψ)
│   └── losses/              # Multi-step rollout loss computation
├── detection/               # Acceleration scoring & attribution (FR-015 to FR-020)
│   ├── rollouts/            # Counterfactual scenario rollout engine
│   ├── scoring/             # Acceleration score computation, percentile flagging
│   └── attribution/         # Modality-specific decomposition (SAR/optical/lights)
├── validation/              # Quality assurance (FR-021 to FR-024)
│   ├── consistency/         # Self-consistency checks
│   ├── backtest/            # Backtesting on known regions
│   └── false_positive/      # False-positive rate measurement
├── visualization/           # Outputs & viz (FR-025 to FR-029)
│   ├── heatmaps/            # Spatial acceleration heatmaps
│   ├── timelines/           # Temporal residual plots
│   └── comparisons/         # Counterfactual scenario comparisons
└── cli/                     # CLI entrypoints (constitution Principle V)
    ├── collect.py           # Data collection command
    ├── preprocess.py        # Preprocessing command
    ├── train.py             # Model training command
    ├── detect.py            # Inference + detection command
    ├── validate.py          # Validation suite command
    └── visualize.py         # Visualization generation command

tests/
├── contract/                # Public CLI interface contract tests
│   ├── test_cli_collect.py
│   ├── test_cli_detect.py
│   └── test_cli_outputs.py
├── integration/             # End-to-end pipeline integration tests
│   ├── test_data_pipeline.py
│   ├── test_training_pipeline.py
│   └── test_detection_pipeline.py
└── unit/                    # Unit tests mirroring src/ structure
    ├── test_data/
    ├── test_models/
    ├── test_detection/
    ├── test_validation/
    └── test_visualization/

data/                        # Local data directory (gitignored)
├── raw/                     # Downloaded Earth Engine data (GeoTIFF/NetCDF)
├── preprocessed/            # Preprocessed tiles (HDF5/Zarr)
├── models/                  # Trained model checkpoints
└── outputs/                 # Generated heatmaps, timelines, reports

configs/                     # Configuration files
├── aoi_examples/            # Example AOI configs (bounding boxes)
├── scenarios/               # Scenario definitions (neutral, observed, extreme)
└── validation_regions/      # Backtesting + false-positive test region configs
```

**Structure Decision**: Single project structure (Option 1) selected. This is a CLI-driven ML pipeline library, not a web service or mobile app. The structure follows a pipeline stages organization:

1. **Data pipeline** (`src/data/`): Collection → Preprocessing → Loading
2. **Model pipeline** (`src/models/`): Encoder → Dynamics → Loss
3. **Detection pipeline** (`src/detection/`): Rollouts → Scoring → Attribution
4. **Validation pipeline** (`src/validation/`): Three-gate validation per constitution
5. **Visualization pipeline** (`src/visualization/`): Heatmaps → Timelines → Comparisons
6. **CLI layer** (`src/cli/`): Each pipeline stage exposed as a scriptable command per Principle V

Tests follow contract (CLI I/O) → integration (multi-stage) → unit (per-module) hierarchy matching constitution's testability requirements.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected** - All design decisions align with constitution principles. Post-design validation:

### KISS Compliance Verification

**Research decisions** (research.md):
- ✓ PyTorch over JAX: Justified by geospatial ecosystem maturity (not premature optimization)
- ✓ rasterio over xarray: Deferred abstraction until multi-AOI scaling needed (YAGNI respected)
- ✓ matplotlib over Plotly: Static outputs sufficient for MVP (no web UI requirement)

**Architecture decisions** (data-model.md, contracts/):
- ✓ World model kept minimal: ConvNet/ViT encoder + 1-2 layer transformer dynamics per PRD Section 5 guidance
- ✓ CLI interface: 6 commands (collect, preprocess, train, detect, validate, visualize) matching pipeline stages—no premature abstraction into meta-orchestration layer
- ✓ File-based storage: HDF5/GeoTIFF/JSON sufficient for single-AOI scale—no database until global multi-AOI deployment

**Rejected over-engineering**:
- ❌ Distributed training framework (single A100 sufficient per spec assumptions)
- ❌ Web dashboard (static PNG/GeoJSON outputs meet SC-007)
- ❌ Real-time streaming pipeline (monthly cadence per spec assumptions)
- ❌ Custom geospatial data format (industry-standard GeoTIFF + HDF5)

## Post-Design Constitution Re-Check

*GATE: Must pass after Phase 1 design.*

### Principle Verification

- **I. Data-Driven Foundation**: ✅ **PASS**
  - contracts/cli-interface.md: `siad-preprocess` enforces EPSG:3857 at 10m resolution
  - data-model.md: Observation entity defines 8-channel tensor with documented normalization
  - quickstart.md: Preprocessing step validates alignment to common spatiotemporal grid

- **II. Counterfactual Reasoning**: ✅ **PASS**
  - contracts/cli-interface.md: `siad-detect --scenarios` supports neutral/observed/custom rollouts
  - data-model.md: Action entity defines rain_anom/temp_anom with neutral=0 constraint
  - quickstart.md: Step 4 demonstrates neutral vs observed scenario comparison

- **III. Testable Predictions (NON-NEGOTIABLE)**: ✅ **PASS**
  - contracts/cli-interface.md: `siad-validate` implements three-gate validation (self-consistency, backtest, false-positive)
  - data-model.md: Validation entities reference spec SC-002 (80% hit rate), SC-003 (< 20% FP rate)
  - quickstart.md: Step 5 shows validation gate execution with pass/fail exit codes

- **IV. Interpretable Attribution**: ✅ **PASS**
  - contracts/cli-interface.md: `siad-detect` outputs hotspots.json with confidence_tier field
  - data-model.md: Modality Attribution entity defines SAR/optical/lights decomposition logic
  - quickstart.md: Step 4 output shows "7 Structural, 3 Activity, 2 Environmental" hotspot breakdown

- **V. Reproducible Pipelines**: ✅ **PASS**
  - contracts/cli-interface.md: All 6 commands follow stdin/stdout/stderr pattern with --dry-run flags
  - data-model.md: Storage section specifies deterministic file formats (HDF5, GeoTIFF, JSON)
  - quickstart.md: Full pipeline composition example chains commands via file paths

### Technical Constraints Re-Check

- Python 3.13+ with UV? ✅ Confirmed in Technical Context + quickstart.md installation
- Earth Engine catalog sources? ✅ Confirmed in research.md decision + contracts `siad-collect`
- 10m resolution target? ✅ Confirmed in data-model.md Tile entity + contracts `--resolution-m`
- Monthly cadence minimum? ✅ Confirmed in data-model.md Timestep entity (calendar month boundaries)
- DRY and KISS adherence? ✅ Verified in Complexity Tracking section above (no over-engineering)

### Development Workflow Re-Check

- MVP-first scope? ✅ quickstart.md targets single AOI (400 tiles, 36 months, 6-month rollout)
- Validation gates defined? ✅ contracts `siad-validate` gates + data-model.md validation entities
- Claims boundary respected? ✅ data-model.md Hotspot entity provides confidence_tier (not intent/actor/causal claims)

**FINAL GATE STATUS**: ✅ **PASS** - Design artifacts satisfy all constitution principles. Proceed to `/speckit.tasks`.

**Design Quality Summary**:
- All NEEDS CLARIFICATION items resolved in research.md
- 9 entities defined in data-model.md matching spec Key Entities
- 6 CLI commands defined in contracts/cli-interface.md covering full pipeline
- quickstart.md provides 15-minute demo from data collection to visualization
- Agent context updated with Python 3.13, PyTorch 2.x, earthengine-api, rasterio dependencies

**Ready for Phase 2**: Implementation plan complete. Next step: `/speckit.tasks` to generate task breakdown.
