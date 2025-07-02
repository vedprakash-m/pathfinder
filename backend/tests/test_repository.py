"""
Unit tests for the repository pattern implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.repository import (
    CosmosDbRepository,
    RepositoryFactory,
    SqlAlchemyRepository,
    with_caching,
    with_error_handling,
    with_performance_monitoring,
)
from app.models.user import User
from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.ext.asyncio import AsyncSession


class TestSqlAlchemyRepository:
    """Test cases for SqlAlchemyRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_model_class(self):
        """Create proper mock model class with SQLAlchemy table."""
        # Create metadata and table
        metadata = MetaData()
        mock_table = Table(
            "test_table",
            metadata,
            Column("id", String, primary_key=True),
            Column("name", String),
            Column("updated_at", String),
            Column("deleted_at", String),
        )

        # Create mock model class that behaves like SQLAlchemy model
        class MockModel:
            __tablename__ = "test_table"
            __table__ = mock_table

            def __init__(self):
                self.id = "test_id"
                self.name = "test_name"
                self.updated_at = None
                self.deleted_at = None

        # Mock class attributes for SQLAlchemy operations
        MockModel.id = mock_table.c.id
        MockModel.name = mock_table.c.name
        MockModel.updated_at = mock_table.c.updated_at
        MockModel.deleted_at = mock_table.c.deleted_at

        return MockModel

    @pytest.fixture
    def repository(self, mock_session, mock_model_class):
        """Create repository instance."""
        return SqlAlchemyRepository(mock_session, mock_model_class)

    @pytest.mark.asyncio
    async def test_repository_initialization(self, repository, mock_session, mock_model_class):
        """Test repository initialization."""
        assert repository.session == mock_session
        assert repository.model_class == mock_model_class
        assert repository.table_name == "test_table"

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session, mock_model_class):
        """Test successful get by ID."""
        mock_result = MagicMock()
        mock_entity = mock_model_class()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result

        _result = await repository.get_by_id("test_id")

        assert result == mock_entity
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """Test get by ID when entity not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        _result = await repository.get_by_id("nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_relations(self, repository, mock_session, mock_model_class):
        """Test get by ID with eager loading."""
        mock_result = MagicMock()
        mock_entity = mock_model_class()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result

        # Mock relation attribute
        mock_model_class.test_relation = MagicMock()

        _result = await repository.get_by_id("test_id", include_relations=["test_relation"])

        assert result == mock_entity
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_filters_basic(self, repository, mock_session, mock_model_class):
        """Test get by filters with basic filtering."""
        mock_result = MagicMock()
        mock_entities = [mock_model_class(), mock_model_class()]
        mock_result.scalars().all.return_value = mock_entities
        mock_session.execute.return_value = mock_result

        filters = {"name": "test"}
        _result = await repository.get_by_filters(filters)

        assert result == mock_entities
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_filters_complex(self, repository, mock_session, mock_model_class):
        """Test get by filters with complex filtering."""
        mock_result = MagicMock()
        mock_entities = [mock_model_class()]
        mock_result.scalars().all.return_value = mock_entities
        mock_session.execute.return_value = mock_result

        # Setup model attributes for complex filtering
        mock_model_class.age = mock_model_class.__table__.c.id  # Reuse existing column
        mock_model_class.status = mock_model_class.__table__.c.name  # Reuse existing column

        filters = {"age": {"gte": 18, "lte": 65}, "status": {"in": ["active", "pending"]}}
        _result = await repository.get_by_filters(filters)

        assert result == mock_entities

    @pytest.mark.asyncio
    async def test_get_by_filters_with_pagination(self, repository, mock_session, mock_model_class):
        """Test get by filters with pagination."""
        mock_result = MagicMock()
        mock_entities = [mock_model_class()]
        mock_result.scalars().all.return_value = mock_entities
        mock_session.execute.return_value = mock_result

        filters = {"name": "test"}
        _result = await repository.get_by_filters(filters, limit=10, offset=20)

        assert result == mock_entities

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session, mock_model_class):
        """Test successful entity creation."""
        mock_entity = mock_model_class()
        mock_entity.id = "test_id"

        _result = await repository.create(mock_entity)

        assert result == mock_entity
        mock_session.add.assert_called_once_with(mock_entity)
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_entity)

    @pytest.mark.asyncio
    async def test_create_no_flush(self, repository, mock_session, mock_model_class):
        """Test entity creation without flush."""
        mock_entity = mock_model_class()
        mock_entity.id = "test_id"

        _result = await repository.create(mock_entity, flush=False)

        assert result == mock_entity
        mock_session.add.assert_called_once_with(mock_entity)
        mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_error_handling(self, repository, mock_session, mock_model_class):
        """Test error handling during creation."""
        mock_entity = mock_model_class()
        mock_session.add.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await repository.create(mock_entity)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_session, mock_model_class):
        """Test successful entity update."""
        # Mock the SQL update execution
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Mock the get_by_id call in update method
        with patch.object(repository, "get_by_id") as mock_get:
            mock_updated_entity = mock_model_class()
            mock_get.return_value = mock_updated_entity

            updates = {"name": "updated_name"}
            _result = await repository.update("test_id", updates)

            assert result == mock_updated_entity

    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_session):
        """Test update when entity not found."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        updates = {"name": "updated_name"}
        _result = await repository.update("nonexistent_id", updates)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_no_return(self, repository, mock_session):
        """Test update without returning updated entity."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        updates = {"name": "updated_name"}
        _result = await repository.update("test_id", updates, return_updated=False)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_hard_delete(self, repository, mock_session):
        """Test hard delete."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        _result = await repository.delete("test_id")

        assert result is True
        mock_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_delete_soft_delete(self, repository, mock_session, mock_model_class):
        """Test soft delete."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_model_class.deleted_at = MagicMock()

        _result = await repository.delete("test_id", soft_delete=True)

        assert result is True
        mock_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_session):
        """Test delete when entity not found."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        _result = await repository.delete("nonexistent_id")

        assert result is False

    @pytest.mark.asyncio
    async def test_count_no_filters(self, repository, mock_session):
        """Test count without filters."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        _result = await repository.count()

        assert result == 5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_filters(self, repository, mock_session):
        """Test count with filters."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_session.execute.return_value = mock_result

        filters = {"status": "active"}
        _result = await repository.count(filters)

        assert result == 3

    @pytest.mark.asyncio
    async def test_exists_true(self, repository):
        """Test exists when entity exists."""
        with patch.object(repository, "get_by_id") as mock_get:
            mock_get.return_value = MagicMock()

            _result = await repository.exists("test_id")

            assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repository):
        """Test exists when entity doesn't exist."""
        with patch.object(repository, "get_by_id") as mock_get:
            mock_get.return_value = None

            _result = await repository.exists("nonexistent_id")

            assert result is False


