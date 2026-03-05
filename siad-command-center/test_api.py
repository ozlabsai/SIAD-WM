"""Test script for SIAD Command Center API."""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint."""
    print("\n=== Testing /health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_aoi_metadata():
    """Test AOI metadata endpoint."""
    print("\n=== Testing /api/aoi ===")
    response = requests.get(f"{BASE_URL}/api/aoi")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Name: {data['name']}")
    print(f"Tile Count: {data['tileCount']}")
    print(f"Time Range: {data['timeRange']}")
    return response.status_code == 200

def test_months():
    """Test months endpoint."""
    print("\n=== Testing /api/aoi/months ===")
    response = requests.get(f"{BASE_URL}/api/aoi/months")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Number of months: {len(data)}")
    print(f"First month: {data[0]}")
    print(f"Last month: {data[-1]}")
    return response.status_code == 200 and len(data) == 12

def test_hotspots():
    """Test hotspots endpoint."""
    print("\n=== Testing /api/detect/hotspots ===")
    response = requests.get(f"{BASE_URL}/api/detect/hotspots?min_score=0.5&limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Number of hotspots: {len(data)}")
    if data:
        print(f"Top hotspot: {data[0]['tileId']} (score: {data[0]['score']:.4f})")
    return response.status_code == 200 and len(data) > 0

def test_tile_detail():
    """Test tile detail endpoint."""
    print("\n=== Testing /api/detect/tile/{tile_id} ===")
    response = requests.get(f"{BASE_URL}/api/detect/tile/tile_x000_y000")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Tile ID: {data['tileId']}")
    print(f"Score: {data['score']}")
    print(f"Region: {data['region']}")
    print(f"Change Type: {data['changeType']}")
    print(f"Heatmap shape: {len(data['heatmap'])}x{len(data['heatmap'][0])}")
    print(f"Timeline points: {len(data['timeline'])}")
    print(f"Baseline data points: {len(data['baselines']['persistence'])}")
    return response.status_code == 200 and len(data['heatmap']) == 16

def test_tile_assets():
    """Test tile assets endpoint."""
    print("\n=== Testing /api/tiles/{tile_id}/assets ===")
    response = requests.get(f"{BASE_URL}/api/tiles/tile_x000_y000/assets?month=2024-01")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Tile ID: {data['tileId']}")
    print(f"Month: {data['month']}")
    print(f"Actual: {data['actual']}")
    print(f"Predicted: {data['predicted']}")
    print(f"Residual: {data['residual']}")
    return response.status_code == 200

def test_static_files():
    """Test static file serving."""
    print("\n=== Testing Static File Serving ===")
    response = requests.get(f"{BASE_URL}/static/tiles/tile_000/month_01/actual.png")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content-Length: {response.headers.get('content-length')} bytes")
    return response.status_code == 200

def main():
    """Run all tests."""
    print("=" * 60)
    print("SIAD Command Center API Test Suite")
    print("=" * 60)

    tests = [
        test_health,
        test_aoi_metadata,
        test_months,
        test_hotspots,
        test_tile_detail,
        test_tile_assets,
        test_static_files
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((test.__name__, False))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
