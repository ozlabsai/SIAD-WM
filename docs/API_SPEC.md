# SIAD API Specification v2.0

**Latent Residual Detection API**

---

## Base URL

```
Development: http://localhost:8000
Production: TBD
```

---

## Authentication

MVP: No authentication required (local demo)
Production: API key or JWT tokens

---

## Core Endpoints

### 1. Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "2.0.0"
}
```

---

### 2. Compute Residuals

```
POST /api/detect/residuals
```

**Request Body:**
```json
{
  "tile_id": "tile_042",
  "context_month": "2024-01",
  "rollout_horizon": 6,
  "normalize_weather": true
}
```

**Response:**
```json
{
  "tile_id": "tile_042",
  "residuals": {
    "2024-02": [0.12, 0.34, ...],  // 256 floats
    "2024-03": [0.15, 0.31, ...],
    "2024-04": [0.18, 0.42, ...],
    "2024-05": [0.21, 0.45, ...],
    "2024-06": [0.19, 0.41, ...],
    "2024-07": [0.17, 0.38, ...]
  },
  "tile_scores": [0.45, 0.52, 0.61, 0.58, 0.55, 0.49],
  "metadata": {
    "computation_time_ms": 1234,
    "model_version": "v2.0",
    "weather_normalized": true
  }
}
```

---

### 3. Get Hotspots

```
GET /api/hotspots
```

**Query Parameters:**
- `start_date` (optional): ISO date, default: earliest available
- `end_date` (optional): ISO date, default: latest available
- `min_score` (optional): float 0-1, default: 0.5
- `alert_type` (optional): "structural" | "activity" | "all", default: "all"
- `limit` (optional): int, default: 10
- `offset` (optional): int, default: 0

**Response:**
```json
{
  "hotspots": [
    {
      "id": "hs_001",
      "rank": 1,
      "tile_id": "tile_042",
      "region": "san_francisco_mission_bay",
      "score": 0.82,
      "onset": "2024-06",
      "duration": 4,
      "alert_type": "structural_acceleration",
      "confidence": "high",
      "coordinates": {
        "lat": 37.7599,
        "lon": -122.3894
      }
    }
  ],
  "total": 47,
  "filters_applied": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "min_score": 0.5
  }
}
```

---

### 4. Get Hotspot Timeline

```
GET /api/hotspots/{hotspot_id}/timeline
```

**Response:**
```json
{
  "hotspot_id": "hs_001",
  "tile_id": "tile_042",
  "timeline": [
    {
      "month": "2024-06",
      "score": 0.67,
      "confidence": "medium"
    },
    {
      "month": "2024-07",
      "score": 0.74,
      "confidence": "high"
    },
    {
      "month": "2024-08",
      "score": 0.82,
      "confidence": "high"
    },
    {
      "month": "2024-09",
      "score": 0.79,
      "confidence": "high"
    }
  ],
  "onset": "2024-06",
  "peak": "2024-08",
  "current_status": "active"
}
```

---

### 5. Get Baseline Comparison

```
GET /api/baselines/{tile_id}
```

**Query Parameters:**
- `month` (required): ISO date (YYYY-MM)

**Response:**
```json
{
  "tile_id": "tile_042",
  "month": "2024-03",
  "residuals": {
    "world_model": 0.52,
    "persistence": 0.68,
    "seasonal": 0.71
  },
  "improvement": {
    "vs_persistence": 0.24,
    "vs_seasonal": 0.27
  },
  "confidence_intervals": {
    "world_model": [0.48, 0.56],
    "persistence": [0.64, 0.72],
    "seasonal": [0.67, 0.75]
  }
}
```

---

### 6. Get Token Heatmap

```
GET /api/tiles/{tile_id}/heatmap
```

**Query Parameters:**
- `month` (required): ISO date
- `normalize_weather` (optional): boolean, default: true

**Response:**
```json
{
  "tile_id": "tile_042",
  "month": "2024-03",
  "heatmap": {
    "shape": [16, 16],
    "values": [
      [0.12, 0.34, 0.23, ..., 0.56],
      [0.18, 0.42, 0.31, ..., 0.62],
      ...
    ],
    "min_value": 0.05,
    "max_value": 0.95,
    "mean_value": 0.43,
    "std_value": 0.18
  },
  "metadata": {
    "normalized": true,
    "colorscale": "viridis"
  }
}
```

---

### 7. Export Hotspots (GeoJSON)

```
GET /api/export/geojson
```

**Query Parameters:**
- `start_date` (optional): ISO date
- `end_date` (optional): ISO date
- `min_score` (optional): float 0-1

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-122.3894, 37.7599]
      },
      "properties": {
        "hotspot_id": "hs_001",
        "tile_id": "tile_042",
        "score": 0.82,
        "onset": "2024-06",
        "duration": 4,
        "alert_type": "structural_acceleration",
        "confidence": "high"
      }
    }
  ]
}
```

---

### 8. Export Timeline (CSV)

```
GET /api/export/timeline.csv
```

**Query Parameters:**
- `hotspot_id` (required): string

**Response:** (CSV format)
```csv
month,score,confidence,alert_type
2024-06,0.67,medium,structural_acceleration
2024-07,0.74,high,structural_acceleration
2024-08,0.82,high,structural_acceleration
2024-09,0.79,high,structural_acceleration
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": {
    "code": "TILE_NOT_FOUND",
    "message": "Tile tile_999 not found in database",
    "details": {
      "tile_id": "tile_999",
      "available_tiles": ["tile_001", "tile_002", ...]
    }
  }
}
```

**Common Error Codes:**
- `TILE_NOT_FOUND` (404)
- `INVALID_DATE_RANGE` (400)
- `MODEL_NOT_LOADED` (503)
- `COMPUTATION_FAILED` (500)
- `RATE_LIMIT_EXCEEDED` (429)

---

## Data Types

### Alert Type
```typescript
type AlertType = "structural_acceleration" | "activity_surge"
```

### Confidence Level
```typescript
type Confidence = "high" | "medium" | "low"
```

### Hotspot
```typescript
interface Hotspot {
  id: string;
  rank: number;
  tile_id: string;
  region: string;
  score: number;  // 0-1
  onset: string;  // ISO date (YYYY-MM)
  duration: number;  // months
  alert_type: AlertType;
  confidence: Confidence;
  coordinates: {
    lat: number;
    lon: number;
  };
}
```

---

## Rate Limits

Development: No limits
Production: 100 requests/minute per IP

---

## Caching Headers

Residual computations are expensive. Use HTTP caching:

```
Cache-Control: public, max-age=3600
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

---

## Versioning

API version included in all responses:

```json
{
  "api_version": "2.0.0",
  "model_version": "2.0",
  ...
}
```

---

**Last Updated:** 2026-03-03
