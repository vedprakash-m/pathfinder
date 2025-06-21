#!/usr/bin/env python3
"""Debug script to test database table creation in test environment."""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_db_setup():
    """Test database setup similar to how pytest fixtures work."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.pool import NullPool
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base
    from sqlalchemy import text

    # Same config as test conftest.py
    TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

    print("Creating engine...")
    engine = create_async_engine(
        TEST_DB_URL,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
        echo=True,  # Enable echo to see SQL
    )

    print("Importing models...")
    # Ensure all models are imported before creating tables
    from app.models.user import User
    from app.models.family import Family, FamilyMember
    from app.models.trip import Trip, TripParticipation
    from app.models.notification import Notification
    from app.models.reservation import Reservation, ReservationDocument
    from app.models.itinerary import Itinerary, ItineraryDay, ItineraryActivity

    print("Creating tables...")
    # Create all tables
    async with engine.begin() as conn:
        # Enable foreign keys for SQLite
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        print("Running create_all...")
        await conn.run_sync(Base.metadata.create_all)

    print("Testing table creation with session...")
    # Test creating a session and checking tables
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Testing user creation...")
        user = User(
            email="test@example.com",
            auth0_id="auth0|test123456",
            name="Test User",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print("User created successfully!")

        # Test reading
        result = await session.execute(text("SELECT * FROM users"))
        rows = result.fetchall()
        print(f"Found {len(rows)} users in database")

    await engine.dispose()
    print("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_db_setup())
