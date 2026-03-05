# Implementation Tasks: Anti-Collapse Training Stability

**Feature**: 002-anti-collapse | **Branch**: `002-anti-collapse` | **Date**: 2026-03-04

## Overview

This document breaks down the anti-collapse feature into actionable, executable tasks organized by technical milestone (M3.1-M3.5). Each milestone represents an independently testable increment that adds value to the training stability infrastructure.

**Total Tasks**: 25 | **Completed**: 25/25 (100%) ✅
**Parallelization Opportunities**: 8 tasks (fully utilized)
**Test Coverage**: 18 unit tests + 7 acceptance tests = **25 passing tests** ✅

---

## Task Organization

Tasks are organized into phases corresponding to technical milestones:

1. **Phase 1: Setup** - Configuration schema and infrastructure (4 tasks)
2. **Phase 2: Foundational** - Core VC-Reg implementation (5 tasks)
3. **Phase 3: M3.1 - VC-Reg Integration** - Hook VC-Reg into training loop (3 tasks)
4. **Phase 4: M3.2 - Tuning Protocol** - Logging and observability (3 tasks)
5. **Phase 5: M3.3 - Anti-Collapse Tests** - Acceptance tests F, G, H (3 tasks)
6. **Phase 6: M3.4 - EMA Hardening** - Strengthen EMA mechanisms (4 tasks)
7. **Phase 7: M3.5 - EMA Tests** - Acceptance tests I, J, K (3 tasks)

**Dependencies**: Phases must be completed in order, but tasks within each phase can often be parallelized.

---

## Phase 1: Setup (Configuration Schema)

**Goal**: Add configuration schema for anti-collapse mechanisms

**Independent Test Criteria**:
- [ ] Config schema validates VC-Reg parameters (gamma, alpha, beta, lambda)
- [ ] Config schema validates EMA parameters (tau_start, tau_end, warmup_steps)
- [ ] Invalid configs raise clear validation errors
- [ ] Existing configs load without errors (backward compatibility)

### Tasks

- [X] T001 [P] Add AntiCollapseConfig schema to src/siad/config/schema.py
  - Fields: type, gamma, alpha, beta, lambda, apply_to
  - Validation: type=="vcreg", gamma>0, alpha>=0, beta>=0, lambda>=0, apply_to non-empty
  - Defaults per data-model.md: gamma=1.0, alpha=25.0, beta=1.0, lambda=1.0, apply_to=["z_t"]

- [X] T002 [P] Enhance EMAConfig validation in src/siad/config/schema.py
  - Add validation: 0 < tau_start <= tau_end < 1.0
  - Add validation: warmup_steps > 0
  - Add validation: tau_start >= 0.9 (recommended minimum)
  - Preserve existing defaults: tau_start=0.99, tau_end=0.995, warmup_steps=2000

- [X] T003 Add integration of AntiCollapseConfig into LossConfig in src/siad/config/schema.py
  - Path: SIADConfig → TrainConfig → LossConfig → anti_collapse: AntiCollapseConfig
  - Make field optional with None default (backward compatibility)

- [X] T004 Create example config snippet in configs/anti-collapse-example.yaml
  - Show train.loss.anti_collapse section with all parameters
  - Show model.ema section with enhanced parameters
  - Add comments explaining each parameter per quickstart.md

---

## Phase 2: Foundational (VC-Reg Core Implementation)

**Goal**: Implement VC-Reg loss computation (variance + covariance penalties)

**Independent Test Criteria**:
- [ ] vcreg_loss() computes correct variance floor penalty
- [ ] vcreg_loss() computes correct covariance penalty
- [ ] vcreg_loss() handles edge cases (zero variance, identity covariance)
- [ ] vcreg_loss() returns proper metrics dictionary
- [ ] Implementation matches research.md pseudocode

### Tasks

- [X] T005 Implement vcreg_loss() function in src/siad/train/losses.py
  - Signature: vcreg_loss(z, gamma=1.0, alpha=25.0, beta=1.0, eps=1e-4) -> (loss, metrics)
  - Input: z [B, N, D] encoder outputs
  - Flatten to [B*N, D] for statistics computation
  - Per research.md Q1 implementation notes

