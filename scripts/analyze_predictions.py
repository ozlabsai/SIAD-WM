#!/usr/bin/env python3
"""Analyze prediction quality to verify model learning

Checks if the model is actually learning or just doing trivial predictions.

Tests:
1. Temporal change detection - Do predictions differ from context?
2. Action sensitivity - Do different climate actions produce different predictions?
3. Spatial variation - Are predictions spatially coherent?
4. Persistence baseline - Is model better than just repeating last frame?
"""

import argparse
import numpy as np
from pathlib import Path
import json


def analyze_gallery(gallery_path: str):
    """Analyze prediction quality from gallery data"""
    gallery_path = Path(gallery_path)

    print("="*60)
    print("SIAD Prediction Quality Analysis")
    print("="*60)

    # Load all tiles
    tile_files = list(gallery_path.glob("tile_*.npz"))

    if len(tile_files) == 0:
        print("ERROR: No gallery tiles found!")
        return

    print(f"\nAnalyzing {len(tile_files)} tiles...")

    results = {
        'temporal_change': [],
        'persistence_improvement': [],
        'spatial_variance': [],
        'action_sensitivity': []
    }

    for tile_file in tile_files:
        data = np.load(tile_file)

        context = data['context_rgb']
        predictions = data['pred_rgbs']
        targets = data['target_rgbs']
        actions = data['actions']

        # Test 1: Temporal Change Detection
        # Compare first prediction to context
        context_pred_diff = np.mean(np.abs(predictions[0] - context))
        results['temporal_change'].append(context_pred_diff)

        # Test 2: Persistence Baseline
        # Is model better than just repeating the last frame?
        persistence_errors = []
        model_errors = []

        for t in range(len(targets)):
            # Persistence: use context as prediction
            persistence_err = np.mean((context - targets[t]) ** 2)

            # Model: actual prediction
            model_err = np.mean((predictions[t] - targets[t]) ** 2)

            persistence_errors.append(persistence_err)
            model_errors.append(model_err)

        avg_persistence = np.mean(persistence_errors)
        avg_model = np.mean(model_errors)

        improvement = (avg_persistence - avg_model) / avg_persistence * 100
        results['persistence_improvement'].append(improvement)

        # Test 3: Spatial Variance
        # Check if predictions have spatial structure (not uniform)
        spatial_var = np.std(predictions[0])
        results['spatial_variance'].append(spatial_var)

        # Test 4: Action Sensitivity (if we had multiple runs)
        # For now, just check if actions vary
        action_var = np.std(actions)
        results['action_sensitivity'].append(action_var)

    # Print results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    print("\n1. TEMPORAL CHANGE DETECTION")
    print(f"   Mean difference (context → pred1): {np.mean(results['temporal_change']):.4f}")
    print(f"   Expected: >0.01 for meaningful change")
    if np.mean(results['temporal_change']) < 0.01:
        print("   ⚠️  WARNING: Predictions barely differ from context!")
        print("   → Model may be learning identity mapping")
    else:
        print("   ✓ Predictions show temporal evolution")

    print("\n2. PERSISTENCE BASELINE COMPARISON")
    avg_improvement = np.mean(results['persistence_improvement'])
    print(f"   Improvement over persistence: {avg_improvement:.1f}%")
    print(f"   Expected: >10% for learned model")
    if avg_improvement < 5:
        print("   ⚠️  WARNING: Model barely beats persistence baseline!")
        print("   → Model may not have learned temporal dynamics")
    else:
        print(f"   ✓ Model outperforms naive persistence")

    print("\n3. SPATIAL VARIANCE")
    avg_spatial_var = np.mean(results['spatial_variance'])
    print(f"   Mean spatial std dev: {avg_spatial_var:.4f}")
    print(f"   Expected: >0.05 for spatial structure")
    if avg_spatial_var < 0.02:
        print("   ⚠️  WARNING: Predictions are spatially uniform!")
        print("   → Model may be predicting constant values")
    else:
        print("   ✓ Predictions have spatial structure")

    print("\n4. ACTION SENSITIVITY")
    avg_action_var = np.mean(results['action_sensitivity'])
    print(f"   Climate action variance: {avg_action_var:.4f}")
    if avg_action_var == 0:
        print("   ℹ️  All tiles used same climate actions (expected for gallery)")
    else:
        print(f"   ✓ Climate actions vary across tiles")

    # Overall assessment
    print("\n" + "="*60)
    print("OVERALL ASSESSMENT")
    print("="*60)

    issues = []
    if np.mean(results['temporal_change']) < 0.01:
        issues.append("No temporal evolution")
    if avg_improvement < 5:
        issues.append("Doesn't beat persistence")
    if avg_spatial_var < 0.02:
        issues.append("No spatial structure")

    if len(issues) == 0:
        print("✓ Model appears to have learned meaningful patterns!")
        print(f"  - Predictions evolve temporally")
        print(f"  - Outperforms persistence baseline by {avg_improvement:.1f}%")
        print(f"  - Maintains spatial structure")
    else:
        print("⚠️  POTENTIAL LEARNING ISSUES DETECTED:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRECOMMENDATIONS:")
        print("  1. Check training loss curves - did loss actually decrease?")
        print("  2. Verify decoder is working - test encode→decode reconstruction")
        print("  3. Try longer training (more epochs)")
        print("  4. Increase model capacity or learning rate")
        print("  5. Check if normalization is too aggressive")

    print("="*60)

    # Save detailed results
    output = {
        'temporal_change': {
            'mean': float(np.mean(results['temporal_change'])),
            'std': float(np.std(results['temporal_change'])),
            'min': float(np.min(results['temporal_change'])),
            'max': float(np.max(results['temporal_change']))
        },
        'persistence_improvement': {
            'mean': float(np.mean(results['persistence_improvement'])),
            'std': float(np.std(results['persistence_improvement'])),
            'min': float(np.min(results['persistence_improvement'])),
            'max': float(np.max(results['persistence_improvement']))
        },
        'spatial_variance': {
            'mean': float(np.mean(results['spatial_variance'])),
            'std': float(np.std(results['spatial_variance']))
        },
        'issues': issues,
        'num_tiles': len(tile_files)
    }

    output_file = gallery_path / "quality_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nDetailed analysis saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gallery", default="siad-command-center/data/gallery")

    args = parser.parse_args()

    analyze_gallery(args.gallery)
