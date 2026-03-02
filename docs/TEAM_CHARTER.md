# SIAD MVP - Team Charter & Task Assignments

**Date**: 2026-02-28
**Lead**: Orchestration Agent
**Constitution**: `.specify/memory/constitution.md` v1.0.0
**Tasks Source**: `specs/001-siad-mvp/tasks.md` (70 tasks total)

## Mission

Implement SIAD (Strategic Infrastructure Acceleration Detector) World Model MVP in Python using Earth Engine for monthly satellite composites, PyTorch for action-conditioned world model training, and neutral-scenario counterfactual rollouts for acceleration detection.

## Team Structure (6 Agents + Lead)

### File Ownership Boundaries (STRICT - No Overlap)

| Agent | Owns | Cannot Touch |
|-------|------|--------------|
| **Data/GEE Pipeline** | `src/siad/data/`, `scripts/export_*.py` | model/, detect/, report/ |
| **Actions/Context** | `src/siad/actions/` | data/collectors/, model/, detect/ |
| **World Model/Training** | `src/siad/model/`, `src/siad/train/` | data/, detect/, report/ |
| **Detection/Attribution/Eval** | `src/siad/detect/`, `src/siad/eval/` | data/, model/, train/ |
| **Infra/DevEx** | Root configs, `pyproject.toml`, `src/siad/cli/`, CI | All module internals |
| **Reporting/UI** | `src/siad/report/`, optional `web/` | data/, model/, detect/ |

### Agent Responsibilities

#### 1. Data/GEE Pipeline Agent
**Tasks**: T009-T015, T016-T020, T027
- Implement Earth Engine collectors for S1/S2/VIIRS/CHIRPS/ERA5
- Monthly compositing with median aggregation
- AOI tiling to 256×256 pixels at 10m resolution
- Export to GCS with layout: `gs://<bucket>/siad/<aoi_id>/<tile_id>/<YYYY-MM>.tif`
- Generate `manifest.jsonl` with band order contract
- **Deliverable**: Reproducible export pipeline + smoke test (1 tile × 2 months)

#### 2. Actions/Context Agent
**Tasks**: T014-T015 (extended), T019 (anomaly computation)
- CHIRPS monthly rainfall aggregation → anomaly (month-of-year climatology)
- Optional ERA5 temperature anomaly
- Inject anomalies into manifest.jsonl rows
- **Deliverable**: Verified anomalies for 12+ months with sanity plots

#### 3. World Model/Training Agent
**Tasks**: T021-T026, T029
- JEPA-style action-conditioned world model (observation encoder, EMA target encoder, action encoder, transition dynamics)
- Multi-step rollout loss (H=6) with recursive prediction
- PyTorch Dataset reading GeoTIFF shards from manifest
- Training script with checkpointing
- **Deliverable**: Training run on sample data (few tiles) → checkpoints + metrics

#### 4. Detection/Attribution/Eval Agent
**Tasks**: T030-T036, T051-T053, T054-T055
- Neutral-scenario counterfactual rollout scoring
- Tile-local percentile normalization (99th threshold)
- Persistence filter (≥2 months) + spatial clustering (≥3 tiles)
- Onset time estimation
- Modality attribution (SAR/Optical/VIIRS) → Structural/Activity/Environmental labels
- False-positive battery (agriculture AOI, river AOI) evaluation
- **Deliverable**: Hotspot JSON + per-month score rasters for sample AOI

#### 5. Infra/DevEx Agent
**Tasks**: T001-T008, T027-T029 (CLI wrappers), T060-T062, T063-T068
- UV/Poetry project setup (pyproject.toml, Python 3.13+)
- CLI entrypoints: `siad export`, `siad train`, `siad detect`, `siad report`
- Config YAML schema (configs/)
- Logging, deterministic runs (seed setting)
- CI smoke tests
- **Deliverable**: Working CLI + CI smoke test passing

#### 6. Reporting/UI Agent
**Tasks**: T038-T040, T047-T050, T056-T059, T069-T070
- HTML/Markdown briefing-grade report
- AOI map thumbnails, hotspot cards, before/after panels
- Timelines, scenario comparison snapshots
- Optional: minimal web viewer
- **Deliverable**: `siad report` generates report from detection outputs

---

## Global Technical Requirements (Acceptance Criteria)

### Data Contract: State Tensor Band Order (MUST BE CONSISTENT EVERYWHERE)

```python
BAND_ORDER_V1 = [
    "S2_B2",      # Blue (10m)
    "S2_B3",      # Green (10m)
    "S2_B4",      # Red (10m)
    "S2_B8",      # NIR (10m)
    "S1_VV",      # SAR VV polarization
    "S1_VH",      # SAR VH polarization
    "VIIRS_avg_rad",  # Nighttime lights
    "S2_valid_mask"   # Cloud-free pixel fraction [0-1]
]
# Optional 9th band: S2_B11 (SWIR1, for construction/bare soil separation)
```

### GCS Export Layout

```
gs://<BUCKET>/siad/<aoi_id>/<tile_id>/<YYYY-MM>.tif
gs://<BUCKET>/siad/<aoi_id>/manifest.jsonl
```

### Manifest Schema (JSONL, one row per tile-month)

```json
{
  "aoi_id": "quickstart-demo",
  "tile_id": "tile_x000_y000",
  "month": "2023-01",
  "gcs_uri": "gs://siad-exports/siad/quickstart-demo/tile_x000_y000/2023-01.tif",
  "rain_anom": -0.35,
  "temp_anom": 0.12,
  "s2_valid_frac": 0.87,
  "band_order_version": "v1",
  "preprocessing_version": "20260228"
}
```

