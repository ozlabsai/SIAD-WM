"""Data loader service for HDF5 and metadata."""

import json
import h5py
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from api.config import HDF5_PATH, METADATA_PATH, TILES_DIR


class DataLoader:
    """Loads and caches data from HDF5 and metadata files."""

    def __init__(self):
        """Initialize data loader and load metadata."""
        self.metadata = self._load_metadata()
        self.h5_file: Optional[h5py.File] = None
        self._open_h5()

    def _load_metadata(self) -> Dict:
        """Load tile metadata from JSON file."""
        with open(METADATA_PATH, 'r') as f:
            return json.load(f)

    def _open_h5(self):
        """Open HDF5 file for reading."""
        if self.h5_file is None:
            self.h5_file = h5py.File(HDF5_PATH, 'r')

    def close(self):
        """Close HDF5 file."""
        if self.h5_file is not None:
            self.h5_file.close()
            self.h5_file = None

    def get_available_months(self) -> List[str]:
        """Get list of available months."""
        return [f"2024-{i:02d}" for i in range(1, 13)]

    def get_tile_ids(self) -> List[str]:
        """Get all tile IDs from HDF5 file."""
        self._open_h5()
        return list(self.h5_file.keys())

    def get_tile_metadata(self, tile_id: str) -> Optional[Dict]:
        """Get metadata for a specific tile."""
        # Convert tile_id format (tile_x000_y000 -> tile_id: 0)
        # The metadata.json uses numeric tile_id starting from 0
        tiles = self.metadata.get('tiles', [])

        # For now, map tile IDs by index (since we have tile_x000_y000, tile_x000_y001, etc.)
        # Extract the numeric part if it's in x,y format
        if 'tile_x' in tile_id:
            # For HDF5 tiles, we need to map them to metadata tiles
            # This is a simplified mapping - in production, you'd have proper mapping
            for idx, tile in enumerate(tiles):
                if f"tile_{idx:03d}" in tile_id or tile.get('tile_id') == idx:
                    return tile

        # Try direct match by tile_id field
        for tile in tiles:
            if str(tile.get('tile_id')) in tile_id:
                return tile

        return None

    def get_tile_data(self, tile_id: str) -> Optional[Dict]:
        """Get all data for a specific tile."""
        self._open_h5()

        if tile_id not in self.h5_file:
            return None

        tile = self.h5_file[tile_id]

        # Load all data
        residuals = np.array(tile['residuals'][:])  # Shape: (12, 256)
        tile_scores = np.array(tile['tile_scores'][:])  # Shape: (12,)
        timestamps = np.array(tile['timestamps'][:])  # Shape: (12,)

        # Load baselines
        baselines = {
            'persistence': np.array(tile['baselines']['persistence'][:]).tolist(),
            'seasonal': np.array(tile['baselines']['seasonal'][:]).tolist()
        }

        # Get metadata attributes
        metadata = dict(tile['metadata'].attrs) if 'metadata' in tile else {}

        return {
            'tile_id': tile_id,
            'residuals': residuals,
            'tile_scores': tile_scores,
            'timestamps': timestamps,
            'baselines': baselines,
            'metadata': metadata
        }

    def get_hotspots(self, min_score: float = 0.5, limit: int = 10) -> List[Dict]:
        """Get ranked hotspots across all tiles."""
        self._open_h5()

        hotspots = []
        tile_ids = self.get_tile_ids()

        for tile_id in tile_ids:
            tile_data = self.get_tile_data(tile_id)
            if not tile_data:
                continue

            # Get max score across all months
            scores = tile_data['tile_scores']
            max_score = float(np.max(scores))
            max_month_idx = int(np.argmax(scores))

            if max_score >= min_score:
                # Get tile metadata
                tile_meta = self.get_tile_metadata(tile_id)

                hotspots.append({
                    'tile_id': tile_id,
                    'score': max_score,
                    'month': f"2024-{max_month_idx + 1:02d}",
                    'lat': tile_meta.get('latitude', tile_data['metadata'].get('lat', 0.0)) if tile_meta else tile_data['metadata'].get('lat', 0.0),
                    'lon': tile_meta.get('longitude', tile_data['metadata'].get('lon', 0.0)) if tile_meta else tile_data['metadata'].get('lon', 0.0),
                    'change_type': tile_meta.get('change_type') if tile_meta else None,
                    'region': tile_meta.get('region') if tile_meta else tile_data['metadata'].get('region'),
                })

        # Sort by score descending and limit
        hotspots.sort(key=lambda x: x['score'], reverse=True)
        return hotspots[:limit]

    def get_tile_detail(self, tile_id: str) -> Optional[Dict]:
        """Get detailed information for a specific tile."""
        tile_data = self.get_tile_data(tile_id)
        if not tile_data:
            return None

        # Get tile metadata
        tile_meta = self.get_tile_metadata(tile_id)

        # Get current max score
        scores = tile_data['tile_scores']
        max_score = float(np.max(scores))

        # Create timeline (12 months)
        timeline = []
        for month_idx in range(12):
            timestamp = tile_data['timestamps'][month_idx]
            # Convert timestamp to ISO format
            try:
                dt = datetime.fromtimestamp(float(timestamp))
                iso_timestamp = dt.isoformat()
            except (ValueError, TypeError, OSError):
                iso_timestamp = f"2024-{month_idx + 1:02d}-01T00:00:00"

            timeline.append({
                'month': f"2024-{month_idx + 1:02d}",
                'score': float(scores[month_idx]),
                'timestamp': iso_timestamp
            })

        # Reshape residuals to 16x16 heatmap (take max across months)
        residuals = tile_data['residuals']  # Shape: (12, 256)
        max_residuals = np.max(residuals, axis=0)  # Shape: (256,)
        heatmap = max_residuals.reshape(16, 16).tolist()

        return {
            'tile_id': tile_id,
            'score': max_score,
            'lat': tile_meta.get('latitude', tile_data['metadata'].get('lat', 0.0)) if tile_meta else tile_data['metadata'].get('lat', 0.0),
            'lon': tile_meta.get('longitude', tile_data['metadata'].get('lon', 0.0)) if tile_meta else tile_data['metadata'].get('lon', 0.0),
            'region': tile_meta.get('region') if tile_meta else tile_data['metadata'].get('region'),
            'change_type': tile_meta.get('change_type') if tile_meta else None,
            'onset_month': tile_meta.get('onset_month') if tile_meta else None,
            'heatmap': heatmap,
            'timeline': timeline,
            'baselines': tile_data['baselines']
        }

    def get_tile_assets(self, tile_id: str, month: str) -> Optional[Dict]:
        """Get asset URLs for a specific tile and month."""
        # Extract month number (e.g., "2024-01" -> "01")
        month_num = month.split('-')[-1]

        # Map tile_id to tile directory (e.g., tile_x000_y000 -> tile_000)
        # For now, use a simple mapping
        tile_num = self._extract_tile_number(tile_id)
        if tile_num is None:
            return None

        tile_dir = TILES_DIR / f"tile_{tile_num:03d}" / f"month_{month_num}"

        if not tile_dir.exists():
            return None

        # Generate asset URLs (relative to static file serving)
        base_url = f"/static/tiles/tile_{tile_num:03d}/month_{month_num}"

        return {
            'tile_id': tile_id,
            'month': month,
            'actual': f"{base_url}/actual.png",
            'predicted': f"{base_url}/predicted.png",
            'residual': f"{base_url}/residual.png"
        }

    def _extract_tile_number(self, tile_id: str) -> Optional[int]:
        """Extract numeric tile number from tile_id."""
        # Handle formats like tile_x000_y000, tile_000, etc.
        import re

        # Try to extract first number after 'tile'
        match = re.search(r'tile[_x]*(\d+)', tile_id)
        if match:
            return int(match.group(1))

        return None


# Global instance
data_loader = DataLoader()
