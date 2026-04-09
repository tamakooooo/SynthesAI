"""
Base Module for Learning Assistant.

This module defines the abstract base class for all module plugins.
"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from learning_assistant.core.event_bus import EventBus


class BaseModule(ABC):
    """
    Abstract base class for module plugins.

    Modules provide core functionality for learning tasks.
    Each module must implement these required methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Module name.

        Returns:
            Module name string
        """
        pass

    @abstractmethod
    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize module with configuration and event bus.

        Args:
            config: Module configuration dict
            event_bus: EventBus instance for event-driven communication
        """
        pass

    @abstractmethod
    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute module core functionality.

        Args:
            input_data: Input data dict (URL, file path, etc.)

        Returns:
            Output data dict (result, file paths, etc.)
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup module resources.
        """
        pass

    def register_cli_commands(self, cli_group: Any) -> None:
        """
        Register CLI commands for this module (optional).

        Override this method to add CLI commands.

        Args:
            cli_group: Typer CLI group to register commands to
        """
        # Optional: subclasses can override to register CLI commands

    def get_metadata(self) -> dict[str, Any]:
        """
        Get module metadata.

        Returns:
            Module metadata dict
        """
        return {
            "name": self.name,
            "type": "module",
        }


class VideoSummaryModule(BaseModule):
    """
    Video Summary Module (MVP).

    This module will be implemented in Week 3-4.
    """

    @property
    def name(self) -> str:
        return "video_summary"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        logger.info(f"Initializing {self.name} module")
        # TODO: Implement initialization (Week 3 Day 27-28)

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"Executing {self.name} module")
        # TODO: Implement execution (Week 3-4)
        return {}

    def cleanup(self) -> None:
        logger.info(f"Cleaning up {self.name} module")
        # TODO: Implement cleanup (Week 3 Day 27-28)
