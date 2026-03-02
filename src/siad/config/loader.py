"""Config loading and validation."""

import logging
from pathlib import Path
import yaml

from .schema import SIADConfig

logger = logging.getLogger(__name__)


def load_config(config_path: str | Path) -> SIADConfig:
    """Load and validate YAML config.

    Args:
        config_path: Path to YAML config file

    Returns:
        Validated SIADConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config validation fails
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    logger.info(f"Loading config from {config_path}")

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    try:
        config = SIADConfig(**raw)
        logger.info(f"Config validated successfully for AOI: {config.aoi.aoi_id}")
        return config
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        raise ValueError(f"Invalid config: {e}") from e
