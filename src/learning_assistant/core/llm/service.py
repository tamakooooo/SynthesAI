"""
LLM Service for Learning Assistant.

This module provides a unified interface for multiple LLM providers using official SDKs.
"""

from typing import Any, Dict, Optional
from loguru import logger

from learning_assistant.core.llm.base import BaseLLMProvider, LLMResponse
from learning_assistant.core.llm.providers.openai import OpenAIProvider
from learning_assistant.core.llm.providers.anthropic import AnthropicProvider
from learning_assistant.core.llm.providers.deepseek import DeepSeekProvider


class LLMService:
    """
    Unified LLM Service for Learning Assistant.

    Provides:
    - Unified interface for multiple providers
    - Provider switching
    - Cost tracking
    - Retry mechanism
    - Response caching

    Uses official SDKs only (no third-party layers like LiteLLM).
    """

    # Provider registry
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "deepseek": DeepSeekProvider,
    }

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize LLM Service.

        Args:
            provider: Provider name (openai, anthropic, deepseek)
            api_key: API key
            model: Model name
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

        # Cost tracking
        self.total_cost = 0.0
        self.daily_cost = 0.0

        # Statistics
        self.call_count = 0
        self.total_tokens = 0

        logger.info(f"LLMService initialized with provider: {provider}, model: {model}")

    def call(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Call LLM API with prompt.

        Args:
            prompt: Prompt string
            **kwargs: Additional call parameters

        Returns:
            LLM response

        Raises:
            Exception: If call fails after retries
        """
        logger.info(f"Calling LLM: {self.provider_name}/{self.model}")

        # TODO: Implement retry mechanism (Week 2 Day 1-3)
        response = self.provider.call(prompt, **kwargs)

        # Update statistics
        self.call_count += 1
        self.total_tokens += response.usage.get("total_tokens", 0)

        # Update cost tracking
        cost = self.provider.estimate_cost(response.usage)
        self.total_cost += cost
        self.daily_cost += cost

        logger.info(f"LLM call completed: tokens={response.usage}, cost=${cost:.4f}")

        return response

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

    def estimate_cost(self, usage: Dict[str, int]) -> float:
        """
        Estimate cost for given token usage.

        Args:
            usage: Token usage dict

        Returns:
            Estimated cost in USD
        """
        return self.provider.estimate_cost(usage)

    def get_statistics(self) -> Dict[str, Any]:
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
        }

    def reset_daily_cost(self) -> None:
        """
        Reset daily cost counter.
        """
        logger.info("Resetting daily cost counter")
        self.daily_cost = 0.0