"""Integration tests for SIAD Command Center API."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and root endpoints."""

    def test_health_check(self):
        """Test health check endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "SIAD Command Center API"
        assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "SIAD Command Center API"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self):
        """Test CORS headers are present in responses."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


class TestAOIEndpoints:
    """Test AOI metadata endpoints."""

    def test_get_aoi_metadata(self):
        """Test GET /api/aoi returns AOI metadata."""
        response = client.get("/api/aoi")
        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "name" in data
        assert "bounds" in data
        assert "tileCount" in data
        assert "timeRange" in data

        # Verify data types
        assert isinstance(data["name"], str)
        assert isinstance(data["bounds"], list)
        assert len(data["bounds"]) == 4  # [west, south, east, north]
        assert isinstance(data["tileCount"], int)
        assert isinstance(data["timeRange"], list)
        assert len(data["timeRange"]) == 2  # [start, end]


class TestHotspotEndpoints:
    """Test hotspot detection endpoints."""

    def test_get_hotspots_default_params(self):
        """Test GET /api/detect/hotspots with default parameters."""
        response = client.get("/api/detect/hotspots")
        assert response.status_code == 200
        data = response.json()

        # Should return a list
        assert isinstance(data, list)

        # If hotspots exist, verify structure
        if len(data) > 0:
            hotspot = data[0]
            required_fields = [
                "tileId", "score", "lat", "lon", "month",
                "changeType", "region"
            ]
            for field in required_fields:
                assert field in hotspot, f"Missing field: {field}"

            # Verify data types
            assert isinstance(hotspot["tileId"], str)
            assert isinstance(hotspot["score"], (int, float))
            assert isinstance(hotspot["lat"], (int, float))
            assert isinstance(hotspot["lon"], (int, float))
            assert isinstance(hotspot["month"], str)
            assert isinstance(hotspot["changeType"], str)
            assert isinstance(hotspot["region"], str)

    def test_get_hotspots_with_threshold(self):
        """Test GET /api/detect/hotspots with min_score threshold."""
        response = client.get("/api/detect/hotspots?min_score=0.8")
        assert response.status_code == 200
        data = response.json()

        # All returned hotspots should meet threshold
        for hotspot in data:
            assert hotspot["score"] >= 0.8

    def test_get_hotspots_with_limit(self):
        """Test GET /api/detect/hotspots with limit parameter."""
        response = client.get("/api/detect/hotspots?limit=10")
        assert response.status_code == 200
        data = response.json()

        # Should return at most 10 results
        assert len(data) <= 10

    def test_get_hotspots_invalid_threshold(self):
        """Test GET /api/detect/hotspots with invalid threshold."""
        # Negative threshold
        response = client.get("/api/detect/hotspots?min_score=-0.5")
        # Should either reject or clamp to valid range
        assert response.status_code in [200, 400, 422]

        # Threshold > 1
        response = client.get("/api/detect/hotspots?min_score=1.5")
        # Should either reject or clamp to valid range
        assert response.status_code in [200, 400, 422]


class TestTileDetailEndpoints:
    """Test tile detail endpoints."""

    def test_get_tile_detail_valid_tile(self):
        """Test GET /api/detect/tile/{tile_id} with valid tile."""
        # First get a valid tile ID from hotspots
        hotspots_response = client.get("/api/detect/hotspots?limit=1")
        assert hotspots_response.status_code == 200
        hotspots = hotspots_response.json()

        if len(hotspots) > 0:
            tile_id = hotspots[0]["tileId"]

            # Get tile detail
            response = client.get(f"/api/detect/tile/{tile_id}")
            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "tileId" in data
            assert "metadata" in data
            assert "timeline" in data

            # Verify metadata structure
            metadata = data["metadata"]
            assert "lat" in metadata
            assert "lon" in metadata
            assert "region" in metadata

            # Verify timeline structure
            timeline = data["timeline"]
            assert isinstance(timeline, list)
            if len(timeline) > 0:
                entry = timeline[0]
                assert "month" in entry
                assert "score" in entry

    def test_get_tile_detail_invalid_tile(self):
        """Test GET /api/detect/tile/{tile_id} with invalid tile ID."""
        response = client.get("/api/detect/tile/invalid_tile_id_12345")
        # Should return 404
        assert response.status_code == 404


class TestStaticFiles:
    """Test static file serving."""

    def test_static_tiles_endpoint_exists(self):
        """Test that static tiles endpoint is mounted."""
        # Try to access a static file path (may not exist, but endpoint should be mounted)
        response = client.get("/static/tiles/tile_x000_y000_2024-01_baseline_rgb.png")
        # Should return either 200 (if file exists) or 404 (if file doesn't exist)
        # Should NOT return 405 (method not allowed) or other routing errors
        assert response.status_code in [200, 404]


class TestErrorHandling:
    """Test API error handling."""

    def test_404_on_invalid_endpoint(self):
        """Test that invalid endpoints return 404."""
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404

    def test_405_on_wrong_method(self):
        """Test that wrong HTTP methods return 405."""
        response = client.post("/health")
        assert response.status_code == 405


class TestDataConsistency:
    """Test data consistency across endpoints."""

    def test_aoi_bounds_contain_hotspots(self):
        """Test that all hotspots are within AOI bounds."""
        # Get AOI bounds
        aoi_response = client.get("/api/aoi")
        assert aoi_response.status_code == 200
        aoi = aoi_response.json()
        west, south, east, north = aoi["bounds"]

        # Get hotspots
        hotspots_response = client.get("/api/detect/hotspots")
        assert hotspots_response.status_code == 200
        hotspots = hotspots_response.json()

        # Verify all hotspots are within bounds
        for hotspot in hotspots:
            lat, lon = hotspot["lat"], hotspot["lon"]
            assert west <= lon <= east, f"Hotspot lon {lon} outside bounds [{west}, {east}]"
            assert south <= lat <= north, f"Hotspot lat {lat} outside bounds [{south}, {north}]"

    def test_hotspot_months_within_aoi_timerange(self):
        """Test that all hotspot months are within AOI time range."""
        # Get AOI time range
        aoi_response = client.get("/api/aoi")
        assert aoi_response.status_code == 200
        aoi = aoi_response.json()
        start_month, end_month = aoi["timeRange"]

        # Get hotspots
        hotspots_response = client.get("/api/detect/hotspots")
        assert hotspots_response.status_code == 200
        hotspots = hotspots_response.json()

        # Verify all hotspot months are within range
        for hotspot in hotspots:
            month = hotspot["month"]
            assert start_month <= month <= end_month, \
                f"Hotspot month {month} outside range [{start_month}, {end_month}]"

    def test_tile_detail_matches_hotspot_data(self):
        """Test that tile detail data matches hotspot list data."""
        # Get first hotspot
        hotspots_response = client.get("/api/detect/hotspots?limit=1")
        assert hotspots_response.status_code == 200
        hotspots = hotspots_response.json()

        if len(hotspots) > 0:
            hotspot = hotspots[0]
            tile_id = hotspot["tileId"]

            # Get tile detail
            detail_response = client.get(f"/api/detect/tile/{tile_id}")
            assert detail_response.status_code == 200
            detail = detail_response.json()

            # Verify matching data
            assert detail["tileId"] == hotspot["tileId"]
            assert detail["metadata"]["lat"] == hotspot["lat"]
            assert detail["metadata"]["lon"] == hotspot["lon"]
            assert detail["metadata"]["region"] == hotspot["region"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
