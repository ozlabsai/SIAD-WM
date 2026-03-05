# Agent 2: API/Backend - Initialization Brief

**Role:** Backend API Implementation & Model Services
**Phase:** MVP (Weeks 1-3)
**Status:** 🟢 Ready to Start

---

## Your Mission

Implement FastAPI backend that serves latent residual detections, integrating the world model with new detection modules.

---

## What's Already Done ✅

1. **API Spec** (`docs/API_SPEC.md`)
   - 8 endpoints defined
   - Request/response schemas
   - Error handling patterns

2. **Detection Modules:**
   - `src/siad/detect/residuals.py` - Residual computation
   - `src/siad/detect/environmental_norm.py` - Weather normalization

3. **Existing Backend Skeleton:**
   - `siad-command-center/api/main.py` - FastAPI app
   - `siad-command-center/api/services/model_loader.py` - Model loading service
   - `siad-command-center/api/services/inference.py` - Inference service (needs extension)

---

## Your Week 1 Tasks

### Task 1: Extend Inference Service
**File:** `siad-command-center/api/services/inference.py`

Add methods for residual computation:

```python
class InferenceService:
    def __init__(self, model: WorldModel):
        self.model = model
        self.device = next(model.parameters()).device

    def compute_residuals(
        self,
        tile_id: str,
        context_month: str,
        rollout_horizon: int = 6,
        normalize_weather: bool = True
    ) -> ResidualResult:
        """Compute latent residuals for a tile

        1. Load context observation
        2. Encode to latent
        3. Generate actions (neutral if normalize_weather=True)
        4. Rollout predictions
        5. Load and encode future observations
        6. Compute cosine distance
        7. Return ResidualResult
        """
        # TODO: Implement using residuals.py and environmental_norm.py
        pass
```

**Deliverable:** Extended inference service with residual computation

---

### Task 2: Implement Core Endpoints
**File:** `siad-command-center/api/routes/detection.py` (new file)

Create detection router:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/detect", tags=["detection"])

class ResidualRequest(BaseModel):
    tile_id: str
    context_month: str  # ISO date YYYY-MM
    rollout_horizon: int = 6
    normalize_weather: bool = True

@router.post("/residuals")
async def compute_residuals(request: ResidualRequest):
    """Compute token-level residuals"""
    # Call inference_service.compute_residuals()
    # Convert ResidualResult to JSON
    pass

@router.get("/hotspots")
async def get_hotspots(
    start_date: str = None,
    end_date: str = None,
    min_score: float = 0.5,
    alert_type: str = "all",
    limit: int = 10
):
    """Get ranked hotspots"""
    # Query pre-computed residuals
    # Rank by score
    # Apply filters
    pass
```

**Deliverable:** Working `/api/detect/residuals` and `/api/hotspots` endpoints

---

### Task 3: Data Loading Service
**File:** `siad-command-center/api/services/data_loader.py` (new file)

Create service to load tiles from disk:

```python
class DataLoader:
    def __init__(self, data_root: Path):
        self.data_root = data_root
        self.manifest = self._load_manifest()

    def load_tile(self, tile_id: str, month: str) -> torch.Tensor:
        """Load 8-channel GeoTIFF for given tile and month

        Returns:
            tensor: [8, 256, 256] normalized tile
        """
        pass

    def load_weather_data(self, tile_id: str, months: List[str]):
        """Load rain and temp anomalies for given months

        Returns:
            rain_anomalies: [T] array
            temp_anomalies: [T] array
        """
        pass
```

**Deliverable:** Data loading service integrated with inference

---

## Your Week 2 Tasks

### Task 4: Pre-computation Script
**File:** `scripts/precompute_residuals.py`

Batch compute residuals for all demo tiles:

```python
#!/usr/bin/env python3
"""Pre-compute residuals for all validation tiles

Usage:
    uv run python scripts/precompute_residuals.py \
        --checkpoint checkpoints/checkpoint_best.pth \
        --manifest data/manifest_22tiles_val.jsonl \
        --output data/residuals.h5 \
        --num-tiles 15
"""

def main():
    # Load model
    # Load dataset
    # For each tile:
    #   For each context month (with 6-month horizon):
    #     Compute residuals
    #     Compute baselines
    #     Write to HDF5
    pass
```

**Deliverable:** Script that generates `data/residuals.h5`

---

### Task 5: HDF5 Storage Service
**File:** `siad-command-center/api/services/storage.py` (new file)

Implement HDF5 reader/writer:

```python
import h5py

class ResidualStorage:
    def __init__(self, hdf5_path: Path):
        self.path = hdf5_path

    def write_residuals(
        self,
        tile_id: str,
        month: str,
        residuals: np.ndarray,
        tile_score: float,
        metadata: dict
    ):
        """Write residuals to HDF5"""
        with h5py.File(self.path, 'a') as f:
            tile_group = f.require_group(tile_id)
            # Append to datasets
            pass

    def read_residuals(self, tile_id: str, month: str) -> np.ndarray:
        """Read residuals from HDF5"""
        with h5py.File(self.path, 'r') as f:
            # Read from datasets
            pass

    def get_all_tile_scores(self, start_month: str, end_month: str):
        """Get scores for all tiles in date range"""
        pass
