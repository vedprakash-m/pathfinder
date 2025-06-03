"""
Budget Manager - Tracks and enforces usage limits
Handles multi-tenant budget management with real-time enforcement
"""
import asyncio
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
from core.types import BudgetStatus, LLMBudgetExceededError, LLMConfigurationError
from services.config_manager import get_config_manager

logger = structlog.get_logger(__name__)


@dataclass
class UsageRecord:
    """Represents a usage record for budget tracking"""
    user_id: str
    tenant_id: Optional[str]
    model_id: str
    cost: float
    timestamp: datetime
    request_id: str


class BudgetPeriod:
    """Represents a budget period (daily/monthly)"""
    
    def __init__(self, period_type: str, start_time: datetime):
        self.period_type = period_type  # 'daily' or 'monthly'
        self.start_time = start_time
        
        if period_type == "daily":
            self.end_time = start_time + timedelta(days=1)
        elif period_type == "monthly":
            # Handle month boundaries properly
            next_month = start_time.replace(day=28) + timedelta(days=4)
            self.end_time = next_month.replace(day=1)
        else:
            raise ValueError(f"Unsupported period type: {period_type}")
    
    def is_active(self, timestamp: datetime) -> bool:
        """Check if timestamp falls within this period"""
        return self.start_time <= timestamp < self.end_time
    
    def time_remaining(self, current_time: datetime) -> timedelta:
        """Get time remaining in this period"""
        if current_time >= self.end_time:
            return timedelta(0)
        return self.end_time - current_time


class BudgetTracker:
    """Tracks budget usage for a specific scope (user/tenant/global)"""
    
    def __init__(self, scope_id: str, daily_limit: float, monthly_limit: float):
        self.scope_id = scope_id
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        
        # Usage tracking
        self.usage_records: List[UsageRecord] = []
        self.daily_usage: float = 0.0
        self.monthly_usage: float = 0.0
        
        # Periods
        self.current_daily_period: Optional[BudgetPeriod] = None
        self.current_monthly_period: Optional[BudgetPeriod] = None
        
        # Alerts
        self.alert_thresholds = [80, 95]  # Percentage thresholds
        self.alerts_sent: List[str] = []  # Track sent alerts
        
    def _ensure_periods(self, timestamp: datetime):
        """Ensure current periods are set and valid"""
        # Check daily period
        if (self.current_daily_period is None or 
            not self.current_daily_period.is_active(timestamp)):
            
            # Start new daily period
            day_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            self.current_daily_period = BudgetPeriod("daily", day_start)
            self.daily_usage = 0.0
            self.alerts_sent = [a for a in self.alerts_sent if not a.startswith("daily_")]
            
        # Check monthly period
        if (self.current_monthly_period is None or 
            not self.current_monthly_period.is_active(timestamp)):
            
            # Start new monthly period
            month_start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.current_monthly_period = BudgetPeriod("monthly", month_start)
            self.monthly_usage = 0.0
            self.alerts_sent = [a for a in self.alerts_sent if not a.startswith("monthly_")]
    
    def add_usage(self, record: UsageRecord) -> bool:
        """
        Add usage record and return whether it exceeds budget
        
        Returns:
            bool: True if usage was added successfully, False if budget exceeded
        """
        self._ensure_periods(record.timestamp)
        
        # Check if adding this cost would exceed limits
        new_daily = self.daily_usage + record.cost
        new_monthly = self.monthly_usage + record.cost
        
        if new_daily > self.daily_limit:
            logger.warning(
                "Daily budget would be exceeded",
                scope_id=self.scope_id,
                current=self.daily_usage,
                limit=self.daily_limit,
                requested=record.cost
            )
            return False
        
        if new_monthly > self.monthly_limit:
            logger.warning(
                "Monthly budget would be exceeded",
                scope_id=self.scope_id,
                current=self.monthly_usage,
                limit=self.monthly_limit,
                requested=record.cost
            )
            return False
        
        # Add the usage
        self.usage_records.append(record)
        self.daily_usage = new_daily
        self.monthly_usage = new_monthly
        
        # Check for alert thresholds
        self._check_alerts()
        
        return True
    
    def check_budget_available(self, estimated_cost: float, timestamp: datetime) -> bool:
        """Check if budget is available for estimated cost"""
        self._ensure_periods(timestamp)
        
        return (
            self.daily_usage + estimated_cost <= self.daily_limit and
            self.monthly_usage + estimated_cost <= self.monthly_limit
        )
    
    def get_status(self, timestamp: datetime) -> BudgetStatus:
        """Get current budget status"""
        self._ensure_periods(timestamp)
        
        # Use the more restrictive of daily/monthly limits
        daily_remaining = max(0, self.daily_limit - self.daily_usage)
        monthly_remaining = max(0, self.monthly_limit - self.monthly_usage)
        
        if daily_remaining < monthly_remaining:
            # Daily is more restrictive
            return BudgetStatus(
                current_usage=self.daily_usage,
                limit=self.daily_limit,
                remaining=daily_remaining,
                percentage_used=(self.daily_usage / self.daily_limit) * 100,
                period_start=self.current_daily_period.start_time,
                period_end=self.current_daily_period.end_time
            )
        else:
            # Monthly is more restrictive
            return BudgetStatus(
                current_usage=self.monthly_usage,
                limit=self.monthly_limit,
                remaining=monthly_remaining,
                percentage_used=(self.monthly_usage / self.monthly_limit) * 100,
                period_start=self.current_monthly_period.start_time,
                period_end=self.current_monthly_period.end_time
            )
    
    def _check_alerts(self):
        """Check if any alert thresholds have been crossed"""
        daily_pct = (self.daily_usage / self.daily_limit) * 100
        monthly_pct = (self.monthly_usage / self.monthly_limit) * 100
        
        for threshold in self.alert_thresholds:
            daily_alert_key = f"daily_{threshold}"
            monthly_alert_key = f"monthly_{threshold}"
            
            if daily_pct >= threshold and daily_alert_key not in self.alerts_sent:
                self.alerts_sent.append(daily_alert_key)
                logger.warning(
                    "Daily budget alert threshold reached",
                    scope_id=self.scope_id,
                    threshold=threshold,
                    usage_pct=round(daily_pct, 1)
                )
            
            if monthly_pct >= threshold and monthly_alert_key not in self.alerts_sent:
                self.alerts_sent.append(monthly_alert_key)
                logger.warning(
                    "Monthly budget alert threshold reached",
                    scope_id=self.scope_id,
                    threshold=threshold,
                    usage_pct=round(monthly_pct, 1)
                )


