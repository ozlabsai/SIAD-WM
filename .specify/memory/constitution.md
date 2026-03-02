<!--
SYNC IMPACT REPORT
==================
Version Change: [NEW] → 1.0.0
Action: Initial constitution creation

Principles Defined:
  1. Data-Driven Foundation
  2. Counterfactual Reasoning
  3. Testable Predictions (NON-NEGOTIABLE)
  4. Interpretable Attribution
  5. Reproducible Pipelines

Sections Added:
  - Technical Constraints
  - Development Workflow
  - Governance

Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md - UPDATED (added Constitution Check section with v1.0.0 principles)
  ✅ .specify/templates/spec-template.md - VALIDATED (no changes needed - focuses on user requirements)
  ✅ .specify/templates/tasks-template.md - UPDATED (added constitution compliance note referencing Principles III and V)
  ✅ .specify/templates/commands/*.md - VALIDATED (no command files exist yet)

Follow-up TODOs:
  - None (all placeholders resolved)

Notes:
  - Initial version ratified based on PRD requirements
  - Principles derived from MVP scope and red-team risk hardening needs
  - Governance emphasizes MVP-first discipline and claims boundaries
-->

# SIAD Constitution

## Core Principles

### I. Data-Driven Foundation

Multi-modal satellite data (Sentinel-1 SAR, Sentinel-2 optical, VIIRS nighttime lights) MUST be preprocessed consistently with temporal alignment and spatial registration before model training.

**Rationale**: Inconsistent preprocessing creates artifacts that contaminate acceleration detection. The world model cannot distinguish structural changes from data misalignment if inputs are not normalized to a common spatiotemporal grid. This principle ensures that all downstream analysis operates on a unified data foundation.

### II. Counterfactual Reasoning

World model rollouts MUST support scenario conditioning (rain/temp anomalies) to separate environmental changes from structural changes. Claims of causality from weather to construction are prohibited.

**Rationale**: Without counterfactual baselines, the detector cannot distinguish seasonal vegetation cycles or flood responses from infrastructure acceleration. Scenario knobs (rain_anom, temp_anom) provide "what-if" rollouts that explain natural variability, reducing false positives. However, these actions do not cause construction—they only control vegetation/water dynamics.

### III. Testable Predictions (NON-NEGOTIABLE)

Model outputs (acceleration scores, hotspot rankings, timelines) MUST be validated through self-consistency checks, backtesting on known regions, and false-positive testing before deployment.

**Rationale**: Geospatial ML without ground-truth labels requires adversarial validation. Self-consistency confirms that neutral scenarios match typical evolution. Backtesting on known "big build" regions provides visual verification. False-positive testing on agriculture/monsoon regions measures robustness. No model leaves evaluation without passing all three gates.

### IV. Interpretable Attribution

Acceleration detections MUST include modality-specific attribution (Structural/Activity/Environmental) using SAR-optical-lights decomposition to enable analyst triage.

**Rationale**: A single acceleration score without attribution creates "black box" alerts that analysts cannot trust. By recomputing scores with SAR-only, optical-only, and lights-only inputs, the system produces three labels: Structural (SAR + lights), Activity (lights-heavy), Environmental (optical NDVI-like). This triages false positives and makes detections defensible.

### V. Reproducible Pipelines

All preprocessing (tiling, compositing, normalization), training (encoder-dynamics-loss), and inference (rollout-scoring) MUST be scriptable via CLI with deterministic outputs for auditing.

**Rationale**: Research code that cannot be re-run is not credible. UV-managed Python 3.13 ensures dependency reproducibility. CLI-driven workflows (stdin/args → stdout, errors → stderr) enable pipeline chaining, testing, and auditing. Every stage from raw Earth Engine data to final heatmaps must be executable as a documented command.

## Technical Constraints

- **Python 3.13+ with UV dependency management** (MUST): UV ensures lockfile reproducibility and fast environment setup per user CLAUDE.md guidance.
- **Earth Engine catalog data sources preferred**: Sentinel-1, Sentinel-2, VIIRS, CHIRPS/ERA5 provide global coverage with consistent APIs.
- **10m spatial resolution target for S1/S2**: Balances detail with computational feasibility for 50×50 km AOI.
- **Monthly temporal cadence minimum**: Reduces cloud artifacts and aligns with VIIRS monthly composites.
- **DRY and KISS code principles**: Code should be "engineered enough"—abstractions only where reuse is clear, simplicity over premature optimization.

## Development Workflow

- **MVP-first discipline**: Single AOI, 36 months history, 6-month rollout horizon. No global model, no weekly cadence, no pixel-level generation until MVP validates core hypotheses.
- **Validation gates enforced sequentially**:
  1. Self-consistency checks (neutral scenario plausibility)
  2. Backtesting on known construction regions (visual verification)
  3. False-positive testing on agriculture/monsoon regions (robustness)
- **Red-team risk hardening before feature expansion**: Address cloud artifacts, seasonality floods, rollout drift, and "just change detection" criticisms with explicit mitigations (S2 valid mask, tile-local percentile scoring, modality attribution, scheduled sampling).
- **Claims boundary enforcement**: Credible claim is "persistent deviation detection with counterfactual baselining." Prohibited claims: intent inference, actor identification, causal attribution from weather to construction, tactical surveillance.

## Governance

This constitution supersedes all ad-hoc development decisions. When implementation choices conflict with principles, the constitution prevails—either justify an amendment or revise the implementation.

**Amendment procedure**:
1. Propose change with rationale (why current principle blocks progress or is incorrect)
2. Document impact on existing code/artifacts
3. Increment version per semantic versioning:
   - MAJOR: Backward-incompatible principle removal/redefinition
   - MINOR: New principle or material expansion
   - PATCH: Clarifications, wording, non-semantic refinements
4. Update all dependent templates (plan, spec, tasks, commands) to reflect amendment
5. Commit with migration plan if breaking changes

**Compliance review**:
- All PRs/code reviews MUST verify adherence to Core Principles (especially III and V)
- Complexity additions MUST be justified against MVP scope and KISS principle
- New features MUST pass validation gates before merging

**Version**: 1.0.0 | **Ratified**: 2026-02-28 | **Last Amended**: 2026-02-28
