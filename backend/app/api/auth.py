"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.models.user import User, UserCreate, UserUpdate, UserResponse, UserProfile
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile with extended information."""
    auth_service = AuthService(db)
    return await auth_service.get_user_profile(current_user.id)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.update_user(current_user.id, user_update)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout user (mainly for logging purposes)."""
    # In a real Auth0 implementation, you might want to revoke tokens
    # or perform cleanup operations
    return {"message": "Successfully logged out"}


@router.get("/validate")
async def validate_token(
    current_user: User = Depends(get_current_user)
):
    """Validate the current authentication token."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }