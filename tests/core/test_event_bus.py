"""
Unit tests for EventBus.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from learning_assistant.core.event_bus import Event, EventBus, EventType


class TestEventType:
    """Test EventType enumeration."""

    def test_event_type_values(self) -> None:
        """Test EventType enum values."""
        assert EventType.VIDEO_DOWNLOADED.value == "video.downloaded"
        assert EventType.VIDEO_TRANSCRIBED.value == "video.transcribed"
        assert EventType.VIDEO_SUMMARIZED.value == "video.summarized"
        assert EventType.LINK_SCRAPED.value == "link.scraped"
        assert EventType.VOCABULARY_EXTRACTED.value == "vocabulary.extracted"
        assert EventType.ERROR_OCCURRED.value == "system.error"

    def test_event_type_count(self) -> None:
        """Test total number of event types."""
        event_types = list(EventType)
        assert len(event_types) == 12


class TestEvent:
    """Test Event dataclass."""

    def test_event_creation_basic(self) -> None:
        """Test creating an event with basic fields."""
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="video_summary",
            data={"video_id": "123", "title": "Test Video"},
        )

        assert event.event_type == EventType.VIDEO_SUMMARIZED
        assert event.source == "video_summary"
        assert event.data == {"video_id": "123", "title": "Test Video"}
        assert isinstance(event.timestamp, datetime)
        assert event.metadata == {}

    def test_event_creation_with_all_fields(self) -> None:
        """Test creating an event with all fields."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        metadata = {"user_id": "user123", "session_id": "session456"}

        event = Event(
            event_type=EventType.ERROR_OCCURRED,
            source="test_module",
            data={"error": "Test error"},
            timestamp=timestamp,
            metadata=metadata,
        )

        assert event.timestamp == timestamp
        assert event.metadata == metadata

    def test_event_timestamp_auto_generated(self) -> None:
        """Test that timestamp is auto-generated if not provided."""
        before = datetime.now()
        event = Event(event_type=EventType.VIDEO_DOWNLOADED, source="test", data={})
        after = datetime.now()

        assert before <= event.timestamp <= after

    def test_event_metadata_default_empty_dict(self) -> None:
        """Test that metadata defaults to empty dict."""
        event = Event(event_type=EventType.VIDEO_TRANSCRIBED, source="test", data={})

        assert event.metadata == {}
        assert isinstance(event.metadata, dict)


class TestEventBusInit:
    """Test EventBus initialization."""

    def test_init_default_max_history(self) -> None:
        """Test EventBus initialization with default max_history."""
        event_bus = EventBus()

        assert event_bus.subscribers == {}
        assert event_bus.event_history == []
        assert event_bus.max_history == 1000

    def test_init_custom_max_history(self) -> None:
        """Test EventBus initialization with custom max_history."""
        event_bus = EventBus(max_history=500)

        assert event_bus.max_history == 500


class TestEventBusSubscribe:
    """Test EventBus subscribe functionality."""

    def test_subscribe_single_handler(self) -> None:
        """Test subscribing a single handler to an event type."""
        event_bus = EventBus()
        handler = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)

        assert EventType.VIDEO_SUMMARIZED in event_bus.subscribers
        assert handler in event_bus.subscribers[EventType.VIDEO_SUMMARIZED]

    def test_subscribe_multiple_handlers_same_event(self) -> None:
        """Test subscribing multiple handlers to the same event type."""
        event_bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler1)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler2)

        assert len(event_bus.subscribers[EventType.VIDEO_SUMMARIZED]) == 2
        assert handler1 in event_bus.subscribers[EventType.VIDEO_SUMMARIZED]
        assert handler2 in event_bus.subscribers[EventType.VIDEO_SUMMARIZED]

    def test_subscribe_same_handler_twice(self) -> None:
        """Test subscribing the same handler twice (should be idempotent)."""
        event_bus = EventBus()
        handler = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)

        # Should only appear once
        assert len(event_bus.subscribers[EventType.VIDEO_SUMMARIZED]) == 1

    def test_subscribe_multiple_event_types(self) -> None:
        """Test subscribing to multiple event types."""
        event_bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler1)
        event_bus.subscribe(EventType.LINK_PROCESSED, handler2)

        assert EventType.VIDEO_SUMMARIZED in event_bus.subscribers
        assert EventType.LINK_PROCESSED in event_bus.subscribers
        assert handler1 in event_bus.subscribers[EventType.VIDEO_SUMMARIZED]
        assert handler2 in event_bus.subscribers[EventType.LINK_PROCESSED]


class TestEventBusUnsubscribe:
    """Test EventBus unsubscribe functionality."""

    def test_unsubscribe_existing_handler(self) -> None:
        """Test unsubscribing an existing handler."""
        event_bus = EventBus()
        handler = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        event_bus.unsubscribe(EventType.VIDEO_SUMMARIZED, handler)

        assert EventType.VIDEO_SUMMARIZED not in event_bus.subscribers

    def test_unsubscribe_nonexistent_handler(self) -> None:
        """Test unsubscribing a handler that was never subscribed."""
        event_bus = EventBus()
        handler = Mock()

        # Should not raise error
        event_bus.unsubscribe(EventType.VIDEO_SUMMARIZED, handler)

    def test_unsubscribe_from_nonexistent_event_type(self) -> None:
        """Test unsubscribing from an event type with no subscribers."""
        event_bus = EventBus()
        handler = Mock()

        # Should not raise error
        event_bus.unsubscribe(EventType.VIDEO_SUMMARIZED, handler)

    def test_unsubscribe_one_of_multiple_handlers(self) -> None:
        """Test unsubscribing one handler while keeping others."""
        event_bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler1)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler2)
        event_bus.unsubscribe(EventType.VIDEO_SUMMARIZED, handler1)

        assert EventType.VIDEO_SUMMARIZED in event_bus.subscribers
        assert handler1 not in event_bus.subscribers[EventType.VIDEO_SUMMARIZED]
        assert handler2 in event_bus.subscribers[EventType.VIDEO_SUMMARIZED]


class TestEventBusPublish:
    """Test EventBus publish functionality."""

    def test_publish_to_single_subscriber(self) -> None:
        """Test publishing an event to a single subscriber."""
        event_bus = EventBus()
        handler = Mock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        event_bus.publish(event)

        handler.assert_called_once_with(event)

    def test_publish_to_multiple_subscribers(self) -> None:
        """Test publishing an event to multiple subscribers."""
        event_bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler1)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler2)
        event_bus.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    def test_publish_no_subscribers(self) -> None:
        """Test publishing an event with no subscribers."""
        event_bus = EventBus()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        # Should not raise error
        event_bus.publish(event)

    def test_publish_handler_raises_exception(self) -> None:
        """Test publishing when handler raises an exception."""
        event_bus = EventBus()
        failing_handler = Mock(side_effect=Exception("Handler failed"))
        working_handler = Mock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, failing_handler)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, working_handler)
        event_bus.publish(event)

        # Both handlers should be called despite exception
        failing_handler.assert_called_once_with(event)
        working_handler.assert_called_once_with(event)

    def test_publish_adds_to_history(self) -> None:
        """Test that publishing adds event to history."""
        event_bus = EventBus()
        handler = Mock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        event_bus.publish(event)

        assert len(event_bus.event_history) == 1
        assert event_bus.event_history[0] == event


class TestEventBusPublishAsync:
    """Test EventBus async publish functionality."""

    @pytest.mark.asyncio
    async def test_publish_async_to_sync_handler(self) -> None:
        """Test async publishing to a sync handler."""
        event_bus = EventBus()
        handler = Mock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        await event_bus.publish_async(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_async_to_async_handler(self) -> None:
        """Test async publishing to an async handler."""
        event_bus = EventBus()
        handler = AsyncMock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        await event_bus.publish_async(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_async_to_multiple_handlers(self) -> None:
        """Test async publishing to multiple mixed handlers."""
        event_bus = EventBus()
        sync_handler = Mock()
        async_handler = AsyncMock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, sync_handler)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, async_handler)
        await event_bus.publish_async(event)

        sync_handler.assert_called_once_with(event)
        async_handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_async_adds_to_history(self) -> None:
        """Test that async publishing adds event to history."""
        event_bus = EventBus()
        handler = Mock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        await event_bus.publish_async(event)

        assert len(event_bus.event_history) == 1
        assert event_bus.event_history[0] == event


