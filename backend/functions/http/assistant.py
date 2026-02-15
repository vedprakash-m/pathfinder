"""
AI Assistant HTTP Functions

Conversational AI assistant for trip planning help.
"""

import logging

import azure.functions as func

from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request
from models.schemas import (
    AssistantRequest,
    MessageResponse,
)
from services.assistant_service import get_assistant_service

bp = func.Blueprint()
logger = logging.getLogger(__name__)


async def require_auth(req: func.HttpRequest):
    """Helper to require authentication and return user."""
    user = await get_user_from_request(req)
    if not user:
        raise APIError(code=ErrorCode.AUTHENTICATION_ERROR, message="Authentication required")
    return user


@bp.route(route="assistant/message", methods=["POST"])
async def send_message(req: func.HttpRequest) -> func.HttpResponse:
    """
    Send a message to the AI assistant.

    Body: AssistantMessageRequest
    """
    try:
        user = await require_auth(req)

        body = req.get_json()
        message_data = AssistantRequest(**body)

        service = get_assistant_service()
        response = await service.send_message(
            user_id=user.id,
            message=message_data.message,
            trip_id=message_data.trip_id,
            family_id=message_data.family_id,
        )

        message_response = MessageResponse.from_document(response)
        return success_response(message_response.model_dump())

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error sending message to assistant")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to process message"), status_code=500
        )


@bp.route(route="assistant/conversation", methods=["GET"])
async def get_conversation(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get conversation history with the assistant.

    Query params:
    - trip_id: Optional filter by trip
    - limit: Max messages (default 50)
    - offset: Pagination offset
    """
    try:
        user = await require_auth(req)

        trip_id = req.params.get("trip_id")
        limit = int(req.params.get("limit", "50"))
        offset = int(req.params.get("offset", "0"))

        service = get_assistant_service()
        messages = await service.get_conversation(user_id=user.id, trip_id=trip_id, limit=limit, offset=offset)

        message_responses = [MessageResponse.from_document(m) for m in messages]

        return success_response(
            {
                "items": [m.model_dump() for m in message_responses],
                "total": len(messages),
                "limit": limit,
                "offset": offset,
            }
        )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting conversation")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get conversation"), status_code=500
        )


@bp.route(route="assistant/conversation", methods=["DELETE"])
async def clear_conversation(req: func.HttpRequest) -> func.HttpResponse:
    """
    Clear conversation history with the assistant.

    Query params:
    - trip_id: Optional filter by trip (if not provided, clears all)
    """
    try:
        user = await require_auth(req)

        trip_id = req.params.get("trip_id")

        service = get_assistant_service()
        deleted_count = await service.clear_conversation(user_id=user.id, trip_id=trip_id)

        return success_response({"message": f"Cleared {deleted_count} messages", "deleted_count": deleted_count})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error clearing conversation")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to clear conversation"), status_code=500
        )


@bp.route(route="trips/{trip_id}/assistant/suggest", methods=["POST"])
async def get_suggestions(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get AI suggestions for a specific trip context.

    Body: {
        "type": "activity" | "destination" | "dining" | "general",
        "context": "optional additional context"
    }
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        body = req.get_json()
        suggestion_type = body.get("type", "general")
        context = body.get("context", "")

        # Build suggestion prompt based on type
        prompts = {
            "activity": f"Suggest 3 fun activities for our trip. {context}",
            "destination": f"Recommend 3 nearby destinations to explore. {context}",
            "dining": f"Suggest 3 restaurants or dining experiences. {context}",
            "general": f"Give me 3 helpful tips for our trip. {context}",
        }

        message = prompts.get(suggestion_type, prompts["general"])

        service = get_assistant_service()
        response = await service.send_message(user_id=user.id, message=message, trip_id=trip_id)

        return success_response({"type": suggestion_type, "suggestions": response.content})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting suggestions")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get suggestions"), status_code=500
        )
