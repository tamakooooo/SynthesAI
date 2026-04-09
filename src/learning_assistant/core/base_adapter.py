"""
Base Adapter for Learning Assistant.

This module defines the abstract base class for all adapter plugins
with enhanced event subscription, lifecycle management, and error handling.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from learning_assistant.core.event_bus import Event, EventBus, EventType


class AdapterState(Enum):
    """
    Adapter lifecycle states.
    """

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class AdapterStatus:
    """
    Adapter status information.
    """

    state: AdapterState
    name: str
    message: str = ""
    error_count: int = 0
    last_error: str | None = None
    uptime_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """
    Abstract base class for adapter plugins.

    Adapters provide platform integration (Siyuan, Obsidian, etc.)
    Each adapter must implement these required methods.

    Enhanced features:
    - Lifecycle state tracking
    - Event subscription helpers
    - Error handling with tracking
    - Configuration validation
    """

    def __init__(self) -> None:
        """Initialize adapter base."""
        self.state: AdapterState = AdapterState.UNINITIALIZED
        self.config: dict[str, Any] = {}
        self.event_bus: EventBus | None = None
        self._subscribed_events: dict[EventType, Callable] = {}
        self._error_count: int = 0
        self._last_error: str | None = None

        logger.debug(f"{self.__class__.__name__} created (uninitialized)")

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Adapter name.

        Returns:
            Adapter name string
        """
        pass

    @property
    def version(self) -> str:
        """
        Adapter version.

        Returns:
            Version string (default: "1.0.0")
        """
        return "1.0.0"

    @property
    def description(self) -> str:
        """
        Adapter description.

        Returns:
            Description string
        """
        return f"{self.name} adapter"

    @abstractmethod
    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize adapter with configuration and event bus.

        Args:
            config: Adapter configuration dict
            event_bus: EventBus instance for subscribing to events

        Note:
            Implementations should call _set_initializing() at start
            and _set_ready() when complete, or _set_error() on failure.
        """
        pass

    @abstractmethod
    def push_content(self, content: dict[str, Any]) -> bool:
        """
        Push content to platform.

        Args:
            content: Content dict (title, body, metadata, etc.)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def sync_data(self, data_type: str, data: dict[str, Any]) -> bool:
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
    def handle_trigger(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
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

        Note:
            Implementations should call _set_shutting_down() at start.
        """
        pass

    # Lifecycle helpers

    def _set_initializing(self) -> None:
        """Set adapter state to INITIALIZING."""
        self.state = AdapterState.INITIALIZING
        logger.info(f"Adapter {self.name} initializing")

    def _set_ready(self) -> None:
        """Set adapter state to READY."""
        self.state = AdapterState.READY
        logger.info(f"Adapter {self.name} ready")

    def _set_error(self, error_message: str) -> None:
        """
        Set adapter state to ERROR.

        Args:
            error_message: Error message
        """
        self.state = AdapterState.ERROR
        self._error_count += 1
        self._last_error = error_message
        logger.error(f"Adapter {self.name} error: {error_message}")

    def _set_shutting_down(self) -> None:
        """Set adapter state to SHUTTING_DOWN."""
        self.state = AdapterState.SHUTTING_DOWN
        logger.info(f"Adapter {self.name} shutting down")

    def get_status(self) -> AdapterStatus:
        """
        Get adapter status.

        Returns:
            AdapterStatus instance
        """
        return AdapterStatus(
            state=self.state,
            name=self.name,
            message=self._get_state_message(),
            error_count=self._error_count,
            last_error=self._last_error,
            metadata=self.get_metadata(),
        )

    def _get_state_message(self) -> str:
        """
        Get human-readable state message.

        Returns:
            State message
        """
        messages = {
            AdapterState.UNINITIALIZED: "Adapter not initialized",
            AdapterState.INITIALIZING: "Adapter initializing",
            AdapterState.READY: "Adapter ready for operation",
            AdapterState.ERROR: f"Adapter in error state: {self._last_error}",
            AdapterState.SHUTTING_DOWN: "Adapter shutting down",
        }
        return messages.get(self.state, "Unknown state")

    # Event subscription helpers

    def subscribe_to_event(
        self, event_type: EventType, handler: Callable[[Event], None] | None = None
    ) -> None:
        """
        Subscribe to an event type on the event bus.

        Args:
            event_type: Event type to subscribe to
            handler: Optional custom handler (default: default_event_handler)
        """
        if not self.event_bus:
            logger.warning("Cannot subscribe to event: event_bus not set")
            return

        # Use default handler if none provided
        if handler is None:
            handler = self.default_event_handler

        # Subscribe to event
        self.event_bus.subscribe(event_type, handler)

        # Track subscription
        self._subscribed_events[event_type] = handler

        logger.debug(f"Adapter {self.name} subscribed to {event_type.value}")

    def unsubscribe_from_event(self, event_type: EventType) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
        """
        if not self.event_bus:
            logger.warning("Cannot unsubscribe from event: event_bus not set")
            return

        if event_type not in self._subscribed_events:
            logger.warning(f"Adapter {self.name} not subscribed to {event_type.value}")
            return

        # Unsubscribe
        handler = self._subscribed_events[event_type]
        self.event_bus.unsubscribe(event_type, handler)

        # Remove from tracking
        del self._subscribed_events[event_type]

        logger.debug(f"Adapter {self.name} unsubscribed from {event_type.value}")

    def unsubscribe_from_all_events(self) -> None:
        """Unsubscribe from all subscribed events."""
        for event_type in list(self._subscribed_events.keys()):
            self.unsubscribe_from_event(event_type)

        logger.debug(f"Adapter {self.name} unsubscribed from all events")

    def default_event_handler(self, event: Event) -> None:
        """
        Default event handler for subscribed events.

        Args:
            event: Event to handle
        """
        logger.info(
            f"Adapter {self.name} received event {event.event_type.value} from {event.source}"
        )

        # Default behavior: log the event
        # Adapters can override this or provide custom handlers
        logger.debug(f"Event data: {event.data}")

    # Configuration helpers

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate adapter configuration.

        Args:
            config: Configuration dict

        Returns:
            True if valid, False otherwise

        Note:
            Base implementation always returns True.
            Subclasses should override for specific validation.
        """
        return True

    def get_config_value(
        self, key: str, default: Any = None, required: bool = False
    ) -> Any:
        """
        Get configuration value with optional default.

        Args:
            key: Configuration key
            default: Default value if key not found
            required: Raise error if key not found

        Returns:
            Configuration value

        Raises:
            ValueError: If required key not found
        """
        if key not in self.config:
            if required:
                raise ValueError(f"Required config key '{key}' not found")
            return default

        return self.config[key]

    # Error tracking helpers

    def record_error(self, error_message: str) -> None:
        """
        Record an error without changing state.

        Args:
            error_message: Error message
        """
        self._error_count += 1
        self._last_error = error_message
        logger.warning(f"Adapter {self.name} recorded error: {error_message}")

    def clear_errors(self) -> None:
        """Clear error history."""
        self._error_count = 0
        self._last_error = None
        logger.debug(f"Adapter {self.name} cleared error history")

    # Metadata

    def get_metadata(self) -> dict[str, Any]:
        """
        Get adapter metadata.

        Returns:
            Adapter metadata dict
        """
        return {
            "name": self.name,
            "type": "adapter",
            "version": self.version,
            "description": self.description,
            "state": self.state.value,
        }

    def get_subscribed_events(self) -> list[EventType]:
        """
        Get list of subscribed event types.

        Returns:
            List of event types
        """
        return list(self._subscribed_events.keys())
