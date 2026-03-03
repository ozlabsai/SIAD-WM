"""Gallery curation service

Loads pre-computed predictions and serves best/worst/average examples.
"""

import json
import numpy as np
import base64
from pathlib import Path
from typing import List, Optional
from io import BytesIO
from PIL import Image


class GalleryService:
    """Service for managing curated prediction gallery"""

    def __init__(self, model_service, gallery_path: str = "siad-command-center/data/gallery"):
        self.model_service = model_service
        self.gallery_path = Path(gallery_path)
        self.metadata = None
        self.stats = None
        self._load_metadata()

    def _load_metadata(self):
        """Load gallery metadata"""
        try:
            meta_path = self.gallery_path / "gallery.json"
            stats_path = self.gallery_path / "stats.json"

            if meta_path.exists():
                with open(meta_path) as f:
                    self.metadata = json.load(f)

            if stats_path.exists():
                with open(stats_path) as f:
                    self.stats = json.load(f)

        except Exception as e:
            print(f"Warning: Could not load gallery metadata: {e}")
            self.metadata = {"best": [], "worst": [], "average": []}
            self.stats = {}

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

    async def get_gallery(
        self,
        category: Optional[str] = None,
        limit: int = 15
    ) -> List[dict]:
        """Get curated gallery entries

        Args:
            category: "best", "worst", "average", or None for all
            limit: Maximum number of entries

        Returns:
            List of gallery entries with thumbnails
        """
        if self.metadata is None:
            return []

        # Get tile IDs for category
        if category:
            tile_ids = self.metadata.get(category, [])
        else:
            # All categories
            tile_ids = (
                self.metadata.get("best", []) +
                self.metadata.get("average", []) +
                self.metadata.get("worst", [])
            )

        tile_ids = tile_ids[:limit]

        # Load entries
        entries = []
        for tile_id in tile_ids:
            tile_path = self.gallery_path / f"{tile_id}.npz"

            if not tile_path.exists():
                continue

            try:
                data = np.load(tile_path)

                # Get context as thumbnail
                context_rgb = data['context_rgb']
                thumbnail = self._rgb_to_base64(context_rgb)

                # Get first prediction for preview
                pred_rgbs = data['pred_rgbs']
                preview = self._rgb_to_base64(pred_rgbs[0])

                # Get MSE
                mse_per_step = data['mse_per_step']
                avg_mse = float(np.mean(mse_per_step))

                # Determine category
                cat = "average"
                if tile_id in self.metadata.get("best", []):
                    cat = "best"
                elif tile_id in self.metadata.get("worst", []):
                    cat = "worst"

                entry = {
                    "tile_id": tile_id,
                    "loss": avg_mse,
                    "category": cat,
                    "thumbnail": thumbnail,
                    "preview": preview,
                    "mse_per_step": mse_per_step.tolist()
                }

                entries.append(entry)

            except Exception as e:
                print(f"Error loading gallery entry {tile_id}: {e}")
                continue

        return entries

    async def get_tile_data(self, tile_id: str) -> Optional[dict]:
        """Get full prediction data for a tile

        Args:
            tile_id: Tile identifier

        Returns:
            Full prediction data with all timesteps
        """
        tile_path = self.gallery_path / f"{tile_id}.npz"

        if not tile_path.exists():
            return None

        try:
            data = np.load(tile_path)

            # Convert all RGBs to base64
            context_rgb = self._rgb_to_base64(data['context_rgb'])

            pred_rgbs = [
                self._rgb_to_base64(data['pred_rgbs'][t])
                for t in range(len(data['pred_rgbs']))
            ]

            target_rgbs = [
                self._rgb_to_base64(data['target_rgbs'][t])
                for t in range(len(data['target_rgbs']))
            ]

            return {
                "tile_id": tile_id,
                "context": context_rgb,
                "predictions": pred_rgbs,
                "targets": target_rgbs,
                "mse_per_step": data['mse_per_step'].tolist(),
                "actions": data['actions'].tolist()
            }

        except Exception as e:
            print(f"Error loading tile data {tile_id}: {e}")
            return None

    async def generate_gallery(self) -> dict:
        """Generate gallery by running inference

        This would trigger the generate_gallery.py script.
        For now, returns status message.
        """
        return {
            "status": "not_implemented",
            "message": "Run scripts/generate_gallery.py to generate gallery data"
        }
