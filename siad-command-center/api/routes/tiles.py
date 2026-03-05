"""Tile asset routes."""

from fastapi import APIRouter, HTTPException, Query
from api.models.schemas import TileAssets
from api.services.data_loader import data_loader

router = APIRouter(prefix="/tiles", tags=["tiles"])


@router.get("/{tile_id}/assets", response_model=TileAssets)
async def get_tile_assets(
    tile_id: str,
    month: str = Query(..., description="Month identifier (e.g., '2024-01')")
):
    """Get imagery asset URLs for a specific tile and month."""
    assets = data_loader.get_tile_assets(tile_id, month)

    if not assets:
        raise HTTPException(
            status_code=404,
            detail=f"Assets not found for tile {tile_id} and month {month}"
        )

    return TileAssets(
        tileId=assets['tile_id'],
        month=assets['month'],
        actual=assets['actual'],
        predicted=assets['predicted'],
        residual=assets['residual']
    )
