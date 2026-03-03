# SIAD Command Center — Component Specifications

**Document Version:** 1.0
**Status:** Ready for Implementation
**Last Updated:** 2026-03-03
**Audience:** Frontend Engineers, QA, Component Library Maintainers

---

## 1. Overview

This document specifies all React components needed to implement the SIAD Command Center tactical UI. Each component includes:
- TypeScript props interface
- State management requirements
- Event handlers and callbacks
- Visual specifications (colors, spacing, typography)
- Responsive behavior
- Accessibility notes

**Design tokens** and **copy** are defined in `tokens.json` and `copy-guide.md` respectively. All styling MUST reference these files.

---

## 2. Component Library

### 2.1 Layout Components

#### AppShell
Top-level wrapper for entire application. Manages layout grid and dark theme context.

**Props:**
```typescript
interface AppShellProps {
  children: React.ReactNode
  theme?: 'dark' | 'light' // default: 'dark'
  showHeader?: boolean // default: true
  showSidebar?: boolean // default: false (planned for future)
}
```

**State:**
- `currentView`: 'landing' | 'gallery' | 'tile-inspector' | 'hex-map'
- `selectedTile`: string | null (tile_id)
- `isLoading`: boolean

**Features:**
- Applies dark theme background (`#0a0a0a`) globally
- Sets up 12-column grid with 1.5rem gutter (from tokens.json)
- Renders responsive layout based on breakpoints
- Manages z-index stacking context

**Responsive:**
- Desktop (1400px+): Full layout, all panels visible
- Tablet (768–1024px): 2-column layout, stack vertical on small screens
- Mobile (<768px): Single column, simplified views

---

#### Header
Application title and status bar.

**Props:**
```typescript
interface HeaderProps {
  title?: string // default: "SIAD COMMAND CENTER"
  statusBadge?: {
    label: string // "MODEL READY" | "INFERENCE RUNNING" | etc.
    variant: 'success' | 'warning' | 'error' | 'info'
    icon?: React.ReactNode
  }
  onNavigate?: (view: string) => void
  breadcrumbs?: Array<{ label: string; onClick: () => void }>
}
```

**Styling:**
- Background: `#0a0a0a`
- Border bottom: `1px solid #262626`
- Title font: Rajdhani Bold, 2.5rem, `#14b8a6` with glow
- Padding: 1.5rem (top) × 1.5rem (sides)
- Height: 80px
- Status badge positioned right, uses tokens.json badge variants

**Features:**
- Cyan glow effect on title
- Breadcrumb navigation
- Status indicator with badge
- Fixed position (z-index: 1020)

---

#### Sidebar
Planned for future; reserved space.

**Props:**
```typescript
interface SidebarProps {
  isOpen: boolean
  onClose?: () => void
  items?: Array<{ label: string; icon: React.ReactNode; onClick: () => void }>
}
```

**Styling:**
- Width: 280px
- Background: `rgba(26, 26, 26, 0.95)`
- Border-right: `1px solid #262626`

---

#### Panel
Reusable container for sections (e.g., climate controls, metadata).

**Props:**
```typescript
interface PanelProps {
  title?: string
  children: React.ReactNode
  variant?: 'default' | 'elevated' | 'overlay' // default: 'default'
  padding?: 'sm' | 'md' | 'lg' // default: 'md' (1.5rem)
  border?: boolean // default: true
  collapsible?: boolean
  onCollapse?: (isCollapsed: boolean) => void
}
```

**Styling (from tokens.json):**
- Background: `rgba(26, 26, 26, 0.95)`
- Border: `1px solid #262626`
- Border-radius: `0.5rem`
- Backdrop filter: `blur(8px)`
- Shadow: `0 4px 6px -1px rgba(0, 0, 0, 0.6)`
- Padding: 1.5rem (md variant)
- Transition: `200ms cubic-bezier(0.4, 0, 0.2, 1)`

**Features:**
- Optional header with title
- Collapsible sections
- Multiple style variants
- Smooth transitions

---

### 2.2 Gallery Components

#### TileGrid
3-column grid layout for gallery cards (responsive to 2 columns on tablet, 1 on mobile).

**Props:**
```typescript
interface TileGridProps {
  tiles: TileData[]
  onTileClick?: (tileId: string) => void
  isLoading?: boolean
  columns?: 3 | 2 | 1 // default: 3
  gap?: 'sm' | 'md' | 'lg' // default: 'md'
}

interface TileData {
  id: string // tile_x001_y003
  imageUrl: string // prediction thumbnail
  groundTruthUrl?: string
  score: number // 0.0–1.0
  rank?: number
  confidence?: number // 0–100
  confidenceTier?: 'high' | 'medium' | 'low'
  attribution?: string // "SAR-dominant", "Optical-only"
  month?: string // "MAY"
}
```

**Styling:**
- Grid: 3 columns, 1.5rem gap
- Container max-width: 1400px
- Margin: auto (centered)

**Responsive:**
- Tablet (768px): 2 columns
- Mobile (<768px): 1 column, full width with padding

---

#### TileCard
Individual gallery card with hover expansion and before/after swipe.

**Props:**
```typescript
interface TileCardProps {
  tile: TileData
  isHovered?: boolean
  isSelected?: boolean
  onClick?: () => void
  onHoverChange?: (isHovered: boolean) => void
  showComparison?: boolean // show swipe toggle
}
```

