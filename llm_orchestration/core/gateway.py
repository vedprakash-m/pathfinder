"""
LLM Gateway - Main orchestration class for LLM requests
Coordinates all services: routing, budget, caching, analytics
"""
import asyncio
import time
from typing import Optional, Dict, Any
import structlog
from core.types import (
    LLMRequest, LLMResponse, TenantInfo, LLMProvider,
    LLMOrchestrationError, LLMBudgetExceededError, LLMRateLimitError
)
from services.config_manager import ConfigManager
from services.routing_engine import RoutingEngine
from services.budget_manager import BudgetManager
from services.llm_adapters import LLMAdapterFactory
from services.cache_manager import CacheManager
from services.circuit_breaker import CircuitBreakerManager
from services.usage_logger import UsageLogger
from services.cost_estimator import CostEstimator
from services.analytics_collector import AnalyticsCollector

logger = structlog.get_logger(__name__)


class LLMGateway:
    """
    Main LLM Gateway orchestration class
    Handles request routing, budget enforcement, caching, and analytics
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        routing_engine: RoutingEngine,
        budget_manager: BudgetManager,
        cache_manager: CacheManager,
        circuit_breaker: CircuitBreakerManager,
        usage_logger: UsageLogger,
        cost_estimator: CostEstimator,
        analytics_collector: AnalyticsCollector
    ):
        self.config_manager = config_manager
        self.routing_engine = routing_engine
        self.budget_manager = budget_manager
        self.cache_manager = cache_manager
        self.circuit_breaker = circuit_breaker
        self.usage_logger = usage_logger
        self.cost_estimator = cost_estimator
        self.analytics_collector = analytics_collector
        
        # LLM adapter factory for creating provider clients
        self.adapter_factory = LLMAdapterFactory(config_manager)
        
        # Track active requests for analytics
        self.active_requests: Dict[str, float] = {}
    
    async def process_request(
        self,
        request: LLMRequest,
        tenant_info: TenantInfo
    ) -> LLMResponse:
        """
        Main request processing pipeline
        1. Validate tenant and budget
        2. Check cache for existing response
        3. Route to appropriate LLM provider
        4. Process request with circuit breaker
        5. Cache response and log usage
        """
        request_id = request.request_id
        start_time = time.time()
        
        try:
            logger.info(
                "Processing LLM request",
                request_id=request_id,
                tenant_id=tenant_info.tenant_id,
                model_preference=request.model_preference,
                task_type=request.task_type
            )
            
            # Track active request
            self.active_requests[request_id] = start_time
            
            # 1. Validate tenant and check budget
            await self._validate_tenant_budget(request, tenant_info)
            
            # 2. Check cache for existing response
            cached_response = await self._check_cache(request)
            if cached_response:
                logger.info("Cache hit", request_id=request_id)
                await self._log_cache_hit(request, tenant_info, start_time)
                return cached_response
            
            # 3. Route request to appropriate LLM provider
            selected_model = await self.routing_engine.select_model(request, tenant_info)
            
            # 4. Process request with circuit breaker protection
            response = await self._process_with_circuit_breaker(
                request, selected_model, tenant_info
            )
            
            # 5. Cache response and log usage
            await self._post_process_response(request, response, tenant_info, start_time)
            
            logger.info(
                "Request processed successfully",
                request_id=request_id,
                model_used=selected_model.provider.value,
                response_time=time.time() - start_time
            )
            
            return response
            
        except Exception as e:
            await self._handle_request_error(request, tenant_info, e, start_time)
            raise
        finally:
            # Clean up active request tracking
            self.active_requests.pop(request_id, None)
    
    async def _validate_tenant_budget(
        self,
        request: LLMRequest,
        tenant_info: TenantInfo
    ) -> None:
        """Validate tenant exists and has sufficient budget"""
        # Check if tenant is active
        if not tenant_info.is_active:
            raise LLMOrchestrationError(f"Tenant {tenant_info.tenant_id} is not active")
        
        # Check budget constraints
        estimated_cost = await self.cost_estimator.estimate_request_cost(request)
        
        budget_check = await self.budget_manager.check_budget_availability(
            tenant_info.tenant_id,
            request.user_id,
            estimated_cost
        )
        
        if not budget_check.can_proceed:
            raise LLMBudgetExceededError(
                f"Budget exceeded for tenant {tenant_info.tenant_id}: {budget_check.reason}"
            )
    
    async def _check_cache(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Check if response exists in cache"""
        try:
            return await self.cache_manager.get_cached_response(request)
        except Exception as e:
            logger.warning("Cache check failed", error=str(e))
            return None
    
    async def _process_with_circuit_breaker(
        self,
        request: LLMRequest,
        selected_model: Any,  # SelectedModel from routing engine
        tenant_info: TenantInfo
    ) -> LLMResponse:
        """Process request with circuit breaker protection"""
        provider_type = selected_model.provider
        
        # Check circuit breaker state
        if not await self.circuit_breaker.can_execute(provider_type):
            raise LLMOrchestrationError(f"Circuit breaker open for {provider_type.value}")
        
        try:
            # Get LLM adapter for the selected provider
            adapter = await self.adapter_factory.get_adapter(
                provider_type,
                selected_model.model_id
            )
            
            # Execute request
            response = await adapter.process_request(request)
            
            # Record successful execution
            await self.circuit_breaker.record_success(provider_type)
            
            return response
            
        except Exception as e:
            # Record failure in circuit breaker
            await self.circuit_breaker.record_failure(provider_type)
            
            # Try fallback model if available
            fallback_model = await self.routing_engine.get_fallback_model(
                request, tenant_info, failed_provider=provider_type
            )
            
            if fallback_model and fallback_model.provider != provider_type:
                logger.warning(
                    "Primary model failed, trying fallback",
                    request_id=request.request_id,
                    primary_provider=provider_type.value,
                    fallback_provider=fallback_model.provider.value,
                    error=str(e)
                )
                
                return await self._process_with_circuit_breaker(
                    request, fallback_model, tenant_info
                )
            
            raise
    
    async def _post_process_response(
        self,
        request: LLMRequest,
        response: LLMResponse,
        tenant_info: TenantInfo,
        start_time: float
    ) -> None:
        """Cache response and log usage data"""
        processing_time = time.time() - start_time
        
        # Cache response for future requests
        try:
            await self.cache_manager.cache_response(request, response)
        except Exception as e:
            logger.warning("Failed to cache response", error=str(e))
        
        # Calculate actual cost
        actual_cost = await self.cost_estimator.calculate_actual_cost(request, response)
        
        # Record budget usage
        await self.budget_manager.record_usage(
            tenant_info.tenant_id,
            request.user_id,
            actual_cost,
            response.model_used
        )
        
        # Log usage data
        await self.usage_logger.log_request(
            request=request,
            response=response,
            tenant_info=tenant_info,
            processing_time=processing_time,
            cost=actual_cost
        )
        
        # Collect analytics
        await self.analytics_collector.record_request_metrics(
            request=request,
            response=response,
            tenant_info=tenant_info,
            processing_time=processing_time,
            cost=actual_cost
        )
    
    async def _log_cache_hit(
        self,
        request: LLMRequest,
        tenant_info: TenantInfo,
        start_time: float
    ) -> None:
        """Log cache hit for analytics"""
        processing_time = time.time() - start_time
        
        await self.analytics_collector.record_cache_hit(
            request=request,
            tenant_info=tenant_info,
            processing_time=processing_time
        )
    
    async def _handle_request_error(
        self,
        request: LLMRequest,
        tenant_info: TenantInfo,
        error: Exception,
        start_time: float
    ) -> None:
        """Handle and log request errors"""
        processing_time = time.time() - start_time
        
        logger.error(
            "Request processing failed",
            request_id=request.request_id,
            tenant_id=tenant_info.tenant_id,
            error=str(error),
            processing_time=processing_time
        )
        
        # Record error in analytics
        await self.analytics_collector.record_error(
            request=request,
            tenant_info=tenant_info,
            error=error,
            processing_time=processing_time
        )
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        return {
            "active_requests": len(self.active_requests),
            "circuit_breakers": await self.circuit_breaker.get_all_states(),
            "cache_stats": await self.cache_manager.get_stats(),
            "budget_alerts": await self.budget_manager.get_active_alerts(),
            "timestamp": time.time()
        }
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all services"""
        logger.info("Shutting down LLM Gateway")
        
        # Wait for active requests to complete (with timeout)
        if self.active_requests:
            logger.info(f"Waiting for {len(self.active_requests)} active requests")
            await asyncio.sleep(5)  # Grace period
        
        # Shutdown services
        await asyncio.gather(
            self.cache_manager.close(),
            self.usage_logger.close(),
            self.analytics_collector.close(),
            return_exceptions=True
        )
        
        logger.info("LLM Gateway shutdown complete")