class BudgetManager:
    """
    Centralized budget management for multi-tenant LLM orchestration
    Provides real-time budget enforcement and tracking
    """
    
    def __init__(self):
        self.config_manager = get_config_manager()
        
        # Budget trackers by scope
        self.global_tracker: Optional[BudgetTracker] = None
        self.tenant_trackers: Dict[str, BudgetTracker] = {}
        self.user_trackers: Dict[str, BudgetTracker] = {}
        
        # Configuration cache
        self._budget_config: Dict[str, Any] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize budget manager with configuration"""
        await self._load_budget_config()
        await self._initialize_global_tracker()
        
        logger.info("Budget manager initialized")
    
    async def _load_budget_config(self):
        """Load budget configuration"""
        self._budget_config = await self.config_manager.get_budget_config()
        
    async def _initialize_global_tracker(self):
        """Initialize global budget tracker"""
        global_config = self._budget_config.get("global", {})
        
        self.global_tracker = BudgetTracker(
            scope_id="global",
            daily_limit=global_config.get("daily_limit", 1000.0),
            monthly_limit=global_config.get("monthly_limit", 25000.0)
        )
        
        # Set alert thresholds
        if "alert_thresholds" in global_config:
            self.global_tracker.alert_thresholds = global_config["alert_thresholds"]
    
    async def _get_tenant_tracker(self, tenant_id: str) -> BudgetTracker:
        """Get or create tenant budget tracker"""
        if tenant_id not in self.tenant_trackers:
            # Get tenant-specific config or use defaults
            tenant_config = await self.config_manager.get_budget_config(tenant_id)
            tenant_defaults = tenant_config.get("tenant_defaults", {})
            
            self.tenant_trackers[tenant_id] = BudgetTracker(
                scope_id=f"tenant:{tenant_id}",
                daily_limit=tenant_defaults.get("daily_limit", 50.0),
                monthly_limit=tenant_defaults.get("monthly_limit", 1000.0)
            )
            
            # Set alert thresholds
            if "alert_thresholds" in tenant_defaults:
                self.tenant_trackers[tenant_id].alert_thresholds = tenant_defaults["alert_thresholds"]
        
        return self.tenant_trackers[tenant_id]
    
    async def _get_user_tracker(self, user_id: str) -> BudgetTracker:
        """Get or create user budget tracker"""
        if user_id not in self.user_trackers:
            user_defaults = self._budget_config.get("user_defaults", {})
            
            self.user_trackers[user_id] = BudgetTracker(
                scope_id=f"user:{user_id}",
                daily_limit=user_defaults.get("daily_limit", 10.0),
                monthly_limit=user_defaults.get("monthly_limit", 200.0)
            )
        
        return self.user_trackers[user_id]
    
    async def enforce_budget(
        self,
        user_id: str,
        tenant_id: Optional[str],
        estimated_cost: float,
        model_id: str
    ) -> bool:
        """
        Check if request can proceed within budget limits
        
        Args:
            user_id: User making the request
            tenant_id: Optional tenant ID
            estimated_cost: Estimated cost of the request
            model_id: Model being requested
            
        Returns:
            bool: True if request can proceed, False if budget exceeded
            
        Raises:
            LLMBudgetExceededError: If budget is exceeded
        """
        async with self._lock:
            timestamp = datetime.utcnow()
            
            # Check global budget
            if not self.global_tracker.check_budget_available(estimated_cost, timestamp):
                raise LLMBudgetExceededError(
                    user_id="global",
                    current_usage=self.global_tracker.daily_usage,
                    limit=self.global_tracker.daily_limit
                )
            
            # Check tenant budget if applicable
            if tenant_id:
                tenant_tracker = await self._get_tenant_tracker(tenant_id)
                if not tenant_tracker.check_budget_available(estimated_cost, timestamp):
                    raise LLMBudgetExceededError(
                        user_id=f"tenant:{tenant_id}",
                        current_usage=tenant_tracker.daily_usage,
                        limit=tenant_tracker.daily_limit
                    )
            
            # Check user budget
            user_tracker = await self._get_user_tracker(user_id)
            if not user_tracker.check_budget_available(estimated_cost, timestamp):
                raise LLMBudgetExceededError(
                    user_id=user_id,
                    current_usage=user_tracker.daily_usage,
                    limit=user_tracker.daily_limit
                )
            
            logger.debug(
                "Budget enforcement passed",
                user_id=user_id,
                tenant_id=tenant_id,
                estimated_cost=estimated_cost,
                model_id=model_id
            )
            
            return True
    
    async def record_usage(
        self,
        user_id: str,
        tenant_id: Optional[str],
        model_id: str,
        actual_cost: float,
        request_id: str
    ) -> None:
        """Record actual usage after request completion"""
        async with self._lock:
            timestamp = datetime.utcnow()
            
            # Create usage record
            record = UsageRecord(
                user_id=user_id,
                tenant_id=tenant_id,
                model_id=model_id,
                cost=actual_cost,
                timestamp=timestamp,
                request_id=request_id
            )
            
            # Record in all applicable trackers
            self.global_tracker.add_usage(record)
            
            if tenant_id:
                tenant_tracker = await self._get_tenant_tracker(tenant_id)
                tenant_tracker.add_usage(record)
            
            user_tracker = await self._get_user_tracker(user_id)
            user_tracker.add_usage(record)
            
            logger.info(
                "Usage recorded",
                user_id=user_id,
                tenant_id=tenant_id,
                model_id=model_id,
                cost=actual_cost,
                request_id=request_id
            )
    
    async def get_budget_status(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        scope: str = "user"
    ) -> BudgetStatus:
        """
        Get budget status for specified scope
        
        Args:
            user_id: User ID
            tenant_id: Optional tenant ID
            scope: 'user', 'tenant', or 'global'
            
        Returns:
            BudgetStatus: Current budget status
        """
        timestamp = datetime.utcnow()
        
        if scope == "global":
            return self.global_tracker.get_status(timestamp)
        elif scope == "tenant" and tenant_id:
            tenant_tracker = await self._get_tenant_tracker(tenant_id)
            return tenant_tracker.get_status(timestamp)
        elif scope == "user":
            user_tracker = await self._get_user_tracker(user_id)
            return user_tracker.get_status(timestamp)
        else:
            raise LLMConfigurationError(f"Invalid scope or missing tenant_id: {scope}")
    
    async def get_remaining_budget(self, user_id: str, tenant_id: Optional[str] = None) -> float:
        """Get remaining budget for user (considering all limits)"""
        timestamp = datetime.utcnow()
        
        # Get all applicable budgets
        remaining_amounts = []
        
        # Global budget
        global_status = self.global_tracker.get_status(timestamp)
        remaining_amounts.append(global_status.remaining)
        
        # Tenant budget
        if tenant_id:
            tenant_tracker = await self._get_tenant_tracker(tenant_id)
            tenant_status = tenant_tracker.get_status(timestamp)
            remaining_amounts.append(tenant_status.remaining)
        
        # User budget
        user_tracker = await self._get_user_tracker(user_id)
        user_status = user_tracker.get_status(timestamp)
        remaining_amounts.append(user_status.remaining)
        
        # Return the most restrictive (lowest) remaining budget
        return min(remaining_amounts)
    
    async def get_usage_summary(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get usage summary for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        summary = {
            "period_hours": hours,
            "total_requests": 0,
            "total_cost": 0.0,
            "models_used": {},
            "hourly_breakdown": {}
        }
        
        # Collect usage records from appropriate trackers
        records = []
        
        if user_id:
            user_tracker = await self._get_user_tracker(user_id)
            records.extend([r for r in user_tracker.usage_records if r.timestamp >= cutoff_time])
        elif tenant_id:
            tenant_tracker = await self._get_tenant_tracker(tenant_id)
            records.extend([r for r in tenant_tracker.usage_records if r.timestamp >= cutoff_time])
        else:
            # Global summary
            records.extend([r for r in self.global_tracker.usage_records if r.timestamp >= cutoff_time])
        
        # Process records
        for record in records:
            summary["total_requests"] += 1
            summary["total_cost"] += record.cost
            
            # Model breakdown
            if record.model_id not in summary["models_used"]:
                summary["models_used"][record.model_id] = {"requests": 0, "cost": 0.0}
            summary["models_used"][record.model_id]["requests"] += 1
            summary["models_used"][record.model_id]["cost"] += record.cost
            
            # Hourly breakdown
            hour_key = record.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in summary["hourly_breakdown"]:
                summary["hourly_breakdown"][hour_key] = {"requests": 0, "cost": 0.0}
            summary["hourly_breakdown"][hour_key]["requests"] += 1
            summary["hourly_breakdown"][hour_key]["cost"] += record.cost
        
        return summary
