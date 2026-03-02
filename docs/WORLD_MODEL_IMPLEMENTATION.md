# World Model/Training Agent - Implementation Summary

**Agent**: World Model/Training  
**Date**: 2026-03-01  
**Tasks**: T021-T026, T029

---

## Summary

Agent: **World Model/Training**

**Plan**: Implement action-conditioned world model using ResNet18 encoder for observations (8-channel input), EMA-stabilized target encoder (JEPA-style), 2-layer MLP for actions ([rain_anom, temp_anom] → latent), 1-layer transformer for dynamics (z_t + u_t → z_{t+1}), recursive multi-step rollout for H=6, train with cosine distance loss aggregated across rollout steps.

**Interfaces**:
- **Input**: manifest.jsonl with GeoTIFF paths + anomaly vectors, config (latent_dim, batch_size, epochs)
- **Output**: checkpoint_best.pth with model weights + config metadata
- **Handoff to Detection**: Trained checkpoint for inference rollouts

**Risks**:
1. GPU OOM with 256×256 tiles - mitigation: use batch_size=8 or 16, gradient checkpointing
2. Rollout drift (predictions diverge after k=3) - mitigation: add scheduled sampling, decay loss weights w_k
3. EMA collapse (target encoder not updating) - mitigation: verify momentum=0.996, log EMA parameter norms

**First PR**:
- docs/model-design.md (architecture specification)
- src/siad/model/encoders.py (ResNet18-based ObsEncoder, EMA TargetEncoder, ActionEncoder)
- src/siad/model/dynamics.py (TransformerEncoderLayer with 1 layer)
- src/siad/model/world_model.py (forward pass: context → rollout latents)
- src/siad/train/dataset.py (loads GeoTIFFs via rasterio, stacks to [8, 256, 256])
- src/siad/train/trainer.py (training loop, saves checkpoint every epoch)
- scripts/train_smoke_test.py (train on synthetic data for 3 epochs)
- scripts/create_mock_geotiffs.py (generate realistic test GeoTIFFs)

**Blockers**:
- Need sample manifest.jsonl from Data agent (can mock 2 tiles × 12 months for smoke test) ✓ RESOLVED with mock data
- Confirm: Use cosine distance or MSE for rollout loss? → **RESOLVED: Cosine distance** (default, configurable)

---

## Implementation Details

### Model Architecture

1. **ObsEncoder** (ResNet18-based)
   - Input: [B, 8, 256, 256] GeoTIFF (8 channels: B2/B3/B4/B8, VV/VH, lights, valid)
   - Output: [B, 256] latent representation
   - Modified ResNet18 with 8-channel first conv, AdaptiveAvgPool + Linear projection

2. **TargetEncoder** (EMA-stabilized)
   - Identical architecture to ObsEncoder
   - Updated via EMA: θ̄ ← 0.996×θ̄ + 0.004×θ
   - No gradient flow (parameters frozen, updated after optimizer.step())

3. **ActionEncoder** (2-layer MLP)
   - Input: [B, 2] actions [rain_anom, temp_anom]
   - Output: [B, 256] action embedding
   - Architecture: Linear(2→128) → ReLU → Dropout → Linear(128→256)

4. **TransitionModel** (1-layer Transformer)
   - Input: concatenated [z_t, u_t] → [B, 512]
   - Output: [B, 256] predicted z_{t+1}
   - TransformerEncoderLayer(d_model=256, nhead=8, dim_feedforward=1024)

### Training Pipeline

**Dataset**: `SIADDataset` loads from manifest.jsonl
- Each sample: 12-month tile sequence
- Window: [0:6] context, [6:12] rollout
- Returns: {obs_context: [6,8,256,256], actions_rollout: [6,2], obs_targets: [6,8,256,256]}

