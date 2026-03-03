# SIAD Command Center Frontend - Quick Start Guide

Get the React + TypeScript + Vite frontend running in 5 minutes.

## 1. Install Dependencies

```bash
cd frontend
npm install
```

This installs:
- React 18.3 & React DOM
- TypeScript 5.3
- Vite 5.0 (build tool)
- Three.js, React Three Fiber (3D graphics)
- Axios (HTTP client)
- All development tools and type definitions

**Expected time**: 1-2 minutes

## 2. Start Development Server

```bash
npm run dev
```

Output:
```
  VITE v5.0.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

Open http://localhost:5173 in your browser.

## 3. Verify API Connection

The app checks FastAPI backend connectivity on startup:
- If you see "Backend Connected" - everything is working
- If you see "Backend Disconnected" - start the backend server at `http://localhost:8000`

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx              # Root component with API health check
│   ├── main.tsx             # Entry point
│   ├── components/          # React components
│   │   ├── Gallery/         # Satellite imagery gallery
│   │   ├── HexMap/          # 3D hexagonal map
│   │   ├── Timeline/        # Temporal scrubber
│   │   ├── Metrics/         # Model metrics display
│   │   └── Layout/          # Header, Sidebar, Footer
│   ├── lib/
│   │   ├── api.ts           # Type-safe API client
│   │   └── types.ts         # TypeScript interfaces
│   └── styles/
│       ├── global.css       # Global styles
│       ├── tactical.css     # Tactical UI components
│       └── tokens.json      # Design system tokens
├── index.html               # HTML entry point
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies & scripts
```

## Available Commands

```bash
# Development server (hot reload enabled)
npm run dev

# Type check & build for production
npm run build

# Preview production build
npm run preview
```

## Key Files to Know

### 1. `src/lib/api.ts` - API Client
Type-safe functions for calling the FastAPI backend:
```typescript
import { getGallery, getTileData, predict } from '@/lib/api'

// Fetch gallery
const gallery = await getGallery({ page: 1 })

// Fetch tile
const tile = await getTileData('tile-123')

