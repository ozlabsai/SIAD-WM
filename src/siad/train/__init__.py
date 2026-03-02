"""SIAD Training Components

Exports:
    - SIADDataset: PyTorch Dataset for loading GeoTIFF shards
    - Trainer: Training loop with EMA updates and checkpointing
"""

from .dataset import SIADDataset
from .trainer import Trainer

__all__ = ["SIADDataset", "Trainer"]
