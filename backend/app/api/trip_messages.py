"""
Trip messages API endpoints.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import get_current_active_user
from app.core.zero_trust import require_permissions
from app.models.user import User
from app.models.cosmos.message import MessageType
from app.services.trip_cosmos import TripCosmosOperations

settings = get_settings()
router = APIRouter()

# Create an instance of the Cosmos operations service
cosmos_service = TripCosmosOperations()


@router.get("/{trip_id}/messages")
async def get_trip_messages(
    trip_id: UUID,
    room_id: Optional[str] = None,
    limit: int = Query(50, gt=0, le=100),
    current_user: User = Depends(require_permissions("trips", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for a trip from Cosmos DB.
    
    Parameters:
    - trip_id: The trip ID
    - room_id: Optional room ID to filter messages by
    - limit: Maximum number of messages to return (default: 50, max: 100)
    """
    try:
        messages = await cosmos_service.get_trip_messages(
            trip_id=str(trip_id),
            room_id=room_id,
            limit=limit
        )
        
        # Convert Cosmos DB documents to dictionary responses
        return [message.dict(exclude={"_resource_id", "_etag", "_ts"}) for message in messages]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )


@router.post("/{trip_id}/messages")
async def send_trip_message(
    trip_id: UUID,
    message: Dict[str, Any],
    room_id: Optional[str] = None,
    current_user: User = Depends(require_permissions("trips", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a new message in the trip chat.
    
    Parameters:
    - trip_id: The trip ID
    - message: Message content (text required)
    - room_id: Optional room ID for focused discussions
    """
    if "text" not in message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must contain 'text'"
        )
    
    message_type = MessageType(message.get("type", "chat"))
    
    try:
        result = await cosmos_service.send_trip_message(
            trip_id=str(trip_id),
            sender_id=str(current_user.id),
            sender_name=current_user.name or current_user.email,
            text=message["text"],
            message_type=message_type,
            room_id=room_id
        )
        
        if result:
            return result.dict(exclude={"_resource_id", "_etag", "_ts"})
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )
