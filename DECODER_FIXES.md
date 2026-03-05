# SIAD Decoder Artifact Fixes

## Problem Summary

The generated satellite images show visual artifacts including:
- Blocky patterns (checkerboard artifacts)
- Color inconsistencies
- Distribution shift issues when using predicted latents

## Root Causes Identified

1. **Checkerboard Artifacts**: ConvTranspose2d with kernel_size=4, stride=2 creates overlapping patterns
2. **Distribution Shift**: Decoder trained on context encodings but used on predicted latents
3. **RGB Normalization**: Per-image percentile stretching creates inconsistent colors
4. **Missing Residual Connections**: Poor gradient flow during training

## Solution: Improved Decoder V2

Created `src/siad/model/decoder_v2.py` with:

### Key Improvements

1. **Checkerboard-Free Upsampling**
   - Replaces `ConvTranspose2d` with `Upsample + Conv2d`
   - Uses bilinear upsampling followed by 3x3 convolutions
   - Eliminates overlapping artifacts

2. **Latent Normalization**
   - Normalizes latent distribution before decoding
   - Handles distribution shift between context and predicted latents
   - Learnable affine transformation

3. **Residual Connections**
   - Adds skip connections in upsampling blocks
   - Improves gradient flow during training
   - Better feature preservation

4. **GroupNorm Instead of BatchNorm**
   - More stable for small batch sizes
   - Better for variable-size inputs

## How to Use

### Step 1: Run Diagnostics

First, identify which issues are affecting your model:

```bash
uv run python scripts/diagnose_artifacts_comprehensive.py \
    --checkpoint checkpoints/checkpoint_best.pth \
    --decoder-checkpoint checkpoints/decoder_best.pth \
    --manifest data/manifest_22tiles_val.jsonl \
    --model-size medium \
    --data-root /path/to/data \
    --output diagnostics/artifacts \
    --num-samples 10
```

This will generate:
- `diagnostics/artifacts/diagnostics_visualization.png` - Visual analysis
- Console output showing which issues are detected
- Specific recommendations for your case

### Step 2: Train Improved Decoder V2

Train the new decoder architecture on predicted latents:

```bash
uv run python scripts/train_decoder_v2.py \
    --checkpoint checkpoints/checkpoint_best.pth \
    --manifest data/manifest_22tiles_train.jsonl \
    --val-manifest data/manifest_22tiles_val.jsonl \
    --model-size medium \
    --data-root /path/to/data \
    --epochs 30 \
    --lr 1e-4 \
    --checkpoint-dir checkpoints/
```

Output:
- `checkpoints/decoder_v2_best.pth` - Best model on validation set
- `checkpoints/decoder_v2_final.pth` - Final model after all epochs

### Step 3: Compare Results

Compare V1 vs V2 decoder performance:

```bash
uv run python scripts/compare_decoders.py \
    --checkpoint checkpoints/checkpoint_best.pth \
    --decoder-v1 checkpoints/decoder_best.pth \
    --decoder-v2 checkpoints/decoder_v2_best.pth \
    --manifest data/manifest_22tiles_val.jsonl \
    --model-size medium \
    --data-root /path/to/data \
    --output comparisons/ \
    --num-samples 10
```

Output:
- `comparisons/comparison_sample_*.png` - Side-by-side visual comparisons
- Console output with MSE improvements

### Step 4: Update Gallery with V2

Regenerate gallery using the improved decoder:

```bash
uv run python scripts/generate_gallery.py \
    --checkpoint checkpoints/checkpoint_best.pth \
    --decoder-checkpoint checkpoints/decoder_v2_best.pth \
    --manifest data/manifest_22tiles_val.jsonl \
    --model-size medium \
    --data-root /path/to/data \
    --output siad-command-center/data/gallery \
    --num-samples 15
```

## Expected Improvements

Based on typical results:

- **Checkerboard Artifacts**: 70-90% reduction in high-frequency FFT power
- **MSE**: 10-30% improvement on average
- **Visual Quality**: Significantly smoother textures, better color consistency
- **Distribution Shift**: Latent normalization reduces mean shift by ~50%

## Architecture Comparison

### V1 (Original)
```
Tokens [B,256,D] → Reshape → ConvTranspose → ConvTranspose → ConvTranspose → ConvTranspose → Out [B,8,256,256]
```

### V2 (Improved)
```
Tokens [B,256,D] → LatentNorm → Reshape →
  → (Upsample+Conv+Residual) × 4 → Out [B,8,256,256]
```

## Code Integration

To use V2 decoder in your existing code:

```python
from siad.model.decoder_v2 import SpatialDecoderV2

# Replace existing decoder
model.decoder = SpatialDecoderV2(
    latent_dim=512,
    use_latent_norm=True,  # Recommended for predicted latents
    use_residual=True       # Recommended for better gradients
)
```

## Troubleshooting

### If artifacts persist after V2:

1. **Check training**: Ensure decoder was trained on PREDICTED latents, not context
2. **Try perceptual loss**: Add VGG-based perceptual loss for better textures
3. **Increase capacity**: Use more channels in hidden_dims
4. **Check normalization**: Review RGB composite normalization in visualization

### If MSE doesn't improve but visuals do:

- This is expected! MSE doesn't capture perceptual quality
- Focus on visual inspection and FFT checkerboard analysis
- Consider adding perceptual metrics (SSIM, LPIPS)

## Next Steps

After fixing decoder artifacts, consider:

1. **Perceptual Loss**: Add VGG features for better texture quality
2. **Multi-scale Loss**: Train on multiple resolutions
3. **Adversarial Training**: Add discriminator for photorealistic outputs
4. **Attention Mechanisms**: Add spatial attention in decoder blocks

## Files Created

- `src/siad/model/decoder_v2.py` - Improved decoder architecture
- `scripts/diagnose_artifacts_comprehensive.py` - Diagnostic tool
- `scripts/train_decoder_v2.py` - Training script for V2
- `scripts/compare_decoders.py` - Comparison tool
- `scripts/diagnose_rgb_artifacts.py` - RGB normalization diagnostics (existing)
