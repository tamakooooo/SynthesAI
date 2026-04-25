"""
Core shared services for Learning Assistant.

This module provides reusable services that can be used across modules.
"""

from learning_assistant.core.services.content_fetcher import ContentFetcher
from learning_assistant.core.services.content_parser import ContentParser

__all__ = [
    "ContentFetcher",
    "ContentParser",
]