# Implementation Tasks: Temporal Conditioning

**Feature**: 003-temporal-conditioning | **Branch**: `003-003-temporal-conditioning` | **Date**: 2026-03-05

## Overview

This document breaks down the temporal conditioning feature into actionable, executable tasks organized by user story (P1, P2, P3). Each user story represents an independently testable increment that delivers value.

**Total Estimated Tasks**: 18
**Parallelization Opportunities**: 8 tasks can run in parallel
**Suggested MVP**: User Story 1 (P1) - Seasonal Transition Accuracy

---

## Task Organization

Tasks are organized into phases corresponding to user stories from spec.md:

1. **Phase 1: Setup** - Project initialization and dependencies (2 tasks)
2. **Phase 2: Foundational** - Blocking prerequisites for all user stories (4 tasks)
3. **Phase 3: User Story 1 (P1)** - Seasonal Transition Accuracy (6 tasks)
4. **Phase 4: User Story 2 (P2)** - Multi-Step Rollout Stability (3 tasks)
5. **Phase 5: User Story 3 (P3)** - Training Efficiency (2 tasks)
6. **Phase 6: Polish** - Cross-cutting concerns (1 task)

**Dependencies**: Phases must be completed in order, but tasks within each phase marked [P] can run in parallel.

---

## Phase 1: Setup (Project Initialization)

**Goal**: Initialize project structure and dependencies for temporal conditioning

**Independent Test Criteria**:
- [ ] Configuration files exist and are valid
- [ ] Project structure matches plan.md

### Tasks

- [X] T001 Create preprocessing config template at configs/preprocess-v2.yaml
  - Copy from configs/preprocess-baseline.yaml if exists, otherwise create new
  - Add preprocessing_version: "v2" field
  - Add temporal_features: ["month_sin", "month_cos"] list
  - Document: "Preprocessing configuration for temporal conditioning (v2 schema)"

- [X] T002 [P] Update .gitignore for Python project per plan.md
  - Verify .gitignore contains: __pycache__/, *.pyc, .venv/, venv/, dist/, *.egg-info/
  - Add: *.h5 (large HDF5 datasets), .env*, *.log
  - Ensure specs/ directory is NOT ignored (contains planning docs)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Implement core temporal feature extraction and action encoder update that all user stories depend on

**Independent Test Criteria**:
- [ ] Temporal features can be computed from timestamps (unit test)
- [ ] ActionEncoder accepts action_dim=4 (unit test)
- [ ] Dataset loader handles v2 schema (unit test)
- [ ] Config schema validates action_dim=4 (unit test)

### Tasks

- [X] T003 [P] Implement compute_temporal_features() in src/siad/data/preprocessing.py
  - Function signature: def compute_temporal_features(timestamp: datetime) -> tuple[float, float]
  - Extract month: month = timestamp.month  # 1-12
  - Compute: angle = 2 * np.pi * month / 12
  - Return: (np.sin(angle), np.cos(angle))
  - Add docstring per contracts/dataset_api.md

- [X] T004 [P] Update ActionEncoder in src/siad/model/actions.py
  - Change default action_dim from 1 or 2 to 4
  - Update docstring: "Input: [B, 4] action vector (rain_anom, temp_anom, month_sin, month_cos)"
  - Verify Linear layer: Linear(action_dim → hidden_dim) handles any action_dim
  - No architecture changes needed (per research.md Q4)

- [X] T005 Extend Dataset.__getitem__() in src/siad/data/dataset.py
  - Check preprocessing_version attribute: version = f.attrs.get('preprocessing_version', 'v1')
  - If version == 'v1': Load actions [H, 2], set timestamps=None
  - If version == 'v2': Load actions [H, 4], load timestamps [H+1]
  - Add temporal feature validation: assert (month_sin**2 + month_cos**2) in [0.99, 1.01]
  - Return dict with timestamps field (None for v1, array for v2)

- [X] T006 Update config schema in src/siad/config/schema.py
  - Find ActionConfig or TransitionConfig class
  - Update action_dim default: Field(default=4, ge=1) (was default=2)
  - Add comment: "# V2: Extended to 4 for temporal features (month_sin, month_cos)"
  - Add preprocessing_version field if not exists: preprocessing_version: str = "v2"

