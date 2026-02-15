"""
AI Assistant Service

Provides conversational AI assistance for trip planning.
"""

import logging
from datetime import UTC, datetime

from models.documents import MessageDocument, TripDocument
from repositories.cosmos_repository import cosmos_repo
from services.llm.client import llm_client
from services.llm.prompts import ASSISTANT_SYSTEM_PROMPT, build_assistant_prompt

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class AssistantService:
    """Handles AI assistant conversations."""

    async def send_message(
        self, user_id: str, message: str, trip_id: str | None = None, family_id: str | None = None
    ) -> MessageDocument:
        """
        Send a message to the AI assistant and get a response.

        Args:
            user_id: ID of the user sending the message
            message: User's message text
            trip_id: Optional trip context
            family_id: Optional family context

        Returns:
            MessageDocument containing the AI response
        """
        # Get trip context if provided
        trip: TripDocument | None = None
        if trip_id:
            query = "SELECT * FROM c WHERE c.entity_type = 'trip' AND c.id = @tripId"
            trips = await cosmos_repo.query(
                query=query,
                parameters=[{"name": "@tripId", "value": trip_id}],
                model_class=TripDocument,
                max_items=1,
            )
            trip = trips[0] if trips else None

        # Get conversation history for context
        history = await self._get_conversation_history(user_id=user_id, trip_id=trip_id, limit=10)

        # Build the prompt
        user_prompt = build_assistant_prompt(message=message, trip=trip, conversation_history=history)

        # Get AI response
        response = await llm_client.complete_with_history(
            system_prompt=ASSISTANT_SYSTEM_PROMPT,
            messages=history + [{"role": "user", "content": user_prompt}],
        )

        # Store user message
        user_msg = MessageDocument(
            pk=f"message_{user_id}",
            trip_id=trip_id or "",
            user_id=user_id,
            user_name="User",
            content=message,
            message_type="user",
        )
        await cosmos_repo.create(user_msg)

        # Store AI response
        ai_msg = MessageDocument(
            pk=f"message_{user_id}",
            trip_id=trip_id or "",
            user_id="assistant",
            user_name="Pathfinder Assistant",
            content=response["content"],
            message_type="assistant",
            metadata={"tokens_used": response.get("tokens_used", 0), "cost": response.get("cost", 0.0)},
        )
        created_msg = await cosmos_repo.create(ai_msg)

        return created_msg

    async def get_conversation(
        self, user_id: str, trip_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[MessageDocument]:
        """
        Get conversation history for a user.

        Args:
            user_id: User ID
            trip_id: Optional trip filter
            limit: Maximum messages to return
            offset: Pagination offset

        Returns:
            List of messages
        """
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'message'
            AND (c.user_id = @userId OR c.user_id = 'assistant')
        """
        params = [{"name": "@userId", "value": user_id}]

        if trip_id:
            query += " AND c.trip_id = @tripId"
            params.append({"name": "@tripId", "value": trip_id})

        query += " ORDER BY c.created_at DESC"

        messages = await cosmos_repo.query(query=query, parameters=params, model_class=MessageDocument, max_items=limit)

        return messages[offset:] if offset else messages

    async def _get_conversation_history(
        self, user_id: str, trip_id: str | None = None, limit: int = 10
    ) -> list[dict[str, str]]:
        """
        Get conversation history formatted for LLM context.

        Args:
            user_id: User ID
            trip_id: Optional trip filter
            limit: Maximum messages

        Returns:
            List of message dicts with role and content
        """
        messages = await self.get_conversation(user_id=user_id, trip_id=trip_id, limit=limit)

        # Convert to LLM format (oldest first)
        history: list[dict[str, str]] = []
        for msg in reversed(messages):
            role = "assistant" if msg.message_type == "assistant" else "user"
            history.append({"role": role, "content": msg.content})

        return history

    async def clear_conversation(self, user_id: str, trip_id: str | None = None) -> int:
        """
        Clear conversation history.

        Args:
            user_id: User ID
            trip_id: Optional trip filter

        Returns:
            Number of messages deleted
        """
        query = """
            SELECT c.id, c.pk FROM c
            WHERE c.entity_type = 'message'
            AND (c.user_id = @userId OR c.user_id = 'assistant')
        """
        params = [{"name": "@userId", "value": user_id}]

        if trip_id:
            query += " AND c.trip_id = @tripId"
            params.append({"name": "@tripId", "value": trip_id})

        results = await cosmos_repo.query(query=query, parameters=params)

        deleted = 0
        for msg in results:
            await cosmos_repo.delete(msg["id"], msg["pk"])
            deleted += 1

        return deleted


# Service singleton
_assistant_service: AssistantService | None = None


def get_assistant_service() -> AssistantService:
    """Get or create assistant service singleton."""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = AssistantService()
    return _assistant_service
