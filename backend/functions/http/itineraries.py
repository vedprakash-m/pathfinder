"""
Itineraries HTTP Functions

AI-powered itinerary generation and management.
"""
import json
import logging
from datetime import UTC, datetime

import azure.functions as func

from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request
from models.schemas import (
    ItineraryGenerateRequest,
    ItineraryResponse,
)
from services.itinerary_service import get_itinerary_service
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


@bp.route(route="trips/{trip_id}/itinerary", methods=["GET"])
async def get_itinerary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get the current itinerary for a trip.
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

        has_access = await trip_service.user_has_access(user.id, trip)
        if not has_access:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Get itinerary
        itinerary_service = get_itinerary_service()
        itinerary = await itinerary_service.get_itinerary(trip_id)

        if not itinerary:
            return success_response({"exists": False, "message": "No itinerary generated yet"})

        itinerary_response = ItineraryResponse.from_document(itinerary)
        return success_response({"exists": True, "itinerary": itinerary_response.model_dump()})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting itinerary")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get itinerary"), status_code=500
        )


@bp.route(route="trips/{trip_id}/itinerary/generate", methods=["POST"])
async def generate_itinerary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Generate a new AI-powered itinerary for a trip.

    Body: ItineraryGenerateRequest (optional preferences)
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        # Parse optional preferences
        preferences = {}
        try:
            body = req.get_json()
            if body:
                gen_request = ItineraryGenerateRequest(**body)
                preferences = gen_request.model_dump(exclude_unset=True)
        except (ValueError, json.JSONDecodeError):
            pass  # No preferences provided

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        has_access = await trip_service.user_has_access(user.id, trip)
        if not has_access:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Generate itinerary
        itinerary_service = get_itinerary_service()
        itinerary = await itinerary_service.generate_itinerary(
            trip=trip, preferences=preferences if preferences else None
        )

        if not itinerary:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to generate itinerary"), status_code=500
            )

        itinerary_response = ItineraryResponse.from_document(itinerary)
        return success_response(
            {"message": "Itinerary generated successfully", "itinerary": itinerary_response.model_dump()},
            status_code=201,
        )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error generating itinerary")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to generate itinerary"), status_code=500
        )


@bp.route(route="trips/{trip_id}/itinerary/approve", methods=["POST"])
async def approve_itinerary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Approve the current itinerary.

    Only the trip organizer can approve.
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        # Verify trip access and organizer role
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        if trip.organizer_user_id != user.id:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Only the organizer can approve the itinerary"),
                status_code=403,
            )

        # Approve itinerary
        itinerary_service = get_itinerary_service()
        itinerary = await itinerary_service.approve_itinerary(trip_id, user.id)

        if not itinerary:
            return error_response(
                APIError(code=ErrorCode.NOT_FOUND, message="No itinerary found to approve"), status_code=404
            )

        itinerary_response = ItineraryResponse.from_document(itinerary)
        return success_response({"message": "Itinerary approved", "itinerary": itinerary_response.model_dump()})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error approving itinerary")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to approve itinerary"), status_code=500
        )


@bp.route(route="trips/{trip_id}/itinerary", methods=["PUT", "PATCH"])
async def update_itinerary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Update the itinerary with manual changes.

    Body: Partial itinerary update
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        body = req.get_json()

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        # Only organizer can edit
        if trip.organizer_user_id != user.id:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Only the organizer can edit the itinerary"),
                status_code=403,
            )

        # Update itinerary
        itinerary_service = get_itinerary_service()
        itinerary = await itinerary_service.update_itinerary(trip_id, body)

        if not itinerary:
            return error_response(
                APIError(code=ErrorCode.NOT_FOUND, message="No itinerary found to update"), status_code=404
            )

        itinerary_response = ItineraryResponse.from_document(itinerary)
        return success_response({"message": "Itinerary updated", "itinerary": itinerary_response.model_dump()})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error updating itinerary")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to update itinerary"), status_code=500
        )


@bp.route(route="trips/{trip_id}/itinerary/regenerate", methods=["POST"])
async def regenerate_itinerary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Regenerate the itinerary with new preferences or feedback.

    Body: ItineraryGenerateRequest with feedback
    """
    try:
        user = await require_auth(req)
        trip_id = req.route_params.get("trip_id")

        if not trip_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Trip ID is required"), status_code=400
            )

        # Parse preferences and feedback
        body = req.get_json()
        feedback = body.get("feedback", "")
        preferences = body.get("preferences", {})

        # Verify trip access
        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Trip not found"), status_code=404)

        has_access = await trip_service.user_has_access(user.id, trip)
        if not has_access:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        # Add feedback to preferences
        if feedback:
            preferences["feedback"] = feedback

        # Regenerate itinerary
        itinerary_service = get_itinerary_service()
        itinerary = await itinerary_service.generate_itinerary(
            trip=trip, preferences=preferences if preferences else None
        )

        if not itinerary:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to regenerate itinerary"), status_code=500
            )

        itinerary_response = ItineraryResponse.from_document(itinerary)
        return success_response(
            {"message": "Itinerary regenerated successfully", "itinerary": itinerary_response.model_dump()}
        )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error regenerating itinerary")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to regenerate itinerary"), status_code=500
        )
