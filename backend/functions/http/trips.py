"""
Trips HTTP Functions

CRUD operations for trip management.
"""

import logging

import azure.functions as func

from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request
from models.schemas import (
    TripCreate,
    TripResponse,
    TripUpdate,
    UserResponse,
)
from services.trip_service import get_trip_service

bp = func.Blueprint()
logger = logging.getLogger(__name__)


async def require_auth(req: func.HttpRequest):
    """Helper to require authentication and return user."""
    user = await get_user_from_request(req)
    if not user:
        raise APIError(code=ErrorCode.AUTHENTICATION_ERROR, message="Authentication required")
    return user


@bp.route(route="trips", methods=["GET"])
async def list_trips(req: func.HttpRequest) -> func.HttpResponse:
    """
    List trips for the current user.

    Query params:
    - family_id: Filter by family
    - status: Filter by status (planning, active, completed, cancelled)
    - limit: Max results (default 50)
    - offset: Pagination offset
    """
    try:
        user = await require_auth(req)

        family_id = req.params.get("family_id")
        status = req.params.get("status")
        limit = int(req.params.get("limit", "50"))
        offset = int(req.params.get("offset", "0"))

        service = get_trip_service()

        if family_id:
            trips = await service.get_family_trips(family_id)
        else:
            trips = await service.get_user_trips(user.id)

        # Apply filters
        if status:
            trips = [t for t in trips if t.status == status]

        # Paginate
        total = len(trips)
        trips = trips[offset : offset + limit]

        # Convert to response
        trip_responses = [TripResponse.from_document(t) for t in trips]

        return success_response(
            {"items": [t.model_dump() for t in trip_responses], "total": total, "limit": limit, "offset": offset}
        )

    except APIError as e:
        return error_response(e, status_code=401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400)
    except Exception:
        logger.exception("Error listing trips")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to list trips"), status_code=500)


@bp.route(route="trips", methods=["POST"])
async def create_trip(req: func.HttpRequest) -> func.HttpResponse:
    """
    Create a new trip.

    Body: TripCreate
    Returns: Created trip
    """
    try:
        user = await require_auth(req)

        body = req.get_json()
        trip_data = TripCreate(**body)

        service = get_trip_service()
        trip = await service.create_trip(data=trip_data, user=user)

        trip_response = TripResponse.from_document(trip)
        return success_response(trip_response.model_dump(), status_code=201)

    except APIError as e:
        return error_response(e, status_code=401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400)
    except Exception:
        logger.exception("Error creating trip")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to create trip"), status_code=500)


@bp.route(route="trips/{trip_id}", methods=["GET"])
async def get_trip(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get a specific trip by ID.
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        service = get_trip_service()
        trip = await service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        # Check access — user_has_access is sync: (trip, user_id)
        if not service.user_has_access(trip, user.id):
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        trip_response = TripResponse.from_document(trip)
        return success_response(trip_response.model_dump())

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting trip")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get trip"), status_code=500)


@bp.route(route="trips/{trip_id}", methods=["PUT", "PATCH"])
async def update_trip(req: func.HttpRequest) -> func.HttpResponse:
    """
    Update a trip.

    Body: TripUpdate (partial update supported)
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        body = req.get_json()
        update_data = TripUpdate(**body)

        service = get_trip_service()
        updated_trip = await service.update_trip(trip_id=trip_id, data=update_data, user=user)

        if not updated_trip:
            return error_response(
                APIError(code=ErrorCode.NOT_FOUND, message="Trip not found or access denied"), status_code=404
            )

        trip_response = TripResponse.from_document(updated_trip)
        return success_response(trip_response.model_dump())

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error updating trip")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to update trip"), status_code=500)


@bp.route(route="trips/{trip_id}", methods=["DELETE"])
async def delete_trip(req: func.HttpRequest) -> func.HttpResponse:
    """
    Delete a trip.

    Only the organizer can delete a trip.
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        service = get_trip_service()
        success = await service.delete_trip(trip_id=trip_id, user=user)

        if not success:
            return error_response(
                APIError(code=ErrorCode.NOT_FOUND, message="Trip not found or access denied"), status_code=404
            )

        return success_response({"message": "Trip deleted successfully"})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error deleting trip")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to delete trip"), status_code=500)


@bp.route(route="trips/{trip_id}/members", methods=["GET"])
async def get_trip_members(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get all members participating in a trip.

    Returns users from all families associated with the trip.
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        service = get_trip_service()
        trip = await service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        # Check access — user_has_access is sync: (trip, user_id)
        if not service.user_has_access(trip, user.id):
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Get members from all participating families
        from services.family_service import get_family_service

        family_service = get_family_service()

        all_members = []
        for family_id in trip.participating_family_ids:
            members = await family_service.get_family_members(family_id)
            all_members.extend(members)

        # Deduplicate by user ID
        seen_ids = set()
        unique_members = []
        for member in all_members:
            if member.id not in seen_ids:
                seen_ids.add(member.id)
                unique_members.append(member)

        member_responses = [UserResponse.from_document(m) for m in unique_members]

        return success_response({"items": [m.model_dump() for m in member_responses], "total": len(unique_members)})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting trip members")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get trip members"), status_code=500
        )
