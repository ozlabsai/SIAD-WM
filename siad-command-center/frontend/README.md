# SIAD Command Center - Frontend

Next.js 14 application with Anduril Lattice-inspired dark UI for satellite-based infrastructure change detection.

## Features

- **Map-First Layout**: Full-screen Mapbox GL JS map with SF Bay Area focus
- **Detections Rail**: Scrollable sidebar with ranked hotspot cards
- **Timeline Player**: Interactive month scrubber with playback controls
- **Dark Theme**: High-contrast Anduril Lattice-style design (no gradients/glows)
- **Real-time Data**: React Query integration with backend API
- **TypeScript**: Full type safety throughout

## Prerequisites

- Node.js 18+ and npm
- Backend API running at http://localhost:8001
- Mapbox account (optional - for actual map tiles)

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   # Edit .env.local and add your Mapbox token (optional)
   NEXT_PUBLIC_API_URL=http://localhost:8001
   NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   ```
   http://localhost:3000
   ```

## Project Structure

```
frontend/
├── app/                  # Next.js App Router
│   ├── layout.tsx       # Root layout with providers
│   ├── page.tsx         # Dashboard page
│   ├── providers.tsx    # React Query provider
│   └── globals.css      # Lattice dark theme
├── components/          # React components
│   ├── MapView.tsx      # Mapbox GL JS map with hotspots
│   ├── DetectionsRail.tsx   # Hotspot list sidebar
│   └── TimelinePlayer.tsx   # Month scrubber
├── lib/                 # Utilities
│   ├── api.ts          # Backend API client
│   └── utils.ts        # Helper functions
└── types/              # TypeScript types
    └── index.ts        # Shared type definitions
```

## API Integration

The frontend connects to the backend API at `http://localhost:8001`:

- `GET /api/aoi` - SF Bay metadata
- `GET /api/detect/hotspots?min_score=0.5&limit=100` - Hotspot list
- `GET /api/detect/tile/{tile_id}` - Tile detail (not yet implemented in UI)
- `GET /api/tiles/{tile_id}/assets?month=YYYY-MM` - Imagery URLs (not yet implemented)

## UI Components

### MapView
- Mapbox GL JS dark basemap
- GeoJSON layer for hotspot markers
- Color-coded by score (red > 0.7, amber > 0.5, cyan < 0.5)
- Click to select hotspot
- Fly-to animation on selection

### DetectionsRail
- Collapsible 400px sidebar
- Sorted by score (highest first)
- Cards show: Tile ID, Score, Confidence, Change Type
- Empty state with helpful message
- Selected hotspot highlighted

### TimelinePlayer
- Bottom bar with month scrubber
- Play/Pause button
- Playback speed selector (1x, 2x, 4x)
- Month markers on slider
- Auto-advance when playing

## Design System

### Colors
- Background: `#0a0a0a` (pitch black)
- Panel: `#1a1a1a` (dark gray)
- Border: `#262626` (subtle)
- Text Primary: `#ffffff`
- Text Secondary: `#a3a3a3`
- Accent: `#22d3ee` (cyan-500)
- Alert Warning: `#fbbf24` (amber-400)
- Alert Danger: `#ef4444` (red-500)

### Typography
- Font: Inter (system default)
- High contrast for readability
- Monospace for tile IDs

### Badges
- High Confidence: Green
- Medium Confidence: Yellow
- Low Confidence: Gray
- Structural: Blue
- Activity: Orange

## Scripts

```bash
npm run dev        # Start development server (port 3000)
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
```

## Known Issues

1. **Mapbox Token**: If not configured, map shows placeholder message
2. **Tile Details**: Detail view not yet implemented (M3)
3. **Filters**: Filter controls not yet implemented (M3)
4. **Export**: GeoJSON export not yet implemented (M3)

## Next Steps (M3)

- [ ] Tile detail modal with timeline chart
- [ ] Filter controls (score, date range, alert type)
- [ ] Search functionality
- [ ] GeoJSON export
- [ ] Baseline comparison visualization
- [ ] Mobile responsive improvements

## Dependencies

**Core:**
- `next@14.2.0` - React framework
- `react@18.3.0` - UI library
- `typescript@5` - Type safety

**Data Fetching:**
- `@tanstack/react-query@5.28.0` - Server state management

**Visualization:**
- `mapbox-gl@3.1.0` - Interactive maps
- `recharts@2.12.0` - Charts (for M3)

**UI:**
- `lucide-react@0.344.0` - Icons
- `date-fns@3.3.0` - Date formatting
- `tailwindcss@3.4.0` - Styling

## Development Notes

- Map requires `NEXT_PUBLIC_MAPBOX_TOKEN` for production tiles
- API calls use React Query for caching and error handling
- All components are client-side (`'use client'`) for interactivity
- TypeScript strict mode enabled
- ESLint with Next.js rules

## License

Part of the SIAD project - Infrastructure Acceleration Detector
