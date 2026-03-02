# Tasks: SIAD MVP - Infrastructure Acceleration Detection

**Input**: Design documents from `/specs/001-siad-mvp/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Constitution Compliance**: All tasks MUST align with SIAD Constitution v1.0.0 principles (see `.specify/memory/constitution.md`). Specifically:
- Principle III (Testable Predictions) requires validation tasks for self-consistency, backtesting, and false-positive testing
- Principle V (Reproducible Pipelines) requires all processing stages be CLI-scriptable

**Tests**: Tests are NOT explicitly requested in the feature specification, so validation tasks are included but unit/integration tests are deferred to post-MVP hardening.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (per plan.md structure)
- Paths shown below use absolute structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Initialize Python 3.13+ project with UV dependency management (uv init, pyproject.toml)
- [ ] T002 [P] Create src/ directory structure per plan.md (data/, models/, detection/, validation/, visualization/, cli/)
- [ ] T003 [P] Create tests/ directory structure (contract/, integration/, unit/)
- [ ] T004 [P] Create data/ directory structure (raw/, preprocessed/, models/, outputs/)
- [ ] T005 [P] Create configs/ directory structure (aoi_examples/, scenarios/, validation_regions/)
- [ ] T006 [P] Install core dependencies via UV (earthengine-api, torch>=2.0, rasterio, numpy, matplotlib, h5py, pytest)
- [ ] T007 [P] Create .gitignore for data/ directory and Python artifacts
- [ ] T008 Create example AOI config in configs/aoi_examples/quickstart-demo.json per data-model.md AOI entity

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create Earth Engine authentication module in src/data/collectors/ee_auth.py
- [ ] T010 [P] Create base collector interface in src/data/collectors/base_collector.py
- [ ] T011 [P] Create Sentinel-1 SAR collector in src/data/collectors/sentinel1_collector.py (FR-002: VV/VH bands, monthly median)
- [ ] T012 [P] Create Sentinel-2 optical collector in src/data/collectors/sentinel2_collector.py (FR-003: B2/B3/B4/B8 bands, cloud masking, valid pixel fraction)
- [ ] T013 [P] Create VIIRS nighttime lights collector in src/data/collectors/viirs_collector.py (FR-004: monthly composite)
- [ ] T014 [P] Create CHIRPS rainfall collector in src/data/collectors/chirps_collector.py (FR-005: precipitation anomalies)
- [ ] T015 [P] Create ERA5 temperature collector in src/data/collectors/era5_collector.py (FR-006: optional 2m temp anomalies)
- [ ] T016 Create reprojection module in src/data/preprocessing/reprojection.py (FR-007: EPSG:3857 at 10m resolution)
- [ ] T017 [P] Create tiling module in src/data/preprocessing/tiling.py (FR-009: 256×256 pixel tiles)
- [ ] T018 [P] Create compositing module in src/data/preprocessing/compositing.py (monthly median composites per FR-002/FR-003)
- [ ] T019 [P] Create normalization module in src/data/preprocessing/normalization.py (FR-010: rainfall/temp z-score anomalies)
- [ ] T020 Create HDF5 dataset builder in src/data/loaders/dataset_builder.py (memory-mapped [N_tiles, N_timesteps, 8, 256, 256])
- [ ] T021 Create PyTorch Dataset class in src/data/loaders/siad_dataset.py (loads HDF5 with 6-month context + 6-month rollout windows)
- [ ] T022 Create observation encoder in src/models/encoders/observation_encoder.py (ConvNet or ViT per research.md, outputs latent z_t)
- [ ] T023 [P] Create target encoder with EMA in src/models/encoders/target_encoder.py (EMA-stabilized version for z_tilde, per FR-014)
- [ ] T024 [P] Create action encoder in src/models/encoders/action_encoder.py (MLP: rain_anom/temp_anom → latent u_t)
- [ ] T025 Create transition dynamics model in src/models/dynamics/transition_model.py (transformer or GRU: F(z_t, u_t) → z_{t+1}, per FR-011)
- [ ] T026 Create multi-step rollout loss in src/models/losses/rollout_loss.py (FR-013: recursive k=1..6 with cosine distance or MSE)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Detect Infrastructure Acceleration in Region (Priority: P1) 🎯 MVP

**Goal**: Implement core detection system producing heatmaps, hotspot rankings, and modality attribution

**Independent Test**: Provide historical imagery for a region with known construction events and verify the system flags these locations with "Structural" or "Activity" confidence tiers while not flagging agricultural regions

### Implementation for User Story 1

- [ ] T027 [P] [US1] Implement CLI collect command in src/cli/collect.py per contracts/cli-interface.md (calls collectors, exports GeoTIFFs)
- [ ] T028 [US1] Implement CLI preprocess command in src/cli/preprocess.py (calls reprojection, tiling, compositing, normalization, builds HDF5)
- [ ] T029 [US1] Implement CLI train command in src/cli/train.py (loads dataset, trains world model with 50 epochs default, saves checkpoints)
- [ ] T030 [US1] Create rollout engine in src/detection/rollouts/rollout_engine.py (loads model, runs recursive 6-month predictions conditioned on actions)
- [ ] T031 [P] [US1] Create acceleration score computation in src/detection/scoring/acceleration_scorer.py (FR-015: computes divergence from neutral baseline, EMA + slope formula)
- [ ] T032 [P] [US1] Create percentile flagging in src/detection/scoring/percentile_flagger.py (FR-016: flags tiles > 99th historical percentile)
- [ ] T033 [P] [US1] Create persistence filter in src/detection/scoring/persistence_filter.py (FR-017: requires ≥2 consecutive months)
- [ ] T034 [P] [US1] Create spatial clustering in src/detection/scoring/spatial_clusterer.py (FR-018: groups ≥3 connected tiles into hotspots)
- [ ] T035 [US1] Create modality-specific rollout in src/detection/attribution/modality_rollout.py (FR-019: re-runs rollouts with SAR-only, optical-only, lights-only inputs)
- [ ] T036 [US1] Create hotspot classifier in src/detection/attribution/hotspot_classifier.py (FR-020: assigns Structural/Activity/Environmental labels based on dominant modality)
- [ ] T037 [US1] Implement CLI detect command in src/cli/detect.py (orchestrates rollout → scoring → clustering → attribution, outputs acceleration_scores.csv + hotspots.json)
- [ ] T038 [P] [US1] Create heatmap generator in src/visualization/heatmaps/heatmap_generator.py (FR-025: spatial acceleration score percentiles via matplotlib)
- [ ] T039 [P] [US1] Create hotspot ranking visualization in src/visualization/heatmaps/hotspot_ranker.py (FR-026: ranked list with before/after thumbnails)
- [ ] T040 [US1] Implement CLI visualize command in src/cli/visualize.py (generates heatmap.png, hotspots_ranked.png, optional GeoJSON export)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (analyst can run collect → preprocess → train → detect → visualize to see acceleration heatmaps and hotspot rankings)

---

## Phase 4: User Story 2 - Compare Counterfactual Scenarios (Priority: P2)

**Goal**: Enable interactive scenario toggling (neutral/observed/extreme weather) to separate infrastructure from environmental changes

**Independent Test**: Run counterfactual rollouts with neutral weather (rain_anom=0, temp_anom=0) vs observed weather, verifying that infrastructure changes remain flagged while vegetation/water changes reduce under neutral scenarios

### Implementation for User Story 2

- [ ] T041 [P] [US2] Create scenario definition loader in src/detection/rollouts/scenario_loader.py (reads configs/scenarios/*.json for custom action sequences)
- [ ] T042 [US2] Extend rollout engine in src/detection/rollouts/rollout_engine.py to support multiple scenario inputs (neutral, observed, custom)
- [ ] T043 [US2] Update CLI detect command in src/cli/detect.py to accept --scenarios flag (neutral,observed,extreme_rain)
- [ ] T044 [P] [US2] Create divergence trajectory plotter in src/visualization/comparisons/divergence_plotter.py (FR-029: rollout trajectory in latent space per scenario)
- [ ] T045 [P] [US2] Create counterfactual heatmap overlay in src/visualization/comparisons/counterfactual_overlay.py (FR-029: divergence heatmap grid for neutral vs observed vs extreme)
- [ ] T046 [US2] Update CLI visualize command in src/cli/visualize.py to generate counterfactual_comparison.png (FR-028: interactive toggle simulation via side-by-side subplot grid)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (analyst can toggle scenarios and see how infrastructure changes remain robust across weather conditions)

---

## Phase 5: User Story 3 - Review Temporal Timeline of Acceleration (Priority: P3)

**Goal**: Generate temporal timeline visualizations showing when acceleration began and how residual scores evolved

**Independent Test**: Examine a region with known construction start date and verify timeline shows residual scores increasing from that month forward with persistence indicators

### Implementation for User Story 3

- [ ] T047 [P] [US3] Create residual time series extractor in src/detection/scoring/residual_extractor.py (per-tile residual scores over all timesteps)
- [ ] T048 [P] [US3] Create timeline plotter in src/visualization/timelines/timeline_plotter.py (FR-027: residual scores with persistence window highlighted, start date marked)
- [ ] T049 [US3] Create hotspot timeline aggregator in src/visualization/timelines/hotspot_timeline_aggregator.py (aggregates residuals across tiles in hotspot cluster)
- [ ] T050 [US3] Update CLI visualize command in src/cli/visualize.py to generate per-hotspot timelines in timelines/ subdirectory (one PNG per hotspot)

**Checkpoint**: All user stories should now be independently functional (analyst can explore heatmaps, toggle scenarios, and review timelines for each hotspot)

---

## Phase 6: Validation Implementation (Constitution Principle III)

**Purpose**: Implement three-gate validation suite per constitution Principle III (Testable Predictions NON-NEGOTIABLE)

- [ ] T051 [P] Create self-consistency validator in src/validation/consistency/self_consistency.py (FR-021: compares neutral scenario vs random actions)
- [ ] T052 [P] Create backtest validator in src/validation/backtest/backtest_runner.py (FR-022: validates against known construction regions from configs/validation_regions/*.json)
- [ ] T053 [P] Create false-positive validator in src/validation/false_positive/fp_tester.py (FR-023: measures FP rate on agriculture/monsoon regions)
- [ ] T054 Create validation metrics aggregator in src/validation/metrics_aggregator.py (FR-024: computes hit_rate, fp_rate, scenario_divergence_reduction per SC-002/SC-003/SC-004)
- [ ] T055 Implement CLI validate command in src/cli/validate.py (orchestrates three gates, outputs summary.json with pass/fail per success criteria)

**Checkpoint**: Validation suite complete - all three gates can be run to verify detection quality

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T056 [P] Create example quickstart AOI config in configs/aoi_examples/quickstart-demo.json with 50×50km bounds
- [ ] T057 [P] Create example validation config in configs/validation_regions/quickstart-demo.json with backtest and FP test regions
- [ ] T058 [P] Create example neutral scenario config in configs/scenarios/neutral.json (rain_anom=0, temp_anom=0 for all timesteps)
- [ ] T059 [P] Create example extreme_rain scenario config in configs/scenarios/extreme_rain.json (rain_anom=+2.5 for all timesteps)
- [ ] T060 [P] Add --help flags to all CLI commands (collect, preprocess, train, detect, validate, visualize)
- [ ] T061 [P] Add --dry-run flags to all CLI commands for input validation without execution
- [ ] T062 [P] Add --verbose flags to all CLI commands for detailed stderr logging
- [ ] T063 Create CLI contract tests in tests/contract/test_cli_collect.py (verifies stdin/stdout, --help, --dry-run, exit codes)
- [ ] T064 [P] Create CLI contract tests in tests/contract/test_cli_preprocess.py
- [ ] T065 [P] Create CLI contract tests in tests/contract/test_cli_train.py
- [ ] T066 [P] Create CLI contract tests in tests/contract/test_cli_detect.py
- [ ] T067 [P] Create CLI contract tests in tests/contract/test_cli_validate.py
- [ ] T068 [P] Create CLI contract tests in tests/contract/test_cli_visualize.py
- [ ] T069 Update README.md with installation instructions (UV setup, Earth Engine authentication)
- [ ] T070 Validate quickstart.md workflow end-to-end (run full pipeline from quickstart guide)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
- **Validation (Phase 6)**: Depends on User Story 1 completion (needs detection outputs to validate)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 detection but independently testable with neutral vs observed scenarios
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses US1 detection outputs but can generate timelines independently

### Within Each User Story

- CLI commands depend on their underlying modules (e.g., T027 collect depends on T011-T015 collectors)
- Detection pipeline flows: rollout (T030) → scoring (T031-T034) → attribution (T035-T036) → CLI detect (T037)
- Visualization depends on detection outputs (T037 must complete before T038-T040)

### Parallel Opportunities

- **Setup tasks (Phase 1)**: T002-T007 can all run in parallel (different directories)
- **Foundational collectors (Phase 2)**: T011-T015 can run in parallel (independent Earth Engine wrappers)
- **Foundational preprocessing (Phase 2)**: T016-T019 can run in parallel (independent preprocessing modules)
- **Foundational encoders (Phase 2)**: T023-T024 can run in parallel (separate encoder types)
- **US1 scoring modules (Phase 3)**: T031-T034 can run in parallel (different scoring/filtering logic)
- **US1 visualization (Phase 3)**: T038-T039 can run in parallel (independent matplotlib generators)
- **US2 visualization (Phase 4)**: T044-T045 can run in parallel (separate visualization types)
- **US3 timeline components (Phase 5)**: T047-T048 can run in parallel (data extraction vs plotting)
- **Validation gates (Phase 6)**: T051-T053 can run in parallel (independent validation logic)
- **Polish configs (Phase 7)**: T056-T059 can run in parallel (JSON config files)
- **CLI flags (Phase 7)**: T060-T062 can run in parallel (separate flag implementations)
- **Contract tests (Phase 7)**: T063-T068 can run in parallel (independent test files)

---

## Parallel Example: User Story 1 (Detection)

```bash
# After Foundational phase completes, launch US1 scoring modules in parallel:
Task: "Create acceleration score computation in src/detection/scoring/acceleration_scorer.py"
Task: "Create percentile flagging in src/detection/scoring/percentile_flagger.py"
Task: "Create persistence filter in src/detection/scoring/persistence_filter.py"
Task: "Create spatial clustering in src/detection/scoring/spatial_clusterer.py"

