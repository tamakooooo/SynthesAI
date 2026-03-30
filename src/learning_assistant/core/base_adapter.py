"""
Base Adapter for Learning Assistant.

This module defines the abstract base class for all adapter plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from loguru import logger

from learning_assistant.core.event_bus import EventBus


class BaseAdapter(ABC):
    """
    Abstract base class for adapter plugins.

    Adapters provide platform integration (Feishu, Siyuan, Obsidian, etc.)
    Each adapter must implement these required methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Adapter name.

        Returns:
            Adapter name string
        """
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize adapter with configuration and event bus.

        Args:
            config: Adapter configuration dict
            event_bus: EventBus instance for subscribing to events
        """
        pass

    @abstractmethod
    def push_content(self, content: Dict[str, Any]) -> bool:
        """
        Push content to platform.

        Args:
            content: Content dict (title, body, metadata, etc.)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def sync_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        """
        Sync data to platform.

        Args:
            data_type: Data type (history, vocabulary, etc.)
            data: Data dict

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def handle_trigger(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle trigger event from platform (webhook, callback, etc.).

        Args:
            trigger_data: Trigger data dict

        Returns:
            Response dict
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup adapter resources.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get adapter metadata.

        Returns:
            Adapter metadata dict
        """
        return {
            "name": self.name,
            "type": "adapter",
        }


class FeishuAdapter(BaseAdapter):
    """
    Feishu Adapter (placeholder).

    This adapter will be implemented in Week 5.
    """

    @property
    def name(self) -> str:
        return "feishu"

    def initialize(self, config: Dict[str, Any], event_bus: EventBus) -> None:
        logger.info(f"Initializing {self.name} adapter")
        # TODO: Implement initialization (Week 5)

    def push_content(self, content: Dict[str, Any]) -> bool:
        logger.info(f"Pushing content to {self.name}")
        # TODO: Implement content push (Week 5)
        return False

    def sync_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        logger.info(f"Syncing data to {self.name}")
        # TODO: Implement data sync (Week 5)
        return False

    def handle_trigger(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Handling trigger from {self.name}")
        # TODO: Implement trigger handling (Week 5)
        return {}

    def cleanup(self) -> None:
        logger.info(f"Cleaning up {self.name} adapter")
        # TODO: Implement cleanup (Week 5)