"""
Preference document service for Cosmos DB operations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.cosmos_db import CosmosDBService
from app.models.cosmos.preference import PreferenceDocument, PreferenceType

settings = get_settings()
logger = logging.getLogger(__name__)


class PreferenceDocumentService:
    """
    Service for managing preference documents in Cosmos DB.

    This service allows for rich, flexible preference storage
    that can adapt to changing user and trip requirements.
    """

    def __init__(self):
        """Initialize the Cosmos DB service with preference container."""
        self.cosmos_service = CosmosDBService[PreferenceDocument](
            container_name=settings.COSMOS_DB_CONTAINER_PREFERENCES,
            model_type=PreferenceDocument,
            partition_key="entity_id",
        )

    async def create_preference(
        self, preference: PreferenceDocument
    ) -> PreferenceDocument:
        """Create a new preference document."""
        # Ensure we have an ID
        if not preference.id:
            preference.id = str(uuid.uuid4())

        # Set timestamps
        current_time = datetime.utcnow()
        preference.created_at = current_time
        preference.updated_at = current_time
        preference.last_used_at = current_time

        # Create the document in Cosmos DB
        result = await self.cosmos_service.create_item(preference)

        # Convert back to Pydantic model and return
        return PreferenceDocument(**result)

    async def get_preference(
        self, preference_id: str, entity_id: str
    ) -> Optional[PreferenceDocument]:
        """Get a preference document by ID and entity ID."""
        return await self.cosmos_service.get_item(preference_id, entity_id)

    async def get_latest_preference(
        self, entity_type: PreferenceType, entity_id: str
    ) -> Optional[PreferenceDocument]:
        """Get the latest preference document for an entity."""
        query = """
            SELECT TOP 1 * FROM c 
            WHERE c.entity_type = @entity_type 
            AND c.entity_id = @entity_id 
            ORDER BY c.version DESC
        """
        parameters = [
            {"name": "@entity_type", "value": entity_type},
            {"name": "@entity_id", "value": entity_id},
        ]

        results = await self.cosmos_service.query_items(
            query=query, parameters=parameters, partition_key_value=entity_id
        )

        return results[0] if results else None

    async def update_preference(
        self, preference: PreferenceDocument, create_version: bool = False
    ) -> PreferenceDocument:
        """
        Update a preference document.

        Args:
            preference: The preference document to update
            create_version: If True, create a new version instead of updating

        Returns:
            The updated preference document
        """
        # If creating a new version
        if create_version:
            # Get the current document to link as previous version
            current = await self.get_preference(preference.id, preference.entity_id)

            # Create a new document with incremented version
            new_version = preference.model_copy(deep=True)
            new_version.id = str(uuid.uuid4())
            new_version.version = preference.version + 1
            new_version.previous_version_id = preference.id
            new_version.updated_at = datetime.utcnow()
            new_version.last_used_at = datetime.utcnow()

            # Create the new version in Cosmos DB
            return await self.create_preference(new_version)

        # Just update the existing document
        preference.updated_at = datetime.utcnow()
        preference.last_used_at = datetime.utcnow()

        # Update the document in Cosmos DB
        result = await self.cosmos_service.replace_item(
            item_id=preference.id,
            item=preference,
            partition_key_value=preference.entity_id,
        )

        # Convert back to Pydantic model and return
        return PreferenceDocument(**result)

    async def delete_preference(self, preference_id: str, entity_id: str) -> None:
        """Delete a preference document."""
        await self.cosmos_service.delete_item(preference_id, entity_id)

    async def update_specific_preference(
        self,
        entity_type: PreferenceType,
        entity_id: str,
        preference_path: str,
        preference_value: Any,
    ) -> Optional[PreferenceDocument]:
        """
        Update a specific preference value by path.

        Args:
            entity_type: Type of entity (user, family, trip)
            entity_id: ID of the entity
            preference_path: Dot-notation path to the preference (e.g. "dietary_restrictions")
            preference_value: New value for the preference

        Returns:
            Updated preference document
        """
        # Get the current preference document
        preference = await self.get_latest_preference(entity_type, entity_id)

        # If no document exists, create a new one
        if not preference:
            preference = PreferenceDocument(
                id=str(uuid.uuid4()),
                entity_type=entity_type,
                entity_id=entity_id,
                preferences={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        # Update the preference at the specified path
        # Split the path by dots to navigate the nested structure
        parts = preference_path.split(".")

        if len(parts) == 1:
            # Top-level attribute
            setattr(preference, parts[0], preference_value)
        else:
            # Nested attribute in a dictionary
            current = preference.preferences
            for i, part in enumerate(parts[:-1]):
                # Create nested dictionaries if they don't exist
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the final value
            current[parts[-1]] = preference_value

        # Update the document
        return await self.update_preference(preference)

    async def get_preference_history(
        self, entity_type: PreferenceType, entity_id: str
    ) -> List[PreferenceDocument]:
        """Get the version history of preferences for an entity."""
        query = """
            SELECT * FROM c 
            WHERE c.entity_type = @entity_type 
            AND c.entity_id = @entity_id 
            ORDER BY c.version DESC
        """
        parameters = [
            {"name": "@entity_type", "value": entity_type},
            {"name": "@entity_id", "value": entity_id},
        ]

        return await self.cosmos_service.query_items(
            query=query, parameters=parameters, partition_key_value=entity_id
        )

    async def record_preference_usage(self, preference_id: str, entity_id: str) -> None:
        """Record that a preference was used (update last_used_at)."""
        preference = await self.get_preference(preference_id, entity_id)
        if preference:
            preference.last_used_at = datetime.utcnow()
            await self.cosmos_service.replace_item(
                item_id=preference_id, item=preference, partition_key_value=entity_id
            )

    async def convert_from_model(
        self,
        entity_type: PreferenceType,
        entity_id: str,
        preferences_data: Dict[str, Any],
    ) -> PreferenceDocument:
        """
        Convert preferences from a model to a document.

        This allows for importing preferences from SQL models into the document database.
        """
        # Check if a document already exists
        existing = await self.get_latest_preference(entity_type, entity_id)
        if existing:
            # Update existing document
            existing.preferences.update(preferences_data)
            existing.updated_at = datetime.utcnow()
            existing.last_used_at = datetime.utcnow()
            return await self.update_preference(existing, create_version=True)

        # Create new document
        preference = PreferenceDocument(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            preferences=preferences_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=datetime.utcnow(),
        )

        return await self.create_preference(preference)
