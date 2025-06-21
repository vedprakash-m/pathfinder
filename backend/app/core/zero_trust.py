"""
Advanced security service with zero-trust implementation.

This module implements a comprehensive zero-trust security model:
- Context-aware authentication
- Just-in-time access verification
- Continuous validation
- Principle of least privilege
- Audit logging for all security events
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import jwt
from app.core.config import get_settings
from app.core.context_validator import context_validator
from app.core.security import User, verify_token
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError

settings = get_settings()
logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuditLogger:
    """Audit logging functionality for security events."""

    @staticmethod
    async def log_access(
        user_id: str,
        resource: str,
        action: str,
        resource_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict] = None,
    ) -> None:
        """Log access attempts to resources."""
        log_entry = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "resource_id": resource_id,
            "action": action,
            "success": success,
            "details": details or {},
            "ip_address": "0.0.0.0",  # Would be set from request in real implementation
            "user_agent": "Unknown",  # Would be set from request in real implementation
        }

        # In production, we would store this in a database or send to a logging service
        logger.info(f"SECURITY_AUDIT: {json.dumps(log_entry)}")

        # Return log entry for potential further processing
        return log_entry


class ZeroTrustSecurity:
    """Zero-trust security implementation."""

    def __init__(self):
        self.audit_logger = AuditLogger()

    async def verify_access(
        self,
        user: User,
        resource_type: str,
        resource_id: str,
        action: str,
        request: Optional[Request] = None,
    ) -> bool:
        """
        Verify if user has permission to access a resource.

        This implements the core of the zero-trust model by:
        1. Verifying user identity
        2. Checking permissions for the specific resource
        3. Validating the context of the request
        4. Logging the access attempt
        """
        # Log the access attempt first
        await self.audit_logger.log_access(
            user_id=user.id,
            resource=resource_type,
            action=action,
            resource_id=resource_id,
            success=False,  # Default to false, will update if successful
            details={"verification_stage": "started"},
        )

        # 1. Verify permissions based on roles
        has_permission = await self._check_permission(user, resource_type, action)
        if not has_permission:
            logger.warning(
                f"Access denied: User {user.id} lacks permission for {action} on {resource_type}"
            )
            return False

        # 2. Verify resource-specific access
        if resource_id:
            resource_access = await self._check_resource_access(user, resource_type, resource_id)
            if not resource_access:
                logger.warning(
                    f"Access denied: User {user.id} cannot access {resource_type}/{resource_id}"
                )
                return False

        # 3. Context validation is skipped as no request object is provided
        # Will be performed in the require_permissions decorator

        # 4. Record successful access
        await self.audit_logger.log_access(
            user_id=user.id,
            resource=resource_type,
            action=action,
            resource_id=resource_id,
            success=True,
            details={"verification_stage": "completed"},
        )

        return True

    async def _check_permission(self, user: User, resource_type: str, action: str) -> bool:
        """Check if user has permission for the action on the resource type."""
        # Map of resource types to required permissions
        permission_map = {
            "trips": {
                "read": ["read:trips"],
                "create": ["create:trips"],
                "update": ["update:trips"],
                "delete": ["delete:trips"],
            },
            "families": {
                "read": ["read:families"],
                "create": ["create:families"],
                "update": ["update:families"],
                "delete": ["delete:families"],
            },
            "itineraries": {
                "read": ["read:itineraries"],
                "create": ["create:itineraries"],
                "update": ["update:itineraries"],
                "delete": ["delete:itineraries"],
            },
        }

        # Get required permissions for this resource and action
        if resource_type in permission_map and action in permission_map[resource_type]:
            required_permissions = permission_map[resource_type][action]

            # Check if user has any of the required permissions
            for permission in required_permissions:
                if permission in user.permissions:
                    return True

            # Special case: admin role has all permissions
            if "admin" in user.roles:
                return True

        return False

    async def _check_resource_access(
        self, user: User, resource_type: str, resource_id: str
    ) -> bool:
        """
        Check if user has access to the specific resource instance.

        This verifies if the user owns or is a participant in the specific resource.
        """
        from uuid import UUID

        from app.core.database import get_async_session
        from sqlalchemy import select, text
        from sqlalchemy.ext.asyncio import AsyncSession

        async for db in get_async_session():
            try:
                # Resource access checks based on resource type
                if resource_type == "trips":
                    # Check if user is the trip owner or a participant
                    query = text(
                        """
                        SELECT EXISTS(
                            SELECT 1 FROM trips 
                            WHERE id = :trip_id AND owner_id = :user_id
                            UNION
                            SELECT 1 FROM trip_participants 
                            WHERE trip_id = :trip_id AND user_id = :user_id
                        )
                    """
                    )

                    result = await db.execute(query, {"trip_id": resource_id, "user_id": user.id})
                    has_access = result.scalar()

                    if not has_access:
                        await self.audit_logger.log_access(
                            user_id=user.id,
                            resource=resource_type,
                            action="access",
                            resource_id=resource_id,
                            success=False,
                            details={"reason": "not_owner_or_participant"},
                        )
                        return False

                elif resource_type == "families":
                    # Check if user is a family member
                    query = text(
                        """
                        SELECT EXISTS(
                            SELECT 1 FROM families 
                            WHERE id = :family_id AND owner_id = :user_id
                            UNION
                            SELECT 1 FROM family_members 
                            WHERE family_id = :family_id AND user_id = :user_id
                        )
                    """
                    )

                    result = await db.execute(query, {"family_id": resource_id, "user_id": user.id})
                    has_access = result.scalar()

                    if not has_access:
                        await self.audit_logger.log_access(
                            user_id=user.id,
                            resource=resource_type,
                            action="access",
                            resource_id=resource_id,
                            success=False,
                            details={"reason": "not_family_member"},
                        )
                        return False

                elif resource_type == "itineraries":
                    # Check if user owns the trip that contains this itinerary
                    query = text(
                        """
                        SELECT EXISTS(
                            SELECT 1 FROM itineraries i
                            JOIN trips t ON i.trip_id = t.id
                            WHERE i.id = :itinerary_id AND t.owner_id = :user_id
                            UNION
                            SELECT 1 FROM itineraries i
                            JOIN trips t ON i.trip_id = t.id
                            JOIN trip_participants tp ON t.id = tp.trip_id
                            WHERE i.id = :itinerary_id AND tp.user_id = :user_id
                        )
                    """
                    )

                    result = await db.execute(
                        query, {"itinerary_id": resource_id, "user_id": user.id}
                    )
                    has_access = result.scalar()

                    if not has_access:
                        await self.audit_logger.log_access(
                            user_id=user.id,
                            resource=resource_type,
                            action="access",
                            resource_id=resource_id,
                            success=False,
                            details={"reason": "not_authorized_for_itinerary"},
                        )
                        return False
                else:
                    # For other resource types, log a warning
                    logger.warning(
                        f"Resource-specific access check not implemented for {resource_type}/{resource_id}"
                    )
                    # Default to permissive for unsupported resource types for backward compatibility
                    return True

                # If we got here, the user has access
                return True

            except Exception as e:
                logger.error(f"Error checking resource access: {e}")
                # Log the error
                await self.audit_logger.log_access(
                    user_id=user.id,
                    resource=resource_type,
                    action="access",
                    resource_id=resource_id,
                    success=False,
                    details={"error": str(e)},
                )
                return False


# Create a global instance of the security service
zero_trust_security = ZeroTrustSecurity()


def require_permissions(resource_type: str, action: str):
    """Decorator to require zero-trust verified permissions for a resource."""

    async def permission_checker(
        request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        try:
            # Verify token and get user
            token_data = await verify_token(credentials.credentials)
            user = User(
                id=token_data.sub,
                email=token_data.email,
                roles=token_data.roles,
                permissions=token_data.permissions,
            )

            # Extract resource ID from path parameters if available
            resource_id = None
            for param in request.path_params.values():
                if isinstance(param, str) and (
                    param.startswith("trip-")
                    or param.startswith("fam-")
                    or param.startswith("itin-")
                ):
                    resource_id = param
                    break

            # Extract context from request for multi-factor validation
            if settings.ENABLE_CONTEXT_VALIDATION:
                # Extract context from request for validation
                context = await context_validator.extract_context(
                    request, user.id, resource_type, action
                )

                # Validate context (device, location, time patterns)
                validation_result = await context_validator.validate_context(context)

                if not validation_result["is_valid"]:
                    # Log context validation failure
                    await zero_trust_security.audit_logger.log_access(
                        user_id=user.id,
                        resource=resource_type,
                        action=action,
                        resource_id=resource_id,
                        success=False,
                        details={
                            "verification_stage": "context_validation",
                            "risk_score": validation_result["risk_score"],
                            "factors": validation_result["factors"],
                        },
                    )

                    # Determine if user needs additional verification or outright rejection
                    if validation_result["risk_score"] > settings.HIGH_RISK_THRESHOLD:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied due to suspicious activity",
                        )
                    elif validation_result["risk_score"] > settings.MFA_TRIGGER_THRESHOLD:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Additional verification required",
                            headers={"X-Require-MFA": "true"},
                        )

            # Verify access using zero-trust security
            has_access = await zero_trust_security.verify_access(
                user, resource_type, resource_id, action, request
            )

            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {action} on {resource_type}",
                )

            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

    return permission_checker
