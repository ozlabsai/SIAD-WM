#!/usr/bin/env python3
"""GPU count and instance type recommendations for SIAD training

Analyzes:
1. Single vs multi-GPU efficiency
2. Spot vs on-demand cost/reliability
3. Recommendations based on training time and interruption risk
"""

def analyze_multi_gpu():
    """Analyze single vs multi-GPU training efficiency"""

    print("="*70)
    print("Multi-GPU Analysis for SIAD (54M params)")
    print("="*70)

    # Training time estimates (single A100)
    single_gpu_time_min = 12  # minutes for batch_size=32

    # Multi-GPU scaling (empirical for transformers)
    # Not linear due to communication overhead
    scaling_efficiency = {
        1: {"speedup": 1.0, "efficiency": 1.0},
        2: {"speedup": 1.7, "efficiency": 0.85},  # 85% efficient
        4: {"speedup": 2.8, "efficiency": 0.70},  # 70% efficient
        8: {"speedup": 4.5, "efficiency": 0.56},  # 56% efficient
    }

    print("\n1. Training Time Comparison (50 epochs)")
    print("-" * 70)
    print(f"{'GPUs':<6} {'Time':<10} {'Speedup':<10} {'Efficiency':<12} {'Cost/hr':<10} {'Total Cost'}")
    print("-" * 70)

    costs_per_gpu = 2.80  # A100 40GB, approximate

    for num_gpus, stats in scaling_efficiency.items():
        time_min = single_gpu_time_min / stats["speedup"]
        time_hr = time_min / 60
        cost_total = time_hr * (costs_per_gpu * num_gpus)
        cost_per_hr = costs_per_gpu * num_gpus

        print(f"{num_gpus:<6} {time_min:>5.1f} min  {stats['speedup']:>5.1f}x     "
              f"{stats['efficiency']:>5.0%}         ${cost_per_hr:>6.2f}    ${cost_total:>6.2f}")

    print("\n2. Analysis")
    print("-" * 70)
    print("✓ Single GPU:    Best efficiency (100%), lowest cost")
    print("✓ 2 GPUs:        Good scaling (1.7x), reasonable if in a hurry")
    print("✗ 4+ GPUs:       Poor efficiency (<70%), higher cost, not worth it")

    print("\n3. Why Multi-GPU Doesn't Help Much Here")
    print("-" * 70)
    print("• Model is small (54M params = 0.2GB)")
    print("• Training is fast (12 min), overhead becomes significant")
    print("• Communication bottleneck: GPUs spend time syncing gradients")
    print("• Data loading is already saturated with single GPU")
    print("• Diminishing returns: 2x GPUs ≠ 2x speed")

    print("\n" + "="*70)
    print("RECOMMENDATION: Use 1 GPU")
    print("="*70)
    print("• Multi-GPU adds complexity without much benefit")
    print("• Save the extra GPUs for parallel experiments instead")
    print("• Run 4 different hyperparameter configs on 4 GPUs simultaneously")
    print("="*70)


