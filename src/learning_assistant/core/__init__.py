"""
Core module for Learning Assistant.

This module provides the core infrastructure including:
- Configuration management
- Event bus
- Plugin management
- LLM service
- Prompt management
"""

from learning_assistant.core.config_manager import ConfigManager
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.history_manager import HistoryManager
from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.plugin_manager import PluginManager
from learning_assistant.core.prompt_manager import PromptManager
from learning_assistant.core.prompt_template import PromptTemplate
from learning_assistant.core.task_manager import TaskManager

__all__ = [
    "ConfigManager",
    "EventBus",
    "HistoryManager",
    "LLMService",
    "PluginManager",
    "PromptManager",
    "PromptTemplate",
    "TaskManager",
]
