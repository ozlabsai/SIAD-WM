# Implementation Plan: Temporal Conditioning

**Branch**: `003-003-temporal-conditioning` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-003-temporal-conditioning/spec.md`

## Summary

Extend the SIAD world model's action conditioning to include **month-of-year cyclical encoding** (`month_sin`, `month_cos`) alongside existing weather anomalies. This provides explicit seasonal context to reduce false anomaly spikes at seasonal transitions (e.g., summer→autumn vegetation changes) and improve multi-step rollout stability across seasonal boundaries.

**Technical Approach**: Extend action vector from [rain_anom, temp_anom] (A=2) to [rain_anom, temp_anom, month_sin, month_cos] (A=4). No architectural changes required - temporal features flow through existing ActionEncoder (`hφ`) and conditioning pathways (action token + FiLM modulation). Data pipeline extracts month from timestamps and computes cyclical encoding `sin(2π*month/12)` and `cos(2π*month/12)`.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution requirement)
**Primary Dependencies**: PyTorch 2.x (world model), rasterio + numpy (geospatial I/O), h5py (dataset storage), pytest (testing)
**Storage**: HDF5 datasets (`*.h5`) for preprocessed satellite imagery tiles, metadata JSON for timestamp tracking
**Testing**: pytest (unit tests for temporal feature extraction, shape contracts, integration tests for full pipeline)
**Target Platform**: Linux server (training on GPU), CLI-driven workflows per constitution Principle V
**Project Type**: Machine learning library with CLI tools (data preprocessing, model training, inference)
**Performance Goals**: Training throughput <5% degradation with temporal features (same as baseline), rollout error reduction >10% on seasonal transitions
**Constraints**: No increase in model parameters (reuses existing ActionEncoder), backward compatible (load old checkpoints with action_dim=2)
**Scale/Scope**: Single-feature MVP scope - extends existing action conditioning (2 dims → 4 dims), affects ~5 files (dataset.py, actions.py, config/schema.py, training config, tests)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with SIAD Constitution (v1.0.0):

- **I. Data-Driven Foundation**: ✓ **COMPLIANT** - Temporal features (month_sin/cos) extracted deterministically from existing timestamp metadata. No new satellite data sources required. Aligns with existing preprocessing pipeline.

- **II. Counterfactual Reasoning**: ✓ **COMPLIANT** - Temporal features enhance counterfactual scenarios by providing seasonal context. Explicitly NOT claiming month causes construction - only that seasonal context helps distinguish vegetation cycles from infrastructure changes. Temporal features are exogenous conditioning, same status as weather anomalies.

- **III. Testable Predictions (NON-NEGOTIABLE)**: ✓ **COMPLIANT** - Acceptance tests defined:
  1. **Shape contract test**: Verify action_dim=4 throughout pipeline
  2. **Seasonal stability test**: Measure residual reduction on 100 summer→autumn pairs (target: >20% reduction)
  3. **Ablation test**: Compare baseline (A=2) vs temporal (A=4) on rollout error across seasons

- **IV. Interpretable Attribution**: ✓ **COMPLIANT** (N/A for this feature) - Temporal conditioning does not affect modality attribution. SAR/optical/lights decomposition remains unchanged. Temporal features only improve base predictions, not attribution.

- **V. Reproducible Pipelines**: ✓ **COMPLIANT** - All temporal feature extraction is deterministic (sin/cos from datetime.month). CLI-scriptable via updated data preprocessing commands. Configuration schema explicitly tracks preprocessing_version="v2" for reproducibility.

**Technical Constraints**:
- Python 3.13+ with UV? ✓ (existing requirement, no change)
- Earth Engine catalog sources? ✓ (no new data sources, uses existing timestamps)
- 10m resolution target? ✓ (no change to spatial resolution)
- Monthly cadence minimum? ✓ (temporal features align with monthly composites)
- DRY and KISS adherence? ✓ (reuses existing ActionEncoder, minimal code change ~50 LOC)

**Development Workflow**:
- MVP-first scope (single AOI, 36mo, 6mo rollout)? ✓ (feature scope limited to action vector extension)
- Validation gates defined (self-consistency → backtest → false-positive)? ✓ (ablation test on seasonal transitions, shape contracts)
- Claims boundary respected (no intent inference, actor ID, causal weather attribution)? ✓ (explicit statement: temporal features do NOT cause construction, only provide context)

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
src/siad/
├── model/
│   ├── actions.py          # ActionEncoder (MODIFIED: input_dim 2→4)
│   ├── transition.py       # Uses ActionEncoder (no changes)
│   └── world_model.py      # Integrates encoder+transition (no changes)
├── data/
│   ├── dataset.py          # Dataset loader (MODIFIED: add temporal features)
│   └── preprocessing.py    # Tile preprocessing (MODIFIED: extract month from timestamps)
├── config/
│   └── schema.py           # Config validation (MODIFIED: action_dim default 2→4)
├── train/
│   └── trainer.py          # Training loop (no changes - accepts any action_dim)
└── cli/
    └── preprocess.py       # CLI commands (MODIFIED: --preprocessing-version v2 flag)

configs/
├── train-baseline.yaml     # Training config (MODIFIED: actions.input_dim: 4)
└── preprocess-v2.yaml      # New preprocessing config with temporal features

tests/
├── unit/
│   ├── test_temporal_features.py     # NEW: Test month_sin/cos extraction
│   ├── test_action_encoder.py        # MODIFIED: Test action_dim=4
│   └── test_dataset.py                # MODIFIED: Test temporal features in batch
└── integration/
    └── test_seasonal_stability.py     # NEW: Ablation test baseline vs temporal
```

**Structure Decision**: Single Python project with CLI tools. Temporal conditioning is a data+model feature affecting 5 files: `actions.py` (ActionEncoder input dim), `dataset.py` (add temporal features to batches), `preprocessing.py` (extract month from timestamps), `schema.py` (config validation), and new test files.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - Feature passes all constitution checks. Implementation reuses existing ActionEncoder architecture (KISS principle), adds <50 LOC for temporal feature extraction (DRY principle), and maintains all testability/reproducibility requirements.
