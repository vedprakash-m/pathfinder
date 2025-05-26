"""
Trip service for managing trips, participations, and related operations.
"""

import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging_config import get_logger
from app.models.trip import (
    Trip, TripParticipation, TripStatus, ParticipationStatus,
    TripCreate, TripUpdate, TripResponse, TripDetail, TripStats,
    ParticipationCreate, ParticipationUpdate, ParticipationResponse,
    TripInvitation
)
from app.models.family import Family
from app.models.user import User

logger = get_logger(__name__)


class TripService:
    """Service for managing trips and participations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_trip(self, trip_data: TripCreate, creator_id: str) -> TripResponse:
        """Create a new trip."""
        try:
            # Convert Pydantic model to dict and handle JSON serialization
            trip_dict = trip_data.dict(exclude={'family_ids'})
            if trip_data.preferences:
                trip_dict['preferences'] = json.dumps(trip_data.preferences.dict())
            else:
                trip_dict['preferences'] = None
            
            # Create trip instance
            trip = Trip(
                **trip_dict,
                creator_id=UUID(creator_id),
                status=TripStatus.PLANNING
            )
            
            self.db.add(trip)
            await self.db.commit()
            await self.db.refresh(trip)
            
            # Add family participations if provided
            if trip_data.family_ids:
                for family_id in trip_data.family_ids:
                    await self._add_family_participation(trip.id, family_id, creator_id)
            
            # Get trip with participation count
            trip_response = await self._build_trip_response(trip)
            
            logger.info(f"Trip created: {trip.id} by user {creator_id}")
            return trip_response
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating trip: {str(e)}")
            raise ValueError(f"Failed to create trip: {str(e)}")
    
    async def get_user_trips(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None
    ) -> List[TripResponse]:
        """Get trips for a user (created or participating)."""
        try:
            # Build query for trips where user is creator or participant
            query = select(Trip).options(
                selectinload(Trip.participations)
            ).where(
                (Trip.creator_id == UUID(user_id)) |
                (Trip.participations.any(TripParticipation.user_id == UUID(user_id)))
            )
            
            # Apply status filter if provided
            if status_filter:
                query = query.where(Trip.status == status_filter)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            trips = result.scalars().all()
            
            # Build response objects
            trip_responses = []
            for trip in trips:
                trip_response = await self._build_trip_response(trip)
                trip_responses.append(trip_response)
            
            return trip_responses
            
        except Exception as e:
            logger.error(f"Error getting user trips: {str(e)}")
            return []
    
    async def get_trip_by_id(self, trip_id: UUID, user_id: str) -> Optional[TripDetail]:
        """Get trip details by ID if user has access."""
        try:
            # Check if user has access to this trip
            if not await self._check_trip_access(trip_id, user_id):
                return None
            
            # Get trip with all related data
            query = select(Trip).options(
                selectinload(Trip.participations).selectinload(TripParticipation.family),
                selectinload(Trip.participations).selectinload(TripParticipation.user),
                selectinload(Trip.creator)
            ).where(Trip.id == trip_id)
            
            result = await self.db.execute(query)
            trip = result.scalar_one_or_none()
            
            if not trip:
                return None
            
            # Build detailed response
            participations = []
            for participation in trip.participations:
                participation_response = ParticipationResponse(
                    id=str(participation.id),
                    trip_id=str(participation.trip_id),
                    family_id=str(participation.family_id),
                    user_id=str(participation.user_id),
                    status=participation.status,
                    budget_allocation=float(participation.budget_allocation) if participation.budget_allocation else None,
                    preferences=json.loads(participation.preferences) if participation.preferences else None,
                    notes=participation.notes,
                    joined_at=participation.joined_at,
                    updated_at=participation.updated_at
                )
                participations.append(participation_response)
            
            trip_detail = TripDetail(
                id=str(trip.id),
                name=trip.name,
                description=trip.description,
                destination=trip.destination,
                start_date=trip.start_date,
                end_date=trip.end_date,
                status=trip.status,
                budget_total=float(trip.budget_total) if trip.budget_total else None,
                preferences=json.loads(trip.preferences) if trip.preferences else None,
                is_public=trip.is_public,
                creator_id=str(trip.creator_id),
                created_at=trip.created_at,
                updated_at=trip.updated_at,
                family_count=len(trip.participations),
                confirmed_families=len([p for p in trip.participations if p.status == ParticipationStatus.CONFIRMED]),
                participations=participations,
                has_itinerary=bool(trip.itinerary_data)
            )
            
            return trip_detail
            
        except Exception as e:
            logger.error(f"Error getting trip {trip_id}: {str(e)}")
            return None
    
    async def update_trip(self, trip_id: UUID, trip_update: TripUpdate, user_id: str) -> TripResponse:
        """Update trip details."""
        try:
            # Check if user is trip creator
            trip = await self._get_trip_by_id(trip_id)
            if not trip:
                raise ValueError("Trip not found")
            
            if str(trip.creator_id) != user_id:
                raise PermissionError("Only trip creator can update trip details")
            
            # Update trip fields
            update_data = trip_update.dict(exclude_unset=True)
            if 'preferences' in update_data and update_data['preferences']:
                update_data['preferences'] = json.dumps(update_data['preferences'].dict())
            
            for field, value in update_data.items():
                if hasattr(trip, field):
                    setattr(trip, field, value)
            
            trip.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(trip)
            
            trip_response = await self._build_trip_response(trip)
            
            logger.info(f"Trip updated: {trip_id} by user {user_id}")
            return trip_response
            
        except (ValueError, PermissionError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating trip {trip_id}: {str(e)}")
            raise ValueError(f"Failed to update trip: {str(e)}")
    
    async def delete_trip(self, trip_id: UUID, user_id: str) -> None:
        """Delete a trip."""
        try:
            # Check if user is trip creator
            trip = await self._get_trip_by_id(trip_id)
            if not trip:
                raise ValueError("Trip not found")
            
            if str(trip.creator_id) != user_id:
                raise PermissionError("Only trip creator can delete the trip")
            
            # Delete trip (cascade will handle participations)
            await self.db.delete(trip)
            await self.db.commit()
            
            logger.info(f"Trip deleted: {trip_id} by user {user_id}")
            
        except (ValueError, PermissionError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting trip {trip_id}: {str(e)}")
            raise ValueError(f"Failed to delete trip: {str(e)}")
    
    async def get_trip_stats(self, trip_id: UUID, user_id: str) -> Optional[TripStats]:
        """Get trip statistics."""
        try:
            # Check access
            if not await self._check_trip_access(trip_id, user_id):
                return None
            
            trip = await self._get_trip_by_id(trip_id)
            if not trip:
                return None
            
            # Calculate statistics
            total_families = len(trip.participations)
            confirmed_families = len([p for p in trip.participations if p.status == ParticipationStatus.CONFIRMED])
            pending_families = len([p for p in trip.participations if p.status == ParticipationStatus.PENDING])
            
            # Calculate budget stats
            budget_allocated = sum(
                float(p.budget_allocation) for p in trip.participations 
                if p.budget_allocation
            )
            budget_spent = 0.0  # TODO: Calculate from reservations/expenses
            
            # Calculate days until trip
            days_until_trip = None
            if trip.start_date:
                days_until_trip = (trip.start_date - date.today()).days
                days_until_trip = max(0, days_until_trip)  # Don't show negative days
            
            # Calculate completion percentage
            completion_percentage = self._calculate_completion_percentage(trip)
            
            stats = TripStats(
                total_families=total_families,
                confirmed_families=confirmed_families,
                pending_families=pending_families,
                total_participants=total_families,  # TODO: Calculate actual participant count from family members
                budget_allocated=budget_allocated,
                budget_spent=budget_spent,
                days_until_trip=days_until_trip,
                completion_percentage=completion_percentage
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting trip stats {trip_id}: {str(e)}")
            return None
    
    # Participation methods
    
    async def add_participant(self, participation_data: ParticipationCreate, user_id: str) -> ParticipationResponse:
        """Add a family to the trip."""
        try:
            trip_id = UUID(participation_data.trip_id)
            family_id = UUID(participation_data.family_id)
            
            # Check if user has permission to add participants
            if not await self._check_trip_admin_access(trip_id, user_id):
                raise ValueError("Not authorized to add participants to this trip")
            
            # Check if family is already participating
            existing = await self.db.execute(
                select(TripParticipation).where(
                    and_(
                        TripParticipation.trip_id == trip_id,
                        TripParticipation.family_id == family_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Family is already participating in this trip")
            
            # Create participation
            participation = TripParticipation(
                trip_id=trip_id,
                family_id=family_id,
                user_id=UUID(user_id),
                status=participation_data.status,
                budget_allocation=participation_data.budget_allocation,
                preferences=json.dumps(participation_data.preferences) if participation_data.preferences else None,
                notes=participation_data.notes
            )
            
            self.db.add(participation)
            await self.db.commit()
            await self.db.refresh(participation)
            
            response = ParticipationResponse(
                id=str(participation.id),
                trip_id=str(participation.trip_id),
                family_id=str(participation.family_id),
                user_id=str(participation.user_id),
                status=participation.status,
                budget_allocation=float(participation.budget_allocation) if participation.budget_allocation else None,
                preferences=json.loads(participation.preferences) if participation.preferences else None,
                notes=participation.notes,
                joined_at=participation.joined_at,
                updated_at=participation.updated_at
            )
            
            logger.info(f"Participant added to trip {trip_id}: family {family_id}")
            return response
            
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding participant: {str(e)}")
            raise ValueError(f"Failed to add participant: {str(e)}")
    
    async def get_trip_participants(self, trip_id: UUID, user_id: str) -> List[ParticipationResponse]:
        """Get trip participants."""
        try:
            # Check access
            if not await self._check_trip_access(trip_id, user_id):
                return []
            
            # Get participations
            query = select(TripParticipation).where(
                TripParticipation.trip_id == trip_id
            )
            
            result = await self.db.execute(query)
            participations = result.scalars().all()
            
            responses = []
            for participation in participations:
                response = ParticipationResponse(
                    id=str(participation.id),
                    trip_id=str(participation.trip_id),
                    family_id=str(participation.family_id),
                    user_id=str(participation.user_id),
                    status=participation.status,
                    budget_allocation=float(participation.budget_allocation) if participation.budget_allocation else None,
                    preferences=json.loads(participation.preferences) if participation.preferences else None,
                    notes=participation.notes,
                    joined_at=participation.joined_at,
                    updated_at=participation.updated_at
                )
                responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting trip participants: {str(e)}")
            return []
    
    async def update_participation(
        self, 
        participation_id: UUID, 
        participation_update: ParticipationUpdate, 
        user_id: str
    ) -> ParticipationResponse:
        """Update family participation status."""
        try:
            # Get participation
            participation = await self.db.get(TripParticipation, participation_id)
            if not participation:
                raise ValueError("Participation not found")
            
            # Check permission (trip creator or family member)
            is_trip_admin = await self._check_trip_admin_access(participation.trip_id, user_id)
            is_family_member = await self._check_family_membership(participation.family_id, user_id)
            
            if not (is_trip_admin or is_family_member):
                raise PermissionError("Not authorized to update this participation")
            
            # Update participation
            update_data = participation_update.dict(exclude_unset=True)
            if 'preferences' in update_data and update_data['preferences']:
                update_data['preferences'] = json.dumps(update_data['preferences'])
            
            for field, value in update_data.items():
                if hasattr(participation, field):
                    setattr(participation, field, value)
            
            participation.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(participation)
            
            response = ParticipationResponse(
                id=str(participation.id),
                trip_id=str(participation.trip_id),
                family_id=str(participation.family_id),
                user_id=str(participation.user_id),
                status=participation.status,
                budget_allocation=float(participation.budget_allocation) if participation.budget_allocation else None,
                preferences=json.loads(participation.preferences) if participation.preferences else None,
                notes=participation.notes,
                joined_at=participation.joined_at,
                updated_at=participation.updated_at
            )
            
            logger.info(f"Participation updated: {participation_id} by user {user_id}")
            return response
            
        except (ValueError, PermissionError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating participation {participation_id}: {str(e)}")
            raise ValueError(f"Failed to update participation: {str(e)}")
    
    async def remove_participant(self, participation_id: UUID, user_id: str) -> None:
        """Remove a family from the trip."""
        try:
            # Get participation
            participation = await self.db.get(TripParticipation, participation_id)
            if not participation:
                raise ValueError("Participation not found")
            
            # Check permission (only trip creator can remove participants)
            if not await self._check_trip_admin_access(participation.trip_id, user_id):
                raise PermissionError("Only trip creator can remove participants")
            
            # Delete participation
            await self.db.delete(participation)
            await self.db.commit()
            
            logger.info(f"Participant removed: {participation_id} by user {user_id}")
            
        except (ValueError, PermissionError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error removing participant {participation_id}: {str(e)}")
            raise ValueError(f"Failed to remove participant: {str(e)}")
    
    async def send_invitation(self, invitation_data: TripInvitation, user_id: str) -> None:
        """Send trip invitation to a family."""
        try:
            trip_id = UUID(invitation_data.trip_id)
            family_id = UUID(invitation_data.family_id)
            
            # Check if user has permission to send invitations
            if not await self._check_trip_admin_access(trip_id, user_id):
                raise ValueError("Not authorized to send invitations for this trip")
            
            # Check if family exists
            family = await self.db.get(Family, family_id)
            if not family:
                raise ValueError("Family not found")
            
            # Check if family is already participating
            existing = await self.db.execute(
                select(TripParticipation).where(
                    and_(
                        TripParticipation.trip_id == trip_id,
                        TripParticipation.family_id == family_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Family is already participating in this trip")
            
            # Create invitation (as pending participation)
            participation = TripParticipation(
                trip_id=trip_id,
                family_id=family_id,
                user_id=UUID(user_id),
                status=ParticipationStatus.INVITED
            )
            
            self.db.add(participation)
            await self.db.commit()
            
            # TODO: Send actual notification/email
            logger.info(f"Invitation sent to family {family_id} for trip {trip_id}")
            
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error sending invitation: {str(e)}")
            raise ValueError(f"Failed to send invitation: {str(e)}")
    
    # Helper methods
    
    async def _get_trip_by_id(self, trip_id: UUID) -> Optional[Trip]:
        """Get trip by ID with participations loaded."""
        query = select(Trip).options(
            selectinload(Trip.participations)
        ).where(Trip.id == trip_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _check_trip_access(self, trip_id: UUID, user_id: str) -> bool:
        """Check if user has access to the trip."""
        query = select(Trip).where(
            and_(
                Trip.id == trip_id,
                (Trip.creator_id == UUID(user_id)) |
                (Trip.participations.any(TripParticipation.user_id == UUID(user_id)))
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _check_trip_admin_access(self, trip_id: UUID, user_id: str) -> bool:
        """Check if user is the trip creator."""
        query = select(Trip).where(
            and_(
                Trip.id == trip_id,
                Trip.creator_id == UUID(user_id)
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _check_family_membership(self, family_id: UUID, user_id: str) -> bool:
        """Check if user is a member of the family."""
        from app.models.family import FamilyMembership
        
        query = select(FamilyMembership).where(
            and_(
                FamilyMembership.family_id == family_id,
                FamilyMembership.user_id == UUID(user_id)
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _add_family_participation(self, trip_id: UUID, family_id: str, user_id: str) -> None:
        """Add family participation to trip."""
        participation = TripParticipation(
            trip_id=trip_id,
            family_id=UUID(family_id),
            user_id=UUID(user_id),
            status=ParticipationStatus.CONFIRMED
        )
        
        self.db.add(participation)
    
    async def _build_trip_response(self, trip: Trip) -> TripResponse:
        """Build TripResponse from Trip model."""
        return TripResponse(
            id=str(trip.id),
            name=trip.name,
            description=trip.description,
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            status=trip.status,
            budget_total=float(trip.budget_total) if trip.budget_total else None,
            preferences=json.loads(trip.preferences) if trip.preferences else None,
            is_public=trip.is_public,
            creator_id=str(trip.creator_id),
            created_at=trip.created_at,
            updated_at=trip.updated_at,
            family_count=len(trip.participations),
            confirmed_families=len([p for p in trip.participations if p.status == ParticipationStatus.CONFIRMED])
        )
    
    def _calculate_completion_percentage(self, trip: Trip) -> float:
        """Calculate trip planning completion percentage."""
        completion_factors = []
        
        # Basic trip info (25%)
        completion_factors.append(25.0 if all([trip.name, trip.destination, trip.start_date, trip.end_date]) else 0.0)
        
        # Participants confirmed (25%)
        total_participants = len(trip.participations)
        confirmed_participants = len([p for p in trip.participations if p.status == ParticipationStatus.CONFIRMED])
        completion_factors.append(25.0 * (confirmed_participants / max(1, total_participants)))
        
        # Budget planning (25%)
        budget_completion = 0.0
        if trip.budget_total:
            allocated_budget = sum(
                float(p.budget_allocation) for p in trip.participations 
                if p.budget_allocation
            )
            budget_completion = min(25.0, 25.0 * (allocated_budget / float(trip.budget_total)))
        completion_factors.append(budget_completion)
        
        # Itinerary (25%)
        completion_factors.append(25.0 if trip.itinerary_data else 0.0)
        
        return sum(completion_factors)
