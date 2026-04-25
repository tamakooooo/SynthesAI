"""
Event Bus for Learning Assistant.

This module provides an event-driven communication system between modules and adapters.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger


class EventType(Enum):
    """
    Event types for Learning Assistant event bus.
    """

    # Video processing events
    VIDEO_DOWNLOADED = "video.downloaded"
    VIDEO_TRANSCRIBED = "video.transcribed"
    VIDEO_SUMMARIZED = "video.summarized"

    # Link processing events
    LINK_SCRAPED = "link.scraped"
    LINK_PROCESSED = "link.processed"

    # Vocabulary events
    VOCABULARY_EXTRACTED = "vocabulary.extracted"

    # Adapter events
    CONTENT_PUSHED = "adapter.content_pushed"
    SYNC_COMPLETED = "adapter.sync_completed"

    # System events
    ERROR_OCCURRED = "system.error"
    TASK_STARTED = "system.task_started"
    TASK_COMPLETED = "system.task_completed"
    TASK_INTERRUPTED = "system.task_interrupted"


@dataclass
class Event:
    """
    Event data structure.
    """

    event_type: EventType
    source: str  # Module or adapter name
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """
    Event Bus for Learning Assistant.

    Provides:
    - Publish-Subscribe pattern
    - Asynchronous event handling
    - Event history tracking
    """

    def __init__(self, max_history: int = 1000) -> None:
        """
        Initialize EventBus.

        Args:
            max_history: Maximum number of events to keep in history
        """
        self.subscribers: dict[EventType, list[Callable]] = {}
        self.event_history: list[Event] = []
        self.max_history = max_history
        logger.info(f"EventBus initialized with max_history={max_history}")

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to
            handler: Handler function to call when event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        if handler not in self.subscribers[event_type]:
            self.subscribers[event_type].append(handler)
            handler_name = getattr(handler, "__name__", str(handler))
            logger.debug(f"Handler {handler_name} subscribed to {event_type.value}")
        else:
            handler_name = getattr(handler, "__name__", str(handler))
            logger.warning(
                f"Handler {handler_name} already subscribed to {event_type.value}"
            )

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove
        """
        if event_type not in self.subscribers:
            logger.warning(f"No subscribers for event type {event_type.value}")
            return

        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            handler_name = getattr(handler, "__name__", str(handler))
            logger.debug(f"Handler {handler_name} unsubscribed from {event_type.value}")

            # Clean up empty subscriber lists
            if not self.subscribers[event_type]:
                del self.subscribers[event_type]
        else:
            handler_name = getattr(handler, "__name__", str(handler))
            logger.warning(
                f"Handler {handler_name} not subscribed to {event_type.value}"
            )

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers synchronously.

        Args:
            event: Event to publish
        """
        logger.info(f"Publishing event {event.event_type.value} from {event.source}")

        # Add to event history
        self._add_to_history(event)

        # Get subscribers for this event type
        handlers = self.subscribers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"No subscribers for event type {event.event_type.value}")
            return

        # Call all handlers
        for handler in handlers:
            try:
                handler(event)
                handler_name = getattr(handler, "__name__", str(handler))
                logger.debug(f"Handler {handler_name} called successfully")
            except Exception as e:
                handler_name = getattr(handler, "__name__", str(handler))
                logger.error(
                    f"Error in handler {handler_name} for event {event.event_type.value}: {e}"
                )

    async def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously to all subscribers.

        Supports both sync and async handlers.

        Args:
            event: Event to publish
        """
        logger.info(
            f"Publishing async event {event.event_type.value} from {event.source}"
        )

        # Add to event history
        self._add_to_history(event)

        # Get subscribers for this event type
        handlers = self.subscribers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"No subscribers for event type {event.event_type.value}")
            return

        # Call all handlers asynchronously
        tasks = []
        for handler in handlers:
            try:
                # Check if handler is async
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    # Run sync handler in executor to avoid blocking
                    loop = asyncio.get_running_loop()
                    tasks.append(loop.run_in_executor(None, handler, event))
            except Exception as e:
                handler_name = getattr(handler, "__name__", str(handler))
                logger.error(
                    f"Error preparing handler {handler_name} for async execution: {e}"
                )

        # Wait for all handlers to complete
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.debug(
                    f"All handlers completed for event {event.event_type.value}"
                )
            except Exception as e:
                logger.error(f"Error in async event handling: {e}")

    def get_event_history(self, event_type: EventType | None = None) -> list[Event]:
        """
        Get event history, optionally filtered by event type.

        Args:
            event_type: Event type to filter by (optional)

        Returns:
            List of events
        """
        if event_type is None:
            return self.event_history.copy()

        return [event for event in self.event_history if event.event_type == event_type]

    def clear_history(self) -> None:
        """
        Clear event history.
        """
        logger.info("Clearing event history")
        self.event_history.clear()

    def _add_to_history(self, event: Event) -> None:
        """
        Add event to history, maintaining max_history limit.

        Args:
            event: Event to add
        """
        self.event_history.append(event)

        # Remove oldest events if we exceed max_history
        if len(self.event_history) > self.max_history:
            removed_count = len(self.event_history) - self.max_history
            self.event_history = self.event_history[-self.max_history :]
            logger.debug(f"Removed {removed_count} old events from history")

    def get_subscriber_count(self, event_type: EventType | None = None) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: Event type to check (optional, returns total if None)

        Returns:
            Number of subscribers
        """
        if event_type is None:
            return sum(len(handlers) for handlers in self.subscribers.values())

        return len(self.subscribers.get(event_type, []))

    def has_subscribers(self, event_type: EventType) -> bool:
        """
        Check if an event type has any subscribers.

        Args:
            event_type: Event type to check

        Returns:
            True if there are subscribers, False otherwise
        """
        return event_type in self.subscribers and len(self.subscribers[event_type]) > 0