**Styling:**
- Width: Fill parent grid cell
- Aspect ratio: 1:1 (square)
- Background: `#1a1a1a`
- Border: `1px solid #262626`
- Border-radius: `0.25rem`
- Transition: all `200ms` cubic-bezier
- Hover: border becomes `#14b8a6`, shadow glow cyan

**States:**
- Default: static thumbnail
- Hover: card expands, shows before/after swipe, metadata visible
- Selected: amber glow (`#f59e0b`), amber border

**Features:**
- Swipeable before/after comparison on hover
- Rank badge (top-left)
- Score badge (bottom-left)
- Confidence indicator
- [View Full Tile] button (appears on hover)
- Smooth hover animation (scale 1.02, shadow expansion)

---

#### FilterTabs
Horizontal tab bar for filtering gallery by category, confidence tier, month.

**Props:**
```typescript
interface FilterTabsProps {
  tabs: Array<{
    id: string
    label: string
    count?: number
    icon?: React.ReactNode
  }>
  activeTab?: string
  onTabChange?: (tabId: string) => void
  variant?: 'category' | 'confidence' | 'date' // styling variant
}
```

**Styling:**
- Background: `#0a0a0a`
- Border-bottom: `1px solid #262626`
- Padding: 1rem (horizontal)
- Height: 48px

**Tab Styling:**
- Font: JetBrains Mono, 0.875rem, uppercase
- Inactive: `#737373` text, transparent background
- Active: `#a5f3fc` text, `rgba(20,184,166,0.15)` background, amber glow
- Border-bottom (active): `2px solid #14b8a6`
- Margin: 0 0.75rem
- Padding: 0.75rem 1rem
- Transition: `200ms`

---

### 2.3 Map Components

#### HexMap
SVG-based 2D hex grid showing all tiles with color coding by percentile rank.

**Props:**
```typescript
interface HexMapProps {
  tiles: Array<{
    id: string
    x: number
    y: number
    percentile: number // 0–100
    isHotspot?: boolean
    isSelected?: boolean
    confidence?: number
    monthDetected?: string
  }>
  onTileSelect?: (tileId: string) => void
  onTileHover?: (tileId: string | null) => void
  onDoubleClick?: (tileId: string) => void
  canvasWidth?: number // default: 800
  canvasHeight?: number // default: 600
  showLegend?: boolean // default: true
  zoom?: number // default: 1
  panX?: number
  panY?: number
}
```

**Styling:**
- Background: `#0a0a0a`
- Border: `1px solid #262626`
- SVG rendering with hex path elements
- Color scale: green (1–25%) → yellow (26–75%) → red (76–99%)
- Hotspot tiles: red with asterisk badge (`🔴*`)

**Hex Tile Styling (from tokens.json):**
- Size: 48px
- Border: `2px solid #14b8a6`
- Background: `rgba(20,184,166,0.05)`
- Hover: `rgba(20,184,166,0.15)` background, `2px solid #22d3ee` border, glow
- Active: `rgba(245,158,11,0.2)` background, amber border + glow

**Features:**
- Smooth pan/zoom (mouse drag, scroll)
- Hover tooltip (tile_id, confidence, hotspot flag, month)
- Double-click to zoom 2x
- Legend panel (color scale explanation)
- Responsive to container size

---

#### MapLegend
Legend panel for hex map, showing color scale and hotspot indicators.

**Props:**
```typescript
interface MapLegendProps {
  percentiles: Array<{
    min: number
    max: number
    label: string
    color: string
  }>
  flaggedHotspotLabel?: string // default: "Flagged hotspot"
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
}
```

**Styling:**
- Background: `rgba(26, 26, 26, 0.95)`
- Border: `1px solid #262626`
- Border-radius: `0.5rem`
- Padding: 1rem
- Position: absolute, offset 1rem from corner
- Font: Inter, 0.75rem, `#a3a3a3`
- Z-index: 10 (above hex tiles)

**Content:**
- Colored boxes (24px × 24px each)
- Percentage ranges (1–25%, 26–75%, 76–99%)
- Label text per range
- Special entry for flagged hotspots (`🔴*`)

---

### 2.4 Inspector Components

#### TileInspector
Full-screen tile analysis view with imagery, timeline, climate controls, and metadata.

**Props:**
```typescript
interface TileInspectorProps {
  tileId: string
  imageUrl: string
  groundTruthUrl?: string
  month: number // 0–5 (MAR–AUG)
  months: string[] // ["MAR", "APR", ..., "AUG"]
  climateParams: {
    rainfall: number[] // per-month, -2σ to +2σ
    temperature: number[] // per-month, -2σ to +2σ
  }
  metadata: TileMetadata
  onMonthChange?: (month: number) => void
  onClimateChange?: (params: ClimateParams) => void
  onClose?: () => void
  onCompare?: () => void
  onExport?: () => void
  isLoading?: boolean
}

interface TileMetadata {
  id: string
  lat: number
  lon: number
  isHotspot: boolean
  confidence: number
  persistence: number // months
  attribution: string
  valLoss: number
  meanResidual: number
  trend: number // 3-month slope
  validPixels: number
  predictionConfidence: number
}
```

**Layout:**
- Left panel (60%): Imagery + timeline + modality controls
- Right panel (40%): Climate controls + metadata + residual stats
- Responsive: Stack vertically on tablet/mobile

**Styling:**
- Background: `#0a0a0a`
- Main container: 1400px max-width, centered
- Panels: separated by 1.5rem gap
- Full height: min 800px

