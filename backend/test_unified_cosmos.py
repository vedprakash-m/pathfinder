#!/usr/bin/env python3
"""
Test script for unified Cosmos DB implementation.
This validates that our unified approach works correctly.
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_unified_cosmos():
    """Test the unified Cosmos DB repository functionality."""
    try:
        from app.core.database_unified import get_cosmos_service

        logger.info("🚀 Testing Unified Cosmos DB Implementation")

        # Test 1: Repository Creation
        logger.info("📝 Test 1: Creating repository instance...")
        cosmos_service = get_cosmos_service()
        repo = cosmos_service.get_repository()
        logger.info("✅ Repository created successfully")

        # Test 2: Container Initialization (simulation mode)
        logger.info("📝 Test 2: Initializing container...")
        await repo.initialize_container()
        logger.info("✅ Container initialized successfully")

        # Test 3: User Operations
        logger.info("📝 Test 3: Testing user operations...")
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "role": "family_admin",
        }

        # Create user
        user_doc = await repo.create_user(user_data)
        logger.info(f"✅ User created: {user_doc.id}")

        # Get user by ID
        retrieved_user = await repo.get_user_by_id(user_doc.id)
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        logger.info("✅ User retrieval successful")

        # Test 4: Family Operations
        logger.info("📝 Test 4: Testing family operations...")
        family_data = {
            "name": "Test Family",
            "admin_user_id": user_doc.id,
            "member_ids": [user_doc.id],
        }

        family_doc = await repo.create_family(family_data)
        logger.info(f"✅ Family created: {family_doc.id}")

        # Test 5: Trip Operations
        logger.info("📝 Test 5: Testing trip operations...")
        trip_data = {
            "title": "Test Trip",
            "description": "A test trip",
            "destination": "Test Destination",
            "organizer_user_id": user_doc.id,
            "status": "planning",
        }

        trip_doc = await repo.create_trip(trip_data, user_doc.id)
        logger.info(f"✅ Trip created: {trip_doc.id}")

        # Get user trips
        user_trips = await repo.get_user_trips(user_doc.id)
        assert len(user_trips) >= 1
        logger.info(f"✅ User trips retrieved: {len(user_trips)} trips")

        # Test 6: Message Operations
        logger.info("📝 Test 6: Testing message operations...")
        message_data = {
            "trip_id": trip_doc.id,
            "user_id": user_doc.id,
            "user_name": user_doc.name or "Test User",
            "content": "Test message",
            "message_type": "text",
        }

        message_doc = await repo.create_message(message_data)
        logger.info(f"✅ Message created: {message_doc.id}")

        # Get trip messages
        trip_messages = await repo.get_trip_messages(trip_doc.id)
        assert len(trip_messages) >= 1
        logger.info(f"✅ Trip messages retrieved: {len(trip_messages)} messages")

        logger.info(
            "🎉 All tests passed! Unified Cosmos DB implementation is working correctly."
        )

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_auth_service():
    """Test the unified auth service."""
    try:
        from app.repositories.cosmos_unified import unified_cosmos_repo
        from app.services.auth_unified import UnifiedAuthService

        logger.info("🔐 Testing Unified Auth Service")

        auth_service = UnifiedAuthService(unified_cosmos_repo)

        # Test user creation through auth service using token payload
        token_payload = {
            "sub": "test-entra-id-unique-456",  # Use unique Entra ID
            "email": "completely_unique_auth_test@example.com",  # Completely unique email
            "name": "Unique Auth Test User",
            "oid": "test-entra-id-unique-456",
        }

        user = await auth_service.get_or_create_user_from_token(token_payload)
        logger.info(f"✅ User created with auto-family: {user.id}")
        logger.info(f"📧 User email: {user.email}")

        # Test user lookup
        found_user = await auth_service.get_user_by_entra_id("test-entra-id-unique-456")
        assert found_user is not None
        logger.info(f"📧 Found user email: {found_user.email}")
        assert found_user.email == "completely_unique_auth_test@example.com"
        logger.info("✅ User lookup by Entra ID successful")

        logger.info("🎉 Auth service test passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Auth service test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("UNIFIED COSMOS DB VALIDATION")
    logger.info("=" * 60)

    # Test repository
    repo_success = await test_unified_cosmos()

    # Test auth service
    auth_success = await test_auth_service()

    if repo_success and auth_success:
        logger.info("=" * 60)
        logger.info("🎉 ALL TESTS PASSED - UNIFIED COSMOS DB IS WORKING!")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("❌ SOME TESTS FAILED")
        logger.error("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
