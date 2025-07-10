"""
Data models for AI integration features including Pathfinder Assistant and Magic Polls
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text


class ContextType(str, Enum):
    """Context types for AI assistant interactions"""

    TRIP_PLANNING = "trip_planning"
    ITINERARY_REVIEW = "itinerary_review"
    FAMILY_COORDINATION = "family_coordination"
    BUDGET_DISCUSSION = "budget_discussion"
    ACTIVITY_SELECTION = "activity_selection"
    SCHEDULING = "scheduling"
    GENERAL_HELP = "general_help"


class PollType(str, Enum):
    """Types of Magic Polls"""

    DESTINATION_CHOICE = "destination_choice"
    ACTIVITY_PREFERENCE = "activity_preference"
    BUDGET_RANGE = "budget_range"
    DATE_SELECTION = "date_selection"
    ACCOMMODATION_TYPE = "accommodation_type"
    MEAL_PREFERENCE = "meal_preference"
    TRANSPORTATION = "transportation"
    CUSTOM = "custom"


class PollStatus(str, Enum):
    """Magic Poll status"""

    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SuggestionType(str, Enum):
    """AI suggestion types"""

    TRIP_IMPROVEMENT = "trip_improvement"
    COST_OPTIMIZATION = "cost_optimization"
    SCHEDULING_CONFLICT = "scheduling_conflict"
    FAMILY_COORDINATION = "family_coordination"
    ACTIVITY_RECOMMENDATION = "activity_recommendation"
    BUDGET_ALERT = "budget_alert"


class ResponseCardType(str, Enum):
    """Types of AI response cards"""

    DESTINATION_INFO = "destination_info"
    ACTIVITY_SUGGESTION = "activity_suggestion"
    BUDGET_BREAKDOWN = "budget_breakdown"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    FAMILY_TIPS = "family_tips"
    ACTION_ITEMS = "action_items"


class AssistantInteraction(Base):
    """Model for Pathfinder Assistant interactions"""

    __tablename__ = "assistant_interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    trip_id = Column(String, nullable=True)
    family_id = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    context_type = Column(String(50), nullable=False)
    response_data = Column(JSON, nullable=True)
    response_cards = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    feedback_rating = Column(Integer, nullable=True)  # 1-5 star rating
    processing_time_ms = Column(Integer, nullable=True)
    ai_provider = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trip_id": self.trip_id,
            "family_id": self.family_id,
            "message": self.message,
            "context_type": self.context_type,
            "response_data": self.response_data,
            "response_cards": self.response_cards,
            "suggestions": self.suggestions,
            "feedback_rating": self.feedback_rating,
            "processing_time_ms": self.processing_time_ms,
            "ai_provider": self.ai_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MagicPoll(Base):
    """Model for Magic Polls with AI-powered decision making"""

    __tablename__ = "magic_polls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String, nullable=False)
    creator_id = Column(String, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    poll_type = Column(String(50), nullable=False)
    # List of poll options with metadata
    options = Column(JSON, nullable=False)
    responses = Column(JSON, nullable=True)  # User responses and preferences
    ai_analysis = Column(JSON, nullable=True)  # AI analysis of responses
    consensus_recommendation = Column(JSON, nullable=True)  # AI recommendation
    status = Column(String(50), nullable=False, default=PollStatus.ACTIVE.value)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "creator_id": self.creator_id,
            "title": self.title,
            "description": self.description,
            "poll_type": self.poll_type,
            "options": self.options,
            "responses": self.responses,
            "ai_analysis": self.ai_analysis,
            "consensus_recommendation": self.consensus_recommendation,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_expired(self) -> bool:
        """Check if the poll has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def get_response_count(self) -> int:
        """Get the number of responses to this poll"""
        if not self.responses:
            return 0
        return len(self.responses.get("user_responses", []))


class AIResponseCard(Base):
    """Model for rich AI response cards"""

    __tablename__ = "ai_response_cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interaction_id = Column(String, nullable=False)
    card_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    # Rich content with images, text, etc.
    content = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=True)  # Available actions for the card
    card_metadata = Column(JSON, nullable=True)  # Additional metadata
    display_order = Column(Integer, nullable=False, default=0)
    is_dismissed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "interaction_id": self.interaction_id,
            "card_type": self.card_type,
            "title": self.title,
            "content": self.content,
            "actions": self.actions,
            "metadata": self.metadata,
            "display_order": self.display_order,
            "is_dismissed": self.is_dismissed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AISuggestion(Base):
    """Model for contextual AI suggestions"""

    __tablename__ = "ai_suggestions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    trip_id = Column(String, nullable=True)
    suggestion_type = Column(String(50), nullable=False)
    context = Column(String(100), nullable=False)  # Current context/page
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Data needed to execute the suggestion
    action_data = Column(JSON, nullable=True)
    priority = Column(Integer, nullable=False, default=5)  # 1-10 priority scale
    is_acknowledged = Column(Boolean, nullable=False, default=False)
    is_dismissed = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trip_id": self.trip_id,
            "suggestion_type": self.suggestion_type,
            "context": self.context,
            "title": self.title,
            "description": self.description,
            "action_data": self.action_data,
            "priority": self.priority,
            "is_acknowledged": self.is_acknowledged,
            "is_dismissed": self.is_dismissed,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_expired(self) -> bool:
        """Check if the suggestion has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        """Check if the suggestion is still active"""
        return not self.is_dismissed and not self.is_acknowledged and not self.is_expired()


# Helper functions for creating common AI interactions


def create_assistant_interaction(
    user_id: str,
    message: str,
    context_type: ContextType,
    trip_id: Optional[str] = None,
    family_id: Optional[str] = None,
) -> AssistantInteraction:
    """Create a new assistant interaction"""
    return AssistantInteraction(
        user_id=user_id,
        trip_id=trip_id,
        family_id=family_id,
        message=message,
        context_type=context_type.value,
    )


def create_magic_poll(
    trip_id: str,
    creator_id: str,
    title: str,
    poll_type: PollType,
    options: List[Dict[str, Any]],
    description: Optional[str] = None,
    expires_hours: int = 72,
) -> MagicPoll:
    """Create a new Magic Poll"""
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

    return MagicPoll(
        trip_id=trip_id,
        creator_id=creator_id,
        title=title,
        description=description,
        poll_type=poll_type.value,
        options=options,
        responses={"user_responses": []},
        expires_at=expires_at,
    )


def create_ai_suggestion(
    user_id: str,
    suggestion_type: SuggestionType,
    context: str,
    title: str,
    description: Optional[str] = None,
    trip_id: Optional[str] = None,
    action_data: Optional[Dict[str, Any]] = None,
    priority: int = 5,
    expires_hours: Optional[int] = None,
) -> AISuggestion:
    """Create a new AI suggestion"""
    expires_at = None
    if expires_hours:
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

    return AISuggestion(
        user_id=user_id,
        trip_id=trip_id,
        suggestion_type=suggestion_type.value,
        context=context,
        title=title,
        description=description,
        action_data=action_data,
        priority=priority,
        expires_at=expires_at,
    )
