"""
Pathfinder Assistant Service - AI-powered assistant with @mention functionality
"""

import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.schemas.assistant import (
    AIResponseCard,
    AssistantInteraction,
    ContextType,
    ResponseCardType,
    create_assistant_interaction,
)
from app.services.llm_orchestration_client import llm_orchestration_client
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PathfinderAssistantService:
    """Service for handling Pathfinder Assistant interactions"""

    def __init__(self):
        self.mention_pattern = re.compile(r"@pathfinder\s+(.+)", re.IGNORECASE)

    async def process_mention(
        self, message: str, user_id: str, context: Dict[str, Any], db: Session
    ) -> Dict[str, Any]:
        """Process @pathfinder mention and generate AI response"""
        start_time = time.time()

        # Extract the actual query from the @mention
        query = self._extract_query_from_mention(message)
        if not query:
            return self._create_error_response("No query found in @pathfinder mention")

        # Determine context type
        context_type = self._determine_context_type(context)

        # Create interaction record
        interaction = create_assistant_interaction(
            user_id=user_id,
            message=message,
            context_type=context_type,
            trip_id=context.get("trip_id"),
            family_id=context.get("family_id"),
        )

        try:
            # Generate AI response
            ai_response = await self._generate_ai_response(query, context)

            # Create response cards
            response_cards = await self._create_response_cards(ai_response, interaction.id, db)

            # Update interaction with response
            processing_time = int((time.time() - start_time) * 1000)
            interaction.response_data = ai_response
            interaction.response_cards = [card.to_dict() for card in response_cards]
            interaction.processing_time_ms = processing_time
            interaction.ai_provider = ai_response.get("provider", "unknown")

            db.add(interaction)
            db.commit()

            return {
                "success": True,
                "interaction_id": interaction.id,
                "response": ai_response,
                "response_cards": [card.to_dict() for card in response_cards],
                "processing_time_ms": processing_time,
            }

        except Exception as e:
            logger.error(f"Error processing assistant mention: {str(e)}")
            interaction.response_data = {"error": str(e)}
            db.add(interaction)
            db.commit()

            return self._create_error_response(f"Assistant error: {str(e)}")

    def _extract_query_from_mention(self, message: str) -> Optional[str]:
        """Extract the actual query from @pathfinder mention"""
        match = self.mention_pattern.search(message)
        if match:
            return match.group(1).strip()
        return None

    def _determine_context_type(self, context: Dict[str, Any]) -> ContextType:
        """Determine the context type based on current context"""
        current_page = context.get("current_page", "")

        if "trip" in current_page.lower():
            if "itinerary" in current_page.lower():
                return ContextType.ITINERARY_REVIEW
            elif "budget" in current_page.lower():
                return ContextType.BUDGET_DISCUSSION
            else:
                return ContextType.TRIP_PLANNING
        elif "family" in current_page.lower():
            return ContextType.FAMILY_COORDINATION
        else:
            return ContextType.GENERAL_HELP

    async def _generate_ai_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response using LLM Orchestration service"""
        try:
            # Prepare the AI prompt with context
            prompt = self._build_assistant_prompt(query, context)

            # Use LLM Orchestration Client
            response = await llm_orchestration_client.generate_text(
                prompt=prompt,
                task_type="trip_assistance",
                user_id=context.get("user_id"),
                max_tokens=500,
                temperature=0.7,
                model_preference="gpt-3.5-turbo",
            )

            return {
                "text": response.get("content", ""),
                "provider": response.get("provider", "unknown"),
                "model": response.get("model_used", "unknown"),
                "usage": response.get("usage", {}),
                "context_used": context,
                "cost": response.get("cost", 0.0),
                "processing_time": response.get("processing_time", 0.0),
            }

        except Exception as e:
            logger.error(f"Error calling LLM service: {str(e)}")
            # Fallback to simple response
            return {
                "text": f"I understand you're asking about: {query}. Let me help you with that trip planning question.",
                "provider": "fallback",
                "model": "simple",
                "context_used": context,
                "cost": 0.0,
                "processing_time": 0.0,
            }

    def _build_assistant_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build contextual prompt for the AI assistant"""
        system_context = "You are Pathfinder Assistant, an AI helper for family trip planning. Provide helpful, actionable advice for coordinating multi-family trips. "
        system_context += (
            "Always be concise but informative. Suggest specific actions when possible.\n\n"
        )

        base_prompt = f"User question: {query}\n\n"

        # Add context information
        if context.get("trip_id"):
            base_prompt += f"Context: User is planning a trip (ID: {context['trip_id']})\n"

        if context.get("family_id"):
            base_prompt += f"Family context: User is part of family (ID: {context['family_id']})\n"

        if context.get("current_page"):
            base_prompt += f"Current page: {context['current_page']}\n"

        if context.get("trip_data"):
            trip_data = context["trip_data"]
            base_prompt += f"Trip details: {trip_data.get('name', 'Unnamed trip')}\n"
            if trip_data.get("destination"):
                base_prompt += f"Destination: {trip_data['destination']}\n"
            if trip_data.get("start_date") and trip_data.get("end_date"):
                base_prompt += f"Dates: {trip_data['start_date']} to {trip_data['end_date']}\n"

        base_prompt += "\nPlease provide helpful, specific advice for family trip coordination."

        return system_context + base_prompt

    async def _create_response_cards(
        self, ai_response: Dict[str, Any], interaction_id: str, db: Session
    ) -> List[AIResponseCard]:
        """Create structured response cards based on AI response"""
        cards = []
        response_text = ai_response.get("text", "")

        # Create main response card
        main_card = AIResponseCard(
            interaction_id=interaction_id,
            card_type=ResponseCardType.ACTION_ITEMS.value,
            title="Pathfinder Assistant",
            content={"text": response_text, "type": "assistant_response"},
            display_order=0,
        )
        cards.append(main_card)

        # Analyze response and create additional cards
        if "budget" in response_text.lower():
            budget_card = AIResponseCard(
                interaction_id=interaction_id,
                card_type=ResponseCardType.BUDGET_BREAKDOWN.value,
                title="Budget Suggestions",
                content={
                    "text": "Consider creating a shared budget tracker for your trip.",
                    "actions": ["Create Budget", "View Budget Tips"],
                },
                actions=[
                    {"label": "Create Budget", "action": "create_budget"},
                    {"label": "Budget Tips", "action": "show_budget_tips"},
                ],
                display_order=1,
            )
            cards.append(budget_card)

        if "activity" in response_text.lower() or "activities" in response_text.lower():
            activity_card = AIResponseCard(
                interaction_id=interaction_id,
                card_type=ResponseCardType.ACTIVITY_SUGGESTION.value,
                title="Activity Ideas",
                content={
                    "text": "I can help you find family-friendly activities for your destination.",
                    "type": "activity_suggestions",
                },
                actions=[
                    {"label": "Find Activities", "action": "search_activities"},
                    {"label": "Create Poll", "action": "create_activity_poll"},
                ],
                display_order=2,
            )
            cards.append(activity_card)

        # Save cards to database
        for card in cards:
            db.add(card)

        return cards

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": error_message,
            "response": {
                "text": f"Sorry, I encountered an issue: {error_message}. Please try again.",
                "provider": "error",
                "model": "none",
            },
            "response_cards": [],
        }

    async def get_contextual_suggestions(
        self, user_id: str, context: Dict[str, Any], db: Session
    ) -> List[Dict[str, Any]]:
        """Get contextual AI suggestions for the current user context"""
        suggestions = []

        # Generate suggestions based on context
        current_page = context.get("current_page", "")

        if "trip" in current_page.lower():
            suggestions.extend(await self._get_trip_suggestions(context, user_id))

        if "family" in current_page.lower():
            suggestions.extend(await self._get_family_suggestions(context, user_id))

        return suggestions

    async def _get_trip_suggestions(
        self, context: Dict[str, Any], user_id: str
    ) -> List[Dict[str, Any]]:
        """Get trip-specific suggestions"""
        suggestions = []

        trip_data = context.get("trip_data", {})

        # Suggest creating a Magic Poll if no polls exist
        if not trip_data.get("has_polls"):
            suggestions.append(
                {
                    "id": f"poll_suggestion_{user_id}",
                    "type": "create_poll",
                    "title": "Create a Magic Poll",
                    "description": "Let AI help your family make decisions together",
                    "action": "create_magic_poll",
                    "priority": 8,
                }
            )

        # Suggest budget planning if no budget exists
        if not trip_data.get("has_budget"):
            suggestions.append(
                {
                    "id": f"budget_suggestion_{user_id}",
                    "type": "budget_planning",
                    "title": "Set up trip budget",
                    "description": "Track expenses and split costs with other families",
                    "action": "create_budget",
                    "priority": 7,
                }
            )

        return suggestions

    async def _get_family_suggestions(
        self, context: Dict[str, Any], user_id: str
    ) -> List[Dict[str, Any]]:
        """Get family-specific suggestions"""
        suggestions = []

        family_data = context.get("family_data", {})

        # Suggest inviting family members if family is small
        if family_data.get("member_count", 0) < 3:
            suggestions.append(
                {
                    "id": f"invite_suggestion_{user_id}",
                    "type": "family_coordination",
                    "title": "Invite family members",
                    "description": "Add more family members to help plan your trips",
                    "action": "invite_family_members",
                    "priority": 6,
                }
            )

        return suggestions

    async def provide_feedback(
        self,
        interaction_id: str,
        rating: int,
        feedback_text: Optional[str],
        db: Session,
    ) -> bool:
        """Provide feedback on an assistant interaction"""
        try:
            interaction = (
                db.query(AssistantInteraction)
                .filter(AssistantInteraction.id == interaction_id)
                .first()
            )

            if interaction:
                interaction.feedback_rating = rating
                if feedback_text:
                    if not interaction.response_data:
                        interaction.response_data = {}
                    interaction.response_data["feedback"] = feedback_text
                interaction.updated_at = datetime.utcnow()
                db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Error providing feedback: {str(e)}")
            return False


# Global instance
assistant_service = PathfinderAssistantService()
