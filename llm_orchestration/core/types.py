"""
Core types and models for the LLM Orchestration Layer
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Supported task types for LLM requests"""

    SIMPLE_QA = "simple_qa"
    COMPLEX_REASONING = "complex_reasoning"
    CODE_GENERATION = "code_generation"
    CREATIVE_WRITING = "creative_writing"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"
    ANTHROPIC = "anthropic"


class RequestPriority(str, Enum):
    """Request priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class LLMRequest(BaseModel):
    """Standardized LLM request structure"""

    prompt: str = Field(..., description="The prompt to send to the LLM")
    user_id: str = Field(..., description="Unique user identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier for multi-tenancy")
    task_type: TaskType = Field(TaskType.SIMPLE_QA, description="Type of task being performed")
    priority: RequestPriority = Field(RequestPriority.NORMAL, description="Request priority")

    # Model preferences
    preferred_model: Optional[str] = Field(None, description="Preferred model ID")
    avoid_models: List[str] = Field(default_factory=list, description="Models to avoid")

    # Request parameters
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response")
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    stream: bool = Field(False, description="Enable streaming response")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    request_id: Optional[str] = Field(None, description="Optional request ID for tracking")

    class Config:
        use_enum_values = True


class TokenUsage(BaseModel):
    """Token usage information"""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Standardized LLM response structure"""

    content: str = Field(..., description="The generated content")
    model_used: str = Field(..., description="Model that generated the response")
    provider: LLMProvider = Field(..., description="Provider that served the request")

    # Usage and cost information
    token_usage: TokenUsage = Field(..., description="Token usage details")
    estimated_cost: float = Field(..., description="Estimated cost in USD")

    # Performance metrics
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    cached: bool = Field(False, description="Whether response was served from cache")

    # Request tracking
    request_id: str = Field(..., description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Fallback information
    fallback_used: bool = Field(False, description="Whether fallback model was used")
    original_model_attempted: Optional[str] = Field(
        None, description="Original model if fallback occurred"
    )

    class Config:
        use_enum_values = True


class BudgetStatus(BaseModel):
    """Budget status information"""

    current_usage: float = Field(..., description="Current usage in USD")
    limit: float = Field(..., description="Budget limit in USD")
    remaining: float = Field(..., description="Remaining budget in USD")
    percentage_used: float = Field(..., description="Percentage of budget used")
    period_start: datetime = Field(..., description="Budget period start")
    period_end: datetime = Field(..., description="Budget period end")


class ModelHealth(BaseModel):
    """Model health status"""

    model_id: str
    provider: LLMProvider
    is_healthy: bool
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    failure_count: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: float = 0.0


class CacheEntry(BaseModel):
    """Cache entry structure"""

    key: str
    content: str
    model_used: str
    timestamp: datetime
    hit_count: int = 0
    token_usage: TokenUsage


class UsageLogEntry(BaseModel):
    """Usage log entry for analytics"""

    request_id: str
    user_id: str
    tenant_id: Optional[str]
    model_used: str
    provider: LLMProvider
    task_type: TaskType

    # Request details
    prompt_length: int
    response_length: int
    token_usage: TokenUsage
    estimated_cost: float

    # Performance
    response_time_ms: int
    cached: bool
    fallback_used: bool

    # Outcome
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    # Timestamps
    request_timestamp: datetime
    response_timestamp: datetime

    class Config:
        use_enum_values = True


class TenantInfo(BaseModel):
    """Tenant configuration information"""

    tenant_id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant display name")
    allowed_providers: List[LLMProvider] = Field(
        default_factory=list, description="Allowed LLM providers"
    )
    budget_limit: float = Field(100.0, description="Monthly budget limit in USD")
    rate_limit_per_minute: int = Field(60, description="Rate limit per minute")
    priority_level: RequestPriority = Field(
        RequestPriority.NORMAL, description="Tenant priority level"
    )

    # Advanced settings
    enable_caching: bool = Field(True, description="Enable response caching")
    max_tokens_per_request: int = Field(4000, description="Maximum tokens per request")
    allowed_models: List[str] = Field(default_factory=list, description="Specific models allowed")

    class Config:
        use_enum_values = True


# Exception classes for typed error handling
class LLMOrchestrationError(Exception):
    """Base exception for LLM orchestration errors"""

    pass


class LLMRateLimitError(LLMOrchestrationError):
    """Raised when rate limit is exceeded"""

    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {provider}")


class LLMServiceUnavailableError(LLMOrchestrationError):
    """Raised when LLM service is unavailable"""

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        super().__init__(f"Service unavailable: {provider}/{model}")


class LLMBudgetExceededError(LLMOrchestrationError):
    """Raised when budget is exceeded"""

    def __init__(self, user_id: str, current_usage: float, limit: float):
        self.user_id = user_id
        self.current_usage = current_usage
        self.limit = limit
        super().__init__(f"Budget exceeded for user {user_id}: {current_usage}/{limit}")


class LLMConfigurationError(LLMOrchestrationError):
    """Raised when there's a configuration error"""

    pass


class LLMAuthenticationError(LLMOrchestrationError):
    """Raised when authentication fails"""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Authentication failed for {provider}")


class LLMValidationError(LLMOrchestrationError):
    """Raised when request validation fails"""

    pass
