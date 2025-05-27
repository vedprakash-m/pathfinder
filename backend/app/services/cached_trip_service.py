"""
Cached trip service implementing Redis caching with the hybrid database approach.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService
from app.models.cosmos.message import MessageDocument, MessageType, MessageStatus
from app.models.cosmos.preference import PreferenceDocument, PreferenceType
from app.models.cosmos.itinerary import ItineraryDocument
from app.services.trip_service import TripService
from app.models.trip import TripResponse, TripDetail, TripStats

logger = logging.getLogger(__name__)


class CachedTripService(TripService):
    """
    Enhanced trip service with Redis caching to optimize database access.
    This service extends the standard TripService by adding a caching layer
    that reduces database load and improves response times.
    """
    
    def __init__(self, db: AsyncSession, cache_service: CacheService):
        """Initialize with database session and cache service."""
        super().__init__(db)
        self.cache = cache_service
        
    async def get_trip_by_id(self, trip_id: UUID, user_id: str) -> Optional[TripDetail]:
        """
        Get trip details by ID with caching.
        First checks cache before falling back to database.
        """
        cache_key = f"trip:{trip_id}:detail"
        cached_trip = await self.cache.get(cache_key, cache_type="trip_data")
        
        if cached_trip:
            logger.debug(f"Cache hit for trip {trip_id}")
            return cached_trip
        
        # Cache miss, get from database
        trip = await super().get_trip_by_id(trip_id, user_id)
        
        if trip:
            # Store in cache (5 minutes TTL for trip data)
            await self.cache.set(cache_key, trip, cache_type="trip_data")
            
        return trip
        
    async def get_user_trips(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None
    ) -> List[TripResponse]:
        """
        Get trips for a user with caching for improved performance.
        """
        # Create a cache key that includes pagination and filters
        filter_part = f":status={status_filter}" if status_filter else ""
        cache_key = f"user:{user_id}:trips{filter_part}:skip={skip}:limit={limit}"
        
        cached_trips = await self.cache.get(cache_key, cache_type="trip_data")
        if cached_trips:
            logger.debug(f"Cache hit for user trips - user {user_id}")
            return cached_trips
        
        # Cache miss, get from database
        trips = await super().get_user_trips(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status_filter=status_filter
        )
        
        if trips:
            # Store in cache (shorter TTL for lists)
            await self.cache.set(cache_key, trips, cache_type="trip_data", ttl=60)
            
        return trips
    
    async def get_trip_stats(self, trip_id: UUID, user_id: str) -> Optional[TripStats]:
        """
        Get trip statistics with caching.
        Stats are frequently accessed but change infrequently.
        """
        cache_key = f"trip:{trip_id}:stats"
        
        cached_stats = await self.cache.get(cache_key, cache_type="trip_data")
        if cached_stats:
            logger.debug(f"Cache hit for trip stats {trip_id}")
            return cached_stats
        
        # Cache miss, calculate from database
        stats = await super().get_trip_stats(trip_id, user_id)
        
        if stats:
            # Store in cache (1 minute TTL for stats as they're accessed frequently)
            await self.cache.set(cache_key, stats, cache_type="trip_data", ttl=60)
            
        return stats
    
    async def update_trip(self, trip_id: UUID, trip_update: Any, user_id: str) -> TripResponse:
        """
        Update trip details and invalidate cache.
        """
        # Execute the update
        trip_response = await super().update_trip(trip_id, trip_update, user_id)
        
        # Invalidate related caches
        await self._invalidate_trip_caches(trip_id, user_id)
        
        return trip_response
    
    async def delete_trip(self, trip_id: UUID, user_id: str) -> None:
        """
        Delete a trip and clear all related caches.
        """
        # Invalidate caches first
        await self._invalidate_trip_caches(trip_id, user_id)
        
        # Execute the delete
        await super().delete_trip(trip_id, user_id)
    
    async def _invalidate_trip_caches(self, trip_id: UUID, user_id: str) -> None:
        """
        Invalidate all caches related to a specific trip.
        This ensures consistency after mutations.
        """
        # Clear specific trip caches
        trip_key = f"trip:{trip_id}"
        await self.cache.clear_pattern(trip_key)
        
        # Clear user trips list caches
        user_trips_key = f"user:{user_id}:trips"
        await self.cache.clear_pattern(user_trips_key)
        
    async def save_itinerary(self, trip_id: UUID, itinerary_data: Dict[str, Any], user_id: str) -> bool:
        """Save itinerary data with cache invalidation."""
        result = await super().save_itinerary(trip_id, itinerary_data, user_id)
        
        if result:
            # Invalidate itinerary caches
            await self.cache.clear_pattern(f"trip:{trip_id}:itinerary")
            await self.cache.clear_pattern(f"trip:{trip_id}:detail")
            
        return result

    # Enhanced Cosmos DB operations with caching

    async def get_trip_messages(
        self,
        trip_id: str,
        room_id: Optional[str] = None,
        limit: int = 50
    ) -> List[MessageDocument]:
        """
        Get trip messages with caching for improved performance.
        """
        # Create a cache key that includes room and limit
        room_part = f":room={room_id}" if room_id else ""
        cache_key = f"trip:{trip_id}:messages{room_part}:limit={limit}"
        
        cached_messages = await self.cache.get(cache_key, cache_type="trip_data")
        if cached_messages:
            logger.debug(f"Cache hit for trip messages - trip {trip_id}")
            return cached_messages
        
        # Cache miss, get from Cosmos DB
        messages = await self.cosmos_ops.get_trip_messages(
            trip_id=trip_id,
            room_id=room_id,
            limit=limit
        )
        
        if messages:
            # Short TTL for messages (30 seconds) as they change frequently
            await self.cache.set(cache_key, messages, cache_type="trip_data", ttl=30)
            
        return messages
    
    async def get_trip_preferences_from_cosmos(
        self,
        trip_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get trip preferences from Cosmos DB with caching.
        """
        cache_key = f"trip:{trip_id}:preferences"
        
        cached_prefs = await self.cache.get(cache_key, cache_type="trip_data")
        if cached_prefs:
            logger.debug(f"Cache hit for trip preferences - trip {trip_id}")
            return cached_prefs
        
        # Cache miss, get from Cosmos DB
        preferences = await self.cosmos_ops.get_trip_preferences_from_cosmos(trip_id)
        
        if preferences:
            # Store in cache (5 minutes TTL for preferences)
            await self.cache.set(cache_key, preferences, cache_type="trip_data")
            
        return preferences
    
    async def send_trip_message(
        self,
        trip_id: str,
        sender_id: str,
        sender_name: str,
        text: str,
        message_type: MessageType = MessageType.CHAT,
        room_id: Optional[str] = None
    ) -> Optional[MessageDocument]:
        """
        Send a trip message and invalidate relevant message caches.
        """
        # Send the message
        message = await self.cosmos_ops.send_trip_message(
            trip_id=trip_id,
            sender_id=sender_id,
            sender_name=sender_name,
            text=text,
            message_type=message_type,
            room_id=room_id
        )
        
        if message:
            # Invalidate message list caches for this trip/room
            room_part = f":room={room_id}" if room_id else ""
            cache_pattern = f"trip:{trip_id}:messages{room_part}"
            await self.cache.clear_pattern(cache_pattern)
            
        return message
