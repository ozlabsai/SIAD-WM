"""Determinism utilities for reproducible runs."""

import random
import logging

logger = logging.getLogger(__name__)


def set_seed(seed: int = 42) -> None:
    """Set RNG seeds for reproducible runs.

    Args:
        seed: Random seed value
    """
    random.seed(seed)

    try:
        import numpy as np

        np.random.seed(seed)
        logger.debug(f"NumPy seed set to {seed}")
    except ImportError:
        logger.warning("NumPy not available, skipping numpy seed")

    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            logger.debug(f"PyTorch CUDA seed set to {seed}")
        logger.debug(f"PyTorch seed set to {seed}")
    except ImportError:
        logger.warning("PyTorch not available, skipping torch seed")

    logger.info(f"Random seed set to {seed} for reproducibility")
