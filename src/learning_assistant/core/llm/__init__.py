"""
LLM Service for Learning Assistant.

This module provides a unified interface for multiple LLM providers.
"""

from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.llm.base import BaseLLMProvider, LLMResponse

__all__ = [
    "LLMService",
    "BaseLLMProvider",
    "LLMResponse",
]