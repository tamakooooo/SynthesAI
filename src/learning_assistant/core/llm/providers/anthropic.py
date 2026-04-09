"""
Anthropic Provider for Learning Assistant.

This module provides Anthropic API integration using official SDK.
"""

from typing import Any

from anthropic import Anthropic
from loguru import logger

from learning_assistant.core.llm.base import BaseLLMProvider, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider implementation using official SDK.

    Supports:
    - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
    - Cost tracking
    - Response validation
    """

    # Pricing (as of 2026-03-31)
    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 0.003,
            "output": 0.015,
        },  # per 1K tokens
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }

    def __init__(self, api_key: str, model: str, **kwargs: Any) -> None:
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name (claude-3-5-sonnet, claude-3-opus, claude-3-haiku)
            **kwargs: Additional parameters
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.kwargs = kwargs
        logger.info(f"Anthropic provider initialized with model: {model}")

    def call(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Call Anthropic API.

        Args:
            prompt: Prompt string
            **kwargs: Additional call parameters (temperature, max_tokens, etc.)

        Returns:
            LLM response
        """
        logger.debug(f"Calling Anthropic API with prompt length: {len(prompt)}")

        # Extract parameters (Anthropic requires max_tokens)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        # Call Anthropic API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        # Extract response content
        # Handle different content block types (TextBlock, ThinkingBlock, etc.)
        if response.content and len(response.content) > 0:
            first_block = response.content[0]
            # Only extract text if it's a TextBlock
            if hasattr(first_block, "text"):
                content = first_block.text
            else:
                content = ""
                logger.warning("Anthropic API returned non-text content block")
        else:
            content = ""
            logger.warning("Anthropic API returned empty content")

        # Extract usage information
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

        logger.info(
            f"Anthropic API call completed: model={self.model}, "
            f"tokens={usage['total_tokens']}, "
            f"cost=${self.estimate_cost(usage):.4f}"
        )

        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            metadata={
                "stop_reason": response.stop_reason,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

    def validate_api_key(self) -> bool:
        """
        Validate Anthropic API key by making a test request.

        Returns:
            True if valid, False otherwise
        """
        logger.debug("Validating Anthropic API key")

        try:
            # Make a minimal API call to validate the key
            _response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )

            # If we got a response, the key is valid
            logger.info("Anthropic API key validation successful")
            return True

        except Exception as e:
            logger.error(f"Anthropic API key validation failed: {e}")
            return False

    def get_available_models(self) -> list[str]:
        """
        Get available Anthropic models.

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
