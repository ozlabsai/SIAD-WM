/**
 * SIAD Command Center - API Client
 * Type-safe Axios client for FastAPI backend communication
 * Backend: http://localhost:8000
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import {
  ApiResponse,
  PaginatedResponse,
  Tile,
  Prediction,
  TileData,
  GalleryEntry,
  GalleryStats,
  ClimateAction,
  ClimateScenario,
  FilterOptions,
  TimeSeriesData,
} from './types.ts'

/* ============================================================================
   1. AXIOS INSTANCE CONFIGURATION
   ========================================================================== */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

// Request interceptor for error handling
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available in future
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

/* ============================================================================
   2. GALLERY ENDPOINTS
   ========================================================================== */

/**
 * Fetch all gallery entries with optional filtering
 */
export const getGallery = async (
  filters?: FilterOptions,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<GalleryEntry>> => {
  const response = await apiClient.get<PaginatedResponse<GalleryEntry>>(
    '/gallery',
    {
      params: {
        page,
        page_size: pageSize,
        ...filters,
      },
    }
  )
  return response.data
}

/**
 * Fetch gallery statistics
 */
export const getGalleryStats = async (): Promise<GalleryStats> => {
  const response = await apiClient.get<GalleryStats>('/gallery/stats')
  return response.data
}

/**
 * Fetch a single gallery entry by ID
 */
export const getGalleryEntry = async (id: string): Promise<GalleryEntry> => {
  const response = await apiClient.get<GalleryEntry>(`/gallery/${id}`)
  return response.data
}

/* ============================================================================
   3. TILE & GEOSPATIAL ENDPOINTS
   ========================================================================== */

/**
 * Fetch tile data by ID
 */
export const getTileData = async (tileId: string): Promise<TileData> => {
  const response = await apiClient.get<TileData>(`/tiles/${tileId}`)
  return response.data
}

/**
 * Fetch all available tiles with filters
 */
export const getTiles = async (filters?: FilterOptions): Promise<Tile[]> => {
  const response = await apiClient.get<Tile[]>('/tiles', {
    params: filters,
  })
  return response.data
}

/**
 * Fetch tiles in a bounding box
 */
export const getTilesByBoundingBox = async (
  north: number,
  south: number,
  east: number,
  west: number
): Promise<Tile[]> => {
  const response = await apiClient.get<Tile[]>('/tiles/bounds', {
    params: { north, south, east, west },
  })
  return response.data
}

/* ============================================================================
   4. PREDICTION ENDPOINTS
   ========================================================================== */

/**
 * Get prediction for a specific tile
 */
export const getPrediction = async (tileId: string): Promise<Prediction> => {
  const response = await apiClient.get<Prediction>(
    `/predictions/${tileId}`
  )
  return response.data
}

/**
 * Get historical predictions for a tile
 */
export const getPredictionHistory = async (
  tileId: string,
  limit: number = 12
): Promise<Prediction[]> => {
  const response = await apiClient.get<Prediction[]>(
    `/predictions/${tileId}/history`,
    {
      params: { limit },
    }
  )
  return response.data
}

/**
 * Run inference/prediction on a specific tile
 * This may trigger model execution
 */
export const predict = async (tileId: string): Promise<Prediction> => {
  const response = await apiClient.post<Prediction>(
    `/predictions/${tileId}/predict`,
    {}
  )
  return response.data
}

/**
 * Batch predictions for multiple tiles
 */
export const batchPredict = async (tileIds: string[]): Promise<Prediction[]> => {
  const response = await apiClient.post<Prediction[]>(
    '/predictions/batch',
    { tile_ids: tileIds }
  )
  return response.data
}

/* ============================================================================
   5. CLIMATE & ENVIRONMENTAL ENDPOINTS
   ========================================================================== */

/**
 * Get climate actions
 */
export const getClimateActions = async (
  filters?: FilterOptions
): Promise<ClimateAction[]> => {
  const response = await apiClient.get<ClimateAction[]>(
    '/climate/actions',
    { params: filters }
  )
  return response.data
}

/**
 * Get climate scenarios for projection
 */
export const getClimateScenarios = async (): Promise<ClimateScenario[]> => {
  const response = await apiClient.get<ClimateScenario[]>(
    '/climate/scenarios'
  )
  return response.data
}

/**
 * Get time series data for a location
 */
export const getTimeSeries = async (
  metric: string,
  latitude: number,
  longitude: number,
  startDate?: string,
  endDate?: string
): Promise<TimeSeriesData> => {
  const response = await apiClient.get<TimeSeriesData>(
    `/timeseries/${metric}`,
    {
      params: {
        latitude,
        longitude,
        start_date: startDate,
        end_date: endDate,
      },
    }
  )
  return response.data
}

/* ============================================================================
   6. ERROR HANDLING & UTILITIES
   ========================================================================== */

/**
 * Generic error handler for API calls
 */
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.detail || error.message
    return typeof message === 'string' ? message : 'An error occurred'
  }
  return 'An unexpected error occurred'
}

/**
 * Check API health/connectivity
 */
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/health')
    return response.status === 200
  } catch {
    return false
  }
}

/**
 * Get API version information
 */
export const getApiVersion = async (): Promise<string> => {
  try {
    const response = await apiClient.get<{ version: string }>('/version')
    return response.data.version
  } catch {
    return 'unknown'
  }
}

/* ============================================================================
   7. EXPORT METHODS FOR CONVENIENCE
   ========================================================================== */

export default {
  // Gallery
  getGallery,
  getGalleryStats,
  getGalleryEntry,

  // Tiles
  getTileData,
  getTiles,
  getTilesByBoundingBox,

  // Predictions
  getPrediction,
  getPredictionHistory,
  predict,
  batchPredict,

  // Climate
  getClimateActions,
  getClimateScenarios,
  getTimeSeries,

  // Utilities
  checkApiHealth,
  getApiVersion,
  handleApiError,
}
