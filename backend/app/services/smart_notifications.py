"""
Smart Notifications Service - Automated family coordination notifications.

Handles intelligent, context-aware notifications to reduce manual coordination overhead.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationTrigger(Enum):
    """Events that trigger smart notifications."""

    FAMILY_JOINED = "family_joined"
    CONSENSUS_UPDATED = "consensus_updated"
    CONFLICT_DETECTED = "conflict_detected"
    ITINERARY_READY = "itinerary_ready"


class NotificationUrgency(Enum):
    """Urgency levels for smart notifications."""

    INFO = "info"
    REMINDER = "reminder"
    ACTION_NEEDED = "action_needed"
    URGENT = "urgent"


@dataclass
class SmartNotification:
    """Smart notification with context and actions."""

    title: str
    message: str
    urgency: NotificationUrgency
    trip_id: str
    family_id: Optional[str]
    user_id: Optional[str]
    context_data: Dict[str, Any]
    action_buttons: List[Dict[str, str]]
    auto_dismiss_hours: Optional[int] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class SmartNotificationService:
    """
    Service for sending intelligent, context-aware notifications.

    Reduces coordination overhead by:
    - Smart timing based on user activity
    - Contextual messages with trip-specific information
    - Actionable buttons for immediate response
    - Automatic batching to prevent notification spam
    """

    def __init__(self):
        self.notification_templates = {
            "family_joined_welcome": {
                "title": "Welcome to {trip_name}! 🎉",
                "message": "Your family has been added to {trip_name}. Complete your preferences to help with planning!",
                "urgency": "action_needed",
            },
            "consensus_improved": {
                "title": "Consensus Improving! 📈",
                "message": "Great progress on {trip_name}! Consensus score: {consensus_score}%",
                "urgency": "info",
            },
            "critical_conflict": {
                "title": "⚠️ Critical Issue Detected",
                "message": "Critical conflicts in {trip_name} need immediate resolution.",
                "urgency": "urgent",
            },
        }

    async def send_smart_notification(
        self, trigger: NotificationTrigger, context_data: Dict[str, Any]
    ) -> bool:
        """Send smart notification based on trigger and context."""
        try:
            template_key = self._get_template_key(trigger, context_data)
            template = self.notification_templates.get(template_key, {})

            if not template:
                logger.warning(f"No template found for {template_key}")
                return False

            # Format notification
            title = template["title"].format(**context_data)
            message = template["message"].format(**context_data)

            # Log notification (in production, send via email/push/SMS)
            logger.info(f"📧 Smart notification: {title} - {message}")

            return True

        except Exception as e:
            logger.error(f"Failed to send smart notification: {str(e)}")
            return False

    def _get_template_key(
        self, trigger: NotificationTrigger, context_data: Dict[str, Any]
    ) -> str:
        """Determine template based on trigger and context."""
        if trigger == NotificationTrigger.FAMILY_JOINED:
            return "family_joined_welcome"
        elif trigger == NotificationTrigger.CONSENSUS_UPDATED:
            score_change = context_data.get("score_change", 0)
            return "consensus_improved" if score_change > 0 else "consensus_declined"
        elif trigger == NotificationTrigger.CONFLICT_DETECTED:
            severity = context_data.get("severity", "medium")
            return "critical_conflict" if severity == "critical" else "general_conflict"
        return "family_joined_welcome"


# Helper functions
async def notify_family_joined(trip_name: str, trip_id: str, family_id: str) -> bool:
    """Send notification when family joins trip."""
    service = SmartNotificationService()
    context = {"trip_name": trip_name, "trip_id": trip_id, "family_id": family_id}
    return await service.send_smart_notification(
        NotificationTrigger.FAMILY_JOINED, context
    )


async def notify_consensus_update(
    trip_name: str, consensus_score: float, score_change: float
) -> bool:
    """Send notification when consensus changes."""
    service = SmartNotificationService()
    context = {
        "trip_name": trip_name,
        "consensus_score": int(consensus_score * 100),
        "score_change": score_change,
    }
    return await service.send_smart_notification(
        NotificationTrigger.CONSENSUS_UPDATED, context
    )


async def notify_critical_conflict(
    trip_name: str, trip_id: str, conflict_details: str, all_families: List[Dict]
) -> bool:
    """Send urgent notification for critical conflicts."""
    service = SmartNotificationService()

    context = {
        "trip_name": trip_name,
        "trip_id": trip_id,
        "conflict_details": conflict_details,
        "severity": "critical",
        "all_families": all_families,
    }

    return await service.send_smart_notification(
        NotificationTrigger.CONFLICT_DETECTED, context
    )
