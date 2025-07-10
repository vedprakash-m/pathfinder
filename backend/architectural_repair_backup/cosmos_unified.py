"""
Unified Cosmos DB Repository - Implementation per Tech Spec.

This module implements the Tech Spec requirement for a single Cosmos DB container
with all entities using a unified data model approach.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from app.core.config import get_settings
from azure.cosmos import CosmosClient, exceptions
from pydantic import BaseModel, Field

settings = get_settings()
logger = logging.getLogger(__name__)


class CosmosDocument(BaseModel):
    """Base document structure for all Cosmos DB entities."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pk: str = Field(..., description="Partition key for the document")
    entity_type: str = Field(..., description="Type of entity (user, family, trip, etc.)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, description="Document version for optimistic concurrency")


class UserDocument(CosmosDocument):
    """User document structure for Cosmos DB."""

    entity_type: Literal["user"] = "user"
    pk: str = Field(..., description="user_{user_id}")

    # Authentication fields
    auth0_id: Optional[str] = None  # Legacy - to be removed
    entra_id: Optional[str] = None
    email: str
    name: Optional[str] = None
    role: str = "family_admin"  # Default role
    picture: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

    # Status fields
    is_active: bool = True
    is_verified: bool = False

    # Onboarding fields
    onboarding_completed: bool = False
    onboarding_completed_at: Optional[datetime] = None
    onboarding_trip_type: Optional[str] = None

    # Relationships
    family_ids: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FamilyDocument(CosmosDocument):
    """Family document structure for Cosmos DB."""

    entity_type: Literal["family"] = "family"
    pk: str = Field(..., description="family_{family_id}")

    name: str
    description: Optional[str] = None
    admin_user_id: str
    members_count: int = 0
    settings: Optional[Dict[str, Any]] = None

    # Family member tracking
    member_ids: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TripDocument(CosmosDocument):
    """Trip document structure for Cosmos DB."""

    entity_type: Literal["trip"] = "trip"
    pk: str = Field(..., description="trip_{trip_id}")

    title: str
    description: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "planning"  # planning, confirmed, in_progress, completed, cancelled
    budget: Optional[float] = None

    # Relationships
    organizer_user_id: str
    participating_family_ids: List[str] = Field(default_factory=list)

    # Trip-specific data
    itinerary: Optional[Dict[str, Any]] = None
    expenses: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MessageDocument(CosmosDocument):
    """Message document structure for Cosmos DB."""

    entity_type: Literal["message"] = "message"
    pk: str = Field(..., description="trip_{trip_id}")

    trip_id: str
    user_id: str
    user_name: str
    content: str
    message_type: str = "text"  # text, system, poll, consensus

    # Message metadata
    thread_id: Optional[str] = None
    reply_to_id: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FamilyInvitationDocument(CosmosDocument):
    """Family invitation document structure for Cosmos DB."""

    entity_type: Literal["family_invitation"] = "family_invitation"
    pk: str = Field(..., description="family_{family_id}")

    family_id: str
    invited_by: str
    email: str
    role: str  # FamilyRole enum value
    status: str = "pending"  # InvitationStatus enum value
    invitation_token: str
    message: Optional[str] = None
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ReservationDocument(CosmosDocument):
    """Reservation document structure for Cosmos DB."""

    entity_type: Literal["reservation"] = "reservation"
    pk: str = Field(..., description="trip_{trip_id}")

    trip_id: str
    type: str  # ReservationType enum value
    name: str
    description: Optional[str] = None
    date: str  # ISO date string
    time: Optional[str] = None
    duration_hours: Optional[float] = None
    location: str
    address: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    cost_per_person: Optional[float] = None
    total_cost: Optional[float] = None
    capacity: Optional[int] = None
    participants: Optional[List[str]] = None  # user IDs
    booking_reference: Optional[str] = None
    status: str = "pending"  # ReservationStatus enum value
    cancellation_policy: Optional[str] = None
    special_requirements: Optional[str] = None
    external_booking_url: Optional[str] = None
    created_by: str


class FeedbackDocument(CosmosDocument):
    """Feedback document structure for Cosmos DB."""

    entity_type: Literal["feedback"] = "feedback"
    pk: str = Field(..., description="trip_{trip_id}")

    trip_id: str
    family_id: str
    user_id: str
    feedback_type: str  # FeedbackType enum value
    target_element: str
    content: str
    suggested_change: Optional[str] = None
    status: str = "pending"  # FeedbackStatus enum value
    response_content: Optional[str] = None
    decision: Optional[str] = None  # "approve", "reject", "modify"
    impact_analysis: Optional[Dict[str, Any]] = None
    next_steps: Optional[List[str]] = None


class ExportDocument(CosmosDocument):
    """Export task document structure for Cosmos DB."""

    entity_type: Literal["export"] = "export"
    pk: str = Field(..., description="user_{user_id}")

    user_id: str
    trip_id: Optional[str] = None
    trip_ids: Optional[List[str]] = None  # For bulk exports
    format: str = "excel"  # export format
    export_type: str = "complete"  # export type
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    file_url: Optional[str] = None
    error_message: Optional[str] = None
    progress: int = 0  # 0-100
    task_id: Optional[str] = None  # Background task ID


class ItineraryDocument(CosmosDocument):
    """Itinerary document structure for Cosmos DB."""

    entity_type: Literal["itinerary"] = "itinerary"
    pk: str = Field(..., description="trip_{trip_id}")

    trip_id: str
    title: str
    description: Optional[str] = None
    itinerary_type: str = "full_trip"  # ItineraryType enum value
    days: List[Dict[str, Any]]  # List of ItineraryDay data
    total_estimated_cost: Optional[float] = None
    customizations: Optional[Dict[str, Any]] = None  # ItineraryCustomization data
    ai_confidence_score: Optional[float] = None
    alternatives: Optional[List[Dict[str, Any]]] = None
    optimization_suggestions: Optional[List[str]] = None
    generated_by: str  # user_id who generated it
    is_active: bool = True  # Whether this is the current itinerary


class UnifiedCosmosRepository:
    """
    Unified repository for all Cosmos DB operations.

    Implements Tech Spec requirement:
    "Single Cosmos DB account (SQL API) in serverless mode for all persistent data"
    """

    def __init__(self):
        """Initialize the unified Cosmos DB repository."""
        self.container_name = "entities"
        self.database_name = settings.COSMOS_DB_DATABASE

        # Initialize Cosmos client
        if settings.COSMOS_DB_ENABLED and settings.COSMOS_DB_URL and settings.COSMOS_DB_KEY:
            try:
                self.client = CosmosClient(
                    settings.COSMOS_DB_URL, credential=settings.COSMOS_DB_KEY
                )
                self.database = self.client.get_database_client(self.database_name)

                # Ensure container exists with proper configuration
                self._ensure_container_exists()

                self.container = self.database.get_container_client(self.container_name)
                logger.info(f"Connected to unified Cosmos DB container: {self.container_name}")

            except Exception as e:
                logger.error(f"Failed to connect to Cosmos DB: {str(e)}")
                self.client = None
                self.database = None
                self.container = None
        else:
            # Development mode or missing credentials
            logger.warning("Cosmos DB not configured - using simulation mode")
            self.client = None
            self.database = None
            self.container = None
            self._simulation_data = {}

    def _ensure_container_exists(self):
        """Ensure the unified entities container exists with proper configuration."""
        try:
            container_definition = {
                "id": self.container_name,
                "partitionKey": {"paths": ["/pk"], "kind": "Hash"},
                "indexingPolicy": {
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [{"path": "/*"}],
                    "excludedPaths": [
                        {"path": "/preferences/*"},
                        {"path": "/itinerary/*"},
                        {"path": "/expenses/*"},
                    ],
                    "compositeIndexes": [
                        [
                            {"path": "/entity_type", "order": "ascending"},
                            {"path": "/created_at", "order": "descending"},
                        ],
                        [
                            {"path": "/pk", "order": "ascending"},
                            {"path": "/updated_at", "order": "descending"},
                        ],
                    ],
                },
            }

            self.database.create_container_if_not_exists(
                body=container_definition, offer_throughput=None  # Use serverless
            )
            logger.info(f"Ensured container '{self.container_name}' exists with proper indexing")

        except Exception as e:
            logger.error(f"Failed to ensure container exists: {str(e)}")
            raise

    async def initialize_container(self):
        """Initialize the Cosmos DB container with proper indexing and settings."""
        try:
            # Check if in simulation mode
            if self.client is None:
                logger.info("Cosmos DB in simulation mode - skipping container initialization")
                return

            # Ensure database exists
            database = self.client.create_database_if_not_exists(id=self.database_name)

            # Container properties with optimized indexing per Tech Spec
            container_properties = {
                "id": self.container_name,
                "partitionKey": {"paths": ["/pk"], "kind": "Hash"},
                "indexingPolicy": {
                    "indexingMode": "consistent",
                    "includedPaths": [{"path": "/*"}],
                    "excludedPaths": [{"path": '/"_etag"/?'}],
                    "compositeIndexes": [
                        [
                            {"path": "/entity_type", "order": "ascending"},
                            {"path": "/created_at", "order": "descending"},
                        ],
                        [
                            {"path": "/entity_type", "order": "ascending"},
                            {"path": "/creator_id", "order": "ascending"},
                        ],
                    ],
                },
            }

            # Create container with serverless throughput
            self.container = database.create_container_if_not_exists(
                body=container_properties, offer_throughput=None  # Serverless mode
            )

            logger.info(f"Cosmos DB container '{self.container_name}' initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB container: {e}")
            raise

    async def create_user(self, user_data: Dict[str, Any]) -> UserDocument:
        """Create a new user document."""
        user_id = str(uuid.uuid4())
        user_doc = UserDocument(id=user_id, pk=f"user_{user_id}", **user_data)

        return await self._create_document(user_doc)

    async def get_user_by_id(self, user_id: str) -> Optional[UserDocument]:
        """Get user by ID."""
        return await self._get_document(f"user_{user_id}", user_id, UserDocument)

    async def get_user_by_email(self, email: str) -> Optional[UserDocument]:
        """Get user by email address."""
        query = "SELECT * FROM c WHERE c.entity_type = 'user' AND c.email = @email"
        params = [{"name": "@email", "value": email}]

        results = await self._query_documents(query, params)
        if results:
            return UserDocument(**results[0])
        return None

    async def get_user_by_entra_id(self, entra_id: str) -> Optional[UserDocument]:
        """Get user by Entra ID."""
        query = "SELECT * FROM c WHERE c.entity_type = 'user' AND c.entra_id = @entra_id"
        params = [{"name": "@entra_id", "value": entra_id}]

        results = await self._query_documents(query, params)
        if results:
            return UserDocument(**results[0])
        return None

    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> UserDocument:
        """Update user document."""
        user_doc = await self.get_user_by_id(user_id)
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        # Update fields
        for key, value in update_data.items():
            if hasattr(user_doc, key):
                setattr(user_doc, key, value)

        user_doc.updated_at = datetime.utcnow()
        user_doc.version += 1

        return await self._update_document(user_doc)

    async def create_family(self, family_data: Dict[str, Any]) -> FamilyDocument:
        """Create a new family document."""
        family_id = str(uuid.uuid4())
        family_doc = FamilyDocument(id=family_id, pk=f"family_{family_id}", **family_data)

        return await self._create_document(family_doc)

    async def get_family_by_id(self, family_id: str) -> Optional[FamilyDocument]:
        """Get family by ID."""
        return await self._get_document(f"family_{family_id}", family_id, FamilyDocument)

    async def get_user_families(self, user_id: str) -> List[FamilyDocument]:
        """Get all families for a user."""
        query = """
        SELECT * FROM c 
        WHERE c.entity_type = 'family' 
        AND ARRAY_CONTAINS(c.member_ids, @user_id)
        """
        params = [{"name": "@user_id", "value": user_id}]

        results = await self._query_documents(query, params)
        return [FamilyDocument(**doc) for doc in results]

    async def get_family(self, family_id: str) -> Optional[FamilyDocument]:
        """Get family by ID (alias for consistency)."""
        return await self.get_family_by_id(family_id)

    async def update_family(self, family_id: str, update_data: Dict[str, Any]) -> FamilyDocument:
        """Update family data."""
        family_doc = await self.get_family_by_id(family_id)
        if not family_doc:
            raise ValueError(f"Family {family_id} not found")

        # Update fields
        for key, value in update_data.items():
            if hasattr(family_doc, key):
                setattr(family_doc, key, value)

        family_doc.updated_at = datetime.utcnow()
        return await self._update_document(family_doc)

    async def delete_family(self, family_id: str) -> None:
        """Delete a family."""
        await self._delete_document(f"family_{family_id}", family_id)

    async def add_user_to_family(self, user_id: str, family_id: str) -> None:
        """Add a user to a family's member list."""
        family_doc = await self.get_family_by_id(family_id)
        if not family_doc:
            raise ValueError(f"Family {family_id} not found")

        if user_id not in family_doc.member_ids:
            family_doc.member_ids.append(user_id)
            family_doc.members_count = len(family_doc.member_ids)
            family_doc.updated_at = datetime.utcnow()
            await self._update_document(family_doc)

    async def remove_user_from_family(self, user_id: str, family_id: str) -> None:
        """Remove a user from a family's member list."""
        family_doc = await self.get_family_by_id(family_id)
        if not family_doc:
            raise ValueError(f"Family {family_id} not found")

        if user_id in family_doc.member_ids:
            family_doc.member_ids.remove(user_id)
            family_doc.members_count = len(family_doc.member_ids)
            family_doc.updated_at = datetime.utcnow()
            await self._update_document(family_doc)

    async def create_trip(self, trip_data: Any, creator_id: str = None) -> TripDocument:
        """Create a new trip document."""
        trip_id = str(uuid.uuid4())

        # Handle both TripCreate objects and dictionaries
        if hasattr(trip_data, "dict"):
            data = trip_data.dict()
        else:
            data = trip_data if isinstance(trip_data, dict) else {}

        # Ensure organizer_user_id is set (support both creator_id and organizer_user_id)
        if creator_id:
            data["organizer_user_id"] = creator_id
        elif "creator_id" in data:
            data["organizer_user_id"] = data.pop("creator_id")
        elif "organizer_user_id" not in data:
            raise ValueError("Trip must have an organizer_user_id")

        trip_doc = TripDocument(id=trip_id, pk=f"trip_{trip_id}", **data)

        return await self._create_document(trip_doc)

    async def get_trip_by_id(self, trip_id: str) -> Optional[TripDocument]:
        """Get trip by ID."""
        return await self._get_document(f"trip_{trip_id}", trip_id, TripDocument)

    async def get_family_trips(self, family_id: str) -> List[TripDocument]:
        """Get all trips for a family."""
        query = """
        SELECT * FROM c 
        WHERE c.entity_type = 'trip' 
        AND ARRAY_CONTAINS(c.participating_family_ids, @family_id)
        ORDER BY c.created_at DESC
        """
        params = [{"name": "@family_id", "value": family_id}]

        results = await self._query_documents(query, params)
        return [TripDocument(**doc) for doc in results]

    async def create_message(self, message_data: Dict[str, Any]) -> MessageDocument:
        """Create a new message document."""
        message_id = str(uuid.uuid4())
        trip_id = message_data.get("trip_id")

        message_doc = MessageDocument(
            id=message_id,
            pk=f"trip_{trip_id}",  # Partition by trip for efficient queries
            **message_data,
        )

        return await self._create_document(message_doc)

    async def get_trip_messages(self, trip_id: str, limit: int = 50) -> List[MessageDocument]:
        """Get messages for a trip."""
        query = """
        SELECT * FROM c 
        WHERE c.entity_type = 'message' 
        AND c.trip_id = @trip_id
        ORDER BY c.created_at DESC
        OFFSET 0 LIMIT @limit
        """
        params = [{"name": "@trip_id", "value": trip_id}, {"name": "@limit", "value": limit}]

        results = await self._query_documents(query, params)
        return [MessageDocument(**doc) for doc in results]

    async def get_user_trips(
        self, user_id: str, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None
    ) -> List[TripDocument]:
        """Get all trips for a user (creator or participant)."""
        query = (
            """
        SELECT * FROM c 
        WHERE c.entity_type = 'trip' 
        AND (c.creator_id = @user_id OR ARRAY_CONTAINS(c.participants, @user_id))
        """
            + (" AND c.status = @status" if status_filter else "")
            + """
        ORDER BY c.created_at DESC
        OFFSET @skip LIMIT @limit
        """
        )

        params = [
            {"name": "@user_id", "value": user_id},
            {"name": "@skip", "value": skip},
            {"name": "@limit", "value": limit},
        ]

        if status_filter:
            params.append({"name": "@status", "value": status_filter})

        results = await self._query_documents(query, params)
        return [TripDocument(**doc) for doc in results]

    async def update_trip(self, trip_id: str, trip_update: Any) -> TripDocument:
        """Update an existing trip."""
        # Get existing trip
        existing_trip = await self.get_trip_by_id(trip_id)
        if not existing_trip:
            raise ValueError(f"Trip {trip_id} not found")

        # Apply updates
        update_data = (
            trip_update.dict(exclude_unset=True) if hasattr(trip_update, "dict") else trip_update
        )
        for field, value in update_data.items():
            if hasattr(existing_trip, field):
                setattr(existing_trip, field, value)

        # Update timestamps
        existing_trip.updated_at = datetime.utcnow()
        existing_trip.version += 1

        # Save to Cosmos DB
        return await self._update_document(existing_trip)

    async def delete_trip(self, trip_id: str) -> None:
        """Delete a trip and related documents."""
        try:
            # Delete the trip document
            await self.container.delete_item(item=trip_id, partition_key=f"trip_{trip_id}")

            # Delete related messages
            messages_query = """
            SELECT c.id FROM c 
            WHERE c.entity_type = 'message' 
            AND c.trip_id = @trip_id
            """
            message_results = await self._query_documents(
                messages_query, [{"name": "@trip_id", "value": trip_id}]
            )

            for message in message_results:
                await self.container.delete_item(
                    item=message["id"], partition_key=f"trip_{trip_id}"
                )

            logger.info(
                f"Successfully deleted trip {trip_id} and {len(message_results)} related messages"
            )

        except Exception as e:
            logger.error(f"Failed to delete trip {trip_id}: {e}")
            raise

    # Family Invitation Methods

    async def create_family_invitation(
        self, invitation_data: Dict[str, Any]
    ) -> FamilyInvitationDocument:
        """Create a new family invitation."""
        invitation_doc = FamilyInvitationDocument(
            pk=f"family_{invitation_data['family_id']}", **invitation_data
        )
        await self._create_document(invitation_doc)
        logger.info(f"Created family invitation: {invitation_doc.id}")
        return invitation_doc

    async def get_family_invitation_by_token(
        self, token: str
    ) -> Optional[FamilyInvitationDocument]:
        """Get a family invitation by token."""
        query = "SELECT * FROM c WHERE c.entity_type = 'family_invitation' AND c.invitation_token = @token"
        parameters = [{"name": "@token", "value": token}]

        results = await self._query_documents(query, parameters)
        if results:
            return FamilyInvitationDocument(**results[0])
        return None

    async def get_family_invitations(self, family_id: str) -> List[FamilyInvitationDocument]:
        """Get all invitations for a family."""
        query = (
            "SELECT * FROM c WHERE c.entity_type = 'family_invitation' AND c.family_id = @family_id"
        )
        parameters = [{"name": "@family_id", "value": family_id}]

        results = await self._query_documents(query, parameters)
        return [FamilyInvitationDocument(**result) for result in results]

    async def update_family_invitation(
        self, invitation_id: str, update_data: Dict[str, Any]
    ) -> Optional[FamilyInvitationDocument]:
        """Update a family invitation."""
        # First get the invitation to know the partition key
        query = "SELECT * FROM c WHERE c.entity_type = 'family_invitation' AND c.id = @id"
        parameters = [{"name": "@id", "value": invitation_id}]

        results = await self._query_documents(query, parameters)
        if not results:
            return None

        invitation = FamilyInvitationDocument(**results[0])

        # Update fields
        for key, value in update_data.items():
            if hasattr(invitation, key):
                setattr(invitation, key, value)

        invitation.updated_at = datetime.utcnow()
        updated_invitation = await self._update_document(invitation)
        logger.info(f"Updated family invitation: {invitation_id}")
        return updated_invitation

    # Trip Message Methods

    async def get_trip_messages(
        self, trip_id: str, room_id: Optional[str] = None, limit: int = 50
    ) -> List[MessageDocument]:
        """Get messages for a trip."""
        query = "SELECT * FROM c WHERE c.entity_type = 'message' AND c.trip_id = @trip_id"
        parameters = [{"name": "@trip_id", "value": trip_id}]

        if room_id:
            query += " AND c.room_id = @room_id"
            parameters.append({"name": "@room_id", "value": room_id})

        query += " ORDER BY c.created_at DESC"

        if limit:
            query += f" OFFSET 0 LIMIT {limit}"

        results = await self._query_documents(query, parameters)
        return [MessageDocument(**result) for result in results]

    async def send_trip_message(
        self,
        trip_id: str,
        sender_id: str,
        sender_name: str,
        text: str,
        message_type: str = "chat",
        room_id: Optional[str] = None,
    ) -> MessageDocument:
        """Send a message in a trip."""
        message_doc = MessageDocument(
            pk=f"trip_{trip_id}",
            trip_id=trip_id,
            user_id=sender_id,
            user_name=sender_name,
            content=text,
            message_type=message_type,
            thread_id=room_id,
        )

        await self._create_document(message_doc)
        logger.info(f"Sent trip message: {message_doc.id} for trip: {trip_id}")
        return message_doc

    # Reservation Management
    async def create_reservation(self, reservation_data: Dict[str, Any]) -> ReservationDocument:
        """Create a new reservation."""
        reservation_doc = ReservationDocument(
            pk=f"trip_{reservation_data['trip_id']}", **reservation_data
        )

        await self._create_document(reservation_doc)
        logger.info(
            f"Created reservation: {reservation_doc.id} for trip: {reservation_data['trip_id']}"
        )
        return reservation_doc

    async def get_trip_reservations(
        self, trip_id: str, status: Optional[str] = None
    ) -> List[ReservationDocument]:
        """Get all reservations for a trip."""
        query = "SELECT * FROM c WHERE c.pk = @pk AND c.entity_type = 'reservation'"
        parameters = [{"name": "@pk", "value": f"trip_{trip_id}"}]

        if status:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status})

        results = await self._query_documents(query, parameters)
        return [ReservationDocument(**doc) for doc in results]

    async def update_reservation(
        self, reservation_id: str, updates: Dict[str, Any]
    ) -> Optional[ReservationDocument]:
        """Update an existing reservation."""
        doc = await self._get_document_by_id(reservation_id)
        if not doc or doc.get("entity_type") != "reservation":
            return None

        updates["updated_at"] = datetime.utcnow()
        updates["version"] = doc.get("version", 1) + 1

        updated_doc = await self._update_document(reservation_id, updates)
        return ReservationDocument(**updated_doc) if updated_doc else None

    async def delete_reservation(self, reservation_id: str) -> bool:
        """Delete a reservation."""
        return await self._delete_document(reservation_id)

    # Feedback Management
    async def create_feedback(self, feedback_data: Dict[str, Any]) -> FeedbackDocument:
        """Create new feedback."""
        feedback_doc = FeedbackDocument(pk=f"trip_{feedback_data['trip_id']}", **feedback_data)

        await self._create_document(feedback_doc)
        logger.info(f"Created feedback: {feedback_doc.id} for trip: {feedback_data['trip_id']}")
        return feedback_doc

    async def get_trip_feedback(
        self, trip_id: str, status: Optional[str] = None
    ) -> List[FeedbackDocument]:
        """Get all feedback for a trip."""
        query = "SELECT * FROM c WHERE c.pk = @pk AND c.entity_type = 'feedback'"
        parameters = [{"name": "@pk", "value": f"trip_{trip_id}"}]

        if status:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status})

        results = await self._query_documents(query, parameters)
        return [FeedbackDocument(**doc) for doc in results]

    async def update_feedback(
        self, feedback_id: str, updates: Dict[str, Any]
    ) -> Optional[FeedbackDocument]:
        """Update existing feedback."""
        doc = await self._get_document_by_id(feedback_id)
        if not doc or doc.get("entity_type") != "feedback":
            return None

        updates["updated_at"] = datetime.utcnow()
        updates["version"] = doc.get("version", 1) + 1

        updated_doc = await self._update_document(feedback_id, updates)
        return FeedbackDocument(**updated_doc) if updated_doc else None

    # Export Management
    async def create_export_task(self, export_data: Dict[str, Any]) -> ExportDocument:
        """Create a new export task."""
        export_doc = ExportDocument(pk=f"user_{export_data['user_id']}", **export_data)

        await self._create_document(export_doc)
        logger.info(f"Created export task: {export_doc.id} for user: {export_data['user_id']}")
        return export_doc

    async def get_user_exports(
        self, user_id: str, status: Optional[str] = None
    ) -> List[ExportDocument]:
        """Get all exports for a user."""
        query = "SELECT * FROM c WHERE c.pk = @pk AND c.entity_type = 'export'"
        parameters = [{"name": "@pk", "value": f"user_{user_id}"}]

        if status:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status})

        results = await self._query_documents(query, parameters)
        return [ExportDocument(**doc) for doc in results]

    async def update_export_task(
        self, export_id: str, updates: Dict[str, Any]
    ) -> Optional[ExportDocument]:
        """Update an export task."""
        doc = await self._get_document_by_id(export_id)
        if not doc or doc.get("entity_type") != "export":
            return None

        updates["updated_at"] = datetime.utcnow()
        updates["version"] = doc.get("version", 1) + 1

        updated_doc = await self._update_document(export_id, updates)
        return ExportDocument(**updated_doc) if updated_doc else None

    # Itinerary Management
    async def create_itinerary(self, itinerary_data: Dict[str, Any]) -> ItineraryDocument:
        """Create a new itinerary."""
        itinerary_doc = ItineraryDocument(pk=f"trip_{itinerary_data['trip_id']}", **itinerary_data)

        await self._create_document(itinerary_doc)
        logger.info(f"Created itinerary: {itinerary_doc.id} for trip: {itinerary_data['trip_id']}")
        return itinerary_doc

    async def get_trip_itineraries(
        self, trip_id: str, active_only: bool = True
    ) -> List[ItineraryDocument]:
        """Get all itineraries for a trip."""
        query = "SELECT * FROM c WHERE c.pk = @pk AND c.entity_type = 'itinerary'"
        parameters = [{"name": "@pk", "value": f"trip_{trip_id}"}]

        if active_only:
            query += " AND c.is_active = true"

        results = await self._query_documents(query, parameters)
        return [ItineraryDocument(**doc) for doc in results]

    async def get_active_itinerary(self, trip_id: str) -> Optional[ItineraryDocument]:
        """Get the active itinerary for a trip."""
        itineraries = await self.get_trip_itineraries(trip_id, active_only=True)
        return itineraries[0] if itineraries else None

    async def update_itinerary(
        self, itinerary_id: str, updates: Dict[str, Any]
    ) -> Optional[ItineraryDocument]:
        """Update an existing itinerary."""
        doc = await self._get_document_by_id(itinerary_id)
        if not doc or doc.get("entity_type") != "itinerary":
            return None

        updates["updated_at"] = datetime.utcnow()
        updates["version"] = doc.get("version", 1) + 1

        updated_doc = await self._update_document(itinerary_id, updates)
        return ItineraryDocument(**updated_doc) if updated_doc else None

    async def deactivate_trip_itineraries(self, trip_id: str) -> int:
        """Deactivate all itineraries for a trip (when generating a new one)."""
        itineraries = await self.get_trip_itineraries(trip_id, active_only=True)
        updated_count = 0

        for itinerary in itineraries:
            await self.update_itinerary(itinerary.id, {"is_active": False})
            updated_count += 1

        return updated_count

    # Private helper methods

    async def _create_document(self, document: CosmosDocument) -> CosmosDocument:
        """Create a document in Cosmos DB."""
        doc_dict = document.model_dump()

        if not self.container:
            # Simulation mode
            pk = doc_dict["pk"]
            if pk not in self._simulation_data:
                self._simulation_data[pk] = {}
            self._simulation_data[pk][doc_dict["id"]] = doc_dict
            return document

        try:
            result = self.container.create_item(body=doc_dict)
            return type(document)(**result)
        except exceptions.CosmosResourceExistsError:
            raise ValueError(f"Document with ID {document.id} already exists")
        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}")
            raise

    async def _get_document(
        self, partition_key: str, item_id: str, model_class
    ) -> Optional[CosmosDocument]:
        """Get a document by partition key and ID."""
        if not self.container:
            # Simulation mode
            if partition_key in self._simulation_data:
                doc = self._simulation_data[partition_key].get(item_id)
                if doc:
                    return model_class(**doc)
            return None

        try:
            result = self.container.read_item(item=item_id, partition_key=partition_key)
            return model_class(**result)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            raise

    async def _update_document(self, document: CosmosDocument) -> CosmosDocument:
        """Update a document in Cosmos DB."""
        doc_dict = document.model_dump()

        if not self.container:
            # Simulation mode
            pk = doc_dict["pk"]
            if pk in self._simulation_data:
                self._simulation_data[pk][doc_dict["id"]] = doc_dict
            return document

        try:
            result = self.container.replace_item(item=doc_dict["id"], body=doc_dict)
            return type(document)(**result)
        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}")
            raise

    async def _query_documents(
        self, query: str, parameters: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query against Cosmos DB."""
        if not self.container:
            # Simulation mode - basic query simulation
            results = []
            for pk_data in self._simulation_data.values():
                for doc in pk_data.values():
                    # Basic filtering - in real implementation, this would be more sophisticated
                    if (
                        "entity_type" in query
                        and "'user'" in query
                        and doc.get("entity_type") == "user"
                    ):
                        results.append(doc)
                    elif (
                        "entity_type" in query
                        and "'family'" in query
                        and doc.get("entity_type") == "family"
                    ):
                        results.append(doc)
                    elif (
                        "entity_type" in query
                        and "'trip'" in query
                        and doc.get("entity_type") == "trip"
                    ):
                        results.append(doc)
                    elif (
                        "entity_type" in query
                        and "'message'" in query
                        and doc.get("entity_type") == "message"
                    ):
                        results.append(doc)
            return results

        try:
            query_spec = {"query": query, "parameters": parameters or []}
            results = list(
                self.container.query_items(query=query_spec, enable_cross_partition_query=True)
            )
            return results
        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            raise


# Global repository instance
unified_cosmos_repo = UnifiedCosmosRepository()
