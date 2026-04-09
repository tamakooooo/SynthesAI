"""
LLM Service for Learning Assistant.

This module provides a unified interface for multiple LLM providers using official SDKs.
"""

import time
from typing import Any

from loguru import logger

from learning_assistant.core.llm.base import BaseLLMProvider, LLMResponse
from learning_assistant.core.llm.providers.anthropic import AnthropicProvider
from learning_assistant.core.llm.providers.deepseek import DeepSeekProvider
from learning_assistant.core.llm.providers.openai import OpenAIProvider


class LLMService:
    """
    Unified LLM Service for Learning Assistant.

    Provides:
    - Unified interface for multiple providers
    - Provider switching
    - Cost tracking
    - Retry mechanism with exponential backoff
    - Response caching

    Uses official SDKs only (no third-party layers like LiteLLM).
    """

    # Provider registry
    PROVIDERS: dict[str, type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "deepseek": DeepSeekProvider,
    }

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize LLM Service.

        Args:
            provider: Provider name (openai, anthropic, deepseek)
            api_key: API key
            model: Model name
            max_retries: Maximum number of retries on failure (default: 3)
            retry_delay: Initial retry delay in seconds (default: 1.0, exponential backoff)
            **kwargs: Additional provider-specific parameters

        Raises:
            ValueError: If provider not supported
        """
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        provider_class = self.PROVIDERS[provider]
        self.provider = provider_class(api_key=api_key, model=model, **kwargs)
        self.provider_name = provider
        self.model = model

        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Cost tracking
        self.total_cost = 0.0
        self.daily_cost = 0.0

        # Statistics
        self.call_count = 0
        self.total_tokens = 0
        self.retry_count = 0

        logger.info(f"LLMService initialized with provider: {provider}, model: {model}")

    def call(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Call LLM API with prompt.

        Implements retry mechanism with exponential backoff.

        Args:
            prompt: Prompt string
            **kwargs: Additional call parameters

        Returns:
            LLM response

        Raises:
            Exception: If call fails after all retries
        """
        logger.info(f"Calling LLM: {self.provider_name}/{self.model}")

        # Retry loop
        for attempt in range(self.max_retries + 1):
            try:
                response = self.provider.call(prompt, **kwargs)

                # Update statistics
                self.call_count += 1
                self.total_tokens += response.usage.get("total_tokens", 0)

                # Update cost tracking
                cost = self.provider.estimate_cost(response.usage)
                self.total_cost += cost
                self.daily_cost += cost

                logger.info(
                    f"LLM call completed: tokens={response.usage}, cost=${cost:.4f}"
                )

                return response

            except Exception as e:
                # Check if this is the last attempt
                if attempt == self.max_retries:
                    logger.error(
                        f"LLM call failed after {self.max_retries + 1} attempts: {e}"
                    )
                    raise

                # Calculate retry delay with exponential backoff
                delay = self.retry_delay * (2**attempt)
                self.retry_count += 1

                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                    f"retrying in {delay:.1f}s: {e}"
                )

                # Wait before retrying
                time.sleep(delay)

        # This should never be reached, but raise exception for safety
        raise Exception("LLM call failed after all retries")

    def validate_api_key(self) -> bool:
        """
        Validate current API key.

        Returns:
            True if valid, False otherwise
        """
        logger.info(f"Validating API key for {self.provider_name}")
        return self.provider.validate_api_key()

    def get_available_models(self) -> list[str]:
        """
        Get available models for current provider.

        Returns:
            List of model names
        """
        return self.provider.get_available_models()

    def estimate_cost(self, usage: dict[str, int]) -> float:
        """
        Estimate cost for given token usage.

        Args:
            usage: Token usage dict

        Returns:
            Estimated cost in USD
        """
        return self.provider.estimate_cost(usage)

    def get_statistics(self) -> dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Statistics dict
        """
        return {
            "provider": self.provider_name,
            "model": self.model,
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "daily_cost": self.daily_cost,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    def reset_daily_cost(self) -> None:
        """
        Reset daily cost counter.
        """
        logger.info("Resetting daily cost counter")
        self.daily_cost = 0.0