class TestCosmosDbRepository:
    """Test cases for CosmosDbRepository."""

    @pytest.fixture
    def mock_container(self):
        """Create mock Cosmos container."""
        container = AsyncMock(spec=ContainerProxy)
        container.id = "test_container"
        return container

    @pytest.fixture
    def repository(self, mock_container):
        """Create repository instance."""
        return CosmosDbRepository(mock_container)

    @pytest.mark.asyncio
    async def test_repository_initialization(self, repository, mock_container):
        """Test repository initialization."""
        assert repository.container == mock_container
        assert repository.partition_key_field == "id"

    @pytest.mark.asyncio
    async def test_get_partition_key_from_dict(self, repository):
        """Test getting partition key from dictionary."""
        item = {"id": "test_id", "name": "test"}
        _result = repository._get_partition_key(item)
        assert result == "test_id"

    @pytest.mark.asyncio
    async def test_get_partition_key_from_string(self, repository):
        """Test getting partition key from string."""
        _result = repository._get_partition_key("test_id")
        assert result == "test_id"

    @pytest.mark.asyncio
    async def test_serialize_entity_dict(self, repository):
        """Test serializing dictionary entity."""
        entity = {"id": "test_id", "name": "test"}
        _result = repository._serialize_entity(entity)
        assert result == entity

    @pytest.mark.asyncio
    async def test_serialize_entity_object(self, repository):
        """Test serializing object entity."""

        class MockEntity:
            def dict(self):
                return {"id": "test_id", "name": "test"}

        entity = MockEntity()
        _result = repository._serialize_entity(entity)
        assert result == {"id": "test_id", "name": "test"}

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_container):
        """Test successful get by ID."""
        mock_item = {"id": "test_id", "name": "test"}
        mock_container.read_item.return_value = mock_item

        _result = await repository.get_by_id("test_id")

        assert result == mock_item
        mock_container.read_item.assert_called_once_with(item="test_id", partition_key="test_id")

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_container):
        """Test get by ID when entity not found."""
        mock_container.read_item.side_effect = CosmosResourceNotFoundError("Not found")

        _result = await repository.get_by_id("nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_filters(self, repository, mock_container):
        """Test get by filters."""
        mock_items = [{"id": "1", "name": "test1"}, {"id": "2", "name": "test2"}]

        async def mock_query_items(query, **kwargs):
            """Mock async iterator for query results."""
            for item in mock_items:
                yield item

        mock_container.query_items.return_value = mock_query_items(
            "", enable_cross_partition_query=True
        )

        filters = {"name": "test"}

        # Since query_items returns an async iterator, we need to handle it properly
        with patch.object(repository.container, "query_items") as mock_query:
            mock_query.return_value = mock_items  # Simplified for testing

            _result = await repository.get_by_filters(filters)

            # The actual implementation would return the list from the async iterator
            mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_container):
        """Test successful entity creation."""
        entity = {"id": "test_id", "name": "test"}
        mock_container.create_item.return_value = entity

        _result = await repository.create(entity)

        assert result == entity
        mock_container.create_item.assert_called_once_with(entity)

    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_container):
        """Test successful entity update."""
        updates = {"name": "updated_name"}
        existing_entity = {"id": "test_id", "name": "old_name"}
        updated_entity = {"id": "test_id", "name": "updated_name"}

        mock_container.read_item.return_value = existing_entity
        mock_container.replace_item.return_value = updated_entity

        _result = await repository.update("test_id", updates)

        assert result == updated_entity
        mock_container.replace_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_container):
        """Test update when entity not found."""
        mock_container.read_item.side_effect = CosmosResourceNotFoundError("Not found")

        updates = {"name": "updated_name"}
        _result = await repository.update("nonexistent_id", updates)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_success(self, repository, mock_container):
        """Test successful entity deletion."""
        mock_container.delete_item.return_value = None

        _result = await repository.delete("test_id")

        assert result is True
        mock_container.delete_item.assert_called_once_with(item="test_id", partition_key="test_id")

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_container):
        """Test delete when entity not found."""
        mock_container.delete_item.side_effect = CosmosResourceNotFoundError("Not found")

        _result = await repository.delete("nonexistent_id")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self, repository, mock_container):
        """Test exists when entity exists."""
        mock_container.read_item.return_value = {"id": "test_id"}

        _result = await repository.exists("test_id")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repository, mock_container):
        """Test exists when entity doesn't exist."""
        mock_container.read_item.side_effect = CosmosResourceNotFoundError("Not found")

        _result = await repository.exists("nonexistent_id")

        assert result is False


