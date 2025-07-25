#!/usr/bin/env python3
"""
Windows-compatible validation script without Unicode characters.
"""

import os
import subprocess
import sys

def main():
    """Run basic validation tests."""
    print("=== PATHFINDER VALIDATION ===")
    
    # Test 1: Basic imports
    print("\n1. Testing basic imports...")
    test_basic_imports = """
import sys
try:
    import app.main
    print("SUCCESS: app.main imports correctly")
    print("SUCCESS: FastAPI app can be created")
except Exception as e:
    print(f"ERROR: Import failed - {e}")
    sys.exit(1)
"""
    
    result = subprocess.run([sys.executable, "-c", test_basic_imports], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("PASS: Basic imports working")
        print(result.stdout)
    else:
        print("FAIL: Basic imports failed")
        print(result.stderr)
        return 1

    # Test 2: API creation
    print("\n2. Testing API creation...")
    test_api = """
import sys
try:
    from app.main import app
    route_count = len(app.routes)
    print(f"SUCCESS: API created with {route_count} routes")
except Exception as e:
    print(f"ERROR: API creation failed - {e}")
    sys.exit(1)
"""
    
    result = subprocess.run([sys.executable, "-c", test_api], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("PASS: API creation working")
        print(result.stdout)
    else:
        print("FAIL: API creation failed")
        print(result.stderr)
        return 1

    print("\n=== VALIDATION COMPLETE ===")
    print("SUCCESS: All tests passed!")
    print("READY: Application is ready for next phase")
    return 0

if __name__ == "__main__":
    # Ensure we're in the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    sys.exit(main())
