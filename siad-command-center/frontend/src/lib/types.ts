/**
 * SIAD Command Center - TypeScript Type Definitions
 * Core data structures for the tactical intelligence dashboard
 */

/* ============================================================================
   1. GEOSPATIAL & TILE DATA
   ========================================================================== */

export interface Coordinates {
  latitude: number
  longitude: number
}

export interface BoundingBox {
  north: number
  south: number
  east: number
  west: number
}

export interface Tile {
  id: string
  coordinates: Coordinates
  boundingBox: BoundingBox
  resolution: number // meters per pixel
  timestamp: string // ISO 8601
  source: 'sentinel-2' | 'landsat-8' | 'modis'
  cloudCover: number // 0-100 percentage
  dataUrl: string
  thumbnailUrl: string
}

/* ============================================================================
   2. CLIMATE & ENVIRONMENTAL DATA
   ========================================================================== */

export interface ClimateMetrics {
  temperature: number // Celsius
  temperatureAnomaly: number // deviation from baseline
  rainfall: number // millimeters
  ndvi: number // Normalized Difference Vegetation Index (0-1)
  soilMoisture: number // percentage
  co2Levels: number // ppm
}

export interface ClimateAction {
  id: string
  name: string
  description: string
  location: Coordinates
  type: 'reforestation' | 'renewable-energy' | 'urban-green' | 'water-conservation'
  startDate: string
  targetDate: string
  status: 'planned' | 'in-progress' | 'completed'
  estimatedImpact: string
  confidence: number // 0-1
}

export interface ClimateScenario {
  id: string
  name: string
  description: string
  timeframe: '2030' | '2050' | '2070' | '2100'
  temperature: number
  co2Level: number
  rainfallChange: number // percentage change
  parameters: Record<string, number>
}

/* ============================================================================
   3. PREDICTION & MODEL OUTPUTS
   ========================================================================== */

export interface Prediction {
  id: string
  tileId: string
  timestamp: string
  model: string
  version: string
  predictions: {
    landCover: Record<string, number> // classification probabilities
    climateMetrics: ClimateMetrics
    uncertaintyMap: number[][] // pixel-level confidence
  }
  metrics: ModelMetrics
  confidence: 'high' | 'medium' | 'low'
  confidence_score: number // 0-1
}

export interface ModelMetrics {
  mse: number // Mean Squared Error
  psnr: number // Peak Signal-to-Noise Ratio (dB)
  ssim: number // Structural Similarity Index (0-1)
  accuracy: number // Overall accuracy (0-1)
  inferenceTime: number // milliseconds
}

export interface TileData {
  tileId: string
  rawImage: string // base64 or URL
  prediction: Prediction
  historical?: {
    predictions: Prediction[]
    timespan: string
  }
}

/* ============================================================================
   4. GALLERY & VISUALIZATION
   ========================================================================== */

export interface GalleryEntry {
  id: string
  title: string
  description: string
  thumbnail: string
  location: Coordinates
  date: string
  category: 'prediction' | 'comparison' | 'climate-action' | 'hazard'
  tags: string[]
  metrics?: ModelMetrics
  featured: boolean
}

export interface GalleryStats {
  totalEntries: number
  totalTiles: number
  dateRange: {
    start: string
    end: string
  }
  topCategories: Array<{
    category: string
    count: number
  }>
  averageConfidence: number
}

/* ============================================================================
   5. TEMPORAL DATA
   ========================================================================== */

export interface TimelineEntry {
  timestamp: string
  event: string
  value?: number
  confidence?: number
  tileIds?: string[]
}

export interface TimeSeriesData {
  metric: string
  unit: string
  data: Array<{
    timestamp: string
    value: number
    confidence?: number
  }>
}

/* ============================================================================
   6. USER INTERFACE STATE
   ========================================================================== */

export interface FilterOptions {
  dateRange?: {
    start: string
    end: string
  }
  location?: BoundingBox
  confidence?: {
    min: number
    max: number
  }
  cloudCover?: {
    min: number
    max: number
  }
  categories?: string[]
  sources?: string[]
}

export interface ViewState {
  selectedTile?: Tile
  selectedPrediction?: Prediction
  timelinePosition: number // 0-1 normalized position
  zoom: number
  pan: { x: number; y: number }
  comparisonMode: 'single' | 'before-after' | 'predictions'
}

export interface PanelState {
  galleryOpen: boolean
  inspectorOpen: boolean
  metricsOpen: boolean
  filterPanelOpen: boolean
}

/* ============================================================================
   7. API RESPONSE TYPES
   ========================================================================== */

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  timestamp: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

/* ============================================================================
   8. THREE.JS / VISUALIZATION DATA
   ========================================================================== */

export interface HexMapData {
  hexagons: Array<{
    id: string
    position: [number, number, number] // x, y, z
    value: number // for coloring
    label?: string
    clickable: boolean
  }>
  bounds: {
    minX: number
    maxX: number
    minY: number
    maxY: number
  }
}

export interface VisualizationConfig {
  colorMap: 'viridis' | 'plasma' | 'inferno' | 'magma' | 'cividis'
  valueRange: [number, number]
  scale: number
  opacity: number
  showLabels: boolean
  animationEnabled: boolean
}
