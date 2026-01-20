"""Unit tests for CosmosRepository."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from repositories.cosmos_repository import CosmosRepository


@pytest.fixture
def mock_container():
    """Create a mock Cosmos DB container."""
    container = AsyncMock()
    return container


@pytest.fixture
def repository(mock_container):
    """Create a repository with mocked container."""
    with patch.object(CosmosRepository, "_get_instance", return_value=None):
        repo = CosmosRepository.__new__(CosmosRepository)
        repo.container = mock_container
        repo._initialized = True
        return repo


class TestCosmosRepository:
    """Test cases for CosmosRepository."""

    @pytest.mark.asyncio
    async def test_create_document(self, repository, mock_container):
        """Test creating a document."""
        mock_container.create_item = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Summer Vacation",
            }
        )

        result = await repository.create(
            {
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Summer Vacation",
            }
        )

        assert result["id"] == "trip_123"
        mock_container.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self, repository, mock_container):
        """Test getting a document by ID."""
        mock_container.read_item = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Summer Vacation",
            }
        )

        result = await repository.get_by_id("trip_123", "trip_123")

        assert result["id"] == "trip_123"
        mock_container.read_item.assert_called_once_with(item="trip_123", partition_key="trip_123")

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_container):
        """Test getting a non-existent document."""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container.read_item = AsyncMock(
            side_effect=CosmosResourceNotFoundError(status_code=404, message="Not found")
        )

        result = await repository.get_by_id("nonexistent", "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_query_documents(self, repository, mock_container):
        """Test querying documents."""
        mock_items = [
            {"id": "trip_1", "name": "Trip 1"},
            {"id": "trip_2", "name": "Trip 2"},
        ]
        mock_container.query_items = MagicMock(return_value=AsyncIteratorMock(mock_items))

        results = await repository.query("SELECT * FROM c WHERE c.entity_type = @type", {"type": "trip"})

        assert len(results) == 2
        assert results[0]["id"] == "trip_1"

    @pytest.mark.asyncio
    async def test_update_document(self, repository, mock_container):
        """Test updating a document."""
        mock_container.replace_item = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "name": "Updated Trip",
            }
        )

        result = await repository.update(
            "trip_123",
            "trip_123",
            {
                "id": "trip_123",
                "pk": "trip_123",
                "name": "Updated Trip",
            },
        )

        assert result["name"] == "Updated Trip"
        mock_container.replace_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document(self, repository, mock_container):
        """Test deleting a document."""
        mock_container.delete_item = AsyncMock()

        await repository.delete("trip_123", "trip_123")

        mock_container.delete_item.assert_called_once_with(item="trip_123", partition_key="trip_123")

    @pytest.mark.asyncio
    async def test_upsert_document(self, repository, mock_container):
        """Test upserting a document."""
        mock_container.upsert_item = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "name": "Upserted Trip",
            }
        )

        result = await repository.upsert(
            {
                "id": "trip_123",
                "pk": "trip_123",
                "name": "Upserted Trip",
            }
        )

        assert result["name"] == "Upserted Trip"
        mock_container.upsert_item.assert_called_once()


class AsyncIteratorMock:
    """Mock async iterator for query results."""

    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item
