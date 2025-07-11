"""
Multi-factor context validation for zero-trust security.

This module provides context-based validation for the zero-trust security model:
- Device fingerprinting
- Location-based validation
- Time-based access patterns
- Behavioral analytics
"""

import ipaddress
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from app.core.config import get_settings
from fastapi import Request
from pydantic import BaseModel

settings = get_settings()
logger = logging.getLogger(__name__)


class AccessContext(BaseModel):
    """Access context model."""

    user_id: str
    ip_address: str
    user_agent: str
    device_fingerprint: Optional[str] = None
    request_time: datetime
    geo_location: Optional[Dict] = None
    resource_type: str
    action: str


class ContextValidator:
    """Multi-factor context validation for zero-trust security."""

    def __init__(self):
        # Load trusted locations (IPs, ranges, countries)
        self.trusted_locations = settings.TRUSTED_LOCATIONS
        self.trusted_networks = [
            ipaddress.ip_network(network) for network in settings.TRUSTED_NETWORKS
        ]

        # Load working hours configuration
        self.working_hours = {
            "start": settings.WORKING_HOURS_START,  # e.g. 8 (8 AM)
            "end": settings.WORKING_HOURS_END,  # e.g. 18 (6 PM)
            "timezone": settings.WORKING_HOURS_TIMEZONE,
        }

        # Initialize user access patterns storage
        self.user_patterns = {}

        # Try to load persisted user patterns
        try:
            with open(settings.USER_PATTERNS_FILE, "r") as f:
                self.user_patterns = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Could not load user access patterns file. Starting fresh.")

    async def extract_context(
        self, request: Request, user_id: str, resource_type: str, action: str
    ) -> AccessContext:
        """Extract context information from a request."""
        # Get basic request information
        ip = request.client.host if request.client else "0.0.0.0"
        user_agent = request.headers.get("User-Agent", "Unknown")
        device_fp = request.headers.get("X-Device-Fingerprint")

        # Get geo information (would come from a real geo-IP service)
        geo = None

        # Get current time in UTC
        now = datetime.now(timezone.utc)

        return AccessContext(
            user_id=user_id,
            ip_address=ip,
            user_agent=user_agent,
            device_fingerprint=device_fp,
            request_time=now,
            geo_location=geo,
            resource_type=resource_type,
            action=action,
        )

    async def validate_context(self, context: AccessContext) -> Dict:
        """
        Validate the access context for suspicious activity.

        Returns a dict with validation results and risk score.
        """
        # Initialize validation results
        results = {
            "is_valid": True,
            "risk_score": 0.0,  # 0.0 to 1.0 (higher is riskier)
            "factors": {},
        }

        # 1. Network location validation
        network_score = await self._validate_network(context.ip_address)
        results["factors"]["network"] = {
            "score": network_score,
            "is_valid": network_score < 0.7,
        }
        results["risk_score"] += network_score * 0.3  # 30% weight

        # 2. Time-based validation
        time_score = await self._validate_time(context.request_time)
        results["factors"]["time"] = {"score": time_score, "is_valid": time_score < 0.8}
        results["risk_score"] += time_score * 0.2  # 20% weight

        # 3. Device validation
        device_score = await self._validate_device(
            context.user_id, context.device_fingerprint
        )
        results["factors"]["device"] = {
            "score": device_score,
            "is_valid": device_score < 0.7,
        }
        results["risk_score"] += device_score * 0.3  # 30% weight

        # 4. Behavioral patterns
        behavior_score = await self._validate_behavior(context)
        results["factors"]["behavior"] = {
            "score": behavior_score,
            "is_valid": behavior_score < 0.8,
        }
        results["risk_score"] += behavior_score * 0.2  # 20% weight

        # Update the overall validity
        results["is_valid"] = results["risk_score"] < settings.MAX_RISK_THRESHOLD

        # Record this access for future pattern analysis
        await self._record_access_pattern(context)

        return results

    async def _validate_network(self, ip_address: str) -> float:
        """Validate the network location."""
        try:
            ip = ipaddress.ip_address(ip_address)

            # Check if IP is in trusted networks
            for network in self.trusted_networks:
                if ip in network:
                    return 0.0  # No risk for trusted networks

            # For demo, return medium risk for unknown networks
            # In prod, would check against threat intelligence feeds
            return 0.5

        except ValueError:
            logger.warning(f"Invalid IP address: {ip_address}")
            return 0.9  # High risk for invalid IPs

    async def _validate_time(self, request_time: datetime) -> float:
        """Validate the access time against working hours."""
        # Convert to configured timezone
        hour = request_time.hour

        # Check if within working hours
        if self.working_hours["start"] <= hour <= self.working_hours["end"]:
            return 0.1  # Low risk during working hours
        elif (
            hour < self.working_hours["start"] - 2
            or hour > self.working_hours["end"] + 2
        ):
            return 0.8  # Higher risk for very unusual hours
        else:
            return 0.4  # Medium risk for slightly outside hours

    async def _validate_device(
        self, user_id: str, device_fingerprint: Optional[str]
    ) -> float:
        """Validate the device fingerprint."""
        if not device_fingerprint:
            return 0.7  # Higher risk when no fingerprint provided

        # Check if user has known devices
        user_key = f"user:{user_id}:devices"
        if (
            user_key in self.user_patterns
            and device_fingerprint in self.user_patterns[user_key]
        ):
            return 0.1  # Low risk for known devices

        return 0.6  # Medium-high risk for new devices

    async def _validate_behavior(self, context: AccessContext) -> float:
        """
        Validate user behavior patterns.

        This checks if the current access follows historical patterns.
        """
        # This would be a more complex behavioral analysis in production
        # For now, use a simple resource access pattern
        user_key = f"user:{context.user_id}:resources"

        if user_key not in self.user_patterns:
            return 0.5  # Medium risk for new users

        # Check if user commonly accesses this resource type
        resource_accesses = self.user_patterns[user_key].get(context.resource_type, 0)
        if resource_accesses > 10:
            return 0.1  # Low risk for frequently accessed resources
        elif resource_accesses > 3:
            return 0.3  # Lower risk for somewhat familiar resources

        return 0.6  # Higher risk for rarely accessed resources

    async def _record_access_pattern(self, context: AccessContext) -> None:
        """Record the access pattern for future validation."""
        # Record device usage
        device_key = f"user:{context.user_id}:devices"
        if context.device_fingerprint:
            if device_key not in self.user_patterns:
                self.user_patterns[device_key] = []
            if context.device_fingerprint not in self.user_patterns[device_key]:
                self.user_patterns[device_key].append(context.device_fingerprint)

        # Record resource access
        resource_key = f"user:{context.user_id}:resources"
        if resource_key not in self.user_patterns:
            self.user_patterns[resource_key] = {}
        if context.resource_type not in self.user_patterns[resource_key]:
            self.user_patterns[resource_key][context.resource_type] = 0

        self.user_patterns[resource_key][context.resource_type] += 1

        # Save patterns periodically (in production would use Redis/database)
        # This is a simplified approach for the example
        try:
            with open(settings.USER_PATTERNS_FILE, "w") as f:
                json.dump(self.user_patterns, f)
        except Exception as e:
            logger.error(f"Failed to save user patterns: {e}")


# Create global instance
context_validator = ContextValidator()
