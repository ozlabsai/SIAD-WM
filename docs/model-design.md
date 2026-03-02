# SIAD World Model Design

## Overview

This document specifies the architecture for the JEPA-style action-conditioned world model that forms the core of SIAD's infrastructure acceleration detection system.

## Model Architecture

### 1. Observation Encoder (f_θ: x_t → z_t)

**Choice: ResNet18 Backbone (ConvNet baseline)**

- **Input**: [B, 8, 256, 256] (8-channel GeoTIFF observations)
  - Channels: S2 (B2/B3/B4/B8) + S1 (VV/VH) + VIIRS (lights) + S2_valid (mask)
- **Output**: [B, latent_dim=256] latent representation z_t
- **Architecture**:
  - Modified ResNet18 with first conv layer adapted for 8 input channels (instead of 3)
  - Remove final FC layer, replace with adaptive average pooling + linear projection to latent_dim
  - BatchNorm for stability
  - Dropout(p=0.1) to prevent overfitting
- **Rationale**: ResNet18 provides proven feature extraction with ~11M parameters, sufficient for 256×256 tiles without GPU OOM risk. ViT-Tiny considered but deferred due to higher memory footprint for MVP.

### 2. Target Encoder (f_θ̄: x_t → z̃_t) with EMA

**EMA Update Formula**:
```
θ̄ ← momentum × θ̄ + (1 - momentum) × θ
momentum = 0.996 (default, can tune 0.99-0.999)
```

- **Purpose**: JEPA-style stabilization - target encoder provides stable predictions for consistency loss
- **Architecture**: Exact copy of observation encoder, updated via exponential moving average (no gradient flow)
- **Update Timing**: After every optimizer step during training
- **Implementation Notes**:
  - Initialize θ̄ = θ at training start
  - Log EMA parameter norms every 100 steps to verify updates are happening
  - Monitor divergence between θ and θ̄ (should stabilize after warmup)

### 3. Action Encoder (h_φ: a_t → u_t)

**Choice: 2-layer MLP with ReLU**

- **Input**: [B, 2] action vector [rain_anom, temp_anom]
- **Output**: [B, latent_dim=256] action embedding u_t
- **Architecture**:
  ```
  Linear(2 → 128) → ReLU → Dropout(0.1) → Linear(128 → latent_dim)
  ```
- **Rationale**: Actions are low-dimensional scalars, simple MLP sufficient for embedding into latent space. Dropout prevents action overfitting.

### 4. Transition Dynamics Model (F_ψ: (z_t, u_t) → z_{t+1})

**Choice: 1-layer Transformer Encoder (recommended for multi-step)**

- **Input**: Concatenated [z_t, u_t] → [B, latent_dim*2]
- **Output**: z_{t+1} prediction [B, latent_dim]
- **Architecture**:
  ```
  Linear(latent_dim*2 → latent_dim) → positional encoding (optional) →
  TransformerEncoderLayer(d_model=latent_dim, nhead=8, dim_feedforward=1024, dropout=0.1) →
  Linear(latent_dim → latent_dim)
  ```
- **Alternative (GRU)**: Single-layer GRU(latent_dim) for faster training, but transformer preferred for multi-step coherence
- **Rationale**: Transformer's self-attention handles long-range dependencies better for H=6 rollouts. GRU viable fallback if memory-constrained.

## Multi-Step Rollout Loss

### Recursive Rollout Formula (H=6)

For each training sample with context window [t-L+1:t] and rollout [t+1:t+H]:

1. Encode context: z_t = f_θ(x_t) (last context frame)
2. For k = 1 to H:
   - Encode target: z̃_{t+k} = f_θ̄(x_{t+k}) (no gradient, stable target)
   - Predict: ẑ_{t+k} = F_ψ(ẑ_{t+k-1}, u_{t+k-1}) where ẑ_t := z_t initially
   - Compute step loss: L_k = cosine_distance(ẑ_{t+k}, z̃_{t+k})

3. Aggregate loss:
   ```
   L_total = Σ_{k=1}^{H} w_k × L_k
   ```

### Loss Function Choice: Cosine Distance (Recommended)

```python
cosine_distance(ẑ, z̃) = 1 - cos_similarity(ẑ, z̃) = 1 - (ẑ · z̃) / (||ẑ|| ||z̃||)
```

- **Rationale**: Cosine distance focuses on directional alignment, robust to magnitude scaling. Normalized latents prevent gradient explosion.
- **Alternative (MSE)**: Mean squared error if latents are unnormalized. More sensitive to outliers.

### Loss Weights (w_k)

**Option 1 (Uniform)**: w_k = 1.0 for all k (simpler, recommended for MVP)

**Option 2 (Exponential Decay)**: w_k = γ^(k-1) where γ=0.95 (downweight later steps to reduce drift penalty)

**Option 3 (Increasing)**: w_k = k/H (emphasize long-horizon accuracy)

**MVP Default**: Uniform weights (Option 1) for simplicity. Monitor rollout drift; if predictions collapse after k=3, switch to Option 2.

## Dataset Windowing Logic

### Manifest Format (manifest.jsonl)

Each line is a JSON object representing a tile's 12-month sequence:

```json
{
  "tile_id": "tile_x000_y000",
  "months": ["2023-01", "2023-02", ..., "2023-12"],
  "observations": [
    "data/preprocessed/tiles/tile_x000_y000_2023-01.tif",
    "data/preprocessed/tiles/tile_x000_y000_2023-02.tif",
    ...
  ],
  "actions": [
    [0.5, -0.3],  // [rain_anom, temp_anom] for 2023-01
    [0.2, 0.1],   // 2023-02
    ...
  ]
}
```

### Dataset Sampling (L=6 context, H=6 rollout)

