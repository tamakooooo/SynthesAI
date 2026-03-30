"""
Event Bus for Learning Assistant.

This module provides an event-driven communication system between modules and adapters.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List
from datetime import datetime
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
    data: Dict[str, Any]
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """
    Event Bus for Learning Assistant.

    Provides:
    - Publish-Subscribe pattern
    - Asynchronous event handling
    - Event history tracking
    """

    def __init__(self) -> None:
        """
        Initialize EventBus.
        """
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []
        logger.info("EventBus initialized")

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to
            handler: Handler function to call when event is published
        """
        # TODO: Implement subscription mechanism (Week 1 Day 5)
        pass

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove
        """
        # TODO: Implement unsubscription mechanism (Week 1 Day 5)
        pass

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        # TODO: Implement synchronous event publishing (Week 1 Day 5)
        pass

    async def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously to all subscribers.

        Args:
            event: Event to publish
        """
        # TODO: Implement asynchronous event publishing (Week 1 Day 5)
        pass

    def get_event_history(self, event_type: EventType | None = None) -> List[Event]:
        """
        Get event history, optionally filtered by event type.

        Args:
            event_type: Event type to filter by (optional)

        Returns:
            List of events
        """
        # TODO: Implement event history retrieval (Week 1 Day 5)
        return []

    def clear_history(self) -> None:
        """
        Clear event history.
        """
        logger.info("Clearing event history")
        self.event_history.clear()