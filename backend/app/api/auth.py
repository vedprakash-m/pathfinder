from __future__ import annotations

"""
Authentication API endpoints - Unified Cosmos DB Implementation.
"""

import logging
from datetime import datetime

from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.core.zero_trust import require_permissions
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserProfile,
    UserResponse,
    UserUpdate,
)
from app.services.auth_unified import UnifiedAuthService
from fastapi import APIRouter, Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_cosmos_repo() -> UnifiedCosmosRepository:
    """Get Cosmos repository dependency."""
    cosmos_service = get_cosmos_service()
    return cosmos_service.get_repository()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Register a new user with automatic Family Admin role assignment."""
    try:
        auth_service = UnifiedAuthService(cosmos_repo)
        user = await auth_service.create_user(user_data)

        logger.info(f"User registered as Family Admin: {user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            family_ids=user.family_ids,
            created_at=user.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        ) from e


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserDocument = Depends(get_current_user),
):
    """Get current user profile."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        phone=current_user.phone,
        picture=current_user.picture,
        preferences=current_user.preferences,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        onboarding_completed=current_user.onboarding_completed,
        onboarding_completed_at=current_user.onboarding_completed_at,
        family_ids=current_user.family_ids,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Update current user information."""
    try:
        # Update user fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)

        current_user.updated_at = datetime.utcnow()
        updated_user = await cosmos_repo.update_document(current_user)

        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            family_ids=updated_user.family_ids,
            created_at=updated_user.created_at,
        )

    except Exception as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed"
        ) from e