class TestEventBusHistory:
    """Test EventBus history functionality."""

    def test_get_event_history_all(self) -> None:
        """Test getting all event history."""
        event_bus = EventBus()
        event1 = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"id": 1},
        )
        event2 = Event(
            event_type=EventType.LINK_PROCESSED,
            source="test",
            data={"id": 2},
        )

        event_bus.publish(event1)
        event_bus.publish(event2)

        history = event_bus.get_event_history()

        assert len(history) == 2
        assert event1 in history
        assert event2 in history

    def test_get_event_history_filtered_by_type(self) -> None:
        """Test getting event history filtered by event type."""
        event_bus = EventBus()
        event1 = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"id": 1},
        )
        event2 = Event(
            event_type=EventType.LINK_PROCESSED,
            source="test",
            data={"id": 2},
        )
        event3 = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"id": 3},
        )

        event_bus.publish(event1)
        event_bus.publish(event2)
        event_bus.publish(event3)

        history = event_bus.get_event_history(EventType.VIDEO_SUMMARIZED)

        assert len(history) == 2
        assert event1 in history
        assert event3 in history
        assert event2 not in history

    def test_get_event_history_empty(self) -> None:
        """Test getting event history when empty."""
        event_bus = EventBus()

        history = event_bus.get_event_history()

        assert history == []

    def test_clear_history(self) -> None:
        """Test clearing event history."""
        event_bus = EventBus()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={},
        )

        event_bus.publish(event)
        event_bus.clear_history()

        assert event_bus.event_history == []

    def test_max_history_limit(self) -> None:
        """Test that event history respects max_history limit."""
        event_bus = EventBus(max_history=5)

        # Publish 10 events
        for i in range(10):
            event = Event(
                event_type=EventType.VIDEO_SUMMARIZED,
                source="test",
                data={"id": i},
            )
            event_bus.publish(event)

        # Should only keep last 5 events
        assert len(event_bus.event_history) == 5

        # Should be the most recent events
        ids = [event.data["id"] for event in event_bus.event_history]
        assert ids == [5, 6, 7, 8, 9]


class TestEventBusHelperMethods:
    """Test EventBus helper methods."""

    def test_get_subscriber_count_total(self) -> None:
        """Test getting total subscriber count."""
        event_bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler1)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler2)
        event_bus.subscribe(EventType.LINK_PROCESSED, handler3)

        count = event_bus.get_subscriber_count()

        assert count == 3

    def test_get_subscriber_count_by_event_type(self) -> None:
        """Test getting subscriber count for specific event type."""
        event_bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler1)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler2)
        event_bus.subscribe(EventType.LINK_PROCESSED, handler3)

        count = event_bus.get_subscriber_count(EventType.VIDEO_SUMMARIZED)

        assert count == 2

    def test_has_subscribers_true(self) -> None:
        """Test has_subscribers returns True when there are subscribers."""
        event_bus = EventBus()
        handler = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)

        assert event_bus.has_subscribers(EventType.VIDEO_SUMMARIZED) is True

    def test_has_subscribers_false(self) -> None:
        """Test has_subscribers returns False when there are no subscribers."""
        event_bus = EventBus()

        assert event_bus.has_subscribers(EventType.VIDEO_SUMMARIZED) is False


class TestEventBusIntegration:
    """Integration tests for EventBus."""

    def test_full_workflow_subscribe_publish_unsubscribe(self) -> None:
        """Test complete workflow: subscribe, publish, unsubscribe."""
        event_bus = EventBus()
        handler = Mock()
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"video_id": "123"},
        )

        # Subscribe
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)
        assert event_bus.has_subscribers(EventType.VIDEO_SUMMARIZED)

        # Publish
        event_bus.publish(event)
        handler.assert_called_once_with(event)

        # Unsubscribe
        event_bus.unsubscribe(EventType.VIDEO_SUMMARIZED, handler)
        assert not event_bus.has_subscribers(EventType.VIDEO_SUMMARIZED)

    @pytest.mark.asyncio
    async def test_async_workflow(self) -> None:
        """Test async event handling workflow."""
        event_bus = EventBus()

        # Track execution order
        execution_order = []

        async def async_handler(event: Event) -> None:
            execution_order.append("async")

        def sync_handler(event: Event) -> None:
            execution_order.append("sync")

        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={},
        )

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, async_handler)
        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, sync_handler)

        await event_bus.publish_async(event)

        # Both handlers should have been called
        assert len(execution_order) == 2
        assert "async" in execution_order
        assert "sync" in execution_order

    def test_multiple_event_types_workflow(self) -> None:
        """Test handling multiple different event types."""
        event_bus = EventBus()

        video_handler = Mock()
        link_handler = Mock()

        event_bus.subscribe(EventType.VIDEO_SUMMARIZED, video_handler)
        event_bus.subscribe(EventType.LINK_PROCESSED, link_handler)

        video_event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="video_module",
            data={"video_id": "123"},
        )
        link_event = Event(
            event_type=EventType.LINK_PROCESSED,
            source="link_module",
            data={"url": "https://example.com"},
        )

        event_bus.publish(video_event)
        event_bus.publish(link_event)

        video_handler.assert_called_once_with(video_event)
        link_handler.assert_called_once_with(link_event)

        # Verify both events are in history
        history = event_bus.get_event_history()
        assert len(history) == 2
