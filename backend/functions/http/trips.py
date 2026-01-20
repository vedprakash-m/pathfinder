"""
Trips HTTP Functions

CRUD operations for trip management.
"""
import logging
from datetime import UTC, datetime

import azure.functions as func

from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request
from models.schemas import (
    TripCreateRequest,
    TripResponse,
    TripUpdateRequest,
)
from services.trip_service import get_trip_service

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

    Body: TripCreateRequest
    Returns: Created trip
    """
    try:
        user = await require_auth(req)

        body = req.get_json()
        trip_data = TripCreateRequest(**body)

        service = get_trip_service()
        trip = await service.create_trip(
            title=trip_data.title,
            description=trip_data.description,
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            organizer_id=user.id,
            family_ids=trip_data.family_ids,
            budget=trip_data.budget,
            currency=trip_data.currency,
        )

        # Send notifications to family members
        # (In production, this would be done via queue for better reliability)

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

        # Check access
        has_access = await service.user_has_access(user.id, trip)
        if not has_access:
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

    Body: TripUpdateRequest (partial update supported)
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        body = req.get_json()
        update_data = TripUpdateRequest(**body)

        service = get_trip_service()

        # Get existing trip
        trip = await service.get_trip(trip_id)
        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        # Check access (only organizer can update)
        if trip.organizer_user_id != user.id:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Only the organizer can update the trip"),
                status_code=403,
            )

        # Apply updates
        update_fields = update_data.model_dump(exclude_unset=True)
        updated_trip = await service.update_trip(trip_id, **update_fields)

        if not updated_trip:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to update trip"), status_code=500
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

        # Get existing trip
        trip = await service.get_trip(trip_id)
        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        # Check access (only organizer can delete)
        if trip.organizer_user_id != user.id:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Only the organizer can delete the trip"),
                status_code=403,
            )

        success = await service.delete_trip(trip_id)

        if not success:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to delete trip"), status_code=500
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

        # Check access
        has_access = await service.user_has_access(user.id, trip)
        if not has_access:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Get members from all participating families
        from services.family_service import get_family_service

        family_service = get_family_service()

        all_members = []
        for family_id in trip.family_ids:
            members = await family_service.get_family_members(family_id)
            all_members.extend(members)

        # Deduplicate by user ID
        seen_ids = set()
        unique_members = []
        for member in all_members:
            if member.id not in seen_ids:
                seen_ids.add(member.id)
                unique_members.append(member)

        from models.schemas import UserResponse

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
