"""
Trip messages API endpoints - Unified Cosmos DB Implementation.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from app.core.config import get_settings
from app.core.database_unified import get_cosmos_repository
from app.core.zero_trust import require_permissions
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.models.cosmos.message import MessageType
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, Query, status

settings = get_settings()
router = APIRouter()


@router.get("/{trip_id}/messages")
async def get_trip_messages(
    trip_id: UUID,
    room_id: Optional[str] = None,
    limit: int = Query(50, gt=0, le=100),
    current_user: User = Depends(require_permissions("trips", "read")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """
    Get messages for a trip from unified Cosmos DB.

    Parameters:
    - trip_id: The trip ID
    - room_id: Optional room ID to filter messages by
    - limit: Maximum number of messages to return (default: 50, max: 100)
    """
    try:
        # Get trip to verify access
        trip = await cosmos_repo.get_trip(str(trip_id))
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        # Get messages using unified repository
        messages = await cosmos_repo.get_trip_messages(
            trip_id=str(trip_id), room_id=room_id, limit=limit
        )

        # Convert to dictionary responses
        return [message.dict() for message in messages]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}",
        )


@router.post("/{trip_id}/messages")
async def send_trip_message(
    trip_id: UUID,
    message: Dict[str, Any],
    room_id: Optional[str] = None,
    current_user: User = Depends(require_permissions("trips", "write")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """
    Send a new message in the trip chat using unified Cosmos DB.

    Parameters:
    - trip_id: The trip ID
    - message: Message content (text required)
    - room_id: Optional room ID for focused discussions
    """
    if "text" not in message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must contain 'text'",
        )

    message_type = MessageType(message.get("type", "chat"))

    try:
        # Get trip to verify access
        trip = await cosmos_repo.get_trip(str(trip_id))
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        # Send message using unified repository
        result = await cosmos_repo.send_trip_message(
            trip_id=str(trip_id),
            sender_id=str(current_user.id),
            sender_name=current_user.name or current_user.email,
            text=message["text"],
            message_type=message_type,
            room_id=room_id,
        )

        if result:
            return result.dict()
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )
