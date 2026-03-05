# Agent 4: Frontend - Initialization Brief

**Role:** React Implementation & Visualization
**Phase:** MVP (Weeks 1-3)
**Status:** 🟢 Ready to Start

---

## Your Mission

Implement the SIAD frontend in React + TypeScript, bringing Agent 3's designs to life with interactive visualizations.

---

## What's Already Done ✅

1. **API Spec** (`docs/API_SPEC.md`) - Backend contract
2. **Existing Frontend Scaffold** (`siad-command-center/frontend/`)
   - React 18.3 + TypeScript
   - Vite build setup
   - Basic components (Gallery, HexMap, Timeline)
   - Three.js integration

3. **Design System** - Agent 3 will provide (Week 1)

---

## Your Week 1 Tasks

### Task 1: Project Setup & Dependencies
**Location:** `siad-command-center/frontend/`

**Install new dependencies:**
```bash
cd siad-command-center/frontend
npm install --save \
  @tanstack/react-query \
  zustand \
  plotly.js-dist-min \
  react-plotly.js \
  recharts \
  axios \
  date-fns

npm install --save-dev \
  @types/plotly.js \
  vitest \
  @testing-library/react
```

**Key libraries:**
- **React Query:** Server state management & caching
- **Zustand:** Local state (filters, UI state)
- **Plotly.js:** Token heatmaps
- **Recharts:** Timeline charts
- **Axios:** API calls
- **date-fns:** Date formatting

**Deliverable:** Updated `package.json` with dependencies

---

### Task 2: API Service Layer
**File:** `src/services/api.ts`

Create typed API client:

```typescript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
interface ResidualRequest {
  tile_id: string;
  context_month: string;
  rollout_horizon: number;
  normalize_weather: boolean;
}

interface ResidualResponse {
  tile_id: string;
  residuals: Record<string, number[]>;  // month -> 256 floats
  tile_scores: number[];
  metadata: any;
}

interface Hotspot {
  id: string;
  rank: number;
  tile_id: string;
  region: string;
  score: number;
  onset: string;
  duration: number;
  alert_type: 'structural_acceleration' | 'activity_surge';
  confidence: 'high' | 'medium' | 'low';
  coordinates: { lat: number; lon: number };
}

// API functions
export const detectAPI = {
  computeResiduals: (req: ResidualRequest) =>
    api.post<ResidualResponse>('/api/detect/residuals', req),

  getHotspots: (params: {
    start_date?: string;
    end_date?: string;
    min_score?: number;
    alert_type?: string;
    limit?: number;
  }) => api.get<{ hotspots: Hotspot[]; total: number }>('/api/hotspots', { params }),

  getHeatmap: (tile_id: string, month: string, normalize_weather: boolean = true) =>
    api.get(`/api/tiles/${tile_id}/heatmap`, {
      params: { month, normalize_weather }
    }),

  getBaselines: (tile_id: string, month: string) =>
    api.get(`/api/baselines/${tile_id}`, { params: { month } }),
};
```

**Deliverable:** Complete API service layer with types

---

### Task 3: Design System Tokens
**File:** `src/styles/tokens.ts`

Implement design tokens from Agent 3:

```typescript
export const colors = {
  bg: {
    base: '#0A0E14',
    elevated: '#151922',
    overlay: '#1F242F',
  },
  text: {
    primary: '#E6E8EB',
    secondary: '#9BA1A6',
    disabled: '#4A5056',
  },
  data: {
    value: '#00D9FF',
    label: '#7A8288',
  },
  alert: {
    high: '#FF4757',
    medium: '#FFA502',
    low: '#FFD93D',
  },
  success: '#6BCF7F',
};

export const typography = {
  heading: {
    fontFamily: 'Inter, sans-serif',
    sizes: { h1: '32px', h2: '24px', h3: '18px', h4: '14px' },
    weight: 600,
  },
  body: {
    fontFamily: 'Inter, sans-serif',
    size: '14px',
    weight: 400,
  },
  mono: {
    fontFamily: '"JetBrains Mono", monospace',
    size: '13px',
  },
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
};
```