---

## Phase 3: User Story 1 (P1) - Seasonal Transition Accuracy

**Goal**: Enable model to distinguish seasonal vegetation changes from infrastructure changes

**Why P1**: Core value proposition - reduces false positives that waste analyst time

**Independent Test**: Run model on summer→autumn transition pairs, verify residual heatmaps show low values for unchanged infrastructure

**Acceptance Criteria** (from spec.md):
- [ ] Given tile with stable infrastructure but changing vegetation, residual < 0.3 in infrastructure regions
- [ ] Temporal model shows >20% reduction in false anomaly flags vs baseline

### Tasks

- [X] T007 [US1] Create test_temporal_features.py in tests/unit/
  - Test: test_compute_temporal_features_range() - Verify month_sin/cos in [-1, 1]
  - Test: test_temporal_features_unit_circle() - Verify sin²+cos² ≈ 1 for all months
  - Test: test_year_boundary_continuity() - Verify Dec→Jan distance < 0.6
  - Test: test_temporal_features_all_months() - Verify correct values for Jan, Apr, Jul, Oct
  - Per contracts/dataset_api.md

- [X] T008 [P] [US1] Create test_action_encoder.py in tests/unit/
  - Test: test_action_encoder_forward_v2() - Forward pass with [B, 4] input
  - Test: test_action_encoder_shape_contract() - Verify output [B, 128]
  - Test: test_action_encoder_dimension_mismatch() - Verify error when input != action_dim
  - Per contracts/model_api.md

- [X] T009 [P] [US1] Create test_dataset.py modifications in tests/unit/
  - Test: test_v2_dataset_loading() - Load v2 dataset, verify action_dim=4
  - Test: test_temporal_feature_validation() - Verify unit circle property in batch
  - Test: test_v1_backward_compat() - Load v1 dataset, verify action_dim=2, timestamps=None
  - Per contracts/dataset_api.md

- [X] T010 [US1] Implement dataset preprocessing with temporal features in src/siad/data/preprocessing.py
  - Add method: add_temporal_features_to_actions(timestamps, actions_v1) -> actions_v2
  - For each timestamp in rollout: compute month_sin/cos using compute_temporal_features()
  - Concatenate with weather: actions_v2 = np.concatenate([actions_v1, temporal], axis=-1)
  - Set HDF5 attribute: f.attrs['preprocessing_version'] = 'v2'
  - Set HDF5 attribute: f.attrs['action_dim'] = 4

- [X] T011 [US1] Update Dataset.collate_fn() in src/siad/data/dataset.py
  - Check all samples have same action_dim: A = batch[0]["actions_rollout"].shape[1]
  - Verify consistency: assert all(sample["actions_rollout"].shape[1] == A for sample in batch)
  - Raise ValueError if mixed v1/v2 in same batch
  - Stack timestamps if not None: timestamps = np.stack([s["timestamps"] for s in batch if s["timestamps"] is not None])
  - Per contracts/dataset_api.md

- [X] T012 [US1] Create example training config at configs/train-temporal-v2.yaml
  - Copy from configs/train-baseline.yaml
  - Update: model.transition.action_dim: 4 (was 2)
  - Update: data.preprocessing_version: "v2"
  - Add comment: "# Temporal conditioning: month_sin/cos added to action vector"
  - Document expected improvements: "# Target: >20% reduction in false anomalies during seasonal transitions"

---

## Phase 4: User Story 2 (P2) - Multi-Step Rollout Stability

**Goal**: Maintain prediction quality across seasonal boundaries in long-horizon rollouts

**Why P2**: Enables longer prediction horizons, critical for planning applications

**Independent Test**: Run 6-step rollouts crossing seasonal boundaries, measure rollout error degradation

**Acceptance Criteria** (from spec.md):
- [ ] Nov→Apr rollout (crossing winter): error at step 6 < 15% higher than step 1 (vs >30% for baseline)
- [ ] Temporal model shows smoother error growth curve across all seasonal transitions

### Tasks

