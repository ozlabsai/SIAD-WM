"""
Rollout engine for counterfactual scenario predictions.

Loads trained world model checkpoint and runs multi-step inference
rollouts conditioned on action sequences (rain/temp anomalies).
"""

from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn


class RolloutEngine:
    """
    World model rollout engine for counterfactual scenario predictions.

    Loads a trained checkpoint and provides rollout() method to generate
    6-month predictions conditioned on action sequences.
    """

    def __init__(
        self,
        checkpoint_path: str,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        Initialize rollout engine from checkpoint.

        Args:
            checkpoint_path: Path to PyTorch checkpoint (.pth file)
            device: Device for inference ("cuda" or "cpu")

        Raises:
            FileNotFoundError: If checkpoint does not exist
            KeyError: If checkpoint missing required keys (model_state_dict, config)
        """
        self.device = torch.device(device)
        self.checkpoint_path = Path(checkpoint_path)

        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        # Extract config
        if "config" not in checkpoint:
            raise KeyError("Checkpoint missing 'config' key")

        self.config = checkpoint["config"]
        self.latent_dim = self.config.get("latent_dim", 256)
        self.context_length = self.config.get("context_length", 6)
        self.rollout_horizon = self.config.get("rollout_horizon", 6)

        # Initialize model architecture using WorldModel
        from siad.model import WorldModel

        self.model = WorldModel(
            latent_dim=self.latent_dim,
            in_channels=self.config.get("in_channels", 8),
            action_dim=self.config.get("action_dim", 2),
            use_transformer=self.config.get("use_transformer", True),
        )

        # Load weights
        if "model_state_dict" not in checkpoint:
            raise KeyError("Checkpoint missing 'model_state_dict' key")

        self.model.load_state_dict(checkpoint["model_state_dict"])

        # Set to evaluation mode
        self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def rollout(
        self,
        context_obs: np.ndarray,
        actions: np.ndarray,
        target_obs: Optional[np.ndarray] = None,
        return_latents: bool = True,
    ) -> dict:
        """
        Run multi-step rollout conditioned on actions.

        Args:
            context_obs: Context observations [L, C=8, H=256, W=256]
            actions: Action sequence [H, 2] (rain_anom, temp_anom per timestep)
            target_obs: Optional target observations [H, C=8, H=256, W=256]
                       for computing divergence
            return_latents: If True, return predicted latent sequence

        Returns:
            {
                "predicted_latents": [H, latent_dim] if return_latents else None,
                "divergences": [H] if target_obs provided else None,
            }

        Algorithm:
            1. Encode context: z_0 = obs_encoder(context_obs[-1])
            2. For k=1..H:
               - u_k = action_encoder(actions[k-1])
               - z_k = dynamics(concat(z_{k-1}, u_k))
            3. If target_obs: compute cosine divergence vs target_encoder(target_obs)
        """
        # Convert to tensors, add batch dimension
        context_obs_t = torch.from_numpy(context_obs).float().unsqueeze(0).to(self.device)  # [1, L, C, H, W]
        actions_t = torch.from_numpy(actions).float().unsqueeze(0).to(self.device)  # [1, H, 2]

        # Run model rollout
        predicted_latents_t = self.model(context_obs_t, actions_t)  # [1, H, latent_dim]

        result = {}
        if return_latents:
            result["predicted_latents"] = predicted_latents_t.squeeze(0).cpu().numpy()  # [H, latent_dim]

        # Compute divergences if target_obs provided
        if target_obs is not None:
            target_obs_t = torch.from_numpy(target_obs).float().to(self.device)  # [H, C, H, W]

            divergences = []
            for k in range(self.rollout_horizon):
                # Encode target observation
                z_target = self.model.target_encoder(target_obs_t[k].unsqueeze(0))  # [1, latent_dim]
                z_pred = predicted_latents_t[0, k].unsqueeze(0)  # [1, latent_dim]

                # Cosine distance: 1 - cosine_similarity
                cosine_sim = nn.functional.cosine_similarity(z_pred, z_target, dim=1)
                divergence = (1.0 - cosine_sim).item()
                divergences.append(divergence)

            result["divergences"] = np.array(divergences)

        return result

    def rollout_neutral_scenario(
        self, context_obs: np.ndarray, target_obs: np.ndarray
    ) -> dict:
        """
        Convenience method for neutral scenario rollout (action=0).

        Args:
            context_obs: Context observations [L, C=8, H=256, W=256]
            target_obs: Target observations [H, C=8, H=256, W=256]

        Returns:
            {
                "divergences": [H],  # Divergence from observed reality
            }
        """
        # Neutral actions: all zeros
        neutral_actions = np.zeros((self.rollout_horizon, 2), dtype=np.float32)

        return self.rollout(
            context_obs=context_obs,
            actions=neutral_actions,
            target_obs=target_obs,
            return_latents=False,
        )
