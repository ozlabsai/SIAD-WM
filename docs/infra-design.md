# SIAD MVP - Infrastructure & DevEx Design

**Version**: 1.0
**Date**: 2026-03-01
**Owner**: Infra/DevEx Agent
**Status**: Design Complete

## 1. Executive Summary

This document defines the infrastructure scaffolding for the SIAD MVP, including:
- Python 3.13+ project structure with UV dependency management
- CLI architecture with click-based command framework
- Configuration management with Pydantic validation
- Deterministic run requirements (logging, seeding, versioning)
- CI smoke testing strategy with GitHub Actions

**Key Design Decisions**:
- UV over Poetry (per constitution and user CLAUDE.md)
- Click over argparse (better subcommand UX, extensibility)
- Pydantic over Cerberus (type safety, IDE support, dict/object duality)
- Structured logging to file + stderr (audit trail + real-time monitoring)
- Minimal CI footprint (smoke tests on tiny sample, <10 min runtime)

---

## 2. UV vs Poetry Justification

**Chosen**: UV

**Rationale**:
1. **User Directive**: User's `~/.claude/CLAUDE.md` mandates "use UV for python execution, dependency management"
2. **Constitution Alignment**: Technical Constraints section specifies "Python 3.13+ with UV dependency management (MUST): UV ensures lockfile reproducibility"
3. **Performance**: UV's Rust-based resolver is 10-100x faster than Poetry for large dependency graphs (torch, rasterio, earthengine-api)
4. **Lockfile Determinism**: `uv.lock` provides bit-for-bit reproducible environments (critical for Principle V: Reproducible Pipelines)
5. **PEP 723 Support**: UV natively supports inline script metadata, useful for future data export scripts

**Trade-offs**:
- Ecosystem maturity: Poetry has more third-party tooling (pre-commit hooks, IDE integrations)
- Mitigation: UV's CLI is Poetry-compatible for most workflows (`uv add`, `uv sync` mirror `poetry add`, `poetry install`)

---

## 3. pyproject.toml Structure

```toml
[project]
name = "siad"
version = "0.1.0"
description = "Satellite Imagery Anomaly Detection - Multi-modal world model for infrastructure change detection"
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
authors = [
    { name = "SIAD Team" }
]

dependencies = [
    "click>=8.1.0",              # CLI framework
    "pydantic>=2.0.0",           # Config validation
    "pyyaml>=6.0",               # Config parsing
    "earthengine-api>=0.1.400",  # GEE data export
    "torch>=2.0.0",              # World model training
    "rasterio>=1.3.0",           # GeoTIFF I/O
    "numpy>=1.24.0",             # Tensor ops
    "h5py>=3.10.0",              # HDF5 dataset storage
    "matplotlib>=3.8.0",         # Visualization
    "Pillow>=10.0.0",            # Thumbnail generation
    "tqdm>=4.66.0",              # Progress bars
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "ruff>=0.2.0",
]

[project.scripts]
siad = "siad.cli.main:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "--strict-markers --tb=short"

[tool.black]
line-length = 100
target-version = ["py313"]

[tool.ruff]
line-length = 100
target-version = "py313"
```

**Dependency Justification**:
- `click`: Industry-standard CLI framework with excellent help formatting, argument validation
- `pydantic`: Type-safe config models (catches errors at startup, not mid-pipeline)
- `earthengine-api`: Required for Data agent GEE export
- `torch>=2.0`: Required for World Model agent (JEPA encoder-dynamics)
- `rasterio`: GeoTIFF I/O (band order contract enforcement)
- `h5py`: Optional for future HDF5 dataset caching (deferred post-MVP)

---

## 4. CLI Architecture

**Framework**: Click

**Structure**:
```
siad (group)
├── export (command)
├── train (command)
├── detect (command)
└── report (command)
```

