"""
Authentication API endpoints - Unified Cosmos DB Implementation.

Updated to use unified Cosmos DB per Tech Spec requirements.
"""

import logging
from datetime import datetime

from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_active_user
from app.core.zero_trust import require_permissions
from app.models.user import User
from app.repositories.cosmos_unified import UserDocument, UnifiedCosmosRepository
from app.schemas.auth import (
    UserCreate, UserUpdate, UserProfile, UserResponse, 
    LoginRequest, LoginResponse, AuthStatusResponse
)
from app.services.auth_unified import UnifiedAuthService
from fastapi import APIRouter, Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    cosmos_service = Depends(get_cosmos_service)
):
    """Register a new user with automatic Family Admin role assignment."""
    cosmos_repo = cosmos_service.get_repository()
    auth_service = UnifiedAuthService(cosmos_repo)

    try:
        # This now includes automatic family creation for Family Admin users
        user = await auth_service.create_user(user_data)

        # Log successful registration with role assignment
        logger.info(f"User registered as Family Admin with auto-family: {user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            onboarding_completed=user.onboarding_completed,
            family_ids=user.family_ids,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    request: Request,
    current_user = Depends(get_current_active_user),
    cosmos_service = Depends(get_cosmos_service)
):
    """Get current user profile with extended information."""
    cosmos_repo = cosmos_service.get_repository()
    auth_service = UnifiedAuthService(cosmos_repo)
    
    # Get user from Cosmos DB using the ID from token
    user = await auth_service.get_user_by_id(current_user.id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Create UserProfile response
    return UserProfile(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        phone=user.phone,
        picture=user.picture,
        preferences=user.preferences,
        is_active=user.is_active,
        is_verified=user.is_verified,
        onboarding_completed=user.onboarding_completed,
        onboarding_completed_at=user.onboarding_completed_at,
        family_ids=user.family_ids,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/entra/login", response_model=LoginResponse)
async def entra_login(
    login_request: LoginRequest,
    cosmos_service = Depends(get_cosmos_service)
):
    """Login using Microsoft Entra External ID token."""
    from app.services.entra_auth_service import EntraAuthService
    
    cosmos_repo = cosmos_service.get_repository()
    entra_service = EntraAuthService()
    
    try:
        result = await entra_service.process_entra_login(login_request.access_token)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Entra ID token"
            )
        
        user, internal_token = result
        
        # Convert UserDocument to UserProfile for response
        user_profile = UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            phone=user.phone,
            picture=user.picture,
            preferences=user.preferences,
            is_active=user.is_active,
            is_verified=user.is_verified,
            onboarding_completed=user.onboarding_completed,
            onboarding_completed_at=user.onboarding_completed_at,
            family_ids=user.family_ids,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return LoginResponse(
            access_token=internal_token,
            user=user_profile
        )
        
    except Exception as e:
        logger.error(f"Entra login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: Request,
    user_update: UserUpdate,
    current_user = Depends(get_current_active_user),
    cosmos_service = Depends(get_cosmos_service)
):
    """Update current user profile."""
    cosmos_repo = cosmos_service.get_repository()
    auth_service = UnifiedAuthService(cosmos_repo)

    try:
        user = await auth_service.update_user(current_user.id, user_update)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            onboarding_completed=user.onboarding_completed,
            family_ids=user.family_ids,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    current_user = Depends(get_current_active_user)
):
    """Logout user (mainly for logging purposes)."""
    logger.info(f"User {current_user.email} logged out")
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
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_service),
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
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_service),
):
    """Mark onboarding as completed for the current user."""
    try:
        auth_service = UnifiedAuthService(cosmos_repo)
        
        # Update user's onboarding status
        update_data = {
            "onboarding_completed": True,
            "onboarding_completed_at": datetime.utcnow(),
        }
        
        # Save trip type if provided
        if request.get("trip_type"):
            update_data["onboarding_trip_type"] = request["trip_type"]

        # Save any completion time analytics
        if request.get("completion_time"):
            logger.info(
                f"User {current_user.email} completed onboarding in {request['completion_time']}ms"
            )

        updated_user = await auth_service.update_user_fields(str(current_user.id), update_data)

        return {
            "success": True,
            "completed": True,
            "completed_at": updated_user.onboarding_completed_at,
        }

    except Exception as e:
        logger.error(f"Failed to complete onboarding for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete onboarding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding",
        )
