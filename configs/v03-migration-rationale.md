# SIAD v0.3 Configuration Migration - Rationale & Validation

## RATIONALE

### Critical Spec Compliance Fixes

**1. Fixed token_dim from 256 to 512**
- **Issue**: Original config had `latent_dim: 256`, but JEPA spec requires D=512
- **Impact**: Model capacity mismatch would cause dimension errors during training
- **Fix**: Renamed to `token_dim: 512` to match spec and avoid confusion with "latent space"
- **Training benefit**: Correct dimensionality ensures proper representation capacity for 8-channel 256×256 inputs

**2. Switched projection from EPSG:3857 to EPSG:32610 (UTM Zone 10N)**
- **Issue**: Web Mercator (3857) introduces distortion at Bay Area latitudes (~37°N)
- **Impact**: Pixel areas vary across AOI; tiles near edges have different actual ground coverage
- **Fix**: UTM Zone 10N provides accurate equal-area representation for Bay Area
- **Training benefit**: Consistent spatial statistics across tiles; better alignment with Sentinel-2 native UTM projection
- **Residual credibility**: Anomaly detection requires comparable spatial scales - distortion would bias residuals

**3. Added cloud probability as optional 9th channel (S2_cloud_prob_norm)**
- **Issue**: Binary S2_valid_mask loses soft quality information
- **Impact**: Model cannot learn to handle varying data quality gracefully
- **Fix**: Added optional cloud_prob channel + per-tile cloudiness_score metadata
- **Training benefit**: Provides continuous quality signal for learned uncertainty estimation
- **Residual credibility**: Residuals in cloudy areas should be weighted lower; soft signal enables this

**4. Expanded action schema from 1D to 4D minimum**
- **Issue**: Original config only had `rain_anom` (implicit 1D action)
- **Impact**: Model lacks temporal conditioning and absolute precipitation signal
- **Fix**: Added `[rain_anom, precip_abs, month_sin, month_cos]` as base action set
- **Training benefit**:
  - Temporal sinusoidal encoding helps model learn seasonal patterns
  - Absolute + anomaly precipitation provides richer environmental context
  - Separates "what month is it" from "what's unusual this month"
- **Residual credibility**: Neutral scenario (a=0) now has clear semantics - "average weather for an unspecified time"

