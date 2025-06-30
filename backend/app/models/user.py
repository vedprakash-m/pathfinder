"""
User model for authentication and profile management.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from app.core.database import GUID, Base
from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


class UserRole(str, Enum):
    """User roles aligned with UX specification."""

    SUPER_ADMIN = "super_admin"
    FAMILY_ADMIN = "family_admin"  # Default for all new users
    TRIP_ORGANIZER = "trip_organizer"  # Can be combined with family_admin
    FAMILY_MEMBER = "family_member"  # Invitation-only


class User(Base):
    """User model for SQLAlchemy."""

    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid4)
    auth0_id = Column(String(255), unique=True, index=True, nullable=True)  # Legacy field for migration
    entra_id = Column(String(255), unique=True, index=True, nullable=True)  # New Entra External ID
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    role = Column(
        SQLEnum(UserRole), nullable=False, default=UserRole.FAMILY_ADMIN
    )  # 🔑 DEFAULT ROLE
    picture = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Onboarding fields
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_trip_type = Column(
        String(50), nullable=True
    )  # weekend-getaway, family-vacation, adventure-trip

    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    administered_families = relationship(
        "Family", foreign_keys="Family.admin_user_id", back_populates="admin"
    )
    family_memberships = relationship("FamilyMember", back_populates="user")
    trip_participations = relationship("TripParticipation", back_populates="user")
    created_trips = relationship("Trip", back_populates="creator")
    notifications = relationship("Notification", back_populates="user")


# Pydantic models for API


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    name: Optional[str] = None
    role: Optional[UserRole] = UserRole.FAMILY_ADMIN  # 🔑 DEFAULT ROLE
    phone: Optional[str] = None
    preferences: Optional[dict] = None


class UserCreate(UserBase):
    """User creation model."""

    entra_id: str  # Required Entra External ID per Vedprakash Domain standards
    auth0_id: Optional[str] = None  # Legacy field for migration compatibility only


class UserUpdate(BaseModel):
    """User update model."""

    name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[dict] = None


class UserResponse(UserBase):
    """User response model."""

    id: str
    auth0_id: Optional[str] = None  # Legacy field for migration
    entra_id: Optional[str] = None  # New Entra External ID
    role: UserRole  # 🔑 INCLUDE ROLE IN RESPONSE
    picture: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Extended user profile model."""

    id: str
    email: str
    name: Optional[str] = None
    role: UserRole  # 🔑 INCLUDE ROLE IN PROFILE
    picture: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[dict] = None
    family_count: int = 0
    trip_count: int = 0
    is_family_admin: bool = False  # 🔑 CONVENIENCE FIELD

    class Config:
        from_attributes = True


class UserPreferences(BaseModel):
    """User preferences model."""

    dietary_restrictions: List[str] = []
    accessibility_needs: List[str] = []
    preferred_activities: List[str] = []
    budget_range: Optional[dict] = None
    travel_style: Optional[str] = None
    accommodation_preferences: List[str] = []
    transportation_preferences: List[str] = []
    notification_settings: dict = {
        "email_notifications": True,
        "push_notifications": True,
        "trip_updates": True,
        "family_updates": True,
    }

    class Config:
        from_attributes = True
