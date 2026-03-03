"""Inference service for real-time predictions"""

import torch
import numpy as np
import base64
from pathlib import Path
from typing import List, Optional
from io import BytesIO
from PIL import Image


class InferenceService:
    """Service for running model inference"""

    def __init__(self, model_service):
        self.model_service = model_service

    def _create_rgb_composite(self, bands: np.ndarray) -> np.ndarray:
        """Create RGB from 8-band satellite image"""
        rgb = bands[[2, 1, 0]].transpose(1, 2, 0)  # [H, W, 3]

        for i in range(3):
            channel = rgb[:, :, i]
            vmin, vmax = np.percentile(channel, [2, 98])
            rgb[:, :, i] = np.clip((channel - vmin) / (vmax - vmin + 1e-8), 0, 1)

        return rgb

    def _rgb_to_base64(self, rgb: np.ndarray) -> str:
        """Convert RGB numpy array to base64 PNG"""
        # Ensure uint8 format
        if rgb.dtype != np.uint8:
            rgb = (rgb * 255).astype(np.uint8)

        # Create PIL image
        img = Image.fromarray(rgb)

        # Encode to PNG in memory
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Convert to base64
        b64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    async def get_available_tiles(self) -> List[dict]:
        """Get list of available tiles

        Returns list of tile metadata from manifest.
        """
        # This would parse the manifest file
        # For now, return placeholder
        return [
            {
                "tile_id": "tile_x000_y000",
                "num_months": 48,
                "date_range": ("2021-01", "2024-12"),
                "bounds": {
                    "min_lon": -122.5,
                    "max_lon": -122.0,
                    "min_lat": 37.5,
                    "max_lat": 38.0
                }
            }
        ]

    async def get_tile_info(self, tile_id: str) -> Optional[dict]:
        """Get metadata for specific tile"""
        tiles = await self.get_available_tiles()
        for tile in tiles:
            if tile["tile_id"] == tile_id:
                return tile
        return None

    async def predict(
        self,
        tile_id: str,
        start_month: str,
        actions: Optional[List[List[float]]] = None
    ) -> dict:
        """Run model inference

        Args:
            tile_id: Tile identifier
            start_month: Starting month (YYYY-MM format)
            actions: Optional climate actions [[rain, temp], ...] for 6 months

        Returns:
            Prediction response with RGB images and metrics
        """
        if not self.model_service.is_loaded():
            raise RuntimeError("Model not loaded")

        model = self.model_service.model
        device = self.model_service.device

        # For demo purposes, load from gallery if available
        # In production, this would load from manifest and run inference
        from .gallery import GalleryService
        gallery = GalleryService(self.model_service)

        tile_data = await gallery.get_tile_data(tile_id)

        if tile_data is None:
            raise ValueError(f"Tile {tile_id} not found in gallery")

        # Return pre-computed results
        return {
            "tile_id": tile_id,
            "start_month": start_month,
            "predictions": tile_data["predictions"],
            "actuals": tile_data["targets"],
            "differences": [],  # Could compute these
            "metrics": {
                "mse_per_step": tile_data["mse_per_step"],
                "avg_mse": float(np.mean(tile_data["mse_per_step"]))
            },
            "latent_confidence": []  # Could compute these
        }
