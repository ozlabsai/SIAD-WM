"""AOI (Area of Interest) routes."""

from fastapi import APIRouter
from typing import List
from api.models.schemas import AOIMetadata, Month
from api.services.data_loader import data_loader

router = APIRouter(prefix="/aoi", tags=["aoi"])


@router.get("", response_model=AOIMetadata)
async def get_aoi_metadata():
    """Get metadata for the Area of Interest (SF Bay)."""
    # Return SF Bay metadata
    # In production, this would come from database or config
    metadata = data_loader.metadata

    return AOIMetadata(
        name="San Francisco Bay Area",
        bounds=[-122.5, 37.0, -121.5, 38.0],
        tileCount=metadata.get('tile_size', len(data_loader.get_tile_ids())),
        timeRange=["2024-01", "2024-12"],
        description="Synthetic satellite change detection dataset covering SF Bay Area"
    )


@router.get("/months", response_model=List[Month])
async def get_available_months():
    """Get list of available months."""
    months = data_loader.get_available_months()

    # Convert to Month objects
    month_labels = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }

    return [
        Month(
            id=month_id,
            label=f"{month_labels[month_id.split('-')[1]]} 2024"
        )
        for month_id in months
    ]
