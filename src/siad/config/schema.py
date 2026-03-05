"""Pydantic models for SIAD configuration validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List


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

    @field_validator("preprocessing_version")
    @classmethod
    def validate_preprocessing_version(cls, v: str) -> str:
        """Validate preprocessing version is v1 or v2."""
        if v not in ["v1", "v2"]:
            raise ValueError(f"preprocessing_version must be 'v1' or 'v2', got '{v}'")
        return v

    @field_validator("action_dim")
    @classmethod
    def validate_action_dim_consistency(cls, v: int, info) -> int:
        """Validate action_dim matches preprocessing_version if both are specified."""
        if "preprocessing_version" in info.data:
            version = info.data["preprocessing_version"]
            expected_dim = 4 if version == "v2" else 2
            if v != expected_dim:
                import warnings
                warnings.warn(
                    f"action_dim={v} does not match preprocessing_version='{version}' "
                    f"(expected {expected_dim}). This may cause runtime errors."
                )
        return v

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


class AntiCollapseConfig(BaseModel):
    """Anti-collapse regularization configuration (VC-Reg)."""

    type: Literal["vcreg"] = Field(
        default="vcreg",
        description="Anti-collapse method (currently only 'vcreg' supported)"
    )
    gamma: float = Field(
        default=1.0,
        gt=0.0,
        description="Variance floor threshold (target std per dimension)"
    )
    alpha: float = Field(
        default=25.0,
        ge=0.0,
        description="Variance loss weight"
    )
    beta: float = Field(
        default=1.0,
        ge=0.0,
        description="Covariance loss weight"
    )
    lambda_: float = Field(
        default=1.0,
        ge=0.0,
        alias="lambda",
        description="Total anti-collapse loss weight"
    )
    apply_to: List[str] = Field(
        default=["z_t"],
        min_length=1,
        description="Where to apply: ['z_t'] or ['z_t', 'z_pred_1']"
    )

    @field_validator("apply_to")
    @classmethod
    def validate_apply_to(cls, v: List[str]) -> List[str]:
        """Validate apply_to targets are valid."""
        valid_targets = {"z_t", "z_pred_1"}
        invalid = set(v) - valid_targets
        if invalid:
            raise ValueError(f"Invalid apply_to targets: {invalid}. Must be in {valid_targets}")
        return v


class EMAConfig(BaseModel):
    """EMA target encoder configuration."""

    tau_start: float = Field(
        default=0.99,
        gt=0.0,
        lt=1.0,
        description="Initial EMA coefficient"
    )
    tau_end: float = Field(
        default=0.995,
        gt=0.0,
        lt=1.0,
        description="Final EMA coefficient after warmup"
    )
    warmup_steps: int = Field(
        default=2000,
        gt=0,
        description="Number of steps to ramp from tau_start to tau_end"
    )

    @field_validator("tau_end")
    @classmethod
    def validate_tau_order(cls, v: float, info) -> float:
        """Validate tau_start <= tau_end for monotonicity."""
        if "tau_start" in info.data and v < info.data["tau_start"]:
            raise ValueError(f"tau_end ({v}) must be >= tau_start ({info.data['tau_start']})")
        return v

    @field_validator("tau_start")
    @classmethod
    def validate_tau_start_minimum(cls, v: float) -> float:
        """Validate tau_start >= 0.9 (recommended minimum)."""
        if v < 0.9:
            import warnings
            warnings.warn(f"tau_start ({v}) < 0.9 may cause EMA instability")
        return v


class LossConfig(BaseModel):
    """Training loss configuration."""

    anti_collapse: Optional[AntiCollapseConfig] = Field(
        default=None,
        description="Anti-collapse regularization config (optional for backward compatibility)"
    )


class TrainConfig(BaseModel):
    """Training configuration."""

    loss: LossConfig = Field(default_factory=LossConfig, description="Loss function config")


class ModelConfig(BaseModel):
    """World model training configuration."""

    latent_dim: int = Field(default=256, description="Latent space dimensionality")
    context_length: int = Field(default=6, description="History length in months")
    rollout_horizon: int = Field(default=6, description="Prediction horizon in months")
    batch_size: int = Field(default=16, description="Training batch size")
    epochs: int = Field(default=50, description="Number of training epochs")
    learning_rate: float = Field(default=1e-4, description="Adam learning rate")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    ema: EMAConfig = Field(default_factory=EMAConfig, description="EMA target encoder config")


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
    train: TrainConfig = Field(default_factory=TrainConfig, description="Training config")
    detection: DetectionConfig
    validation: Optional[ValidationConfig] = None
