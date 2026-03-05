# Agent 1: Architecture - Initialization Brief

**Role:** System Architecture & Detection Pipeline Design
**Phase:** MVP (Weeks 1-3)
**Status:** 🟢 Ready to Start

---

## Your Mission

Design and implement the core detection pipeline architecture for SIAD v2.0, focusing on latent-space residual detection without decoder.

---

## What's Already Done ✅

1. **API Specification** (`docs/API_SPEC.md`)
   - Complete REST API contract
   - 8 core endpoints defined
   - Request/response schemas

2. **Core Modules Implemented:**
   - `src/siad/detect/residuals.py` - Token residual computation
   - `src/siad/detect/environmental_norm.py` - Weather normalization

3. **Existing Infrastructure:**
   - World model trained (encoder + transition)
   - Dataset with 22 tiles (validation set)
   - FastAPI skeleton in `siad-command-center/api/`

---

## Your Week 1 Tasks

### Task 1: Baseline Comparison Module
**File:** `src/siad/detect/baselines.py`

Implement three baseline predictors:

```python
def persistence_baseline(z_context, horizon=6):
    """Predict no change: Z_t+1 = Z_t"""
    # Simply repeat context for all future timesteps
    pass

def seasonal_baseline(encoder, tile_id, month_t, horizon=6):
    """Predict same as last year: Z_t+1 = Z_t-12"""
    # Load observation from 12 months ago
    # Encode and use as prediction
    pass

def linear_extrapolation_baseline(z_history, horizon=6):
    """Extrapolate linear trend from recent months"""
    # Fit linear trend to last 3 months
    # Extrapolate forward
    pass
```

**Deliverable:** Working baseline module with unit tests

---

### Task 2: Storage Schema Design
**File:** `docs/STORAGE_SCHEMA.md`

Design HDF5 structure for pre-computed residuals:

```
residuals.h5
├── tile_001/
│   ├── residuals/          # [T, 256] float32
│   ├── tile_scores/        # [T] float32
│   ├── timestamps/         # [T] datetime64
│   ├── metadata/           # Group attrs
│   │   ├── lat: float
│   │   ├── lon: float
│   │   ├── region: str
│   │   └── data_quality: str
│   └── baselines/          # Subgroup
│       ├── persistence/    # [T] float32
│       ├── seasonal/       # [T] float32
│       └── linear/         # [T] float32
```

**Deliverable:** HDF5 schema spec + example read/write code

---

### Task 3: Data Flow Diagram
**File:** `docs/DATA_FLOW.md`

Create detailed data flow diagram showing:

1. **Preprocessing:** GeoTIFF → 8-channel tensor
2. **Encoding:** Tensor → latent tokens
3. **Rollout:** Context + actions → predicted tokens
4. **Residual:** Predicted vs observed → cosine distance
5. **Aggregation:** Tokens → tile score
6. **Storage:** Scores → HDF5
7. **API:** HDF5 → JSON response

Use Mermaid diagrams or ASCII art.

**Deliverable:** Visual data flow documentation

---

## Your Week 2 Tasks

### Task 4: Spatial Clustering Algorithm
**File:** `src/siad/detect/clustering.py`

Implement simple adjacency-based clustering:

```python
def cluster_hotspots(hotspots: List[Hotspot], max_distance_km: float = 5.0):
    """Merge adjacent hotspots into clusters

    Args:
        hotspots: List of hotspot detections
        max_distance_km: Max distance to merge (default 5km)

    Returns:
        clusters: List of merged hotspot clusters
    """
    # 1. Build adjacency graph (distance < threshold)
    # 2. Find connected components
    # 3. Merge metadata (onset = earliest, duration = max, score = mean)
    pass
```

**Deliverable:** Clustering module with tests

---

### Task 5: Batch Inference Pipeline Design
**File:** `docs/BATCH_INFERENCE.md`

Design pipeline for pre-computing all residuals:

```bash
# Pseudocode
for tile in validation_tiles:
    for context_month in range(start, end - 6):
        1. Load observation at context_month
        2. Encode to latent
        3. Generate neutral actions (rain=0, temp=0)
        4. Rollout 6 months
        5. Encode actual future (months t+1 to t+6)
        6. Compute residuals
        7. Compute baselines
        8. Write to HDF5
```

**Deliverable:** Pipeline design doc + script outline

---

### Task 6: Caching Strategy
**File:** `docs/CACHING.md`

Design multi-layer cache:

