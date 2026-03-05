# SIAD Command Center - Quick Start Guide

## Start Backend Server

```bash
cd /Users/guynachshon/Documents/ozlabs/labs/SIAD/siad-command-center
uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

Server will start at: **http://localhost:8001**

## Access API Documentation

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

## Test Endpoints

```bash
# Health check
curl http://localhost:8001/health

# Get AOI metadata
curl http://localhost:8001/api/aoi

# Get available months
curl http://localhost:8001/api/aoi/months

# Get top hotspots
curl 'http://localhost:8001/api/detect/hotspots?min_score=0.5&limit=10'

# Get tile detail
curl http://localhost:8001/api/detect/tile/tile_x000_y000

# Get tile assets
curl 'http://localhost:8001/api/tiles/tile_x000_y000/assets?month=2024-01'

# Get satellite image
curl http://localhost:8001/static/tiles/tile_000/month_01/actual.png -o actual.png
```

## Run Test Suite

```bash
uv run python test_api.py
```

Expected output: **7/7 tests passed**

## Frontend Development

The backend is configured for CORS with these origins:
- http://localhost:3000 (React default)
- http://localhost:5173 (Vite default)
- http://localhost:5175 (Alternative port)

All API endpoints are prefixed with `/api/`

## Data Sources

- **HDF5 Data**: `data/residuals_test.h5` (20 tiles, 12 months each)
- **Metadata**: `data/satellite_imagery/metadata.json` (75 tiles)
- **Imagery**: `data/satellite_imagery/tiles/tile_{NNN}/month_{MM}/`

## File Structure

```
/Users/guynachshon/Documents/ozlabs/labs/SIAD/siad-command-center/
├── api/                    # Backend API
│   ├── main.py            # FastAPI application
│   ├── config.py          # Configuration
│   ├── models/            # Pydantic schemas
│   ├── routes/            # API endpoints
│   └── services/          # Data loader
├── data/                  # Data files
│   ├── residuals_test.h5 # HDF5 data
│   └── satellite_imagery/ # Metadata & images
├── test_api.py           # Test suite
└── QUICKSTART.md         # This file
```

## Troubleshooting

**Port already in use?**
```bash
# Use a different port
uv run uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload
```

**Missing dependencies?**
```bash
uv pip install fastapi uvicorn h5py python-multipart
```

**HDF5 file not found?**
- Ensure you're running from the project root directory
- Check `data/residuals_test.h5` exists

## Next Steps

1. Start the backend server (see command above)
2. Test endpoints with curl or visit `/docs`
3. Start frontend development (M1b)
4. Connect frontend to `http://localhost:8001/api/`

For detailed API documentation, see `api/README.md`
For implementation details, see `IMPLEMENTATION_REPORT.md`
