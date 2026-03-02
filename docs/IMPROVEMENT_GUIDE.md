# SIAD Model Improvement Guide

Your small model achieved **0.0888 validation loss** - a good starting point! Here's how to systematically improve it.

## Priority 1: More Training Data (Highest ROI)

**Current**: 20 tiles, 690 observations  
**Target**: 100-500 tiles, 3,600-18,000 observations

### Why This Matters Most
- Neural scaling laws: 5× more data → ~20-30% better performance
- Better geographic diversity → stronger generalization
- More robust to distribution shift

### How to Scale Up

```bash
# 1. Update export configuration
vim configs/test-export.yaml
# Change: num_tiles: 100 (or 200, 500)

# 2. Run export (takes ~1-2 hours for 100 tiles)
GOOGLE_CLOUD_PROJECT=siad-earth-engine uv run siad export \
    --config configs/test-export.yaml

# 3. Download to A100
gsutil -m cp -r gs://siad-earth-engine/geotiffs data/

# 4. Create manifest
uv run python scripts/create_manifest.py \
    --data-dir data/geotiffs \
    --output data/manifest.jsonl \
    --min-months 12

# 5. Train with more data
MODEL_SIZE=medium ./scripts/train_a100.sh data/manifest.jsonl
```

**Expected improvement**: 0.0888 → **0.06-0.07** loss

---

## Priority 2: Larger Model (Medium ROI)

**Current**: Small (157M params)  
**Options**: Medium (400M), Large (1.2B), XLarge (3B)

### Model Scaling Strategy

```bash
# Medium model (best for 100-500 tiles)
MODEL_SIZE=medium ./scripts/train_a100.sh data/manifest.jsonl
# Expected: 0.0888 → 0.075-0.080 loss
# Training time: ~45 min

# Large model (best for 500+ tiles)
MODEL_SIZE=large ./scripts/train_a100.sh data/manifest.jsonl
# Expected: 0.075 → 0.060-0.070 loss
# Training time: ~2 hours

# XLarge model (requires 1000+ tiles)
MODEL_SIZE=xlarge ./scripts/train_a100.sh data/manifest.jsonl
# Expected: 0.060 → 0.045-0.055 loss
# Training time: ~4-5 hours
```

**Rule of thumb**: Model size should match data size
- 20 tiles → tiny/small
- 100 tiles → small/medium  
- 500 tiles → medium/large
- 1000+ tiles → large/xlarge

---

## Priority 3: Longer Context Window (High ROI for Temporal Tasks)

**Current**: 1-month context  
**Better**: 3-6 month context

### Why Longer Context Helps
- Current model only sees 1 month to predict next 6 months
- Seasonal patterns require multi-month history
- Crop cycles, weather patterns need longer memory

### Implementation

```python
# In scripts/train.py, line 55:
context_length=3,  # Changed from 1

# Or use configuration file:
# configs/training_configs.yaml has preset configs
```

**Memory impact**:
- context_length=1: 32 batch size  
- context_length=3: 24 batch size (33% more memory)
- context_length=6: 16 batch size (2× more memory)

**Expected improvement**: 0.0888 → **0.075-0.080** loss

---

## Priority 4: Training Hyperparameters

### Learning Rate Schedule

Current uses constant LR with linear warmup. Try cosine decay:

```python
# In trainer.py, add:
from torch.optim.lr_scheduler import CosineAnnealingLR

scheduler = CosineAnnealingLR(
    optimizer,
    T_max=epochs,
    eta_min=1e-6
)
```

### Longer Training

Current: 50 epochs  
Try: 100-200 epochs with lower learning rate

```bash
# Set environment variables:
EPOCHS=100 LR=5e-5 ./scripts/train_a100.sh data/manifest.jsonl
```

### Data Augmentation

Add random crops, flips, brightness jitter:

```python
# In dataset.py:
def augment(self, x):
    # Random horizontal flip
    if random.random() > 0.5:
        x = np.flip(x, axis=-1)
    
    # Random brightness (±10%)
    x = x * (0.9 + 0.2 * random.random())
    
    return x
```

**Expected improvement**: 5-10% better generalization

---

## Priority 5: Architecture Improvements

### 1. **Hierarchical Latent Space**

Current: Flat 256 tokens at single resolution  
Better: Multi-scale tokens (16 + 64 + 256)

```python
# Encode at multiple resolutions
z_coarse = encode(downsample(x, 4))   # 16 tokens
z_medium = encode(downsample(x, 2))   # 64 tokens  
z_fine = encode(x)                     # 256 tokens
```

### 2. **Temporal Attention**

Add cross-attention between context frames:

