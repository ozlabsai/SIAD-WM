# SIAD Command Center

**Satellite Intelligence Anomaly Detection - Command & Control Interface**

A professional web application for detecting and analyzing infrastructure changes from multi-modal satellite imagery using AI-powered anomaly detection.

![SIAD Command Center](docs/screenshot.png)

## Overview

SIAD Command Center provides real-time detection and analysis of infrastructure anomalies from satellite data. The system combines SAR (Synthetic Aperture Radar), optical, and thermal satellite imagery with a world model to identify unexpected changes indicative of construction, urban development, or infrastructure expansion.

### Key Features

- **Automated Anomaly Detection**: ML-powered detection of infrastructure changes from satellite residuals
- **Interactive Map Visualization**: Mapbox-powered interface showing hotspot locations
- **Temporal Timeline**: Playback and scrubbing through months of satellite data
- **Detailed Analytics**: Per-tile analysis with timeline charts, heatmaps, and modality attribution
- **Filtering & Search**: Dynamic filtering by score, date range, change type, and tile ID
- **Data Export**: Export detections as GeoJSON or CSV for downstream analysis
- **Professional UI**: Lattice-style dark interface designed for operations centers

### Technology Stack

**Frontend:**
- Next.js 14 (React 18)
- TypeScript
- Mapbox GL JS (map rendering)
- Recharts (data visualization)
- TanStack Query (data fetching)
- Tailwind CSS (styling)

**Backend:**
- FastAPI (Python 3.13+)
- HDF5 (data storage)
- NumPy (array operations)
- Uvicorn (ASGI server)

---

## Quick Start

### Prerequisites

- **Python 3.13+** (managed via `uv`)
- **Node.js 18+** and npm
- **Mapbox Access Token** (optional, for basemaps)

### 1. Clone Repository

```bash
git clone <repository-url>
cd siad-command-center
```

### 2. Setup Backend

```bash
# Install UV package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Backend dependencies are managed by UV
# Data files should be in data/ directory
```

### 3. Setup Frontend

```bash
cd frontend
npm install

# Optional: Configure Mapbox token
echo "NEXT_PUBLIC_MAPBOX_TOKEN=your_token_here" > .env.local
```

### 4. Run Backend API

```bash
# From project root
uv run uvicorn api.main:app --reload --port 8001
```

Backend will be available at `http://localhost:8001`

API docs at `http://localhost:8001/docs`

### 5. Run Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 6. Access Application

Open your browser to `http://localhost:3000`

---

## Project Structure

```
siad-command-center/
├── api/                      # FastAPI backend
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration
│   ├── models/              # Data models (Pydantic schemas)
│   ├── routes/              # API endpoints
│   │   ├── aoi.py          # AOI metadata
│   │   ├── detection.py    # Hotspot detection
│   │   └── tiles.py        # Tile details
│   └── services/            # Business logic
│       └── data_loader.py  # HDF5 data loading
│
├── frontend/                 # Next.js frontend
│   ├── app/                 # Next.js app directory
│   │   ├── page.tsx        # Main dashboard
│   │   ├── layout.tsx      # Root layout
│   │   └── providers.tsx   # React Query provider
│   ├── components/          # React components
│   │   ├── MapView.tsx           # Mapbox map
│   │   ├── DetectionsRail.tsx    # Hotspot list sidebar
│   │   ├── TimelinePlayer.tsx    # Timeline controls
│   │   ├── TileDetailModal.tsx   # Detail view modal
│   │   ├── FilterPanel.tsx       # Filtering controls
│   │   └── MapLegend.tsx         # Map legend
│   ├── lib/                 # Utilities
│   │   ├── api.ts          # API client
│   │   └── utils.ts        # Helper functions
│   ├── types/               # TypeScript types
│   │   └── index.ts        # Shared types
│   └── tests/               # Test suites
│       └── e2e/            # Playwright E2E tests
│
├── data/                     # Data storage
│   ├── residuals_test.h5    # HDF5 residuals data
│   └── aoi_sf_seed/         # Seed dataset
│       ├── hotspots_ranked.json
│       ├── metadata.json
│       ├── months.json
│       └── tiles/           # Per-tile data
│
├── scripts/                  # Utility scripts
│   ├── generate_test_dataset.py
│   ├── create_seed_dataset.py
│   ├── validate_demo_data.py
│   └── ...
│
├── tests/                    # Backend tests
│   ├── test_integration.py  # API integration tests
│   └── test_performance.py  # Performance benchmarks
│
├── docs/                     # Documentation
├── DEMO_SCRIPT.md           # 2-minute demo walkthrough
├── ARCHITECTURE.md          # System architecture
├── TROUBLESHOOTING.md       # Common issues
└── README.md                # This file
```

