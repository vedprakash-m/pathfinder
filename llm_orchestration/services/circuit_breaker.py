"""
Circuit Breaker Manager - Implements circuit breaker pattern for LLM providers
Prevents cascade failures and provides automatic recovery
"""

import asyncio
import time
from enum import Enum
from typing import Any, Dict

import structlog
from core.llm_types import LLMProviderType

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Individual circuit breaker for a specific service/provider
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 3,
        request_timeout: int = 30,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.request_timeout = request_timeout

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0

        # Request tracking
        self.total_requests = 0
        self.total_failures = 0

        self._lock = asyncio.Lock()

    async def can_execute(self) -> bool:
        """Check if requests can be executed through this circuit"""
        async with self._lock:
            current_time = time.time()

            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if current_time - self.last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True

            return False

    async def record_success(self) -> None:
        """Record a successful request"""
        async with self._lock:
            current_time = time.time()
            self.total_requests += 1
            self.last_success_time = current_time

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info("Circuit breaker transitioning to CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def record_failure(self) -> None:
        """Record a failed request"""
        async with self._lock:
            current_time = time.time()
            self.total_requests += 1
            self.total_failures += 1
            self.failure_count += 1
            self.last_failure_time = current_time

            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    logger.warning(
                        "Circuit breaker transitioning to OPEN",
                        failure_count=self.failure_count,
                        threshold=self.failure_threshold,
                    )
                    self.state = CircuitState.OPEN
            elif self.state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker returning to OPEN")
                self.state = CircuitState.OPEN
                self.success_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        failure_rate = 0.0
        if self.total_requests > 0:
            failure_rate = self.total_failures / self.total_requests

        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "failure_rate": failure_rate,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
        }


class CircuitBreakerManager:
    """
    Manages circuit breakers for all LLM providers
    Provides centralized circuit breaker coordination
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize circuit breakers for all providers

        Args:
            config: Configuration with circuit breaker settings per provider
        """
        self.config = config
        self.circuit_breakers: Dict[LLMProviderType, CircuitBreaker] = {}

        # Initialize circuit breakers for each provider
        for provider_type in LLMProviderType:
            provider_config = config.get(provider_type.value, config.get("default", {}))

            self.circuit_breakers[provider_type] = CircuitBreaker(
                failure_threshold=provider_config.get("failure_threshold", 5),
                recovery_timeout=provider_config.get("recovery_timeout", 60),
                success_threshold=provider_config.get("success_threshold", 3),
                request_timeout=provider_config.get("request_timeout", 30),
            )

            logger.info(
                "Circuit breaker initialized",
                provider=provider_type.value,
                failure_threshold=provider_config.get("failure_threshold", 5),
                recovery_timeout=provider_config.get("recovery_timeout", 60),
            )

    async def can_execute(self, provider: LLMProviderType) -> bool:
        """Check if requests can be executed for a provider"""
        if provider not in self.circuit_breakers:
            logger.warning(f"No circuit breaker found for provider {provider.value}")
            return True

        return await self.circuit_breakers[provider].can_execute()

    async def record_success(self, provider: LLMProviderType) -> None:
        """Record successful request for a provider"""
        if provider in self.circuit_breakers:
            await self.circuit_breakers[provider].record_success()

    async def record_failure(self, provider: LLMProviderType) -> None:
        """Record failed request for a provider"""
        if provider in self.circuit_breakers:
            await self.circuit_breakers[provider].record_failure()

    async def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        states = {}

        for provider, circuit_breaker in self.circuit_breakers.items():
            states[provider.value] = circuit_breaker.get_stats()

        return states

    async def force_open(self, provider: LLMProviderType) -> None:
        """Manually open a circuit breaker (for maintenance)"""
        if provider in self.circuit_breakers:
            async with self.circuit_breakers[provider]._lock:
                self.circuit_breakers[provider].state = CircuitState.OPEN
                self.circuit_breakers[provider].last_failure_time = time.time()

            logger.info(f"Circuit breaker manually opened for {provider.value}")

    async def force_close(self, provider: LLMProviderType) -> None:
        """Manually close a circuit breaker (after maintenance)"""
        if provider in self.circuit_breakers:
            async with self.circuit_breakers[provider]._lock:
                self.circuit_breakers[provider].state = CircuitState.CLOSED
                self.circuit_breakers[provider].failure_count = 0
                self.circuit_breakers[provider].success_count = 0

            logger.info(f"Circuit breaker manually closed for {provider.value}")

    async def get_healthy_providers(self) -> list[LLMProviderType]:
        """Get list of providers with closed circuit breakers"""
        healthy_providers = []

        for provider, circuit_breaker in self.circuit_breakers.items():
            if await circuit_breaker.can_execute():
                healthy_providers.append(provider)

        return healthy_providers

    async def get_provider_health_score(self, provider: LLMProviderType) -> float:
        """
        Get health score for a provider (0.0 to 1.0)
        Based on recent success rate and circuit state
        """
        if provider not in self.circuit_breakers:
            return 1.0

        circuit_breaker = self.circuit_breakers[provider]
        stats = circuit_breaker.get_stats()

        # Base score on failure rate
        base_score = 1.0 - stats["failure_rate"]

        # Adjust based on circuit state
        if stats["state"] == CircuitState.OPEN.value:
            return 0.0
        elif stats["state"] == CircuitState.HALF_OPEN.value:
            return base_score * 0.5
        else:  # CLOSED
            return base_score

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all circuit breaker states"""
        total_providers = len(self.circuit_breakers)
        healthy_count = 0
        open_count = 0
        half_open_count = 0

        for circuit_breaker in self.circuit_breakers.values():
            state = circuit_breaker.state
            if state == CircuitState.CLOSED:
                healthy_count += 1
            elif state == CircuitState.OPEN:
                open_count += 1
            elif state == CircuitState.HALF_OPEN:
                half_open_count += 1

        return {
            "total_providers": total_providers,
            "healthy_providers": healthy_count,
            "open_circuits": open_count,
            "half_open_circuits": half_open_count,
            "overall_health": healthy_count / total_providers if total_providers > 0 else 0.0,
        }
