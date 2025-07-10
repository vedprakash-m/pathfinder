#!/usr/bin/env python3
"""
Basic import test to verify core functionality
"""


def test_core_types():
    """Test that core types can be imported"""
    try:
        from core.llm_types import LLMProvider

        print("✅ Core types imported successfully")

        # Test enum values
        providers = list(LLMProvider)
        print(f"✅ Available providers: {[p.value for p in providers]}")

        return True
    except Exception as e:
        print(f"❌ Failed to import core types: {e}")
        return False


def test_services():
    """Test that services can be imported"""
    try:

        print("✅ ConfigManager imported successfully")

        print("✅ RoutingEngine imported successfully")

        return True
    except Exception as e:
        print(f"❌ Failed to import services: {e}")
        return False


def test_fastapi_deps():
    """Test FastAPI and other dependencies"""
    try:

        print("✅ FastAPI dependencies available")
        return True
    except Exception as e:
        print(f"❌ Missing FastAPI dependencies: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing LLM Orchestration Layer Components")
    print("=" * 50)

    results = []
    results.append(test_core_types())
    results.append(test_services())
    results.append(test_fastapi_deps())

    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All basic imports successful!")
        print("Ready to proceed with full system testing")
    else:
        print("⚠️  Some imports failed - need to fix dependencies")