---

## Usage Guide

### Basic Workflow

1. **View Hotspots**: Detection rail on right shows ranked anomalies
2. **Select Hotspot**: Click card or map marker to view details
3. **Analyze**: Modal shows timeline, imagery, and attribution
4. **Filter**: Adjust score threshold, date range, or search by tile ID
5. **Export**: Download filtered results as GeoJSON or CSV
6. **Playback**: Use timeline player to watch temporal evolution

### Filtering Options

- **Score Threshold**: Minimum anomaly score (0.0 - 1.0)
- **Date Range**: Start and end months
- **Search**: Filter by tile ID (e.g., "tile 1", "tile 2")
- **Alert Type**: All / Critical / High / Elevated
- **Confidence**: All / High / Medium / Low

### Timeline Playback

- **Play/Pause**: Automatic month-by-month playback
- **Speed**: 1x, 2x, 4x playback speed
- **Scrub**: Click timeline bar to jump to specific month
- **Filter**: Map updates to show hotspots for current month

### Export Formats

**GeoJSON:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [lon, lat]
      },
      "properties": {
        "tileId": "tile_1",
        "score": 0.946,
        "month": "Month 3",
        "changeType": "urban_construction",
        ...
      }
    }
  ]
}
```

**CSV:**
```csv
Tile ID,Score,Latitude,Longitude,Month,Change Type,Region,Confidence,Alert Type
tile_1,0.946,49.182815,-130.949542,Month 3,urban_construction,temperate,High,Critical
```

---

## API Reference

### Base URL

```
http://localhost:8001
```

### Endpoints

#### Health Check

```http
GET /health
```

Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "SIAD Command Center API",
  "version": "1.0.0"
}
```

#### Get AOI Metadata

```http
GET /api/aoi
```

Returns Area of Interest metadata.

**Response:**
```json
{
  "name": "SF Bay Area",
  "bounds": [-122.5, 37.2, -121.5, 38.0],
  "tileCount": 100,
  "timeRange": ["2024-01", "2024-12"]
}
```

#### List Hotspots

```http
GET /api/detect/hotspots?min_score=0.5&limit=100
```

Returns list of detected hotspots.

**Query Parameters:**
- `min_score` (float): Minimum anomaly score (default: 0.5)
- `limit` (int): Maximum results (default: 100)

**Response:**
```json
[
  {
    "tileId": "tile_1",
    "score": 0.946,
    "lat": 49.182815,
    "lon": -130.949542,
    "month": "Month 3",
    "changeType": "urban_construction",
    "region": "temperate",
    "confidence": "High",
    "alert_type": "Critical"
  }
]
```

#### Get Tile Detail

```http
GET /api/detect/tile/{tile_id}
```

Returns detailed analysis for specific tile.

**Response:**
```json
{
  "tileId": "tile_1",
  "metadata": {
    "lat": 49.182815,
    "lon": -130.949542,
    "region": "temperate",
    "changeType": "urban_construction",
    "onset": "Month 4"
  },
  "timeline": [
    {
      "month": "Month 1",
      "score": 0.318,
      "timestamp": "2024-01"
    }
  ]
}
```

---

## Development

### Running Tests

**Backend Integration Tests:**
```bash
uv run pytest tests/test_integration.py -v
```

**Backend Performance Tests:**
```bash
uv run pytest tests/test_performance.py -v
```

**Frontend E2E Tests:**
```bash
cd frontend
npm run test:e2e
```

