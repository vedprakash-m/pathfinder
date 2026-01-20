"""
AI Assistant Service

Provides conversational AI assistance for trip planning.
"""
import uuid
from datetime import UTC, datetime
from typing import Optional

from models.documents import MessageDocument, TripDocument
from repositories.cosmos_repository import CosmosRepository
from services.llm.client import LLMClient
from services.llm.prompts import ASSISTANT_SYSTEM_PROMPT, build_assistant_prompt


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class AssistantService:
    """Handles AI assistant conversations."""

    def __init__(self) -> None:
        self._repo: Optional[CosmosRepository] = None
        self._llm: Optional[LLMClient] = None

    @property
    def repo(self) -> CosmosRepository:
        if self._repo is None:
            self._repo = CosmosRepository()
        return self._repo

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    async def send_message(
        self, user_id: str, message: str, trip_id: Optional[str] = None, family_id: Optional[str] = None
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
        await self.repo.initialize()

        # Get trip context if provided
        trip: Optional[TripDocument] = None
        if trip_id:
            trip_dict = await self.repo.get_by_id(trip_id, trip_id)
            if trip_dict and trip_dict.get("entity_type") == "trip":
                trip = TripDocument(**trip_dict)

        # Get conversation history for context
        history = await self._get_conversation_history(user_id=user_id, trip_id=trip_id, limit=10)

        # Build the prompt
        user_prompt = build_assistant_prompt(message=message, trip=trip, conversation_history=history)

        # Get AI response
        response = await self.llm.complete_with_history(
            system_prompt=ASSISTANT_SYSTEM_PROMPT, messages=history + [{"role": "user", "content": user_prompt}]
        )

        # Store user message
        user_msg = MessageDocument(
            id=str(uuid.uuid4()),
            entity_type="message",
            user_id=user_id,
            trip_id=trip_id,
            family_id=family_id,
            content=message,
            message_type="user",
            is_ai_response=False,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        await self.repo.create(user_msg.model_dump(), user_msg.id)

        # Store AI response
        ai_msg = MessageDocument(
            id=str(uuid.uuid4()),
            entity_type="message",
            user_id="assistant",
            trip_id=trip_id,
            family_id=family_id,
            content=response,
            message_type="assistant",
            is_ai_response=True,
            created_at=utc_now(),
            updated_at=utc_now(),
            metadata={"in_reply_to": user_msg.id, "tokens_used": self.llm.tokens_used},
        )
        await self.repo.create(ai_msg.model_dump(), ai_msg.id)

        return ai_msg

    async def get_conversation(
        self, user_id: str, trip_id: Optional[str] = None, limit: int = 50, offset: int = 0
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
        await self.repo.initialize()

        # Build query based on context
        conditions = ["c.entity_type = 'message'", f"(c.user_id = '{user_id}' OR c.user_id = 'assistant')"]

        if trip_id:
            conditions.append(f"c.trip_id = '{trip_id}'")

        query = f"""
            SELECT * FROM c
            WHERE {' AND '.join(conditions)}
            ORDER BY c.created_at DESC
            OFFSET {offset} LIMIT {limit}
        """

        results = await self.repo.query(query)
        return [MessageDocument(**msg) for msg in results]

    async def _get_conversation_history(
        self, user_id: str, trip_id: Optional[str] = None, limit: int = 10
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
            role = "assistant" if msg.is_ai_response else "user"
            history.append({"role": role, "content": msg.content})

        return history

    async def clear_conversation(self, user_id: str, trip_id: Optional[str] = None) -> int:
        """
        Clear conversation history.

        Args:
            user_id: User ID
            trip_id: Optional trip filter

        Returns:
            Number of messages deleted
        """
        await self.repo.initialize()

        conditions = ["c.entity_type = 'message'", f"(c.user_id = '{user_id}' OR c.user_id = 'assistant')"]

        if trip_id:
            conditions.append(f"c.trip_id = '{trip_id}'")

        query = f"SELECT c.id FROM c WHERE {' AND '.join(conditions)}"
        results = await self.repo.query(query)

        deleted = 0
        for msg in results:
            await self.repo.delete(msg["id"], msg["id"])
            deleted += 1

        return deleted


# Service singleton
_assistant_service: Optional[AssistantService] = None


def get_assistant_service() -> AssistantService:
    """Get or create assistant service singleton."""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = AssistantService()
    return _assistant_service