---

#### Timeline (Scrubber)
Interactive month selector with drag handle and auto-play.

**Props:**
```typescript
interface TimelineProps {
  months: string[] // ["MAR", "APR", ..., "AUG"]
  currentMonth: number // 0–5
  onMonthChange?: (month: number) => void
  showAutoPlay?: boolean // default: true
  autoPlaySpeed?: 'slow' | 'normal' | 'fast' // default: 'normal'
  onAutoPlayToggle?: (enabled: boolean) => void
  onSpeedChange?: (speed: string) => void
}
```

**Styling (from tokens.json):**
- Height: 48px
- Background: `linear-gradient(to bottom, rgba(20,184,166,0.1), rgba(20,184,166,0.05))`
- Border: `1px solid #262626`
- Border-radius: `0.375rem`
- Padding: 0.5rem
- Thumb width: 24px, height: 32px
- Thumb background: `linear-gradient(135deg, #14b8a6, #0891b2)`
- Thumb border: `1px solid #22d3ee`
- Thumb shadow: glow-cyan

**Features:**
- Click month label to jump instantly
- Drag thumb to scrub smoothly
- Arrow keys to move ±1 month
- Auto-play loops MAR→AUG
- Speed control: Slow (1000ms), Normal (500ms), Fast (250ms)
- Month labels highlight in accent color when active
- Imagery updates with 150ms crossfade

---

#### ImageComparison
Toggle between ground truth and prediction imagery with smooth crossfade.

**Props:**
```typescript
interface ImageComparisonProps {
  predictionUrl: string
  groundTruthUrl?: string
  isComparing?: boolean // show ground truth
  onToggle?: (isComparing: boolean) => void
  width?: number | string // default: '100%'
  height?: number | string // default: 'auto'
  imageAlt?: string
}
```

**Styling:**
- Container: relative positioning
- Images: absolute, full container size
- Crossfade transition: 200ms
- Toggle label positioned top-right, monospace font

**Features:**
- Smooth CSS crossfade between images
- Label updates dynamically ("Ground Truth" / "Prediction")
- Space key toggles state
- Accessible via ARIA labels

---

### 2.5 Control Components

#### ClimateSlider
Per-month rainfall or temperature slider, range -2σ to +2σ.

**Props:**
```typescript
interface ClimateSliderProps {
  label: string // "Rainfall Anomaly (MM)" | "Temperature Deviation (°C)"
  month: string // "MAR", "APR", etc.
  value: number // -2 to +2 (sigma)
  onChange?: (value: number) => void
  min?: number // default: -2
  max?: number // default: +2
  step?: number // default: 0.1
  unit?: string // "σ" (default)
  variant?: 'rainfall' | 'temperature'
  disabled?: boolean
  showTooltip?: boolean // default: true
}
```

**Styling (from tokens.json):**
- Height: 6px (track)
- Background track: `rgba(10,10,10,0.8)`
- Border: `1px solid #262626`
- Border-radius: 3px

**Thumb Styling:**
- Width/Height: 20px
- Background: radial-gradient (amber)
- Border: `2px solid #fcd34d`
- Shadow: glow-amber

**Variant Styles:**
- Rainfall: track gradient blue → cyan
- Temperature: track gradient cyan → amber

**Features:**
- Real-time onChange callback
- Tooltip shows current value and range
- Visual feedback via glow
- Keyboard support (arrow keys)
- Disabled state (opacity 0.5)

---

#### PresetButton
Quick preset selection (Neutral, Wet, Dry, Hot, Custom).

**Props:**
```typescript
interface PresetButtonProps {
  preset: 'neutral' | 'wet' | 'dry' | 'hot' | 'custom'
  isActive?: boolean
  onClick?: () => void
  label?: string // override default
  disabled?: boolean
}
```

**Styling:**
- Font: JetBrains Mono, 0.75rem, uppercase, semibold
- Padding: 0.5rem 1rem
- Border: `1px solid transparent` (default) or `1px solid #f59e0b` (active)
- Background: transparent (default) or `rgba(245,158,11,0.15)` (active)
- Color: `#737373` (default) or `#f59e0b` (active)
- Border-radius: `0.375rem`
- Shadow: glow-amber (active)
- Transition: all `200ms`

**Features:**
- Visual indication of active preset
- Horizontal button group layout
- Tooltip explains preset behavior
- Updates all sliders simultaneously

---

#### ToggleButton
Generic toggle control (e.g., modality checkboxes, comparison mode).

**Props:**
```typescript
interface ToggleButtonProps {
  label: string
  isChecked: boolean
  onChange?: (checked: boolean) => void
  icon?: React.ReactNode
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg' // default: 'md'
  variant?: 'default' | 'inline' // default: 'default'
}
```

**Styling:**
- Container: flex row, gap 0.75rem
- Checkbox: native or custom 20×20px box
- Checkbox border: `1px solid #262626` (default), `1px solid #14b8a6` (checked)
- Background: transparent (default), `rgba(20,184,166,0.1)` (checked)
- Label: Inter, 0.875rem, `#f5f5f5`
- Transition: `200ms`

**Features:**
- Native accessibility (true checkbox input)
- Custom styling matches design tokens
- Icon + label pairing
- Keyboard support (Space to toggle)

---

### 2.6 Metric Components

#### StatCard
Compact metric display (validation loss, mean residual, etc.).