```

**Deliverable:** Storage service with unit tests

---

### Task 6: Baseline Endpoints
**File:** `siad-command-center/api/routes/baselines.py` (new file)

Implement baseline comparison:

```python
@router.get("/baselines/{tile_id}")
async def get_baseline_comparison(
    tile_id: str,
    month: str
):
    """Compare world model vs persistence/seasonal baselines"""
    # Load world model residual from HDF5
    # Load baseline residuals from HDF5
    # Compute improvement metrics
    # Return comparison
    pass
```

**Deliverable:** `/api/baselines/{tile_id}` endpoint working

---

## Your Week 3 Tasks

### Task 7: Heatmap Endpoint
**File:** `siad-command-center/api/routes/visualization.py` (new file)

Serve 16×16 token heatmaps:

```python
@router.get("/tiles/{tile_id}/heatmap")
async def get_token_heatmap(
    tile_id: str,
    month: str,
    normalize_weather: bool = True
):
    """Get 16×16 residual heatmap for visualization"""
    # Load residuals [256]
    # Reshape to [16, 16]
    # Return as nested array with metadata
    pass
```

**Deliverable:** Heatmap endpoint + sample test

---

### Task 8: Export Endpoints
**File:** `siad-command-center/api/routes/export.py` (new file)

Implement GeoJSON and CSV export:

```python
@router.get("/export/geojson")
async def export_hotspots_geojson(...):
    """Export hotspots as GeoJSON FeatureCollection"""
    pass

@router.get("/export/timeline.csv")
async def export_timeline_csv(hotspot_id: str):
    """Export timeline as CSV"""
    pass
```

**Deliverable:** Working export endpoints

---

## Key Files You'll Create

```
siad-command-center/api/
├── routes/
│   ├── detection.py        # Residual & hotspot endpoints
│   ├── baselines.py        # Baseline comparison
│   ├── visualization.py    # Heatmap endpoint
│   └── export.py           # GeoJSON/CSV export
├── services/
│   ├── inference.py        # Extended with residuals
│   ├── data_loader.py      # Tile loading
│   └── storage.py          # HDF5 operations
└── models/
    └── schemas.py          # Pydantic models for requests/responses
```

---

## API Testing

Create integration tests:

```python
# tests/api/test_detection_endpoints.py

def test_compute_residuals():
    response = client.post("/api/detect/residuals", json={
        "tile_id": "tile_001",
        "context_month": "2024-01",
        "rollout_horizon": 6,
        "normalize_weather": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "residuals" in data
    assert len(data["tile_scores"]) == 6
```

---

## Dependencies

**You depend on:**
- Agent 1 (Architecture) for storage schema and baseline module
- Existing trained model checkpoint
- Dataset manifests

**Others depend on you:**
- Agent 4 (Frontend) needs your API to be functional
- Agent 5 (UX) needs to test workflows against API

---

## Key Decisions

1. **Sync vs Async:** Use async endpoints or sync?
   - Recommendation: Async for I/O-bound ops (file loading), sync for compute

2. **Caching layer:** Redis or in-memory?
   - Recommendation: In-memory for MVP, Redis for production

3. **Error handling:** How to handle missing tiles?
   - Recommendation: Return 404 with helpful message + list of available tiles

4. **Pre-compute scope:** How many tiles?
   - Recommendation: 15-20 tiles for demo (full validation set)

---

## Performance Targets

| Endpoint | Target | Max |
|----------|--------|-----|
| `/api/hotspots` | < 200ms | 500ms |
| `/api/detect/residuals` (cached) | < 100ms | 300ms |
| `/api/detect/residuals` (compute) | < 2s | 5s |
| `/api/baselines/{tile_id}` | < 150ms | 400ms |

**Profile and optimize in Week 3!**

---

## Example Workflow

```python
# 1. Start server
uv run python -m uvicorn siad-command-center.api.main:app --reload

# 2. Test residual computation
curl -X POST http://localhost:8000/api/detect/residuals \
  -H "Content-Type: application/json" \
  -d '{
    "tile_id": "tile_001",
    "context_month": "2024-01",
    "rollout_horizon": 6,
    "normalize_weather": true
  }'

# 3. Get hotspots
curl http://localhost:8000/api/hotspots?limit=10&min_score=0.5

# 4. Get baseline comparison
curl http://localhost:8000/api/baselines/tile_001?month=2024-03
```

---

## Resources

**Existing Code:**
- `siad-command-center/api/` - Current API skeleton
- `src/siad/detect/` - Detection modules you'll integrate
- `src/siad/model/` - World model classes

**Data:**
- `data/manifest_22tiles_val.jsonl` - Tile metadata
- `checkpoints/checkpoint_best.pth` - Trained model

---

## Success Criteria (Week 3)

- [ ] `/api/detect/residuals` endpoint functional
- [ ] `/api/hotspots` returns ranked list
- [ ] `/api/baselines/{tile_id}` compares models
- [ ] Pre-computation script processes 15 tiles
- [ ] HDF5 storage operational
- [ ] API tests passing
- [ ] Performance targets met

---

## Communication

**Sync with:**
- **Agent 1 (Architecture):** Daily on storage schema
- **Agent 4 (Frontend):** Mid-week on API contracts
- **All agents:** End of Week 1 architecture review

---

**Ready to code? Start with Task 1: Extend Inference Service!**

🚀 Let's build!
