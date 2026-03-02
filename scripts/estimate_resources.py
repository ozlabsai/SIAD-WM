#!/usr/bin/env python3
"""Estimate compute resources needed for SIAD training

Calculates:
1. Model parameter count and memory
2. Training memory (activations, gradients, optimizer states)
3. Recommended GPU specs
4. Cost-performance analysis
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from siad.model import WorldModel


def count_parameters(model):
    """Count trainable and total parameters"""
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total


def estimate_model_memory(num_params, dtype_bytes=4):
    """Estimate model memory (parameters only)

    Args:
        num_params: Number of parameters
        dtype_bytes: 4 for fp32, 2 for fp16/bf16
    """
    return num_params * dtype_bytes / (1024**3)  # GB


def estimate_training_memory(
    num_params,
    batch_size,
    sequence_length,  # H for rollout
    num_tokens,       # N = 256
    latent_dim,       # D = 512
    dtype_bytes=2     # fp16/bf16 mixed precision
):
    """Estimate total training memory

    Components:
    1. Model parameters (fp32 master copy)
    2. Gradients (fp32)
    3. Optimizer states (AdamW = 2x params for momentum + variance)
    4. Activations (largest: intermediate rollout states)
    """
    # 1. Model parameters (fp32 master copy for mixed precision)
    model_mem = estimate_model_memory(num_params, dtype_bytes=4)

    # 2. Gradients (fp32)
    grad_mem = model_mem

    # 3. Optimizer states (AdamW: momentum + variance)
    optimizer_mem = 2 * model_mem

    # 4. Activations (forward pass, largest tensor)
    # Rollout: [B, H, N, D] predictions + targets
    # Plus encoder outputs, transition intermediates
    rollout_activations = 2 * batch_size * sequence_length * num_tokens * latent_dim * dtype_bytes / (1024**3)

    # Transformer activations (attention maps, MLPs)
    # Rough estimate: ~3x the rollout tensor size for all intermediate activations
    transformer_activations = 3 * rollout_activations

    total_activations = rollout_activations + transformer_activations

    # Total
    total = model_mem + grad_mem + optimizer_mem + total_activations

    breakdown = {
        "model_params": model_mem,
        "gradients": grad_mem,
        "optimizer": optimizer_mem,
        "activations": total_activations,
        "total": total
    }

    return breakdown


def recommend_gpu(total_memory_gb, batch_size):
    """Recommend GPU based on memory requirements"""

    # Add 20% safety margin
    required_vram = total_memory_gb * 1.2

    gpus = {
        "L4": {
            "vram": 24,
            "price_per_hr": 0.70,  # Approx GCP/AWS pricing
            "tflops_fp16": 121,
            "good_for": "Development, small-scale training"
        },
        "A10": {
            "vram": 24,
            "price_per_hr": 1.00,
            "tflops_fp16": 125,
            "good_for": "Cost-effective training"
        },
        "RTX 6000 Ada": {
            "vram": 48,
            "price_per_hr": 1.50,
            "tflops_fp16": 183,
            "good_for": "Single-GPU workstation training"
        },
        "A100 40GB": {
            "vram": 40,
            "price_per_hr": 2.80,
            "tflops_fp16": 312,
            "good_for": "Fast training, medium batches"
        },
        "A100 80GB": {
            "vram": 80,
            "price_per_hr": 4.00,
            "tflops_fp16": 312,
            "good_for": "Large batches, long sequences"
        },
        "H100": {
            "vram": 80,
            "price_per_hr": 5.50,
            "tflops_fp16": 989,
            "good_for": "Maximum speed, production training"
        },
        "H200": {
            "vram": 141,
            "price_per_hr": 7.00,  # Estimated
            "tflops_fp16": 989,
            "good_for": "Extreme batch sizes, research"
        },
        "B200": {
            "vram": 192,
            "price_per_hr": 10.00,  # Estimated
            "tflops_fp16": 2250,
            "good_for": "Future-proofing, multi-model training"
        }
    }

    print(f"\n{'='*70}")
    print(f"GPU Recommendations (Required VRAM: {required_vram:.1f}GB)")
    print(f"{'='*70}")

    viable = []
    for name, specs in gpus.items():
        fits = specs["vram"] >= required_vram
        status = "✓" if fits else "✗"

        if fits:
            utilization = (required_vram / specs["vram"]) * 100
            cost_per_epoch = specs["price_per_hr"] * 0.5  # Assume ~30min per epoch

            print(f"\n{status} {name:15s} | {specs['vram']}GB VRAM | ${specs['price_per_hr']:.2f}/hr")
            print(f"  Utilization: {utilization:.1f}% | ~${cost_per_epoch:.2f} per epoch")
            print(f"  {specs['tflops_fp16']} TFLOPS (FP16) | {specs['good_for']}")

            viable.append({
                "name": name,
                "specs": specs,
                "utilization": utilization,
                "cost_efficiency": specs["tflops_fp16"] / specs["price_per_hr"]
            })
        else:
            shortage = required_vram - specs["vram"]
            print(f"\n{status} {name:15s} | {specs['vram']}GB VRAM (short {shortage:.1f}GB)")

    if not viable:
        print("\n⚠ No GPUs have sufficient VRAM!")
        print(f"  Consider: Reduce batch size or sequence length")
        return None

    # Rank by cost efficiency
    best = max(viable, key=lambda x: x["cost_efficiency"])
    print(f"\n{'='*70}")
    print(f"RECOMMENDED: {best['name']}")
    print(f"  Best cost/performance for this workload")
    print(f"  {best['specs']['tflops_fp16']} TFLOPS at ${best['specs']['price_per_hr']:.2f}/hr")
    print(f"{'='*70}")

    return viable


def main():
    """Estimate resource requirements"""
    print("="*70)
    print("SIAD World Model Resource Estimation")
    print("="*70)

    # Create model
    print("\n1. Model Architecture")
    print("-" * 70)
    model = WorldModel(
        in_channels=8,
        latent_dim=512,
        action_dim=1,
        encoder_blocks=4,
        transition_blocks=6,
        dropout=0.0
    )

    trainable, total = count_parameters(model)
    print(f"Parameters (trainable): {trainable:,}")
    print(f"Parameters (total):     {total:,}")
    print(f"Model size (fp32):      {estimate_model_memory(total, 4):.2f} GB")
    print(f"Model size (fp16):      {estimate_model_memory(total, 2):.2f} GB")

    # Training configurations
    configs = [
        {"name": "Small (dev)", "batch_size": 4, "horizon": 6},
        {"name": "Medium", "batch_size": 8, "horizon": 6},
        {"name": "Large", "batch_size": 16, "horizon": 6},
        {"name": "XLarge", "batch_size": 32, "horizon": 6},
    ]

    print("\n2. Training Memory Estimates (Mixed Precision fp16)")
    print("-" * 70)

    for config in configs:
        name = config["name"]
        bs = config["batch_size"]
        H = config["horizon"]

        mem = estimate_training_memory(
            num_params=total,
            batch_size=bs,
            sequence_length=H,
            num_tokens=256,
            latent_dim=512,
            dtype_bytes=2
        )

        print(f"\n{name:15s} (batch={bs}, H={H})")
        print(f"  Model params:   {mem['model_params']:6.2f} GB")
        print(f"  Gradients:      {mem['gradients']:6.2f} GB")
        print(f"  Optimizer:      {mem['optimizer']:6.2f} GB")
        print(f"  Activations:    {mem['activations']:6.2f} GB")
        print(f"  TOTAL:          {mem['total']:6.2f} GB")

        # Recommend GPU for this config
        if name == "Medium":  # Show detailed breakdown for medium config
            recommend_gpu(mem['total'], bs)

    # System recommendations
    print("\n" + "="*70)
    print("3. System Recommendations")
    print("="*70)
    print("\nCPU/RAM:")
    print("  CPU cores:  8-16 cores (for data loading)")
    print("  RAM:        32-64 GB (for dataset caching)")
    print("  Storage:    500GB+ SSD (for GCS cache + checkpoints)")

    print("\nTraining Speed Estimates (Medium config, H100):")
    print("  ~30-45 seconds per epoch (depends on dataset size)")
    print("  ~50 epochs = 25-40 minutes total")
    print("  Cost: ~$2-4 per full training run")

    print("\n" + "="*70)
    print("4. Recommendations Summary")
    print("="*70)
    print("\n💰 Best Value:    L4 or A10 (batch=4-8)")
    print("   - $0.70-1.00/hr")
    print("   - Good for development and initial experiments")
    print("   - Can run batch_size=4-8 comfortably")

    print("\n⚡ Best Speed:    H100 (batch=16-32)")
    print("   - $5.50/hr")
    print("   - 3x faster than A100")
    print("   - Can run batch_size=16-32")
    print("   - Best for production training")

    print("\n🎯 Recommended:   A100 40GB (batch=8-12)")
    print("   - $2.80/hr")
    print("   - Best price/performance balance")
    print("   - Widely available on GCP/AWS/Lambda")
    print("   - Can run batch_size=8-12")

    print("\n❌ Skip:          H200, B200")
    print("   - Overkill for this model size (~54M params)")
    print("   - Better for 1B+ parameter models")
    print("   - Much higher cost without proportional benefit")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