**Props:**
```typescript
interface StatCardProps {
  label: string // "MEAN RESIDUAL", "VALIDATION LOSS", etc.
  value: number | string
  unit?: string // "%", "dB", "σ", etc.
  format?: 'decimal' | 'percent' | 'scientific'
  icon?: React.ReactNode
  color?: string // uses token color
  tooltip?: string
  trend?: number // slope for arrow indicator
  size?: 'sm' | 'md' | 'lg' // default: 'md'
}
```

**Styling:**
- Background: `#1a1a1a`
- Border: `1px solid #262626`
- Border-radius: `0.375rem`
- Padding: 1rem
- Font label: JetBrains Mono, 0.75rem, uppercase, `#a3a3a3`
- Font value: JetBrains Mono, 1.25rem, bold, `#f5f5f5`
- Box shadow: `sm` (subtle)

**Features:**
- Compact layout for dense dashboards
- Optional trend indicator (↑ ↓ ↔)
- Tooltip on hover
- Responsive sizing
- Color-coded for metric type

---

#### ConfidenceIndicator
Circular badge showing confidence tier (High/Medium/Low).

**Props:**
```typescript
interface ConfidenceIndicatorProps {
  value: number // 0–100
  label?: 'H' | 'M' | 'L' | 'HIGH' | 'MEDIUM' | 'LOW' // auto-derived from value
  tooltip?: string
  size?: 'sm' | 'md' | 'lg' // default: 'md' (24px)
}
```

**Styling (from tokens.json):**
- Size: 24px (md)
- Border-radius: 50%
- Display: flex, align-items center, justify-content center

**Variants:**
- High (>80%): green border + bg, `#22c55e`, glow-green
- Medium (50–80%): amber border + bg, `#f59e0b`, glow-amber
- Low (<50%): red border + bg, `#ef4444`, glow-red

**Features:**
- Auto-derive tier from numeric value
- Optional custom label
- Tooltip with interpretation
- Glowing effect matches tier

---

#### MetricBadge
Inline badge for displaying metrics (MSE, PSNR, SSIM, Accuracy).

**Props:**
```typescript
interface MetricBadgeProps {
  metric: 'mse' | 'psnr' | 'ssim' | 'accuracy'
  value: number
  tooltip?: string
  size?: 'sm' | 'md' // default: 'md'
}
```

**Styling (from tokens.json):**
- Padding: 0.375rem 0.75rem
- Border-radius: 12px
- Font: JetBrains Mono, 0.75rem, semibold, uppercase
- Display: inline-flex, gap 0.375rem
- Border: `1px solid`

**Variants:**
- MSE: cyan bg, cyan text
- PSNR: amber bg, amber text
- SSIM: green bg, green text
- Accuracy: purple bg, purple text

**Features:**
- Color-coded by metric type
- Monospace formatting
- Optional tooltip with interpretation
- Inline layout for dense panels

---

## 3. Component Hierarchy

```
AppShell
├── Header
│   ├── Title (Rajdhani, glow)
│   ├── Breadcrumbs (navigation)
│   └── StatusBadge
│       ├── Badge (variant)
│       └── Icon
│
├── MainContent (grid container)
│   │
│   ├── [Landing View]
│   │   ├── HeroImage
│   │   ├── Headline
│   │   ├── CTAButtons (Explore Gallery, Interactive Map)
│   │   └── QuickStats
│   │       └── StatCard[]
│   │
│   ├── [Gallery View]
│   │   ├── FilterTabs (Category, Tier, Month)
│   │   ├── TileGrid
│   │   │   └── TileCard[]
│   │   │       ├── ThumbnailImage
│   │   │       ├── RankBadge
│   │   │       ├── ScoreBadge
│   │   │       ├── ConfidenceIndicator
│   │   │       ├── AttributionBadge
│   │   │       ├── ImageComparison (on hover)
│   │   │       └── [View Tile] Button
│   │   │
│   │   └── Pagination
│   │       ├── PrevButton
│   │       ├── PageNumbers[]
│   │       └── NextButton
│   │
│   ├── [Hex Map View]
│   │   ├── HexMap (SVG canvas)
│   │   │   ├── HexTile[] (interactive)
│   │   │   └── Tooltip (hover)
│   │   │
│   │   ├── MapLegend
│   │   │   ├── PercentileBand[] (color + label)
│   │   │   └── HotspotFlagEntry
│   │   │
│   │   └── HotspotList
│   │       └── HotspotEntry[]
│   │
│   └── [Tile Inspector View]
│       ├── LeftPanel (60%)
│       │   ├── ImageContainer
│       │   │   ├── ImageComparison
│       │   │   │   ├── PredictionImage
│       │   │   │   └── GroundTruthImage
│       │   │   └── ComparisonToggle
│       │   │
│       │   ├── Timeline
│       │   │   ├── MonthLabels[]
│       │   │   ├── Scrubber (drag handle)
│       │   │   ├── AutoPlayToggle
│       │   │   └── SpeedControl
│       │   │
│       │   ├── ResidualHeatmapToggle
│       │   │   └── OpacitySlider
│       │   │
│       │   └── ModalityControls
│       │       ├── ToggleButton (SAR)
│       │       ├── ToggleButton (Optical)
│       │       ├── ToggleButton (Lights)
│       │       └── RecomputeButton
│       │
│       └── RightPanel (40%)
│           ├── Panel (Climate Scenario)
│           │   ├── Section (Rainfall Anomaly)
│           │   │   ├── ClimateSlider (per month) × 6
│           │   │   └── Tooltip
│           │   │
│           │   ├── Section (Temperature Anomaly)
│           │   │   ├── ClimateSlider (per month) × 6
│           │   │   └── Tooltip
│           │   │
│           │   └── PresetButtons
│           │       ├── PresetButton (Neutral)
│           │       ├── PresetButton (Wet)
│           │       ├── PresetButton (Dry)
│           │       ├── PresetButton (Hot)
│           │       └── PresetButton (Custom)
│           │
│           ├── Panel (Tile Metadata)
│           │   ├── StatCard (TILE ID)
│           │   ├── StatCard (LATITUDE / LONGITUDE)
│           │   ├── StatCard (HOTSPOT?)
│           │   ├── StatCard (PERSISTENCE)
│           │   ├── StatCard (ATTRIBUTION)
│           │   └── StatCard (VALIDATION LOSS)
│           │
│           ├── Panel (Residual Stats)
│           │   ├── StatCard (MEAN RESIDUAL)
│           │   ├── StatCard (TREND)
│           │   ├── StatCard (VALID PIXELS)
│           │   └── ConfidenceIndicator
│           │
│           ├── MetricBadges[]
│           │   ├── MetricBadge (MSE)
│           │   ├── MetricBadge (PSNR)
│           │   ├── MetricBadge (SSIM)
│           │   └── MetricBadge (Accuracy)
│           │
│           └── ActionButtons
│               ├── [COMPARE] Button
│               ├── [EXPORT] Button
│               └── [BACK TO GALLERY] Button
│
└── [Modals]
    ├── LoadingSpinner (with status text)
    ├── ErrorAlert (with action button)
    ├── ToastNotification (transient)
    └── HelpPanel (help icon trigger)
```

