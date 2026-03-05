"""Detection routes for hotspot analysis."""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from api.models.schemas import Hotspot, HotspotDetail
from api.services.data_loader import data_loader
from api.config import DEFAULT_MIN_SCORE, DEFAULT_LIMIT

router = APIRouter(prefix="/detect", tags=["detection"])


@router.get("/hotspots", response_model=List[Hotspot])
async def get_hotspots(
    min_score: float = Query(DEFAULT_MIN_SCORE, ge=0.0, le=1.0, description="Minimum anomaly score threshold"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=100, description="Maximum number of results")
):
    """Get ranked hotspots across all tiles."""
    hotspots = data_loader.get_hotspots(min_score=min_score, limit=limit)

    return [
        Hotspot(
            tileId=hs['tile_id'],
            score=hs['score'],
            lat=hs['lat'],
            lon=hs['lon'],
            month=hs['month'],
            changeType=hs['change_type'],
            region=hs['region']
        )
        for hs in hotspots
    ]


@router.get("/tile/{tile_id}", response_model=HotspotDetail)
async def get_tile_detail(tile_id: str):
    """Get detailed information for a specific tile."""
    detail = data_loader.get_tile_detail(tile_id)

    if not detail:
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} not found")

    return HotspotDetail(
        tileId=detail['tile_id'],
        score=detail['score'],
        lat=detail['lat'],
        lon=detail['lon'],
        region=detail['region'],
        changeType=detail['change_type'],
        onsetMonth=detail['onset_month'],
        heatmap=detail['heatmap'],
        timeline=[
            {
                'month': t['month'],
                'score': t['score'],
                'timestamp': t['timestamp']
            }
            for t in detail['timeline']
        ],
        baselines={
            'persistence': detail['baselines']['persistence'],
            'seasonal': detail['baselines']['seasonal']
        }
    )