1. **Model cache:** Keep encoder/transition in GPU memory
2. **Latent cache:** Cache encoded tiles (Redis or in-memory)
3. **Residual cache:** Cache computed residuals (1 hour TTL)
4. **API cache:** HTTP cache headers

**Deliverable:** Caching architecture doc

---

## Your Week 3 Tasks

### Task 7: Integration Testing
**File:** `tests/integration/test_detection_pipeline.py`

End-to-end test:

```python
def test_full_detection_pipeline():
    # 1. Load tile
    # 2. Compute residuals
    # 3. Detect persistence
    # 4. Compare baselines
    # 5. Cluster hotspots
    # 6. Verify outputs
    pass
```

**Deliverable:** Integration test suite

---

### Task 8: Performance Profiling
**File:** `docs/PERFORMANCE.md`

Profile and optimize:

1. Measure inference time per tile
2. Identify bottlenecks (encoding? rollout? residuals?)
3. Propose optimizations (batching, caching, quantization)
4. Document performance targets vs actuals

**Deliverable:** Performance report with optimization recommendations

---

## Key Interfaces You'll Define

### 1. Baseline Interface
```python
class BaselinePredictor(ABC):
    @abstractmethod
    def predict(self, context, horizon) -> torch.Tensor:
        """Return predicted latents [H, 256, 512]"""
        pass
```

### 2. Storage Interface
```python
class ResidualStore:
    def write(self, tile_id: str, month: str, residuals: np.ndarray):
        """Write residuals to HDF5"""
        pass

    def read(self, tile_id: str, month: str) -> np.ndarray:
        """Read residuals from HDF5"""
        pass
```

### 3. Pipeline Interface
```python
def batch_compute_residuals(
    tiles: List[str],
    model: WorldModel,
    output_path: Path
) -> Dict[str, List[float]]:
    """Batch compute residuals for all tiles"""
    pass
```

---

## Dependencies

**You depend on:**
- Agent 2 (API) for endpoint implementation feedback
- Existing modules: `residuals.py`, `environmental_norm.py`

**Others depend on you:**
- Agent 2 needs your storage schema to implement data services
- Agent 4 needs your data flow to design frontend API calls

---

## Key Decisions You'll Make

1. **Clustering algorithm:** Adjacency vs DBSCAN vs hierarchical?
   - Recommendation: Start simple (adjacency), add DBSCAN in Phase 2

2. **HDF5 vs alternative:** Stick with HDF5 or use Parquet/Zarr?
   - Recommendation: HDF5 (good for numerical arrays, fast random access)

3. **Baseline priority:** Which baselines for MVP?
   - Recommendation: Persistence (easy) + seasonal (if data available)

4. **Batch vs streaming:** Pre-compute all or compute on-demand?
   - Recommendation: Pre-compute for demo (15-20 tiles), on-demand for production

---

## Resources

**Codebase:**
- `/src/siad/model/` - World model implementation
- `/src/siad/detect/` - Detection modules (you'll add more here)
- `/src/siad/train/dataset.py` - Dataset loader (reference for data format)

**Documentation:**
- `/docs/API_SPEC.md` - API contract
- `/docs/MODEL.md` - Model architecture
- `/docs/detection-design.md` - Original detection design (pre-v2.0)

**Example Data:**
- `/data/manifest_22tiles_val.jsonl` - Validation tile metadata
- `/siad-command-center/data/gallery/` - Pre-computed gallery data (old format)

---

## Success Criteria (Week 3)

- [ ] Baseline module passes unit tests
- [ ] HDF5 schema documented and validated
- [ ] Clustering algorithm tested on sample data
- [ ] Batch inference script can process 5 tiles
- [ ] Integration tests pass
- [ ] Performance profiling complete

---

## Communication

**Sync with:**
- **Agent 2 (API):** Daily on storage schema and data interfaces
- **Agent 4 (Frontend):** Mid-week on data flow and API contracts
- **All agents:** End of Week 1 for architecture review

**Deliverables location:**
- Code: `/src/siad/detect/`
- Docs: `/docs/`
- Tests: `/tests/integration/`

---

## Questions to Resolve

1. Do we have 12+ months of historical data for seasonal baseline?
2. What's the target AOI? (Mission Bay? Oakland Port? Full SF?)
3. Should clustering happen in backend or frontend?

**Ask these in team sync!**

---

**Ready to start? Begin with Task 1: Baseline Module!**

Good luck! 🚀