**Deliverable:** Design tokens + CSS variables

---

## Your Week 2 Tasks

### Task 4: Token Heatmap Component
**File:** `src/components/TokenHeatmap.tsx`

Implement 16×16 residual grid:

```typescript
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';

const Plot = createPlotlyComponent(Plotly);

interface TokenHeatmapProps {
  residuals: number[];  // 256 floats
  onTokenClick?: (tokenIndex: number) => void;
}

export function TokenHeatmap({ residuals, onTokenClick }: TokenHeatmapProps) {
  // Reshape 256 -> 16x16
  const grid = [];
  for (let i = 0; i < 16; i++) {
    grid.push(residuals.slice(i * 16, (i + 1) * 16));
  }

  const data = [{
    z: grid,
    type: 'heatmap',
    colorscale: 'Viridis',
    showscale: true,
  }];

  const layout = {
    width: 400,
    height: 400,
    xaxis: { title: 'Token X' },
    yaxis: { title: 'Token Y' },
    plot_bgcolor: colors.bg.base,
    paper_bgcolor: colors.bg.elevated,
  };

  return (
    <div className="token-heatmap">
      <Plot
        data={data}
        layout={layout}
        onClick={(event) => {
          const point = event.points[0];
          const tokenIndex = point.y * 16 + point.x;
          onTokenClick?.(tokenIndex);
        }}
      />
    </div>
  );
}
```

**Deliverable:** Interactive token heatmap component

---

### Task 5: Hotspot List Component
**File:** `src/components/HotspotList.tsx`

Render ranked hotspots:

```typescript
interface HotspotListProps {
  hotspots: Hotspot[];
  onSelect: (hotspot: Hotspot) => void;
  selectedId?: string;
}

export function HotspotList({ hotspots, onSelect, selectedId }: HotspotListProps) {
  return (
    <div className="hotspot-list">
      {hotspots.map((hotspot) => (
        <HotspotCard
          key={hotspot.id}
          hotspot={hotspot}
          isSelected={hotspot.id === selectedId}
          onClick={() => onSelect(hotspot)}
        />
      ))}
    </div>
  );
}

function HotspotCard({ hotspot, isSelected, onClick }: {...}) {
  return (
    <div
      className={`hotspot-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="header">
        <span className="rank">#{hotspot.rank}</span>
        <span className="region">{hotspot.region}</span>
        <span className={`confidence ${hotspot.confidence}`}>
          {hotspot.confidence.toUpperCase()}
        </span>
      </div>
      <div className="metrics">
        <span>Score: {hotspot.score.toFixed(2)}</span>
        <span>Onset: {hotspot.onset}</span>
      </div>
      <div className="metadata">
        <span>Duration: {hotspot.duration}mo</span>
        <span>Type: {hotspot.alert_type}</span>
      </div>
    </div>
  );
}
```

**Deliverable:** Hotspot list with card components

---

### Task 6: Timeline Chart Component
**File:** `src/components/TimelineChart.tsx`

Visualize score over time:

```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine } from 'recharts';

interface TimelineChartProps {
  data: Array<{ month: string; score: number }>;
  threshold?: number;
}

export function TimelineChart({ data, threshold = 0.5 }: TimelineChartProps) {
  return (
    <div className="timeline-chart">
      <LineChart width={600} height={300} data={data}>
        <XAxis dataKey="month" stroke={colors.text.secondary} />
        <YAxis domain={[0, 1]} stroke={colors.text.secondary} />
        <Tooltip
          contentStyle={{
            backgroundColor: colors.bg.overlay,
            border: `1px solid ${colors.text.disabled}`,
          }}
        />
        <ReferenceLine
          y={threshold}
          stroke={colors.alert.medium}
          strokeDasharray="3 3"
          label="Threshold"
        />
        <Line
          type="monotone"
          dataKey="score"
          stroke={colors.data.value}
          strokeWidth={2}
          dot={{ fill: colors.data.value, r: 4 }}
        />
      </LineChart>
    </div>
  );
}
```

**Deliverable:** Timeline chart component

---

### Task 7: Environmental Controls
**File:** `src/components/EnvironmentalControls.tsx`

Implement weather sliders:

```typescript
import { useState } from 'react';

