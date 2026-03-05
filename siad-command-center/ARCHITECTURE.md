# SIAD Command Center - System Architecture

**Version 1.0.0** | Last Updated: 2025-03-04

This document describes the system architecture, data flow, and technical design decisions for the SIAD Command Center.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Data Flow](#data-flow)
4. [Component Architecture](#component-architecture)
5. [API Design](#api-design)
6. [Data Models](#data-models)
7. [Technology Choices](#technology-choices)
8. [Performance Considerations](#performance-considerations)
9. [Security & CORS](#security--cors)
10. [Future Enhancements](#future-enhancements)

---

## System Overview

SIAD Command Center is a **3-tier web application** for satellite anomaly detection:

1. **Data Tier**: HDF5 files + JSON metadata
2. **API Tier**: FastAPI backend serving detection data
3. **Presentation Tier**: Next.js frontend with interactive visualizations

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser (Client)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        Next.js Frontend (localhost:3000)             │   │
│  │  - React Components (MapView, DetectionsRail, etc)  │   │
│  │  - TanStack Query (API client + caching)            │   │
│  │  - Mapbox GL JS (map rendering)                     │   │
│  │  - Recharts (data visualization)                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/JSON (REST API)
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              FastAPI Backend (localhost:8001)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Routes                                           │   │
│  │  - /health              (health check)              │   │
│  │  - /api/aoi             (AOI metadata)              │   │
│  │  - /api/detect/hotspots (list detections)           │   │
│  │  - /api/detect/tile/:id (tile details)              │   │
│  │  - /static/tiles/*      (static imagery)            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Services                                             │   │
│  │  - DataLoader (HDF5 reading, caching)               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │ File I/O
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    Data Storage (Filesystem)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ data/residuals_test.h5    (HDF5 residuals data)     │   │
│  │ data/aoi_sf_seed/         (JSON metadata)           │   │
│  │   ├── hotspots_ranked.json                          │   │
│  │   ├── metadata.json                                 │   │
│  │   ├── months.json                                   │   │
│  │   └── tiles/              (per-tile data + imagery) │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagram

### Full System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                 Satellite Data Pipeline (Upstream)              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │ SAR Imagery  │   │   Optical    │   │   Thermal    │       │
│  │ (Sentinel-1) │   │ (Sentinel-2) │   │  (Landsat)   │       │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘       │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │  World Model    │                          │
│                    │  (PyTorch DL)   │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │ Residual Calc.  │                          │
│                    │ Actual - Pred   │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │  HDF5 Export    │                          │
│                    └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HDF5 files
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│              SIAD Command Center (This Application)             │
│                                                                  │
│  Frontend (Next.js)  ◄──HTTP/JSON──►  Backend (FastAPI)        │
│                                              │                   │
│                                         HDF5 Reader              │
│                                              │                   │
│                                         Data Files               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Exports (GeoJSON/CSV)
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                 Downstream Analysis (Optional)                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   GIS Tools  │   │  Notebooks   │   │   Reporting  │       │
│  │    (QGIS)    │   │  (Jupyter)   │   │   (Tableau)  │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Request Flow: Loading Hotspots

```
1. User opens http://localhost:3000
   └─> Next.js page renders

2. Frontend useQuery hook triggers
   └─> GET /api/detect/hotspots?min_score=0.5&limit=100

3. FastAPI backend receives request
   └─> CORS middleware validates origin
   └─> Route handler: detection.get_hotspots()
   └─> Service: data_loader.get_hotspots_list()
       └─> Reads: data/aoi_sf_seed/hotspots_ranked.json
       └─> Filters by min_score
       └─> Limits to 100 results
       └─> Returns List[Hotspot]

4. Backend serializes to JSON
   └─> Response: [{"tileId": "tile_1", "score": 0.946, ...}, ...]

5. Frontend receives response
   └─> TanStack Query caches result
   └─> React re-renders with data
   └─> DetectionsRail displays hotspot cards
   └─> MapView plots hotspot markers
```

### Request Flow: Viewing Tile Detail

```
1. User clicks hotspot card "tile_1"
   └─> onClick handler triggers
   └─> setSelectedHotspot(hotspot)
   └─> setIsModalOpen(true)

2. Modal component renders
   └─> useQuery hook for tile detail
   └─> GET /api/detect/tile/1

3. Backend receives request
   └─> Route: detection.get_tile_detail(tile_id=1)
   └─> Service: data_loader.get_tile_timeline()
       └─> Reads: data/aoi_sf_seed/tiles/1/timeline.json
       └─> Reads: data/aoi_sf_seed/metadata.json
       └─> Constructs TileDetail response

4. Backend returns tile detail
   └─> Includes: metadata, timeline, imagery URLs

5. Frontend displays in modal
   └─> Timeline chart (Recharts)
   └─> Imagery comparison
   └─> Metadata table
```

### Data Update Flow (Timeline Playback)

```
1. User clicks "Play" button
   └─> setIsPlaying(true)

2. useEffect hook starts interval
   └─> Every 1000ms (or 500ms/250ms for 2x/4x):
       └─> currentMonth increments
       └─> setCurrentMonth(nextMonth)

3. React re-renders with new currentMonth
   └─> useMemo recalculates filteredHotspots
       └─> Filters allHotspots by currentMonth
   └─> MapView receives new hotspots
       └─> Updates markers on map
   └─> DetectionsRail displays filtered list

4. Timeline continues until end or user clicks "Pause"
```

---

## Component Architecture

### Frontend Component Hierarchy

```
App (page.tsx)
├── Header
│   ├── Title
│   └── Stats (AOI name, tile count, hotspot count)
│
├── Main Content (flex container)
│   ├── MapView
│   │   ├── Mapbox GL JS instance
│   │   ├── Hotspot markers (GeoJSON layer)
│   │   └── MapLegend
│   │
│   └── DetectionsRail
│       ├── Header (title + collapse button)
│       ├── FilterPanel
│       │   ├── Score threshold slider
│       │   ├── Date range pickers
│       │   ├── Alert type dropdown
│       │   ├── Confidence dropdown
│       │   └── Search input (tile ID)
│       │
│       ├── Hotspot Cards List (scrollable)
│       │   └── HotspotCard (repeated)
│       │       ├── Tile ID
│       │       ├── Score badge
│       │       ├── Severity badge
│       │       ├── Alert type badge
│       │       └── Metadata (onset, change type)
│       │
│       └── Footer
│           ├── Hotspot count
│           └── Export buttons (GeoJSON, CSV)
│
├── TimelinePlayer (bottom bar)
│   ├── Play/Pause button
│   ├── Month display
│   ├── Timeline slider
│   └── Speed selector (1x, 2x, 4x)
│
└── TileDetailModal (overlay)
    ├── Header (tile ID + close button)
    ├── Timeline Chart (Recharts line chart)
    ├── Imagery Comparison
    │   ├── Actual image
    │   ├── Predicted image
    │   └── Residual heatmap
    ├── Modality Attribution (bar chart)
    └── Metadata Table
```

### Backend Component Architecture

```
api/
├── main.py (FastAPI app)
│   ├── CORS middleware
│   ├── Static files mount (/static/tiles)
│   ├── Health endpoint (/health)
│   └── Router includes
│
├── config.py (configuration)
│   ├── DATA_DIR
│   ├── SEED_DIR
│   ├── TILES_DIR
│   ├── API_PREFIX
│   └── CORS_ORIGINS
│
├── models/
│   └── schemas.py (Pydantic models)
│       ├── AOI
│       ├── Hotspot
│       ├── TileDetail
│       └── TimelineEntry
│
├── routes/
│   ├── aoi.py
│   │   └── GET /api/aoi
│   ├── detection.py
│   │   ├── GET /api/detect/hotspots
│   │   └── GET /api/detect/tile/{tile_id}
│   └── tiles.py (reserved for future)
│
└── services/
    └── data_loader.py
        ├── HDF5 file handle (singleton)
        ├── get_aoi_metadata()
        ├── get_hotspots_list()
        ├── get_tile_timeline()
        └── close() (cleanup)
```

---

## API Design

### RESTful Principles

The API follows REST conventions:

- **Resources**: AOI, Hotspots, Tiles
- **Methods**: GET (read-only operations)
- **Status Codes**: 200 (success), 404 (not found), 422 (validation error)
- **Content-Type**: `application/json`

### Endpoint Design Patterns

**Collection endpoints** (list resources):
```
GET /api/detect/hotspots
- Returns array of resources
- Supports filtering (min_score, limit)
- Sorted by score (descending)
```

**Single resource endpoints** (get by ID):
```
GET /api/detect/tile/{tile_id}
- Returns single resource
- 404 if not found
```

**Metadata endpoints** (system info):
```
GET /api/aoi
- Returns AOI-level metadata
- No ID required (singleton resource)
```

### Pagination Strategy

Current implementation uses **limit-based** pagination:
```
GET /api/detect/hotspots?limit=100
```

For future scaling, consider **cursor-based** pagination:
```
GET /api/detect/hotspots?limit=100&cursor=tile_50
```

### Filtering Strategy

**Server-side** (implemented):
- `min_score`: Filter by anomaly threshold
- `limit`: Limit result count

**Client-side** (implemented in frontend):
- Date range: Filter by month
- Alert type: Filter by severity
- Confidence: Filter by confidence level
- Search: Filter by tile ID substring

This hybrid approach balances:
- **Server-side**: Reduces network payload (score filtering is expensive)
- **Client-side**: Enables instant UI updates (no network round-trip)

---

## Data Models

### Core Entities

#### Hotspot

**Purpose**: Represents a single anomaly detection event.

**Schema**:
```typescript
interface Hotspot {
  tileId: string;          // e.g., "tile_1"
  score: number;           // 0.0 - 1.0
  lat: number;             // Latitude (WGS84)
  lon: number;             // Longitude (WGS84)
  month: string;           // e.g., "Month 3" or "2024-03"
  changeType: string;      // "urban_construction", "infrastructure", etc.
  region: string;          // "temperate", "tropical", "polar"
  onset?: string;          // First detection month
  confidence?: string;     // "High", "Medium", "Low"
  alert_type?: string;     // "Critical", "High", "Elevated"
}
```

#### TileDetail

**Purpose**: Detailed analysis for a specific tile.

**Schema**:
```typescript
interface TileDetail {
  tileId: string;
  metadata: {
    lat: number;
    lon: number;
    region: string;
    changeType: string;
    onset: string;
  };
  timeline: TimelineEntry[];
}

interface TimelineEntry {
  month: string;
  score: number;
  timestamp?: string;  // ISO 8601 date
}
```

#### AOI

**Purpose**: Area of Interest metadata (study region info).

**Schema**:
```typescript
interface AOI {
  name: string;           // "SF Bay Area"
  bounds: [number, number, number, number];  // [west, south, east, north]
  tileCount: number;      // Total tiles in AOI
  timeRange: [string, string];  // [start_month, end_month]
}
```

### Data Relationships

```
AOI (1)
 └── contains (1..*)
     ├── Tile (N)
     │    └── has (1..*)
     │        └── Hotspot (M)
     │             └── detected_in
     │                 └── Month
     │
     └── Month (T)
          └── has (0..*)
              └── Hotspot
```

---

## Technology Choices

### Backend: FastAPI

**Why FastAPI:**
- ✅ **Performance**: ASGI-based, handles async I/O efficiently
- ✅ **Type Safety**: Pydantic models with automatic validation
- ✅ **API Docs**: Auto-generated OpenAPI/Swagger docs
- ✅ **Modern Python**: Native async/await support
- ✅ **Easy Testing**: TestClient for integration tests

**Alternatives Considered:**
- Flask: Simpler but lacks async and auto-docs
- Django REST: Too heavyweight for this use case

### Frontend: Next.js

**Why Next.js:**
- ✅ **React 18**: Modern React with Server Components
- ✅ **TypeScript**: Type safety across codebase
- ✅ **Performance**: Automatic code splitting, image optimization
- ✅ **Developer Experience**: Fast refresh, zero config
- ✅ **Production Ready**: Built-in optimizations

**Alternatives Considered:**
- Create React App: Deprecated, not actively maintained
- Vite: Fast but lacks Next.js SSR/SSG capabilities

### Data Storage: HDF5

**Why HDF5:**
- ✅ **Efficient**: Optimized for large array data
- ✅ **Hierarchical**: Natural fit for tile-based data
- ✅ **Compression**: Reduces storage by 10x
- ✅ **Partial Reads**: Load only needed tiles (not entire file)
- ✅ **Industry Standard**: Widely used in scientific computing

**Alternatives Considered:**
- PostgreSQL: Overkill for read-only data, slower for arrays
- Cloud Storage (S3): Adds latency, requires auth

### Map Rendering: Mapbox GL JS

**Why Mapbox:**
- ✅ **Performance**: WebGL-based, handles 1000+ markers smoothly
- ✅ **Customization**: Full control over styling
- ✅ **GeoJSON Support**: Native understanding of geospatial data
- ✅ **Interactive**: Click handlers, hover states, zoom controls

**Alternatives Considered:**
- Leaflet: Simpler but canvas-based (slower for many markers)
- Google Maps: More restrictive licensing, less customization

### State Management: TanStack Query

**Why TanStack Query:**
- ✅ **Caching**: Automatic request deduplication
- ✅ **Sync**: Background refetching keeps data fresh
- ✅ **Optimistic Updates**: Better UX with immediate feedback
- ✅ **DevTools**: Inspect cache and query states

**Alternatives Considered:**
- Redux: Overkill, too much boilerplate
- SWR: Similar but less features than TanStack Query

---

## Performance Considerations

### Backend Optimizations

1. **HDF5 File Caching**
   - DataLoader keeps HDF5 file open (singleton pattern)
   - Avoids repeated file open/close overhead
   - ~50ms improvement per request

2. **JSON File Reading**
   - Read JSON files once at startup
   - Cache in memory for subsequent requests
   - Trade-off: Memory for speed

3. **Filtering Strategy**
   - Filter by score on server (reduces payload)
   - Other filters on client (instant UI updates)

4. **Static File Serving**
   - FastAPI StaticFiles middleware
   - Efficient file streaming (no memory buffering)

### Frontend Optimizations

1. **Code Splitting**
   - Next.js automatic route-based splitting
   - Lazy load modal components
   - Reduces initial bundle size

2. **Map Marker Clustering** (future)
   - Use Mapbox clustering for 1000+ hotspots
   - Improves render performance

3. **Virtualized Lists** (future)
   - Use react-window for DetectionsRail
   - Only render visible cards (constant memory)

4. **Memoization**
   - useMemo for filteredHotspots computation
   - Avoids re-filtering on every render

### Caching Strategy

```
┌──────────────┐
│   Browser    │
│   ├─ Memory  │ ◄─ React state (component-level)
│   └─ Query   │ ◄─ TanStack Query cache (5min TTL)
└──────────────┘
       │
       │ HTTP
       │
┌──────────────┐
│   Backend    │
│   ├─ Memory  │ ◄─ HDF5 file handle (process-level)
│   └─ Disk    │ ◄─ HDF5 + JSON files
└──────────────┘
```

**Cache Invalidation:**
- Frontend: Manual refresh or 5min TTL
- Backend: Restart required for data updates (by design - demo app)

---

## Security & CORS

### CORS Configuration

**Allowed Origins:**
```python
CORS_ORIGINS = [
    "http://localhost:3000",    # Dev frontend
    "http://127.0.0.1:3000",    # Dev frontend (alt)
]
```

**Allowed Methods:**
- GET (all endpoints)
- POST, PUT, DELETE (none implemented yet)

**Allowed Headers:**
- All (`*`) for simplicity in dev

### Security Considerations

**Current (Demo):**
- ✅ CORS enabled for localhost only
- ✅ Read-only API (no mutations)
- ❌ No authentication (public demo)
- ❌ No rate limiting

**Production Recommendations:**
1. **Authentication**: Add API keys or OAuth2
2. **Rate Limiting**: Prevent abuse (e.g., 100 req/min per IP)
3. **HTTPS**: Encrypt data in transit
4. **Input Validation**: Already handled by Pydantic (✓)
5. **Content Security Policy**: Prevent XSS attacks

### Data Privacy

**No PII Collected:**
- No user accounts
- No cookies
- No tracking
- Satellite data is public domain

---

## Future Enhancements

### Near-Term (Next Sprint)

1. **Advanced Filtering**
   - Multi-select change types
   - Confidence level filtering
   - Spatial filtering (draw polygon on map)

2. **Real-Time Updates**
   - WebSocket connection for live data
   - Server-sent events for new detections

3. **Enhanced Visualizations**
   - 3D terrain view (Mapbox 3D)
   - Heatmap overlay (density visualization)
   - Time-lapse GIF export

### Mid-Term (Next Quarter)

1. **User Accounts**
   - Save custom filters
   - Bookmark favorite tiles
   - Export history

2. **Collaboration**
   - Shared workspaces
   - Comments on detections
   - Case management workflow

3. **Advanced Analytics**
   - Anomaly clustering (DBSCAN)
   - Trend analysis (growth rate calculation)
   - Predictive alerts (forecasting)

### Long-Term (6+ Months)

1. **Scalability**
   - PostgreSQL backend (replace JSON files)
   - Redis caching layer
   - Load balancer for horizontal scaling

2. **Machine Learning Integration**
   - Retrain model on validated detections
   - Active learning feedback loop
   - Explainable AI (SHAP values for attribution)

3. **Enterprise Features**
   - Multi-tenancy (organizations)
   - Role-based access control
   - Audit logging
   - SLA monitoring

---

## Appendix: Key Files

### Configuration
- `api/config.py`: Backend settings
- `frontend/.env.local`: Frontend environment variables

### Entry Points
- `api/main.py`: Backend startup
- `frontend/app/page.tsx`: Frontend main page

### Data Models
- `api/models/schemas.py`: Pydantic schemas
- `frontend/types/index.ts`: TypeScript types

### Core Logic
- `api/services/data_loader.py`: Data access layer
- `frontend/lib/api.ts`: API client

---

**Architecture Version:** 1.0.0
**Last Reviewed:** 2025-03-04
**Next Review:** After M6 completion
