"""
Cosmos DB Repository

Unified data access layer for all Cosmos DB operations.
Uses a single container with partition keys for efficient querying.
"""
import logging
import os
from typing import Any, Optional, TypeVar

from azure.cosmos import exceptions
from azure.cosmos.aio import CosmosClient

from models.documents import BaseDocument

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseDocument)


class CosmosRepository:
    """
    Unified Cosmos DB repository providing CRUD operations for all entity types.

    Uses singleton pattern to maintain a single connection across the application.
    All entities are stored in a single container with partition keys.
    """

    _instance: Optional["CosmosRepository"] = None
    _client: Optional[CosmosClient] = None
    _container = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _get_container(self):
        """Get or create Cosmos DB container client."""
        if self._container is not None:
            return self._container

        if self._client is None:
            cosmos_url = os.environ.get("COSMOS_DB_URL")
            cosmos_key = os.environ.get("COSMOS_DB_KEY")

            if not cosmos_url or not cosmos_key:
                raise ValueError("COSMOS_DB_URL and COSMOS_DB_KEY must be set")

            self._client = CosmosClient(url=cosmos_url, credential=cosmos_key)

        database_name = os.environ.get("COSMOS_DB_DATABASE", "pathfinder")
        container_name = os.environ.get("COSMOS_DB_CONTAINER", "entities")

        database = self._client.get_database_client(database_name)
        self._container = database.get_container_client(container_name)

        return self._container

    async def create(self, document: T) -> T:
        """
        Create a new document in Cosmos DB.

        Args:
            document: Document to create

        Returns:
            Created document with server-generated fields
        """
        container = await self._get_container()
        doc_dict = document.model_dump(mode="json")

        try:
            result = await container.create_item(body=doc_dict)
            logger.info(f"Created {document.entity_type} document: {document.id}")
            return type(document)(**result)
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Document already exists: {document.id}")
            raise
        except Exception as e:
            logger.exception(f"Failed to create document: {e}")
            raise

    async def get_by_id(self, doc_id: str, partition_key: str, model_class: type[T]) -> Optional[T]:
        """
        Get a document by ID and partition key.

        Args:
            doc_id: Document ID
            partition_key: Partition key value
            model_class: Pydantic model class to deserialize into

        Returns:
            Document if found, None otherwise
        """
        container = await self._get_container()

        try:
            result = await container.read_item(item=doc_id, partition_key=partition_key)
            return model_class(**result)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.exception(f"Failed to get document {doc_id}: {e}")
            raise

    async def query(
        self,
        query: str,
        parameters: Optional[list[dict[str, Any]]] = None,
        model_class: Optional[type[T]] = None,
        partition_key: Optional[str] = None,
        max_items: int = 100,
    ) -> list[Any]:
        """
        Query documents using SQL-like syntax.

        Args:
            query: Cosmos DB SQL query
            parameters: Query parameters
            model_class: Optional model class to deserialize results
            partition_key: Optional partition key to scope query
            max_items: Maximum items to return

        Returns:
            List of documents (as model instances or dicts)
        """
        container = await self._get_container()
        items = []

        query_options = {
            "query": query,
            "parameters": parameters or [],
            "max_item_count": max_items,
        }

        if partition_key:
            query_options["partition_key"] = partition_key
        else:
            query_options["enable_cross_partition_query"] = True

        try:
            async for item in container.query_items(**query_options):
                if model_class:
                    items.append(model_class(**item))
                else:
                    items.append(item)

                if len(items) >= max_items:
                    break

            return items
        except Exception as e:
            logger.exception(f"Query failed: {e}")
            raise

    async def update(self, document: T) -> T:
        """
        Update an existing document (full replacement).

        Args:
            document: Document with updated fields

        Returns:
            Updated document
        """
        container = await self._get_container()

        # Update timestamp and version
        document.touch()
        doc_dict = document.model_dump(mode="json")

        try:
            result = await container.replace_item(item=doc_dict["id"], body=doc_dict)
            logger.info(f"Updated {document.entity_type} document: {document.id}")
            return type(document)(**result)
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Document not found for update: {document.id}")
            raise
        except Exception as e:
            logger.exception(f"Failed to update document: {e}")
            raise

    async def upsert(self, document: T) -> T:
        """
        Create or update a document.

        Args:
            document: Document to upsert

        Returns:
            Upserted document
        """
        container = await self._get_container()
        doc_dict = document.model_dump(mode="json")

        try:
            result = await container.upsert_item(body=doc_dict)
            logger.info(f"Upserted {document.entity_type} document: {document.id}")
            return type(document)(**result)
        except Exception as e:
            logger.exception(f"Failed to upsert document: {e}")
            raise

    async def delete(self, doc_id: str, partition_key: str) -> bool:
        """
        Delete a document.

        Args:
            doc_id: Document ID
            partition_key: Partition key value

        Returns:
            True if deleted, False if not found
        """
        container = await self._get_container()

        try:
            await container.delete_item(item=doc_id, partition_key=partition_key)
            logger.info(f"Deleted document: {doc_id}")
            return True
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Document not found for deletion: {doc_id}")
            return False
        except Exception as e:
            logger.exception(f"Failed to delete document: {e}")
            raise

    async def count(
        self, query: str, parameters: Optional[list[dict[str, Any]]] = None, partition_key: Optional[str] = None
    ) -> int:
        """
        Count documents matching a query.

        Args:
            query: Count query (should select COUNT(1))
            parameters: Query parameters
            partition_key: Optional partition key

        Returns:
            Count of matching documents
        """
        container = await self._get_container()

        query_options = {
            "query": query,
            "parameters": parameters or [],
        }

        if partition_key:
            query_options["partition_key"] = partition_key
        else:
            query_options["enable_cross_partition_query"] = True

        try:
            async for item in container.query_items(**query_options):
                # Count query returns a single document with $1 field
                return item.get("$1", 0)
            return 0
        except Exception as e:
            logger.exception(f"Count query failed: {e}")
            raise

    async def query_by_type(
        self,
        entity_type: str,
        model_class: type[T],
        additional_filter: Optional[str] = None,
        parameters: Optional[list[dict[str, Any]]] = None,
        max_items: int = 100,
    ) -> list[T]:
        """
        Query documents by entity type.

        Args:
            entity_type: Type of entity (user, family, trip, etc.)
            model_class: Model class to deserialize into
            additional_filter: Optional additional WHERE clause
            parameters: Query parameters
            max_items: Maximum items to return

        Returns:
            List of documents
        """
        query = "SELECT * FROM c WHERE c.entity_type = @entityType"
        params = [{"name": "@entityType", "value": entity_type}]

        if additional_filter:
            query += f" AND {additional_filter}"

        if parameters:
            params.extend(parameters)

        return await self.query(query=query, parameters=params, model_class=model_class, max_items=max_items)

    async def close(self):
        """Close the Cosmos DB connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._container = None
            logger.info("Cosmos DB connection closed")


# Singleton instance
cosmos_repo = CosmosRepository()
