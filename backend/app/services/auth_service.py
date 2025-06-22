"""
Authentication service for user management with Microsoft Entra External ID.

This module handles:
- User authentication with Microsoft Entra External ID (replacing Auth0)
- JWT token validation
- User profile management
- Session management
- Migration compatibility (supports both Auth0 and Entra External ID during transition)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User, UserCreate, UserUpdate
from app.services.entra_auth_service import EntraAuthService, EntraExternalIDError
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Service for handling authentication operations with Microsoft Entra External ID.
    Maintains backward compatibility with Auth0 during migration period.
    """

    def __init__(self):
        # Initialize Entra External ID service
        self.entra_service = EntraAuthService()
        
        # Legacy Auth0 settings for compatibility (can be removed after migration)
        self.auth0_domain = getattr(settings, 'AUTH0_DOMAIN', None)
        self.auth0_client_id = getattr(settings, 'AUTH0_CLIENT_ID', None)
        self.auth0_client_secret = getattr(settings, 'AUTH0_CLIENT_SECRET', None)
        self.auth0_audience = getattr(settings, 'AUTH0_AUDIENCE', None)
        
        logger.info("AuthService initialized with Entra External ID support")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    async def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate JWT token.
        Supports both Entra External ID and Auth0 tokens during migration.
        """
        try:
            # Try Entra External ID first
            payload = await self.entra_service.validate_token(token)
            if payload:
                logger.debug("Token validated as Entra External ID token")
                return payload

            # Fallback to legacy Auth0 validation for migration compatibility
            if self.auth0_domain and settings.ENVIRONMENT == "development":
                # Skip signature verification in development
                payload = jwt.get_unverified_claims(token)
                logger.debug("Token validated as Auth0 token (dev mode)")
                return payload

            return None

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user with automatic Family Admin role and family setup."""
        try:
            from uuid import uuid4
            from app.models.family import Family, FamilyMember, FamilyRole

            # Create user record with both auth fields for migration compatibility
            db_user = User(
                email=user_data.email,
                name=user_data.name,
                auth0_id=user_data.auth0_id,  # Legacy field
                entra_id=user_data.entra_id,  # New field
                picture=None,
                phone=user_data.phone,
                preferences=(
                    str(user_data.preferences) if user_data.preferences else None
                ),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(db_user)
            await db.flush()  # Get user ID without committing

            # 🔑 AUTO-CREATE FAMILY for new Family Admin users
            family = Family(
                id=uuid4(),
                name=(f"{db_user.name}'s Family" if db_user.name else f"{db_user.email}'s Family"),
                description="Auto-created family",
                admin_user_id=db_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(family)
            await db.flush()  # Get family ID

            # 🔑 AUTO-CREATE FAMILY MEMBER RECORD
            family_member = FamilyMember(
                id=uuid4(),
                family_id=family.id,
                user_id=db_user.id,
                name=db_user.name if db_user.name else db_user.email.split("@")[0],
                role=FamilyRole.COORDINATOR,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(family_member)
            await db.commit()
            await db.refresh(db_user)

            logger.info(f"Created user with auto-family: {db_user.email} (Family: {family.name})")
            return db_user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user with family: {e}")
            raise ValueError(f"User creation failed: {str(e)}")

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_auth0_id(self, db: AsyncSession, auth0_user_id: str) -> Optional[User]:
        """Get user by Auth0 user ID (legacy compatibility)."""
        result = await db.execute(select(User).filter(User.auth0_id == auth0_user_id))
        return result.scalar_one_or_none()

    async def get_user_by_entra_id(self, db: AsyncSession, entra_id: str) -> Optional[User]:
        """Get user by Entra External ID."""
        result = await db.execute(select(User).filter(User.entra_id == entra_id))
        return result.scalar_one_or_none()

    async def update_user(
        self, db: AsyncSession, user_id: str, user_update: UserUpdate
    ) -> Optional[User]:
        """Update user information."""
        try:
            db_user = await self.get_user_by_id(db, user_id)
            if not db_user:
                return None

            update_data = user_update.model_dump(exclude_unset=True)

            # Update fields
            for field, value in update_data.items():
                if hasattr(db_user, field):
                    setattr(db_user, field, value)

            db_user.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_user)
            return db_user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user: {e}")
            return None

    async def authenticate_user(
        self, db: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """Authenticate user with email and password (for local development only)."""
        user = await self.get_user_by_email(db, email)
        if not user:
            return None

        # For OAuth-only users, password authentication is not supported
        return None

    def create_access_token_for_user(self, user: User) -> str:
        """Create internal access token for user."""
        return create_access_token(data={"sub": str(user.id), "email": user.email})

    async def verify_token(self, token: str):
        """Verify token using new Entra External ID service."""
        return await self.decode_token(token)

    async def get_current_user(self, db: AsyncSession, token: str) -> Optional[User]:
        """Get current user from token."""
        try:
            payload = await self.decode_token(token)
            if not payload:
                return None

            # Try to find user by multiple identifiers
            user_id = payload.get("sub")
            email = payload.get("email") or payload.get("upn")

            if user_id:
                # First try by Entra ID
                user = await self.get_user_by_entra_id(db, user_id)
                if user:
                    return user

                # Then try by Auth0 ID (legacy)
                user = await self.get_user_by_auth0_id(db, user_id)
                if user:
                    return user

            # Finally try by email
            if email:
                user = await self.get_user_by_email(db, email)
                if user:
                    return user

            return None

        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None

    async def process_entra_login(
        self, db: AsyncSession, access_token: str
    ) -> Optional[tuple[User, str]]:
        """
        Process Entra External ID login and return user and internal token.
        This replaces the process_auth0_login method.
        """
        try:
            # Use the Entra service to process login
            result = await self.entra_service.process_entra_login(db, access_token)
            if result:
                user, internal_token = result
                logger.info(f"Successful Entra External ID login for: {user.email}")
                return user, internal_token
            
            return None

        except Exception as e:
            logger.error(f"Error processing Entra External ID login: {e}")
            return None

    # Legacy method for backward compatibility - marked for removal
    async def process_auth0_login(
        self, db: Session, access_token: str
    ) -> Optional[tuple[User, str]]:
        """
        Legacy Auth0 login method - maintained for backward compatibility.
        New implementations should use process_entra_login.
        """
        logger.warning("process_auth0_login is deprecated. Use process_entra_login instead.")
        
        # Convert to AsyncSession and delegate to Entra login
        if hasattr(db, 'execute'):  # Check if it's already an AsyncSession
            return await self.process_entra_login(db, access_token)
        else:
            logger.error("Legacy Auth0 login requires session conversion")
            return None

    def delete_user(self, db: Session, user_id: str) -> bool:
        """Delete user - placeholder for admin operations."""
        # Implementation would go here
        return False

    def get_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        email_filter: Optional[str] = None,
    ) -> List[User]:
        """Get users with pagination and filtering - placeholder for admin operations."""
        # Implementation would go here
        return []

    async def send_password_reset_email(self, email: str) -> bool:
        """Send password reset email - not applicable for OAuth-only authentication."""
        logger.info("Password reset not supported for OAuth-only authentication")
        return False

    def get_entra_login_url(self, redirect_uri: str, state: str = None) -> str:
        """
        Get Entra External ID login URL.
        This replaces get_auth0_login_url.
        """
        try:
            return self.entra_service.get_login_url(redirect_uri, state)
        except Exception as e:
            logger.error(f"Error generating Entra login URL: {e}")
            return ""

    # Legacy method for backward compatibility - marked for removal
    def get_auth0_login_url(self, redirect_uri: str) -> str:
        """
        Legacy Auth0 login URL method - maintained for backward compatibility.
        New implementations should use get_entra_login_url.
        """
        logger.warning("get_auth0_login_url is deprecated. Use get_entra_login_url instead.")
        return self.get_entra_login_url(redirect_uri)

    async def exchange_code_for_token(
        self, code: str, redirect_uri: str, state: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token using Entra External ID.
        This replaces the Auth0 token exchange.
        """
        try:
            return await self.entra_service.exchange_code_for_token(code, redirect_uri, state)
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on authentication service.
        """
        try:
            entra_health = await self.entra_service.health_check()
            
            return {
                "status": "healthy" if entra_health.get("status") == "healthy" else "degraded",
                "provider": "Microsoft Entra External ID",
                "legacy_support": self.auth0_domain is not None,
                "entra_service": entra_health,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global auth service instance
auth_service = AuthService()
