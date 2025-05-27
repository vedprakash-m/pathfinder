"""
Test configuration and fixtures for the Pathfinder backend.
"""
import asyncio
import os
import pytest
import pytest_asyncio
import json
from typing import AsyncGenerator, Dict
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Set test environment variables before any imports
import os
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["DISABLE_TELEMETRY"] = "true"

# Load test environment file
import dotenv
dotenv.load_dotenv("/Users/vedprakashmishra/pathfinder/backend/.env.test")

# Import models and app modules
from app.core.database import Base, get_db
# Import ALL models to ensure they're registered with Base metadata
from app.models.trip import Trip, TripParticipation, TripStatus, ParticipationStatus
from app.models.family import Family
from app.models.user import User
from app.models.notification import Notification
from app.models.reservation import Reservation
from app.models.itinerary import Itinerary  # Add missing model
from app.services.trip_service import TripService

# Test settings
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import StaticPool
    from sqlalchemy import event
    
    engine = create_async_engine(
        TEST_DB_URL, 
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False
        },
        echo=False  # Disable echo during table creation
    )
    
    # Ensure all models are imported before creating tables
    from app.models.user import User
    from app.models.family import Family, FamilyMember
    from app.models.trip import Trip, TripParticipation
    from app.models.notification import Notification
    from app.models.reservation import Reservation, ReservationDocument
    from app.models.itinerary import Itinerary, ItineraryDay, ItineraryActivity
    
    # Create all tables
    async with engine.begin() as conn:
        # Enable foreign keys for SQLite
        from sqlalchemy import text
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup - drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for a test."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Use async_sessionmaker to create the session
    async_session = async_sessionmaker(
        bind=db_engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    
    # Create a session and start an explicit transaction
    session = async_session()
    
    # Start a transaction that will be rolled back
    transaction = await session.begin()
    
    # Create a helper function to expire all identity map entries
    async def expire_all():
        for instance in session.identity_map.values():
            session.expire(instance)
    
    # Attach the helper function to the session
    session.expire_all = expire_all
    
    try:
        yield session
    finally:
        # Always rollback the transaction
        await transaction.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def trip_service(db_session) -> TripService:
    """Create a TripService instance for testing."""
    return TripService(db_session)


@pytest.fixture(scope="function", autouse=True)
def mock_cosmos_db_settings(monkeypatch):
    """
    Mock Cosmos DB settings to avoid connection errors during tests.
    This fixture runs automatically for all tests.
    """
    # Create a mock settings object
    mock_settings = MagicMock()
    mock_settings.COSMOS_DB_URL = 'https://mock-cosmos-url'
    mock_settings.COSMOS_DB_KEY = 'mock-key'
    mock_settings.COSMOS_DB_DATABASE = 'mock-db'
    mock_settings.COSMOS_DB_CONTAINER = 'mock-container'
    
    # Replace the get_settings function to return our mock
    monkeypatch.setattr('app.core.config.get_settings', lambda: mock_settings)


@pytest_asyncio.fixture(scope="function")
async def mock_cosmos_service():
    """Create mock Cosmos DB services with proper async behavior."""
    mock = MagicMock()
    
    # Create AsyncMock for each service
    mock.itinerary_service = AsyncMock()
    mock.message_service = AsyncMock()
    mock.preference_service = AsyncMock()
    
    # Configure the mocks to return appropriate values
    mock.itinerary_service.get_itinerary.return_value = {'id': 'mock-itinerary', 'content': {}}
    mock.itinerary_service.create_itinerary.return_value = {'id': 'new-itinerary-id'}
    
    mock.message_service.get_messages.return_value = []
    mock.message_service.create_message.return_value = {'id': 'new-message-id'}
    
    mock.preference_service.get_preferences.return_value = {}
    mock.preference_service.save_preferences.return_value = {'id': 'preferences-id'}
    
    return mock


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session) -> User:
    """Create a test user."""
    # Create user without starting a new transaction
    user = User(
        email="test@example.com",
        auth0_id="auth0|test123456",
        name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    
    # Refresh to ensure we have the latest data
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_family(db_session, test_user) -> Family:
    """Create a test family."""
    family = Family(
        name="Test Family",
        admin_user_id=test_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(family)
    await db_session.flush()
    
    # Refresh to ensure we have the latest data
    await db_session.refresh(family)
    return family


@pytest_asyncio.fixture(scope="function")
async def test_trip(db_session, test_user) -> Trip:
    """Create a test trip."""
    trip = Trip(
        name="Test Trip",
        description="A test trip for unit testing",
        destination="Test Destination",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=37),
        status=TripStatus.PLANNING,
        budget_total=5000.00,
        preferences=json.dumps({
            "accommodation_type": ["hotel"],
            "transportation_mode": ["car"],
            "activity_types": ["sightseeing", "outdoor"],
            "dining_preferences": ["local cuisine"],
            "pace": "moderate"
        }),
        is_public=False,
        creator_id=test_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(trip)
    await db_session.flush()
    
    # Refresh to ensure we have the latest data
    await db_session.refresh(trip)
    return trip


@pytest_asyncio.fixture(scope="function")
async def test_trip_participation(db_session, test_trip, test_family, test_user) -> TripParticipation:
    """Create a test trip participation."""
    participation = TripParticipation(
        trip_id=test_trip.id,
        family_id=test_family.id,
        user_id=test_user.id,
        status=ParticipationStatus.CONFIRMED,
        budget_allocation=1000.00,
        preferences=json.dumps({
            "accommodation_preference": "private_room",
            "meal_preferences": ["vegetarian"],
            "activity_interests": ["museums", "nature"]
        }),
        notes="Test participation notes",
        joined_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(participation)
    await db_session.flush()
    
    # Refresh to ensure we have the latest data
    await db_session.refresh(participation)
    return participation


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API responses with proper object structure."""
    # Create mock objects that behave like OpenAI response objects
    from unittest.mock import MagicMock
    
    # Create the mock response object
    mock_response = MagicMock()
    
    # Mock the usage object
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 80
    mock_usage.completion_tokens = 120
    mock_usage.total_tokens = 200
    mock_response.usage = mock_usage
    
    # Mock the message object
    mock_message = MagicMock()
    mock_message.role = "assistant"
    mock_message.content = json.dumps({
        "overview": {
            "destination": "Test Destination",
            "duration": 7,
            "total_participants": 4,
            "estimated_cost_per_person": 1250.0,
            "best_time_to_visit": "Summer",
            "weather_info": "Warm and sunny",
            "travel_tips": ["Pack light", "Bring sunscreen"]
        },
        "daily_itinerary": [
            {
                "day": 1,
                "date": "",
                "theme": "Arrival and Orientation",
                "activities": [
                    {
                        "time": "09:00",
                        "activity": "Airport Arrival",
                        "location": "Test Airport",
                        "description": "Arrive at airport and collect luggage",
                        "duration": "1 hour",
                        "cost_per_person": 0,
                        "booking_required": False,
                        "family_friendly": True,
                        "accessibility_notes": "Airport has wheelchair access",
                        "alternatives": []
                    }
                ],
                "meals": [],
                "accommodation": {
                    "name": "Test Hotel",
                    "type": "Hotel",
                    "cost_per_room": 200,
                    "amenities": ["WiFi", "Pool"],
                    "booking_link": ""
                },
                "daily_budget_breakdown": {
                    "activities": 0,
                    "meals": 100,
                    "accommodation": 200,
                    "transportation": 50,
                    "total": 350
                }
            }
        ],
        "budget_summary": {
            "total_estimated_cost": 1400,
            "cost_per_person": 350,
            "cost_breakdown": {
                "accommodation": 200,
                "activities": 0,
                "meals": 100,
                "transportation": 50,
                "miscellaneous": 0
            }
        }
    })
    
    # Mock the choice object
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    mock_choice.index = 0
    
    # Add choices list to response
    mock_response.choices = [mock_choice]
    
    # Add other attributes
    mock_response.id = "chatcmpl-123"
    mock_response.object = "chat.completion"
    mock_response.created = 1677858242
    mock_response.model = "gpt-4o-mini"
    
    return mock_response
