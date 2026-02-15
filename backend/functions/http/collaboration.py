"""
Collaboration HTTP Functions

Polls, voting, and consensus features for trip planning.
"""

import logging

import azure.functions as func

from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request
from models.schemas import (
    PollCreate,
    PollResponse,
    PollVote,
)
from services.collaboration_service import get_collaboration_service
from services.trip_service import get_trip_service

bp = func.Blueprint()
logger = logging.getLogger(__name__)


async def require_auth(req: func.HttpRequest):
    """Helper to require authentication and return user."""
    user = await get_user_from_request(req)
    if not user:
        raise APIError(code=ErrorCode.AUTHENTICATION_ERROR, message="Authentication required")
    return user


@bp.route(route="trips/{trip_id}/polls", methods=["GET"])
async def list_polls(req: func.HttpRequest) -> func.HttpResponse:
    """
    List all polls for a trip.

    Query params:
    - status: Filter by status (active, closed)
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        # user_has_access is sync: (trip, user_id)
        if not trip_service.user_has_access(trip, user.id):
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Get polls
        status_filter = req.params.get("status")
        collab_service = get_collaboration_service()
        polls = await collab_service.get_trip_polls(trip_id)

        # Filter by status if requested
        if status_filter:
            polls = [p for p in polls if p.status == status_filter]

        poll_responses = [PollResponse.from_document(p, user.id) for p in polls]

        return success_response({"items": [p.model_dump() for p in poll_responses], "total": len(polls)})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error listing polls")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to list polls"), status_code=500)


@bp.route(route="trips/{trip_id}/polls", methods=["POST"])
async def create_poll(req: func.HttpRequest) -> func.HttpResponse:
    """
    Create a new poll for a trip.

    Body: PollCreate
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        body = req.get_json()
        poll_data = PollCreate(**body)
        # Ensure the trip_id in the body matches the route
        poll_data.trip_id = trip_id

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        if not trip_service.user_has_access(trip, user.id):
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Create poll — service expects (data: PollCreate, user: UserDocument)
        collab_service = get_collaboration_service()
        poll = await collab_service.create_poll(data=poll_data, user=user)

        poll_response = PollResponse.from_document(poll, user.id)
        return success_response(poll_response.model_dump(), status_code=201)

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error creating poll")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to create poll"), status_code=500)


@bp.route(route="trips/{trip_id}/polls/{poll_id}", methods=["GET"])
async def get_poll(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get a specific poll.
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")
        poll_id = req.route_params.get("poll_id")

        if not trip_id or not poll_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID and Poll ID are required"), status_code=400
            )

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        if not trip_service.user_has_access(trip, user.id):
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Get poll
        collab_service = get_collaboration_service()
        poll = await collab_service.get_poll(poll_id)

        if not poll or poll.trip_id != trip_id:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Poll not found"), status_code=404)

        poll_response = PollResponse.from_document(poll, user.id)
        return success_response(poll_response.model_dump())

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting poll")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get poll"), status_code=500)


@bp.route(route="trips/{trip_id}/polls/{poll_id}/vote", methods=["POST"])
async def vote_on_poll(req: func.HttpRequest) -> func.HttpResponse:
    """
    Cast a vote on a poll.

    Body: PollVote
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")
        poll_id = req.route_params.get("poll_id")

        if not trip_id or not poll_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID and Poll ID are required"), status_code=400
            )

        body = req.get_json()
        vote_data = PollVote(**body)

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        if not trip_service.user_has_access(trip, user.id):
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Cast vote — service expects (poll_id, vote: PollVote, user: UserDocument)
        collab_service = get_collaboration_service()
        poll = await collab_service.vote_on_poll(poll_id=poll_id, vote=vote_data, user=user)

        if not poll:
            return error_response(
                APIError(code=ErrorCode.NOT_FOUND, message="Poll not found or closed"), status_code=404
            )

        poll_response = PollResponse.from_document(poll, user.id)
        return success_response({"message": "Vote recorded", "poll": poll_response.model_dump()})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error voting on poll")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to record vote"), status_code=500)


@bp.route(route="trips/{trip_id}/polls/{poll_id}/close", methods=["POST"])
async def close_poll(req: func.HttpRequest) -> func.HttpResponse:
    """
    Close a poll.

    Only the poll creator or trip organizer can close.
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")
        poll_id = req.route_params.get("poll_id")

        if not trip_id or not poll_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID and Poll ID are required"), status_code=400
            )

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        # Get poll to check creator
        collab_service = get_collaboration_service()
        poll = await collab_service.get_poll(poll_id)

        if not poll or poll.trip_id != trip_id:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Poll not found"), status_code=404)

        # Check permissions — PollDocument uses creator_id (not creator_user_id)
        is_creator = poll.creator_id == user.id
        is_organizer = trip.organizer_user_id == user.id

        if not is_creator and not is_organizer:
            return error_response(
                APIError(
                    code=ErrorCode.AUTHORIZATION_ERROR, message="Only the creator or organizer can close this poll"
                ),
                status_code=403,
            )

        # Close poll — service expects (poll_id, user)
        closed_poll = await collab_service.close_poll(poll_id=poll_id, user=user)

        if not closed_poll:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to close poll"), status_code=500
            )

        poll_response = PollResponse.from_document(closed_poll, user.id)
        return success_response({"message": "Poll closed", "poll": poll_response.model_dump()})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error closing poll")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to close poll"), status_code=500)


@bp.route(route="trips/{trip_id}/consensus", methods=["GET"])
async def get_consensus(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get AI-analyzed consensus status for a trip's polls.
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        if not trip_service.user_has_access(trip, user.id):
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Get consensus status
        collab_service = get_collaboration_service()
        consensus = await collab_service.get_consensus_status(trip_id)

        return success_response(consensus)

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting consensus")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get consensus status"), status_code=500
        )