# Then launch US1 visualization modules in parallel:
Task: "Create heatmap generator in src/visualization/heatmaps/heatmap_generator.py"
Task: "Create hotspot ranking visualization in src/visualization/heatmaps/hotspot_ranker.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T026) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T027-T040)
4. **STOP and VALIDATE**: Test User Story 1 independently using quickstart.md workflow
5. Run Phase 6: Validation (T051-T055) to verify detection quality gates
6. Deploy/demo if validation passes (SC-002: ≥80% hit rate, SC-003: <20% FP rate)

**MVP Checkpoint**: After Phase 3 + Phase 6, you have a complete, validated detection system that produces heatmaps and hotspot rankings. This is shippable.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Run validation → Deploy/Demo (MVP!)
3. Add User Story 2 → Test scenario toggling independently → Deploy/Demo (enhanced MVP with counterfactual reasoning)
4. Add User Story 3 → Test timeline generation independently → Deploy/Demo (full MVP with temporal analysis)
5. Add Polish (Phase 7) → Contract tests + configs → Final release

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T026)
2. Once Foundational is done:
   - Developer A: User Story 1 (T027-T040) - Detection core
   - Developer B: User Story 2 (T041-T046) - Counterfactual scenarios
   - Developer C: User Story 3 (T047-T050) - Timeline visualization
   - Developer D: Validation suite (T051-T055)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability (US1, US2, US3)
- Each user story should be independently completable and testable
- Constitution Principle III (Testable Predictions) enforced via Phase 6 validation tasks
- Constitution Principle V (Reproducible Pipelines) enforced via CLI-driven design and --dry-run flags
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Count Summary

- **Total Tasks**: 70
- **Setup Phase**: 8 tasks
- **Foundational Phase**: 18 tasks (CRITICAL blocking phase)
- **User Story 1 (P1)**: 14 tasks (MVP core)
- **User Story 2 (P2)**: 6 tasks
- **User Story 3 (P3)**: 4 tasks
- **Validation Phase**: 5 tasks (constitution-mandated)
- **Polish Phase**: 15 tasks

**Parallel Opportunities**: 42 tasks marked [P] can run in parallel when dependencies are met

**MVP Scope**: Phases 1-3 + Phase 6 = 45 tasks for shippable detection system
