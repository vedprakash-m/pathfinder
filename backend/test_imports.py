#!/usr/bin/env python3
"""
Simple import test script to validate basic dependencies and app imports.
"""

print("🔍 Testing Python Environment and Dependencies...")

# Test 1: Basic Python environment
try:
    import sys
    print(f"✅ Python version: {sys.version}")
except Exception as e:
    print(f"❌ Python environment issue: {e}")
    sys.exit(1)

# Test 2: Core dependencies
dependencies = [
    "pydantic",
    "pydantic_settings", 
    "fastapi",
    "uvicorn"
]

for dep in dependencies:
    try:
        __import__(dep)
        print(f"✅ {dep}: OK")
    except ImportError as e:
        print(f"❌ {dep}: MISSING - {e}")
    except Exception as e:
        print(f"⚠️  {dep}: ERROR - {e}")

# Test 3: Application imports
print("\n🔍 Testing Application Imports...")

app_imports = [
    "app.core.config",
    "app.main"
]

for imp in app_imports:
    try:
        __import__(imp)
        print(f"✅ {imp}: OK")
    except ImportError as e:
        print(f"❌ {imp}: IMPORT ERROR - {e}")
    except Exception as e:
        print(f"⚠️  {imp}: RUNTIME ERROR - {e}")

print("\n✨ Import validation complete!")