---

## 4. Global State Management

State is managed via React Context (or similar). The following global state is required:

```typescript
interface GlobalState {
  // Navigation & Selection
  currentView: 'landing' | 'gallery' | 'tile-inspector' | 'hex-map'
  selectedTileId: string | null

  // Timeline
  currentMonth: number // 0–5 (MAR–AUG)

  // Climate Parameters (per month)
  climateParams: {
    rainfall: number[] // -2σ to +2σ
    temperature: number[] // -2σ to +2σ
  }
  activePreset: 'neutral' | 'wet' | 'dry' | 'hot' | 'custom'

  // Inference & Data
  isLoading: boolean
  inferenceProgress?: string // "Encoding observations...", etc.
  inferenceError?: string

  // Gallery & Tiles
  galleryTiles: TileData[]
  selectedTile?: TileData
  hexMapTiles: HexMapTile[]

  // UI Toggles
  showComparison: boolean // Ground Truth toggle
  comparisonMode: 'prediction' | 'ground-truth'
  modalities: {
    sar: boolean
    optical: boolean
    lights: boolean
  }
  showResidualHeatmap: boolean
  heatmapOpacity: number // 0–100

  // System Status
  modelReady: boolean
  backendAvailable: boolean
}

interface Actions {
  navigateTo(view: string): void
  selectTile(tileId: string): void
  setMonth(month: number): void
  updateClimateParam(type: 'rainfall' | 'temperature', month: number, value: number): void
  setPreset(preset: string): void
  toggleComparison(enabled: boolean): void
  toggleModality(modality: 'sar' | 'optical' | 'lights', enabled: boolean): void
  setHeatmapOpacity(opacity: number): void
  startInference(): void
  onInferenceComplete(results: InferenceResults): void
  onInferenceError(error: string): void
}
```

**Context Provider:**
```typescript
// src/context/GlobalContext.tsx
export const GlobalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // useReducer or similar state management
  return (
    <GlobalContext.Provider value={state}>
      {children}
    </GlobalContext.Provider>
  )
}

export const useGlobal = () => useContext(GlobalContext)
```

---

## 5. Visual Specifications

### 5.1 Color Palette (tokens.json)

**Backgrounds:**
- Primary: `#0a0a0a` (main bg)
- Secondary: `#1a1a1a` (elevated, cards)
- Tertiary: `#262626` (borders, dividers)
- Panel: `rgba(26, 26, 26, 0.95)` (semi-transparent)

**Accent Colors:**
- Cyan (hover): `#14b8a6` (primary interactive)
- Amber (selected): `#f59e0b` (highlight, alerts)
- Green (success): `#22c55e`
- Red (error): `#ef4444`

**Text:**
- Primary: `#f5f5f5` (main text)
- Secondary: `#d4d4d4` (secondary, labels)
- Tertiary: `#a3a3a3` (dim, metadata)
- Disabled: `#737373`

**Borders:**
- Default: `#262626`
- Hover: `#3f3f3f`
- Active: `#14b8a6` (cyan)
- Error: `#ef4444`

---

### 5.2 Typography

**Fonts:**
- Display headers: Rajdhani (geometric, structured)
- UI labels: Inter (clean, readable)
- Data/monospace: JetBrains Mono (code-like, precise)

**Sizes:**
- xs: 0.75rem (small labels, badges)
- sm: 0.875rem (secondary text)
- base: 1rem (body text)
- lg: 1.125rem (section headers)
- xl: 1.25rem (subheadings)
- 2xl: 1.5rem (section titles)
- 3xl: 1.875rem (page titles)
- 4xl: 2.25rem (hero text)
- 5xl: 3rem (main titles)

