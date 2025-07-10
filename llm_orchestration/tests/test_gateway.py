"""
Unit tests for the LLM Gateway
"""

from unittest.mock import AsyncMock, Mock

import pytest
from core.gateway import LLMGateway
from core.llm_types import LLMRequest, LLMResponse, RequestPriority, TaskType, TokenUsage


@pytest.fixture
async def mock_gateway():
    """Create a mock gateway with all dependencies"""

    # Mock all the service dependencies
    config_manager = Mock()
    routing_engine = AsyncMock()
    budget_manager = AsyncMock()
    cache_manager = AsyncMock()
    circuit_breaker = AsyncMock()
    usage_logger = AsyncMock()
    cost_estimator = AsyncMock()
    analytics_collector = AsyncMock()

    # Configure mocks
    budget_manager.check_budget_availability.return_value = Mock(can_proceed=True)
    cache_manager.get_cached_response.return_value = None
    circuit_breaker.can_execute.return_value = True
    cost_estimator.estimate_request_cost.return_value = 0.01
    cost_estimator.calculate_actual_cost.return_value = 0.015

    # Mock routing engine to return a selected model
    selected_model = Mock()
    selected_model.provider = LLMProviderType.OPENAI
    selected_model.model_id = "gpt-3.5-turbo"
    routing_engine.select_model.return_value = selected_model

    gateway = LLMGateway(
        config_manager=config_manager,
        routing_engine=routing_engine,
        budget_manager=budget_manager,
        cache_manager=cache_manager,
        circuit_breaker=circuit_breaker,
        usage_logger=usage_logger,
        cost_estimator=cost_estimator,
        analytics_collector=analytics_collector,
    )

    # Mock the adapter factory
    mock_adapter = AsyncMock()
    mock_response = LLMResponse(
        request_id="test-123",
        content="This is a test response",
        model_used="gpt-3.5-turbo",
        provider="openai",
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        metadata={},
    )
    mock_adapter.process_request.return_value = mock_response
    gateway.adapter_factory.get_adapter = AsyncMock(return_value=mock_adapter)

    return gateway


@pytest.fixture
def sample_request():
    """Create a sample LLM request"""
    return LLMRequest(
        request_id="test-123",
        user_id="user-456",
        prompt="What is the capital of France?",
        task_type=TaskType.QUESTION_ANSWERING,
        priority=RequestPriority.NORMAL,
        parameters=LLMRequestParameters(temperature=0.7, max_tokens=100),
    )


@pytest.fixture
def sample_tenant():
    """Create a sample tenant info"""
    return TenantInfo(
        tenant_id="tenant-789",
        is_active=True,
        subscription_tier="premium",
        daily_budget_limit=100.0,
        monthly_budget_limit=3000.0,
        rate_limit_requests_per_minute=100,
        allowed_providers=[LLMProviderType.OPENAI, LLMProviderType.GEMINI],
        custom_settings={},
    )


@pytest.mark.asyncio
async def test_process_request_success(mock_gateway, sample_request, sample_tenant):
    """Test successful request processing"""

    response = await mock_gateway.process_request(sample_request, sample_tenant)

    # Verify response
    assert response is not None
    assert response.request_id == "test-123"
    assert response.content == "This is a test response"
    assert response.provider == "openai"

    # Verify service calls
    mock_gateway.budget_manager.check_budget_availability.assert_called_once()
    mock_gateway.cache_manager.get_cached_response.assert_called_once()
    mock_gateway.routing_engine.select_model.assert_called_once()
    mock_gateway.circuit_breaker.can_execute.assert_called_once()


@pytest.mark.asyncio
async def test_process_request_cache_hit(mock_gateway, sample_request, sample_tenant):
    """Test request processing with cache hit"""

    # Configure cache to return a response
    cached_response = LLMResponse(
        request_id="test-123",
        content="Cached response",
        model_used="gpt-3.5-turbo",
        provider="openai",
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        metadata={},
    )
    mock_gateway.cache_manager.get_cached_response.return_value = cached_response

    response = await mock_gateway.process_request(sample_request, sample_tenant)

    # Verify cache hit response
    assert response.content == "Cached response"

    # Verify that LLM adapter was not called for cache hit
    mock_gateway.adapter_factory.get_adapter.assert_not_called()


@pytest.mark.asyncio
async def test_process_request_budget_exceeded(mock_gateway, sample_request, sample_tenant):
    """Test request processing when budget is exceeded"""

    # Configure budget manager to reject
    mock_gateway.budget_manager.check_budget_availability.return_value = Mock(
        can_proceed=False, reason="Daily budget exceeded"
    )

    with pytest.raises(Exception):  # Should raise LLMBudgetExceededError
        await mock_gateway.process_request(sample_request, sample_tenant)


@pytest.mark.asyncio
async def test_process_request_circuit_breaker_open(mock_gateway, sample_request, sample_tenant):
    """Test request processing when circuit breaker is open"""

    # Configure circuit breaker to be open
    mock_gateway.circuit_breaker.can_execute.return_value = False

    with pytest.raises(Exception):  # Should raise LLMGatewayError
        await mock_gateway.process_request(sample_request, sample_tenant)


@pytest.mark.asyncio
async def test_system_health(mock_gateway):
    """Test system health endpoint"""

    # Configure mocks for health check
    mock_gateway.circuit_breaker.get_all_states.return_value = {"openai": "closed"}
    mock_gateway.cache_manager.get_stats.return_value = {"hits": 10, "misses": 5}
    mock_gateway.budget_manager.get_active_alerts.return_value = []

    health = await mock_gateway.get_system_health()

    assert "active_requests" in health
    assert "circuit_breakers" in health
    assert "cache_stats" in health
    assert "budget_alerts" in health
    assert "timestamp" in health


if __name__ == "__main__":
    pytest.main([__file__])
