"""
LLM Service Adapter - Abstract base class and provider implementations
Handles secure API key retrieval and standardized LLM interactions
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
import structlog
from core.llm_types import (
    LLMAuthenticationError,
    LLMProvider,
    LLMRateLimitError,
    LLMRequest,
    LLMResponse,
    LLMServiceUnavailableError,
    LLMValidationError,
    TokenUsage,
)
from services.key_vault import get_key_vault_service

logger = structlog.get_logger(__name__)


class LLMServiceAdapter(ABC):
    """
    Abstract base class for LLM service adapters
    Provides standardized interface for all LLM providers
    """

    def __init__(self, provider: LLMProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self.base_url = config.get("base_url")
        self.timeout = config.get("timeout_seconds", 30)
        self.max_concurrent = config.get("max_concurrent_requests", 50)
        self.rate_limit_rpm = config.get("rate_limit_rpm", 1000)

        # API key will be fetched securely at runtime
        self._api_key: Optional[str] = None
        self._api_key_fetched: bool = False

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

    async def _ensure_api_key(self) -> str:
        """Securely fetch API key from Key Vault if not already cached"""
        if not self._api_key_fetched:
            key_vault = get_key_vault_service()
            secret_ref = self._get_secret_reference()

            try:
                self._api_key = await key_vault.get_secret(secret_ref)
                self._api_key_fetched = True
                logger.debug("API key fetched from Key Vault", provider=self.provider.value)
            except Exception as e:
                logger.error("Failed to fetch API key", provider=self.provider.value, error=str(e))
                raise LLMAuthenticationError(self.provider.value)

        if not self._api_key:
            raise LLMAuthenticationError(f"No API key available for {self.provider.value}")

        return self._api_key

    @abstractmethod
    def _get_secret_reference(self) -> str:
        """Get the Key Vault secret reference for this provider"""
        pass

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=self.max_concurrent),
            )
        return self._client

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response for the given request"""
        pass

    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Generate streaming response for the given request"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy and accessible"""
        pass

    async def close(self):
        """Clean up resources"""
        if self._client:
            await self._client.aclose()
            self._client = None