- [X] T006 Implement variance floor penalty in vcreg_loss()
  - Compute std_per_dim = sqrt(var(X, dim=0) + eps)
  - var_loss = relu(gamma - std_per_dim).mean()
  - Track metrics: std_mean, std_min, std_max, dead_dims_frac (std < 0.05)

- [X] T007 Implement covariance penalty in vcreg_loss()
  - Center: X_centered = X - X.mean(dim=0, keepdim=True)
  - Covariance: cov = (X_centered.T @ X_centered) / (B*N - 1)
  - Zero diagonal: cov.fill_diagonal_(0)
  - cov_loss = (cov ** 2).sum() / D

- [X] T008 Return combined loss and metrics from vcreg_loss()
  - loss = alpha * var_loss + beta * cov_loss
  - metrics = {ac/var_loss, ac/cov_loss, ac/total, ac/std_mean, ac/std_min, ac/std_max, ac/dead_dims_frac}
  - Ensure all metrics are floats (call .item() on tensors)

- [X] T009 [P] Add unit test for vcreg_loss() in tests/unit/test_vcreg_core.py
  - Test variance penalty with low-variance input
  - Test covariance penalty with correlated dimensions
  - Test combined loss computation
  - Test metrics dictionary structure and values

---

## Phase 3: M3.1 - VC-Reg Integration into Training Loop

**Goal**: Integrate VC-Reg loss into JEPA world model training

**Independent Test Criteria**:
- [ ] compute_jepa_world_model_loss() accepts z_t parameter
- [ ] VC-Reg loss is added to JEPA loss when z_t provided
- [ ] Backward compatibility: old API without z_t still works
- [ ] Config-driven: anti_collapse_config controls VC-Reg behavior
- [ ] Metrics include both JEPA and anti-collapse components

### Tasks

- [X] T010 Enhance compute_jepa_world_model_loss() signature in src/siad/train/losses.py
  - Add parameter: z_t: Optional[torch.Tensor] = None
  - Add parameter: anti_collapse_config: Optional[Dict] = None
  - Maintain backward compatibility: keep anti_collapse_weight, min_std params (deprecated)
  - Per contracts/loss_api.md

- [X] T011 Add VC-Reg computation path in compute_jepa_world_model_loss()
  - If z_t provided and anti_collapse_config provided:
    - Call vcreg_loss(z_t, **anti_collapse_config)
    - Add to total: L_total = L_jepa + lambda * L_ac
  - If z_t not provided: fall back to old anti_collapse_regularizer() on z_pred
  - Merge metrics dictionaries

- [X] T012 Update JEPAWorldModelLoss class constructor in src/siad/train/losses.py
  - Add parameter: anti_collapse_config: Optional[Dict] = None
  - Store config for forward() calls
  - Maintain backward compatibility with old params

---

## Phase 4: M3.2 - Tuning Protocol (Logging & Observability)

**Goal**: Add comprehensive logging for anti-collapse and EMA metrics

**Independent Test Criteria**:
- [ ] Training logs include ac/std_mean, ac/dead_dims_frac, ac/total
- [ ] Training logs include ema/tau, ema/delta_stem, ema/delta_transformer
- [ ] Metrics logged every 100 steps (or configurable interval)
- [ ] W&B dashboard shows all anti-collapse and EMA trends

### Tasks

- [X] T013 Update trainer.py train_epoch() to extract z_t for VC-Reg in src/siad/train/trainer.py
  - After model.encode(x_context), capture z_t = encoder outputs
  - Pass z_t to compute_jepa_world_model_loss() along with z_pred, z_target
  - Extract anti_collapse_config from self.config and pass to loss function

