"""
Reservation models for the Pathfinder application.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID


class ReservationType(str, Enum):
    """Reservation types."""

    ACCOMMODATION = "accommodation"
    RESTAURANT = "restaurant"
    ACTIVITY = "activity"
    ATTRACTION = "attraction"
    TRANSPORTATION = "transportation"
    RENTAL_CAR = "rental_car"
    FLIGHT = "flight"
    EVENT = "event"
    TOUR = "tour"
    CUSTOM = "custom"


class ReservationStatus(str, Enum):
    """Reservation status types."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status types."""

    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class CancellationPolicy(str, Enum):
    """Cancellation policy types."""

    FREE_CANCELLATION = "free_cancellation"
    MODERATE = "moderate"
    STRICT = "strict"
    NO_REFUND = "no_refund"


class Reservation(Base):
    """Reservation model."""

    __tablename__ = "reservations"

    id = Column(GUID(), primary_key=True, default=uuid4)
    trip_id = Column(GUID(), ForeignKey("trips.id"), nullable=False)
    family_id = Column(GUID(), ForeignKey("families.id"), nullable=False)
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Reservation details
    type = Column(SQLEnum(ReservationType), nullable=False)
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.PENDING)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.UNPAID)

    # Basic information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    provider_name = Column(String(200), nullable=True)  # Hotel name, restaurant name, etc.

    # Location information
    location_name = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    google_place_id = Column(String(100), nullable=True)

    # Timing
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    duration_hours = Column(Numeric(5, 2), nullable=True)

    # Capacity and pricing
    number_of_guests = Column(Integer, nullable=False, default=1)
    number_of_rooms = Column(Integer, nullable=True)  # For accommodations
    cost_per_person = Column(Numeric(10, 2), nullable=True)
    total_cost = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Booking information
    confirmation_number = Column(String(100), nullable=True)
    booking_reference = Column(String(100), nullable=True)
    booking_url = Column(Text, nullable=True)
    booking_email = Column(String(200), nullable=True)
    booking_phone = Column(String(20), nullable=True)

    # Policy and terms
    cancellation_policy = Column(SQLEnum(CancellationPolicy), nullable=True)
    cancellation_deadline = Column(DateTime, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)

    # Payment information
    deposit_amount = Column(Numeric(10, 2), nullable=True)
    deposit_paid_at = Column(DateTime, nullable=True)
    full_payment_due = Column(DateTime, nullable=True)
    payment_method = Column(String(50), nullable=True)

    # Additional details
    special_requests = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    confirmation_email_sent = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)

    # External integration
    external_booking_id = Column(String(100), nullable=True)
    external_provider = Column(String(50), nullable=True)  # booking.com, expedia, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="reservations")
    family = relationship("Family", back_populates="reservations")
    creator = relationship("User", foreign_keys=[created_by])


class ReservationDocument(Base):
    """Reservation document model for storing tickets, confirmations, etc."""

    __tablename__ = "reservation_documents"

    id = Column(GUID(), primary_key=True, default=uuid4)
    reservation_id = Column(GUID(), ForeignKey("reservations.id"), nullable=False)

    # Document details
    name = Column(String(200), nullable=False)
    document_type = Column(String(50), nullable=False)  # confirmation, ticket, receipt, etc.
    file_path = Column(String(500), nullable=True)
    file_url = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Metadata
    uploaded_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reservation = relationship("Reservation", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])


# Add relationship to Reservation model
Reservation.documents = relationship(
    "ReservationDocument", back_populates="reservation", cascade="all, delete-orphan"
)


# Pydantic models for API serialization
class ReservationDocumentBase(BaseModel):
    """Base reservation document model."""

    name: str = Field(..., max_length=200)
    document_type: str = Field(..., max_length=50)
    file_url: Optional[str] = None


class ReservationDocumentCreate(ReservationDocumentBase):
    """Reservation document creation model."""

    pass


class ReservationDocumentResponse(ReservationDocumentBase):
    """Reservation document response model."""

    id: UUID
    reservation_id: UUID
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ReservationBase(BaseModel):
    """Base reservation model."""

    type: ReservationType
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    provider_name: Optional[str] = Field(None, max_length=200)
    location_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    google_place_id: Optional[str] = Field(None, max_length=100)
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    duration_hours: Optional[Decimal] = None
    number_of_guests: int = 1
    number_of_rooms: Optional[int] = None
    cost_per_person: Optional[Decimal] = None
    total_cost: Decimal
    currency: str = Field(default="USD", max_length=3)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_reference: Optional[str] = Field(None, max_length=100)
    booking_url: Optional[str] = None
    booking_email: Optional[str] = Field(None, max_length=200)
    booking_phone: Optional[str] = Field(None, max_length=20)
    cancellation_policy: Optional[CancellationPolicy] = None
    cancellation_deadline: Optional[datetime] = None
    terms_and_conditions: Optional[str] = None
    deposit_amount: Optional[Decimal] = None
    full_payment_due: Optional[datetime] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    special_requests: Optional[str] = None
    notes: Optional[str] = None
    external_booking_id: Optional[str] = Field(None, max_length=100)
    external_provider: Optional[str] = Field(None, max_length=50)


class ReservationCreate(ReservationBase):
    """Reservation creation model."""

    trip_id: UUID
    family_id: UUID


class ReservationUpdate(BaseModel):
    """Reservation update model."""

    status: Optional[ReservationStatus] = None
    payment_status: Optional[PaymentStatus] = None
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    provider_name: Optional[str] = Field(None, max_length=200)
    location_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    google_place_id: Optional[str] = Field(None, max_length=100)
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    duration_hours: Optional[Decimal] = None
    number_of_guests: Optional[int] = None
    number_of_rooms: Optional[int] = None
    cost_per_person: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_reference: Optional[str] = Field(None, max_length=100)
    booking_url: Optional[str] = None
    booking_email: Optional[str] = Field(None, max_length=200)
    booking_phone: Optional[str] = Field(None, max_length=20)
    cancellation_policy: Optional[CancellationPolicy] = None
    cancellation_deadline: Optional[datetime] = None
    terms_and_conditions: Optional[str] = None
    deposit_amount: Optional[Decimal] = None
    deposit_paid_at: Optional[datetime] = None
    full_payment_due: Optional[datetime] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    special_requests: Optional[str] = None
    notes: Optional[str] = None
    external_booking_id: Optional[str] = Field(None, max_length=100)
    external_provider: Optional[str] = Field(None, max_length=50)


class ReservationResponse(ReservationBase):
    """Reservation response model."""

    id: UUID
    trip_id: UUID
    family_id: UUID
    created_by: UUID
    status: ReservationStatus
    payment_status: PaymentStatus
    deposit_paid_at: Optional[datetime] = None
    confirmation_email_sent: bool
    reminder_sent: bool
    documents: list[ReservationDocumentResponse] = []
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReservationListResponse(BaseModel):
    """Paginated reservation list response."""

    reservations: list[ReservationResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class ReservationSummary(BaseModel):
    """Reservation summary for trip overview."""

    total_reservations: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    total_cost: Decimal
    pending_payments: Decimal
    upcoming_deadlines: list[dict]


class ReservationFilters(BaseModel):
    """Reservation filtering options."""

    type: Optional[ReservationType] = None
    status: Optional[ReservationStatus] = None
    payment_status: Optional[PaymentStatus] = None
    family_id: Optional[UUID] = None
    check_in_from: Optional[datetime] = None
    check_in_to: Optional[datetime] = None
    min_cost: Optional[Decimal] = None
    max_cost: Optional[Decimal] = None
