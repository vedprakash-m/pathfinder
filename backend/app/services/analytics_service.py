"""
Analytics Service for Pathfinder
Provides comprehensive tracking of user behavior, feature adoption, and performance metrics
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.cache_service import cache_service
from app.core.config import get_settings
from app.core.logging_config import create_logger

settings = get_settings()
logger = create_logger(__name__)


class EventType(Enum):
    """Analytics event types."""

    USER_ACTION = "user_action"
    FEATURE_USAGE = "feature_usage"
    PERFORMANCE = "performance"
    ERROR = "error"
    BUSINESS_METRIC = "business_metric"
    ONBOARDING_START = "onboarding_start"
    ONBOARDING_COMPLETE = "onboarding_complete"
    ONBOARDING_SKIP = "onboarding_skip"


@dataclass
class AnalyticsEvent:
    """Analytics event data structure."""

    event_type: EventType
    event_name: str
    user_id: Optional[str]
    timestamp: datetime
    properties: Dict[str, Any]
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


class AnalyticsService:
    """Service for collecting and analyzing user behavior analytics."""

    def __init__(self):
        self.events_cache_key = "analytics:events"
        self.metrics_cache_key = "analytics:metrics"
        self.user_sessions_key = "analytics:user_sessions"

    async def track_event(
        self,
        event_type: EventType,
        event_name: str,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Track an analytics event."""

        try:
            event = AnalyticsEvent(
                event_type=event_type,
                event_name=event_name,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                properties=properties or {},
                session_id=session_id,
                request_id=request_id,
            )

            # Store event in cache for processing
            await self._store_event(event)

            # Update real-time metrics
            await self._update_real_time_metrics(event)

            logger.info(
                f"Analytics event tracked: {event_name}",
                user_id=user_id,
                event_type=event_type.value,
            )

        except Exception as e:
            logger.error(f"Failed to track analytics event: {e}")

    async def track_user_action(
        self,
        action: str,
        user_id: str,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Track a user action event."""
        await self.track_event(
            event_type=EventType.USER_ACTION,
            event_name=action,
            user_id=user_id,
            properties=properties,
            session_id=session_id,
        )

    async def track_feature_usage(
        self,
        feature: str,
        user_id: str,
        usage_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Track feature usage for adoption analysis."""
        await self.track_event(
            event_type=EventType.FEATURE_USAGE,
            event_name=f"feature_used_{feature}",
            user_id=user_id,
            properties={"feature": feature, **(usage_context or {})},
            session_id=session_id,
        )

    async def track_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        properties: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Track performance metrics."""
        await self.track_event(
            event_type=EventType.PERFORMANCE,
            event_name=metric_name,
            properties={"value": value, "unit": unit, **(properties or {})},
            request_id=request_id,
        )

    async def track_business_metric(
        self,
        metric: str,
        value: Any,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track business metrics like trip completion, cost savings, etc."""
        await self.track_event(
            event_type=EventType.BUSINESS_METRIC,
            event_name=metric,
            user_id=user_id,
            properties={"value": value, **(properties or {})},
        )

    async def get_user_analytics(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get analytics data for a specific user."""

        try:
            events = await self._get_user_events(user_id, hours)

            # Analyze user behavior
            action_counts = {}
            feature_usage = {}
            session_data = {}

            for event in events:
                if event["event_type"] == EventType.USER_ACTION.value:
                    action_counts[event["event_name"]] = (
                        action_counts.get(event["event_name"], 0) + 1
                    )

                elif event["event_type"] == EventType.FEATURE_USAGE.value:
                    feature = event["properties"].get("feature")
                    if feature:
                        feature_usage[feature] = feature_usage.get(feature, 0) + 1

                # Track session activity
                session_id = event.get("session_id")
                if session_id:
                    if session_id not in session_data:
                        session_data[session_id] = {
                            "start_time": event["timestamp"],
                            "end_time": event["timestamp"],
                            "event_count": 0,
                        }
                    session_data[session_id]["end_time"] = event["timestamp"]
                    session_data[session_id]["event_count"] += 1

            return {
                "user_id": user_id,
                "time_period_hours": hours,
                "total_events": len(events),
                "action_counts": action_counts,
                "feature_usage": feature_usage,
                "sessions": len(session_data),
                "session_details": session_data,
            }

        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {"error": str(e)}

    async def get_feature_adoption_metrics(
        self,
        hours: int = 168,  # 1 week default
    ) -> Dict[str, Any]:
        """Get feature adoption metrics across all users."""

        try:
            events = await self._get_events_by_type(EventType.FEATURE_USAGE, hours)

            feature_stats = {}
            unique_users = set()

            for event in events:
                feature = event["properties"].get("feature")
                if feature:
                    if feature not in feature_stats:
                        feature_stats[feature] = {
                            "usage_count": 0,
                            "unique_users": set(),
                        }

                    feature_stats[feature]["usage_count"] += 1
                    if event["user_id"]:
                        feature_stats[feature]["unique_users"].add(event["user_id"])
                        unique_users.add(event["user_id"])

            # Convert sets to counts and calculate adoption rates
            total_unique_users = len(unique_users)
            adoption_metrics = {}

            for feature, stats in feature_stats.items():
                unique_user_count = len(stats["unique_users"])
                adoption_metrics[feature] = {
                    "usage_count": stats["usage_count"],
                    "unique_users": unique_user_count,
                    "adoption_rate": (
                        unique_user_count / total_unique_users if total_unique_users > 0 else 0
                    ),
                }

            return {
                "time_period_hours": hours,
                "total_unique_users": total_unique_users,
                "features": adoption_metrics,
            }

        except Exception as e:
            logger.error(f"Failed to get feature adoption metrics: {e}")
            return {"error": str(e)}

    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics summary."""

        try:
            events = await self._get_events_by_type(EventType.PERFORMANCE, hours)

            metrics = {}

            for event in events:
                metric_name = event["event_name"]
                value = event["properties"].get("value")
                unit = event["properties"].get("unit", "ms")

                if metric_name not in metrics:
                    metrics[metric_name] = {"values": [], "unit": unit, "count": 0}

                metrics[metric_name]["values"].append(value)
                metrics[metric_name]["count"] += 1

            # Calculate statistics
            performance_summary = {}
            for metric_name, data in metrics.items():
                values = data["values"]
                if values:
                    performance_summary[metric_name] = {
                        "count": len(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "unit": data["unit"],
                        "p95": self._calculate_percentile(values, 95),
                        "p99": self._calculate_percentile(values, 99),
                    }

            return {
                "time_period_hours": hours,
                "metrics": performance_summary,
                "summary": {
                    "total_measurements": sum(m["count"] for m in performance_summary.values()),
                    "avg_response_time": performance_summary.get("api_response_time", {}).get(
                        "avg", 0
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}

    async def get_business_metrics(
        self,
        hours: int = 168,  # 1 week default
    ) -> Dict[str, Any]:
        """Get business metrics like trip completion rates, user satisfaction, etc."""

        try:
            events = await self._get_events_by_type(EventType.BUSINESS_METRIC, hours)

            metrics = {}

            for event in events:
                metric_name = event["event_name"]
                value = event["properties"].get("value")

                if metric_name not in metrics:
                    metrics[metric_name] = []

                metrics[metric_name].append(
                    {
                        "value": value,
                        "timestamp": event["timestamp"],
                        "user_id": event["user_id"],
                        "properties": event["properties"],
                    }
                )

            # Calculate business KPIs
            business_summary = {}

            # Trip completion rate
            if "trip_completed" in metrics and "trip_started" in metrics:
                completed_trips = len(metrics["trip_completed"])
                started_trips = len(metrics["trip_started"])
                business_summary["trip_completion_rate"] = (
                    completed_trips / started_trips if started_trips > 0 else 0
                )

            # User satisfaction scores
            if "user_satisfaction" in metrics:
                satisfaction_scores = [
                    m["value"]
                    for m in metrics["user_satisfaction"]
                    if isinstance(m["value"], (int, float))
                ]
                if satisfaction_scores:
                    business_summary["avg_satisfaction"] = sum(satisfaction_scores) / len(
                        satisfaction_scores
                    )
                    business_summary["satisfaction_responses"] = len(satisfaction_scores)

            # Time saved metrics
            if "time_saved_hours" in metrics:
                time_saved_values = [
                    m["value"]
                    for m in metrics["time_saved_hours"]
                    if isinstance(m["value"], (int, float))
                ]
                if time_saved_values:
                    business_summary["total_time_saved_hours"] = sum(time_saved_values)
                    business_summary["avg_time_saved_per_trip"] = sum(time_saved_values) / len(
                        time_saved_values
                    )

            return {
                "time_period_hours": hours,
                "raw_metrics": metrics,
                "business_summary": business_summary,
            }

        except Exception as e:
            logger.error(f"Failed to get business metrics: {e}")
            return {"error": str(e)}

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (percentile / 100.0) * (len(sorted_values) - 1)

        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index % 1)

    async def _store_event(self, event: AnalyticsEvent) -> None:
        """Store event in cache for processing."""
        try:
            # Store in daily cache buckets for efficient querying
            date_key = event.timestamp.strftime("%Y-%m-%d")
            cache_key = f"{self.events_cache_key}:{date_key}"

            # Get existing events for the day
            existing_events = await cache_service.get(cache_key) or []
            if isinstance(existing_events, str):
                existing_events = json.loads(existing_events)

            # Add new event
            existing_events.append(event.to_dict())

            # Store back with 7-day TTL
            await cache_service.set(cache_key, json.dumps(existing_events), ttl=7 * 24 * 3600)

        except Exception as e:
            logger.error(f"Failed to store analytics event: {e}")

    async def _update_real_time_metrics(self, event: AnalyticsEvent) -> None:
        """Update real-time metrics cache."""
        try:
            # Update metrics counters
            metrics_key = f"{self.metrics_cache_key}:realtime"
            metrics = await cache_service.get(metrics_key) or {}
            if isinstance(metrics, str):
                metrics = json.loads(metrics)

            # Initialize if needed
            if "event_counts" not in metrics:
                metrics["event_counts"] = {}
            if "last_updated" not in metrics:
                metrics["last_updated"] = datetime.utcnow().isoformat()

            # Update counters
            event_key = f"{event.event_type.value}:{event.event_name}"
            metrics["event_counts"][event_key] = metrics["event_counts"].get(event_key, 0) + 1
            metrics["last_updated"] = datetime.utcnow().isoformat()

            # Store with 1-hour TTL
            await cache_service.set(metrics_key, json.dumps(metrics), ttl=3600)

        except Exception as e:
            logger.error(f"Failed to update real-time metrics: {e}")

    async def _get_user_events(self, user_id: str, hours: int) -> List[Dict[str, Any]]:
        """Get events for a specific user within time range."""
        events = []

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours)

        # Query each day in range
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_key = current_date.strftime("%Y-%m-%d")
            cache_key = f"{self.events_cache_key}:{date_key}"

            day_events = await cache_service.get(cache_key) or []
            if isinstance(day_events, str):
                day_events = json.loads(day_events)

            # Filter by user and time range
            for event in day_events:
                if (
                    event.get("user_id") == user_id
                    and start_date <= datetime.fromisoformat(event["timestamp"]) <= end_date
                ):
                    events.append(event)

            current_date += timedelta(days=1)

        return events

    async def _get_events_by_type(self, event_type: EventType, hours: int) -> List[Dict[str, Any]]:
        """Get events of a specific type within time range."""
        events = []

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours)

        # Query each day in range
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_key = current_date.strftime("%Y-%m-%d")
            cache_key = f"{self.events_cache_key}:{date_key}"

            day_events = await cache_service.get(cache_key) or []
            if isinstance(day_events, str):
                day_events = json.loads(day_events)

            # Filter by event type and time range
            for event in day_events:
                if (
                    event.get("event_type") == event_type.value
                    and start_date <= datetime.fromisoformat(event["timestamp"]) <= end_date
                ):
                    events.append(event)

            current_date += timedelta(days=1)

        return events


# Global analytics service instance
analytics_service = AnalyticsService()


async def get_analytics_service() -> AnalyticsService:
    """Dependency injection for analytics service."""
    return analytics_service
