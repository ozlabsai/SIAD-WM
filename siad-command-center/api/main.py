"""SIAD Command Center - FastAPI Backend

Tactical satellite intelligence API for model inference and gallery curation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import torch
from pathlib import Path

from .services.model_loader import ModelService
from .services.inference import InferenceService
from .services.gallery import GalleryService

# Initialize FastAPI app
app = FastAPI(
    title="SIAD Command Center API",
    description="Tactical satellite intelligence world model inference",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
model_service = ModelService()
inference_service = InferenceService(model_service)
gallery_service = GalleryService(model_service)


# Request/Response models
class PredictionRequest(BaseModel):
    tile_id: str
    start_month: str  # "YYYY-MM"
    actions: Optional[List[List[float]]] = None  # [[rain, temp], ...] for 6 months


class PredictionResponse(BaseModel):
    tile_id: str
    start_month: str
    predictions: List[str]  # Base64 encoded RGB images
    actuals: List[str]  # Base64 encoded RGB images
    differences: List[str]  # Base64 encoded difference maps
    metrics: dict  # Loss, PSNR, SSIM per timestep
    latent_confidence: List[List[float]]  # 16x16 confidence heatmap per timestep


class TileInfo(BaseModel):
    tile_id: str
    num_months: int
    date_range: tuple
    bounds: dict  # {min_lon, max_lon, min_lat, max_lat}


class GalleryEntry(BaseModel):
    tile_id: str
    month: str
    loss: float
    category: str  # "best", "worst", "average"
    thumbnail: str  # Base64 RGB
    preview_url: str


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "operational",
        "model_loaded": model_service.is_loaded(),
        "device": str(model_service.device)
    }


# Tile management
@app.get("/api/tiles", response_model=List[TileInfo])
async def list_tiles():
    """List all available tiles with metadata"""
    try:
        tiles = await inference_service.get_available_tiles()
        return tiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tiles/{tile_id}")
async def get_tile_info(tile_id: str):
    """Get detailed info for a specific tile"""
    try:
        tile_info = await inference_service.get_tile_info(tile_id)
        if tile_info is None:
            raise HTTPException(status_code=404, detail=f"Tile {tile_id} not found")
        return tile_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Inference
@app.post("/api/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Run model inference for a tile

    Generates 6-month prediction rollout with RGB visualizations.
    """
    try:
        result = await inference_service.predict(
            tile_id=request.tile_id,
            start_month=request.start_month,
            actions=request.actions
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Gallery
@app.get("/api/gallery", response_model=List[GalleryEntry])
async def get_gallery(
    category: Optional[str] = None,  # "best", "worst", "average"
    limit: int = 15
):
    """Get curated gallery of predictions

    Returns best/worst/average predictions sorted by loss.
    """
    try:
        entries = await gallery_service.get_gallery(category=category, limit=limit)
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gallery/generate")
async def generate_gallery():
    """Generate gallery by running inference on all tiles

    This is a long-running operation that curates best/worst/average examples.
    """
    try:
        status = await gallery_service.generate_gallery()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Startup
@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    print("Loading SIAD World Model...")
    await model_service.load_model(
        checkpoint_path="checkpoints/checkpoint_best.pth",
        decoder_path="checkpoints/decoder_best.pth",
        model_size="medium"
    )
    print("Model loaded successfully!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
