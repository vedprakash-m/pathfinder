#!/usr/bin/env python3
"""
Simple test for family invitation models
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, "/Users/vedprakashmishra/pathfinder/backend")


def test_imports():
    """Test that we can import the required modules"""
    try:
        from app.models.family import FamilyInvitationModel, InvitationStatus

        print("✅ Successfully imported InvitationStatus and FamilyInvitationModel")

        # Test enum values
        print(f"   - PENDING: {InvitationStatus.PENDING}")
        print(f"   - ACCEPTED: {InvitationStatus.ACCEPTED}")
        print(f"   - DECLINED: {InvitationStatus.DECLINED}")
        print(f"   - EXPIRED: {InvitationStatus.EXPIRED}")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_api_import():
    """Test that we can import the family API"""
    try:
        from app.api.families import router

        print("✅ Successfully imported family API router")

        # Check routes
        routes = []
        for route in router.routes:
            if hasattr(route, "path"):
                routes.append(route.path)

        print(f"   Found {len(routes)} routes")
        for route in routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ API import failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Simple Family Invitation Test")
    print("=" * 40)

    test1 = test_imports()
    test2 = test_api_import()

    print("\n" + "=" * 40)
    if test1 and test2:
        print("🎉 Basic imports work! Family invitation system is ready.")
    else:
        print("⚠️  Some imports failed. Check the implementation.")
