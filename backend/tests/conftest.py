"""Pytest configuration for backend tests."""
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

# Set test environment variables before importing modules
os.environ.setdefault("COSMOS_DB_URL", "https://localhost:8081")
os.environ.setdefault("COSMOS_DB_KEY", "test-key")
os.environ.setdefault("COSMOS_DB_NAME", "pathfinder")
os.environ.setdefault(
    "SIGNALR_CONNECTION_STRING", "Endpoint=https://test.service.signalr.net;AccessKey=test;Version=1.0;"
)
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_MODEL", "gpt-5-mini")
os.environ.setdefault("ENTRA_TENANT_ID", "test-tenant")
os.environ.setdefault("ENTRA_CLIENT_ID", "test-client")
os.environ.setdefault(
    "AZURE_STORAGE_CONNECTION_STRING",
    "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net",
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_cosmos_container():
    """Create a mock Cosmos DB container."""
    container = AsyncMock()
    container.create_item = AsyncMock()
    container.read_item = AsyncMock()
    container.query_items = MagicMock()
    container.replace_item = AsyncMock()
    container.upsert_item = AsyncMock()
    container.delete_item = AsyncMock()
    return container


@pytest.fixture
def mock_cosmos_client(mock_cosmos_container):
    """Create a mock Cosmos DB client."""
    database = MagicMock()
    database.get_container_client.return_value = mock_cosmos_container

    client = MagicMock()
    client.get_database_client.return_value = database
    return client


@pytest.fixture
def mock_signalr_client():
    """Create a mock SignalR client."""
    client = AsyncMock()
    client.send_to_user = AsyncMock()
    client.send_to_group = AsyncMock()
    client.add_user_to_group = AsyncMock()
    return client


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="Test response"))]
    completion.usage = MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150)

    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=completion)
    return client


@pytest.fixture
def sample_user():
    """Create a sample user document."""
    return {
        "id": "user_123",
        "pk": "user_123",
        "entity_type": "user",
        "email": "test@example.com",
        "display_name": "Test User",
        "family_ids": ["family_1"],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_family():
    """Create a sample family document."""
    return {
        "id": "family_123",
        "pk": "family_123",
        "entity_type": "family",
        "name": "Test Family",
        "owner_id": "user_123",
        "member_ids": ["user_123"],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_trip():
    """Create a sample trip document."""
    return {
        "id": "trip_123",
        "pk": "trip_123",
        "entity_type": "trip",
        "name": "Test Trip",
        "destination": "Hawaii",
        "start_date": "2024-07-01",
        "end_date": "2024-07-14",
        "family_ids": ["family_123"],
        "created_by": "user_123",
        "status": "planning",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_poll():
    """Create a sample poll document."""
    return {
        "id": "poll_123",
        "pk": "trip_123",
        "entity_type": "poll",
        "trip_id": "trip_123",
        "question": "Where should we have dinner?",
        "options": [
            {"id": "opt_1", "text": "Italian", "votes": []},
            {"id": "opt_2", "text": "Japanese", "votes": []},
        ],
        "created_by": "user_123",
        "status": "open",
        "expires_at": "2024-07-01T18:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def auth_headers():
    """Create sample authorization headers."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json",
    }
