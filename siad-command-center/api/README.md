# SIAD Command Center API

Backend API for Satellite Intelligence Anomaly Detection Command Center.

## Overview

FastAPI-based REST API that serves hotspot detection data from HDF5 files and satellite imagery.

## Architecture

```
api/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── models/
│   └── schemas.py       # Pydantic data models
├── routes/
│   ├── aoi.py          # Area of Interest endpoints
│   ├── detection.py    # Hotspot detection endpoints
│   └── tiles.py        # Tile asset endpoints
└── services/
    └── data_loader.py  # HDF5 and metadata data loader
```

## Endpoints

### Health Check
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API info

### AOI (Area of Interest)
- `GET /api/aoi` - Get AOI metadata
- `GET /api/aoi/months` - Get available months

### Detection
- `GET /api/detect/hotspots?min_score=0.5&limit=10` - Get ranked hotspots
- `GET /api/detect/tile/{tile_id}` - Get detailed tile information

### Tiles
- `GET /api/tiles/{tile_id}/assets?month=2024-01` - Get tile imagery URLs

### Static Files
- `GET /static/tiles/{tile_dir}/{month_dir}/{image}.png` - Serve satellite imagery

## Data Structure

### HDF5 File Structure
```
residuals_test.h5
├── tile_x000_y000/
│   ├── residuals (12, 256)      # Monthly residuals
│   ├── tile_scores (12,)        # Monthly anomaly scores
│   ├── timestamps (12,)         # Unix timestamps
│   ├── baselines/
│   │   ├── persistence (12,)    # Persistence baseline
│   │   └── seasonal (12,)       # Seasonal baseline
│   └── metadata                 # Tile metadata attributes
└── ...
```

### Response Models

#### Hotspot
```json
{
  "tileId": "tile_x000_y000",
  "score": 1.0,
  "lat": 29.05,
  "lon": -138.11,
  "month": "2024-06",
  "changeType": "deforestation",
  "region": "desert"
}
```

#### HotspotDetail
```json
{
  "tileId": "tile_x000_y000",
  "score": 1.0,
  "lat": 29.05,
  "lon": -138.11,
  "region": "desert",
  "changeType": "deforestation",
  "onsetMonth": 7,
  "heatmap": [[...], ...],  // 16x16 array
  "timeline": [
    {
      "month": "2024-01",
      "score": 0.31,
      "timestamp": "2024-01-01T00:00:00"
    },
    ...
  ],
  "baselines": {
    "persistence": [0.56, 0.52, ...],
    "seasonal": [0.50, 0.46, ...]
  }
}
```

## Running the API

### Development Server
```bash
# Start server on port 8001
uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### Testing
```bash
# Run test suite
uv run python test_api.py

# Manual tests
curl http://localhost:8001/health
curl http://localhost:8001/api/aoi
curl 'http://localhost:8001/api/detect/hotspots?min_score=0.5&limit=5'
curl http://localhost:8001/api/detect/tile/tile_x000_y000
curl 'http://localhost:8001/api/tiles/tile_x000_y000/assets?month=2024-01'
```

### API Documentation
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Configuration

Edit `api/config.py` to customize:
- Data paths (HDF5, metadata, tiles directory)
- CORS origins
- API prefix
- Default detection thresholds

## CORS

CORS is enabled for:
- http://localhost:3000 (React default)
- http://localhost:5173 (Vite default)
- http://localhost:5175 (Alternative port)

## Dependencies

- FastAPI - Web framework
- Uvicorn - ASGI server
- h5py - HDF5 file reading
- numpy - Numerical operations
- pydantic - Data validation

## Notes

- HDF5 file is kept open during application lifetime for performance
- Metadata is cached in memory on startup
- Static files are served directly by FastAPI
- All timestamps are in ISO 8601 format
- Heatmaps are 16x16 arrays reshaped from 256-token residuals
- Scores are normalized to [0, 1] range