```python
# In transition model:
temporal_attention = CrossAttention(
    query=z_current,
    key_value=z_context_history
)
```

### 3. **Action Conditioning Enhancement**

Current: Simple FiLM modulation  
Better: Learned action embeddings + cross-attention

---

## Recommended Experiment Sequence

### Phase 1: Data Scaling (Do This First!)
```bash
# Week 1: Export 100 tiles
num_tiles: 100
# Train: small, medium, large
# Expected best: medium @ 0.070 loss

# Week 2: Export 200 tiles
num_tiles: 200
# Train: medium, large
# Expected best: large @ 0.055 loss
```

### Phase 2: Architecture Tuning
```bash
# Try longer context
context_length: 3
# Expected: 0.055 → 0.050 loss

# Try longer rollout
rollout_horizon: 12  # Full year predictions
```

### Phase 3: Hyperparameter Sweep
```bash
# Try different learning rates, batch sizes, epochs
# Use wandb sweeps for efficient search
```

---

## Evaluation Best Practices

### 1. **Geographic Holdout**

Current: Random 80/20 split  
Better: Spatial split

```python
# Hold out entire regions for testing
train_tiles = tiles[:80]  # Western region
val_tiles = tiles[80:]    # Eastern region
```

### 2. **Temporal Holdout**

Test on future months not seen during training:

```python
# Train on 2021-2022
# Test on 2023
```

### 3. **Per-Band Metrics**

Track loss per channel to diagnose issues:

```python
metrics = {
    'mse_rgb': mse(pred[:, :3], target[:, :3]),
    'mse_nir': mse(pred[:, 3], target[:, 3]),
    'mse_sar': mse(pred[:, 4:6], target[:, 4:6]),
    'mse_nightlights': mse(pred[:, 6], target[:, 6])
}
```

---

## Expected Performance Roadmap

| Configuration | Loss | Quality |
|--------------|------|---------|
| Current (small, 20 tiles, L=1) | 0.0888 | ✅ Good |
| Medium, 100 tiles, L=1 | 0.070 | ✅ Good |
| Medium, 100 tiles, L=3 | 0.065 | ✅✅ Very Good |
| Large, 200 tiles, L=3 | 0.055 | ✅✅ Very Good |
| Large, 500 tiles, L=6 | 0.045 | ✅✅✅ Excellent |
| XLarge, 1000 tiles, L=6 | 0.035 | 🏆 State-of-art |

---

## Quick Wins (Can Do Today)

1. **Train medium model on existing data**
   ```bash
   MODEL_SIZE=medium ./scripts/train_a100.sh data/manifest.jsonl
   # 45 minutes → ~0.075 loss
   ```

2. **Longer training**
   ```bash
   EPOCHS=100 ./scripts/train_a100.sh data/manifest.jsonl
   # Better convergence
   ```

3. **Upload models to HuggingFace**
   ```bash
   ./scripts/upload_model.sh checkpoints/checkpoint_best.pth small OzLabs/siad-wm-small
   # Share with community
   ```

---

## Long-term Goals

### Research Direction: Climate Impact Modeling

Once you have a good model (0.04-0.05 loss):

1. **Train with real climate actions** (not dummy [0,0])
   - Use actual rainfall and temperature data
   - Learn causal relationships

2. **Counterfactual predictions**
   - "What if temperature was 2°C higher?"
   - "What if rainfall decreased 20%?"

3. **Uncertainty quantification**
   - Ensemble predictions
   - Confidence intervals

4. **Attention visualization**
   - Which regions affect predictions?
   - Temporal attention patterns

---

## Questions to Guide Experimentation

Before each experiment, ask:

1. **What's the hypothesis?**
   - "More data → better generalization"
   - "Longer context → better temporal modeling"

2. **How will I measure success?**
   - Validation loss on held-out tiles
   - Per-band MSE
   - Visual quality of predictions

3. **What's the cost?**
   - Training time
   - Data collection time
   - Computational resources

4. **Is this the bottleneck?**
   - Is the model underfitting? → Increase capacity
   - Is it overfitting? → More data or regularization
   - Is loss not decreasing? → Better optimization

---

## Next Steps

**Immediate (This Week)**:
- [ ] Train medium model on current 20 tiles
- [ ] Export 100 tiles from Earth Engine
- [ ] Upload small model to HuggingFace

**Short-term (Next 2 Weeks)**:
- [ ] Train medium/large on 100 tiles
- [ ] Implement context_length=3
- [ ] Set up spatial holdout evaluation

**Long-term (Next Month)**:
- [ ] Export 500 tiles
- [ ] Train xlarge model
- [ ] Add real climate actions
- [ ] Publish results

Start with more data - it's the highest leverage improvement! 🚀
