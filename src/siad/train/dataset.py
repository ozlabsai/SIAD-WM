"""PyTorch Dataset for SIAD World Model Training

Loads GeoTIFF shards from manifest.jsonl with 6-month context + 6-month rollout windows.
Includes optional data augmentation for improved generalization.

V2 Schema (Temporal Conditioning):
- Supports preprocessing_version field in manifest for backward compatibility
- Extends action vectors from [rain_anom, temp_anom] to include temporal features
- Computes month_sin/cos from timestamp data
"""

import json
import torch
from torch.utils.data import Dataset
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    print("Warning: rasterio not installed. GeoTIFF loading will fail.")

# Import temporal feature computation
from siad.data.preprocessing import compute_temporal_features


class SIADDataset(Dataset):
    """PyTorch Dataset for SIAD world model training

    Loads GeoTIFF observations and action vectors from manifest.jsonl.

    Manifest format (one JSON object per line):

    V1 Schema (baseline):
    {
        "tile_id": "tile_x000_y000",
        "months": ["2023-01", "2023-02", ..., "2023-12"],
        "observations": ["path/to/tile_2023-01.tif", ...],  # 12 GeoTIFFs
        "actions": [[rain_anom, temp_anom], ...]             # 12 action vectors [A=2]
    }

    V2 Schema (temporal conditioning):
    {
        "tile_id": "tile_x000_y000",
        "months": ["2023-01", "2023-02", ..., "2023-12"],
        "observations": ["path/to/tile_2023-01.tif", ...],
        "actions": [[rain_anom, temp_anom], ...],            # Weather anomalies only
        "preprocessing_version": "v2"                        # Optional, defaults to v1
    }

    Note: V2 schema stores only weather anomalies in manifest. Temporal features
    (month_sin, month_cos) are computed dynamically from "months" field.

    Returns:
        Sample dict with keys:
            - obs_context: [L=6, C=8, H=256, W=256] context observations
            - actions_rollout: [H=6, A] rollout action vectors (A=2 for v1, A=4 for v2)
            - obs_targets: [H=6, C=8, H=256, W=256] target observations
            - tile_id: str
            - months_context: List[str]
            - months_rollout: List[str]
            - timestamps: Optional[List[datetime]] - Only for v2 (None for v1)

    Args:
        manifest_path: Path to manifest.jsonl
        context_length: Number of context months (L, default 6)
        rollout_horizon: Number of rollout months (H, default 6)
        data_root: Root directory for resolving relative GeoTIFF paths
        normalize: Whether to normalize observations to [0, 1] (default True)
        augment: Whether to apply data augmentation (default False)
                 Augmentation includes:
                 - Random horizontal/vertical flips (geographic invariance)
                 - Random rotations (±10 degrees)
                 - Brightness jitter (±10% for cloud/shadow variation)
        preprocessing_version: Override preprocessing version ("v1" or "v2")
                               If None, read from manifest (default None)
    """

    def __init__(
        self,
        manifest_path: str,
        context_length: int = 1,  # Changed to 1 for single-month context per MODEL.md
        rollout_horizon: int = 6,
        data_root: Optional[str] = None,
        normalize: bool = True,
        augment: bool = False,
        preprocessing_version: Optional[str] = None
    ):
        if not RASTERIO_AVAILABLE:
            raise ImportError("rasterio is required for GeoTIFF loading. Install with: uv add rasterio")

        self.manifest_path = Path(manifest_path)
        self.context_length = context_length
        self.rollout_horizon = rollout_horizon
        self.data_root = Path(data_root) if data_root else self.manifest_path.parent
        self.normalize = normalize
        self.augment = augment
        self.preprocessing_version_override = preprocessing_version

        # Load manifest
        self.samples = self._load_manifest()

        # Detect preprocessing version from first sample (can be overridden per sample)
        first_version = self.samples[0].get('preprocessing_version', 'v1')
        detected_version = preprocessing_version or first_version

        print(f"Loaded {len(self.samples)} samples from {manifest_path}")
        print(f"  Context length: {context_length} months")
        print(f"  Rollout horizon: {rollout_horizon} months")
        print(f"  Preprocessing version: {detected_version} (action_dim={4 if detected_version == 'v2' else 2})")
        if augment:
            print(f"  Augmentation: ENABLED (flips, rotations ±10°, brightness ±10%)")

    def _load_manifest(self) -> List[Dict]:
        """Load and parse manifest.jsonl"""
        samples = []

        with open(self.manifest_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    sample = json.loads(line)
                    # Validate sample structure
                    required_keys = ["tile_id", "months", "observations", "actions"]
                    if not all(k in sample for k in required_keys):
                        raise ValueError(f"Missing keys: {required_keys}")

                    # Verify length requirements
                    min_length = self.context_length + self.rollout_horizon
                    available_months = len(sample["observations"])

                    if available_months < min_length:
                        raise ValueError(
                            f"Sample has {available_months} observations, "
                            f"need at least {min_length} (context_length={self.context_length} + "
                            f"rollout_horizon={self.rollout_horizon})"
                        )
                    if len(sample["actions"]) < min_length:
                        raise ValueError(
                            f"Sample has {len(sample['actions'])} actions, "
                            f"need at least {min_length}"
                        )

                    # Validate context_length against available data
                    if self.context_length > available_months - self.rollout_horizon:
                        raise ValueError(
                            f"context_length={self.context_length} is too large. "
                            f"With {available_months} months and rollout_horizon={self.rollout_horizon}, "
                            f"max context_length is {available_months - self.rollout_horizon}"
                        )

                    samples.append(sample)

                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON at line {line_num}: {e}")
                except ValueError as e:
                    print(f"Warning: Skipping invalid sample at line {line_num}: {e}")

        if not samples:
            raise ValueError(f"No valid samples found in {self.manifest_path}")

        return samples

    def _load_geotiff(self, path: str) -> np.ndarray:
        """Load GeoTIFF and return as [C, H, W] numpy array

        Args:
            path: Path to GeoTIFF file

        Returns:
            arr: [C=8, H=256, W=256] array (float32)
        """
        # Resolve path relative to data_root
        full_path = self.data_root / path if not Path(path).is_absolute() else Path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"GeoTIFF not found: {full_path}")

        with rasterio.open(full_path) as src:
            # Read all 8 bands: [C, H, W]
            arr = src.read()  # Shape: [num_bands, height, width]

            if arr.shape[0] != 8:
                raise ValueError(
                    f"Expected 8 bands, got {arr.shape[0]} in {full_path}\n"
                    f"Expected band order: [B2, B3, B4, B8, VV, VH, lights, valid]"
                )

            # Convert to float32
            arr = arr.astype(np.float32)

            # Resize to exactly 256x256 if needed (handles slight size variations from EE exports)
            if arr.shape[1] != 256 or arr.shape[2] != 256:
                # Use simple resize (nearest neighbor for valid mask, bilinear for others)
                from scipy.ndimage import zoom

                h_scale = 256 / arr.shape[1]
                w_scale = 256 / arr.shape[2]

                resized = np.zeros((8, 256, 256), dtype=np.float32)
                for c in range(8):
                    # Use order=0 (nearest) for valid mask, order=1 (bilinear) for data
                    order = 0 if c == 7 else 1  # Last channel is valid mask
                    resized[c] = zoom(arr[c], (h_scale, w_scale), order=order)

                arr = resized

            # Normalize to [0, 1] if requested
            if self.normalize:
                # Handle potential NaN/inf values
                arr = np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=0.0)
                # Min-max normalization per channel
                for c in range(arr.shape[0]):
                    channel = arr[c]
                    min_val, max_val = channel.min(), channel.max()
                    if max_val > min_val:
                        arr[c] = (channel - min_val) / (max_val - min_val)
                    else:
                        arr[c] = 0.0  # Constant channel

            return arr

    def _apply_augmentation(self, arr: np.ndarray) -> np.ndarray:
        """Apply random augmentation to a single image

        Augmentations preserve satellite imagery properties:
        - Random horizontal/vertical flips (geographic invariance)
        - Small rotations (±10 degrees)
        - Brightness jitter (±10% for cloud/shadow variation)

        Args:
            arr: [C, H, W] array

        Returns:
            Augmented [C, H, W] array
        """
        # Random horizontal flip (50% chance)
        if np.random.rand() < 0.5:
            arr = np.flip(arr, axis=2).copy()

        # Random vertical flip (50% chance)
        if np.random.rand() < 0.5:
            arr = np.flip(arr, axis=1).copy()

        # Random rotation (±10 degrees)
        angle = np.random.uniform(-10, 10)
        if abs(angle) > 0.1:  # Skip if negligible
            from scipy.ndimage import rotate
            # Rotate each channel independently
            # Use order=1 (bilinear) for data, order=0 (nearest) for valid mask
            for c in range(arr.shape[0]):
                order = 0 if c == 7 else 1  # Last channel is valid mask
                arr[c] = rotate(arr[c], angle, reshape=False, order=order, mode='nearest')

        # Brightness jitter (±10%) - only for optical bands (first 4 channels)
        # Don't jitter SAR (channels 4-5) or nightlights (channel 6) or valid mask (channel 7)
        brightness_factor = np.random.uniform(0.9, 1.1)
        arr[:4] = np.clip(arr[:4] * brightness_factor, 0.0, 1.0)

        return arr

    def _apply_augmentation_to_sequence(self, obs_sequence: np.ndarray) -> np.ndarray:
        """Apply consistent augmentation to a temporal sequence

        Ensures the same geometric augmentation is applied across all timesteps
        to preserve temporal alignment.

        Args:
            obs_sequence: [T, C, H, W] array (T timesteps)

        Returns:
            Augmented [T, C, H, W] array
        """
        # Sample augmentation parameters once for the entire sequence
        flip_h = np.random.rand() < 0.5
        flip_v = np.random.rand() < 0.5
        angle = np.random.uniform(-10, 10)
        brightness_factor = np.random.uniform(0.9, 1.1)

        augmented = obs_sequence.copy()

        # Apply same geometric transforms to all timesteps
        for t in range(obs_sequence.shape[0]):
            # Flips
            if flip_h:
                augmented[t] = np.flip(augmented[t], axis=2).copy()
            if flip_v:
                augmented[t] = np.flip(augmented[t], axis=1).copy()

            # Rotation
            if abs(angle) > 0.1:
                from scipy.ndimage import rotate
                for c in range(augmented.shape[1]):
                    order = 0 if c == 7 else 1  # Last channel is valid mask
                    augmented[t, c] = rotate(
                        augmented[t, c], angle, reshape=False, order=order, mode='nearest'
                    )

            # Brightness jitter (different per timestep to simulate varying conditions)
            brightness_t = np.random.uniform(0.9, 1.1)
            augmented[t, :4] = np.clip(augmented[t, :4] * brightness_t, 0.0, 1.0)

        return augmented

    def __len__(self) -> int:
        return len(self.samples)

    @staticmethod
    def collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """Collate batch of samples with version consistency checking.

        Ensures all samples in batch have consistent action_dim (cannot mix v1 and v2).
        Batches observations, actions, and optionally timestamps.

        Args:
            batch: List of dictionaries from __getitem__()

        Returns:
            Dictionary with batched tensors:
                - obs_context: [B, C, H, W] or [B, L, C, H, W] (depends on context_length)
                - obs_targets: [B, H, C, H, W]
                - actions_rollout: [B, H, A] where A ∈ {2, 4}
                - tile_id: List[str]
                - months_context: List[List[str]]
                - months_rollout: List[List[str]]
                - timestamps: List[List[datetime]] or None (None if all samples are v1)

        Raises:
            ValueError: If batch contains mixed v1/v2 samples (inconsistent action_dim)
        """
        if len(batch) == 0:
            raise ValueError("Cannot collate empty batch")

        # Check action_dim consistency across batch
        A = batch[0]["actions_rollout"].shape[1]
        for i, sample in enumerate(batch):
            sample_action_dim = sample["actions_rollout"].shape[1]
            if sample_action_dim != A:
                raise ValueError(
                    f"Mixed preprocessing versions in batch: "
                    f"sample 0 has action_dim={A}, sample {i} has action_dim={sample_action_dim}. "
                    f"Cannot mix v1 (action_dim=2) and v2 (action_dim=4) in same batch."
                )

        # Stack observations
        obs_context = torch.stack([s["obs_context"] for s in batch])  # [B, ...]
        obs_targets = torch.stack([s["obs_targets"] for s in batch])  # [B, H, C, H, W]

        # Stack actions
        actions_rollout = torch.stack([s["actions_rollout"] for s in batch])  # [B, H, A]

        # Collect metadata (not tensors)
        tile_ids = [s["tile_id"] for s in batch]
        months_context = [s["months_context"] for s in batch]
        months_rollout = [s["months_rollout"] for s in batch]

        # Stack timestamps if available (v2 only)
        timestamps_batch = [s["timestamps"] for s in batch if s["timestamps"] is not None]
        timestamps = timestamps_batch if len(timestamps_batch) == len(batch) else None

        return {
            "obs_context": obs_context,
            "obs_targets": obs_targets,
            "actions_rollout": actions_rollout,
            "tile_id": tile_ids,
            "months_context": months_context,
            "months_rollout": months_rollout,
            "timestamps": timestamps
        }

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Get training sample with version-aware action loading

        Returns:
            Dict with keys:
                - obs_context: [L, C, H, W] context observations
                - actions_rollout: [H, A] rollout actions (A=2 for v1, A=4 for v2)
                - obs_targets: [H, C, H, W] target observations
                - tile_id: str
                - months_context: List[str]
                - months_rollout: List[str]
                - timestamps: Optional[List[datetime]] - Only for v2 (None for v1)
        """
        sample = self.samples[idx]

        # Detect preprocessing version (per-sample or global override)
        version = self.preprocessing_version_override or sample.get('preprocessing_version', 'v1')

        # Extract windows
        L = self.context_length
        H = self.rollout_horizon

        # Context: indices [0:L]
        obs_context_paths = sample["observations"][:L]
        months_context = sample["months"][:L]

        # Rollout: indices [L:L+H]
        actions_rollout_v1 = np.array(sample["actions"][L:L+H], dtype=np.float32)  # [H, 2]
        obs_targets_paths = sample["observations"][L:L+H]
        months_rollout = sample["months"][L:L+H]

        # Load GeoTIFFs
        obs_context = np.stack([self._load_geotiff(p) for p in obs_context_paths])  # [L, C, H, W]
        obs_targets = np.stack([self._load_geotiff(p) for p in obs_targets_paths])  # [H, C, H, W]

        # Apply augmentation if enabled
        if self.augment:
            # Concatenate context and targets for consistent augmentation
            full_sequence = np.concatenate([obs_context, obs_targets], axis=0)  # [L+H, C, H, W]
            full_sequence = self._apply_augmentation_to_sequence(full_sequence)
            # Split back
            obs_context = full_sequence[:L]
            obs_targets = full_sequence[L:]

        # Version-aware action processing
        timestamps = None
        if version == 'v1':
            # V1: Use weather anomalies only [H, 2]
            actions_rollout = actions_rollout_v1
        elif version == 'v2':
            # V2: Extend with temporal features [H, 4]
            # Parse month strings to datetime for temporal feature extraction
            timestamps = []
            temporal_features = []

            for month_str in months_rollout:
                # Parse "YYYY-MM" to datetime (use day=15 as representative)
                try:
                    year, month = map(int, month_str.split('-'))
                    timestamp = datetime(year, month, 15)
                    timestamps.append(timestamp)

                    # Compute temporal features
                    month_sin, month_cos = compute_temporal_features(timestamp)
                    temporal_features.append([month_sin, month_cos])
                except ValueError:
                    raise ValueError(
                        f"Invalid month format '{month_str}' in sample {idx}. "
                        f"Expected 'YYYY-MM' format."
                    )

            temporal_features = np.array(temporal_features, dtype=np.float32)  # [H, 2]

            # Validate unit circle property (per contract)
            month_sin = temporal_features[:, 0]
            month_cos = temporal_features[:, 1]
            unit_circle_check = month_sin**2 + month_cos**2
            if not np.all((unit_circle_check >= 0.99) & (unit_circle_check <= 1.01)):
                raise AssertionError(
                    f"Temporal features violate unit circle property in sample {idx}: "
                    f"sin²+cos² = {unit_circle_check}"
                )

            # Concatenate: [H, 2] + [H, 2] → [H, 4]
            actions_rollout = np.concatenate([actions_rollout_v1, temporal_features], axis=-1)
        else:
            raise ValueError(
                f"Unknown preprocessing_version '{version}' in sample {idx}. "
                f"Expected 'v1' or 'v2'."
            )

        # Convert to tensors (use .copy() to ensure tensors are contiguous and can be batched)
        obs_context = torch.from_numpy(obs_context.copy())
        obs_targets = torch.from_numpy(obs_targets.copy())
        actions_rollout = torch.from_numpy(actions_rollout.copy())  # [H, A] where A ∈ {2, 4}

        # If context_length=1, squeeze to [C, H, W] for single-image input
        if self.context_length == 1:
            obs_context = obs_context.squeeze(0)

        return {
            "obs_context": obs_context,
            "actions_rollout": actions_rollout,
            "obs_targets": obs_targets,
            "tile_id": sample["tile_id"],
            "months_context": months_context,
            "months_rollout": months_rollout,
            "timestamps": timestamps  # None for v1, List[datetime] for v2
        }


def create_mock_manifest(
    output_path: str,
    num_tiles: int = 2,
    num_months: int = 12,
    tile_shape: Tuple[int, int] = (256, 256)
):
    """Create mock manifest.jsonl for testing (without actual GeoTIFFs)

    Args:
        output_path: Where to save manifest.jsonl
        num_tiles: Number of tiles to generate
        num_months: Number of months per tile (must be >= 12 for L=6, H=6)
        tile_shape: Tile dimensions (default 256x256)
    """
    import random

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        for tile_idx in range(num_tiles):
            tile_id = f"tile_x{tile_idx:03d}_y{tile_idx:03d}"

            months = [f"2023-{m:02d}" for m in range(1, num_months + 1)]
            observations = [
                f"data/preprocessed/tiles/{tile_id}_{month}.tif"
                for month in months
            ]
            actions = [
                [random.uniform(-2, 2), random.uniform(-1, 1)]  # [rain_anom, temp_anom]
                for _ in range(num_months)
            ]

            sample = {
                "tile_id": tile_id,
                "months": months,
                "observations": observations,
                "actions": actions
            }

            f.write(json.dumps(sample) + '\n')

    print(f"Created mock manifest at {output_path} with {num_tiles} tiles × {num_months} months")
