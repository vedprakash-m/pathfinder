"""
Unified Authentication Service using Cosmos DB per Tech Spec.

This service replaces the SQL-based authentication with Cosmos DB unified approach
while maintaining 100% compliance with Apps_Auth_Requirement.md standards.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.config import get_settings
from app.core.database_unified import get_cosmos_repository
from app.repositories.cosmos_unified import FamilyDocument, UserDocument
from app.services.entra_auth_service import EntraAuthService

settings = get_settings()
logger = logging.getLogger(__name__)


class UnifiedAuthService:
    """
    Unified authentication service using Cosmos DB.

    Implements Apps_Auth_Requirement.md standards:
    - Microsoft Entra ID integration
    - VedUser interface compliance
    - Family auto-creation for new users
    """

    def __init__(self, cosmos_repo=None):
        """Initialize the unified auth service."""
        self.cosmos_repo = cosmos_repo or get_cosmos_repository()
        self.entra_service = EntraAuthService()
        logger.info("Unified AuthService initialized with Cosmos DB")

    async def get_or_create_user_from_token(self, token_payload: Dict[str, Any]) -> UserDocument:
        """
        Get or create user from Entra ID token payload.

        This implements the VedUser interface per Apps_Auth_Requirement.md
        """
        entra_id = token_payload.get("sub")
        email = token_payload.get("email")
        name = token_payload.get("name")

        if not entra_id or not email:
            raise ValueError("Invalid token payload: missing sub or email")

        # Try to find existing user by Entra ID
        user = await self.cosmos_repo.get_user_by_entra_id(entra_id)

        if user:
            # Update last login
            await self.cosmos_repo.update_user(user.id, {"updated_at": datetime.utcnow()})
            logger.info(f"Existing user logged in: {user.email}")
            return user

        # Try to find by email (migration scenario)
        user = await self.cosmos_repo.get_user_by_email(email)

        if user:
            # Update with Entra ID
            await self.cosmos_repo.update_user(
                user.id, {"entra_id": entra_id, "updated_at": datetime.utcnow()}
            )
            logger.info(f"Migrated user to Entra ID: {user.email}")
            return user

        # Create new user with auto-family creation
        return await self._create_new_user_with_family(entra_id, email, name, token_payload)

    async def _create_new_user_with_family(
        self, entra_id: str, email: str, name: Optional[str], token_payload: Dict[str, Any]
    ) -> UserDocument:
        """
        Create new user with automatic family creation per Tech Spec.

        Implements family-atomic architecture: new users automatically get a family.
        """
        _user_id = str(uuid4())

        # Create user document
        user_data = {
            "entra_id": entra_id,
            "email": email,
            "name": name,
            "role": "family_admin",  # Default role per UX Spec
            "picture": token_payload.get("picture"),
            "is_active": True,
            "is_verified": True,  # Entra ID users are pre-verified
            "onboarding_completed": False,
        }

        user = await self.cosmos_repo.create_user(user_data)

        # Auto-create family for new user (family-atomic architecture)
        family_name = f"{name}'s Family" if name else f"{email.split('@')[0]}'s Family"
        family_data = {
            "name": family_name,
            "description": "Auto-created family for new user",
            "admin_user_id": user.id,
            "members_count": 1,
            "member_ids": [user.id],
        }

        family = await self.cosmos_repo.create_family(family_data)

        # Update user with family association
        await self.cosmos_repo.update_user(user.id, {"family_ids": [family.id]})

        logger.info(f"Created new user with auto-family: {email} -> {family.name}")
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[UserDocument]:
        """Get user by ID."""
        return await self.cosmos_repo.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[UserDocument]:
        """Get user by email."""
        return await self.cosmos_repo.get_user_by_email(email)

    async def get_user_by_entra_id(self, entra_id: str) -> Optional[UserDocument]:
        """Get user by Entra ID."""
        return await self.cosmos_repo.get_user_by_entra_id(entra_id)

    async def update_user_onboarding(
        self, user_id: str, trip_type: str, completed: bool = True
    ) -> UserDocument:
        """Update user onboarding status."""
        update_data = {
            "onboarding_completed": completed,
            "onboarding_trip_type": trip_type,
            "updated_at": datetime.utcnow(),
        }

        if completed:
            update_data["onboarding_completed_at"] = datetime.utcnow()

        return await self.cosmos_repo.update_user(user_id, update_data)

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token using Entra External ID.

        Returns token payload if valid, None if invalid.
        """
        try:
            return await self.entra_service.validate_token(token)
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None

    async def get_user_families(self, user_id: str):
        """Get all families for a user."""
        return await self.cosmos_repo.get_user_families(user_id)

    async def create_user(self, user_data) -> UserDocument:
        """Create a new user with automatic family creation."""

        _user_id = str(uuid4())
        family_id = str(uuid4())

        # Create user document
        user_doc = UserDocument(
            id=user_id,
            pk=f"user_{user_id}",
            email=user_data.email,
            name=user_data.name,
            phone=user_data.phone if hasattr(user_data, "phone") else None,
            preferences=user_data.preferences if hasattr(user_data, "preferences") else None,
            role="family_admin",  # Default role per PRD
            is_active=True,
            family_ids=[family_id],
        )

        # Create family document with user as admin
        family_doc = FamilyDocument(
            id=family_id,
            pk=f"family_{family_id}",
            name=f"{user_data.name or user_data.email.split('@')[0]}'s Family",
            admin_user_id=user_id,
            member_ids=[user_id],
            members_count=1,
        )

        # Save both documents to Cosmos DB
        await self.cosmos_repo.create_user(user_doc)
        await self.cosmos_repo.create_family(family_doc)

        logger.info(f"Created user {user_id} with auto-family {family_id}")
        return user_doc

    async def update_user(self, user_id: str, update_data) -> Optional[UserDocument]:
        """Update user information."""
        try:
            # Convert update_data to dict if it's a Pydantic model
            if hasattr(update_data, "dict"):
                update_dict = update_data.dict(exclude_unset=True)
            else:
                update_dict = update_data

            # Add updated_at timestamp
            update_dict["updated_at"] = datetime.utcnow()

            # Update user in Cosmos DB
            updated_user = await self.cosmos_repo.update_user(user_id, update_dict)

            logger.info(f"Updated user {user_id}")
            return updated_user

        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return None


# Global unified auth service instance
unified_auth_service = UnifiedAuthService()


def get_unified_auth_service() -> UnifiedAuthService:
    """Dependency to get the unified auth service."""
    return unified_auth_service
