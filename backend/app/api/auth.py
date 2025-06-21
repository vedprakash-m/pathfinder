"""
Authentication API endpoints.
"""

import logging
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.zero_trust import require_permissions
from app.models.user import User, UserCreate, UserProfile, UserResponse, UserUpdate
from app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with automatic Family Admin role assignment."""
    auth_service = AuthService()

    try:
        # This now includes automatic family creation for Family Admin users
        user = await auth_service.create_user(db, user_data)

        # Log successful registration with role assignment
        logger.info(
            f"User registered as Family Admin with auto-family: {user.email}")

        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(require_permissions("user", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile with extended information."""
    auth_service = AuthService()
    user = auth_service.get_user_by_id(db, str(current_user.id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Create UserProfile response with additional fields
    return UserProfile(
        id=str(user.id),
        email=user.email,
        name=user.name,
        picture=user.picture,
        phone=user.phone,
        preferences=user.preferences,
        family_count=0,  # TODO: Calculate actual family count
        trip_count=0,  # TODO: Calculate actual trip count
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: Request,
    user_update: UserUpdate,
    current_user: User = Depends(require_permissions("user", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    auth_service = AuthService()

    try:
        user = auth_service.update_user(db, str(current_user.id), user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(require_permissions("user", "logout")),
):
    """Logout user (mainly for logging purposes)."""
    # In a real Auth0 implementation, you might want to revoke tokens
    # or perform cleanup operations
    return {"message": "Successfully logged out"}


@router.get("/validate")
async def validate_token(
    request: Request, current_user: User = Depends(require_permissions("user", "read"))
):
    """Validate the current authentication token."""
    return {"valid": True, "user_id": current_user.id, "email": current_user.email}


# Onboarding endpoints
@router.get("/user/onboarding-status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's onboarding status."""
    return {
        "completed": current_user.onboarding_completed or False,
        "completed_at": current_user.onboarding_completed_at,
        "trip_type": current_user.onboarding_trip_type,
    }


@router.post("/user/complete-onboarding")
async def complete_onboarding(
    request: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark onboarding as completed for the current user."""
    try:
        # Update user's onboarding status
        current_user.onboarding_completed = True
        current_user.onboarding_completed_at = datetime.utcnow()

        # Save trip type if provided
        if request.get("trip_type"):
            current_user.onboarding_trip_type = request["trip_type"]

        # Save any completion time analytics
        if request.get("completion_time"):
            logger.info(
                f"User {current_user.email} completed onboarding in {request['completion_time']}ms"
            )

        await db.commit()
        await db.refresh(current_user)

        return {
            "success": True,
            "completed": True,
            "completed_at": current_user.onboarding_completed_at,
        }

    except Exception as e:
        logger.error(
            f"Failed to complete onboarding for user {current_user.email}: {str(e)}"
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding",
        )
