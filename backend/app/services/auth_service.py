from __future__ import annotations

"""
Minimal Auth Service - Updated for Cosmos DB only.
This service is simplified during architectural repair.
"""

import logging
from typing import Optional

from app.core.config import get_settings
from app.core.database_unified import get_cosmos_service

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Minimal auth service using Cosmos DB."""

    def __init__(self):
        self.cosmos_service = get_cosmos_service()

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email from Cosmos DB."""
        try:
            # This will be implemented when we rebuild the API layer
            return {"email": email, "id": "temp", "role": "family_admin"}
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    async def create_user(self, db_session, user_data) -> dict:
        """Create user in Cosmos DB.

        Args:
            db_session: Database session (kept for interface compatibility)
            user_data: User creation data (UserCreate object or dict)

        Returns:
            dict: Created user data
        """
        try:
            # Convert UserCreate object to dict if needed
            if hasattr(user_data, "model_dump"):
                user_dict = user_data.model_dump()
            elif hasattr(user_data, "dict"):
                user_dict = user_data.dict()
            else:
                user_dict = user_data

            # This will be implemented when we rebuild the API layer
            return {
                "email": user_dict.get("email"),
                "id": "temp",
                "role": "family_admin",
                "entra_id": user_dict.get("entra_id"),
                "auth0_id": user_dict.get("auth0_id"),
                "name": user_dict.get("name"),
            }
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise


# Global auth service instance
auth_service = AuthService()
