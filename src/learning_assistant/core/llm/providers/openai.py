"""
OpenAI Provider for Learning Assistant.

This module provides OpenAI API integration using official SDK.
"""

from typing import Any

from loguru import logger
from openai import OpenAI

from learning_assistant.core.llm.base import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation using official SDK.

    Supports:
    - GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
    - Cost tracking
    - Response validation
    """

    # Pricing (as of 2026-03-31)
    # Official OpenAI models
    PRICING = {
        "gpt-4o": {"input": 0.005, "output": 0.015},  # per 1K tokens
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        # Custom/Third-party models (placeholder pricing - update with actual rates)
        "kimi-k2.5": {"input": 0.002, "output": 0.005},  # Moonshot AI
        "glm-5": {"input": 0.001, "output": 0.002},  # Zhipu AI
        "deepseek-chat": {"input": 0.001, "output": 0.002},
        "qwen3.6-plus": {"input": 0.002, "output": 0.004},  # Alibaba
    }

    def __init__(self, api_key: str, model: str, **kwargs: Any) -> None:
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4o, gpt-4-turbo, gpt-3.5-turbo)
            **kwargs: Additional parameters (base_url, timeout, etc.)
        """
        # Extract base_url for custom endpoints
        base_url = kwargs.get("base_url")

        # Initialize OpenAI client with base_url if provided
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info(
                f"OpenAI provider initialized with model: {model}, base_url: {base_url}"
            )
        else:
            self.client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI provider initialized with model: {model}")

        self.model = model
        self.kwargs = kwargs

    def call(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Call OpenAI API.

        Args:
            prompt: Prompt string
            **kwargs: Additional call parameters (temperature, max_tokens, etc.)

        Returns:
            LLM response
        """
        logger.debug(f"Calling OpenAI API with prompt length: {len(prompt)}")

        # Merge initialization kwargs with call kwargs (call kwargs take precedence)
        merged_kwargs = {**self.kwargs, **kwargs}

        # Extract parameters with defaults
        temperature = merged_kwargs.get("temperature", 0.7)
        max_tokens = merged_kwargs.get("max_tokens", 2000)

        # Build messages list with system prompt (if provided)
        messages = []
        system_prompt = merged_kwargs.get("system_prompt")
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            logger.debug(f"Added system prompt: {len(system_prompt)} chars")
        messages.append({"role": "user", "content": prompt})

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
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
            logger.warning("OpenAI API response missing usage information")

        logger.info(
            f"OpenAI API call completed: model={self.model}, "
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
        Validate OpenAI API key by making a test request.

        Returns:
            True if valid, False otherwise
        """
        logger.debug("Validating OpenAI API key")

        try:
            # Make a minimal API call to validate the key
            _response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )

            # If we got a response, the key is valid
            logger.info("OpenAI API key validation successful")
            return True

        except Exception as e:
            logger.error(f"OpenAI API key validation failed: {e}")
            return False

    def get_available_models(self) -> list[str]:
        """
        Get available OpenAI models from API.

        Returns:
            List of model names from API
        """
        logger.info(f"Fetching available models from API (base_url: {self.kwargs.get('base_url', 'default')})")

        try:
            # Call OpenAI API to list models
            models_response = self.client.models.list()

            # Extract model IDs
            models = [model.id for model in models_response.data]

            # Filter to chat models only (exclude embedding, audio, etc.)
            chat_models = [
                m for m in models
                if any(keyword in m.lower() for keyword in ['gpt', 'chat', 'kimi', 'claude', 'deepseek', 'llama', 'qwen'])
                or not any(keyword in m.lower() for keyword in ['embed', 'whisper', 'tts', 'davinci', 'babbage'])
            ]

            # Sort alphabetically
            chat_models.sort()

            logger.info(f"Found {len(chat_models)} chat models: {chat_models[:10]}...")
            return chat_models

        except Exception as e:
            logger.warning(f"Failed to fetch models from API: {e}, falling back to static list")
            # Fallback to static list if API call fails
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