class TestRepositoryFactory:
    """Test cases for RepositoryFactory."""

    @pytest.fixture
    def mock_session_factory(self):
        """Create mock session factory."""
        return MagicMock()

    @pytest.fixture
    def mock_cosmos_containers(self):
        """Create mock cosmos containers."""
        return {"test_container": AsyncMock()}

    @pytest.fixture
    def factory(self, mock_session_factory, mock_cosmos_containers):
        """Create factory instance."""
        return RepositoryFactory(mock_session_factory, mock_cosmos_containers)

    def test_factory_initialization(self, factory, mock_session_factory):
        """Test factory initialization."""
        assert factory.session_factory == mock_session_factory

    def test_create_sql_repository(self, factory):
        """Test creating SQL repository."""
        mock_session = MagicMock()
        factory.session_factory.return_value = mock_session

        repository = factory.create_sql_repository(User)

        assert isinstance(repository, SqlAlchemyRepository)

    def test_create_cosmos_repository(self, factory, mock_cosmos_containers):
        """Test creating Cosmos repository."""
        repository = factory.create_cosmos_repository("test_container")

        assert isinstance(repository, CosmosDbRepository)

    def test_create_cosmos_repository_missing_container(self, factory):
        """Test creating Cosmos repository with missing container."""
        with pytest.raises(ValueError):
            factory.create_cosmos_repository("nonexistent_container")


class TestRepositoryDecorators:
    """Test cases for repository decorators."""

    @pytest.mark.asyncio
    async def test_error_handling_decorator_success(self):
        """Test error handling decorator with successful operation."""

        @with_error_handling
        async def mock_method():
            return "success"

        _result = await mock_method()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_error_handling_decorator_failure(self):
        """Test error handling decorator with failure."""

        @with_error_handling
        async def mock_method():
            raise Exception("test error")

        _result = await mock_method()
        assert result is None

    @pytest.mark.asyncio
    async def test_caching_decorator(self):
        """Test caching decorator functionality."""
        cache_decorator = with_caching("test", ttl=300)

        @cache_decorator
        async def mock_method(self, arg1):
            return f"result_{arg1}"

        # Create mock repository with cache
        mock_repo = MagicMock()
        mock_repo.cache = MagicMock()
        mock_repo.cache.get = AsyncMock(return_value=None)
        mock_repo.cache.set = AsyncMock()

        _result = await mock_method(mock_repo, "test_arg")
        assert result == "result_test_arg"

    @pytest.mark.asyncio
    async def test_performance_monitoring_decorator(self):
        """Test performance monitoring decorator."""
        monitor_decorator = with_performance_monitoring("test_operation")

        @monitor_decorator
        async def mock_method(arg1):
            return f"result_{arg1}"

        _result = await mock_method("test_arg")
        assert result == "result_test_arg"
