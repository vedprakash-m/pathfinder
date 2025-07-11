"""
Cost monitoring service for tracking AI and infrastructure usage.
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.logging_config import get_logger
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


@dataclass
class CostAlert:
    """Cost alert data structure."""

    service: str
    usage_percentage: float
    threshold: float
    current_usage: float
    limit: float
    timestamp: datetime
    severity: str


class CostMonitoringService:
    """Real-time cost monitoring and alerts service."""

    def __init__(self, notification_service: Optional[NotificationService] = None):
        self.cost_thresholds = {
            "cosmos_db_ru_daily": float(
                os.getenv("COSMOS_DB_RU_DAILY_LIMIT", "100000")
            ),
            "openai_tokens_daily": float(
                os.getenv("OPENAI_TOKENS_DAILY_LIMIT", "1000000")
            ),
            "storage_gb_monthly": float(os.getenv("STORAGE_GB_MONTHLY_LIMIT", "100")),
            "bandwidth_gb_monthly": float(
                os.getenv("BANDWIDTH_GB_MONTHLY_LIMIT", "500")
            ),
            "ai_cost_daily": float(os.getenv("AI_COST_DAILY_LIMIT", "50.0")),
        }
        self.current_usage = {}
        self.notification_service = notification_service

    async def track_cost(self, service: str, usage: float, unit: str) -> None:
        """Track usage and check against thresholds."""
        key = f"{service}_{unit}"

        if key not in self.current_usage:
            self.current_usage[key] = 0

        self.current_usage[key] += usage

        # Check threshold
        if key in self.cost_thresholds:
            threshold = self.cost_thresholds[key]
            usage_percentage = (self.current_usage[key] / threshold) * 100

            # Send alerts at 80% and 95% thresholds
            if usage_percentage > 80:
                await self.send_cost_alert(service, usage_percentage, threshold)

        logger.info(
            f"Cost tracked for {service}",
            service=service,
            usage=usage,
            unit=unit,
            total_usage=self.current_usage.get(key, 0),
            threshold=self.cost_thresholds.get(key, 0),
        )

    async def send_cost_alert(
        self, service: str, percentage: float, threshold: float
    ) -> None:
        """Send cost alerts to administrators."""
        # Only send alerts if notification service is available
        if not self.notification_service:
            logger.warning(
                f"Cost alert triggered but notification service not available: {service} at {percentage:.1f}%"
            )
            return

        severity = "high" if percentage > 95 else "medium"

        alert = CostAlert(
            service=service,
            usage_percentage=percentage,
            threshold=threshold,
            current_usage=self.current_usage.get(f"{service}_daily", 0),
            limit=threshold,
            timestamp=datetime.now(timezone.utc),
            severity=severity,
        )

        alert_message = {
            "type": "cost_alert",
            "service": alert.service,
            "usage_percentage": alert.usage_percentage,
            "threshold": alert.threshold,
            "current_usage": alert.current_usage,
            "limit": alert.limit,
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity,
            "message": f"Cost alert for {service}: {percentage:.1f}% of daily limit reached",
        }

        # Send to monitoring system and administrators
        await self.notification_service.send_admin_alert(alert_message)

        logger.warning(
            f"Cost alert sent for {service}",
            service=service,
            usage_percentage=percentage,
            severity=severity,
        )

    async def get_cost_summary(self) -> Dict[str, Any]:
        """Get current cost usage summary."""
        summary = {}

        for key, threshold in self.cost_thresholds.items():
            current = self.current_usage.get(key, 0)
            percentage = (current / threshold) * 100 if threshold > 0 else 0

            summary[key] = {
                "current_usage": current,
                "threshold": threshold,
                "percentage": percentage,
                "status": self._get_status(percentage),
            }

        return summary

    def _get_status(self, percentage: float) -> str:
        """Get status based on usage percentage."""
        if percentage >= 95:
            return "critical"
        elif percentage >= 80:
            return "warning"
        elif percentage >= 60:
            return "caution"
        else:
            return "normal"

    async def reset_daily_usage(self) -> None:
        """Reset daily usage counters (called by scheduler)."""
        daily_keys = [key for key in self.current_usage.keys() if "daily" in key]
        for key in daily_keys:
            self.current_usage[key] = 0

        logger.info("Daily usage counters reset")

    async def reset_monthly_usage(self) -> None:
        """Reset monthly usage counters (called by scheduler)."""
        monthly_keys = [key for key in self.current_usage.keys() if "monthly" in key]
        for key in monthly_keys:
            self.current_usage[key] = 0

        logger.info("Monthly usage counters reset")


class AIModelSelector:
    """Dynamic AI model selection based on cost and quality requirements."""

    MODEL_CONFIGS = {
        "gpt-4o": {
            "cost_per_1k_tokens": {"input": 0.005, "output": 0.015},
            "quality_score": 95,
            "max_tokens": 128000,
            "best_for": ["complex_reasoning", "detailed_planning"],
        },
        "gpt-4o-mini": {
            "cost_per_1k_tokens": {"input": 0.00015, "output": 0.0006},
            "quality_score": 85,
            "max_tokens": 128000,
            "best_for": ["general_tasks", "cost_optimization"],
        },
        "gpt-3.5-turbo": {
            "cost_per_1k_tokens": {"input": 0.0015, "output": 0.002},
            "quality_score": 75,
            "max_tokens": 16385,
            "best_for": ["simple_tasks", "budget_conscious"],
        },
    }

    def __init__(self, cost_monitor: CostMonitoringService):
        self.cost_monitor = cost_monitor

    async def select_model(
        self,
        task_type: str,
        quality_requirement: str = "balanced",
        budget_priority: bool = False,
    ) -> str:
        """Select the best model based on requirements and current budget."""

        # Get current cost status
        cost_summary = await self.cost_monitor.get_cost_summary()
        ai_cost_status = cost_summary.get("ai_cost_daily", {})
        current_percentage = ai_cost_status.get("percentage", 0)

        # Force budget model if we're over 80% of daily budget
        if current_percentage > 80 or budget_priority:
            return "gpt-4o-mini"

        # Select based on quality requirement and task type
        if quality_requirement == "high" and task_type in [
            "complex_reasoning",
            "detailed_planning",
        ]:
            return "gpt-4o"
        elif quality_requirement == "medium" or current_percentage > 60:
            return "gpt-4o-mini"
        elif quality_requirement == "low" or current_percentage > 40:
            return "gpt-3.5-turbo"
        else:
            # Default to balanced choice
            return "gpt-4o-mini"

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model."""
        return self.MODEL_CONFIGS.get(model_name, {})

    def calculate_estimated_cost(self, model_name: str, estimated_tokens: int) -> float:
        """Calculate estimated cost for a given model and token count."""
        model_config = self.MODEL_CONFIGS.get(model_name, {})
        if not model_config:
            return 0.0

        # Assume 70% input, 30% output token distribution
        input_tokens = int(estimated_tokens * 0.7)
        output_tokens = int(estimated_tokens * 0.3)

        costs = model_config["cost_per_1k_tokens"]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]

        return input_cost + output_cost


# Global instances
cost_monitoring_service = CostMonitoringService()
ai_model_selector = AIModelSelector(cost_monitoring_service)
