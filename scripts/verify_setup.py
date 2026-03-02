#!/usr/bin/env python3
"""Verify SIAD setup on a new machine

Checks:
1. Python environment and dependencies
2. Google Cloud credentials
3. Model imports
4. Data access (GCS)
"""

import sys
from pathlib import Path

def check_python_version():
    """Verify Python version"""
    print("1. Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python {version.major}.{version.minor}.{version.micro} (expected 3.9+)")
        return False

def check_dependencies():
    """Verify key dependencies are installed"""
    print("\n2. Checking dependencies...")
    deps = {
        "torch": "PyTorch",
        "google.cloud.storage": "Google Cloud Storage",
        "ee": "Earth Engine API",
    }

    all_ok = True
    for module, name in deps.items():
        try:
            __import__(module)
            print(f"   ✓ {name}")
        except ImportError:
            print(f"   ✗ {name} not found")
            all_ok = False

    return all_ok

def check_model_imports():
    """Verify SIAD model can be imported"""
    print("\n3. Checking SIAD model imports...")
    try:
        from siad.model import WorldModel, create_world_model_from_config
        print("   ✓ WorldModel imported successfully")

        # Test instantiation
        model = WorldModel(in_channels=8, latent_dim=512, action_dim=1)
        print(f"   ✓ WorldModel instantiated (parameters: {sum(p.numel() for p in model.parameters()):,})")
        return True
    except Exception as e:
        print(f"   ✗ Model import failed: {e}")
        return False

def check_gcp_credentials():
    """Verify Google Cloud credentials"""
    print("\n4. Checking Google Cloud credentials...")
    import os

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not project:
        print("   ✗ GOOGLE_CLOUD_PROJECT not set")
        return False
    else:
        print(f"   ✓ GOOGLE_CLOUD_PROJECT={project}")

    # Check credentials
    try:
        from google.cloud import storage
        client = storage.Client(project=project)
        print(f"   ✓ GCS client initialized")
        return True
    except Exception as e:
        print(f"   ✗ GCS authentication failed: {e}")
        print("   → Run: gcloud auth application-default login")
        return False

def check_data_access():
    """Verify can access GCS bucket"""
    print("\n5. Checking data access...")
    import os

    try:
        from google.cloud import storage
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "siad-earth-engine")
        client = storage.Client(project=project)

        # Try to list buckets
        buckets = list(client.list_buckets(max_results=5))
        print(f"   ✓ Can access GCS (found {len(buckets)} buckets)")

        # Check for SIAD bucket (warning only, not a failure)
        bucket_name = "siad-training-data"
        try:
            bucket = client.bucket(bucket_name)
            if bucket.exists():
                print(f"   ✓ SIAD bucket '{bucket_name}' exists")
            else:
                print(f"   ℹ SIAD bucket '{bucket_name}' not found (run data export if needed)")
        except:
            print(f"   ℹ Cannot check bucket '{bucket_name}' (not critical)")

        return True
    except Exception as e:
        print(f"   ✗ Data access failed: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("SIAD Setup Verification")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_model_imports(),
        check_gcp_credentials(),
        check_data_access(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("✓ All checks passed! SIAD is ready to use.")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
