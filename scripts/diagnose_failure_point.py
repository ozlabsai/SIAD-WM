#!/usr/bin/env python3
"""Diagnose where the failure happens: encoder, transition, or decoder?

Tests each component separately to isolate the issue:
1. Encoder reconstruction: encode(x) → decode(z) vs x (decoder quality on CONTEXT)
2. Transition prediction: rollout(z0) → z_pred vs z_target (latent space quality)
3. End-to-end: encode → rollout → decode vs ground truth (full pipeline)

This tells us which component is breaking the predictions.
"""

import argparse
import torch
import numpy as np
from pathlib import Path
from tqdm import tqdm
import yaml

from siad.model import WorldModel
from siad.train.dataset import SIADDataset


def diagnose_model(
    checkpoint_path: str,
    decoder_checkpoint_path: str,
    model_size: str,
    manifest_path: str,
    data_root: str,
    num_samples: int = 10,
    device: str = "cuda"
):
    """Run diagnostic tests on each model component"""

    # Load model config
    config_path = Path(__file__).parent.parent / "configs" / "model_sizes.yaml"
    with open(config_path) as f:
        model_configs = yaml.safe_load(f)

    model_config = model_configs[model_size]

    # Load model
    print("Loading model...")
    model = WorldModel(
        in_channels=8,
        action_dim=2,
        use_decoder=True,
        **model_config
    )

    # Load encoder + transition
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)

    # Load decoder
    decoder_ckpt = torch.load(decoder_checkpoint_path, map_location=device)
    model.decoder.load_state_dict(decoder_ckpt['decoder_state_dict'])

    model.to(device)
    model.train(False)

    print(f"Model loaded: {model_size}")
    print(f"  Encoder val loss: {checkpoint.get('best_val_loss', 'N/A')}")
    print(f"  Decoder val loss: {decoder_ckpt.get('val_loss', 'N/A')}")

    # Load dataset
    dataset = SIADDataset(
        manifest_path=manifest_path,
        context_length=1,
        rollout_horizon=6,
        normalize=True,
        data_root=data_root
    )

    print(f"\nTesting on {num_samples} samples...")
    print("="*60)

    # Collect metrics
    decoder_mse = []
    transition_mse = []
    end_to_end_mse = []
    persistence_mse = []

    for idx in tqdm(range(min(num_samples, len(dataset))), desc="Testing"):
        sample = dataset[idx]

        x_context = sample['obs_context'].unsqueeze(0).to(device)  # [1, 8, 256, 256]
        actions = sample['actions_rollout'].unsqueeze(0).to(device)  # [1, 6, 2]
        x_targets = sample['obs_targets'].to(device)  # [6, 8, 256, 256]

        with torch.no_grad():
            # ============================================================
            # TEST 1: Decoder Quality on Context (encode → decode)
            # ============================================================
            z_context = model.encode(x_context)  # [1, 256, D]
            x_context_recon = model.decode(z_context)  # [1, 8, 256, 256]

            # MSE between context and its reconstruction
            mse_decoder = torch.mean((x_context - x_context_recon) ** 2).item()
            decoder_mse.append(mse_decoder)

            # ============================================================
            # TEST 2: Transition Model Quality (latent space predictions)
            # ============================================================
            # We need to encode targets to get ground truth latents
            # Note: This assumes we have a target encoder (EMA)
            if hasattr(model, 'target_encoder') and model.target_encoder is not None:
                # Encode targets
                x_targets_batch = x_targets.unsqueeze(1)  # [6, 1, 8, 256, 256]
                z_targets = []
                for t in range(6):
                    z_t = model.target_encoder(x_targets_batch[t])  # [1, 256, D]
                    z_targets.append(z_t)
                z_targets = torch.stack(z_targets, dim=1)  # [1, 6, 256, D]

                # Predict latents
                z_pred = model.rollout(z_context, actions, H=6)  # [1, 6, 256, D]

                # MSE in latent space
                mse_transition = torch.mean((z_pred - z_targets) ** 2).item()
                transition_mse.append(mse_transition)
            else:
                # Can't test transition without target encoder
                transition_mse.append(None)

            # ============================================================
            # TEST 3: End-to-End (encode → rollout → decode)
            # ============================================================
            z_pred = model.rollout(z_context, actions, H=6)  # [1, 6, 256, D]
            x_pred = model.decode(z_pred)  # [1, 6, 8, 256, 256]

            # Average MSE across all timesteps
            mse_e2e_per_step = []
            for t in range(6):
                mse_t = torch.mean((x_pred[0, t] - x_targets[t]) ** 2).item()
                mse_e2e_per_step.append(mse_t)

            mse_e2e = np.mean(mse_e2e_per_step)
            end_to_end_mse.append(mse_e2e)

            # ============================================================
            # TEST 4: Persistence Baseline
            # ============================================================
            # Just repeat context for all timesteps
            mse_persist_per_step = []
            for t in range(6):
                mse_t = torch.mean((x_context[0] - x_targets[t]) ** 2).item()
                mse_persist_per_step.append(mse_t)

            mse_persist = np.mean(mse_persist_per_step)
            persistence_mse.append(mse_persist)

    # ============================================================
    # RESULTS
    # ============================================================
    print("\n" + "="*60)
    print("DIAGNOSTIC RESULTS")
    print("="*60)

    print("\n1. DECODER QUALITY (Context Reconstruction)")
    print(f"   encode(context) → decode → MSE: {np.mean(decoder_mse):.6f}")
    print(f"   Expected: ~0.07 (decoder val loss)")
    if np.mean(decoder_mse) < 0.1:
        print("   ✓ Decoder works well on context encodings")
    else:
        print("   ⚠️  Decoder quality is poor even on context!")

    print("\n2. TRANSITION MODEL QUALITY (Latent Space)")
    if transition_mse[0] is not None:
        print(f"   rollout(z0) → z_pred MSE: {np.mean([m for m in transition_mse if m is not None]):.6f}")
        print(f"   Expected: ~0.013 (encoder val loss)")
        if np.mean([m for m in transition_mse if m is not None]) < 0.05:
            print("   ✓ Transition model predicts well in latent space")
        else:
            print("   ⚠️  Transition model has high latent error!")
    else:
        print("   ⚠️  No target encoder found - can't measure latent space error")
        print("   (This is OK for JEPA models trained without target encoder)")

    print("\n3. END-TO-END PIPELINE")
    print(f"   encode → rollout → decode MSE: {np.mean(end_to_end_mse):.6f}")

    print("\n4. PERSISTENCE BASELINE")
    print(f"   Repeat context MSE: {np.mean(persistence_mse):.6f}")

    improvement = (np.mean(persistence_mse) - np.mean(end_to_end_mse)) / np.mean(persistence_mse) * 100
    print(f"\n5. IMPROVEMENT OVER PERSISTENCE: {improvement:.1f}%")

    print("\n" + "="*60)
    print("DIAGNOSIS")
    print("="*60)

    # Diagnose the issue
    if np.mean(decoder_mse) > 0.15:
        print("❌ ISSUE: Decoder fails even on context reconstruction")
        print("   → Problem is in the decoder itself")
        print("   → Retrain decoder with better loss function or architecture")

    elif transition_mse[0] is not None and np.mean([m for m in transition_mse if m is not None]) > 0.1:
        print("❌ ISSUE: Transition model has high latent space error")
        print("   → Problem is in the transition model / encoder training")
        print("   → Need longer training or better model capacity")

    elif np.mean(end_to_end_mse) > 2 * np.mean(decoder_mse):
        print("❌ ISSUE: Decoder works on context but fails on predictions")
        print("   → Decoder doesn't generalize to predicted latents")
        print("   → This is the issue we're fixing!")
        print(f"   → Context reconstruction MSE: {np.mean(decoder_mse):.6f}")
        print(f"   → Prediction reconstruction MSE: {np.mean(end_to_end_mse):.6f}")
        print(f"   → Ratio: {np.mean(end_to_end_mse) / np.mean(decoder_mse):.2f}x worse")
        print("\n   SOLUTION: Retrain decoder on predicted latents (not context)")

    elif improvement < 0:
        print("❌ ISSUE: Predictions worse than persistence")
        print("   Potential causes:")
        print("   - Predicted latents diverge from realistic distribution")
        print("   - Decoder introduces artifacts on predicted latents")
        print("   - Training data has too little temporal variation")
        print("\n   SOLUTION: Retrain decoder on predicted latents")

    else:
        print("✓ All components work well individually")
        print(f"  Model beats persistence by {improvement:.1f}%")

    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--decoder-checkpoint", required=True)
    parser.add_argument("--model-size", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--num-samples", type=int, default=10)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")

    args = parser.parse_args()

    diagnose_model(
        checkpoint_path=args.checkpoint,
        decoder_checkpoint_path=args.decoder_checkpoint,
        model_size=args.model_size,
        manifest_path=args.manifest,
        data_root=args.data_root,
        num_samples=args.num_samples,
        device=args.device
    )
