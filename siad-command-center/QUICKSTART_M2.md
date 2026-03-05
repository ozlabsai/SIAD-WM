# SIAD Command Center - Quick Start (M2)

Complete guide to running the SIAD Command Center frontend and backend together.

## Prerequisites

- Python 3.9+ with UV
- Node.js 18+ with npm
- Mapbox account (optional, for map tiles)

---

## Backend Setup

1. **Navigate to API directory:**
   ```bash
   cd api
   ```

2. **Start the backend server:**
   ```bash
   uv run uvicorn main:app --reload --port 8001
   ```

3. **Verify backend is running:**
   ```bash
   curl http://localhost:8001/api/aoi
   # Should return SF Bay Area metadata
   ```

**Backend URL:** http://localhost:8001

**Available Endpoints:**
- `GET /api/aoi` - Area of Interest metadata
- `GET /api/detect/hotspots?min_score=0.5&limit=100` - Hotspot list
- `GET /api/detect/tile/{tile_id}` - Tile detail
- `GET /api/tiles/{tile_id}/assets?month=2024-01` - Imagery URLs
- `GET /static/tiles/...` - Static satellite imagery

---

## Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies (first time only):**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   ```bash
   # Edit .env.local
   NEXT_PUBLIC_API_URL=http://localhost:8001
   NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here  # Optional
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Open in browser:**
   ```
   http://localhost:3000
   ```

**Frontend URL:** http://localhost:3000

---

## Running Both Servers

### Option 1: Two Terminals

**Terminal 1 (Backend):**
```bash
cd siad-command-center/api
uv run uvicorn main:app --reload --port 8001
```

**Terminal 2 (Frontend):**
```bash
cd siad-command-center/frontend
npm run dev
```

### Option 2: Background Processes

**Start both servers:**
```bash
# Backend (background)
cd api && uv run uvicorn main:app --reload --port 8001 &

# Frontend (background)
cd frontend && npm run dev &
```

**Stop both servers:**
```bash
# Find and kill processes
lsof -ti:8001 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

---

## Verification

### 1. Backend Health Check
```bash
curl http://localhost:8001/api/aoi
```
Expected output:
```json
{
  "name": "San Francisco Bay Area",
  "bounds": [-122.5, 37.0, -121.5, 38.0],
  "tileCount": 128,
  "timeRange": ["2024-01", "2024-12"],
  "description": "Synthetic satellite change detection dataset covering SF Bay Area"
}
```

### 2. Frontend Health Check
```bash
curl -I http://localhost:3000
```
Expected output:
```
HTTP/1.1 200 OK
...
```

### 3. Hotspots API
```bash
curl "http://localhost:8001/api/detect/hotspots?min_score=0.5&limit=3" | python3 -m json.tool
```

---

## UI Features

### Dashboard (http://localhost:3000)

**Header:**
- Title: "SIAD: Infrastructure Acceleration Detector"
- AOI name: "San Francisco Bay Area"
- Stats: Tile count, hotspot count

**Map View:**
- Full-screen Mapbox GL JS map
- Centered on SF Bay (37.7749, -122.4194)
- Hotspot markers color-coded by score:
  - Red: score >= 0.7 (high confidence)
  - Amber: score >= 0.5 (medium confidence)
  - Cyan: score < 0.5 (low confidence)
- Click marker to select hotspot

**Detections Rail (Right Sidebar):**
- 400px width, collapsible
- Scrollable list of hotspot cards
- Sorted by score (descending)
- Each card shows:
  - Tile ID (monospace)
  - Score (large, prominent)
  - Confidence badge (High/Medium/Low)
  - Alert type badge (Structural/Activity)
  - First detected month
  - Change type
- Click card to select hotspot
- Empty state message if no hotspots

**Timeline Player (Bottom Bar):**
- 80px height, full-width scrubber
- Play/Pause button
- Current month display
- Month range: Jan 2024 - Dec 2024
- Playback speed selector: 1x, 2x, 4x
- Scrubber with month markers
- Auto-advance when playing

---

## Troubleshooting

### Backend Issues

**Port 8001 already in use:**
```bash
lsof -ti:8001 | xargs kill -9
```

**No data in backend:**
- Check `api/data/` directory for synthetic data
- Run data generation scripts if needed

### Frontend Issues

**Port 3000 already in use:**
```bash
lsof -ti:3000 | xargs kill -9
```

**Map not displaying:**
- Check `.env.local` for `NEXT_PUBLIC_MAPBOX_TOKEN`
- Map will show placeholder if token is invalid/missing
- Get token at https://account.mapbox.com/

**No hotspots showing:**
- Verify backend is running: `curl http://localhost:8001/api/aoi`
- Check browser console for API errors (F12)
- Verify `NEXT_PUBLIC_API_URL=http://localhost:8001` in `.env.local`

