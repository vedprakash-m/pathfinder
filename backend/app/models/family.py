"""
Family model for group management and coordination.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from app.core.database import Base, GUID


class FamilyRole(str, Enum):
    """Family member roles."""

    COORDINATOR = "coordinator"
    ADULT = "adult"
    CHILD = "child"


class InvitationStatus(str, Enum):
    """Family invitation status."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Family(Base):
    """Family model for SQLAlchemy."""

    __tablename__ = "families"

    id = Column(GUID(), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    admin_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    preferences = Column(Text, nullable=True)  # JSON string
    emergency_contact = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    admin = relationship(
        "User", foreign_keys="Family.admin_user_id", back_populates="administered_families"
    )
    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    invitations = relationship(
        "FamilyInvitationModel", back_populates="family", cascade="all, delete-orphan"
    )
    trip_participations = relationship("TripParticipation", back_populates="family")
    reservations = relationship("Reservation", back_populates="family")
    notifications = relationship("Notification", back_populates="family")


class FamilyMember(Base):
    """Family member model for SQLAlchemy."""

    __tablename__ = "family_members"

    id = Column(GUID(), primary_key=True, default=uuid4)
    family_id = Column(GUID(), ForeignKey("families.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(FamilyRole), nullable=False)
    age = Column(Integer, nullable=True)
    dietary_restrictions = Column(Text, nullable=True)  # JSON string
    accessibility_needs = Column(Text, nullable=True)  # JSON string
    emergency_contact = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    family = relationship("Family", back_populates="members")
    user = relationship("User", back_populates="family_memberships")


class FamilyInvitationModel(Base):
    """Family invitation model for SQLAlchemy."""

    __tablename__ = "family_invitations"

    id = Column(GUID(), primary_key=True, default=uuid4)
    family_id = Column(GUID(), ForeignKey("families.id"), nullable=False)
    invited_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(SQLEnum(FamilyRole), nullable=False, default=FamilyRole.ADULT)
    status = Column(SQLEnum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING)
    invitation_token = Column(String(255), nullable=False, unique=True)
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    family = relationship("Family", back_populates="invitations")
    inviter = relationship("User")


# Pydantic models for API


class EmergencyContact(BaseModel):
    """Emergency contact information."""

    name: str
    relationship: str
    phone: str
    email: Optional[str] = None


class FamilyPreferences(BaseModel):
    """Family preferences model."""

    dietary_restrictions: List[str] = []
    accessibility_needs: List[str] = []
    preferred_activities: List[str] = []
    budget_range: Optional[dict] = None
    accommodation_preferences: List[str] = []
    emergency_contacts: List[EmergencyContact] = []


class FamilyMemberBase(BaseModel):
    """Base family member model."""

    name: str
    role: FamilyRole
    age: Optional[int] = None
    dietary_restrictions: List[str] = []
    accessibility_needs: List[str] = []
    emergency_contact: Optional[EmergencyContact] = None


class FamilyMemberCreate(FamilyMemberBase):
    """Family member creation model."""

    user_id: Optional[str] = None


class FamilyMemberUpdate(BaseModel):
    """Family member update model."""

    name: Optional[str] = None
    role: Optional[FamilyRole] = None
    age: Optional[int] = None
    dietary_restrictions: Optional[List[str]] = None
    accessibility_needs: Optional[List[str]] = None
    emergency_contact: Optional[EmergencyContact] = None
    is_active: Optional[bool] = None


class FamilyMemberResponse(FamilyMemberBase):
    """Family member response model."""

    id: str
    family_id: str
    user_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FamilyBase(BaseModel):
    """Base family model."""

    name: str
    description: Optional[str] = None
    preferences: Optional[FamilyPreferences] = None


class FamilyCreate(FamilyBase):
    """Family creation model."""

    coordinator_user_id: str


class FamilyUpdate(BaseModel):
    """Family update model."""

    name: Optional[str] = None
    description: Optional[str] = None
    preferences: Optional[FamilyPreferences] = None
    is_active: Optional[bool] = None


class FamilyResponse(FamilyBase):
    """Family response model."""

    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: int = 0

    class Config:
        from_attributes = True


class FamilyDetail(FamilyResponse):
    """Detailed family model with members."""

    members: List[FamilyMemberResponse] = []


class FamilyInvitationBase(BaseModel):
    """Base family invitation model."""

    family_id: str
    email: str
    role: FamilyRole
    message: Optional[str] = None
    expires_at: datetime


class FamilyInvitationCreate(FamilyInvitationBase):
    """Family invitation creation model."""

    pass


class FamilyInvitationUpdate(BaseModel):
    """Family invitation update model."""

    email: Optional[str] = None
    role: Optional[FamilyRole] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    status: Optional[InvitationStatus] = None


class FamilyInvitationResponse(FamilyInvitationBase):
    """Family invitation response model."""

    id: str
    invited_by: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