**Loss Function**: Multi-step rollout loss
```python
for k in range(6):
    z_pred_k = F(z_pred_{k-1}, u_k)  # Recursive prediction
    z_target_k = TargetEncoder(obs_target_k)  # Stable target
    loss_k = 1 - cos_similarity(z_pred_k, z_target_k)

total_loss = mean(loss_1, ..., loss_6)
```

**Training Loop**:
1. Forward rollout (recursive 6-step predictions)
2. Compute cosine distance loss
3. Backprop, clip gradients (max_norm=1.0)
4. Optimizer step
5. **EMA update target encoder** (critical for JEPA)
6. Save checkpoints (every 5 epochs + best model)

### File Structure

```
src/siad/
├── model/
│   ├── __init__.py
│   ├── encoders.py          # ObsEncoder, TargetEncoder, ActionEncoder
│   ├── dynamics.py           # TransitionModel (Transformer/GRU)
│   └── world_model.py        # WorldModel integration + rollout loss
├── train/
│   ├── __init__.py
│   ├── dataset.py            # SIADDataset (loads GeoTIFFs from manifest)
│   └── trainer.py            # Training loop with EMA, checkpointing
└── ...

scripts/
├── train_smoke_test.py       # Synthetic data smoke test (no GeoTIFFs)
└── create_mock_geotiffs.py   # Generate mock 8-band GeoTIFFs

docs/
├── model-design.md           # Full architecture specification
└── WORLD_MODEL_IMPLEMENTATION.md  # This document
```

---

## Testing & Validation

### Smoke Test (No Real Data)
```bash
# Run on synthetic data (20 training samples, 5 validation)
uv run scripts/train_smoke_test.py

# Expected: 3 epochs, loss decreases, checkpoint saved
```

### Mock GeoTIFF Test
```bash
# Generate 2 tiles × 12 months of 8-band GeoTIFFs
uv run scripts/create_mock_geotiffs.py --output-dir data/mock_test

# Test dataset loading
python -c "
from siad.train import SIADDataset
ds = SIADDataset('data/mock_test/manifest.jsonl', data_root='data/mock_test')
print(f'Loaded {len(ds)} samples')
sample = ds[0]
print(f'obs_context: {sample[\"obs_context\"].shape}')  # [6,8,256,256]
"
```

---

## Handoff to Detection Agent

**Checkpoint Format** (`checkpoint_best.pth`):
```python
{
    "epoch": 50,
    "model_state_dict": {...},
    "config": {
        "latent_dim": 256,
        "context_length": 6,
        "rollout_horizon": 6,
        "band_order_version": "v1",
        "model_architecture": {
            "obs_encoder": "ResNet18",
            "dynamics": "Transformer"
        }
    },
    "seed": 42
}
```

**Loading for Inference**:
```python
from siad.model import WorldModel
import torch

checkpoint = torch.load('checkpoint_best.pth')
config = checkpoint['config']

model = WorldModel(
    latent_dim=config['latent_dim'],
    in_channels=8,
    action_dim=2
)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Run rollouts for acceleration scoring
with torch.no_grad():
    z_pred = model(obs_context, actions_observed)  # [B, 6, 256]
    z_neutral = model(obs_context, actions_neutral)  # Counterfactual
```

---

## Constitution Compliance

**Principle II: Counterfactual Reasoning** ✓
- Action conditioning enables neutral vs observed scenario rollouts
- Detection agent can query: "What if rain_anom=0 instead of +2.0?"

**Principle V: Reproducible Pipelines** ✓
- Seed management: `torch.manual_seed(42)` in trainer
- Full config saved in checkpoint (latent_dim, band_order_version, architecture)
- CLI-scriptable: `uv run scripts/train_smoke_test.py` demonstrates automated pipeline

---

## Status

✓ Implementation complete  
✓ Smoke test passing (synthetic data)  
✓ Mock GeoTIFF generator ready  
✓ Checkpoint format validated  
✓ Ready for integration with Data agent outputs  

**Next**: Data agent provides real manifest.jsonl → Full training on actual satellite imagery