interface EnvironmentalControlsProps {
  onUpdate: (rain: number, temp: number, normalize: boolean) => void;
}

export function EnvironmentalControls({ onUpdate }: EnvironmentalControlsProps) {
  const [rain, setRain] = useState(0);  // -3 to +3 σ
  const [temp, setTemp] = useState(0);  // -2 to +2 °C
  const [normalize, setNormalize] = useState(true);

  const handleChange = (newRain: number, newTemp: number, newNormalize: boolean) => {
    setRain(newRain);
    setTemp(newTemp);
    setNormalize(newNormalize);
    onUpdate(newRain, newTemp, newNormalize);
  };

  return (
    <div className="environmental-controls">
      <h3>Environmental Conditions</h3>

      <div className="control">
        <label>Rain Anomaly: {rain.toFixed(1)}σ</label>
        <input
          type="range"
          min={-3}
          max={3}
          step={0.1}
          value={rain}
          onChange={(e) => handleChange(parseFloat(e.target.value), temp, normalize)}
          disabled={normalize}
        />
      </div>

      <div className="control">
        <label>Temp Anomaly: {temp.toFixed(1)}°C</label>
        <input
          type="range"
          min={-2}
          max={2}
          step={0.1}
          value={temp}
          onChange={(e) => handleChange(rain, parseFloat(e.target.value), normalize)}
          disabled={normalize}
        />
      </div>

      <div className="control">
        <label>
          <input
            type="checkbox"
            checked={normalize}
            onChange={(e) => handleChange(rain, temp, e.target.checked)}
          />
          Normalize to Neutral Weather
        </label>
      </div>

      {normalize && (
        <div className="info">
          ℹ️ Weather normalized (rain=0, temp=0) to isolate structural changes
        </div>
      )}
    </div>
  );
}
```

**Deliverable:** Environmental controls component

---

## Your Week 3 Tasks

### Task 8: Dashboard Page
**File:** `src/pages/Dashboard.tsx`

Assemble dashboard:

```typescript
import { useQuery } from '@tanstack/react-query';
import { HotspotList } from '../components/HotspotList';
import { HexMap } from '../components/HexMap';

export function Dashboard() {
  const { data: hotspots, isLoading } = useQuery({
    queryKey: ['hotspots'],
    queryFn: () => detectAPI.getHotspots({ limit: 10, min_score: 0.5 }),
  });

  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);

  if (isLoading) return <LoadingState />;

  return (
    <div className="dashboard">
      <header>
        <h1>SIAD Detection System</h1>
        <Filters />
      </header>

      <main className="grid">
        <aside className="hotspot-list-panel">
          <HotspotList
            hotspots={hotspots?.hotspots || []}
            onSelect={setSelectedHotspot}
            selectedId={selectedHotspot?.id}
          />
        </aside>

        <section className="map-panel">
          <HexMap hotspots={hotspots?.hotspots || []} />
        </section>
      </main>
    </div>
  );
}
```

**Deliverable:** Functional dashboard page

---

### Task 9: Hotspot Detail Page
**File:** `src/pages/HotspotDetail.tsx`

Implement detail view:

```typescript
export function HotspotDetail({ hotspotId }: { hotspotId: string }) {
  const { data: timeline } = useQuery({
    queryKey: ['timeline', hotspotId],
    queryFn: () => api.get(`/api/hotspots/${hotspotId}/timeline`),
  });

  const { data: heatmap } = useQuery({
    queryKey: ['heatmap', hotspotId],
    queryFn: () => detectAPI.getHeatmap(hotspotId, selectedMonth),
  });

  return (
    <div className="hotspot-detail">
      <header>
        <BackButton />
        <h1>Hotspot #{hotspot.rank}: {hotspot.region}</h1>
      </header>

      <div className="grid">
        <section className="timeline">
          <TimelineChart data={timeline} />
        </section>

        <section className="heatmap">
          <TokenHeatmap residuals={heatmap.values.flat()} />
        </section>

        <section className="imagery">
          <ImageryViewer tileId={hotspot.tile_id} month={selectedMonth} />
        </section>

        <section className="controls">
          <EnvironmentalControls onUpdate={handleEnvironmentChange} />
        </section>

        <section className="baselines">
          <BaselineComparison tileId={hotspot.tile_id} month={selectedMonth} />
        </section>
      </div>

      <footer className="explanation">
        {generateExplanation(hotspot)}
      </footer>
    </div>
  );
}
```

**Deliverable:** Hotspot detail page with all panels

---

### Task 10: State Management
**File:** `src/stores/appStore.ts`

Create Zustand store:

```typescript
import create from 'zustand';

