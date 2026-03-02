#!/usr/bin/env python3
"""Storage requirements analysis for SIAD training on cloud GPUs"""

def analyze_storage_needs():
    """Calculate storage requirements for SIAD training"""

    print("="*70)
    print("SIAD Storage Requirements Analysis")
    print("="*70)

    storage_breakdown = {
        "Code & Environment": {
            "SIAD repository": 0.05,  # 50 MB
            "Python packages (UV cache)": 2.0,  # 2 GB (PyTorch, etc.)
            "CUDA libraries": 5.0,  # 5 GB
            "OS overhead": 5.0,  # 5 GB
            "Total": 12.05,
        },
        "Training Data (cached from GCS)": {
            "Dataset (temp cache)": 20.0,  # 20 GB (depends on dataset size)
            "Preprocessed tensors": 10.0,  # 10 GB (cached batches)
            "Total": 30.0,
        },
        "Model & Checkpoints": {
            "Model checkpoint (single)": 0.21,  # 210 MB (54M params × 4 bytes)
            "Checkpoint history (5 epochs)": 1.05,  # 5 × 210 MB
            "Best model": 0.21,  # 210 MB
            "Optimizer states": 0.84,  # 4 × 210 MB (AdamW)
            "Total": 2.31,
        },
        "Logs & Metrics": {
            "Training logs": 0.1,  # 100 MB
            "TensorBoard logs": 0.5,  # 500 MB
            "Total": 0.6,
        },
    }

    print("\n1. Storage Breakdown")
    print("-" * 70)

    total_required = 0
    for category, items in storage_breakdown.items():
        print(f"\n{category}:")
        category_total = items.pop("Total")
        for item, size_gb in items.items():
            print(f"  {item:<35s} {size_gb:>6.2f} GB")
        print(f"  {'─'*35} {'─'*9}")
        print(f"  {'Subtotal':<35s} {category_total:>6.2f} GB")
        total_required += category_total

    print(f"\n{'='*45}")
    print(f"{'TOTAL REQUIRED':<35s} {total_required:>6.2f} GB")
    print(f"{'='*45}")

    # Recommendations
    print("\n2. Storage Configuration Recommendations")
    print("-" * 70)

    configs = [
        {
            "name": "Minimal (tight budget)",
            "container": 30,
            "volume": 50,
            "network": 0,
            "notes": "Just enough, no room for extra experiments"
        },
        {
            "name": "Recommended",
            "container": 30,
            "volume": 100,
            "network": 0,
            "notes": "Comfortable headroom for caching and experiments"
        },
        {
            "name": "Comfortable",
            "container": 50,
            "volume": 200,
            "network": 0,
            "notes": "Plenty of space for multiple runs and datasets"
        },
        {
            "name": "Overkill (avoid)",
            "container": 50,
            "volume": 100,
            "network": 500,
            "notes": "Expensive network volume not needed"
        },
    ]

    for config in configs:
        total = config["container"] + config["volume"] + config["network"]
        marker = "✅" if config["name"] == "Recommended" else "⚠️" if "Overkill" in config["name"] else "💰"

        print(f"\n{marker} {config['name']}")
        print(f"  Container: {config['container']} GB")
        print(f"  Volume:    {config['volume']} GB (temporary)")
        print(f"  Network:   {config['network']} GB")
        print(f"  Total:     {total} GB")
        print(f"  Note:      {config['notes']}")

    # Workflow explanation
    print("\n3. Why You DON'T Need Network Volume")
    print("-" * 70)
    print("""
Your workflow:
1. Start pod → Clone repo from GitHub
2. Download data from GCS to Volume Disk (temp cache)
3. Train model → Save checkpoints to Volume Disk
4. Upload final checkpoint to GCS (permanent storage)
5. Stop pod → Volume Disk erased (but results already in GCS)

Network Volume would cost extra and provide no benefit because:
  • GCS is your permanent storage (free, unlimited)
  • Training is fast (12 min), no need for persistence
  • Checkpoints are small (210 MB), quick to upload to GCS
  • Next run starts fresh anyway (new data, new experiment)
    """)

    # Cost comparison
    print("\n4. Storage Cost Comparison (typical cloud provider)")
    print("-" * 70)

    # Approximate costs (varies by provider)
    volume_disk_cost = 0.10  # $/GB/month for temporary disk
    network_volume_cost = 0.20  # $/GB/month for persistent disk

    print(f"\nVolume Disk (temporary):    ${volume_disk_cost:.2f}/GB/month")
    print(f"Network Volume (persistent): ${network_volume_cost:.2f}/GB/month (2x more!)")

    scenarios = [
        ("Recommended (100 GB volume)", 100, 0),
        ("With network (100 volume + 500 network)", 100, 500),
    ]

    print(f"\n{'Configuration':<40s} {'Monthly Cost':<15s} {'Per-run Cost'}")
    print("-" * 70)

    for name, vol_gb, net_gb in scenarios:
        # Assume 10 training runs per month, each 0.2 hours
        hours_per_month = 10 * 0.2  # 2 hours total
        cost_per_month = (vol_gb * volume_disk_cost) + (net_gb * network_volume_cost)
        cost_per_run = cost_per_month / 10

        marker = "✅" if net_gb == 0 else "❌"
        print(f"{marker} {name:<38s} ${cost_per_month:>6.2f}         ${cost_per_run:>6.2f}")

    print("\nSavings with Volume Disk only: $100/month 💰")

    # Best practices
    print("\n5. Best Practices")
    print("-" * 70)
    print("""
✅ DO:
  • Use Volume Disk (temporary) for /workspace
  • Cache datasets from GCS to local disk during training
  • Save checkpoints locally during training (fast)
  • Upload final checkpoint to GCS before stopping pod
  • Keep GCS as source of truth for data and results

❌ DON'T:
  • Pay for Network Volume (unnecessary for 12-min training)
  • Store data permanently on pod (use GCS instead)
  • Skimp on Volume Disk size (100-200 GB is cheap insurance)
    """)

    # Recommended setup
    print("\n" + "="*70)
    print("RECOMMENDED CONFIGURATION")
    print("="*70)
    print("""
Container Disk:  30 GB  (default, for OS/libraries)
Volume Disk:     100 GB (temporary, for /workspace)
Network Volume:  0 GB   (skip it, use GCS instead)

Total cost:      ~$10/month for storage (negligible vs GPU cost)
GPU cost:        ~$0.95/hr (much larger expense)

Strategy:
  1. Pull data from GCS at training start
  2. Train with local caching on Volume Disk
  3. Push checkpoints to GCS before pod stops
  4. Let Volume Disk be erased (results safe in GCS)
    """)

    print("="*70)


if __name__ == "__main__":
    analyze_storage_needs()