- [X] T013 [P] [US2] Implement checkpoint dimension upgrade in src/siad/model/world_model.py
  - Override load_state_dict() method
  - Detect checkpoint action_dim: checkpoint_dim = state_dict['action_encoder.mlp.0.weight'].shape[1]
  - If checkpoint_dim < self.action_encoder.action_dim: pad weights
  - Padding logic: new_weight[:, :checkpoint_dim] = old_weight, new_weight[:, checkpoint_dim:] = 0
  - Log: "Upgraded checkpoint: {checkpoint_dim}→{current_dim} dims (temporal features zero-initialized)"
  - Per contracts/model_api.md

- [X] T014 [P] [US2] Create test_checkpoint_upgrade.py in tests/unit/
  - Test: test_checkpoint_dimension_match() - Load v2 checkpoint into v2 model (no padding)
  - Test: test_checkpoint_dimension_upgrade() - Load v1 checkpoint into v2 model (with padding)
  - Test: test_zero_init_neutrality() - Verify padded weights are exactly 0.0
  - Test: test_checkpoint_downgrade_error() - Verify error when loading v2 into v1 model
  - Per contracts/model_api.md

- [X] T015 [US2] Create integration test in tests/integration/test_rollout_stability.py
  - Test: test_rollout_across_year_boundary() - Nov→Apr rollout (6 steps)
  - Verify month encoding updates each step: Nov, Dec, Jan, Feb, Mar, Apr
  - Verify Dec→Jan transition uses continuous sin/cos (no spike)
  - Measure error accumulation: assert error[5] / error[0] < 1.15  # <15% growth
  - Compare baseline vs temporal: assert temporal_error_growth < 0.5 * baseline_error_growth

---

## Phase 5: User Story 3 (P3) - Training Efficiency

**Goal**: Ensure temporal features don't increase training time or model size

**Why P3**: Operational constraint - ensures feature doesn't slow down research iteration

**Independent Test**: Measure training throughput (samples/sec) before and after temporal features

**Acceptance Criteria** (from spec.md):
- [ ] Training throughput decreases by <5%
- [ ] Model parameter count remains unchanged

### Tasks

- [X] T016 [P] [US3] Create performance benchmark in tests/integration/test_training_throughput.py
  - Test: test_model_parameter_count() - Count params for action_dim=2 vs action_dim=4
  - Verify: ActionEncoder params increase by exactly 128 (2 dims × 64 hidden)
  - Verify: Total model params increase by <0.01% (128 / ~100M)
  - Assert: param_count_v2 - param_count_v1 == 128

- [X] T017 [US3] Create throughput test in tests/integration/test_training_throughput.py
  - Test: test_training_throughput_v1_vs_v2()
  - Setup: Create small dataset (100 samples), train for 10 steps
  - Measure baseline (action_dim=2): samples_per_sec_v1
  - Measure temporal (action_dim=4): samples_per_sec_v2
  - Assert: (samples_per_sec_v1 - samples_per_sec_v2) / samples_per_sec_v1 < 0.05  # <5% degradation
  - Log: "Throughput: v1={v1:.2f} sps, v2={v2:.2f} sps, degradation={deg:.2%}"

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Finalize implementation with documentation and validation

### Tasks

- [X] T018 Create preprocessing manifest at configs/preprocessing_manifest_v2.json
  - Document version: "v2"
  - List features: {"weather": ["rain_anom", "temp_anom"], "temporal": ["month_sin", "month_cos"]}
  - Document changes from v1: "Added temporal features", "Action shape [B,H,2]→[B,H,4]"
  - Add backward_compatible: true
  - Add created_at: ISO 8601 timestamp
  - Add git_commit: current git SHA
  - Per data-model.md

---

## Dependencies

### User Story Dependencies

**Sequential** (must complete in order):
- Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (Polish)

**Within Phase 2** (Foundational):
- T003, T004 [P] (can run in parallel - different files)
- T005 (depends on T003 - uses compute_temporal_features)
- T006 [P] (can run in parallel with T003-T005)

**Within Phase 3** (US1):
- T007, T008, T009 [P] (all tests, can run in parallel)
- T010 (depends on T003, T005 - integrates temporal features)
- T011 (depends on T005 - extends collate function)
- T012 [P] (config, can run in parallel with T010-T011)

**Within Phase 4** (US2):
- T013, T014 [P] (can run in parallel - checkpoint logic + tests)
- T015 (depends on T010 - needs dataset with temporal features)

