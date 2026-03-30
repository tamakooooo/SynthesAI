"""
Base LLM Provider for Learning Assistant.

This module defines the abstract base class for all LLM provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """
    LLM response structure.
    """

    content: str
    model: str
    usage: Dict[str, int]  # {"prompt_tokens": int, "completion_tokens": int}
    metadata: Dict[str, Any] = {}


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM provider implementations.

    Each provider (OpenAI, Anthropic, DeepSeek) must implement these methods.
    """

    @abstractmethod
    def __init__(self, api_key: str, model: str, **kwargs: Any) -> None:
        """
        Initialize provider with API key and model.

        Args:
            api_key: API key for authentication
            model: Model name
            **kwargs: Additional provider-specific parameters
        """
        pass

    @abstractmethod
    def call(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Call LLM API with prompt.

        Args:
            prompt: Prompt string
            **kwargs: Additional call parameters (temperature, max_tokens, etc.)

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        Validate API key by making a test request.

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model names
        """
        pass

    @abstractmethod
    def estimate_cost(self, usage: Dict[str, int]) -> float:
        """
        Estimate cost based on token usage.

        Args:
            usage: Token usage dict

        Returns:
            Estimated cost in USD
        """
        pass