### World Model Architecture Requirements

- **Not 1-step "lite"**: Multi-step rollout training (H=6)
- **Action conditioning**: Rain/temp anomalies → action encoder → latent u_t
- **EMA target encoder**: Stabilized targets z_tilde per JEPA
- **Recursive rollout**: z_{t+1} = F(z_t, u_t), iterate k=1..6
- **Loss**: Sum over rollout steps with optional decay weights

### Detection Requirements

- **NEUTRAL scenario baseline**: rain_anom=0, temp_anom=0 counterfactual
- **Tile-local percentile**: Each tile compared to its own 99th percentile
- **Persistence**: ≥2 consecutive months above threshold
- **Clustering**: ≥3 spatially connected tiles → hotspot
- **Attribution tags**: Structural (SAR+lights), Activity (lights-heavy), Environmental (optical NDVI-like)

---

## End-to-End Smoke Test (First Round Goal)

**Smoke Test Spec**:
1. **Export**: 1 AOI, 2 tiles, 2 months → GCS + manifest.jsonl
2. **Train**: Load 2-tile sample, run 10 training steps → checkpoint
3. **Detect**: Run neutral rollout, compute scores → 1 hotspot JSON
4. **Report**: Generate tiny HTML report with 1 map thumbnail

**Acceptance**: Pipeline runs end-to-end without errors, produces all output files

---

## First Round Deliverables (Today)

Each agent must produce:

### 1. Design Note (1-2 pages in `docs/<agent-name>-design.md`)

**Template**:
```markdown
# <Agent Name> Design Note

## Module API
- Public functions/classes
- Input formats (file paths, schemas)
- Output formats (file paths, schemas)

## Dependencies
- Upstream: What I consume (from which agent/module)
- Downstream: What I produce (for which agent/module)

## Failure Modes
- What can go wrong (EE quota, OOM, missing data)
- How I handle errors (retry, log, fail-fast)
- Validation checks (schema validation, sanity bounds)

## Testing Strategy
- Smoke test: Minimal runnable example
- Unit tests: Key functions (if applicable)
- Integration test: End-to-end with upstream/downstream

## Open Questions/Blockers
- What I need from other agents
- Ambiguities in spec
```

### 2. Code Skeleton + One Test

- Create directory structure
- Implement minimal interfaces (can be stubs with `pass` or `raise NotImplementedError`)
- Add at least ONE runnable smoke script or pytest test
- Update README.md in your module directory

### 3. Reply to Lead

**Format**:
```
Agent: <Name>
Plan: <1-sentence summary of approach>
Interfaces: <Key inputs/outputs>
Risks: <Top 3 failure modes>
First PR: <List of files to create>
Blockers: <What I need from teammates>
```

---

## Coordination Protocol

### Communication

- **Primary**: Reply to Lead with status updates
- **Blockers**: Tag Lead + affected teammate
- **Design changes**: Propose in design note, get Lead approval before coding

### File Conflicts Prevention

- Each agent works ONLY in their owned directories
- Shared interfaces defined in `docs/CONTRACTS.md` (Lead creates)
- No agent modifies another agent's code (use interfaces)

### Integration Points

| From Agent | To Agent | Interface | Location |
|------------|----------|-----------|----------|
| Data/GEE → World Model | manifest.jsonl schema | `docs/CONTRACTS.md` |
| Data/GEE → Actions | Exported tiles | manifest.jsonl |
| Actions → World Model | Anomaly vectors | manifest.jsonl rows |
| World Model → Detection | Checkpoint format | `data/models/<name>.pth` |
| Detection → Reporting | Hotspot JSON schema | `data/outputs/<aoi>/hotspots.json` |
| Infra → All | Config schema | `configs/schema.yaml` |

---

## Task Assignment Summary

| Agent | Task IDs | Count | Priority |
|-------|----------|-------|----------|
| Data/GEE | T009-T020, T027 | 13 | P0 (blocks all) |
| Actions | T014-T015, T019 | 3 | P0 (blocks training) |
| World Model | T021-T026, T029 | 7 | P1 (blocks detection) |
| Detection | T030-T036, T051-T055 | 12 | P2 (blocks reporting) |
| Infra | T001-T008, T060-T068 | 17 | P0 (foundation) |
| Reporting | T038-T040, T047-T050, T056-T059, T069-T070 | 13 | P3 (final output) |

**Total**: 65 tasks assigned (5 tasks deferred to post-smoke-test)

---

## Next Steps (Lead's Actions)

1. ✅ Create this charter
2. ⏳ Create `docs/CONTRACTS.md` with interface schemas
3. ⏳ Launch 6 agents in parallel with initial assignments
4. ⏳ Collect design notes from all agents
5. ⏳ Review design notes, resolve conflicts
6. ⏳ Monitor smoke test progress
7. ⏳ Validate end-to-end smoke test
8. ⏳ Report completion to user

---

**Constitution Compliance Checkpoints**:
- [ ] Principle I: Band order contract enforced (Data agent)
- [ ] Principle II: Action conditioning implemented (Actions + Model agents)
- [ ] Principle III: Validation gates implemented (Detection agent)
- [ ] Principle IV: Attribution tags produced (Detection agent)
- [ ] Principle V: CLI-scriptable (Infra agent)