interface AppState {
  filters: {
    startDate: string;
    endDate: string;
    minScore: number;
    alertType: string;
  };
  setFilters: (filters: Partial<AppState['filters']>) => void;
  selectedHotspot: string | null;
  setSelectedHotspot: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  filters: {
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    minScore: 0.5,
    alertType: 'all',
  },
  setFilters: (newFilters) =>
    set((state) => ({ filters: { ...state.filters, ...newFilters } })),
  selectedHotspot: null,
  setSelectedHotspot: (id) => set({ selectedHotspot: id }),
}));
```

**Deliverable:** State management with Zustand

---

## Key Files Structure

```
siad-command-center/frontend/src/
├── components/
│   ├── TokenHeatmap.tsx
│   ├── HotspotList.tsx
│   ├── TimelineChart.tsx
│   ├── EnvironmentalControls.tsx
│   ├── BaselineComparison.tsx
│   ├── ImageryViewer.tsx
│   └── LoadingState.tsx
├── pages/
│   ├── Dashboard.tsx
│   └── HotspotDetail.tsx
├── services/
│   └── api.ts
├── stores/
│   └── appStore.ts
├── styles/
│   ├── tokens.ts
│   ├── global.css
│   └── components/
└── utils/
    └── formatters.ts
```

---

## Testing

Create component tests:

```typescript
// tests/components/TokenHeatmap.test.tsx
import { render, screen } from '@testing-library/react';
import { TokenHeatmap } from '../components/TokenHeatmap';

test('renders 16x16 heatmap', () => {
  const residuals = Array(256).fill(0.5);
  render(<TokenHeatmap residuals={residuals} />);
  expect(screen.getByRole('figure')).toBeInTheDocument();
});
```

---

## Dependencies

**You depend on:**
- Agent 2 (API) for working endpoints
- Agent 3 (Design) for visual specifications
- Agent 5 (UX) for interaction patterns

**Others depend on you:**
- Agent 5 (UX) needs working frontend for testing
- Agent 6 (Copy) needs to see UI for context

---

## Success Criteria (Week 3)

- [ ] All 7 core components implemented
- [ ] Dashboard page functional
- [ ] Hotspot detail page functional
- [ ] API integration working
- [ ] Design system tokens applied
- [ ] Basic tests passing
- [ ] Responsive layout (desktop)

---

## Communication

**Sync with:**
- **Agent 2 (API):** Daily on API integration
- **Agent 3 (Design):** Daily on implementation questions
- **Agent 5 (UX):** Mid-week on interactions
- **All agents:** End of Week 2 for demo

---

**Ready to code? Start with Task 1: Project Setup!**

⚛️ Build it!
