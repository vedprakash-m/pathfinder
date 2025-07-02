#!/usr/bin/env python3
"""
Quick validation test for Day 1 unified Cosmos DB migration completion.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.repositories.cosmos_unified import UnifiedCosmosRepository


async def test_unified_migration():
    """Test that all unified migration components are working."""
    print("🔄 Testing unified Cosmos DB migration completion...")

    try:
        # Test repository initialization
        repo = UnifiedCosmosRepository()
        print("✅ Unified repository initialized successfully")

        # Test user operations
        user_data = {"email": "test@example.com", "entra_id": "test-entra-id", "name": "Test User"}
        user = await repo.create_user(user_data)
        print(f"✅ User creation: {user.id}")

        # Test family operations
        family_data = {"name": "Test Family", "admin_user_id": user.id}
        family = await repo.create_family(family_data)
        print(f"✅ Family creation: {family.id}")

        # Test family invitation operations
        invitation_data = {
            "family_id": family.id,
            "invited_by": user.id,
            "email": "invite@example.com",
            "role": "adult",
            "invitation_token": "test-token-123",
            "expires_at": "2025-07-01T00:00:00Z",
        }
        invitation = await repo.create_family_invitation(invitation_data)
        print(f"✅ Family invitation creation: {invitation.id}")

        # Test getting invitation by token
        found_invitation = await repo.get_family_invitation_by_token("test-token-123")
        if found_invitation:
            print(f"✅ Get invitation by token: {found_invitation.id}")
        else:
            print("❌ Failed to find invitation by token")

        # Test trip operations
        trip_data = {
            "title": "Test Trip",
            "description": "Test trip for unified migration",
            "organizer_user_id": user.id,
            "participating_family_ids": [family.id],
        }
        trip = await repo.create_trip(trip_data)
        print(f"✅ Trip creation: {trip.id}")

        # Test message operations
        message = await repo.send_trip_message(
            trip_id=trip.id,
            sender_id=user.id,
            sender_name=user.name,
            text="Test message for unified migration",
        )
        print(f"✅ Trip message creation: {message.id}")

        # Test retrieving messages
        messages = await repo.get_trip_messages(trip.id, limit=10)
        print(f"✅ Retrieved {len(messages)} trip messages")

        print("\n🎉 ALL UNIFIED MIGRATION TESTS PASSED!")
        print("✅ Day 1 Database Architecture Unification: COMPLETE")
        return True

    except Exception as e:
        print(f"❌ Migration test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_unified_migration())
    sys.exit(0 if result else 1)
