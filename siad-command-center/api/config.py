"""Configuration settings for SIAD Command Center API."""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HDF5_PATH = DATA_DIR / "residuals_test.h5"
METADATA_PATH = DATA_DIR / "satellite_imagery" / "metadata.json"
TILES_DIR = DATA_DIR / "satellite_imagery" / "tiles"

# API Configuration
API_PREFIX = "/api"
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5175",
]

# Detection thresholds
DEFAULT_MIN_SCORE = 0.5
DEFAULT_LIMIT = 10
