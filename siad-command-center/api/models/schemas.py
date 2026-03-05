"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional


class AOIMetadata(BaseModel):
    """Area of Interest metadata."""
    name: str = Field(..., description="Name of the AOI")
    bounds: List[float] = Field(..., description="Bounding box [minLon, minLat, maxLon, maxLat]")
    tileCount: int = Field(..., description="Total number of tiles")
    timeRange: List[str] = Field(..., description="Available time range [start, end]")
    description: Optional[str] = Field(None, description="AOI description")


class Month(BaseModel):
    """Month identifier."""
    id: str = Field(..., description="Month identifier (e.g., '2024-01')")
    label: str = Field(..., description="Human-readable label (e.g., 'January 2024')")


class Hotspot(BaseModel):
    """Hotspot detection result."""
    tileId: str = Field(..., description="Tile identifier")
    score: float = Field(..., description="Anomaly score (0-1)")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    month: str = Field(..., description="Detection month (e.g., '2024-07')")
    changeType: Optional[str] = Field(None, description="Predicted change type")
    region: Optional[str] = Field(None, description="Region type")


class TimelinePoint(BaseModel):
    """Timeline data point."""
    month: str = Field(..., description="Month identifier")
    score: float = Field(..., description="Anomaly score")
    timestamp: str = Field(..., description="ISO timestamp")


class BaselineData(BaseModel):
    """Baseline comparison data."""
    persistence: List[float] = Field(..., description="Persistence baseline scores (12 months)")
    seasonal: List[float] = Field(..., description="Seasonal baseline scores (12 months)")


class HotspotDetail(BaseModel):
    """Detailed hotspot information."""
    tileId: str = Field(..., description="Tile identifier")
    score: float = Field(..., description="Current anomaly score")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    region: Optional[str] = Field(None, description="Region type")
    changeType: Optional[str] = Field(None, description="Change type")
    onsetMonth: Optional[int] = Field(None, description="Onset month (1-12)")
    heatmap: List[List[float]] = Field(..., description="16x16 heatmap array")
    timeline: List[TimelinePoint] = Field(..., description="12-month timeline")
    baselines: BaselineData = Field(..., description="Baseline comparison data")


class TileAssets(BaseModel):
    """Tile imagery assets."""
    tileId: str = Field(..., description="Tile identifier")
    month: str = Field(..., description="Month identifier")
    actual: str = Field(..., description="URL to actual satellite image")
    predicted: str = Field(..., description="URL to predicted image")
    residual: str = Field(..., description="URL to residual heatmap")


class Case(BaseModel):
    """Investigation case (future use)."""
    caseId: str = Field(..., description="Case identifier")
    title: str = Field(..., description="Case title")
    tiles: List[str] = Field(..., description="Associated tile IDs")
    status: str = Field(..., description="Case status")
    createdAt: str = Field(..., description="Creation timestamp")
