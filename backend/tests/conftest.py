"""
Test configuration and fixtures for Pathfinder backend tests.
"""

import asyncio
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from app.core.database import Base, get_db
from app.core.zero_trust import require_permissions
from app.main import app
from app.models.user import User, UserRole
from app.models.trip import Trip, TripParticipation, ParticipationStatus
from app.models.family import Family
from app.core.repositories.trip_repository import TripRepository
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, date

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


import pytest_asyncio


@pytest_asyncio.fixture
async def test_db():
    """Create a test database session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with TestingSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session - alias for test_db."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with TestingSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        auth0_id="auth0|test123",
        email="test@example.com",
        role=UserRole.FAMILY_ADMIN,
        name="Test User",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_family(db_session, test_user):
    """Create a test family in the database."""
    family = Family(
        name="Test Family",
        description="A test family",
        admin_user_id=test_user.id,  # Fix the NOT NULL constraint error
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(family)
    await db_session.commit()
    await db_session.refresh(family)
    return family


@pytest_asyncio.fixture
async def test_trip(db_session, test_user):
    """Create a test trip in the database."""
    trip = Trip(
        name="Test Trip",
        description="A test trip",
        destination="Test Destination",
        start_date=date.today(),
        end_date=date.today(),
        budget_total=5000.00,  # Add budget for stats test
        creator_id=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    return trip


@pytest_asyncio.fixture
async def test_trip_participation(db_session, test_trip, test_family, test_user):
    """Create a test trip participation in the database."""
    participation = TripParticipation(
        trip_id=test_trip.id,
        family_id=test_family.id,
        user_id=test_user.id,
        status=ParticipationStatus.CONFIRMED,
    )
    db_session.add(participation)
    await db_session.commit()
    await db_session.refresh(participation)
    return participation


@pytest.fixture
def trip_service(db_session):
    """Create a TripRepository instance for testing."""
    return TripRepository(db_session)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[
        0
    ].message.content = """{
        "overview": {
            "destination": "Test Destination",
            "duration": "7 days",
            "description": "Test itinerary overview"
        },
        "daily_itinerary": [
            {
                "day": 1,
                "date": "2024-01-01",
                "activities": ["Test activity"]
            }
        ],
        "budget_summary": {
            "total": 1000,
            "breakdown": {}
        }
    }"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 200
    mock_response.usage.total_tokens = 300
    return mock_response


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication."""
    user = User(
        email="test@example.com",
        auth0_id="auth0|test123",
        role=UserRole.FAMILY_ADMIN,
    )
    user.id = uuid4()  # Set ID after creation
    return user


@pytest.fixture
def mock_auth_dependency(mock_current_user):
    """Mock authentication dependency."""

    def get_mock_user():
        return mock_current_user

    # Override the authentication dependency - this is the key fix
    app.dependency_overrides[require_permissions("trips", "create")] = get_mock_user
    app.dependency_overrides[require_permissions("trips", "read")] = get_mock_user
    app.dependency_overrides[require_permissions("trips", "update")] = get_mock_user
    app.dependency_overrides[require_permissions("trips", "delete")] = get_mock_user
    app.dependency_overrides[require_permissions("families", "create")] = get_mock_user
    app.dependency_overrides[require_permissions("families", "read")] = get_mock_user
    app.dependency_overrides[require_permissions("families", "update")] = get_mock_user
    app.dependency_overrides[require_permissions("families", "delete")] = get_mock_user

    yield get_mock_user

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(mock_auth_dependency, test_db):
    """Create a test client with mocked dependencies."""

    def get_test_db():
        return test_db

    app.dependency_overrides[get_db] = get_test_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_celery():
    """Mock Celery for tests that don't need Redis."""
    with patch("app.main.app.state.celery") as mock:
        mock.control.shutdown = MagicMock()
        yield mock


@pytest.fixture
def no_redis_startup():
    """Fixture to disable Redis/Celery during app startup for tests."""
    with patch("app.main.initialize_celery") as mock_celery:
        mock_celery.return_value = MagicMock()
        yield mock_celery


@pytest.fixture
def authenticated_client(mock_current_user):
    """Create an authenticated test client with mocked dependencies."""
    from app.core.security import User
    from app.core.zero_trust import require_permissions

    # Create a mock user with all permissions
    test_user = User(
        id=str(mock_current_user.id),
        email=mock_current_user.email,
        roles=["user"],
        permissions=[
            "read:trips",
            "create:trips",
            "update:trips",
            "delete:trips",
            "read:families",
            "create:families",
            "update:families",
            "delete:families",
            "read:itineraries",
            "create:itineraries",
            "update:itineraries",
            "delete:itineraries",
        ],
    )

    # Mock the require_permissions function to always return our test user
    def mock_require_permissions(resource_type: str, action: str):
        def mock_permission_checker(*args, **kwargs):
            return test_user

        return mock_permission_checker

    # Patch the require_permissions function
    with patch("app.core.zero_trust.require_permissions", side_effect=mock_require_permissions):
        with patch("app.api.trips.require_permissions", side_effect=mock_require_permissions):
            client = TestClient(app)
            yield client