**Weights:**
- Light: 300
- Normal: 400
- Medium: 500
- Semibold: 600
- Bold: 700
- Black: 900

---

### 5.3 Spacing

All spacing uses 4px base unit (tokens.json):
- 1 = 0.25rem (4px)
- 2 = 0.5rem (8px)
- 3 = 0.75rem (12px)
- 4 = 1rem (16px)
- 6 = 1.5rem (24px)
- 8 = 2rem (32px)
- 12 = 3rem (48px)

**Common Layout:**
- Grid gutter: 1.5rem (24px)
- Panel padding: 1rem or 1.5rem
- Section margin: 2rem (32px)

---

### 5.4 Shadows & Glows

**Shadows (depth):**
- sm: `0 1px 2px 0 rgba(0, 0, 0, 0.5)`
- base: `0 1px 3px 0 rgba(0, 0, 0, 0.6), 0 1px 2px 0 rgba(0, 0, 0, 0.8)`
- md: `0 4px 6px -1px rgba(0, 0, 0, 0.6), 0 2px 4px -1px rgba(0, 0, 0, 0.8)`
- lg: `0 10px 15px -3px rgba(0, 0, 0, 0.7), 0 4px 6px -2px rgba(0, 0, 0, 0.9)`

**Glows (interactive):**
- Cyan glow: `0 0 20px rgba(20, 184, 166, 0.5), 0 0 40px rgba(20, 184, 166, 0.2)`
- Amber glow: `0 0 20px rgba(245, 158, 11, 0.5), 0 0 40px rgba(245, 158, 11, 0.2)`

---

### 5.5 Transitions & Animations

**Timing Functions:**
- Fast: `100ms cubic-bezier(0.4, 0, 0.2, 1)` (micro-interactions)
- Base: `200ms cubic-bezier(0.4, 0, 0.2, 1)` (default state changes)
- Slow: `300ms cubic-bezier(0.4, 0, 0.2, 1)` (panel transitions)
- Slower: `500ms cubic-bezier(0.4, 0, 0.2, 1)` (imagery fades)

**Common Animations:**
- Crossfade (imagery swap): 200ms opacity transition
- Glow on hover: 200ms box-shadow
- Slider drag: instant onChange, visual feedback immediate
- Timeline scrub: 150ms image crossfade

**Disabled animations for `prefers-reduced-motion`:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

### 5.6 Responsive Breakpoints

**Desktop (1400px+):** Full layout, 3-column gallery, hex map visible
**Tablet (768–1024px):** 2-column gallery, stacked panels, hex map smaller
**Mobile (<768px):** 1-column, simplified views, no hex map (future consideration)

---

## 6. Component Props Reference Table

| Component | Key Props | Default | Notes |
|-----------|-----------|---------|-------|
| **AppShell** | `theme`, `showHeader`, `children` | dark, true | Top-level wrapper |
| **Header** | `title`, `statusBadge`, `breadcrumbs` | "SIAD COMMAND CENTER", none | Fixed z-index 1020 |
| **Panel** | `title`, `variant`, `padding`, `collapsible` | default, md, true | Reusable container |
| **TileGrid** | `tiles`, `columns`, `gap` | N/A, 3, md | Responsive grid |
| **TileCard** | `tile`, `isSelected`, `showComparison` | N/A, false, false | Hover expansion |
| **FilterTabs** | `tabs`, `activeTab`, `variant` | N/A, none, category | Horizontal tabs |
| **HexMap** | `tiles`, `zoom`, `canvasWidth`, `showLegend` | N/A, 1, 800, true | SVG-based |
| **MapLegend** | `percentiles`, `position` | N/A, top-left | Legend overlay |
| **TileInspector** | `tileId`, `month`, `climateParams` | N/A, N/A, N/A | Full-screen view |
| **Timeline** | `months`, `currentMonth`, `autoPlaySpeed` | N/A, N/A, normal | Scrubber + controls |
| **ImageComparison** | `predictionUrl`, `groundTruthUrl`, `isComparing` | N/A, N/A, false | Crossfade toggle |
| **ClimateSlider** | `label`, `month`, `value`, `variant` | N/A, N/A, N/A, rainfall | Per-month control |
| **PresetButton** | `preset`, `isActive`, `label` | N/A, false, auto | Quick selection |
| **ToggleButton** | `label`, `isChecked`, `size` | N/A, false, md | Checkbox variant |
| **StatCard** | `label`, `value`, `unit`, `format` | N/A, N/A, N/A, decimal | Compact metric |
| **ConfidenceIndicator** | `value`, `label`, `size` | N/A, auto, md | Circular badge |
| **MetricBadge** | `metric`, `value` | N/A, N/A | Inline badge |

---

## 7. Event Handlers & Callbacks

### 7.1 User Interaction Events

```typescript
// Gallery
onTileCardClick(tileId: string): void
onTileCardHover(tileId: string, isHovered: boolean): void
onFilterTabChange(tabId: string): void

// Hex Map
onHexClick(tileId: string): void
onHexHover(tileId: string | null): void
onHexDoubleClick(tileId: string): void
onHexMapPan(x: number, y: number): void
onHexMapZoom(zoomLevel: number): void

// Tile Inspector
onMonthChange(month: number): void
onClimateSliderChange(type: string, month: number, value: number): void
onPresetSelect(preset: string): void
onComparisonToggle(enabled: boolean): void
onModalityToggle(modality: string, enabled: boolean): void
onHeatmapOpacityChange(opacity: number): void
onResidualHeatmapToggle(enabled: boolean): void
onExportClick(): void
onCompareClick(): void
onBackClick(): void
```

