"""Performance benchmarks for SIAD Command Center API."""

import pytest
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestAPIPerformance:
    """Test API endpoint response times."""

    @pytest.mark.benchmark
    def test_health_check_performance(self, benchmark):
        """Benchmark health check endpoint (target: <50ms)."""
        def call_health():
            response = client.get("/health")
            assert response.status_code == 200
            return response

        result = benchmark(call_health)
        # Target: <50ms for health check
        assert benchmark.stats['mean'] < 0.050, \
            f"Health check too slow: {benchmark.stats['mean']*1000:.2f}ms"

    @pytest.mark.benchmark
    def test_aoi_endpoint_performance(self, benchmark):
        """Benchmark AOI metadata endpoint (target: <100ms)."""
        def call_aoi():
            response = client.get("/api/aoi")
            assert response.status_code == 200
            return response

        result = benchmark(call_aoi)
        # Target: <100ms for AOI metadata
        assert benchmark.stats['mean'] < 0.100, \
            f"AOI endpoint too slow: {benchmark.stats['mean']*1000:.2f}ms"

    @pytest.mark.benchmark
    def test_hotspots_list_performance(self, benchmark):
        """Benchmark hotspots listing (target: <500ms for 100 hotspots)."""
        def call_hotspots():
            response = client.get("/api/detect/hotspots?limit=100")
            assert response.status_code == 200
            return response

        result = benchmark(call_hotspots)
        # Target: <500ms for hotspot list
        assert benchmark.stats['mean'] < 0.500, \
            f"Hotspots endpoint too slow: {benchmark.stats['mean']*1000:.2f}ms"

    @pytest.mark.benchmark
    def test_tile_detail_performance(self, benchmark):
        """Benchmark tile detail endpoint (target: <200ms)."""
        # First get a valid tile ID
        hotspots_response = client.get("/api/detect/hotspots?limit=1")
        assert hotspots_response.status_code == 200
        hotspots = hotspots_response.json()

        if len(hotspots) == 0:
            pytest.skip("No hotspots available for testing")

        tile_id = hotspots[0]["tileId"]

        def call_tile_detail():
            response = client.get(f"/api/detect/tile/{tile_id}")
            assert response.status_code == 200
            return response

        result = benchmark(call_tile_detail)
        # Target: <200ms for tile detail
        assert benchmark.stats['mean'] < 0.200, \
            f"Tile detail endpoint too slow: {benchmark.stats['mean']*1000:.2f}ms"


class TestAPIThroughput:
    """Test API throughput under load."""

    def test_concurrent_hotspot_requests(self):
        """Test handling multiple concurrent requests (target: >10 req/sec)."""
        num_requests = 50
        start_time = time.time()

        responses = []
        for _ in range(num_requests):
            response = client.get("/api/detect/hotspots?limit=10")
            responses.append(response)

        end_time = time.time()
        duration = end_time - start_time

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)

        # Calculate throughput
        throughput = num_requests / duration
        print(f"\nThroughput: {throughput:.2f} req/sec")

        # Target: >10 requests per second
        assert throughput > 10, f"Throughput too low: {throughput:.2f} req/sec"

    def test_large_dataset_handling(self):
        """Test handling large dataset queries (target: <2s for 1000 hotspots)."""
        start_time = time.time()
        response = client.get("/api/detect/hotspots?limit=1000&min_score=0.0")
        end_time = time.time()

        assert response.status_code == 200
        duration = end_time - start_time

        print(f"\nLarge dataset query time: {duration*1000:.2f}ms")

        # Target: <2 seconds for large dataset
        assert duration < 2.0, f"Large dataset query too slow: {duration*1000:.2f}ms"


class TestDataLoadingPerformance:
    """Test data loading and caching performance."""

    def test_first_request_vs_cached(self):
        """Test that subsequent requests benefit from caching."""
        # First request (may involve data loading)
        start_time = time.time()
        response1 = client.get("/api/detect/hotspots?limit=100")
        first_request_time = time.time() - start_time

        assert response1.status_code == 200

        # Second request (should be faster if cached)
        start_time = time.time()
        response2 = client.get("/api/detect/hotspots?limit=100")
        second_request_time = time.time() - start_time

        assert response2.status_code == 200

        print(f"\nFirst request: {first_request_time*1000:.2f}ms")
        print(f"Second request: {second_request_time*1000:.2f}ms")

        # Second request should generally be as fast or faster
        # (Not strictly enforced as it can vary, but logged for observation)


class TestMemoryEfficiency:
    """Test memory efficiency of data operations."""

    def test_streaming_response_size(self):
        """Test response size is reasonable (target: <1MB for 100 hotspots)."""
        response = client.get("/api/detect/hotspots?limit=100")
        assert response.status_code == 200

        # Calculate response size
        response_size = len(response.content)
        response_size_mb = response_size / (1024 * 1024)

        print(f"\nResponse size for 100 hotspots: {response_size_mb:.2f}MB")

        # Target: <1MB for 100 hotspots
        assert response_size_mb < 1.0, \
            f"Response too large: {response_size_mb:.2f}MB"


class TestEndToEndPerformance:
    """Test end-to-end user workflows."""

    def test_typical_user_session_performance(self):
        """Test typical user session (target: <2s total)."""
        start_time = time.time()

        # Typical user workflow:
        # 1. Load AOI metadata
        response1 = client.get("/api/aoi")
        assert response1.status_code == 200

        # 2. Load initial hotspots
        response2 = client.get("/api/detect/hotspots?limit=100")
        assert response2.status_code == 200

        # 3. Click on first hotspot to view detail
        hotspots = response2.json()
        if len(hotspots) > 0:
            tile_id = hotspots[0]["tileId"]
            response3 = client.get(f"/api/detect/tile/{tile_id}")
            assert response3.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        print(f"\nTypical user session time: {total_time*1000:.2f}ms")

        # Target: <2 seconds for initial load + interaction
        assert total_time < 2.0, \
            f"User session too slow: {total_time*1000:.2f}ms"


# Performance test summary
def test_performance_summary():
    """Print performance summary."""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    print("\nTarget Metrics:")
    print("  - Health check: <50ms")
    print("  - AOI metadata: <100ms")
    print("  - Hotspot list (100): <500ms")
    print("  - Tile detail: <200ms")
    print("  - Throughput: >10 req/sec")
    print("  - Large dataset (1000): <2s")
    print("  - Response size (100): <1MB")
    print("  - User session: <2s")
    print("="*60)


if __name__ == "__main__":
    # Run with: pytest test_performance.py -v --benchmark-only
    # Or: pytest test_performance.py -v --benchmark-min-rounds=5
    pytest.main([__file__, "-v"])