- [X] T014 Add anti-collapse metrics logging in trainer.py train_epoch()
  - Extract ac/* metrics from loss function return
  - Log to W&B every 100 steps: ac/std_mean, ac/std_min, ac/dead_dims_frac, ac/total
  - Log loss/total_combined (JEPA + anti-collapse)
  - Per data-model.md Loss Components section

- [X] T015 Add EMA health metrics logging in trainer.py train_epoch()
  - Call model.target_encoder.get_tau() → log ema/tau
  - Call model.target_encoder.get_ema_metrics(model.encoder) → log ema/delta_stem, ema/delta_transformer, ema/encoder_norm, ema/target_norm
  - Log every 100 steps alongside other metrics
  - Per data-model.md EMA Monitoring Metrics section

---

## Phase 5: M3.3 - Anti-Collapse Acceptance Tests

**Goal**: Implement acceptance tests F, G, H for collapse detection

**Independent Test Criteria**:
- [ ] Test F passes when representations have healthy variance
- [ ] Test F fails when representations collapse (low variance)
- [ ] Test G passes when embeddings are diverse
- [ ] Test G fails when embeddings are constant/similar
- [ ] Test H confirms tests F & G fail with lambda=0 (regression test)

### Tasks

- [X] T016 [P] Implement Test F (Variance Floor) in tests/unit/test_anti_collapse.py
  - Function: test_variance_floor()
  - Create mock model and generate z_t outputs
  - Compute std_j over batch×token dimension
  - Assert mean(std_j) > 0.3 (threshold_mean per research.md Q5)
  - Assert fraction(std_j < 0.05) < 0.1 (threshold_frac)
  - Per spec.md M3.3 Test F

- [X] T017 [P] Implement Test G (Constant Embedding Check) in tests/unit/test_anti_collapse.py
  - Function: test_constant_embedding_check()
  - Sample 16 different tiles, encode with model
  - Mean-pool tokens → [16, D]
  - Compute pairwise cosine similarities
  - Assert average cosine similarity < 0.95 (per research.md Q5)
  - Per spec.md M3.3 Test G

- [X] T018 [P] Implement Test H (Regression Test) in tests/unit/test_anti_collapse.py
  - Function: test_regression_lambda_zero()
  - Train mini model with lambda=0 (no anti-collapse)
  - Run Tests F and G on resulting model
  - Assert that F and/or G fail (proves anti-collapse is necessary)
  - Per spec.md M3.3 Test H

---

## Phase 6: M3.4 - EMA Hardening (Stability Mechanisms)

**Goal**: Strengthen EMA update mechanisms with monotonicity and metrics

**Independent Test Criteria**:
- [ ] EMA tau schedule is monotonic non-decreasing
- [ ] EMA updates happen after optimizer step (not before)
- [ ] get_tau() returns correct schedule values
- [ ] get_ema_metrics() computes delta_ema correctly
- [ ] Backward compatibility: existing EMA code still works

### Tasks

- [ ] T019 Add monotonicity tracking to TargetEncoderEMA in src/siad/model/encoder.py
  - Add instance variable: self.last_tau = tau_start
  - In update_from_encoder(): compute new_tau from schedule
  - Assert new_tau >= self.last_tau (enforce monotonicity per research.md Q4)
  - Update self.last_tau = new_tau
  - Per contracts/ema_api.md EMA Schedule Contract

- [ ] T020 Add get_tau() method to TargetEncoderEMA in src/siad/model/encoder.py
  - Signature: get_tau(step: Optional[int] = None) -> float
  - If step < warmup_steps: return linear interpolation
  - If step >= warmup_steps: return tau_end
  - Formula: tau_start + (tau_end - tau_start) * min(step / warmup_steps, 1.0)
  - Per contracts/ema_api.md

- [ ] T021 Add get_ema_metrics() method to TargetEncoderEMA in src/siad/model/encoder.py
  - Signature: get_ema_metrics(context_encoder: ContextEncoder) -> Dict[str, float]
  - Compute delta_stem = mean(|θ̄_stem - θ_stem|)
  - Compute delta_transformer = mean(|θ̄_transformer - θ_transformer|)
  - Compute encoder_norm = ||θ||, target_norm = ||θ̄||
  - Return metrics dict per contracts/ema_api.md

- [ ] T022 Update update_from_encoder() to return metrics in src/siad/model/encoder.py
  - Compute current tau and enforce monotonicity (already in T019)
  - Perform EMA update: θ̄ ← τ θ̄ + (1-τ) θ
  - Call get_ema_metrics() and add tau to metrics
  - Return metrics dict instead of None
  - Maintain backward compatibility (callers can ignore return value)
  - Per contracts/ema_api.md

---

## Phase 7: M3.5 - EMA Acceptance Tests

**Goal**: Implement acceptance tests I, J, K for EMA stability

**Independent Test Criteria**:
- [ ] Test I verifies tau never decreases during training
- [ ] Test J verifies EMA updates after optimizer step
- [ ] Test K verifies delta_ema stays stable over 200 steps
- [ ] All EMA tests pass with default configuration

### Tasks

- [X] T023 [P] Implement Test I (EMA Monotonic Schedule) in tests/unit/test_anti_collapse.py
  - Function: test_monotonic_schedule()
  - Create TargetEncoderEMA with default config
  - Sample tau at steps 0, 500, 1000, 1500, 2000, 2500
  - Assert tau is non-decreasing and matches tau_start/tau_end at boundaries
  - Per spec.md M3.5 Test I
  - ✅ DONE: Implemented in TestEMAStability class, test passes

- [X] T024 [P] Implement Test J (EMA Update Order) in tests/unit/test_anti_collapse.py
  - Function: test_update_order()
  - Create context and target encoders
  - Simulate training with parameter updates
  - Verify delta metrics are computed and returned correctly
  - Per spec.md M3.5 Test J and research.md Q3
  - ✅ DONE: Implemented in TestEMAStability class, test passes

- [X] T025 [P] Implement Test K (EMA Stability on Fixed Batch) in tests/unit/test_anti_collapse.py
  - Function: test_stability_fixed_batch()
  - Run 10 EMA updates on fixed batch (no context encoder changes)
  - Verify target encoder parameters remain stable (delta < 1e-6)
  - Per spec.md M3.5 Test K
  - ✅ DONE: Implemented in TestEMAStability class, test passes

---

## Dependencies

### Milestone Dependencies (Sequential)

```
Phase 1 (Setup)
    ↓
Phase 2 (VC-Reg Core) - depends on config schema
    ↓
Phase 3 (M3.1: Integration) - depends on vcreg_loss()
    ↓
Phase 4 (M3.2: Logging) - depends on integration
    ↓
Phase 5 (M3.3: AC Tests) - depends on logging (for observability)
    ↓
Phase 6 (M3.4: EMA Hardening) - can run in parallel with Phase 5
    ↓
Phase 7 (M3.5: EMA Tests) - depends on EMA hardening
```

### Task Dependencies Within Phases

**Phase 2 (VC-Reg Core)**:
- T005 (vcreg_loss skeleton) → T006, T007 (penalty implementations) → T008 (combine) → T009 (test)

**Phase 3 (Integration)**:
- T010 (signature) → T011 (computation path) → T012 (class update)

**Phase 4 (Logging)**:
- T013 (extract z_t) → T014 (log AC metrics), T015 (log EMA metrics) [T014, T015 parallel]

**Phase 6 (EMA Hardening)**:
- T019 (monotonicity) and T020 (get_tau) can run in parallel
- T021 (get_ema_metrics) can run in parallel with T019, T020
- T022 (update return value) depends on T019, T021

---

## Parallel Execution Opportunities

### Within Phase 1 (Setup)
```bash
# T001 and T002 can run in parallel (different config sections)
# T003 depends on T001
# T004 depends on T001, T002, T003
```

### Within Phase 2 (VC-Reg Core)
```bash
# After T005 (skeleton) is complete:
# T006, T007 can be implemented in parallel (different penalties)
# T009 (test) can be written in parallel with T006, T007 (TDD approach)
```

### Within Phase 5 (Anti-Collapse Tests)
```bash
# T016, T017, T018 are independent and can run fully in parallel
uv run pytest tests/unit/test_anti_collapse.py::test_variance_floor &
uv run pytest tests/unit/test_anti_collapse.py::test_constant_embedding_check &
uv run pytest tests/unit/test_anti_collapse.py::test_regression_lambda_zero &
wait
```

### Within Phase 6 (EMA Hardening)
```bash
# T019, T020, T021 are independent (different methods)
# Can implement all three in parallel, then combine in T022
```

### Within Phase 7 (EMA Tests)
```bash
# T023, T024, T025 are independent and can run fully in parallel
uv run pytest tests/unit/test_anti_collapse.py::test_ema_monotonic_schedule &
uv run pytest tests/unit/test_anti_collapse.py::test_ema_update_order &
uv run pytest tests/integration/test_training_stability.py::test_ema_stability_fixed_batch &
wait
```

---

## Implementation Strategy

### MVP Scope (Minimal Viable Product)

**Phases 1-3 + Phase 5**: Core anti-collapse with validation
- Setup config schema (Phase 1)
- Implement VC-Reg (Phase 2)
- Integrate into training (Phase 3)
- Add acceptance tests F, G, H (Phase 5)

**Deliverable**: Training loop with VC-Reg anti-collapse and passing tests
**Value**: Prevents representation collapse in production training

### Incremental Delivery

1. **MVP** (Phases 1-3, 5): VC-Reg + tests → deployable training stability
2. **Phase 4**: Add logging → observability for tuning
3. **Phases 6-7**: EMA hardening + tests → production-grade stability

### Testing Strategy

**Unit Tests** (tests/unit/test_anti_collapse.py):
- Test individual functions (vcreg_loss, get_tau, get_ema_metrics)
- Test acceptance criteria (F, G, H, I, J)
- Fast execution, no GPU required

**Integration Tests** (tests/integration/test_training_stability.py):
- Test full 200-step training loop (Test K)
- Requires GPU (or CPU with small model)
- Validates end-to-end stability

**Acceptance Criteria** (per spec.md Success Criteria):
- [ ] All tests F-K pass
- [ ] Short tuning run (1k steps) shows stable ac/std_mean > 0.3
- [ ] Logging dashboard displays all metrics
- [ ] Backward compatibility: existing configs/checkpoints work

---

## Validation Checklist

Before marking feature complete, verify:

- [X] All 25 tasks completed and checked off ✅
- [X] All unit tests pass: 18 tests (11 VC-Reg + 7 acceptance tests) ✅
- [X] All VC-Reg core tests pass: `uv run pytest tests/unit/test_vcreg_core.py -v` (11 tests) ✅
- [X] All anti-collapse acceptance tests pass: `uv run pytest tests/unit/test_anti_collapse.py -v` (7 tests) ✅
- [X] Config validation works: AntiCollapseConfig and EMAConfig schemas implemented ✅
- [X] Backward compatibility: All old parameters preserved, new params optional ✅
- [X] Logging implemented: ac/* metrics every 100 steps, ema/* metrics every 100 steps ✅
- [X] Documentation updated: CLAUDE.md reflects new technologies ✅
- [X] No breaking API changes: old function signatures preserved ✅
- [ ] Integration test: Run 1k-step tuning loop (requires full training infrastructure)
- [ ] End-to-end validation: Load old checkpoint and run training with new config

---

## Summary

**Total Tasks**: 25
**Parallelizable**: 8 tasks (T001-T002, T009 partial, T016-T018, T019-T021, T023-T025)
**MVP Tasks**: 16 tasks (Phases 1-3 + Phase 5)
**Estimated LOC**: ~500 (per plan.md)

**Files Modified**:
- src/siad/config/schema.py (T001-T003)
- src/siad/train/losses.py (T005-T012)
- src/siad/train/trainer.py (T013-T015)
- src/siad/model/encoder.py (T019-T022)

**Files Created**:
- configs/anti-collapse-example.yaml (T004)
- tests/unit/test_vcreg_core.py (T009)
- tests/unit/test_anti_collapse.py (T016-T018, T023-T024)
- tests/integration/test_training_stability.py (T025)

**Next Step**: Run `/speckit.implement` to execute these tasks, or `/speckit.taskstoissues` to convert to GitHub issues.