### 7.2 Inference Events

```typescript
// Inference lifecycle
onInferenceStart(): void
onInferenceProgress(stage: string): void // "Encoding", "Rolling out", etc.
onInferenceComplete(results: InferenceResults): void
onInferenceError(error: string): void
onInferenceCancelled(): void

interface InferenceResults {
  tileId: string
  month: number
  predictionImage: string // base64 or URL
  residuals: number[][]
  confidence: number
  metrics: {
    mse: number
    psnr: number
    ssim: number
    accuracy: number
  }
}
```

---

## 8. Accessibility Requirements

### 8.1 Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Focus through all interactive elements |
| `Enter` / `Space` | Activate button, toggle checkbox |
| `Arrow Left` / `Arrow Right` | Scrub timeline, adjust slider |
| `Arrow Up` / `Arrow Down` | Adjust slider fine-grain |
| `Escape` | Close modal, return to previous view |
| `?` | Show help panel |
| `Ctrl+S` | Export/save current tile |

### 8.2 ARIA Labels

All interactive elements MUST include ARIA labels:

```typescript
// Example: Tile card
<button
  aria-label="Tile x001_y003, Rank 1, Residual 0.042, Confidence 94%"
  onClick={() => onTileClick('x001_y003')}
>
  {/* ... */}
</button>

// Example: Climate slider
<input
  type="range"
  aria-label="Rainfall anomaly for March: -2 to +2 sigma"
  aria-valuenow={value}
  aria-valuemin={-2}
  aria-valuemax={2}
/>

// Example: Image
<img
  src="prediction.png"
  alt="Satellite prediction for tile_x001_y003, April 2026, residual 0.042"
/>
```

### 8.3 Color Contrast

**WCAG AA Requirements:**
- Text on background: ≥4.5:1
- UI elements (borders): ≥3:1

Verify all text against background colors:
- `#f5f5f5` on `#0a0a0a`: 15.3:1 ✓
- `#14b8a6` on `#0a0a0a`: 6.7:1 ✓
- `#737373` on `#0a0a0a`: 3.2:1 ✗ (use for non-critical UI only)

### 8.4 Icon + Text Pairing

Never use icons alone for critical information:

```typescript
// Good
<button>
  <IconCompare /> COMPARE GROUND TRUTH
</button>

// Bad
<button>
  <IconCompare aria-label="Compare" />
</button>

// Also good (alt text)
<button aria-label="Compare ground truth">
  <IconCompare />
</button>
```

---

## 9. Error Handling & Loading States

### 9.1 Loading States

**During Inference:**
```
Spinner (pulsing cyan glow)
"Encoding observations..."
  ↓ (step updates dynamically)
"Rolling out predictions..."
  ↓
"Decoding to pixel space..."
  ↓
"PREDICTION COMPLETE" (green badge)
```

**Gallery Load:**
```
"Fetching gallery entries..."
[Spinner with background activity indicator]
```

**Tile Details Load:**
```
"Loading tile metadata..."
[Placeholder skeleton cards]
```

### 9.2 Error States

**Backend Unavailable:**
- Banner at top: "Backend unavailable. Check API connection."
- Color: `#ef4444` (red)
- Action: [RETRY] button with auto-retry every 5s

**Timeout:**
- Alert: "Request timed out. The model may be slow or unresponsive."
- Color: `#f59e0b` (amber, warning)
- Action: [RETRY] button
- Fallback: Load cached result if available

**Tile Not Found:**
- Message: "Tile tile_x001_y003 not found."
- Help: "Available tiles: tile_x000_y001, tile_x000_y002, ..."
- Action: [SELECT ANOTHER TILE] button

**Invalid Climate Parameters:**
- Position: Below climate slider
- Message: "Rainfall anomaly must be between -2σ and +2σ."
- Auto-action: Reset slider to valid range

**OOM (Out of Memory):**
- Critical error banner
- Message: "Out of memory during inference. Try smaller tile or fewer months."
- Suggestion: Reduce resolution or tile size

---

## 10. Performance Considerations

### 10.1 Image Optimization

- **Prediction images:** 256×256px, JPG or WebP, max 30KB
- **Heatmap overlays:** PNG (lossless), max 50KB
- **Gallery thumbnails:** 200×200px, WebP, max 10KB
- **Ground truth reference:** Cache indefinitely
- **Predictions (neutral scenario):** Cache for session
- **Scenario variants:** Cache for 5 minutes

### 10.2 Component Rendering

- Use `React.memo()` for expensive components (TileCard, HexMap)
- Lazy-load off-screen tiles in gallery (Intersection Observer)
- Virtual scrolling for large galleries (react-window or similar)
- Debounce slider changes (200ms) before inference

### 10.3 API Calls

- `GET /tiles` → <100ms
- `POST /predict` (inference) → <1s (cached) or <10s (fresh)
- `GET /gallery` → <200ms

---

## 11. Browser & Device Support

**Target Browsers:**
- Chrome/Edge 90+ (modern standards)
- Firefox 88+
- Safari 14+

**Devices:**
- Desktop (1400px+): Full-featured
- Tablet (768–1024px): Responsive layouts
- Mobile (<768px): Simplified (future, not MVP)

