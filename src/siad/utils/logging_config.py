"""Logging configuration for SIAD."""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(verbose: bool = False) -> None:
    """Configure root logger with file and stderr handlers.

    Args:
        verbose: If True, set level to DEBUG; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create logs directory if missing
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger configuration
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_dir / f"siad_{timestamp}.log"),
            logging.StreamHandler(sys.stderr),
        ],
        force=True,  # Override any existing configuration
    )

    # Suppress noisy third-party loggers
    logging.getLogger("earthengine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized (level={'DEBUG' if verbose else 'INFO'})")
    logger.info(f"Log file: logs/siad_{timestamp}.log")