**Build errors:**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

---

## Development Workflow

### Making Changes

**Backend changes:**
1. Edit files in `api/`
2. FastAPI auto-reloads on file save
3. Test endpoint: `curl http://localhost:8001/api/...`

**Frontend changes:**
1. Edit files in `frontend/`
2. Next.js hot-reloads on file save
3. Check browser console (F12) for errors
4. Verify TypeScript: `npm run build`

### Adding New Features

**New API endpoint:**
1. Add route in `api/main.py` or `api/routes/`
2. Update TypeScript types in `frontend/types/index.ts`
3. Add API client function in `frontend/lib/api.ts`
4. Use in component with React Query

**New UI component:**
1. Create in `frontend/components/`
2. Import types from `@/types`
3. Use utilities from `@/lib/utils`
4. Add to page in `frontend/app/page.tsx`

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│           Browser (Port 3000)               │
│  ┌─────────────────────────────────────┐   │
│  │     Next.js 14 Frontend             │   │
│  │  - MapView (Mapbox GL JS)           │   │
│  │  - DetectionsRail (Hotspot cards)   │   │
│  │  - TimelinePlayer (Month scrubber)  │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼──────────────────────────┘
                  │ HTTP (React Query)
                  ↓
┌─────────────────────────────────────────────┐
│         FastAPI Backend (Port 8001)         │
│  ┌─────────────────────────────────────┐   │
│  │     API Endpoints                   │   │
│  │  - /api/aoi                         │   │
│  │  - /api/detect/hotspots             │   │
│  │  - /api/detect/tile/{tile_id}       │   │
│  │  - /api/tiles/{tile_id}/assets      │   │
│  │  - /static/tiles/...                │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼──────────────────────────┘
                  │
                  ↓
         ┌─────────────────┐
         │  Synthetic Data  │
         │  (api/data/)     │
         └─────────────────┘
```

---

## File Structure

```
siad-command-center/
├── api/                     # FastAPI backend
│   ├── main.py             # API entry point
│   ├── routes/             # API route handlers
│   ├── data/               # Synthetic data
│   └── static/             # Static assets
├── frontend/               # Next.js frontend
│   ├── app/                # App Router pages
│   │   ├── page.tsx        # Dashboard
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Lattice theme
│   ├── components/         # React components
│   │   ├── MapView.tsx     # Map component
│   │   ├── DetectionsRail.tsx  # Hotspot rail
│   │   └── TimelinePlayer.tsx  # Timeline
│   ├── lib/                # Utilities
│   │   ├── api.ts          # API client
│   │   └── utils.ts        # Helpers
│   └── types/              # TypeScript types
│       └── index.ts        # Type definitions
├── docs/                   # Documentation
│   └── UI_COPY.csv        # UI copy specifications
├── M2_IMPLEMENTATION_REPORT.md  # M2 report
└── QUICKSTART_M2.md        # This file
```

---

## Next Steps

### M3: Advanced Features

1. **Tile Detail Modal**
   - Timeline chart with residuals
   - Baseline comparison visualization
   - Modality attribution breakdown
   - Satellite imagery viewer

2. **Filter Controls**
   - Score threshold slider
   - Date range picker
   - Alert type selector
   - Confidence filter

3. **Search & Export**
   - Text search by tile ID
   - GeoJSON export
   - CSV export for timeline data

4. **Enhanced Map**
   - Heatmap overlay
   - Tile boundary visualization
   - Popup on hover

---

## Resources

- **Backend API Docs:** http://localhost:8001/docs (Swagger UI)
- **Frontend README:** `frontend/README.md`
- **M2 Report:** `M2_IMPLEMENTATION_REPORT.md`
- **UI Copy Specs:** `docs/UI_COPY.csv`

---

## Support

If you encounter issues:

1. Check both servers are running:
   ```bash
   curl http://localhost:8001/api/aoi  # Backend
   curl -I http://localhost:3000       # Frontend
   ```

2. Check browser console (F12) for errors

3. Restart both servers:
   ```bash
   # Kill existing processes
   lsof -ti:8001 | xargs kill -9
   lsof -ti:3000 | xargs kill -9

   # Restart
   cd api && uv run uvicorn main:app --reload --port 8001 &
   cd frontend && npm run dev &
   ```

4. Check logs:
   - Backend: Terminal running uvicorn
   - Frontend: Terminal running npm run dev

---

**Ready to build the future of infrastructure monitoring!**