**CSS Features Required:**
- CSS Grid (layout)
- Flexbox (components)
- CSS Custom Properties (tokens)
- CSS Transitions (animations)
- SVG (hex map)

---

## 12. Testing Checklist

### 12.1 Component Unit Tests

- [ ] Props validation (TypeScript)
- [ ] Default props applied correctly
- [ ] Event handlers fire with correct arguments
- [ ] State updates trigger re-renders
- [ ] Accessibility attributes present (aria-label, role)
- [ ] Keyboard interactions work (Enter, Space, Escape, Arrows)

### 12.2 Integration Tests

- [ ] Gallery → Click tile → Tile Inspector opens
- [ ] Hex Map → Click hex → Inspector shows correct tile
- [ ] Timeline scrubber → Month change → Image updates
- [ ] Climate slider → Change value → Inference triggered (if enabled)
- [ ] Preset button → Active state updates, all sliders reset
- [ ] Comparison toggle → Space key or button works
- [ ] Export button → Generates file download

### 12.3 Visual Regression Tests

- [ ] Hover states trigger glows
- [ ] Selected states show amber highlight
- [ ] Loading states show spinner + text
- [ ] Error states show red alerts
- [ ] Responsive breakpoints reflow correctly
- [ ] Animations respect prefers-reduced-motion

### 12.4 Accessibility Tests

- [ ] Keyboard navigation (Tab, Enter, Space, Arrows, Escape)
- [ ] Screen reader compatibility (ARIA labels, semantic HTML)
- [ ] Color contrast (WCAG AA minimum)
- [ ] Focus indicators visible (cyan glow)

---

## 13. API Contracts

### 13.1 GET /api/gallery

**Response:**
```json
{
  "tiles": [
    {
      "id": "tile_x001_y003",
      "imageUrl": "https://...",
      "groundTruthUrl": "https://...",
      "score": 0.0664,
      "rank": 1,
      "confidence": 94,
      "confidenceTier": "high",
      "attribution": "SAR-dominant",
      "month": "MAY"
    }
  ],
  "count": 15,
  "totalCount": 15
}
```

### 13.2 POST /api/predict

**Request:**
```json
{
  "tileId": "tile_x001_y003",
  "month": 1,
  "climateParams": {
    "rainfall": [0, 0.5, 1.0, 0.5, 0, -0.5],
    "temperature": [0, 0, 0, 0, 0, 0]
  }
}
```

**Response:**
```json
{
  "tileId": "tile_x001_y003",
  "month": 1,
  "predictionImage": "base64-encoded PNG",
  "residuals": [[0.01, 0.02, ...], ...],
  "confidence": 87,
  "metrics": {
    "mse": 0.0664,
    "psnr": 28.4,
    "ssim": 0.847,
    "accuracy": 94.2
  }
}
```

### 13.3 GET /api/tiles/{tileId}

**Response:**
```json
{
  "id": "tile_x001_y003",
  "lat": 37.4,
  "lon": -122.1,
  "isHotspot": true,
  "confidence": 87,
  "persistence": 2,
  "attribution": "SAR-dominant",
  "valLoss": 0.0131,
  "meanResidual": 0.042,
  "trend": 0.015,
  "validPixels": 96.2
}
```

---

## 14. Future Enhancements

1. **Video playback:** Smooth 6-month animation (instead of month-by-month)
2. **3D globe view:** Global tile coverage (when expanded beyond SF Bay Area)
3. **Collaborative annotations:** Teams mark hotspots, leave comments
4. **Advanced filtering:** ML-powered search ("show me tiles with SAR changes")
5. **Export to Geojson:** Download predictions as vector tiles
6. **Time-series forecasting:** 12-month rollout (not just 6)
7. **Uncertainty quantification:** Per-pixel confidence maps
8. **Comparison snapshots:** Save before/after pairs for reports

---

## 15. Related Documents

- `ux-spec.md` — Full UX specification, flows, interactions
- `tokens.json` — Design tokens (colors, typography, spacing, shadows)
- `copy-guide.md` — Interface copy and microcopy standards
- `tactical.css` — Base styles and utility classes (to be created)
- API Documentation (TBD)

---

## Appendix: Component Import Template

```typescript
// Example: Importing and using components
import { AppShell, Header, TileGrid, TileCard, TileInspector } from '@/components'
import { useGlobal } from '@/context/GlobalContext'

export const App: React.FC = () => {
  const { currentView, selectedTile, navigateTo } = useGlobal()

  return (
    <AppShell>
      <Header
        title="SIAD COMMAND CENTER"
        statusBadge={{
          label: 'MODEL READY',
          variant: 'success',
        }}
      />

      {currentView === 'gallery' && (
        <TileGrid
          tiles={tiles}
          onTileClick={(tileId) => {
            selectTile(tileId)
            navigateTo('tile-inspector')
          }}
        />
      )}

      {currentView === 'tile-inspector' && selectedTile && (
        <TileInspector
          tileId={selectedTile.id}
          imageUrl={selectedTile.imageUrl}
          onClose={() => navigateTo('gallery')}
        />
      )}
    </AppShell>
  )
}
```

---

## Revision Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-03 | Initial spec: all layout, gallery, map, inspector, control, and metric components with full props, styling, and hierarchy |

---

**End of Component Specifications**

For implementation questions or clarifications, refer to `ux-spec.md`, `tokens.json`, and `copy-guide.md`. When you encounter decisions not covered here, document them and update this file.
