"""
Audit logging service for tracking security events.

This module implements comprehensive audit logging for security events in the application,
which is a key component of the zero-trust security model.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from fastapi import Request

settings = get_settings()
logger = logging.getLogger("security.audit")


class AuditLog:
    """Audit log record containing security event details."""

    def __init__(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ):
        """Initialize a new audit log entry."""
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        self.event_type = event_type
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.status = status
        self.details = details or {}

        # Extract request metadata if provided
        if request:
            self.ip_address = request.client.host if request.client else "unknown"
            self.user_agent = request.headers.get("User-Agent", "unknown")
            self.path = request.url.path
            self.method = request.method
        else:
            self.ip_address = "unknown"
            self.user_agent = "unknown"
            self.path = None
            self.method = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "status": self.status,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "path": self.path,
            "method": self.method,
            "environment": settings.ENVIRONMENT,
        }

    def to_json(self) -> str:
        """Convert audit log to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Service for logging security audit events."""

    def __init__(self):
        """Initialize the audit logger."""
        self.enable_console = True
        self.enable_db = False  # Will be implemented in future

        # Configure local logging
        if settings.ENVIRONMENT == "production":
            self.enable_db = True

    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> str:
        """Log a security audit event."""
        audit_log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            details=details,
            request=request,
        )

        # Log to console
        if self.enable_console:
            log_message = f"SECURITY_AUDIT: {audit_log.to_json()}"
            if status == "failure":
                logger.warning(log_message)
            else:
                logger.info(log_message)

        # Store in database (future implementation)
        if self.enable_db:
            # This would store the audit log in a database
            # await self._store_in_db(audit_log)
            pass

        return audit_log.event_id

    async def log_auth_event(
        self,
        event: str,
        user_id: Optional[str],
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> str:
        """Log an authentication event."""
        return await self.log_event(
            event_type="auth",
            user_id=user_id,
            action=event,
            status=status,
            details=details,
            request=request,
        )

    async def log_access_event(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> str:
        """Log a resource access event."""
        return await self.log_event(
            event_type="access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            details=details,
            request=request,
        )

    async def log_data_change(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> str:
        """Log a data change event."""
        return await self.log_event(
            event_type="data_change",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details={"before": before, "after": after},
            request=request,
        )

    async def log_security_event(
        self,
        event: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        request: Optional[Request] = None,
    ) -> str:
        """Log a general security event."""
        return await self.log_event(
            event_type="security",
            user_id=user_id,
            action=event,
            status=status,
            details=details,
            request=request,
        )


# Create a global instance of the audit logger
audit_logger = AuditLogger()
