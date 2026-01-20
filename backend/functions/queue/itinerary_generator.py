"""
Itinerary Generator Queue Function

Processes async itinerary generation requests from the queue.
"""
import json
import logging
from datetime import UTC, datetime

import azure.functions as func

from services.itinerary_service import get_itinerary_service
from services.notification_service import NotificationType, get_notification_service
from services.realtime_service import RealtimeEvents, get_realtime_service

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


@bp.queue_trigger(arg_name="msg", queue_name="itinerary-requests", connection="AZURE_STORAGE_CONNECTION_STRING")
async def process_itinerary_request(msg: func.QueueMessage) -> None:
    """
    Process an itinerary generation request from the queue.

    Message format:
    {
        "trip_id": "uuid",
        "preferences": {...},
        "requested_by": "user_id"
    }
    """
    try:
        # Parse message
        message_body = msg.get_body().decode("utf-8")
        request = json.loads(message_body)

        trip_id = request.get("trip_id")
        preferences = request.get("preferences", {})
        requested_by = request.get("requested_by")

        if not trip_id:
            logger.error("Invalid message: missing trip_id")
            return

        logger.info(f"Processing itinerary request for trip {trip_id}")

        # Get trip
        from services.trip_service import get_trip_service

        trip_service = get_trip_service()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            logger.error(f"Trip not found: {trip_id}")
            return

        # Generate itinerary
        itinerary_service = get_itinerary_service()
        itinerary = await itinerary_service.generate_itinerary(
            trip=trip, preferences=preferences if preferences else None
        )

        if itinerary:
            logger.info(f"Successfully generated itinerary for trip {trip_id}")

            # Send real-time notification
            realtime_service = get_realtime_service()
            await realtime_service.send_to_group(
                group_name=trip_id,
                target=RealtimeEvents.ITINERARY_GENERATED,
                data={"trip_id": trip_id, "itinerary_id": itinerary.id, "status": "ready"},
            )

            # Create notifications for trip participants
            notification_service = get_notification_service()

            # Get all participants
            from services.family_service import get_family_service

            family_service = get_family_service()

            member_ids = set()
            for family_id in trip.family_ids:
                members = await family_service.get_family_members(family_id)
                for member in members:
                    member_ids.add(member.id)

            # Send notifications (excluding requester)
            for member_id in member_ids:
                if member_id != requested_by:
                    await notification_service.create_notification(
                        user_id=member_id,
                        notification_type=NotificationType.ITINERARY_READY,
                        title="Itinerary Ready!",
                        body=f"The itinerary for {trip.title} is ready for review.",
                        trip_id=trip_id,
                        action_url=f"/trips/{trip_id}/itinerary",
                    )
        else:
            logger.error(f"Failed to generate itinerary for trip {trip_id}")

            # Notify requester of failure
            if requested_by:
                notification_service = get_notification_service()
                await notification_service.create_notification(
                    user_id=requested_by,
                    notification_type=NotificationType.ITINERARY_READY,
                    title="Itinerary Generation Failed",
                    body=f"We couldn't generate the itinerary for {trip.title}. Please try again.",
                    trip_id=trip_id,
                )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in queue message: {e}")
    except Exception as e:
        logger.exception(f"Error processing itinerary request: {e}")
        raise  # Re-raise to trigger retry