**Click Advantages**:
1. **Subcommand Support**: Native `@click.group()` decorator makes routing clean
2. **Help Formatting**: Auto-generated `--help` with option descriptions, defaults
3. **Type Validation**: `click.Path(exists=True)`, `click.Choice(['neutral', 'observed'])` prevent bad inputs
4. **Extensibility**: Easy to add global flags (`--verbose`, `--dry-run`) to all commands
5. **Testing**: Click's `CliRunner` enables isolated command testing without subprocess overhead

**Alternative (Argparse)**:
- Pros: Stdlib (no dependency), familiar to many developers
- Cons: Verbose subcommand setup, poor help formatting, weak type validation
- Verdict: Click's DX advantages outweigh stdlib preference

**Command Pattern**:
```python
@click.command()
@click.option('--config', type=click.Path(exists=True), required=True)
@click.option('--dry-run', is_flag=True, help="Validate inputs without executing")
@click.option('--verbose', is_flag=True, help="Enable DEBUG logging")
def export(config: str, dry_run: bool, verbose: bool):
    """Export satellite imagery from GEE for AOI defined in config."""
    setup_logging(verbose)
    cfg = load_config(config)
    if dry_run:
        logger.info("DRY RUN: Would export AOI %s", cfg.aoi.aoi_id)
        return
    # Delegate to Data agent module
    from siad.data.gee_export import export_aoi
    export_aoi(cfg)
```

**Global Flags (All Commands)**:
- `--dry-run`: Validate config, check file paths, log intended actions, exit 0 (no side effects)
- `--verbose`: Set logging level to DEBUG (default: INFO)
- `--help`: Auto-generated by Click

---

## 5. Config Validation Strategy

**Chosen**: Pydantic

**Schema Definition** (`src/siad/config/schema.py`):
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class AOIConfig(BaseModel):
    aoi_id: str = Field(..., min_length=1)
    bounds: dict[str, float]  # {min_lon, max_lon, min_lat, max_lat}
    projection: str = "EPSG:3857"
    resolution_m: int = 10
    tile_size_px: int = 256

    @field_validator('bounds')
    def validate_bounds(cls, v):
        required = {'min_lon', 'max_lon', 'min_lat', 'max_lat'}
        if not required.issubset(v.keys()):
            raise ValueError(f"bounds must contain {required}")
        if v['min_lon'] >= v['max_lon'] or v['min_lat'] >= v['max_lat']:
            raise ValueError("min_lon/lat must be less than max_lon/lat")
        return v

class DataConfig(BaseModel):
    gcs_bucket: str = "siad-exports"
    export_path: str = "gs://siad-exports/siad/{aoi_id}"
    start_month: str  # YYYY-MM format
    end_month: str
    sources: list[Literal["s1", "s2", "viirs", "chirps", "era5"]] = ["s1", "s2", "viirs", "chirps", "era5"]

class ModelConfig(BaseModel):
    latent_dim: int = 256
    context_length: int = 6
    rollout_horizon: int = 6
    batch_size: int = 16
    epochs: int = 50
    learning_rate: float = 1e-4

class DetectionConfig(BaseModel):
    percentile_threshold: float = 99.0
    persistence_months: int = 2
    min_cluster_size: int = 3
    scenarios: list[str] = ["neutral", "observed"]

class SIADConfig(BaseModel):
    aoi: AOIConfig
    data: DataConfig
    model: ModelConfig
    detection: DetectionConfig
```

**Loading API** (`src/siad/config/loader.py`):
```python
import yaml
from pathlib import Path
from .schema import SIADConfig