**Within Phase 5** (US3):
- T016, T017 [P] (both performance tests, can run in parallel)

### File Dependencies

| File | Tasks Modifying | Execution Order |
|------|----------------|-----------------|
| src/siad/data/preprocessing.py | T003, T010 | T003 → T010 |
| src/siad/model/actions.py | T004 | T004 (standalone) |
| src/siad/data/dataset.py | T005, T011 | T005 → T011 |
| src/siad/config/schema.py | T006 | T006 (standalone) |
| src/siad/model/world_model.py | T013 | T013 (standalone) |

**Parallel Execution Examples**:
- Phase 2: Run T003 + T004 + T006 in parallel (different files), then T005
- Phase 3: Run T007 + T008 + T009 + T012 in parallel (all tests/config), then T010 → T011
- Phase 4: Run T013 + T014 in parallel, then T015
- Phase 5: Run T016 + T017 in parallel

---

## Implementation Strategy

### MVP Scope (User Story 1 Only)

**Minimum Viable Product**: Implement only Phase 1-3 (Setup + Foundational + US1)
- Delivers core value: Seasonal transition accuracy
- 12 tasks total (T001-T012)
- Independently testable: Summer→autumn residual reduction
- Enables early validation of temporal features

**Incremental Delivery**:
1. **Week 1**: MVP (Phases 1-3) - Seasonal accuracy
2. **Week 2**: US2 (Phase 4) - Rollout stability
3. **Week 3**: US3 (Phase 5) - Efficiency validation + Polish

### Test-Driven Development

Per contracts, tests are organized by user story:

**US1 Tests** (T007-T009):
- Unit: temporal features, action encoder, dataset loading
- Validates: Shape contracts, temporal feature properties

**US2 Tests** (T014-T015):
- Unit: checkpoint upgrade logic
- Integration: rollout stability across year boundaries

**US3 Tests** (T016-T017):
- Integration: parameter count, training throughput

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] All 18 tasks completed and checked off
- [ ] All unit tests pass: `uv run pytest tests/unit/ -v`
- [ ] All integration tests pass: `uv run pytest tests/integration/ -v`
- [ ] Config validation works: action_dim=4 in configs/train-temporal-v2.yaml
- [ ] Backward compatibility: load v1 dataset/checkpoint with v2 model
- [ ] Documentation complete: preprocessing_manifest_v2.json exists
- [ ] No breaking API changes: existing code runs without modification
- [ ] Performance targets met:
  - [ ] Training throughput <5% degradation (US3)
  - [ ] Model params unchanged (except +128 for temporal features)
  - [ ] Rollout error reduction >10% on seasonal transitions (US1)
  - [ ] False anomaly rate reduction >20% (US1)

---

## Summary

**Total Tasks**: 18
**Parallelizable**: 8 tasks (T002, T003, T004, T006, T007, T008, T009, T012, T013, T014, T016, T017)
**MVP Tasks**: 12 (Phases 1-3, T001-T012)
**Estimated LOC**: ~370 (per plan.md)

**Files Modified**:
- src/siad/data/preprocessing.py (T003, T010)
- src/siad/model/actions.py (T004)
- src/siad/data/dataset.py (T005, T011)
- src/siad/config/schema.py (T006)
- src/siad/model/world_model.py (T013)

**Files Created**:
- configs/preprocess-v2.yaml (T001)
- configs/train-temporal-v2.yaml (T012)
- configs/preprocessing_manifest_v2.json (T018)
- tests/unit/test_temporal_features.py (T007)
- tests/unit/test_action_encoder.py (T008)
- tests/unit/test_dataset.py (T009)
- tests/unit/test_checkpoint_upgrade.py (T014)
- tests/integration/test_rollout_stability.py (T015)
- tests/integration/test_training_throughput.py (T016, T017)

**User Story Coverage**:
- US1 (P1 - Seasonal Accuracy): T007-T012 (6 tasks) ✓ Independently testable
- US2 (P2 - Rollout Stability): T013-T015 (3 tasks) ✓ Independently testable
- US3 (P3 - Training Efficiency): T016-T017 (2 tasks) ✓ Independently testable

**Next Step**: Run `/speckit.implement` to execute these tasks in order.
