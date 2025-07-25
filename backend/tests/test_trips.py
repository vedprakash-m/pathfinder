"""
Tests for trip service functionality.
"""

from datetime import date, datetime, timedelta

import pytest
from app.models.cosmos.enums import ParticipationStatus, TripStatus

# Cosmos models - updated import paths for unified architecture
from app.models.cosmos.trip import ParticipationStatus, TripCreate, TripDocument

# Backward compatibility aliases
TripUpdate = TripDocument

# SQL User model removed - use Cosmos UserDocument


@pytest.mark.asyncio
async def test_create_trip(trip_service, test_user, test_family):
    """Test creating a new trip."""
    # Arrange
    user_id = str(test_user.id)
    trip_data = TripCreate(
        name="New Trip",
        description="A new test trip",
        destination="New Destination",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=37),
        budget_total=5000.00,
        family_ids=[str(test_family.id)],
        is_public=False,
    )

    # Act - Create trip directly with repository
    trip_response = await trip_service.create_trip(trip_data, user_id)

    # Assert
    assert trip_response is not None
    assert trip_response.name == "New Trip"
    assert trip_response.description == "A new test trip"
    assert trip_response.destination == "New Destination"
    assert trip_response.status == TripStatus.PLANNING
    assert str(trip_response.creator_id) == user_id


@pytest.mark.asyncio
async def test_get_user_trips(trip_service, test_user, test_trip):
    """Test retrieving trips for a user."""
    # Arrange
    user_id = str(test_user.id)

    # Act
    trips = await trip_service.get_user_trips(user_id)

    # Assert
    assert len(trips) >= 1
    assert any(str(trip.id) == str(test_trip.id) for trip in trips)


@pytest.mark.asyncio
async def test_get_trip_by_id(trip_service, test_user, test_trip):
    """Test retrieving a trip by ID."""
    # Arrange
    user_id = str(test_user.id)
    trip_id = test_trip.id

    # Act
    trip_detail = await trip_service.get_trip_by_id(trip_id, user_id)

    # Assert
    assert trip_detail is not None
    assert str(trip_detail.id) == str(test_trip.id)
    assert trip_detail.name == test_trip.name
    assert trip_detail.destination == test_trip.destination


@pytest.mark.asyncio
async def test_update_trip(trip_service, test_user, test_trip):
    """Test updating a trip's details."""
    # Arrange
    user_id = str(test_user.id)
    trip_id = test_trip.id
    trip_update = TripUpdate(name="Updated Trip Name", description="Updated description")

    # Act
    updated_trip = await trip_service.update_trip(trip_id, trip_update, user_id)

    # Assert
    assert updated_trip is not None
    assert updated_trip.name == "Updated Trip Name"
    assert updated_trip.description == "Updated description"


@pytest.mark.asyncio
async def test_delete_trip(trip_service, test_user, test_trip):
    """Test deleting a trip."""
    # Arrange
    user_id = str(test_user.id)
    trip_id = test_trip.id

    # Act
    await trip_service.delete_trip(trip_id, user_id)

    # Assert - trip should no longer be retrievable
    deleted_trip = await trip_service.get_trip_by_id(trip_id, user_id)
    assert deleted_trip is None


@pytest.mark.asyncio
async def test_get_trip_stats(trip_service, test_user, test_trip, test_trip_participation):
    """Test retrieving trip statistics."""
    # Arrange
    user_id = str(test_user.id)
    trip_id = test_trip.id

    # Act
    trip_stats = await trip_service.get_trip_stats(trip_id, user_id)

    # Assert
    assert trip_stats is not None
    assert trip_stats.total_families >= 1
    assert trip_stats.confirmed_families >= 1
    assert trip_stats.budget_allocated > 0
    assert trip_stats.days_until_trip is not None


@pytest.mark.asyncio
async def test_add_family_to_trip(trip_service, test_user, test_trip, db_session):
    """Test adding a new family to a trip."""
    # Arrange
    user_id = str(test_user.id)
    trip_id = test_trip.id

    # Create a new family
    new_family = Family(
        name="New Test Family",
        admin_user_id=test_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db_session.add(new_family)
    await db_session.commit()

    family_id = str(new_family.id)

    # Act
    participation = await trip_service.add_family_to_trip(
        trip_id, family_id, user_id, budget_allocation=1500.00
    )

    # Assert
    assert participation is not None
    assert str(participation.trip_id) == str(trip_id)
    assert str(participation.family_id) == family_id
    assert participation.budget_allocation == 1500.00
    assert participation.status == ParticipationStatus.CONFIRMED


@pytest.mark.asyncio
async def test_cannot_update_trip_without_permission(trip_service, test_trip, db_session):
    """Test that a non-creator cannot update a trip."""
    # Arrange
    # Create another user
    other_user = User(
        email="other@example.com",
        auth0_id="auth0|other123456",
        name="Other User",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    user_id = str(other_user.id)
    trip_id = test_trip.id
    trip_update = TripUpdate(name="Unauthorized Update")

    # Act & Assert
    with pytest.raises(PermissionError):
        await trip_service.update_trip(trip_id, trip_update, user_id)


@pytest.mark.asyncio
async def test_cannot_delete_trip_without_permission(trip_service, test_trip, db_session):
    """Test that a non-creator cannot delete a trip."""
    # Arrange
    # Create another user
    other_user = User(
        email="other@example.com",
        auth0_id="auth0|other123456",
        name="Other User",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    user_id = str(other_user.id)
    trip_id = test_trip.id

    # Act & Assert
    with pytest.raises(PermissionError):
        await trip_service.delete_trip(trip_id, user_id)
