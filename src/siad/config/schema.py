"""Pydantic models for SIAD configuration validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional


class AOIConfig(BaseModel):
    """Area of Interest configuration."""

    aoi_id: str = Field(..., min_length=1, description="Unique AOI identifier")
    bounds: dict[str, float] = Field(..., description="Geographic bounding box")
    projection: str = Field(default="EPSG:3857", description="Spatial projection")
    resolution_m: int = Field(default=10, description="Spatial resolution in meters")
    tile_size_px: int = Field(default=256, description="Tile size in pixels")

    @field_validator("bounds")
    @classmethod
    def validate_bounds(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate bounding box has required keys and valid ranges."""
        required = {"min_lon", "max_lon", "min_lat", "max_lat"}
        if not required.issubset(v.keys()):
            raise ValueError(f"bounds must contain {required}")
        if v["min_lon"] >= v["max_lon"]:
            raise ValueError("min_lon must be less than max_lon")
        if v["min_lat"] >= v["max_lat"]:
            raise ValueError("min_lat must be less than max_lat")
        return v


class DataConfig(BaseModel):
    """Data export and loading configuration."""

    gcs_bucket: str = Field(default="siad-exports", description="GCS bucket name")
    export_path: str = Field(
        default="gs://siad-exports/siad/{aoi_id}",
        description="GCS path template",
    )
    start_month: str = Field(..., description="Start month (YYYY-MM)")
    end_month: str = Field(..., description="End month (YYYY-MM)")
    sources: list[Literal["s1", "s2", "viirs", "chirps", "era5"]] = Field(
        default=["s1", "s2", "viirs", "chirps", "era5"],
        description="Data sources",
    )
    preprocessing_version: str = Field(
        default="v2",
        description="Preprocessing schema version (v1: weather only, v2: weather + temporal features)"
    )
    action_dim: int = Field(
        default=4,
        ge=1,
        description="Action vector dimension (2 for v1, 4 for v2 with temporal features)"
    )

    @field_validator("start_month", "end_month")
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        """Validate month format is YYYY-MM."""
        if len(v) != 7 or v[4] != "-":
            raise ValueError(f"Month must be in YYYY-MM format, got {v}")
        year, month = v.split("-")
        if not year.isdigit() or not month.isdigit():
            raise ValueError(f"Month must be in YYYY-MM format, got {v}")
        if not (1 <= int(month) <= 12):
            raise ValueError(f"Month must be 01-12, got {month}")
        return v

    @field_validator("preprocessing_version")
    @classmethod
    def validate_preprocessing_version(cls, v: str) -> str:
        """Validate preprocessing version is v1 or v2."""
        if v not in ["v1", "v2"]:
            raise ValueError(f"preprocessing_version must be 'v1' or 'v2', got '{v}'")
        return v


class ModelConfig(BaseModel):
    """World model training configuration."""

    latent_dim: int = Field(default=256, description="Latent space dimensionality")
    context_length: int = Field(default=6, description="History length in months")
    rollout_horizon: int = Field(default=6, description="Prediction horizon in months")
    batch_size: int = Field(default=16, description="Training batch size")
    epochs: int = Field(default=50, description="Number of training epochs")
    learning_rate: float = Field(default=1e-4, description="Adam learning rate")
    seed: int = Field(default=42, description="Random seed for reproducibility")


class DetectionConfig(BaseModel):
    """Anomaly detection configuration."""

    percentile_threshold: float = Field(
        default=99.0,
        ge=0.0,
        le=100.0,
        description="Percentile threshold for anomaly detection",
    )
    persistence_months: int = Field(
        default=2,
        ge=1,
        description="Minimum consecutive months above threshold",
    )
    min_cluster_size: int = Field(
        default=3,
        ge=1,
        description="Minimum tiles per cluster",
    )
    scenarios: list[str] = Field(
        default=["neutral", "observed"],
        description="Counterfactual scenarios",
    )


class ValidationConfig(BaseModel):
    """Validation configuration (optional)."""

    backtest_regions: Optional[str] = Field(
        default=None,
        description="Path to backtest regions JSON",
    )
    fp_test_regions: Optional[str] = Field(
        default=None,
        description="Path to false-positive test regions JSON",
    )


class SIADConfig(BaseModel):
    """Root SIAD configuration."""

    aoi: AOIConfig
    data: DataConfig
    model: ModelConfig
    detection: DetectionConfig
    validation: Optional[ValidationConfig] = None