**Frontend E2E Tests (UI Mode):**
```bash
cd frontend
npm run test:e2e:ui
```

### Linting

**Frontend:**
```bash
cd frontend
npm run lint
```

**Backend:**
```bash
uv run ruff check .
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
npm run start
```

**Backend:**
```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port 8001
```

---

## Data Format

### HDF5 Structure

```
residuals_test.h5
├── metadata/
│   └── aoi (JSON string)
└── tiles/
    ├── 1/
    │   ├── residuals (float32, shape: [months, height, width, channels])
    │   ├── timestamps (int64, shape: [months])
    │   └── coordinates (float32, shape: [2])
    └── 2/
        └── ...
```

### Hotspots JSON

```json
{
  "hotspots": [
    {
      "tile_id": 1,
      "month": 3,
      "change_type": "urban_construction",
      "location": {"lat": 49.18, "lon": -130.95},
      "region_id": 16,
      "size_pixels": 3,
      "mean_score": 0.944,
      "max_score": 0.946,
      "severity": "critical"
    }
  ],
  "total_count": 9
}
```

---

## Performance

### Target Metrics

- **Time to Interactive**: <3s
- **API Response Times**:
  - Health check: <50ms
  - AOI metadata: <100ms
  - Hotspot list (100): <500ms
  - Tile detail: <200ms
- **Frontend Bundle Size**: <1MB
- **Map Rendering**: 60fps
- **Large Dataset**: <2s for 1000 hotspots

### Optimization Tips

1. **Backend**: Use HDF5 caching for frequently accessed tiles
2. **Frontend**: Lazy load map markers with clustering
3. **Network**: Enable gzip compression on API responses
4. **Images**: Use WebP format for tile imagery

---

## Deployment

### Docker (Recommended)

Coming soon - Docker Compose configuration for one-command deployment.

### Manual Deployment

**Backend:**
```bash
# Use production ASGI server
uv run gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

**Frontend:**
```bash
# Build and serve
cd frontend
npm run build
npm run start
```

**Reverse Proxy (Nginx):**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8001;
    }

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

---

## Troubleshooting

### Common Issues

**Backend not starting:**
```bash
# Check Python version
python --version  # Should be 3.13+

# Check data files exist
ls data/residuals_test.h5

# Check port not in use
lsof -i :8001
```

**Frontend not loading:**
```bash
# Check Node version
node --version  # Should be 18+

# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev
```

**Map not rendering:**
- Check Mapbox token in `frontend/.env.local`
- Hotspots will still be visible without basemap

**No hotspots showing:**
- Verify backend is running and healthy: `curl http://localhost:8001/health`
- Check browser console for API errors
- Verify data files exist in `data/aoi_sf_seed/`

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

---

## Demo

Follow the [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for a comprehensive 2-minute walkthrough of all features.

**Quick demo:**
```bash
# Terminal 1: Start backend
uv run uvicorn api.main:app --reload --port 8001

# Terminal 2: Start frontend
cd frontend && npm run dev

# Browser: Open http://localhost:3000
# 1. View hotspots in detection rail
# 2. Click top hotspot to see details
# 3. Adjust filters and observe changes
# 4. Click Play on timeline
# 5. Export data as GeoJSON
```

---

## Contributing

This is a demonstration project for the SIAD system. For questions or contributions, please contact the development team.

### Development Guidelines

1. **Code Style**: Follow existing patterns (TypeScript for frontend, Python type hints for backend)
2. **Tests**: Add tests for new features
3. **Documentation**: Update relevant docs when changing functionality
4. **Commits**: Use clear, descriptive commit messages

---

## License

[Your License Here]

---

## Acknowledgments

- **Satellite Data**: [Data source acknowledgment]
- **World Model**: [Model acknowledgment]
- **Design**: Inspired by Lattice operations interfaces
- **Stack**: Built with FastAPI, Next.js, Mapbox, and modern web technologies

---

## Contact

For questions, issues, or feedback:
- Email: [your-email@example.com]
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]

---

**Version:** 1.0.0
**Last Updated:** 2025-03-04
**Status:** Production Demo Ready