**5. Renamed and clarified scenario semantics**
- **Issue**: "observed" scenario was conceptually wrong (that's just the ground truth, not a scenario)
- **Impact**: Confusion about what counterfactuals mean
- **Fix**:
  - Kept `neutral` (a=0) for anomaly detection baseline
  - Added `weather_bestfit` as post-training detector scenario (optimize actions to fit)
  - Added `counterfactuals` placeholder for explicit ±2σ precipitation experiments
- **Training benefit**: Clear separation between training (learns dynamics) and detection (compares scenarios)
- **Residual credibility**: Neutral residuals now have unambiguous interpretation

**6. Added anti-collapse regularization (VICReg-style)**
- **Issue**: Original config had no anti-collapse mechanism
- **Impact**: JEPA models are prone to representation collapse without explicit regularization
- **Fix**: Added variance-covariance regularizer with weights (1.0, 1.0)
- **Training benefit**:
  - Variance term prevents all tokens from collapsing to same vector
  - Covariance term decorrelates dimensions, encouraging diverse features
  - Mandatory per MODEL.md spec for training stability
- **Residual credibility**: Collapsed representations produce meaningless residuals

### Clarified Responsibilities

**7. Separated export vs. train configs**
- **Rationale**: Data generation concerns (band order, normalization) differ from training concerns (loss weights, optimizer)
- **Benefit**: Can version and modify independently; clearer ownership

**8. Moved detection thresholds out of training config**
- **Rationale**: Detection is downstream post-processing, not a training hyperparameter
- **Benefit**: Prevents confusion; detector can be tuned separately without retraining

**9. Explicit versioning fields**
- **Rationale**: Track breaking changes to data format, model architecture, preprocessing
- **Benefit**: Reproducibility; can detect config/checkpoint mismatches

### Correctness and Clarity

**10. Computed and documented frame vs. window counts**
- **Issue**: Original config said "10k samples" but was ambiguous about frames vs. windows
- **Fix**:
  - `num_frames = 784 tiles × 48 months = 37,632 tile-months`
  - `num_windows = 784 tiles × (48 - 6) = 32,928 training examples` (with H=6)
- **Benefit**: Clear expectations for dataset size; can validate manifest completeness

**11. Defined CHIRPS aggregation and anomaly computation explicitly**
- **Issue**: Original config mentioned CHIRPS but didn't specify how monthly precip is computed
- **Fix**:
  - Aggregation: sum daily precipitation over calendar month
  - Anomaly: z-score vs. 10-year climatology (2015-2024), month-of-year specific
  - Outputs both `precip_abs` (normalized mm) and `precip_anom` (z-score)
- **Benefit**: Reproducible preprocessing; clear semantics for neutral scenario

**12. Added quality metadata beyond binary mask**
- **Issue**: Binary mask is too coarse for nuanced quality assessment
- **Fix**: Export includes `s2_valid_frac`, `s2_cloud_mean`, `s1_coverage`, `viirs_coverage`
- **Benefit**:
  - Can filter low-quality tiles post-export
  - Can weight loss by quality during training (future work)
  - Enables quality-stratified evaluation

## VALIDATION CHECKLIST

### A. Band Order & Channel Count

- [ ] **Band order exactly matches spec v1**
  - [ ] Index 0: S2_B2 (Blue)
  - [ ] Index 1: S2_B3 (Green)
  - [ ] Index 2: S2_B4 (Red)
  - [ ] Index 3: S2_B8 (NIR)
  - [ ] Index 4: S1_VV_db_norm
  - [ ] Index 5: S1_VH_db_norm
  - [ ] Index 6: VIIRS_avg_rad_norm
  - [ ] Index 7: S2_valid_mask
  - [ ] Index 8: S2_cloud_prob_norm (optional)

- [ ] **Channel count validation**
  - [ ] `export.yaml`: `band_order` has 8 required + 1 optional entry
  - [ ] `train.yaml`: `input_channels: 8` (base model, cloud_prob optional)
  - [ ] Model can accept variable C ∈ {8, 9} (check input projection layer)

### B. Model Architecture

- [ ] **Token dimensions match spec**
  - [ ] `token_dim: 512` (D=512, NOT 256)
  - [ ] `num_tokens: 256` (N=256)
  - [ ] `spatial_grid: [16, 16]` (16×16 = 256 tokens)
  - [ ] `patch_size: 16` (256 / 16 = 16 patches)

- [ ] **Computed token grid is correct**
  - [ ] Input: [B, 8, 256, 256]
  - [ ] After patching: [B, 16×16, 512] = [B, 256, 512]
  - [ ] Matches N=256, D=512

### C. Temporal Dimensions

- [ ] **Window counts are correct**
  - [ ] Context length: H_ctx = 6
  - [ ] Rollout horizon: H_roll = 6
  - [ ] Total window: 12 months
  - [ ] Expected tiles: 784
  - [ ] Expected months: 48
  - [ ] **Computed num_frames**: 784 × 48 = 37,632 ✓
  - [ ] **Computed num_windows**: 784 × (48 - 6) = 32,928 ✓
  - [ ] Train split (85%): ~28,000 windows
  - [ ] Val split (15%): ~4,900 windows

### D. Action Schema

- [ ] **Action dimension matches config**
  - [ ] `action_dim: 4` in both export and train configs
  - [ ] Action fields defined: [rain_anom, precip_abs, month_sin, month_cos]
  - [ ] Model action_embedding_dim: 128

- [ ] **Action computations specified**
  - [ ] `rain_anom`: CHIRPS z-score vs. climatology
  - [ ] `precip_abs`: Normalized monthly total (mm)
  - [ ] `month_sin`: sin(2π × month / 12)
  - [ ] `month_cos`: cos(2π × month / 12)

- [ ] **Neutral scenario semantics**
  - [ ] Neutral sets all actions to 0
  - [ ] Interpretation: "average weather, unspecified time"
  - [ ] Used for residual-based anomaly detection

### E. Projection & Tiling

- [ ] **Projection correctness**
  - [ ] EPSG:32610 (UTM Zone 10N) for Bay Area
  - [ ] Longitude range [-123.0, -121.5] falls within Zone 10N bounds
  - [ ] Latitude range [36.9, 38.0] is valid
  - [ ] Minimal distortion: <0.1% area variation across AOI

- [ ] **Tile alignment across sources**
  - [ ] S2: Native UTM, reproject to EPSG:32610 if needed
  - [ ] S1: GRD products, reproject to EPSG:32610
  - [ ] VIIRS: Monthly composite, resample to 10m in EPSG:32610
  - [ ] CHIRPS: 0.05° resolution, resample to 10m in EPSG:32610
  - [ ] All sources resampled to exactly 256×256 @ 10m resolution

- [ ] **Tile size and coverage**
  - [ ] Tile size: 256px × 10m = 2.56km per tile
  - [ ] Expected grid: ~28×28 = 784 tiles
  - [ ] Validate: Actual exported tile count matches expected ±5%

### F. Quality Signals

- [ ] **Binary mask present**
  - [ ] S2_valid_mask (index 7) is required
  - [ ] Values: {0, 1}
  - [ ] Created from cloud_prob > 50% threshold

- [ ] **Soft quality signal present (one of)**
  - [ ] Option 1: S2_cloud_prob_norm as 9th channel (preferred)
  - [ ] Option 2: Per-tile metadata field `s2_cloud_mean`
  - [ ] Option 3: Per-token weight map (derived, future work)

- [ ] **Quality metadata exported**
  - [ ] `s2_valid_frac` ∈ [0, 1]
  - [ ] `s2_cloud_mean` ∈ [0, 100]
  - [ ] `s1_coverage` ≥ 1 (at least one S1 obs per month)
  - [ ] `viirs_coverage` ∈ [0, 1]

- [ ] **Minimum quality filter**
  - [ ] `min_s2_valid_frac: 0.3` in train config
  - [ ] Tiles with <30% valid pixels are excluded from training

### G. Anti-Collapse Regularization

- [ ] **Regularizer enabled**
  - [ ] `anticollapse_weight: 0.1` > 0
  - [ ] `anticollapse_type: "variance_covariance"`

- [ ] **VICReg parameters**
  - [ ] `variance_gamma: 1.0`
  - [ ] `covariance_gamma: 1.0`

- [ ] **Monitoring during training**
  - [ ] Log `val/token_variance` (should stay high, >0.1)
  - [ ] Log `val/token_covariance` (should stay low, <0.5)
  - [ ] If variance collapses (<0.01), increase anticollapse_weight

### H. EMA Target Encoder

- [ ] **EMA schedule configured**
  - [ ] `ema_decay_init: 0.996`
  - [ ] `ema_decay_end: 1.0`
  - [ ] `ema_decay_schedule: "cosine"`
  - [ ] Log `ema_decay` metric to verify schedule

### I. Normalization Consistency

- [ ] **S2 reflectance normalization**
  - [ ] SR bands divided by 10,000 → [0, 1]
  - [ ] Matches spec `reflectance_0_1`

- [ ] **S1 dB normalization**
  - [ ] Raw backscatter → dB: 10 × log10(x)
  - [ ] Clamp to [-25, 0]
  - [ ] Normalize: (dB - (-25)) / (0 - (-25)) → [0, 1]
  - [ ] Matches spec `linear_clamp`

- [ ] **VIIRS log normalization**
  - [ ] Apply log1p: log(1 + avg_rad)
  - [ ] Clip to AOI percentiles [p1, p99]
  - [ ] Scale to [0, 1]
  - [ ] Matches spec `percentile_clip`

- [ ] **CHIRPS precipitation**
  - [ ] Monthly sum (mm)
  - [ ] Z-score anomaly: (P_t - μ_m) / (σ_m + 1e-6)
  - [ ] Absolute normalized: P_t / P_max

### J. Config Versioning

- [ ] **Version fields present**
  - [ ] `config_version: "0.3"`
  - [ ] `model_spec_version: "0.2"`
  - [ ] `band_order_version: "v1"`
  - [ ] `preprocessing_version: "v2"`

- [ ] **Version compatibility**
  - [ ] Export config versions match train config versions
  - [ ] Checkpoint metadata includes config versions
  - [ ] Can detect version mismatches at load time

### K. End-to-End Smoke Test

- [ ] **Export dry run passes**
  ```bash
  uv run siad export --config configs/export-bay-area-v03.yaml --dry-run
  ```

- [ ] **Single tile-month export succeeds**
  - [ ] GeoTIFF has 8 or 9 bands
  - [ ] Shape: [C, 256, 256]
  - [ ] Projection metadata: EPSG:32610
  - [ ] Pixel spacing: 10m × 10m

- [ ] **Manifest entry is valid**
  - [ ] JSON parseable
  - [ ] Has all required fields (tile_id, month, gcs_uri, actions, quality)
  - [ ] Actions object has 4+ fields

- [ ] **Model loads and forward pass succeeds**
  ```python
  # Load config and create model
  cfg = load_config("configs/train-bay-area-v03.yaml")
  model = create_jepa_model(cfg)

  # Mock batch
  B, C, H, W = 4, 8, 256, 256
  A = 4
  T = 12
  x = torch.randn(B, T, C, H, W)
  a = torch.randn(B, T, A)

  # Forward pass
  pred, target = model(x, a, context_length=6)

  # Validate shapes
  assert pred.shape == (B, 6, 256, 512)  # 6 rollout steps, N=256 tokens, D=512
  assert target.shape == (B, 6, 256, 512)
  ```

- [ ] **Loss computation succeeds**
  ```python
  loss_dict = model.compute_loss(pred, target)
  assert "jepa_loss" in loss_dict
  assert "anticollapse_loss" in loss_dict
  assert "total_loss" in loss_dict
  assert loss_dict["total_loss"].requires_grad
  ```

### L. Known Risks & Mitigations

- [ ] **Risk: UTM projection may clip tiles at AOI edges**
  - [ ] Mitigation: Validate exported tile count matches expected grid
  - [ ] Mitigation: Check that edge tiles have full 256×256 coverage

- [ ] **Risk: S2_cloud_prob may not be available in all regions/times**
  - [ ] Mitigation: Made 9th channel optional in config
  - [ ] Mitigation: Fallback to 8-channel model if cloud_prob unavailable
  - [ ] Mitigation: Per-tile metadata includes `s2_cloud_mean` as backup

- [ ] **Risk: CHIRPS climatology may be noisy for small AOIs**
  - [ ] Mitigation: Use 10-year window (2015-2024) for robust statistics
  - [ ] Mitigation: Compute AOI-level (not per-tile) climatology
  - [ ] Mitigation: Add epsilon (1e-6) to std to prevent division by zero

- [ ] **Risk: Action dimension expansion breaks backward compatibility**
  - [ ] Mitigation: Version field `preprocessing_version: "v2"` flags the change
  - [ ] Mitigation: Old checkpoints with A=1 cannot load this config (fail fast)

- [ ] **Risk: Anti-collapse weight too high may hurt prediction accuracy**
  - [ ] Mitigation: Start with 0.1 (conservative)
  - [ ] Mitigation: Monitor both anticollapse_loss and jepa_loss
  - [ ] Mitigation: If jepa_loss plateaus high, reduce anticollapse_weight to 0.05

## SUMMARY

This v0.3 configuration migration brings the SIAD export and training pipeline into full compliance with the JEPA World Model specification (MODEL.md). Key improvements:

1. **Correctness**: Fixed critical bugs (token_dim, projection, action schema)
2. **Stability**: Added mandatory anti-collapse regularization
3. **Clarity**: Separated export/train concerns, explicit versioning
4. **Richness**: Enhanced action schema, soft quality signals
5. **Reproducibility**: Documented all computations, expected counts

The configuration is now ready for large-scale export and training with credible residuals for anomaly detection.
