"""
Cost Estimator - Calculates and estimates costs for LLM requests
Supports multiple pricing models and real-time cost tracking
"""
from typing import Dict, Any, Optional
import structlog
from core.types import LLMRequest, LLMResponse, LLMProviderType, TaskType

logger = structlog.get_logger(__name__)


class CostEstimator:
    """
    Estimates and calculates costs for LLM requests across different providers
    Maintains up-to-date pricing information and billing models
    """
    
    def __init__(self, pricing_config: Dict[str, Any]):
        """
        Initialize with pricing configuration
        
        Args:
            pricing_config: Configuration containing pricing info per provider/model
        """
        self.pricing_config = pricing_config
        
        # Default pricing fallbacks (in USD per 1K tokens)
        self.default_pricing = {
            LLMProviderType.OPENAI: {
                "input_token_cost": 0.0015,
                "output_token_cost": 0.002,
            },
            LLMProviderType.GEMINI: {
                "input_token_cost": 0.0005,
                "output_token_cost": 0.0015,
            },
            LLMProviderType.CLAUDE: {
                "input_token_cost": 0.008,
                "output_token_cost": 0.024,
            },
            LLMProviderType.COHERE: {
                "input_token_cost": 0.0015,
                "output_token_cost": 0.002,
            }
        }
        
        # Cache for calculated costs
        self.cost_cache: Dict[str, float] = {}
    
    async def estimate_request_cost(self, request: LLMRequest) -> float:
        """
        Estimate cost for a request before processing
        Based on prompt length and expected response size
        """
        try:
            # Estimate input tokens from prompt
            estimated_input_tokens = self._estimate_tokens(request.prompt)
            
            # Estimate output tokens based on task type and max_tokens
            estimated_output_tokens = self._estimate_output_tokens(request)
            
            # Get pricing for preferred provider or default
            provider = request.model_preference or LLMProviderType.OPENAI
            pricing = self._get_provider_pricing(provider, request.model_id)
            
            # Calculate estimated cost
            input_cost = (estimated_input_tokens / 1000) * pricing["input_token_cost"]
            output_cost = (estimated_output_tokens / 1000) * pricing["output_token_cost"]
            
            total_cost = input_cost + output_cost
            
            logger.debug(
                "Cost estimated",
                request_id=request.request_id,
                provider=provider.value,
                estimated_input_tokens=estimated_input_tokens,
                estimated_output_tokens=estimated_output_tokens,
                estimated_cost=total_cost
            )
            
            return total_cost
            
        except Exception as e:
            logger.warning("Cost estimation failed", request_id=request.request_id, error=str(e))
            return 0.01  # Default fallback cost
    
    async def calculate_actual_cost(
        self,
        request: LLMRequest,
        response: LLMResponse
    ) -> float:
        """
        Calculate actual cost after processing
        Based on real token usage from the response
        """
        try:
            if not response.usage:
                # Fallback to estimation if usage not available
                return await self.estimate_request_cost(request)
            
            # Get actual token usage
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
            # Get pricing for the provider that was actually used
            provider = LLMProviderType(response.provider)
            pricing = self._get_provider_pricing(provider, response.model_used)
            
            # Calculate actual cost
            input_cost = (prompt_tokens / 1000) * pricing["input_token_cost"]
            output_cost = (completion_tokens / 1000) * pricing["output_token_cost"]
            
            total_cost = input_cost + output_cost
            
            logger.debug(
                "Actual cost calculated",
                request_id=request.request_id,
                provider=provider.value,
                model=response.model_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                actual_cost=total_cost
            )
            
            return total_cost
            
        except Exception as e:
            logger.warning(
                "Actual cost calculation failed",
                request_id=request.request_id,
                error=str(e)
            )
            return await self.estimate_request_cost(request)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text
        Uses approximation: ~4 characters per token for English text
        """
        if not text:
            return 0
        
        # Basic estimation: 4 chars per token (rough approximation)
        # In production, you'd use tiktoken or similar for accurate counting
        estimated_tokens = len(text) // 4
        
        # Add some overhead for formatting and special tokens
        return int(estimated_tokens * 1.1)
    
    def _estimate_output_tokens(self, request: LLMRequest) -> int:
        """
        Estimate output token count based on request parameters and task type
        """
        # Check if max_tokens is specified in parameters
        if request.parameters and hasattr(request.parameters, 'max_tokens'):
            max_tokens = request.parameters.max_tokens
            if max_tokens:
                return min(max_tokens, 4000)  # Cap at reasonable limit
        
        # Estimate based on task type
        task_type_estimates = {
            TaskType.QUESTION_ANSWERING: 150,
            TaskType.TRANSLATION: 200,
            TaskType.SUMMARIZATION: 300,
            TaskType.CODE_GENERATION: 500,
            TaskType.CREATIVE_WRITING: 800,
            TaskType.CONVERSATION: 200,
            TaskType.ANALYSIS: 400,
            TaskType.OTHER: 300
        }
        
        return task_type_estimates.get(request.task_type, 300)
    
    def _get_provider_pricing(
        self,
        provider: LLMProviderType,
        model_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get pricing information for a specific provider and model
        """
        # Check if specific model pricing exists in config
        if model_id and provider.value in self.pricing_config:
            provider_config = self.pricing_config[provider.value]
            if "models" in provider_config and model_id in provider_config["models"]:
                return provider_config["models"][model_id]
        
        # Check provider-level pricing in config
        if provider.value in self.pricing_config:
            provider_config = self.pricing_config[provider.value]
            if "default" in provider_config:
                return provider_config["default"]
        
        # Fall back to default pricing
        return self.default_pricing.get(provider, self.default_pricing[LLMProviderType.OPENAI])
    
    async def get_cost_breakdown(
        self,
        tenant_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for a tenant over a time period
        This would typically query the usage logs
        """
        # TODO: Implement actual cost breakdown from usage logs
        # This is a placeholder structure
        return {
            "tenant_id": tenant_id,
            "period": {"start": start_date, "end": end_date},
            "total_cost": 0.0,
            "breakdown_by_provider": {},
            "breakdown_by_model": {},
            "breakdown_by_task_type": {},
            "breakdown_by_user": {},
            "usage_statistics": {
                "total_requests": 0,
                "total_tokens": 0,
                "average_cost_per_request": 0.0
            }
        }
    
    async def estimate_monthly_cost(
        self,
        tenant_id: str,
        daily_requests: int,
        average_prompt_length: int,
        preferred_provider: LLMProviderType = LLMProviderType.OPENAI
    ) -> Dict[str, Any]:
        """
        Estimate monthly cost based on usage patterns
        """
        # Estimate tokens per request
        estimated_input_tokens = self._estimate_tokens("x" * average_prompt_length)
        estimated_output_tokens = 300  # Average response
        
        # Get pricing
        pricing = self._get_provider_pricing(preferred_provider)
        
        # Calculate cost per request
        cost_per_request = (
            (estimated_input_tokens / 1000) * pricing["input_token_cost"] +
            (estimated_output_tokens / 1000) * pricing["output_token_cost"]
        )
        
        # Calculate monthly costs
        daily_cost = daily_requests * cost_per_request
        monthly_cost = daily_cost * 30
        
        return {
            "tenant_id": tenant_id,
            "estimates": {
                "cost_per_request": cost_per_request,
                "daily_cost": daily_cost,
                "monthly_cost": monthly_cost,
                "provider": preferred_provider.value
            },
            "assumptions": {
                "daily_requests": daily_requests,
                "average_prompt_length": average_prompt_length,
                "estimated_input_tokens": estimated_input_tokens,
                "estimated_output_tokens": estimated_output_tokens
            },
            "recommendations": self._get_cost_recommendations(monthly_cost)
        }
    
    def _get_cost_recommendations(self, monthly_cost: float) -> list[str]:
        """
        Provide cost optimization recommendations
        """
        recommendations = []
        
        if monthly_cost > 1000:
            recommendations.append("Consider implementing aggressive caching for repeated queries")
            recommendations.append("Evaluate using smaller models for simple tasks")
        
        if monthly_cost > 500:
            recommendations.append("Implement request deduplication")
            recommendations.append("Consider batch processing for non-urgent requests")
        
        recommendations.append("Monitor token usage patterns to optimize prompt engineering")
        recommendations.append("Set up budget alerts to prevent unexpected overages")
        
        return recommendations
    
    async def update_pricing(self, new_pricing: Dict[str, Any]) -> None:
        """
        Update pricing configuration
        This would typically be called when pricing changes are detected
        """
        self.pricing_config.update(new_pricing)
        
        # Clear cost cache when pricing changes
        self.cost_cache.clear()
        
        logger.info("Pricing configuration updated", providers=list(new_pricing.keys()))
    
    def get_current_pricing(self) -> Dict[str, Any]:
        """
        Get current pricing configuration for all providers
        """
        return {
            "pricing_config": self.pricing_config,
            "default_pricing": {
                provider.value: pricing 
                for provider, pricing in self.default_pricing.items()
            },
            "last_updated": "2024-01-01T00:00:00Z"  # TODO: Track actual update time
        }
