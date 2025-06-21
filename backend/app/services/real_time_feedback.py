"""
Real-Time Feedback Integration Service - Solves Pain Point #3

"No effective way to gather and incorporate changes/feedback during planning process"

Features:
- Live collaborative editing with change tracking
- In-context commenting and suggestion system
- Change impact visualization (cost, time, logistics)
- Quick approval/rejection workflow for modifications
- Real-time conflict resolution during editing
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback that can be submitted."""

    SUGGESTION = "suggestion"
    CONCERN = "concern"
    APPROVAL = "approval"
    REJECTION = "rejection"
    QUESTION = "question"
    MODIFICATION = "modification"


class FeedbackStatus(Enum):
    """Status of feedback items."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class ChangeImpactLevel(Enum):
    """Impact level of proposed changes."""

    LOW = "low"  # Minor adjustments, no cost/schedule impact
    MEDIUM = "medium"  # Moderate changes, some cost/schedule impact
    HIGH = "high"  # Significant changes, major cost/schedule impact
    CRITICAL = "critical"  # Major restructuring required


@dataclass
class FeedbackItem:
    """Individual feedback item with context and tracking."""

    id: str
    feedback_type: FeedbackType
    trip_id: str
    family_id: str
    user_id: str
    target_element: str  # What they're commenting on (activity, accommodation, etc.)
    content: str
    suggested_change: Optional[str] = None
    impact_analysis: Optional[Dict[str, Any]] = None
    status: FeedbackStatus = FeedbackStatus.PENDING
    responses: List[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.responses is None:
            self.responses = []


@dataclass
class ChangeImpact:
    """Analysis of how a proposed change affects the trip."""

    impact_level: ChangeImpactLevel
    cost_delta: float  # Change in cost (positive = increase, negative = decrease)
    time_delta: int  # Change in time/duration (minutes)
    affected_families: List[str]  # Family IDs that would be affected
    alternative_options: List[str]  # Alternative approaches
    implementation_complexity: str  # Description of what's needed to implement
    risk_assessment: str  # Potential risks or concerns


@dataclass
class LiveEditingSession:
    """Active live editing session for collaborative feedback."""

    session_id: str
    trip_id: str
    active_editors: Set[str]  # User IDs currently editing
    locked_elements: Dict[str, str]  # element_id -> user_id who has lock
    pending_changes: List[Dict[str, Any]]
    last_activity: datetime = None

    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now(timezone.utc)


class RealTimeFeedbackService:
    """
    Service for managing real-time feedback and collaborative editing.

    Addresses Pain Point #3: "No effective way to gather and incorporate
    changes/feedback during planning process"
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.active_sessions: Dict[str, LiveEditingSession] = {}
        self.feedback_store: Dict[str, List[FeedbackItem]] = {}  # trip_id -> feedback list

    # Real-time feedback collection

    async def submit_feedback(self, feedback_item: FeedbackItem) -> Dict[str, Any]:
        """Submit new feedback item with impact analysis."""
        try:
            # Analyze impact of the feedback/suggestion
            if feedback_item.suggested_change:
                impact = await self._analyze_change_impact(feedback_item)
                feedback_item.impact_analysis = asdict(impact)

            # Store feedback
            trip_id = feedback_item.trip_id
            if trip_id not in self.feedback_store:
                self.feedback_store[trip_id] = []

            self.feedback_store[trip_id].append(feedback_item)

            # Notify relevant parties
            await self._notify_feedback_received(feedback_item)

            # Check if immediate action is needed
            if feedback_item.feedback_type in [FeedbackType.CONCERN, FeedbackType.REJECTION]:
                await self._trigger_urgent_review(feedback_item)

            logger.info(
                f"Feedback submitted: {feedback_item.feedback_type.value} for trip {trip_id}"
            )

            return {
                "success": True,
                "feedback_id": feedback_item.id,
                "impact_analysis": feedback_item.impact_analysis,
                "next_steps": self._get_next_steps(feedback_item),
            }

        except Exception as e:
            logger.error(f"Failed to submit feedback: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_trip_feedback(
        self, trip_id: str, status_filter: Optional[FeedbackStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get all feedback for a trip, optionally filtered by status."""
        try:
            feedback_list = self.feedback_store.get(trip_id, [])

            if status_filter:
                feedback_list = [f for f in feedback_list if f.status == status_filter]

            # Convert to dict format and add summary stats
            feedback_data = []
            for feedback in feedback_list:
                feedback_dict = asdict(feedback)
                feedback_dict["created_at"] = feedback.created_at.isoformat()
                feedback_dict["updated_at"] = feedback.updated_at.isoformat()
                feedback_data.append(feedback_dict)

            return feedback_data

        except Exception as e:
            logger.error(f"Failed to get trip feedback: {str(e)}")
            return []

    async def respond_to_feedback(self, feedback_id: str, response: Dict[str, Any]) -> bool:
        """Respond to existing feedback item."""
        try:
            # Find feedback item
            feedback_item = None
            for trip_feedback in self.feedback_store.values():
                for item in trip_feedback:
                    if item.id == feedback_id:
                        feedback_item = item
                        break
                if feedback_item:
                    break

            if not feedback_item:
                logger.warning(f"Feedback item {feedback_id} not found")
                return False

            # Add response
            response["timestamp"] = datetime.now(timezone.utc).isoformat()
            feedback_item.responses.append(response)
            feedback_item.updated_at = datetime.now(timezone.utc)

            # Update status if specified
            if "new_status" in response:
                feedback_item.status = FeedbackStatus(response["new_status"])

            # Notify relevant parties
            await self._notify_feedback_response(feedback_item, response)

            logger.info(f"Response added to feedback {feedback_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to respond to feedback: {str(e)}")
            return False

    # Live collaborative editing

    async def start_editing_session(self, trip_id: str, user_id: str) -> str:
        """Start or join a live editing session."""
        try:
            session_id = f"edit_{trip_id}"

            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = LiveEditingSession(
                    session_id=session_id,
                    trip_id=trip_id,
                    active_editors=set(),
                    locked_elements={},
                    pending_changes=[],
                )

            session = self.active_sessions[session_id]
            session.active_editors.add(user_id)
            session.last_activity = datetime.now(timezone.utc)

            # Notify other editors
            await self._notify_editor_joined(session, user_id)

            logger.info(f"User {user_id} joined editing session for trip {trip_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to start editing session: {str(e)}")
            return ""

    async def lock_element(self, session_id: str, user_id: str, element_id: str) -> bool:
        """Lock an element for editing by a specific user."""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]

            # Check if element is already locked
            if element_id in session.locked_elements:
                current_owner = session.locked_elements[element_id]
                if current_owner != user_id:
                    logger.info(f"Element {element_id} already locked by {current_owner}")
                    return False

            # Lock the element
            session.locked_elements[element_id] = user_id
            session.last_activity = datetime.now(timezone.utc)

            # Notify other editors
            await self._notify_element_locked(session, user_id, element_id)

            return True

        except Exception as e:
            logger.error(f"Failed to lock element: {str(e)}")
            return False

    async def submit_live_change(
        self, session_id: str, user_id: str, change_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit a live change during collaborative editing."""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            session = self.active_sessions[session_id]

            # Validate user has lock on the element being changed
            element_id = change_data.get("element_id")
            if element_id and element_id in session.locked_elements:
                if session.locked_elements[element_id] != user_id:
                    return {"success": False, "error": "Element locked by another user"}

            # Analyze change impact
            impact = await self._analyze_live_change_impact(change_data, session.trip_id)

            # Add change to pending list
            change_record = {
                "change_id": f"change_{len(session.pending_changes)}_{int(datetime.now().timestamp())}",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "change_data": change_data,
                "impact_analysis": asdict(impact),
                "status": (
                    "pending_approval"
                    if impact.impact_level in [ChangeImpactLevel.HIGH, ChangeImpactLevel.CRITICAL]
                    else "auto_approved"
                ),
            }

            session.pending_changes.append(change_record)
            session.last_activity = datetime.now(timezone.utc)

            # Notify other editors
            await self._notify_live_change(session, change_record)

            # Auto-implement low-impact changes
            if impact.impact_level in [ChangeImpactLevel.LOW, ChangeImpactLevel.MEDIUM]:
                await self._implement_change(change_record, session.trip_id)
                change_record["status"] = "implemented"

            return {
                "success": True,
                "change_id": change_record["change_id"],
                "impact_analysis": change_record["impact_analysis"],
                "status": change_record["status"],
                "requires_approval": impact.impact_level
                in [ChangeImpactLevel.HIGH, ChangeImpactLevel.CRITICAL],
            }

        except Exception as e:
            logger.error(f"Failed to submit live change: {str(e)}")
            return {"success": False, "error": str(e)}

    async def approve_change(self, session_id: str, change_id: str, approver_id: str) -> bool:
        """Approve a pending change."""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]

            # Find the change
            change_record = None
            for change in session.pending_changes:
                if change["change_id"] == change_id:
                    change_record = change
                    break

            if not change_record:
                return False

            # Implement the change
            await self._implement_change(change_record, session.trip_id)
            change_record["status"] = "approved_and_implemented"
            change_record["approved_by"] = approver_id
            change_record["approved_at"] = datetime.now(timezone.utc).isoformat()

            # Notify editors
            await self._notify_change_approved(session, change_record)

            logger.info(f"Change {change_id} approved and implemented by {approver_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to approve change: {str(e)}")
            return False

    # Analysis and impact assessment

    async def _analyze_change_impact(self, feedback_item: FeedbackItem) -> ChangeImpact:
        """Analyze the impact of a proposed change."""
        try:
            content = feedback_item.content.lower()

            # Simple heuristics for impact assessment
            impact_level = ChangeImpactLevel.LOW
            cost_delta = 0.0
            time_delta = 0

            # Cost-related changes
            if any(word in content for word in ["expensive", "budget", "cost", "price"]):
                impact_level = ChangeImpactLevel.MEDIUM
                cost_delta = 50.0

            # Time-related changes
            if any(word in content for word in ["time", "schedule", "duration", "delay"]):
                impact_level = ChangeImpactLevel.MEDIUM
                time_delta = 30

            # High-impact keywords
            if any(word in content for word in ["cancel", "replace", "major"]):
                impact_level = ChangeImpactLevel.HIGH
                cost_delta = 200.0
                time_delta = 120

            # Critical impact keywords
            if any(word in content for word in ["safety", "emergency", "critical"]):
                impact_level = ChangeImpactLevel.CRITICAL
                cost_delta = 500.0
                time_delta = 240

            return ChangeImpact(
                impact_level=impact_level,
                cost_delta=cost_delta,
                time_delta=time_delta,
                affected_families=[feedback_item.family_id],
                alternative_options=self._generate_alternatives(feedback_item),
                implementation_complexity=self._assess_complexity(impact_level),
                risk_assessment=self._assess_risks(impact_level),
            )

        except Exception as e:
            logger.error(f"Failed to analyze change impact: {str(e)}")
            return ChangeImpact(
                impact_level=ChangeImpactLevel.LOW,
                cost_delta=0.0,
                time_delta=0,
                affected_families=[],
                alternative_options=[],
                implementation_complexity="Unknown",
                risk_assessment="Unable to assess",
            )

    async def _analyze_live_change_impact(
        self, change_data: Dict[str, Any], trip_id: str
    ) -> ChangeImpact:
        """Analyze impact of a live change during collaborative editing."""
        # Similar to _analyze_change_impact but for live editing context
        change_type = change_data.get("type", "modification")

        if change_type == "delete":
            impact_level = ChangeImpactLevel.HIGH
        elif change_type == "add":
            impact_level = ChangeImpactLevel.MEDIUM
        else:  # modification
            impact_level = ChangeImpactLevel.LOW

        return ChangeImpact(
            impact_level=impact_level,
            cost_delta=0.0,
            time_delta=15,  # Assume small time impact for live changes
            affected_families=[],
            alternative_options=[],
            implementation_complexity="Real-time implementation",
            risk_assessment="Low risk for live changes",
        )

    def _generate_alternatives(self, feedback_item: FeedbackItem) -> List[str]:
        """Generate alternative approaches based on feedback."""
        alternatives = []

        if feedback_item.feedback_type == FeedbackType.CONCERN:
            alternatives.extend(
                [
                    "Modify the existing plan to address concerns",
                    "Provide additional options for the family",
                    "Discuss alternatives in family meeting",
                ]
            )
        elif feedback_item.feedback_type == FeedbackType.SUGGESTION:
            alternatives.extend(
                [
                    "Implement suggestion as proposed",
                    "Implement modified version of suggestion",
                    "Combine with other family suggestions",
                ]
            )

        return alternatives

    def _assess_complexity(self, impact_level: ChangeImpactLevel) -> str:
        """Assess implementation complexity based on impact level."""
        complexity_map = {
            ChangeImpactLevel.LOW: "Simple modification, can be implemented immediately",
            ChangeImpactLevel.MEDIUM: "Moderate changes required, may need family coordination",
            ChangeImpactLevel.HIGH: "Significant replanning required, affects multiple elements",
            ChangeImpactLevel.CRITICAL: "Major restructuring needed, requires all family approval",
        }
        return complexity_map.get(impact_level, "Unknown complexity")

    def _assess_risks(self, impact_level: ChangeImpactLevel) -> str:
        """Assess risks associated with the change."""
        risk_map = {
            ChangeImpactLevel.LOW: "Minimal risk, unlikely to affect other families",
            ChangeImpactLevel.MEDIUM: "Some risk of cost or schedule impact",
            ChangeImpactLevel.HIGH: "Higher risk of significant disruption to trip plans",
            ChangeImpactLevel.CRITICAL: "High risk - could affect trip viability or safety",
        }
        return risk_map.get(impact_level, "Risk assessment unavailable")

    def _get_next_steps(self, feedback_item: FeedbackItem) -> List[str]:
        """Get recommended next steps based on feedback type and impact."""
        next_steps = []

        if feedback_item.impact_analysis:
            impact_level = ChangeImpactLevel(feedback_item.impact_analysis["impact_level"])

            if impact_level == ChangeImpactLevel.CRITICAL:
                next_steps.extend(
                    [
                        "Immediate review by trip organizer required",
                        "Family discussion recommended",
                        "Consider impact on all families",
                    ]
                )
            elif impact_level == ChangeImpactLevel.HIGH:
                next_steps.extend(
                    ["Review with other families", "Assess cost and schedule implications"]
                )
            else:
                next_steps.extend(
                    ["Review and implement if appropriate", "Notify affected families of change"]
                )

        return next_steps

    # Notification methods (placeholder implementations)

    async def _notify_feedback_received(self, feedback_item: FeedbackItem):
        """Notify relevant parties that feedback was received."""
        logger.info(
            f"📝 Feedback received: {feedback_item.feedback_type.value} from family {feedback_item.family_id}"
        )

    async def _trigger_urgent_review(self, feedback_item: FeedbackItem):
        """Trigger urgent review for critical feedback."""
        logger.info(f"🚨 Urgent review triggered for feedback: {feedback_item.id}")

    async def _notify_feedback_response(
        self, feedback_item: FeedbackItem, response: Dict[str, Any]
    ):
        """Notify about response to feedback."""
        logger.info(f"💬 Response added to feedback {feedback_item.id}")

    async def _notify_editor_joined(self, session: LiveEditingSession, user_id: str):
        """Notify about user joining editing session."""
        logger.info(f"👥 User {user_id} joined editing session {session.session_id}")

    async def _notify_element_locked(
        self, session: LiveEditingSession, user_id: str, element_id: str
    ):
        """Notify about element being locked for editing."""
        logger.info(f"🔒 Element {element_id} locked by {user_id}")

    async def _notify_live_change(self, session: LiveEditingSession, change_record: Dict[str, Any]):
        """Notify about live change being made."""
        logger.info(f"⚡ Live change submitted: {change_record['change_id']}")

    async def _notify_change_approved(
        self, session: LiveEditingSession, change_record: Dict[str, Any]
    ):
        """Notify about change being approved."""
        logger.info(f"✅ Change approved: {change_record['change_id']}")

    async def _implement_change(self, change_record: Dict[str, Any], trip_id: str):
        """Actually implement the approved change."""
        # In production, this would update the trip data
        logger.info(f"🔧 Implementing change {change_record['change_id']} for trip {trip_id}")


# Helper functions for easy integration


async def submit_trip_feedback(
    db: AsyncSession,
    trip_id: str,
    family_id: str,
    user_id: str,
    feedback_type: str,
    content: str,
    target_element: str,
    suggested_change: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit feedback for a trip element."""
    service = RealTimeFeedbackService(db)

    feedback_item = FeedbackItem(
        id=f"feedback_{trip_id}_{family_id}_{int(datetime.now().timestamp())}",
        feedback_type=FeedbackType(feedback_type),
        trip_id=trip_id,
        family_id=family_id,
        user_id=user_id,
        target_element=target_element,
        content=content,
        suggested_change=suggested_change,
    )

    return await service.submit_feedback(feedback_item)


async def get_feedback_dashboard_data(db: AsyncSession, trip_id: str) -> Dict[str, Any]:
    """Get comprehensive feedback dashboard data for a trip."""
    service = RealTimeFeedbackService(db)

    all_feedback = await service.get_trip_feedback(trip_id)
    pending_feedback = await service.get_trip_feedback(trip_id, FeedbackStatus.PENDING)

    # Calculate summary statistics
    feedback_by_type = {}
    for feedback in all_feedback:
        fb_type = feedback["feedback_type"]
        feedback_by_type[fb_type] = feedback_by_type.get(fb_type, 0) + 1

    return {
        "trip_id": trip_id,
        "total_feedback_items": len(all_feedback),
        "pending_items": len(pending_feedback),
        "feedback_by_type": feedback_by_type,
        "recent_feedback": all_feedback[-5:] if all_feedback else [],  # Last 5 items
        "active_editing_sessions": len(service.active_sessions),
        "response_rate": 0.85,  # Placeholder - calculate based on actual responses
        "average_resolution_time_hours": 4.2,  # Placeholder
    }