def analyze_spot_vs_ondemand():
    """Analyze spot vs on-demand instances"""

    print("\n" + "="*70)
    print("Spot vs On-Demand Analysis")
    print("="*70)

    # Pricing (A100 40GB estimates)
    ondemand_price = 2.80  # $/hr
    spot_price = 0.95      # $/hr (66% discount typical)

    # Training characteristics
    training_time_min = 12
    training_time_hr = training_time_min / 60

    # Interruption risk
    spot_interruption_rate = 0.05  # ~5% chance per hour (varies by region)

    print("\n1. Cost Comparison")
    print("-" * 70)

    # On-demand
    ondemand_cost = training_time_hr * ondemand_price
    print(f"On-Demand:  ${ondemand_price:.2f}/hr × {training_time_hr:.2f}hr = ${ondemand_cost:.2f}")

    # Spot (best case - no interruption)
    spot_cost_best = training_time_hr * spot_price
    print(f"Spot (OK):  ${spot_price:.2f}/hr × {training_time_hr:.2f}hr = ${spot_cost_best:.2f}")

    # Spot (worst case - 1 interruption at 50% progress)
    # Need to restart, so 1.5x time
    spot_cost_worst = (training_time_hr * 1.5) * spot_price
    print(f"Spot (INT): ${spot_price:.2f}/hr × {training_time_hr*1.5:.2f}hr = ${spot_cost_worst:.2f}")

    savings_best = ondemand_cost - spot_cost_best
    savings_worst = ondemand_cost - spot_cost_worst

    print(f"\nSavings:    ${savings_best:.2f} (best) to ${savings_worst:.2f} (with 1 interruption)")

    print("\n2. Interruption Risk Analysis")
    print("-" * 70)

    # Probability of interruption during training
    prob_interrupt = 1 - (1 - spot_interruption_rate) ** training_time_hr

    print(f"Interruption rate:  ~{spot_interruption_rate*100:.0f}% per hour")
    print(f"Training duration:  {training_time_min:.0f} minutes")
    print(f"Interrupt probability: ~{prob_interrupt*100:.1f}% chance during training")

    print("\n3. Trade-offs")
    print("-" * 70)

    print("\n💰 SPOT INSTANCES:")
    print("  Pros:")
    print("    • 66% cheaper ($0.95/hr vs $2.80/hr)")
    print(f"    • Save ${savings_best:.2f} per run (if no interruption)")
    print("    • Good for batch experiments (run multiple, some may interrupt)")
    print("  Cons:")
    print(f"    • ~{prob_interrupt*100:.1f}% chance of interruption during 12-min training")
    print("    • Need robust checkpointing to resume")
    print("    • Annoying to restart (but only loses ~6 min on average)")
    print("    • Not available in all regions/zones")

    print("\n🎯 ON-DEMAND INSTANCES:")
    print("  Pros:")
    print("    • 100% reliable, never interrupted")
    print("    • Predictable costs")
    print("    • Available everywhere")
    print(f"    • Extra ${ondemand_cost - spot_cost_best:.2f} buys peace of mind")
    print("  Cons:")
    print("    • 3x more expensive than spot")

    print("\n4. Break-Even Analysis")
    print("-" * 70)

    # How many interruptions before spot becomes more expensive?
    interruptions_to_breakeven = (ondemand_cost - spot_cost_best) / (spot_cost_worst - spot_cost_best)

    print(f"Spot becomes more expensive after {interruptions_to_breakeven:.1f} interruptions")
    print(f"With {prob_interrupt*100:.1f}% interrupt rate, you'd need ~{1/prob_interrupt:.0f} runs to hit that")

    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)

    print("\n💰 Use SPOT if:")
    print("  • Running many experiments (10+ runs)")
    print("  • Comfortable with occasional restarts")
    print("  • Have good checkpointing (save every epoch)")
    print(f"  • Willing to save ~${savings_best:.2f} per run")
    print("  • Not on a tight deadline")

    print("\n🎯 Use ON-DEMAND if:")
    print("  • Running final production training")
    print("  • Need guaranteed completion")
    print("  • Short on time / deadline-driven")
    print(f"  • ${ondemand_cost:.2f} total cost is acceptable")
    print("  • Want simplicity (no restart hassles)")

    print("\n🧠 SMART STRATEGY:")
    print("  1. Development/tuning: Use SPOT (many experiments, interrupts OK)")
    print("  2. Final training: Use ON-DEMAND (guarantee completion)")
    print("  3. Best of both worlds: Save 66% on 90% of runs, pay premium for final 10%")

    print("\n" + "="*70)


def main():
    """Run all analyses"""
    analyze_multi_gpu()
    analyze_spot_vs_ondemand()

    print("\n" + "="*70)
    print("FINAL RECOMMENDATIONS FOR SIAD")
    print("="*70)

    print("\n📋 Quick Decision Matrix:")
    print("-" * 70)
    print("Situation                          | GPU Count | Instance Type")
    print("-" * 70)
    print("Development/hyperparameter tuning  | 1 GPU     | Spot")
    print("Running many experiments           | 4x 1 GPU  | Spot (parallel)")
    print("Final production training          | 1 GPU     | On-Demand")
    print("Urgent deadline                    | 1 GPU     | On-Demand")
    print("Budget-constrained research        | 1 GPU     | Spot")
    print("-" * 70)

    print("\n⚡ Optimal Setup:")
    print("  • 1× A100 80GB (you have this)")
    print("  • Spot instance for experiments")
    print("  • On-demand for final run")
    print("  • Checkpointing every epoch")
    print("  • Total cost: $0.50-2.00 per experiment")

    print("\n🚀 Pro Tip: Parallel Experiments")
    print("  Instead of 4 GPUs on 1 experiment (poor scaling):")
    print("  → Run 4 different configs on 4× 1-GPU spot instances")
    print("  → 4x more experiments in same time")
    print("  → Better hyperparameter coverage")
    print("  → Same cost, much better science!")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
