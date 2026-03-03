# SIAD Command Center - Frontend

Modern React + TypeScript + Vite application for the Satellite Intelligence & Action Dashboard tactical demo.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Gallery/          # Satellite imagery gallery
│   │   ├── HexMap/           # 3D hexagonal map visualization
│   │   ├── Timeline/         # Temporal scrubber component
│   │   ├── Metrics/          # Model metrics display
│   │   └── Layout/           # Layout components (Header, Sidebar, Footer)
│   ├── lib/
│   │   ├── api.ts            # Type-safe Axios API client
│   │   └── types.ts          # TypeScript interfaces
│   ├── styles/
│   │   ├── tokens.json       # Design system tokens
│   │   ├── tactical.css      # Tactical UI system styles
│   │   └── global.css        # Global styles
│   ├── App.tsx               # Root component
│   └── main.tsx              # Entry point
├── public/                    # Static assets
├── index.html                 # HTML entry point
├── package.json               # Dependencies
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
└── README.md                 # This file
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Create .env.local from .env.example
cp .env.example .env.local
```

### Development

```bash
# Start development server
npm run dev

# The app will be available at http://localhost:5173
```

### Building

```bash
# Build for production
npm run build

# Preview production build locally
npm run preview
```

## Technologies

- **React** 18.3 - UI framework
- **TypeScript** 5.3 - Type safety
- **Vite** 5.0 - Build tool
- **Three.js** 0.160 - 3D graphics
- **React Three Fiber** 8.15 - React renderer for Three.js
- **Axios** 1.6 - HTTP client
- **Tailwind-inspired CSS** - Design system

## API Integration

The frontend connects to a FastAPI backend at `http://localhost:8000`. Key endpoints:

- `GET /gallery` - Fetch gallery entries
- `GET /tiles/{tileId}` - Fetch tile data
- `GET /predictions/{tileId}` - Get predictions
- `POST /predictions/{tileId}/predict` - Run inference
- `GET /climate/actions` - Get climate actions
- `GET /health` - API health check

See `src/lib/api.ts` for complete API client implementation.

## Design System

The project uses a military/tactical aesthetic with:

- **Colors**: Dark backgrounds (#0a0a0a, #1a1a1a) with cyan (#14b8a6) and amber (#f59e0b) accents
- **Typography**: Rajdhani (display), Inter (UI), JetBrains Mono (code)
- **Components**: Hex tiles, timeline scrubber, climate sliders, metric badges
- **Effects**: Glow shadows, scan line animations, grid overlays

See `src/styles/tokens.json` for complete token definitions.

## Component Development

### Creating a New Component

```typescript
// src/components/MyComponent/index.tsx
import { MyComponentProps } from './types'

export function MyComponent({ prop1, prop2 }: MyComponentProps) {
  return (
    <div className="my-component">
      {/* Component content */}
    </div>
  )
}

export default MyComponent
```

### Using the API Client

```typescript
import { getGallery, getPrediction } from '@/lib/api'

async function loadData() {
  try {
    const gallery = await getGallery({ page: 1 })
    const prediction = await getPrediction(tileId)
  } catch (error) {
    console.error('API Error:', error)
  }
}
```

### Using Design Tokens

```tsx
// Access tokens from tokens.json
import tokens from '@/styles/tokens.json'

const hexTileColor = tokens.colors.accent.cyan['500']
```

## Environment Variables

Create `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_ENV=development
VITE_DEBUG=true
VITE_ENABLE_3D_MAP=true
```

## Type Safety

The project uses strict TypeScript with comprehensive type definitions:

- `Tile` - Satellite tile data
- `Prediction` - Model prediction output
- `GalleryEntry` - Gallery item
- `ClimateAction` - Climate action tracking
- `ModelMetrics` - ML model performance

See `src/lib/types.ts` for all type definitions.

## Styling

- **Global styles**: `src/styles/global.css`
- **Component styles**: `src/styles/tactical.css`
- **Design tokens**: `src/styles/tokens.json`

Uses utility-first approach with predefined classes from `tactical.css`:
- `.hex-tile` - Hexagonal tile component
- `.timeline-scrubber` - Timeline control
- `.metric-badge` - Metric display badge
- `.confidence-indicator` - Confidence visualization
- `.tactical-border` - Styled border with glow
- `.tactical-grid` - Grid overlay effect

## Performance Optimization

- Lazy component loading with React.lazy
- Vite chunk splitting for vendor libraries
- Image optimization for satellite imagery
- WebGL rendering via Three.js

## Accessibility

- Semantic HTML structure
- ARIA labels for interactive elements
- Focus states and keyboard navigation
- High contrast support
- Reduced motion preferences respected

## Contributing

When adding new features:

1. Create type definitions in `src/lib/types.ts`
2. Add API functions to `src/lib/api.ts`
3. Create component in `src/components/`
4. Use design tokens from `tokens.json`
5. Follow existing code style

## Troubleshooting

### API Connection Issues

If you see "Backend Disconnected":

1. Ensure FastAPI server is running on `http://localhost:8000`
2. Check `VITE_API_URL` in `.env.local`
3. Verify CORS configuration in backend

### Build Errors

```bash
# Clear dependencies and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Development Server Issues

```bash
# Check if port 5173 is available
# Or specify different port
npm run dev -- --port 3000
```

## License

Part of the SIAD (Satellite Intelligence & Action Dashboard) project.
