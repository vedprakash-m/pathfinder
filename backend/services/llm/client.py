"""
LLM Client

OpenAI client wrapper with cost tracking and error handling.
"""
import logging
import os
from typing import Any, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """
    OpenAI client wrapper with cost tracking.

    Uses singleton pattern to maintain a single client instance.
    Tracks token usage and costs for budget management.
    """

    _instance: Optional["LLMClient"] = None
    _client: Optional[AsyncOpenAI] = None

    # Cost per 1K tokens (gpt-5-mini estimated pricing)
    # Update these as pricing changes
    COST_PER_1K_INPUT = 0.0001
    COST_PER_1K_OUTPUT = 0.0004

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            self._client = AsyncOpenAI(api_key=api_key)

        return self._client

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Generate a completion using the configured model.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            json_mode: Whether to request JSON output

        Returns:
            Dict with content, tokens_used, cost, and model
        """
        model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response_format = {"type": "json_object"} if json_mode else None

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
            )

            # Extract response
            content = response.choices[0].message.content or ""
            usage = response.usage

            # Calculate cost
            if usage:
                input_cost = (usage.prompt_tokens / 1000) * self.COST_PER_1K_INPUT
                output_cost = (usage.completion_tokens / 1000) * self.COST_PER_1K_OUTPUT
                total_cost = input_cost + output_cost
                tokens_used = usage.total_tokens
            else:
                total_cost = 0.0
                tokens_used = 0

            logger.info(f"LLM request completed: {tokens_used} tokens, ${total_cost:.6f}")

            return {"content": content, "tokens_used": tokens_used, "cost": total_cost, "model": model}

        except Exception as e:
            logger.exception(f"LLM request failed: {e}")
            raise

    async def complete_with_history(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Generate a completion with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with content, tokens_used, cost, and model
        """
        model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
        client = self._get_client()

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        try:
            response = await client.chat.completions.create(
                model=model, messages=full_messages, max_tokens=max_tokens, temperature=temperature
            )

            content = response.choices[0].message.content or ""
            usage = response.usage

            if usage:
                input_cost = (usage.prompt_tokens / 1000) * self.COST_PER_1K_INPUT
                output_cost = (usage.completion_tokens / 1000) * self.COST_PER_1K_OUTPUT
                total_cost = input_cost + output_cost
                tokens_used = usage.total_tokens
            else:
                total_cost = 0.0
                tokens_used = 0

            return {"content": content, "tokens_used": tokens_used, "cost": total_cost, "model": model}

        except Exception as e:
            logger.exception(f"LLM request with history failed: {e}")
            raise

    async def check_health(self) -> bool:
        """Check if the LLM service is available."""
        try:
            response = await self.complete(prompt="Say 'ok' if you're working.", max_tokens=5, temperature=0)
            return "ok" in response["content"].lower()
        except Exception:
            return False


# Singleton instance
llm_client = LLMClient()
