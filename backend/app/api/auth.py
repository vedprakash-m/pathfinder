"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.core.zero_trust import require_permissions
from app.models.user import User, UserCreate, UserUpdate, UserResponse, UserProfile
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    auth_service = AuthService()
    
    try:
        user = await auth_service.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(require_permissions("user", "read")),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile with extended information."""
    auth_service = AuthService()
    user = auth_service.get_user_by_id(db, str(current_user.id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
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
        trip_count=0     # TODO: Calculate actual trip count
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: Request,
    user_update: UserUpdate,
    current_user: User = Depends(require_permissions("user", "update")),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    auth_service = AuthService()
    
    try:
        user = auth_service.update_user(db, str(current_user.id), user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(require_permissions("user", "logout"))
):
    """Logout user (mainly for logging purposes)."""
    # In a real Auth0 implementation, you might want to revoke tokens
    # or perform cleanup operations
    return {"message": "Successfully logged out"}


@router.get("/validate")
async def validate_token(
    request: Request,
    current_user: User = Depends(require_permissions("user", "read"))
):
    """Validate the current authentication token."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }