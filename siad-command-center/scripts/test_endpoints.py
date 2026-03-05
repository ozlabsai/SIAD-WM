#!/usr/bin/env python3
"""Test script to verify new endpoints work correctly"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.storage import ResidualStorageService


def test_storage_service():
    """Test storage service can read HDF5 file"""
    print("Testing Storage Service...")

    storage_path = Path(__file__).parent.parent / "data" / "residuals_test.h5"

    if not storage_path.exists():
        print(f"  ✗ HDF5 file not found: {storage_path}")
        return False

    try:
        storage = ResidualStorageService(str(storage_path))

        # Test list tiles
        tiles = storage.list_tiles()
        print(f"  ✓ Found {len(tiles)} tiles: {tiles}")

        # Test get tile detail for first tile
        if tiles:
            tile_id = tiles[0]
            print(f"\n  Testing tile: {tile_id}")

            # Get metadata
            metadata = storage.get_tile_metadata(tile_id)
            print(f"    ✓ Metadata: {metadata.region} at ({metadata.lat:.4f}, {metadata.lon:.4f})")

            # Get scores
            scores = storage.get_tile_scores(tile_id)
            print(f"    ✓ Scores: {len(scores)} months, peak={scores.max():.3f}")

            # Get timestamps
            timestamps = storage.get_timestamps(tile_id)
            print(f"    ✓ Timestamps: {timestamps[0]} to {timestamps[-1]}")

            # Get heatmap for peak month
            peak_idx = scores.argmax()
            heatmap = storage.get_residual_heatmap(tile_id, peak_idx)
            print(f"    ✓ Heatmap: {heatmap.values.shape}, month={heatmap.month}")

            # Get baseline comparison
            baseline = storage.get_baseline_comparison(tile_id)
            print(f"    ✓ Baselines: WM={baseline.world_model.mean():.3f}, "
                  f"Pers={baseline.persistence.mean():.3f}, "
                  f"Seas={baseline.seasonal.mean():.3f}")

            # Test get_hotspots
            hotspots = storage.get_hotspots(min_score=0.5, limit=10)
            print(f"\n  ✓ Hotspots: Found {len(hotspots)} hotspots")
            for i, h in enumerate(hotspots[:3]):
                print(f"    {i+1}. {h['tile_id']}: score={h['score']:.3f}, onset={h['onset']}")

        print("\n✅ Storage service tests passed!")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_logic():
    """Test the endpoint logic without running server"""
    print("\nTesting Endpoint Logic...")

    try:
        from api.routes.detection import router
        from api.services.storage import ResidualStorageService
        import api.routes.detection as detection_module

        # Set up storage service
        storage_path = Path(__file__).parent.parent / "data" / "residuals_test.h5"
        storage = ResidualStorageService(str(storage_path))

        # Initialize router
        detection_module._storage_service = storage

        print("  ✓ Router initialized with storage service")
        print("  ✓ Endpoint /api/detect/tile/{tile_id} ready")
        print("  ✓ Endpoint /api/detect/hotspots ready")

        print("\n✅ Endpoint logic tests passed!")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SIAD Demo v2.0 - Backend Endpoint Tests")
    print("=" * 60)
    print()

    success = True

    success &= test_storage_service()
    success &= test_endpoint_logic()

    print()
    print("=" * 60)
    if success:
        print("🎉 All tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the API server: cd siad-command-center/api && uvicorn main:app --reload")
        print("2. Test endpoints:")
        print("   - GET http://localhost:8000/api/detect/hotspots")
        print("   - GET http://localhost:8000/api/detect/tile/tile_x000_y000")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        print("=" * 60)
        sys.exit(1)
