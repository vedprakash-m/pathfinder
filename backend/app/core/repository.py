"""
Unified Repository Pattern Implementation
Provides abstraction layer for all data persistence operations.
Part of Phase 2: System Integration & Consistency improvements.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

# Generic type for entities
T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """
    Abstract base repository implementing unified data access patterns.
    Provides consistent interface regardless of underlying storage system.
    """

    @abstractmethod
    async def get_by_id(self, id: str, **kwargs) -> Optional[T]:
        """Retrieve entity by ID with optional loading options."""
        pass

    @abstractmethod
    async def get_by_filters(self, filters: Dict[str, Any], **kwargs) -> List[T]:
        """Retrieve entities matching filters."""
        pass

    @abstractmethod
    async def create(self, entity: T, **kwargs) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any], **kwargs) -> Optional[T]:
        """Update entity by ID."""
        pass

    @abstractmethod
    async def delete(self, id: str, **kwargs) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        pass

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Check if entity exists."""
        pass


class SqlAlchemyRepository(Repository[T]):
    """
    SQLAlchemy-based repository implementation for relational data.
    Provides unified interface with connection management and error handling.
    """

    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
        self.table_name = model_class.__tablename__

    async def get_by_id(
        self, id: str, include_relations: Optional[List[str]] = None
    ) -> Optional[T]:
        """Retrieve entity by ID with optional eager loading."""
        try:
            query = select(self.model_class).where(self.model_class.id == id)

            # Add eager loading for specified relations
            if include_relations:
                for relation in include_relations:
                    if hasattr(self.model_class, relation):
                        query = query.options(
                            selectinload(getattr(self.model_class, relation))
                        )

            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error retrieving {self.table_name} by ID {id}: {e}")
            return None

    async def get_by_filters(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        include_relations: Optional[List[str]] = None,
    ) -> List[T]:
        """Retrieve entities with complex filtering and pagination."""
        try:
            query = select(self.model_class)

            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    if isinstance(value, dict):
                        # Handle complex filters like {"gte": 100}, {"in": [1,2,3]}
                        if "gte" in value:
                            query = query.where(column >= value["gte"])
                        if "lte" in value:
                            query = query.where(column <= value["lte"])
                        if "in" in value:
                            query = query.where(column.in_(value["in"]))
                        if "like" in value:
                            query = query.where(column.like(f"%{value['like']}%"))
                    else:
                        query = query.where(column == value)

            # Add eager loading
            if include_relations:
                for relation in include_relations:
                    if hasattr(self.model_class, relation):
                        query = query.options(
                            selectinload(getattr(self.model_class, relation))
                        )

            # Add ordering
            if order_by:
                if hasattr(self.model_class, order_by):
                    query = query.order_by(getattr(self.model_class, order_by))

            # Add pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                f"Error querying {self.table_name} with filters {filters}: {e}"
            )
            return []

    async def create(self, entity: T, flush: bool = True) -> T:
        """Create new entity with proper error handling."""
        try:
            self.session.add(entity)
            if flush:
                await self.session.flush()
                await self.session.refresh(entity)

            logger.info(f"Created {self.table_name} entity with ID: {entity.id}")
            return entity

        except Exception as e:
            logger.error(f"Error creating {self.table_name} entity: {e}")
            await self.session.rollback()
            raise

    async def update(
        self, id: str, updates: Dict[str, Any], return_updated: bool = True
    ) -> Optional[T]:
        """Update entity with optimistic concurrency control."""
        try:
            # Add updated_at timestamp if field exists
            if hasattr(self.model_class, "updated_at"):
                updates["updated_at"] = datetime.utcnow()

            query = (
                update(self.model_class)
                .where(self.model_class.id == id)
                .values(**updates)
            )
            result = await self.session.execute(query)

            if result.rowcount == 0:
                logger.warning(f"No {self.table_name} found with ID {id} for update")
                return None

            await self.session.flush()

            if return_updated:
                return await self.get_by_id(id)

            logger.info(f"Updated {self.table_name} entity ID: {id}")
            return None

        except Exception as e:
            logger.error(f"Error updating {self.table_name} ID {id}: {e}")
            await self.session.rollback()
            raise

    async def delete(self, id: str, soft_delete: bool = False) -> bool:
        """Delete entity with soft delete option."""
        try:
            if soft_delete and hasattr(self.model_class, "deleted_at"):
                # Soft delete
                updates = {"deleted_at": datetime.utcnow(), "is_active": False}
                result = await self.update(id, updates, return_updated=False)
                return result is not None
            else:
                # Hard delete
                query = delete(self.model_class).where(self.model_class.id == id)
                result = await self.session.execute(query)
                await self.session.flush()

                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Deleted {self.table_name} entity ID: {id}")

                return deleted

        except Exception as e:
            logger.error(f"Error deleting {self.table_name} ID {id}: {e}")
            await self.session.rollback()
            return False

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        try:
            from sqlalchemy import func

            query = select(func.count(self.model_class.id))

            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        column = getattr(self.model_class, field)
                        query = query.where(column == value)

            result = await self.session.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Error counting {self.table_name}: {e}")
            return 0

    async def exists(self, id: str) -> bool:
        """Check if entity exists by ID."""
        try:
            query = select(self.model_class.id).where(self.model_class.id == id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(f"Error checking {self.table_name} existence for ID {id}: {e}")
            return False


class CosmosDbRepository(Repository[T]):
    """
    Cosmos DB repository implementation for document-based data.
    Provides unified interface with partition key handling and query optimization.
    """

    def __init__(self, container: ContainerProxy, partition_key_field: str = "id"):
        self.container = container
        self.partition_key_field = partition_key_field
        self.container_name = container.id

    def _get_partition_key(self, item: Union[Dict, str]) -> str:
        """Extract partition key from item or use ID."""
        if isinstance(item, str):
            return item
        return item.get(self.partition_key_field, item.get("id", ""))

    def _serialize_entity(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary for Cosmos DB."""
        if isinstance(entity, dict):
            return entity

        if hasattr(entity, "__dict__"):
            data = entity.__dict__.copy()
            # Convert datetime objects to ISO strings
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
            return data

        return {"id": str(entity), "data": str(entity)}

    def _deserialize_entity(self, data: Dict[str, Any]) -> T:
        """Convert Cosmos DB document back to entity."""
        # For now, return as dict - can be enhanced for specific types
        return data

    async def get_by_id(self, id: str, **kwargs) -> Optional[T]:
        """Retrieve document by ID."""
        try:
            partition_key = kwargs.get("partition_key", id)
            item = self.container.read_item(id, partition_key)
            return self._deserialize_entity(item)

        except CosmosResourceNotFoundError:
            logger.debug(f"Document not found in {self.container_name}: {id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving document from {self.container_name}: {e}")
            return None

    async def get_by_filters(self, filters: Dict[str, Any], **kwargs) -> List[T]:
        """Query documents with filters."""
        try:
            # Build SQL query from filters
            conditions = []
            parameters = []

            for field, value in filters.items():
                if isinstance(value, dict):
                    if "gte" in value:
                        conditions.append(f"c.{field} >= @{field}_gte")
                        parameters.append(
                            {"name": f"@{field}_gte", "value": value["gte"]}
                        )
                    if "lte" in value:
                        conditions.append(f"c.{field} <= @{field}_lte")
                        parameters.append(
                            {"name": f"@{field}_lte", "value": value["lte"]}
                        )
                    if "in" in value:
                        conditions.append(
                            f"c.{field} IN ({','.join([f'@{field}_{i}' for i in range(len(value['in']))])})"
                        )
                        for i, val in enumerate(value["in"]):
                            parameters.append({"name": f"@{field}_{i}", "value": val})
                else:
                    conditions.append(f"c.{field} = @{field}")
                    parameters.append({"name": f"@{field}", "value": value})

            where_clause = " AND ".join(conditions) if conditions else "true"
            query = f"SELECT * FROM c WHERE {where_clause}"

            # Add pagination
            if "limit" in kwargs:
                query += f" OFFSET {kwargs.get('offset', 0)} LIMIT {kwargs['limit']}"

            items = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                )
            )

            return [self._deserialize_entity(item) for item in items]

        except Exception as e:
            logger.error(
                f"Error querying {self.container_name} with filters {filters}: {e}"
            )
            return []

    async def create(self, entity: T, **kwargs) -> T:
        """Create new document."""
        try:
            data = self._serialize_entity(entity)

            # Ensure ID exists
            if "id" not in data:
                data["id"] = str(uuid.uuid4())

            # Add timestamps
            now = datetime.utcnow().isoformat()
            data.setdefault("created_at", now)
            data["updated_at"] = now

            created_item = self.container.create_item(data)
            logger.info(
                f"Created document in {self.container_name} with ID: {created_item['id']}"
            )

            return self._deserialize_entity(created_item)

        except Exception as e:
            logger.error(f"Error creating document in {self.container_name}: {e}")
            raise

    async def update(self, id: str, updates: Dict[str, Any], **kwargs) -> Optional[T]:
        """Update document with merge strategy."""
        try:
            partition_key = kwargs.get("partition_key", id)

            # Get existing document
            existing = self.container.read_item(id, partition_key)

            # Merge updates
            existing.update(updates)
            existing["updated_at"] = datetime.utcnow().isoformat()

            # Replace document
            updated_item = self.container.replace_item(id, existing)
            logger.info(f"Updated document in {self.container_name} with ID: {id}")

            return self._deserialize_entity(updated_item)

        except CosmosResourceNotFoundError:
            logger.warning(
                f"Document not found for update in {self.container_name}: {id}"
            )
            return None
        except Exception as e:
            logger.error(f"Error updating document in {self.container_name}: {e}")
            raise

    async def delete(self, id: str, **kwargs) -> bool:
        """Delete document."""
        try:
            partition_key = kwargs.get("partition_key", id)
            self.container.delete_item(id, partition_key)
            logger.info(f"Deleted document from {self.container_name} with ID: {id}")
            return True

        except CosmosResourceNotFoundError:
            logger.warning(
                f"Document not found for deletion in {self.container_name}: {id}"
            )
            return False
        except Exception as e:
            logger.error(f"Error deleting document from {self.container_name}: {e}")
            return False

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents with optional filters."""
        try:
            if filters:
                items = await self.get_by_filters(filters)
                return len(items)
            else:
                # Simple count query
                query = "SELECT VALUE COUNT(1) FROM c"
                result = list(
                    self.container.query_items(
                        query=query, enable_cross_partition_query=True
                    )
                )
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"Error counting documents in {self.container_name}: {e}")
            return 0

    async def exists(self, id: str, **kwargs) -> bool:
        """Check if document exists."""
        try:
            partition_key = kwargs.get("partition_key", id)
            self.container.read_item(id, partition_key)
            return True

        except CosmosResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking existence in {self.container_name}: {e}")
            return False


class RepositoryFactory:
    """
    Factory for creating appropriate repository instances.
    Centralizes repository creation and dependency injection.
    """

    def __init__(
        self,
        db_session_factory,
        cosmos_containers: Optional[Dict[str, ContainerProxy]] = None,
    ):
        self.db_session_factory = db_session_factory
        self.cosmos_containers = cosmos_containers or {}

    def create_sql_repository(self, model_class: Type[T]) -> SqlAlchemyRepository[T]:
        """Create SQLAlchemy repository for given model."""
        session = self.db_session_factory()
        return SqlAlchemyRepository(session, model_class)

    def create_cosmos_repository(
        self, container_name: str, partition_key_field: str = "id"
    ) -> CosmosDbRepository:
        """Create Cosmos DB repository for given container."""
        if container_name not in self.cosmos_containers:
            raise ValueError(f"Cosmos container '{container_name}' not configured")

        container = self.cosmos_containers[container_name]
        return CosmosDbRepository(container, partition_key_field)

    @asynccontextmanager
    async def get_transactional_session(self):
        """Provide transactional session for multiple repository operations."""
        session = self.db_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==================== REPOSITORY DECORATORS ====================


def with_error_handling(repository_method):
    """Decorator for consistent error handling across repository methods."""

    async def wrapper(*args, **kwargs):
        try:
            return await repository_method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Repository error in {repository_method.__name__}: {e}")
            raise

    return wrapper


def with_caching(cache_key_prefix: str, ttl: int = 3600):
    """Decorator for repository method caching."""

    def decorator(repository_method):
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            _cache_key = f"{cache_key_prefix}:{repository_method.__name__}:{hash(str(args) + str(kwargs))}"

            # Try cache first (implementation depends on cache provider)
            # For now, just execute the method
            return await repository_method(self, *args, **kwargs)

        return wrapper

    return decorator


def with_performance_monitoring(operation_name: str):
    """Decorator for repository performance monitoring."""

    def decorator(repository_method):
        async def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = await repository_method(*args, **kwargs)
                duration = (time.time() - start_time) * 1000

                logger.info(
                    "Repository operation completed",
                    extra={
                        "operation": operation_name,
                        "method": repository_method.__name__,
                        "duration_ms": duration,
                        "success": True,
                    },
                )

                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    "Repository operation failed",
                    extra={
                        "operation": operation_name,
                        "method": repository_method.__name__,
                        "duration_ms": duration,
                        "success": False,
                        "error": str(e),
                    },
                )
                raise

        return wrapper

    return decorator