def load_config(config_path: str | Path) -> SIADConfig:
    """Load and validate YAML config."""
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    return SIADConfig(**raw)  # Pydantic validates on construction
```

**Pydantic Advantages**:
1. **Type Safety**: IDE autocomplete on `cfg.aoi.bounds.min_lon` (vs dict key lookups)
2. **Error Messages**: Clear validation errors ("bounds.min_lon: field required" vs generic KeyError)
3. **Defaults**: `gcs_bucket = "siad-exports"` vs manual dict.get() boilerplate
4. **Extensibility**: Easy to add custom validators (e.g., check GCS bucket exists)

**Alternative (Cerberus)**:
- Pros: Pure schema (no classes), JSON Schema alignment
- Cons: No IDE support, dict-only output, weaker error messages
- Verdict: Pydantic's type safety aligns with KISS principle (fewer runtime bugs)

---

## 6. Deterministic Run Requirements

**Principle V Compliance**: "All preprocessing, training, and inference MUST be scriptable via CLI with deterministic outputs for auditing."

**Mechanisms**:

### 6.1 Logging Configuration
```python
# src/siad/utils/logging_config.py
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(verbose: bool = False):
    """Configure root logger with file + stderr handlers."""
    level = logging.DEBUG if verbose else logging.INFO
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create logs directory if missing
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger configuration
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_dir / f"siad_{timestamp}.log"),
            logging.StreamHandler(sys.stderr)
        ]
    )

    # Suppress noisy third-party loggers
    logging.getLogger("earthengine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
```

**Contract**:
- All CLI commands call `setup_logging()` before any logic
- All modules use `logger = logging.getLogger(__name__)` (never print())
- Logs persist to `logs/siad_<timestamp>.log` for auditing (excluded from git via .gitignore)

### 6.2 Random Seed Setting
```python
# src/siad/utils/determinism.py
import random
import numpy as np
import torch

def set_seed(seed: int = 42):
    """Set RNG seeds for reproducible runs."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
```

**Contract**:
- Training command calls `set_seed(42)` before model initialization
- Config schema can override seed via `model.seed: int = 42`

### 6.3 Version Tracking
```python
# src/siad/__init__.py
__version__ = "0.1.0"

# In checkpoint saving (Model agent):
checkpoint = {
    "epoch": epoch,
    "model_state_dict": model.state_dict(),
    "config": cfg.model.model_dump(),
    "siad_version": __version__,
    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
}
```

**Contract**:
- Every model checkpoint embeds SIAD version + git SHA
- Detection agent logs warning if checkpoint was trained with different version

---

## 7. CI Smoke Test Plan

**Platform**: GitHub Actions

**Workflow**: `.github/workflows/smoke_test.yml`

**Strategy**:
- Run end-to-end pipeline (export → train → detect) on minimal sample
- Sample size: 1 tile (2.56 km²) × 2 months (Jan-Feb 2023)
- Expected runtime: <10 minutes (5 min export + 3 min train + 2 min detect)
- Trigger: Push to main, Pull Request to main

**Workflow Stages**:
1. **Setup**: Install UV, sync dependencies (`uv sync`)
2. **Lint**: Run ruff, black checks (`uv run ruff check`, `uv run black --check`)
3. **Unit Tests**: Run pytest on non-integration tests (`uv run pytest tests/unit`)
4. **Contract Tests**: Verify CLI help/dry-run (`uv run pytest tests/contract`)
5. **Smoke Test**: Run mini pipeline on cached sample data
   - Use pre-exported GeoTIFF in `tests/fixtures/sample_tile.tif` (checked into git, <5 MB)
   - Train model for 5 epochs (not 50) with tiny batch size (2)
   - Run detection, assert hotspots.json is valid JSON with schema compliance

**Caching**:
- Cache UV virtual environment (key: `uv.lock` hash)
- Cache Earth Engine exports (deferred to post-MVP, requires GCS setup)

**Failure Modes**:
1. **Dependency conflicts**: torch + numpy version incompatibility
   - Mitigation: Pin versions in pyproject.toml, test in CI with fresh venv
2. **GEE auth timeout**: EE authentication fails in CI
   - Mitigation: Use pre-exported fixtures, skip GEE tests in CI (run locally)
3. **CI timeout**: Smoke test exceeds 10 min
   - Mitigation: Use tiny sample (1 tile × 2 months), reduce epochs to 5

---

## 8. Directory Structure

```
siad/
├── .github/
│   └── workflows/
│       └── smoke_test.yml          # CI configuration
├── configs/
│   ├── quickstart-demo.yaml        # Example AOI config
│   └── schema.yaml                 # Config schema docs (Pydantic exports JSONSchema)
├── data/                           # Ignored by git (except fixtures)
│   ├── models/                     # Training outputs (checkpoints, metrics)
│   ├── outputs/                    # Detection outputs (hotspots, scores)
│   └── exports/                    # Local cache of GEE exports (optional)
├── logs/                           # Ignored by git
│   └── siad_*.log                  # Timestamped log files
├── src/
│   └── siad/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py            # Click group + global options
│       │   ├── export.py          # Wrapper for Data agent
│       │   ├── train.py           # Wrapper for Model agent
│       │   ├── detect.py          # Wrapper for Detection agent
│       │   └── report.py          # Wrapper for Reporting agent
│       ├── config/
│       │   ├── __init__.py
│       │   ├── schema.py          # Pydantic models
│       │   └── loader.py          # Config loading + validation
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── logging_config.py  # setup_logging()
│       │   └── determinism.py     # set_seed()
│       ├── data/                  # Data agent (T009-T026, future PR)
│       ├── model/                 # Model agent (T030-T044, future PR)
│       ├── detection/             # Detection agent (T045-T053, future PR)
│       └── reporting/             # Reporting agent (T054-T059, future PR)
├── tests/
│   ├── contract/
│   │   └── test_cli_help.py       # CLI contract tests (T063-T068)
│   ├── unit/
│   │   └── test_config_loader.py  # Config validation tests
│   ├── integration/               # Future: cross-agent tests
│   └── fixtures/
│       └── sample_tile.tif        # Tiny GeoTIFF for smoke tests
├── .gitignore
├── pyproject.toml
├── uv.lock                        # Auto-generated by UV
└── README.md
```

---

## 9. Failure Modes & Mitigations

### 9.1 Dependency Version Conflicts
**Symptom**: `torch 2.1.0` requires `numpy<1.27`, but `rasterio` requires `numpy>=1.27`

**Mitigation**:
- Pin versions explicitly in pyproject.toml (don't use `>=` loosely)
- Run `uv lock --upgrade` weekly to detect conflicts early
- Test in CI with fresh venv (no local cache contamination)

### 9.2 Config Schema Drift
**Symptom**: Data agent adds `data.cloud_mask_threshold` param, but Infra agent's schema.py is outdated

**Mitigation**:
- Centralize schema in `src/siad/config/schema.py` (single source of truth)
- All agents import from this schema (no ad-hoc dict munging)
- Add validation test: `pytest tests/contract/test_config_schema.py` checks all example configs pass validation
- Update schema.py atomically with feature PR (don't defer)

### 9.3 CI Timeout
**Symptom**: Smoke test exceeds 10 min (GitHub Actions free tier limit)

**Mitigation**:
- Use minimal sample (1 tile × 2 months)
- Reduce training epochs (5 instead of 50)
- Cache UV venv (saves 2-3 min per run)
- Skip GEE export in CI (use pre-baked fixture)

### 9.4 GCS Authentication in CI
**Symptom**: `gcloud auth` fails in GitHub Actions (no service account)

**Mitigation**:
- For MVP: Use pre-exported fixtures in `tests/fixtures/` (check into git)
- Post-MVP: Set up GitHub Secrets with GCS service account JSON
- Document local-only GEE export workflow (developers run `siad export` manually)

### 9.5 Log File Accumulation
**Symptom**: `logs/` directory grows to hundreds of MB with old runs

**Mitigation**:
- Add `.gitignore` rule: `logs/*.log`
- Add cleanup script: `uv run python -m siad.utils.cleanup_logs --days 30` (future)
- Document manual cleanup in README: "Run `rm logs/*.log` to clear old logs"

---

## 10. First PR Checklist

**Files to Create/Modify**:
- [x] `docs/infra-design.md` (this document)
- [ ] `pyproject.toml` (dependencies, scripts)
- [ ] `.gitignore` (data/, logs/, Python artifacts)
- [ ] `README.md` (installation, quick start)
- [ ] `configs/quickstart-demo.yaml`
- [ ] `configs/schema.yaml` (JSONSchema export from Pydantic)
- [ ] `src/siad/__init__.py`
- [ ] `src/siad/cli/main.py`
- [ ] `src/siad/cli/export.py`
- [ ] `src/siad/cli/train.py`
- [ ] `src/siad/cli/detect.py`
- [ ] `src/siad/cli/report.py`
- [ ] `src/siad/config/schema.py`
- [ ] `src/siad/config/loader.py`
- [ ] `src/siad/utils/logging_config.py`
- [ ] `src/siad/utils/determinism.py`
- [ ] `tests/contract/test_cli_help.py`
- [ ] `.github/workflows/smoke_test.yml`

**Success Criteria**:
1. `uv sync` completes without errors
2. `siad --help` shows all 4 subcommands
3. `siad export --help` shows config option + dry-run flag
4. `pytest tests/contract/` passes (CLI help tests)
5. GitHub Actions smoke test runs in <10 min

---

## 11. Open Questions

**Q1: GCS bucket name for MVP?**
- **Answer**: Default to `siad-exports` in config schema, document override in quickstart-demo.yaml

**Q2: Should we pin torch CPU-only to reduce install size?**
- **Answer**: No, leave torch unpinned (auto-detects CUDA). Developers with GPU can install `torch[cuda]` manually.

**Q3: Config versioning strategy (YAML schema changes)?**
- **Answer**: For MVP, no versioning (schema is frozen). Post-MVP, add `config_version: "1.0"` field, validate in loader.

---

## 12. Constitution Compliance Check

**Principle I (Data-Driven Foundation)**: N/A (Infra agent doesn't process satellite data)

**Principle II (Counterfactual Reasoning)**: N/A (Infra agent doesn't implement world model)

**Principle III (Testable Predictions)**: ✅ Partially satisfied
- CLI contract tests validate `--help` and `--dry-run` flags
- Smoke tests validate end-to-end pipeline (future PR)

**Principle IV (Interpretable Attribution)**: N/A (Infra agent doesn't implement detection)

**Principle V (Reproducible Pipelines)**: ✅ Fully satisfied
- UV lockfile ensures dependency reproducibility
- CLI-driven workflows (stdin/args → stdout, errors → stderr)
- Logging to file + stderr for audit trail
- Deterministic run support (seed setting, version tracking)

**Technical Constraints**:
- ✅ Python 3.13+ with UV: pyproject.toml specifies `requires-python = ">=3.13"`
- ✅ DRY and KISS: Minimal abstractions (no premature config layers, direct Pydantic models)

**Development Workflow**:
- ✅ MVP-first: Only 4 commands (export/train/detect/report), no bells/whistles
- ✅ Red-team risk hardening: Dry-run flag prevents accidental runs, verbose logging aids debugging

---

## Appendix A: Click vs Argparse Comparison

| Feature | Click | Argparse |
|---------|-------|----------|
| Subcommand routing | `@click.group()` decorator | Manual `add_subparsers()` |
| Help formatting | Rich, auto-aligned | Plain text, manual formatting |
| Type validation | `click.Path(exists=True)` | Manual `os.path.exists()` |
| Testing | `CliRunner()` (no subprocess) | `subprocess.run()` overhead |
| Extensibility | Plugin architecture | Subclass `ArgumentParser` |
| Dependency | External (`pip install click`) | Stdlib (no install) |
| **Verdict** | ✅ Recommended for SIAD | ❌ Too verbose for multi-command CLI |

---

## Appendix B: Pydantic vs Cerberus Comparison

| Feature | Pydantic | Cerberus |
|---------|----------|----------|
| Output type | Python classes (type-safe) | Dicts (runtime errors) |
| IDE support | Full autocomplete | No autocomplete |
| Error messages | Clear, field-specific | Generic, nested dicts |
| Custom validators | `@field_validator` decorator | Manual `validate_<field>()` |
| Performance | Fast (Rust core in v2) | Pure Python |
| **Verdict** | ✅ Recommended for SIAD | ❌ No type safety |

---

**Version History**:
- 2026-03-01: Initial design (v1.0)
