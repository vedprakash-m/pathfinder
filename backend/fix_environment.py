#!/usr/bin/env python3
"""
Environment Fix Script for Binary Compatibility Issues

This script fixes common binary compatibility issues found in CI/CD environments,
specifically the pandas/numpy version mismatch that prevents app.main from importing.
"""

import os
import subprocess
import sys


def run_command(cmd, description, ignore_errors=False):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 or ignore_errors:
        print(f"✅ {description} - COMPLETED")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    else:
        print(f"❌ {description} - FAILED")
        print(f"Error: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return False


def fix_numpy_pandas_compatibility():
    """Fix numpy/pandas binary compatibility issues."""
    print("🔧 Fixing numpy/pandas binary compatibility...")

    # Uninstall problematic packages
    run_command(
        ["pip", "uninstall", "-y", "pandas", "numpy"],
        "Uninstalling pandas and numpy",
        ignore_errors=True,
    )

    # Upgrade pip
    run_command(["pip", "install", "--upgrade", "pip"], "Upgrading pip")

    # Install compatible versions
    run_command(["pip", "install", "numpy==1.24.3"], "Installing compatible numpy")

    run_command(["pip", "install", "pandas==2.0.3"], "Installing compatible pandas")

    # Test the fix
    result = subprocess.run(
        [
            "python3",
            "-c",
            "import pandas as pd; import numpy as np; print(f'✅ pandas {pd.__version__}, numpy {np.__version__}')",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ Binary compatibility fixed!")
        print(result.stdout)
        return True
    else:
        print("❌ Binary compatibility still broken")
        print(result.stderr)
        return False


def reinstall_all_dependencies():
    """Reinstall all dependencies to ensure compatibility."""
    print("🔄 Reinstalling all dependencies...")

    # Read requirements
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False

    # Force reinstall all requirements
    run_command(
        ["pip", "install", "--force-reinstall", "--no-cache-dir", "-r", "requirements.txt"],
        "Force reinstalling all requirements",
    )

    return True


def main():
    """Run environment fixes."""
    print("🔧 Environment Compatibility Fix Script")
    print("=" * 50)

    # Change to backend directory
    backend_dir = "/Users/vedprakashmishra/pathfinder/backend"
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found: {backend_dir}")
        return 1

    os.chdir(backend_dir)
    print(f"Working in: {backend_dir}")

    # Fix numpy/pandas compatibility
    if not fix_numpy_pandas_compatibility():
        print("⚠️ Binary compatibility fix failed, trying full reinstall...")
        if not reinstall_all_dependencies():
            print("❌ Full reinstall failed")
            return 1

    # Test critical imports after fix
    print("\n🧪 Testing critical imports after fix...")

    critical_modules = [
        "app.api.feedback",
        "app.api.trips",
        "app.core.dependencies",
        "app.main",  # This should work now
    ]

    failed = []
    for module_name in critical_modules:
        result = subprocess.run(
            ["python3", "-c", f"import {module_name}; print('✅ {module_name}: OK')"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"✅ {module_name}: OK")
        else:
            print(f"❌ {module_name}: FAILED")
            failed.append(module_name)

    if not failed:
        print("\n🎉 All environment fixes successful!")
        print("✅ Ready for local validation")
        return 0
    else:
        print(f"\n❌ {len(failed)} modules still failing:")
        for module in failed:
            print(f"  - {module}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
