"""
Azure Cosmos DB integration for document storage.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from app.core.config import get_settings
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.container import ContainerProxy
from pydantic import BaseModel

settings = get_settings()
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class CosmosDBService(Generic[T]):
    """
    Generic service for Azure Cosmos DB operations.

    This service implements the document storage part of the hybrid database strategy,
    providing a flexible schema approach for data that doesn't fit well in SQL tables.
    """

    def __init__(self, container_name: str, model_type: Type[T], partition_key: str):
        """Initialize the Cosmos DB client for a specific container."""
        self.model_type = model_type
        self.partition_key = partition_key

        # In local development, we'll use a simulated document storage
        if settings.ENVIRONMENT == "development" and not settings.COSMOS_DB_ENABLED:
            self.client = None
            self.database = None
            self.container = None
            self.simulation_data = {}
            logger.warning(f"Using simulated Cosmos DB for {container_name}")
            return

        # In production environments, connect to actual Cosmos DB
        try:
            self.client = CosmosClient(settings.COSMOS_DB_URL, credential=settings.COSMOS_DB_KEY)

            self.database = self.client.get_database_client(settings.COSMOS_DB_DATABASE)
            self.container = self.database.get_container_client(container_name)

            logger.info(f"Connected to Cosmos DB container: {container_name}")

        except Exception as e:
            logger.error(f"Failed to connect to Cosmos DB: {str(e)}")
            # Fall back to simulation in case of connection errors
            self.client = None
            self.database = None
            self.container = None
            self.simulation_data = {}

    async def create_item(self, item: T) -> Dict[str, Any]:
        """Create a new document in Cosmos DB."""
        # Convert Pydantic model to dict
        item_dict = item.model_dump()

        # Ensure we have an ID
        if "id" not in item_dict:
            item_dict["id"] = str(uuid.uuid4())

        # Add timestamp
        item_dict["_ts"] = int(datetime.utcnow().timestamp())

        # In development simulation mode
        if not self.container:
            item_id = item_dict["id"]
            pk_value = item_dict.get(self.partition_key, "default")
            if pk_value not in self.simulation_data:
                self.simulation_data[pk_value] = {}
            self.simulation_data[pk_value][item_id] = item_dict
            return item_dict

        # In production with real Cosmos DB
        try:
            result = self.container.create_item(body=item_dict)
            return result
        except exceptions.CosmosResourceExistsError:
            raise ValueError(f"Item with ID {item_dict['id']} already exists")
        except Exception as e:
            logger.error(f"Cosmos DB create error: {str(e)}")
            raise

    async def get_item(self, item_id: str, partition_key_value: str) -> Optional[T]:
        """Get an item by ID and partition key."""
        # In development simulation mode
        if not self.container:
            if partition_key_value in self.simulation_data:
                item = self.simulation_data[partition_key_value].get(item_id)
                if item:
                    return self.model_type(**item)
            return None

        # In production with real Cosmos DB
        try:
            item = self.container.read_item(item=item_id, partition_key=partition_key_value)
            return self.model_type(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Cosmos DB read error: {str(e)}")
            raise

    async def query_items(
        self,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        partition_key_value: Optional[str] = None,
    ) -> List[T]:
        """Query items with SQL-like syntax."""
        items = []
        parameters = parameters or []

        # In development simulation mode
        if not self.container:
            # Very basic simulation of query capabilities
            if "SELECT * FROM c" in query and partition_key_value:
                if partition_key_value in self.simulation_data:
                    for item_dict in self.simulation_data[partition_key_value].values():
                        items.append(self.model_type(**item_dict))
            return items

        # In production with real Cosmos DB
        try:
            query_options = {}
            if partition_key_value:
                query_options["partition_key"] = partition_key_value

            results = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=partition_key_value is None,
                **query_options,
            )

            for item in results:
                items.append(self.model_type(**item))

            return items

        except Exception as e:
            logger.error(f"Cosmos DB query error: {str(e)}")
            raise

    async def replace_item(self, item_id: str, item: T, partition_key_value: str) -> Dict[str, Any]:
        """Replace an existing item."""
        # Convert Pydantic model to dict
        item_dict = item.model_dump()

        # Ensure ID matches
        item_dict["id"] = item_id

        # Update timestamp
        item_dict["_ts"] = int(datetime.utcnow().timestamp())

        # In development simulation mode
        if not self.container:
            if partition_key_value in self.simulation_data:
                if item_id in self.simulation_data[partition_key_value]:
                    self.simulation_data[partition_key_value][item_id] = item_dict
                    return item_dict
            raise ValueError(f"Item with ID {item_id} not found")

        # In production with real Cosmos DB
        try:
            result = self.container.replace_item(
                item=item_id, body=item_dict, partition_key=partition_key_value
            )
            return result
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError(f"Item with ID {item_id} not found")
        except Exception as e:
            logger.error(f"Cosmos DB replace error: {str(e)}")
            raise

    async def delete_item(self, item_id: str, partition_key_value: str) -> None:
        """Delete an item by ID and partition key."""
        # In development simulation mode
        if not self.container:
            if partition_key_value in self.simulation_data:
                if item_id in self.simulation_data[partition_key_value]:
                    del self.simulation_data[partition_key_value][item_id]
                    return
            raise ValueError(f"Item with ID {item_id} not found")

        # In production with real Cosmos DB
        try:
            self.container.delete_item(item=item_id, partition_key=partition_key_value)
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError(f"Item with ID {item_id} not found")
        except Exception as e:
            logger.error(f"Cosmos DB delete error: {str(e)}")
            raise


def get_cosmos_client() -> Optional[CosmosClient]:
    """
    Get a Cosmos DB client instance.
    Returns None if running in development mode without Cosmos DB enabled.
    """
    if settings.ENVIRONMENT == "development" and not settings.COSMOS_DB_ENABLED:
        return None

    try:
        return CosmosClient(settings.COSMOS_DB_URL, credential=settings.COSMOS_DB_KEY)
    except Exception as e:
        logger.error(f"Failed to create Cosmos DB client: {str(e)}")
        return None