From each 12-month tile sequence, extract:
- **obs_context**: GeoTIFFs at indices [0:6] → stack to [6, 8, 256, 256]
- **actions_rollout**: anomaly vectors at indices [6:12] → stack to [6, 2]
- **obs_targets**: GeoTIFFs at indices [6:12] → stack to [6, 8, 256, 256]

**Total samples**: N_tiles × 1 (single window per 12-month tile)

For longer sequences (e.g., 36 months), use sliding windows:
- Window stride = 1 month → (T - L - H + 1) samples per tile

## Training Hyperparameters

```python
{
    "latent_dim": 256,
    "context_length": 6,  # L
    "rollout_horizon": 6,  # H
    "batch_size": 16,      # Reduce to 8 if GPU OOM
    "learning_rate": 1e-4,
    "weight_decay": 1e-5,
    "optimizer": "AdamW",
    "epochs": 50,
    "ema_momentum": 0.996,
    "grad_clip_norm": 1.0,
    "scheduler": "CosineAnnealingLR",
    "warmup_epochs": 5,
    "seed": 42,            # Reproducibility (Principle V)
    "band_order_version": "v1"  # [B2, B3, B4, B8, VV, VH, lights, valid]
}
```

### GPU Memory Estimate (batch_size=16)

- Obs context: 16 × 6 × 8 × 256 × 256 × 4 bytes ≈ 200 MB
- Obs targets: 16 × 6 × 8 × 256 × 256 × 4 bytes ≈ 200 MB
- Model params: ~15M params × 4 bytes ≈ 60 MB
- Activations + gradients: ~2-3x model size ≈ 150 MB
- **Total**: ~600-700 MB per batch → Safe for 8GB GPU

**Mitigation for OOM**:
1. Reduce batch_size to 8
2. Enable gradient checkpointing (recompute activations during backward pass)
3. Use mixed precision (FP16) via torch.cuda.amp

## Checkpoint Format

Saved as `checkpoint_epoch_{N}.pth`:

```python
{
    "epoch": int,
    "model_state_dict": {
        "obs_encoder": {...},
        "target_encoder": {...},
        "action_encoder": {...},
        "dynamics": {...}
    },
    "optimizer_state_dict": {...},
    "scheduler_state_dict": {...},
    "train_loss": float,
    "val_loss": float,
    "config": {
        "latent_dim": 256,
        "context_length": 6,
        "rollout_horizon": 6,
        "band_order_version": "v1",
        "ema_momentum": 0.996,
        "model_architecture": {
            "obs_encoder": "ResNet18",
            "dynamics": "Transformer"
        }
    },
    "seed": 42
}
```

**Best checkpoint** saved separately as `checkpoint_best.pth` (lowest validation loss).

## Failure Modes & Mitigations

### 1. GPU Out-of-Memory (OOM)

**Symptoms**: CUDA out of memory error during training
**Mitigations**:
- Reduce batch_size from 16 → 8 → 4
- Enable gradient checkpointing in ResNet18
- Use mixed precision training (torch.cuda.amp)
- Process on CPU if no GPU available (slower but functional)

### 2. NaN Loss

**Symptoms**: Loss becomes NaN after a few steps
**Root Causes**:
- Gradient explosion (very large updates)
- Division by zero in cosine similarity
- Unstable normalization
**Mitigations**:
- Enable gradient clipping (max_norm=1.0)
- Add epsilon=1e-8 to cosine similarity denominator
- Check for NaN in inputs (invalid GeoTIFF pixels)
- Verify batch normalization stability (switch to LayerNorm if needed)

### 3. Rollout Drift

**Symptoms**: Predictions diverge after k=3, loss plateaus high
**Root Causes**:
- Compounding errors in recursive rollouts
- Action conditioning too weak
- Target encoder collapse (not updating)
**Mitigations**:
- Add scheduled sampling (mix ground-truth z_t with predictions during training)
- Use exponential decay loss weights (w_k = 0.95^(k-1))
- Verify EMA momentum (log θ̄ parameter norms)
- Reduce rollout horizon during warmup (H=3 for first 10 epochs, then H=6)

### 4. EMA Target Encoder Collapse

**Symptoms**: Target encoder outputs identical to observation encoder (EMA not updating)
**Root Causes**:
- Momentum too high (θ̄ frozen)
- Update logic not called
**Mitigations**:
- Log EMA parameter difference: ||θ - θ̄|| every 100 steps
- Verify update_target_encoder() called after optimizer.step()
- Try lower momentum (0.99 instead of 0.996)

### 5. Action Conditioning Ignored

**Symptoms**: Model predictions don't change when varying rain_anom/temp_anom
**Root Causes**:
- Action encoder outputs near-zero (vanishing gradients)
- Dynamics model ignoring action embeddings
**Mitigations**:
- Monitor action encoder output norm (should be ~1.0 after warmup)
- Increase action encoder hidden dim (128 → 256)
- Add action residual connection: z_{t+1} = F(z_t) + u_t (direct action influence)

## Implementation Checklist

- [ ] Verify 8-channel input handling in ResNet18 first conv layer
- [ ] Implement EMA update in training loop (not optimizer hook)
- [ ] Add gradient clipping before optimizer.step()
- [ ] Save checkpoint every epoch + best checkpoint tracking
- [ ] Log train/val loss, EMA divergence, action norms to TensorBoard/WandB
- [ ] Test forward pass with dummy batch before training
- [ ] Verify reproducibility (same seed → same results)

## References

- JEPA (Joint Embedding Predictive Architecture): Assran et al., 2023
- ResNet: He et al., 2016
- Transformer: Vaswani et al., 2017
- EMA for self-supervised learning: Grill et al., 2020 (BYOL)
