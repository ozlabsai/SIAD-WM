#!/usr/bin/env python3
"""Test API endpoints using TestClient"""

import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.main import app, startup_event


async def init_app():
    """Initialize the app"""
    await startup_event()


def test_endpoints():
    """Test the endpoints"""

    # Initialize app
    asyncio.run(init_app())

    # Create test client
    client = TestClient(app)

    print("Testing API Endpoints...")
    print("=" * 60)

    # Test 1: Health check
    print("\n1. Testing /health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data}")
        print("   ✓ Health check passed")
    else:
        print(f"   ✗ Failed: {response.text}")
        return False

    # Test 2: Get hotspots
    print("\n2. Testing /api/detect/hotspots endpoint...")
    response = client.get("/api/detect/hotspots?min_score=0.5&limit=10")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total hotspots: {data['total']}")
        print(f"   Returned: {len(data['hotspots'])}")
        print(f"   Source: {data['filters_applied']['source']}")
        if data['hotspots']:
            print(f"   Top hotspot: {data['hotspots'][0]['tile_id']} (score={data['hotspots'][0]['score']:.3f})")
        print("   ✓ Hotspots endpoint passed")
    else:
        print(f"   ✗ Failed: {response.text}")
        return False

    # Test 3: Get tile detail
    print("\n3. Testing /api/detect/tile/tile_x000_y000 endpoint...")
    response = client.get("/api/detect/tile/tile_x000_y000")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Tile ID: {data['tileId']}")
        print(f"   Region: {data['region']}")
        print(f"   Score: {data['score']:.3f}")
        print(f"   Onset: {data['onset']}")
        print(f"   Coordinates: ({data['coordinates']['lat']:.4f}, {data['coordinates']['lon']:.4f})")
        print(f"   Heatmap shape: {len(data['heatmapData'])}×{len(data['heatmapData'][0])}")
        print(f"   Timeline entries: {len(data['timelineData'])}")
        print(f"   Baseline data keys: {list(data['baselineData'].keys())}")
        print("   ✓ Tile detail endpoint passed")
    else:
        print(f"   ✗ Failed: {response.text}")
        return False

    # Test 4: Get tile detail for another tile
    print("\n4. Testing /api/detect/tile/tile_x000_y001 endpoint...")
    response = client.get("/api/detect/tile/tile_x000_y001")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Region: {data['region']}")
        print(f"   Score: {data['score']:.3f}")
        print("   ✓ Second tile detail passed")
    else:
        print(f"   ✗ Failed: {response.text}")
        return False

    # Test 5: Get non-existent tile (should return 404 or mock data)
    print("\n5. Testing /api/detect/tile/tile_x999_y999 endpoint...")
    response = client.get("/api/detect/tile/tile_x999_y999")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        # Mock data fallback
        data = response.json()
        print(f"   Returned mock data for: {data['tileId']}")
        print("   ✓ Mock data fallback working")
    elif response.status_code == 404:
        print("   ✓ Correctly returns 404 for missing tile")
    else:
        print(f"   ✗ Unexpected status: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ All endpoint tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_endpoints()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
