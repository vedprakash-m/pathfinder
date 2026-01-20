"""
Realtime Service

Manages Azure SignalR Service integration for real-time messaging.
"""
import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Optional
from urllib.parse import quote

from core.config import get_settings


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class SignalRMessage:
    """Represents a message to send via SignalR."""

    def __init__(
        self, target: str, arguments: list[Any], user_id: Optional[str] = None, group_name: Optional[str] = None
    ) -> None:
        self.target = target
        self.arguments = arguments
        self.user_id = user_id
        self.group_name = group_name


class RealtimeService:
    """Handles Azure SignalR Service integration."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._connection_string = self._settings.SIGNALR_CONNECTION_STRING
        self._hub_name = "pathfinder"

        # Parse connection string
        self._endpoint: Optional[str] = None
        self._access_key: Optional[str] = None
        self._parse_connection_string()

    def _parse_connection_string(self) -> None:
        """Parse SignalR connection string into components."""
        if not self._connection_string:
            return

        parts = self._connection_string.split(";")
        for part in parts:
            if part.startswith("Endpoint="):
                self._endpoint = part[9:].rstrip("/")
            elif part.startswith("AccessKey="):
                self._access_key = part[10:]

    def _generate_access_token(self, audience: str, user_id: Optional[str] = None, ttl_seconds: int = 3600) -> str:
        """
        Generate a JWT access token for SignalR.

        Args:
            audience: Token audience (URL)
            user_id: Optional user ID to embed
            ttl_seconds: Token TTL in seconds

        Returns:
            JWT access token
        """
        if not self._access_key:
            raise ValueError("SignalR access key not configured")

        # Build claims
        now = utc_now()
        expiry = now + timedelta(seconds=ttl_seconds)

        header = {"alg": "HS256", "typ": "JWT"}

        payload = {"aud": audience, "iat": int(now.timestamp()), "exp": int(expiry.timestamp())}

        if user_id:
            payload["nameid"] = user_id

        # Encode
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()

        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()

        message = f"{header_b64}.{payload_b64}"

        # Sign
        signature = hmac.new(self._access_key.encode(), message.encode(), hashlib.sha256).digest()

        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

        return f"{message}.{signature_b64}"

    def get_client_negotiate_response(self, user_id: str) -> dict[str, str]:
        """
        Get negotiate response for client connection.

        Args:
            user_id: User ID for connection

        Returns:
            Dict with url and accessToken for client
        """
        if not self._endpoint:
            raise ValueError("SignalR endpoint not configured")

        # Client endpoint URL
        client_url = f"{self._endpoint}/client/?hub={self._hub_name}"

        # Generate token
        audience = f"{self._endpoint}/client/?hub={self._hub_name}"
        token = self._generate_access_token(audience, user_id)

        return {"url": client_url, "accessToken": token}

    def get_server_endpoint(self, path: str) -> str:
        """Get server API endpoint URL."""
        if not self._endpoint:
            raise ValueError("SignalR endpoint not configured")
        return f"{self._endpoint}/api/v1/hubs/{self._hub_name}/{path}"

    def get_server_headers(self) -> dict[str, str]:
        """Get headers for server-to-SignalR API calls."""
        if not self._endpoint:
            raise ValueError("SignalR endpoint not configured")

        audience = f"{self._endpoint}/api/v1/hubs/{self._hub_name}"
        token = self._generate_access_token(audience)

        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def send_to_user(self, user_id: str, target: str, data: Any) -> bool:
        """
        Send message to a specific user.

        Args:
            user_id: Target user ID
            target: Client method name
            data: Message data

        Returns:
            True if sent successfully
        """
        # In production, this would make an HTTP call to SignalR REST API
        # For now, we log the intent and return True
        # This will be replaced with actual httpx calls

        endpoint = self.get_server_endpoint(f"users/{quote(user_id)}")
        headers = self.get_server_headers()

        payload = {"target": target, "arguments": [data] if not isinstance(data, list) else data}

        # TODO: Make actual HTTP POST request
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(endpoint, json=payload, headers=headers)
        #     return response.status_code == 202

        return True

    async def send_to_group(self, group_name: str, target: str, data: Any) -> bool:
        """
        Send message to a group.

        Args:
            group_name: Target group (e.g., trip ID)
            target: Client method name
            data: Message data

        Returns:
            True if sent successfully
        """
        endpoint = self.get_server_endpoint(f"groups/{quote(group_name)}")
        headers = self.get_server_headers()

        payload = {"target": target, "arguments": [data] if not isinstance(data, list) else data}

        # TODO: Make actual HTTP POST request
        return True

    async def add_user_to_group(self, user_id: str, group_name: str) -> bool:
        """
        Add user to a SignalR group.

        Args:
            user_id: User ID
            group_name: Group name

        Returns:
            True if successful
        """
        endpoint = self.get_server_endpoint(f"groups/{quote(group_name)}/users/{quote(user_id)}")
        headers = self.get_server_headers()

        # TODO: Make actual HTTP PUT request
        return True

    async def remove_user_from_group(self, user_id: str, group_name: str) -> bool:
        """
        Remove user from a SignalR group.

        Args:
            user_id: User ID
            group_name: Group name

        Returns:
            True if successful
        """
        endpoint = self.get_server_endpoint(f"groups/{quote(group_name)}/users/{quote(user_id)}")
        headers = self.get_server_headers()

        # TODO: Make actual HTTP DELETE request
        return True

    async def broadcast(self, target: str, data: Any) -> bool:
        """
        Broadcast message to all connected clients.

        Args:
            target: Client method name
            data: Message data

        Returns:
            True if sent successfully
        """
        endpoint = self.get_server_endpoint("")
        headers = self.get_server_headers()

        payload = {"target": target, "arguments": [data] if not isinstance(data, list) else data}

        # TODO: Make actual HTTP POST request
        return True


# Real-time event types
class RealtimeEvents:
    """Constants for real-time event types."""

    # Trip events
    TRIP_UPDATED = "tripUpdated"
    TRIP_DELETED = "tripDeleted"

    # Collaboration events
    POLL_CREATED = "pollCreated"
    POLL_UPDATED = "pollUpdated"
    POLL_CLOSED = "pollClosed"
    VOTE_RECEIVED = "voteReceived"

    # Chat events
    MESSAGE_RECEIVED = "messageReceived"
    TYPING_INDICATOR = "typingIndicator"

    # Itinerary events
    ITINERARY_GENERATED = "itineraryGenerated"
    ITINERARY_APPROVED = "itineraryApproved"

    # Member events
    MEMBER_JOINED = "memberJoined"
    MEMBER_LEFT = "memberLeft"

    # Notification events
    NOTIFICATION = "notification"


# Service singleton
_realtime_service: Optional[RealtimeService] = None


def get_realtime_service() -> RealtimeService:
    """Get or create realtime service singleton."""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeService()
    return _realtime_service