class OpenAIAdapter(LLMServiceAdapter):
    """OpenAI API adapter"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(LLMProvider.OPENAI, config)

    def _get_secret_reference(self) -> str:
        return "secret-openai-api-key"  # Key Vault reference, not the actual key

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API"""
        start_time = time.time()
        request_id = request.request_id or f"openai_{int(time.time() * 1000)}"

        try:
            async with self._semaphore:
                api_key = await self._ensure_api_key()
                client = await self._get_client()

                # Prepare request payload
                payload = {
                    "model": request.preferred_model or "gpt-4o-mini",
                    "messages": [{"role": "user", "content": request.prompt}],
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature or 0.7,
                    "stream": False,
                }

                # Remove None values
                payload = {k: v for k, v in payload.items() if v is not None}

                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

                logger.debug(
                    "Sending request to OpenAI", model=payload["model"], request_id=request_id
                )

                response = await client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    raise LLMRateLimitError(self.provider.value, retry_after)

                # Handle authentication errors
                if response.status_code == 401:
                    raise LLMAuthenticationError(self.provider.value)

                # Handle service unavailable
                if response.status_code >= 500:
                    raise LLMServiceUnavailableError(self.provider.value, payload["model"])

                # Parse successful response
                response.raise_for_status()
                data = response.json()

                # Extract response data
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                model_used = data.get("model", payload["model"])

                # Calculate token usage and cost
                token_usage = TokenUsage(
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                )

                estimated_cost = self._calculate_cost(token_usage, model_used)
                response_time_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    "OpenAI request completed",
                    model=model_used,
                    tokens=token_usage.total_tokens,
                    cost=estimated_cost,
                    response_time_ms=response_time_ms,
                    request_id=request_id,
                )

                return LLMResponse(
                    content=content,
                    model_used=model_used,
                    provider=self.provider,
                    token_usage=token_usage,
                    estimated_cost=estimated_cost,
                    response_time_ms=response_time_ms,
                    cached=False,
                    request_id=request_id,
                    fallback_used=False,
                )

        except (LLMRateLimitError, LLMAuthenticationError, LLMServiceUnavailableError):
            raise
        except httpx.TimeoutException:
            raise LLMServiceUnavailableError(self.provider.value, "timeout")
        except Exception as e:
            logger.error("OpenAI request failed", error=str(e), request_id=request_id)
            raise LLMServiceUnavailableError(self.provider.value, str(e))

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API"""
        async with self._semaphore:
            api_key = await self._ensure_api_key()
            client = await self._get_client()

            payload = {
                "model": request.preferred_model or "gpt-4o-mini",
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature or 0.7,
                "stream": True,
            }

            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", json=payload, headers=headers
            ) as response:
                if response.status_code != 200:
                    raise LLMServiceUnavailableError(self.provider.value, "stream_error")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break

                        try:
                            import json

                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except:
                            continue

    def _calculate_cost(self, token_usage: TokenUsage, model: str) -> float:
        """Calculate estimated cost based on token usage"""
        # Cost per 1K tokens (these would come from config)
        costs = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        }

        model_costs = costs.get(model, costs["gpt-4o-mini"])

        input_cost = (token_usage.input_tokens / 1000) * model_costs["input"]
        output_cost = (token_usage.output_tokens / 1000) * model_costs["output"]

        return round(input_cost + output_cost, 6)

    async def health_check(self) -> bool:
        """Check OpenAI API health"""
        try:
            api_key = await self._ensure_api_key()
            client = await self._get_client()

            headers = {"Authorization": f"Bearer {api_key}"}

            # Make a simple request to list models
            response = await client.get(f"{self.base_url}/models", headers=headers, timeout=5.0)

            return response.status_code == 200

        except Exception as e:
            logger.error("OpenAI health check failed", error=str(e))
            return False


class GeminiAdapter(LLMServiceAdapter):
    """Google Gemini API adapter"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(LLMProvider.GEMINI, config)

    def _get_secret_reference(self) -> str:
        return "secret-gemini-api-key"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini API"""
        start_time = time.time()
        request_id = request.request_id or f"gemini_{int(time.time() * 1000)}"

        try:
            async with self._semaphore:
                api_key = await self._ensure_api_key()
                client = await self._get_client()

                model = request.preferred_model or "gemini-1.5-flash"

                payload = {
                    "contents": [{"parts": [{"text": request.prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": request.max_tokens,
                        "temperature": request.temperature or 0.7,
                    },
                }

                # Remove None values
                if request.max_tokens is None:
                    del payload["generationConfig"]["maxOutputTokens"]

                url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"

                logger.debug("Sending request to Gemini", model=model, request_id=request_id)

                response = await client.post(url, json=payload)

                if response.status_code == 429:
                    raise LLMRateLimitError(self.provider.value, None)

                if response.status_code == 401:
                    raise LLMAuthenticationError(self.provider.value)

                if response.status_code >= 500:
                    raise LLMServiceUnavailableError(self.provider.value, model)

                response.raise_for_status()
                data = response.json()

                # Extract content
                content = ""
                if "candidates" in data and data["candidates"]:
                    content = data["candidates"][0]["content"]["parts"][0]["text"]

                # Estimate token usage (Gemini API doesn't always return usage)
                token_usage = TokenUsage(
                    input_tokens=len(request.prompt) // 4,  # Rough estimate
                    output_tokens=len(content) // 4,
                    total_tokens=(len(request.prompt) + len(content)) // 4,
                )

                estimated_cost = self._calculate_cost(token_usage, model)
                response_time_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    "Gemini request completed",
                    model=model,
                    tokens=token_usage.total_tokens,
                    cost=estimated_cost,
                    response_time_ms=response_time_ms,
                    request_id=request_id,
                )

                return LLMResponse(
                    content=content,
                    model_used=model,
                    provider=self.provider,
                    token_usage=token_usage,
                    estimated_cost=estimated_cost,
                    response_time_ms=response_time_ms,
                    cached=False,
                    request_id=request_id,
                    fallback_used=False,
                )

        except (LLMRateLimitError, LLMAuthenticationError, LLMServiceUnavailableError):
            raise
        except Exception as e:
            logger.error("Gemini request failed", error=str(e), request_id=request_id)
            raise LLMServiceUnavailableError(self.provider.value, str(e))

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini API"""
        # Gemini streaming implementation would go here
        raise NotImplementedError("Gemini streaming not implemented yet")

    def _calculate_cost(self, token_usage: TokenUsage, model: str) -> float:
        """Calculate estimated cost for Gemini"""
        costs = {
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        }

        model_costs = costs.get(model, costs["gemini-1.5-flash"])

        input_cost = (token_usage.input_tokens / 1000) * model_costs["input"]
        output_cost = (token_usage.output_tokens / 1000) * model_costs["output"]

        return round(input_cost + output_cost, 6)

    async def health_check(self) -> bool:
        """Check Gemini API health"""
        try:
            api_key = await self._ensure_api_key()
            client = await self._get_client()

            # Make a simple request
            url = f"{self.base_url}/models?key={api_key}"
            response = await client.get(url, timeout=5.0)

            return response.status_code == 200

        except Exception as e:
            logger.error("Gemini health check failed", error=str(e))
            return False


class PerplexityAdapter(LLMServiceAdapter):
    """Perplexity API adapter"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(LLMProvider.PERPLEXITY, config)

    def _get_secret_reference(self) -> str:
        return "secret-perplexity-api-key"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Perplexity API"""
        # Similar implementation to OpenAI but with Perplexity-specific handling
        raise NotImplementedError("Perplexity adapter not fully implemented yet")

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Generate streaming response using Perplexity API"""
        raise NotImplementedError("Perplexity streaming not implemented yet")

    async def health_check(self) -> bool:
        """Check Perplexity API health"""
        return True  # Placeholder


# Adapter factory
def create_adapter(provider: LLMProvider, config: Dict[str, Any]) -> LLMServiceAdapter:
    """Factory function to create appropriate adapter"""
    adapters = {
        LLMProvider.OPENAI: OpenAIAdapter,
        LLMProvider.GEMINI: GeminiAdapter,
        LLMProvider.PERPLEXITY: PerplexityAdapter,
    }

    adapter_class = adapters.get(provider)
    if not adapter_class:
        raise LLMValidationError(f"Unsupported provider: {provider.value}")

    return adapter_class(config)
