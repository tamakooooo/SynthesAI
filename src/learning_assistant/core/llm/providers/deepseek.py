"""
DeepSeek Provider for Learning Assistant.

This module provides DeepSeek API integration using OpenAI-compatible API.
"""

from typing import Any

from loguru import logger
from openai import OpenAI

from learning_assistant.core.llm.base import BaseLLMProvider, LLMResponse


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek provider implementation using OpenAI-compatible API.

    Supports:
    - DeepSeek Chat, DeepSeek Coder
    - Cost tracking
    - Response validation
    """

    # Pricing (as of 2026-03-31)
    PRICING = {
        "deepseek-chat": {"input": 0.001, "output": 0.002},  # per 1K tokens
        "deepseek-coder": {"input": 0.001, "output": 0.002},
    }

    # DeepSeek API endpoint
    BASE_URL = "https://api.deepseek.com"

    def __init__(self, api_key: str, model: str, **kwargs: Any) -> None:
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key
            model: Model name (deepseek-chat, deepseek-coder)
            **kwargs: Additional parameters
        """
        # Use OpenAI SDK with DeepSeek base_url (OpenAI-compatible API)
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model
        self.kwargs = kwargs
        logger.info(f"DeepSeek provider initialized with model: {model}")

    def call(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Call DeepSeek API.

        Args:
            prompt: Prompt string
            **kwargs: Additional call parameters (temperature, max_tokens, etc.)

        Returns:
            LLM response
        """
        logger.debug(f"Calling DeepSeek API with prompt length: {len(prompt)}")

        # Extract parameters
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        # Call DeepSeek API (OpenAI-compatible)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract response content
        content = response.choices[0].message.content or ""

        # Extract usage information (handle None case)
        if response.usage is not None:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        else:
            # Fallback if usage information is not provided
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            logger.warning("DeepSeek API response missing usage information")

        logger.info(
            f"DeepSeek API call completed: model={self.model}, "
            f"tokens={usage['total_tokens']}, "
            f"cost=${self.estimate_cost(usage):.4f}"
        )

        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

    def validate_api_key(self) -> bool:
        """
        Validate DeepSeek API key by making a test request.

        Returns:
            True if valid, False otherwise
        """
        logger.debug("Validating DeepSeek API key")

        try:
            # Make a minimal API call to validate the key
            _response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )

            # If we got a response, the key is valid
            logger.info("DeepSeek API key validation successful")
            return True

        except Exception as e:
            logger.error(f"DeepSeek API key validation failed: {e}")
            return False

    def get_available_models(self) -> list[str]:
        """
        Get available DeepSeek models.

        Returns:
            List of model names
        """
        return list(self.PRICING.keys())

    def estimate_cost(self, usage: dict[str, int]) -> float:
        """
        Estimate cost based on token usage.

        Args:
            usage: Token usage dict {"prompt_tokens": int, "completion_tokens": int}

        Returns:
            Estimated cost in USD
        """
        # Get pricing for current model
        pricing = self.PRICING.get(self.model)

        if not pricing:
            logger.warning(f"No pricing data for model: {self.model}")
            return 0.0

        # Calculate cost
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        cost = (prompt_tokens * pricing["input"] / 1000) + (
            completion_tokens * pricing["output"] / 1000
        )

        return cost
