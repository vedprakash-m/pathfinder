"""
Simple unit tests for model classes to ensure they are exercised in test coverage.
"""

import uuid
from datetime import date, datetime, timezone

# Cosmos models - updated import paths for unified architecture
from app.schemas.notification import NotificationType

# SQL Trip model removed - use Cosmos TripDocument, TripStatus

# User model tests
# SQL User model removed - use Cosmos UserDocument, UserCreate, UserResponse, UserRole


def test_user_create_model():
    """Test User creation with valid data."""
    user_data = {
        "email": "test@example.com",
        "entra_id": "entra|testuser123",  # Required for Microsoft Entra External ID
        "name": "John Doe",
        "role": UserRole.FAMILY_ADMIN,
    }
    user_create = UserCreate(**user_data)
    assert user_create.email == "test@example.com"
    assert user_create.entra_id == "entra|testuser123"
    assert user_create.name == "John Doe"
    assert user_create.role == UserRole.FAMILY_ADMIN


def test_user_response_model():
    """Test UserResponse model."""
    user_data = {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "John Doe",
        "role": UserRole.FAMILY_ADMIN,
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.now(timezone.utc),
    }
    user_response = UserResponse(**user_data)
    assert user_response.email == "test@example.com"
    assert user_response.is_active is True


def test_user_role_enum():
    """Test UserRole enum values."""
    assert UserRole.SUPER_ADMIN == "super_admin"
    assert UserRole.FAMILY_ADMIN == "family_admin"
    assert UserRole.TRIP_ORGANIZER == "trip_organizer"
    assert UserRole.FAMILY_MEMBER == "family_member"


def test_family_member_role_enum():
    """Test FamilyRole enum values."""
    assert FamilyRole.COORDINATOR == "coordinator"
    assert FamilyRole.ADULT == "adult"
    assert FamilyRole.CHILD == "child"


def test_trip_status_enum():
    """Test TripStatus enum values."""
    assert TripStatus.PLANNING == "planning"
    assert TripStatus.CONFIRMED == "confirmed"
    assert TripStatus.IN_PROGRESS == "in_progress"
    assert TripStatus.COMPLETED == "completed"
    assert TripStatus.CANCELLED == "cancelled"


def test_notification_type_enum():
    """Test NotificationType enum values."""
    assert NotificationType.TRIP_INVITATION == "trip_invitation"
    assert NotificationType.TRIP_UPDATE == "trip_update"
    assert NotificationType.FAMILY_INVITATION == "family_invitation"
    assert NotificationType.ITINERARY_READY == "itinerary_ready"
    assert NotificationType.RESERVATION_CONFIRMED == "reservation_confirmed"


class TestModelCreation:
    """Test basic model instantiation."""

    def test_user_creation(self):
        """Test User model creation."""
        user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            name="Test User",
            role=UserRole.FAMILY_ADMIN,
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == UserRole.FAMILY_ADMIN

    def test_family_creation(self):
        """Test Family model creation."""
        family = Family(
            id=str(uuid.uuid4()),
            name="Test Family",
            admin_user_id=str(uuid.uuid4()),
            description="A test family",
        )
        assert family.name == "Test Family"
        assert family.description == "A test family"

    def test_trip_creation(self):
        """Test Trip model creation."""
        trip = Trip(
            id=str(uuid.uuid4()),
            name="Test Trip",
            destination="Paris",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 15),
            status=TripStatus.PLANNING,
            creator_id=str(uuid.uuid4()),
        )

        assert trip.name == "Test Trip"
        assert trip.destination == "Paris"
        assert trip.status == TripStatus.PLANNING
