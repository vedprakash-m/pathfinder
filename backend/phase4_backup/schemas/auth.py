"""
Authentication schemas for API requests and responses.
Unified Cosmos DB implementation per Tech Spec.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    picture: Optional[str] = None


class UserProfile(BaseModel):
    """Schema for user profile response."""

    id: str
    email: str
    name: Optional[str] = None
    role: str
    phone: Optional[str] = None
    picture: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: bool
    is_verified: bool
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None
    family_ids: List[str]
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    """Schema for basic user response."""

    id: str
    email: str
    name: Optional[str] = None
    role: str
    is_active: bool
    onboarding_completed: bool
    family_ids: List[str]
    created_at: datetime


class LoginRequest(BaseModel):
    """Schema for login request."""

    access_token: str


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class RegisterRequest(BaseModel):
    """Schema for registration request."""

    email: EmailStr
    name: str
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthStatusResponse(BaseModel):
    """Schema for authentication status response."""

    authenticated: bool
    user: Optional[UserProfile] = None