// Run prediction
const prediction = await predict('tile-123')
```

### 2. `src/lib/types.ts` - Type Definitions
Core data structures:
- `Tile` - Satellite tile data
- `Prediction` - ML model outputs
- `GalleryEntry` - Gallery item
- `ClimateAction` - Climate actions
- `ModelMetrics` - Performance metrics

### 3. `src/styles/tokens.json` - Design System
Color palette, typography, spacing, component styles:
```json
{
  "colors": {
    "accent": { "cyan": "#14b8a6", "amber": "#f59e0b" },
    "text": { "primary": "#f5f5f5" }
  },
  "typography": {
    "fonts": {
      "tactical": "'Rajdhani', sans-serif"
    }
  }
}
```

### 4. `src/styles/tactical.css` - Component Styles
Pre-built CSS classes for tactical UI:
- `.hex-tile` - Hexagonal tiles
- `.timeline-scrubber` - Timeline control
- `.metric-badge` - Metric displays
- `.tactical-grid` - Grid overlay
- `.tactical-border` - Styled borders

## Configuration

### Environment Variables

Create `.env.local` from `.env.example`:
```bash
cp .env.example .env.local
```

Key variables:
```env
VITE_API_URL=http://localhost:8000
VITE_ENV=development
VITE_DEBUG=true
```

### Vite Config

`vite.config.ts` includes:
- React plugin for JSX/TSX
- API proxy configuration (paths `/api/*` → backend)
- Chunk splitting for vendor libraries
- Source map generation for debugging

### TypeScript Config

`tsconfig.json` enables:
- Strict type checking
- Path alias support (`@/*` → `src/*`)
- JSX/TSX support
- Strict null checks and more

## Component Development

### Creating a New Component

```typescript
// src/components/MyComponent/index.tsx
import { ReactNode } from 'react'

interface MyComponentProps {
  title: string
  children?: ReactNode
}

export function MyComponent({ title, children }: MyComponentProps) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="font-tactical text-xl font-bold">{title}</h2>
      {children}
    </div>
  )
}

export default MyComponent
```

### Using API Client

```typescript
import { getGallery, handleApiError } from '@/lib/api'

export function GalleryList() {
  const [entries, setEntries] = useState<GalleryEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadGallery = async () => {
      try {
        const data = await getGallery({ page: 1 })
        setEntries(data.items)
      } catch (error) {
        console.error(handleApiError(error))
      } finally {
        setLoading(false)
      }
    }

    loadGallery()
  }, [])

  return (
    <div>
      {entries.map(entry => (
        <div key={entry.id}>{entry.title}</div>
      ))}
    </div>
  )
}
```

## Styling

### Using Utility Classes

```tsx
<div className="flex flex-col gap-4 items-center justify-center p-6">
  <h1 className="font-tactical text-2xl font-bold text-cyan">Title</h1>
  <p className="text-secondary">Subtitle</p>
</div>
```

### Available Utilities

From `tactical.css`:
- Layout: `.flex`, `.grid`, `.items-center`, `.justify-between`
- Text: `.text-primary`, `.text-secondary`, `.font-tactical`, `.font-mono`
- Spacing: `.px-4`, `.py-2`, `.gap-3`
- Colors: `.text-cyan`, `.text-amber`, `.bg-dark`
- Animations: `.animate-pulse-cyan`, `.animate-fade-in`

## API Integration

### Backend Expected at: `http://localhost:8000`

Key endpoints implemented in `src/lib/api.ts`:

```
GET  /gallery                     → getGallery()
GET  /gallery/stats              → getGalleryStats()
GET  /tiles/{tileId}             → getTileData()
GET  /tiles/bounds               → getTilesByBoundingBox()
GET  /predictions/{tileId}       → getPrediction()
POST /predictions/{tileId}/predict → predict()
GET  /climate/actions            → getClimateActions()
GET  /health                     → checkApiHealth()
```

## Troubleshooting

### Port Already in Use

```bash
npm run dev -- --port 3000
```

### TypeScript Errors

Clear cache and rebuild:
```bash
rm -rf node_modules .next
npm install
npm run build
```

### API Connection Errors

1. Check FastAPI is running: `http://localhost:8000/health`
2. Verify `VITE_API_URL` in `.env.local`
3. Check browser console for CORS errors
4. Check backend logs for issues

### Hot Reload Not Working

```bash
# Restart dev server
npm run dev
```

## Next Steps

1. **Start Frontend**: `npm run dev`
2. **Check API Connection**: Look for "Backend Connected" indicator
3. **Browse Components**: Check `src/components/` for example implementations
4. **Review Types**: See `src/lib/types.ts` for data structures
5. **Implement Features**: Use `src/components/Gallery` as a template

## File Size Overview

After `npm install`:
- `node_modules`: ~500MB
- `src`: ~50KB
- Project ready for development

After `npm run build`:
- `dist`: ~300KB (minified, gzipped ~100KB)
- Ready for production deployment

## Performance Tips

- Vite automatically optimizes dependencies
- React chunk is split from vendor libraries
- Three.js used for GPU-accelerated rendering
- Images lazy-loaded by default
- CSS utility classes tree-shaken during build

## IDE Setup (VS Code)

Recommended extensions:
- ES7+ React/Redux/React-Native snippets
- TypeScript Vue Plugin
- Prettier - Code formatter
- Vite

Settings (`.vscode/settings.json`):
```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Learning Resources

- React: https://react.dev
- TypeScript: https://www.typescriptlang.org/docs
- Vite: https://vitejs.dev/guide
- Three.js: https://threejs.org/docs
- Axios: https://axios-http.com/docs/intro

## Support

For issues or questions, check:
1. `README.md` - Comprehensive documentation
2. `src/lib/api.ts` - API client examples
3. `src/components/` - Component examples
4. Backend logs for API errors

---

**Happy coding! The dashboard is ready for feature development.** 🚀
