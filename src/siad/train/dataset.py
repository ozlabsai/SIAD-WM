"""PyTorch Dataset for SIAD World Model Training

Loads GeoTIFF shards from manifest.jsonl with 6-month context + 6-month rollout windows.
"""

import json
import torch
from torch.utils.data import Dataset
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    print("Warning: rasterio not installed. GeoTIFF loading will fail.")


class SIADDataset(Dataset):
    """PyTorch Dataset for SIAD world model training

    Loads GeoTIFF observations and action vectors from manifest.jsonl.

    Manifest format (one JSON object per line):
    {
        "tile_id": "tile_x000_y000",
        "months": ["2023-01", "2023-02", ..., "2023-12"],
        "observations": ["path/to/tile_2023-01.tif", ...],  # 12 GeoTIFFs
        "actions": [[rain_anom, temp_anom], ...]             # 12 action vectors
    }

    Returns:
        Sample dict with keys:
            - obs_context: [L=6, C=8, H=256, W=256] context observations
            - actions_rollout: [H=6, 2] rollout action vectors
            - obs_targets: [H=6, C=8, H=256, W=256] target observations
            - tile_id: str
            - months_context: List[str]
            - months_rollout: List[str]

    Args:
        manifest_path: Path to manifest.jsonl
        context_length: Number of context months (L, default 6)
        rollout_horizon: Number of rollout months (H, default 6)
        data_root: Root directory for resolving relative GeoTIFF paths
        normalize: Whether to normalize observations to [0, 1] (default True)
    """

    def __init__(
        self,
        manifest_path: str,
        context_length: int = 6,
        rollout_horizon: int = 6,
        data_root: Optional[str] = None,
        normalize: bool = True
    ):
        if not RASTERIO_AVAILABLE:
            raise ImportError("rasterio is required for GeoTIFF loading. Install with: uv add rasterio")

        self.manifest_path = Path(manifest_path)
        self.context_length = context_length
        self.rollout_horizon = rollout_horizon
        self.data_root = Path(data_root) if data_root else self.manifest_path.parent
        self.normalize = normalize

        # Load manifest
        self.samples = self._load_manifest()

        print(f"Loaded {len(self.samples)} samples from {manifest_path}")
        print(f"  Context length: {context_length} months")
        print(f"  Rollout horizon: {rollout_horizon} months")

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
                    if len(sample["observations"]) < min_length:
                        raise ValueError(
                            f"Sample has {len(sample['observations'])} observations, "
                            f"need at least {min_length}"
                        )
                    if len(sample["actions"]) < min_length:
                        raise ValueError(
                            f"Sample has {len(sample['actions'])} actions, "
                            f"need at least {min_length}"
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

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Get training sample

        Returns:
            Dict with keys:
                - obs_context: [L, C, H, W] context observations
                - actions_rollout: [H, 2] rollout actions
                - obs_targets: [H, C, H, W] target observations
                - tile_id: str
                - months_context: List[str]
                - months_rollout: List[str]
        """
        sample = self.samples[idx]

        # Extract windows
        L = self.context_length
        H = self.rollout_horizon

        # Context: indices [0:L]
        obs_context_paths = sample["observations"][:L]
        months_context = sample["months"][:L]

        # Rollout: indices [L:L+H]
        actions_rollout = sample["actions"][L:L+H]
        obs_targets_paths = sample["observations"][L:L+H]
        months_rollout = sample["months"][L:L+H]

        # Load GeoTIFFs
        obs_context = np.stack([self._load_geotiff(p) for p in obs_context_paths])  # [L, C, H, W]
        obs_targets = np.stack([self._load_geotiff(p) for p in obs_targets_paths])  # [H, C, H, W]

        # Convert to tensors
        obs_context = torch.from_numpy(obs_context)
        obs_targets = torch.from_numpy(obs_targets)
        actions_rollout = torch.tensor(actions_rollout, dtype=torch.float32)  # [H, 2]

        return {
            "obs_context": obs_context,
            "actions_rollout": actions_rollout,
            "obs_targets": obs_targets,
            "tile_id": sample["tile_id"],
            "months_context": months_context,
            "months_rollout": months_rollout
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
