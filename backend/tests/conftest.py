"""
Test configuration and fixtures for Pathfinder backend tests.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from app.core.database import Base, get_db
from app.core.zero_trust import require_permissions
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
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


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication."""
    return User(
        id="test-user-123",
        email="test@example.com",
        auth0_id="auth0|test123",
        role="user",
        family_id="test-family-456",
    )


@pytest.fixture
def mock_auth_dependency(mock_current_user):
    """Mock authentication dependency."""

    def get_mock_user():
        return mock_current_user

    # Override the authentication dependency
    app.dependency_overrides[require_permissions("trips", "create")] = get_mock_user
    app.dependency_overrides[require_permissions("trips", "read")] = get_mock_user
    app.dependency_overrides[require_permissions("trips", "update")] = get_mock_user
    app.dependency_overrides[require_permissions("trips", "delete")] = get_mock_user

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
