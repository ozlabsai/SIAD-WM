// API Response Types matching backend schemas

export interface AOI {
  name: string;
  bounds: [number, number, number, number]; // [west, south, east, north]
  tileCount: number;
  timeRange: [string, string]; // ["YYYY-MM", "YYYY-MM"]
  description: string;
}

export interface Hotspot {
  tileId: string;
  score: number;
  lat: number;
  lon: number;
  month: string; // "YYYY-MM"
  changeType: string; // e.g., "deforestation", "construction"
  region: string;
  // Derived fields for UI
  confidence?: 'High' | 'Medium' | 'Low';
  alert_type?: 'Structural' | 'Activity';
  onset?: string;
  duration?: number;
}

export interface TileDetail {
  tileId: string; // Backend returns camelCase
  lat: number;
  lon: number;
  score: number;
  region?: string;
  changeType?: string;
  onsetMonth?: number;
  metadata?: {
    bounds?: [number, number, number, number];
    center?: [number, number];
  };
  timeline: TimelinePoint[];
  heatmap: HeatmapData;
  baselines?: BaselineComparison;
}

export interface TimelinePoint {
  month: string; // "YYYY-MM"
  score: number;
  timestamp: string; // ISO timestamp
  // UI-only fields (not from API)
  observed?: number;
  predicted?: number;
  confidence?: 'High' | 'Medium' | 'Low';
}

export interface HeatmapData {
  months?: string[]; // ["2024-01", ...] - UI only
  modalities?: string[]; // ["SAR", "Optical", "Lights"] - UI only
  values?: number[][]; // 2D array - from backend this is a flat 16x16 array
}

export interface BaselineComparison {
  persistence: number[]; // Array of 12 monthly scores
  seasonal: number[]; // Array of 12 monthly scores
}

// Legacy - no longer used
export interface BaselineMetrics {
  mae: number;
  rmse: number;
  improvement: number; // percentage
}

export interface TileAssets {
  tile_id: string;
  month: string;
  assets: {
    sar?: string;
    optical?: string;
    lights?: string;
    composite?: string;
  };
}

// UI State Types

export interface MapViewport {
  latitude: number;
  longitude: number;
  zoom: number;
}

export interface FilterState {
  minScore: number;
  dateRange: [string, string] | null;
  alertType: 'All' | 'Structural' | 'Activity';
  confidence: 'All' | 'High' | 'Medium' | 'Low';
  minDuration: number;
  searchQuery: string;
}

export interface TimelineState {
  currentMonth: string;
  isPlaying: boolean;
  playbackSpeed: 1 | 2 | 4;
  availableMonths: string[];
}

// GeoJSON Types for Mapbox

export interface HotspotFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number]; // [lon, lat]
  };
  properties: {
    tile_id: string;
    score: number;
    confidence: string;
    alert_type: string;
  };
}

export interface HotspotFeatureCollection {
  type: 'FeatureCollection';
  features: HotspotFeature[];
}
