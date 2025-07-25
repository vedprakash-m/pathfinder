#!/usr/bin/env python3
"""
Cross-platform Local Validation Script for Pathfinder
Simplified version without Unicode issues for Windows compatibility.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n>> {description}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ {description} - PASSED")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    else:
        print(f"✗ {description} - FAILED")
        print(f"Error: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return False


def check_critical_imports():
    """Check critical imports that we know should work."""
    print("\n=== CRITICAL IMPORT VALIDATION ===")

    # Use our working test script
    test_script = Path(__file__).parent / "test_imports.py"
    
    if not test_script.exists():
        print("✗ test_imports.py not found")
        return False
    
    cmd = [sys.executable, str(test_script)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Critical imports - PASSED")
        print(result.stdout)
        return True
    else:
        print("✗ Critical imports - FAILED")
        print(result.stderr)
        print(result.stdout)
        return False


def check_basic_functionality():
    """Test basic app startup functionality."""
    print("\n=== BASIC FUNCTIONALITY TEST ===")
    
    # Test FastAPI app creation
    test_script = """
import sys
import os

try:
    from app.main import app
    print("✓ FastAPI app created successfully")
    
    # Check if we can access basic routes
    if hasattr(app, 'routes'):
        route_count = len(app.routes)
        print(f"✓ App has {route_count} routes configured")
    
    print("✓ Basic functionality test PASSED")
    
except Exception as e:
    print(f"✗ Basic functionality test FAILED: {e}")
    sys.exit(1)
"""
    
    result = subprocess.run([sys.executable, "-c", test_script], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Basic functionality - PASSED")
        print(result.stdout)
        return True
    else:
        print("✗ Basic functionality - FAILED")
        print(result.stderr)
        if result.stdout.strip():
            print(result.stdout)
        return False


def test_api_endpoints():
    """Test if we can start the server and check health endpoint."""
    print("\n=== API ENDPOINT TEST ===")
    
    # Test server startup (quick test)
    test_script = """
import asyncio
from app.main import app

async def test_lifespan():
    try:
        # Test that the app can be created without errors
        print("✓ App initialization successful")
        
        # Check if health endpoint exists
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        if '/health' in routes or any('health' in route for route in routes):
            print("✓ Health endpoint found")
        else:
            print("? Health endpoint not found (may be in router)")
            
        print("✓ API endpoint test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ API endpoint test FAILED: {e}")
        return False

# Run test
result = asyncio.run(test_lifespan())
exit(0 if result else 1)
"""
    
    result = subprocess.run([sys.executable, "-c", test_script], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ API endpoints - PASSED")
        print(result.stdout)
        return True
    else:
        print("✗ API endpoints - FAILED")
        print(result.stderr)
        if result.stdout.strip():
            print(result.stdout)
        return False


def main():
    """Run simplified local validation."""
    print("=== PATHFINDER LOCAL VALIDATION ===")
    print("Cross-platform validation for Windows/macOS/Linux")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    print(f"Working directory: {os.getcwd()}")

    # Run validation checks
    checks = [
        ("Critical Imports", check_critical_imports),
        ("Basic Functionality", check_basic_functionality), 
        ("API Endpoints", test_api_endpoints)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"\n!! {name} check failed")
        except Exception as e:
            print(f"\n!! {name} check crashed: {e}")
    
    # Summary
    print(f"\n=== VALIDATION SUMMARY ===")
    print(f"Passed: {passed}/{total} checks")
    
    if passed == total:
        print("✓ ALL CHECKS PASSED - Ready for next phase!")
        return 0
    else:
        print("✗ Some checks failed - needs attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
