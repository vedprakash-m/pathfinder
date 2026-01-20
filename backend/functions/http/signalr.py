"""
SignalR HTTP Functions

Handles SignalR Service negotiation and messaging.
"""
import json
import logging
from datetime import UTC, datetime

import azure.functions as func

from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request
from services.realtime_service import get_realtime_service

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


async def require_auth(req: func.HttpRequest):
    """Helper to require authentication and return user."""
    user = await get_user_from_request(req)
    if not user:
        raise APIError(code=ErrorCode.AUTHENTICATION_ERROR, message="Authentication required")
    return user


@bp.route(route="signalr/negotiate", methods=["POST"])
async def negotiate(req: func.HttpRequest) -> func.HttpResponse:
    """
    Negotiate SignalR connection.

    Returns connection info for the client to establish WebSocket.
    """
    try:
        user = await require_auth(req)

        service = get_realtime_service()
        connection_info = service.get_client_negotiate_response(user.id)

        return func.HttpResponse(body=json.dumps(connection_info), status_code=200, mimetype="application/json")

    except APIError as e:
        return error_response(e, status_code=401)
    except ValueError as e:
        logger.error(f"SignalR configuration error: {e}")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="SignalR not configured"), status_code=500
        )
    except Exception:
        logger.exception("Error negotiating SignalR connection")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to negotiate connection"), status_code=500
        )


@bp.route(route="signalr/groups/{group_name}/join", methods=["POST"])
async def join_group(req: func.HttpRequest) -> func.HttpResponse:
    """
    Join a SignalR group.

    Groups are typically trip IDs or family IDs for scoped messaging.
    """
    try:
        user = await require_auth(req)
        group_name = req.route_params.get("group_name")

        if not group_name:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Group name is required"), status_code=400
            )

        service = get_realtime_service()
        success = await service.add_user_to_group(user.id, group_name)

        if success:
            return success_response({"message": f"Joined group {group_name}"})
        else:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to join group"), status_code=500
            )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error joining group")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to join group"), status_code=500)


@bp.route(route="signalr/groups/{group_name}/leave", methods=["POST"])
async def leave_group(req: func.HttpRequest) -> func.HttpResponse:
    """
    Leave a SignalR group.
    """
    try:
        user = await require_auth(req)
        group_name = req.route_params.get("group_name")

        if not group_name:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Group name is required"), status_code=400
            )

        service = get_realtime_service()
        success = await service.remove_user_from_group(user.id, group_name)

        if success:
            return success_response({"message": f"Left group {group_name}"})
        else:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to leave group"), status_code=500
            )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error leaving group")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to leave group"), status_code=500)


@bp.route(route="signalr/send", methods=["POST"])
async def send_message_to_group(req: func.HttpRequest) -> func.HttpResponse:
    """
    Send a message to a group.

    Body: {
        "group": "group_name",
        "target": "eventName",
        "data": {...}
    }
    """
    try:
        user = await require_auth(req)

        body = req.get_json()
        group = body.get("group")
        target = body.get("target")
        data = body.get("data")

        if not group or not target:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Group and target are required"), status_code=400
            )

        # Add sender info to data
        if isinstance(data, dict):
            data["sender_id"] = user.id
            data["timestamp"] = utc_now().isoformat()

        service = get_realtime_service()
        success = await service.send_to_group(group, target, data)

        if success:
            return success_response({"message": "Message sent"})
        else:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to send message"), status_code=500
            )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error sending message")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to send message"), status_code=500
        )
