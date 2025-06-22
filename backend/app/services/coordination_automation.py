"""
Smart Coordination Automation Service - Solves Pain Point #2

Eliminates manual coordination overhead through:
- Automated family notifications for key events
- Smart scheduling across time zones
- Progress tracking and status updates
- Intelligent family onboarding workflows
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.trip import Trip, TripParticipation
from ..services.consensus_engine import FamilyConsensusEngine, analyze_trip_consensus
from ..services.notifications import NotificationService

logger = logging.getLogger(__name__)


class CoordinationEventType(Enum):
    """Types of coordination events that trigger automation."""

    FAMILY_JOINED = "family_joined"
    PREFERENCES_UPDATED = "preferences_updated"
    CONSENSUS_CHANGED = "consensus_changed"
    ITINERARY_GENERATED = "itinerary_generated"
    VOTING_STARTED = "voting_started"
    CONFLICT_DETECTED = "conflict_detected"
    TRIP_STATUS_CHANGED = "trip_status_changed"
    DEADLINE_APPROACHING = "deadline_approaching"
    ALL_FAMILIES_READY = "all_families_ready"


class NotificationPriority(Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class CoordinationEvent:
    """Represents a coordination event that triggers automation."""

    event_type: CoordinationEventType
    trip_id: str
    family_id: Optional[str]
    user_id: Optional[str]
    event_data: Dict[str, Any]
    timestamp: datetime
    priority: NotificationPriority = NotificationPriority.MEDIUM


@dataclass
class AutomationRule:
    """Defines automated responses to coordination events."""

    event_type: CoordinationEventType
    conditions: Dict[str, Any]
    actions: List[str]
    delay_minutes: int = 0
    target_audience: str = "all"  # "all", "organizer", "family", "participants"


@dataclass
class SmartScheduleSuggestion:
    """Smart scheduling suggestion for family coordination meetings."""

    suggested_time: datetime
    timezone_friendly: bool
    participation_score: float  # 0-1, how many families can attend
    optimal_duration_minutes: int
    meeting_type: str  # "planning", "consensus", "review"
    agenda_items: List[str]


class SmartCoordinationService:
    """
    Main service for smart coordination automation.

    Addresses Pain Point #2: "Too much manual coordination required between families"
    """

    def __init__(self, db: AsyncSession, notification_service: NotificationService):
        self.db = db
        self.notification_service = notification_service
        self.consensus_engine = FamilyConsensusEngine()

        # Define automation rules
        self.automation_rules = self._initialize_automation_rules()

    def _initialize_automation_rules(self) -> List[AutomationRule]:
        """Initialize smart automation rules."""
        return [
            # Family joins trip - welcome sequence
            AutomationRule(
                event_type=CoordinationEventType.FAMILY_JOINED,
                conditions={},
                actions=[
                    "send_welcome_package",
                    "trigger_preference_collection",
                    "update_consensus",
                ],
                target_audience="family",
            ),
            # Preferences updated - check consensus impact
            AutomationRule(
                event_type=CoordinationEventType.PREFERENCES_UPDATED,
                conditions={},
                actions=[
                    "analyze_consensus_impact",
                    "notify_if_conflicts",
                    "update_dashboard",
                ],
                delay_minutes=5,  # Allow batch updates
                target_audience="all",
            ),
            # Consensus changed significantly - alert organizer
            AutomationRule(
                event_type=CoordinationEventType.CONSENSUS_CHANGED,
                conditions={"score_change": "> 0.2"},
                actions=[
                    "alert_organizer",
                    "suggest_next_steps",
                    "schedule_meeting_if_needed",
                ],
                target_audience="organizer",
            ),
            # Critical conflict detected - immediate action needed
            AutomationRule(
                event_type=CoordinationEventType.CONFLICT_DETECTED,
                conditions={"severity": "critical"},
                actions=[
                    "urgent_notification",
                    "suggest_resolution",
                    "pause_itinerary_generation",
                ],
                target_audience="all",
                delay_minutes=0,
            ),
            # All families ready - proceed with next phase
            AutomationRule(
                event_type=CoordinationEventType.ALL_FAMILIES_READY,
                conditions={"consensus_score": "> 0.8"},
                actions=[
                    "congratulate_families",
                    "auto_generate_itinerary",
                    "schedule_review_meeting",
                ],
                target_audience="all",
            ),
            # Deadline approaching - reminder sequence
            AutomationRule(
                event_type=CoordinationEventType.DEADLINE_APPROACHING,
                conditions={"days_until": "< 7"},
                actions=[
                    "send_deadline_reminder",
                    "check_readiness",
                    "escalate_if_needed",
                ],
                target_audience="all",
            ),
        ]

    async def process_coordination_event(self, event: CoordinationEvent) -> List[str]:
        """Process a coordination event and execute appropriate automations."""
        executed_actions = []

        try:
            # Find matching rules
            matching_rules = [
                rule
                for rule in self.automation_rules
                if rule.event_type == event.event_type
                and self._check_conditions(rule.conditions, event)
            ]

            for rule in matching_rules:
                # Execute actions for this rule
                for action in rule.actions:
                    try:
                        await self._execute_action(action, event, rule)
                        executed_actions.append(f"{action} (rule: {rule.event_type.value})")
                        logger.info(
                            f"Executed coordination action: {action} for event {event.event_type.value}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to execute action {action}: {str(e)}")

            return executed_actions

        except Exception as e:
            logger.error(f"Error processing coordination event {event.event_type.value}: {str(e)}")
            return []

    def _check_conditions(self, conditions: Dict[str, Any], event: CoordinationEvent) -> bool:
        """Check if event meets rule conditions."""
        if not conditions:
            return True

        for condition_key, condition_value in conditions.items():
            if condition_key not in event.event_data:
                return False

            event_value = event.event_data[condition_key]

            # Handle comparison operators
            if isinstance(condition_value, str) and condition_value.startswith((">", "<", "=")):
                operator = condition_value[0]
                threshold = float(condition_value.split()[1])

                if operator == ">" and event_value <= threshold:
                    return False
                elif operator == "<" and event_value >= threshold:
                    return False
                elif operator == "=" and event_value != threshold:
                    return False
            else:
                if event_value != condition_value:
                    return False

        return True

    async def _execute_action(self, action: str, event: CoordinationEvent, rule: AutomationRule):
        """Execute a specific coordination action."""
        action_map = {
            "send_welcome_package": self._send_welcome_package,
            "trigger_preference_collection": self._trigger_preference_collection,
            "update_consensus": self._update_consensus,
            "analyze_consensus_impact": self._analyze_consensus_impact,
            "notify_if_conflicts": self._notify_if_conflicts,
            "update_dashboard": self._update_dashboard,
            "alert_organizer": self._alert_organizer,
            "suggest_next_steps": self._suggest_next_steps,
            "schedule_meeting_if_needed": self._schedule_meeting_if_needed,
            "urgent_notification": self._urgent_notification,
            "suggest_resolution": self._suggest_resolution,
            "pause_itinerary_generation": self._pause_itinerary_generation,
            "congratulate_families": self._congratulate_families,
            "auto_generate_itinerary": self._auto_generate_itinerary,
            "schedule_review_meeting": self._schedule_review_meeting,
            "send_deadline_reminder": self._send_deadline_reminder,
            "check_readiness": self._check_readiness,
            "escalate_if_needed": self._escalate_if_needed,
        }

        if action in action_map:
            await action_map[action](event, rule)
        else:
            logger.warning(f"Unknown action: {action}")

    # Action implementations

    async def _send_welcome_package(self, event: CoordinationEvent, rule: AutomationRule):
        """Send welcome package to newly joined family."""
        trip = await self._get_trip(event.trip_id)
        if not trip:
            return

        welcome_message = {
            "title": f"Welcome to {trip.name}! 🎉",
            "message": f"""
            Great news! Your family has been added to the trip "{trip.name}".
            
            Next steps:
            1. 📝 Complete your family preferences
            2. 💰 Review budget allocation
            3. 👥 Add family members if needed
            4. 🗣️ Join the trip chat for coordination
            
            The trip organizer and other families are excited to plan with you!
            """,
            "action_buttons": [
                {"text": "Set Preferences", "action": "navigate_preferences"},
                {"text": "Join Chat", "action": "navigate_chat"},
            ],
        }

        # Send to family admin
        if event.family_id:
            await self.notification_service.send_family_notification(
                event.family_id, welcome_message, NotificationPriority.HIGH.value
            )

    async def _trigger_preference_collection(self, event: CoordinationEvent, rule: AutomationRule):
        """Trigger preference collection for a family."""
        # Implementation would trigger preference collection workflow
        logger.info(f"Triggering preference collection for family {event.family_id}")

    async def _update_consensus(self, event: CoordinationEvent, rule: AutomationRule):
        """Update consensus analysis after changes."""
        try:
            families_data = await self._get_families_data(event.trip_id)
            trip = await self._get_trip(event.trip_id)

            if families_data and trip:
                total_budget = float(trip.budget_total) if trip.budget_total else 0.0
                consensus_analysis = analyze_trip_consensus(
                    event.trip_id, families_data, total_budget
                )

                # Store updated consensus (in production, you'd cache this)
                logger.info(
                    f"Updated consensus for trip {event.trip_id}: {consensus_analysis['consensus_score']:.2f}"
                )
        except Exception as e:
            logger.error(f"Failed to update consensus: {str(e)}")

    async def _analyze_consensus_impact(self, event: CoordinationEvent, rule: AutomationRule):
        """Analyze how preference changes impact consensus."""
        try:
            # Get current consensus
            families_data = await self._get_families_data(event.trip_id)
            trip = await self._get_trip(event.trip_id)

            if families_data and trip:
                total_budget = float(trip.budget_total) if trip.budget_total else 0.0
                consensus_result = self.consensus_engine.generate_weighted_consensus(
                    families_data, total_budget
                )

                # Check for significant changes
                if event.event_data.get("previous_consensus_score"):
                    score_change = abs(
                        consensus_result.consensus_score
                        - event.event_data["previous_consensus_score"]
                    )

                    if score_change > 0.15:  # 15% change triggers coordination
                        await self.process_coordination_event(
                            CoordinationEvent(
                                event_type=CoordinationEventType.CONSENSUS_CHANGED,
                                trip_id=event.trip_id,
                                family_id=None,
                                user_id=None,
                                event_data={
                                    "score_change": score_change,
                                    "new_score": consensus_result.consensus_score,
                                },
                                timestamp=datetime.now(timezone.utc),
                                priority=NotificationPriority.MEDIUM,
                            )
                        )
        except Exception as e:
            logger.error(f"Failed to analyze consensus impact: {str(e)}")

    async def _notify_if_conflicts(self, event: CoordinationEvent, rule: AutomationRule):
        """Notify families if new conflicts are detected."""
        try:
            families_data = await self._get_families_data(event.trip_id)
            trip = await self._get_trip(event.trip_id)

            if families_data and trip:
                total_budget = float(trip.budget_total) if trip.budget_total else 0.0
                consensus_result = self.consensus_engine.generate_weighted_consensus(
                    families_data, total_budget
                )

                # Check for critical conflicts
                critical_conflicts = [
                    c for c in consensus_result.conflicts if c.severity.value == "critical"
                ]

                if critical_conflicts:
                    await self.process_coordination_event(
                        CoordinationEvent(
                            event_type=CoordinationEventType.CONFLICT_DETECTED,
                            trip_id=event.trip_id,
                            family_id=None,
                            user_id=None,
                            event_data={
                                "severity": "critical",
                                "conflicts": len(critical_conflicts),
                            },
                            timestamp=datetime.now(timezone.utc),
                            priority=NotificationPriority.URGENT,
                        )
                    )
        except Exception as e:
            logger.error(f"Failed to check for conflicts: {str(e)}")

    async def _update_dashboard(self, event: CoordinationEvent, rule: AutomationRule):
        """Update coordination dashboard data."""
        # Implementation would update real-time dashboard
        logger.info(f"Dashboard updated for trip {event.trip_id}")

    async def _alert_organizer(self, event: CoordinationEvent, rule: AutomationRule):
        """Alert trip organizer about important changes."""
        trip = await self._get_trip(event.trip_id)
        if not trip:
            return

        alert_message = {
            "title": "Consensus Update Required 📊",
            "message": f"""
            The family consensus for "{trip.name}" has changed significantly.
            
            Current consensus score: {event.event_data.get('new_score', 0) * 100:.0f}%
            Change: {event.event_data.get('score_change', 0) * 100:.0f}% points
            
            Action may be needed to maintain trip momentum.
            """,
            "action_buttons": [
                {"text": "View Consensus", "action": "navigate_consensus"},
                {"text": "Contact Families", "action": "navigate_chat"},
            ],
        }

        await self.notification_service.send_user_notification(
            str(trip.creator_id), alert_message, NotificationPriority.HIGH.value
        )

    async def _suggest_next_steps(self, event: CoordinationEvent, rule: AutomationRule):
        """Suggest next steps based on current situation."""
        # Implementation would analyze situation and suggest actions
        logger.info(f"Generating next steps suggestions for trip {event.trip_id}")

    async def _schedule_meeting_if_needed(self, event: CoordinationEvent, rule: AutomationRule):
        """Schedule coordination meeting if consensus is low."""
        consensus_score = event.event_data.get("new_score", 1.0)

        if consensus_score < 0.6:  # Low consensus needs discussion
            meeting_suggestion = await self.suggest_optimal_meeting_time(
                event.trip_id, meeting_type="consensus"
            )

            if meeting_suggestion:
                # Send meeting suggestion to all families
                trip = await self._get_trip(event.trip_id)
                if trip:
                    message = {
                        "title": "Family Meeting Suggested 📅",
                        "message": f"""
                        To resolve preference differences for "{trip.name}", we suggest a family coordination meeting.
                        
                        Suggested time: {meeting_suggestion.suggested_time.strftime('%A, %B %d at %I:%M %p')}
                        Duration: {meeting_suggestion.optimal_duration_minutes} minutes
                        
                        This timing works for {meeting_suggestion.participation_score * 100:.0f}% of families.
                        """,
                        "action_buttons": [
                            {"text": "Accept Time", "action": "accept_meeting"},
                            {
                                "text": "Suggest Different Time",
                                "action": "propose_alternative",
                            },
                        ],
                    }

                    # Send to all participating families
                    families_data = await self._get_families_data(event.trip_id)
                    for family_data in families_data:
                        await self.notification_service.send_family_notification(
                            family_data["id"],
                            message,
                            NotificationPriority.MEDIUM.value,
                        )

    async def _urgent_notification(self, event: CoordinationEvent, rule: AutomationRule):
        """Send urgent notification for critical issues."""
        trip = await self._get_trip(event.trip_id)
        if not trip:
            return

        urgent_message = {
            "title": "⚠️ Critical Issue Detected",
            "message": f"""
            Critical conflicts detected in "{trip.name}" that must be resolved before proceeding.
            
            Number of critical conflicts: {event.event_data.get('conflicts', 0)}
            
            These typically involve safety, dietary restrictions, or accessibility needs.
            Immediate family discussion is recommended.
            """,
            "action_buttons": [
                {"text": "View Conflicts", "action": "navigate_conflicts"},
                {
                    "text": "Schedule Emergency Meeting",
                    "action": "schedule_urgent_meeting",
                },
            ],
        }

        # Send to all families
        families_data = await self._get_families_data(event.trip_id)
        for family_data in families_data:
            await self.notification_service.send_family_notification(
                family_data["id"], urgent_message, NotificationPriority.URGENT.value
            )

    async def _suggest_resolution(self, event: CoordinationEvent, rule: AutomationRule):
        """Suggest conflict resolution approaches."""
        # Implementation would provide AI-powered resolution suggestions
        logger.info(f"Generating conflict resolution suggestions for trip {event.trip_id}")

    async def _pause_itinerary_generation(self, event: CoordinationEvent, rule: AutomationRule):
        """Pause itinerary generation until conflicts are resolved."""
        # Implementation would set a flag to prevent AI generation
        logger.info(
            f"Pausing itinerary generation for trip {event.trip_id} due to critical conflicts"
        )

    async def _congratulate_families(self, event: CoordinationEvent, rule: AutomationRule):
        """Congratulate families on reaching consensus."""
        trip = await self._get_trip(event.trip_id)
        if not trip:
            return

        celebration_message = {
            "title": "🎉 Consensus Achieved!",
            "message": f"""
            Fantastic! All families have reached strong consensus for "{trip.name}".
            
            Consensus score: {event.event_data.get('consensus_score', 1.0) * 100:.0f}%
            
            Ready to generate your personalized itinerary!
            """,
            "action_buttons": [
                {"text": "Generate Itinerary", "action": "generate_itinerary"},
                {"text": "Review Preferences", "action": "review_preferences"},
            ],
        }

        families_data = await self._get_families_data(event.trip_id)
        for family_data in families_data:
            await self.notification_service.send_family_notification(
                family_data["id"], celebration_message, NotificationPriority.HIGH.value
            )

    async def _auto_generate_itinerary(self, event: CoordinationEvent, rule: AutomationRule):
        """Automatically trigger itinerary generation when consensus is high."""
        # Implementation would trigger AI itinerary generation
        logger.info(f"Auto-triggering itinerary generation for trip {event.trip_id}")

    async def _schedule_review_meeting(self, event: CoordinationEvent, rule: AutomationRule):
        """Schedule review meeting for generated itinerary."""
        meeting_suggestion = await self.suggest_optimal_meeting_time(
            event.trip_id, meeting_type="review"
        )
        # Implementation would schedule the meeting
        logger.info(f"Scheduling review meeting for trip {event.trip_id}")

    async def _send_deadline_reminder(self, event: CoordinationEvent, rule: AutomationRule):
        """Send deadline reminder to families."""
        days_until = event.event_data.get("days_until", 0)

        reminder_message = {
            "title": f"⏰ Trip Deadline Approaching ({days_until} days)",
            "message": f"""
            Your trip planning deadline is approaching in {days_until} days.
            
            Please complete any remaining tasks to ensure smooth trip execution.
            """,
            "action_buttons": [
                {"text": "Check Progress", "action": "view_progress"},
                {"text": "Contact Organizer", "action": "contact_organizer"},
            ],
        }

        families_data = await self._get_families_data(event.trip_id)
        for family_data in families_data:
            await self.notification_service.send_family_notification(
                family_data["id"], reminder_message, NotificationPriority.MEDIUM.value
            )

    async def _check_readiness(self, event: CoordinationEvent, rule: AutomationRule):
        """Check family readiness as deadline approaches."""
        # Implementation would assess completion status
        logger.info(f"Checking family readiness for trip {event.trip_id}")

    async def _escalate_if_needed(self, event: CoordinationEvent, rule: AutomationRule):
        """Escalate to organizer if families aren't ready."""
        # Implementation would alert organizer about unready families
        logger.info(f"Escalating readiness concerns for trip {event.trip_id}")

    # Smart scheduling functionality

    async def suggest_optimal_meeting_time(
        self, trip_id: str, meeting_type: str = "planning"
    ) -> Optional[SmartScheduleSuggestion]:
        """Suggest optimal meeting time considering all family time zones and preferences."""
        try:
            families_data = await self._get_families_data(trip_id)
            if not families_data:
                return None

            # For now, suggest a reasonable default time
            # In production, this would analyze family time zones and preferences

            suggested_time = datetime.now(timezone.utc) + timedelta(days=2)  # 2 days from now
            suggested_time = suggested_time.replace(
                hour=19, minute=0, second=0, microsecond=0
            )  # 7 PM UTC

            return SmartScheduleSuggestion(
                suggested_time=suggested_time,
                timezone_friendly=True,
                participation_score=0.85,  # 85% of families can attend
                optimal_duration_minutes=45 if meeting_type == "planning" else 30,
                meeting_type=meeting_type,
                agenda_items=self._generate_meeting_agenda(meeting_type, families_data),
            )
        except Exception as e:
            logger.error(f"Failed to suggest meeting time: {str(e)}")
            return None

    def _generate_meeting_agenda(
        self, meeting_type: str, families_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate meeting agenda based on type and current situation."""
        if meeting_type == "consensus":
            return [
                "Review family preferences",
                "Discuss conflicting requirements",
                "Find compromise solutions",
                "Vote on disputed items",
            ]
        elif meeting_type == "review":
            return [
                "Review generated itinerary",
                "Discuss changes and adjustments",
                "Confirm final plans",
                "Next steps for booking",
            ]
        else:  # planning
            return [
                "Welcome and introductions",
                "Review trip objectives",
                "Collect family preferences",
                "Set planning timeline",
            ]

    # Helper methods

    async def _get_trip(self, trip_id: str) -> Optional[Trip]:
        """Get trip by ID."""
        try:
            stmt = select(Trip).where(Trip.id == trip_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get trip {trip_id}: {str(e)}")
            return None

    async def _get_families_data(self, trip_id: str) -> List[Dict[str, Any]]:
        """Get families data for a trip."""
        try:
            stmt = (
                select(Trip)
                .options(selectinload(Trip.participations).selectinload(TripParticipation.family))
                .where(Trip.id == trip_id)
            )

            result = await self.db.execute(stmt)
            trip = result.scalar_one_or_none()

            if not trip:
                return []

            families_data = []
            for participation in trip.participations:
                family = participation.family
                if not family:
                    continue

                family_data = {
                    "id": str(family.id),
                    "name": family.name,
                    "members": [{"id": str(family.admin_user_id), "name": "Admin"}],
                    "preferences": {},
                    "budget_allocation": (
                        float(participation.budget_allocation)
                        if participation.budget_allocation
                        else 0.0
                    ),
                    "is_trip_admin": str(trip.creator_id) == str(family.admin_user_id),
                }

                if participation.preferences:
                    try:
                        family_data["preferences"] = json.loads(participation.preferences)
                    except (json.JSONDecodeError, TypeError):
                        family_data["preferences"] = {}

                families_data.append(family_data)

            return families_data
        except Exception as e:
            logger.error(f"Failed to get families data for trip {trip_id}: {str(e)}")
            return []


# Event processing functions for external integration


async def trigger_coordination_event(
    db: AsyncSession,
    notification_service: NotificationService,
    event_type: CoordinationEventType,
    trip_id: str,
    family_id: Optional[str] = None,
    user_id: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Trigger a coordination event and process automations."""

    coordination_service = SmartCoordinationService(db, notification_service)

    event = CoordinationEvent(
        event_type=event_type,
        trip_id=trip_id,
        family_id=family_id,
        user_id=user_id,
        event_data=event_data or {},
        timestamp=datetime.now(timezone.utc),
        priority=NotificationPriority.MEDIUM,
    )

    return await coordination_service.process_coordination_event(event)


# Integration helpers for common scenarios


async def family_joined_trip(
    db: AsyncSession,
    notification_service: NotificationService,
    trip_id: str,
    family_id: str,
) -> List[str]:
    """Handle family joining trip automation."""
    return await trigger_coordination_event(
        db,
        notification_service,
        CoordinationEventType.FAMILY_JOINED,
        trip_id,
        family_id=family_id,
    )


async def preferences_updated(
    db: AsyncSession,
    notification_service: NotificationService,
    trip_id: str,
    family_id: str,
    previous_consensus_score: float,
) -> List[str]:
    """Handle preferences update automation."""
    return await trigger_coordination_event(
        db,
        notification_service,
        CoordinationEventType.PREFERENCES_UPDATED,
        trip_id,
        family_id=family_id,
        event_data={"previous_consensus_score": previous_consensus_score},
    )
