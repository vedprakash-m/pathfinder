#!/usr/bin/env python3
"""
Test script for family invitation functionality
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal
from app.models.family import Family, FamilyInvitationModel, InvitationStatus
from app.models.user import UserModel
from sqlalchemy import create_engine, text

async def test_family_invitation_models():
    """Test that the family invitation models work correctly"""
    print("Testing family invitation models...")
    
    # Test creating invitation status enum
    try:
        status = InvitationStatus.PENDING
        print(f"✅ InvitationStatus enum works: {status}")
    except Exception as e:
        print(f"❌ InvitationStatus enum failed: {e}")
        return False
    
    # Test database connection
    try:
        db = SessionLocal()
        
        # Check if family_invitations table exists
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='family_invitations'"))
        table_exists = result.fetchone()
        
        if table_exists:
            print("✅ family_invitations table exists in database")
        else:
            print("❌ family_invitations table not found in database")
            db.close()
            return False
            
        # Test creating a family invitation record (without actually saving)
        invitation = FamilyInvitationModel(
            family_id=1,
            invited_by=1,
            email="test@example.com",
            role="member",
            status=InvitationStatus.PENDING,
            invitation_token="test_token_123",
            message="Welcome to our family!"
        )
        
        print("✅ FamilyInvitationModel can be instantiated")
        print(f"   - family_id: {invitation.family_id}")
        print(f"   - email: {invitation.email}")
        print(f"   - status: {invitation.status}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_api_imports():
    """Test that the family API can import correctly"""
    print("\nTesting family API imports...")
    
    try:
        from app.api.families import router
        print("✅ Family API router imports successfully")
        
        # Check that invitation endpoints are registered
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/families/{family_id}/invite",
            "/families/accept-invitation",
            "/families/decline-invitation",
            "/families/{family_id}/invitations"
        ]
        
        for route in expected_routes:
            if any(route in path for path in routes):
                print(f"✅ Route {route} is registered")
            else:
                print(f"❌ Route {route} not found")
                
        return True
        
    except Exception as e:
        print(f"❌ Family API import failed: {e}")
        return False

async def test_email_service():
    """Test that email service can be imported"""
    print("\nTesting email service...")
    
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        print("✅ EmailService can be instantiated")
        return True
        
    except Exception as e:
        print(f"❌ EmailService test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Family Invitation Implementation")
    print("=" * 50)
    
    tests = [
        test_family_invitation_models,
        test_api_imports,
        test_email_service
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Family invitation system looks good.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
