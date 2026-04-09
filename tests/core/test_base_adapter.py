"""
Unit tests for enhanced BaseAdapter.
"""

from unittest.mock import Mock

import pytest

from learning_assistant.core.base_adapter import (
    BaseAdapter,
    AdapterState,
    AdapterStatus,
)
from learning_assistant.core.event_bus import EventBus, Event, EventType
from tests.core.adapter_test_framework import (
    MockAdapter,
    AdapterTestMixin,
    EventSubscriberMixin,
)


class TestAdapterState:
    """Test AdapterState enum."""

    def test_state_values(self) -> None:
        """Test state enum values."""
        assert AdapterState.UNINITIALIZED.value == "uninitialized"
        assert AdapterState.INITIALIZING.value == "initializing"
        assert AdapterState.READY.value == "ready"
        assert AdapterState.ERROR.value == "error"
        assert AdapterState.SHUTTING_DOWN.value == "shutting_down"


class TestAdapterStatus:
    """Test AdapterStatus dataclass."""

    def test_status_creation(self) -> None:
        """Test creating status."""
        status = AdapterStatus(
            state=AdapterState.READY,
            name="test",
            message="Test adapter",
        )

        assert status.state == AdapterState.READY
        assert status.name == "test"
        assert status.message == "Test adapter"
        assert status.error_count == 0
        assert status.last_error is None

    def test_status_with_errors(self) -> None:
        """Test status with error information."""
        status = AdapterStatus(
            state=AdapterState.ERROR,
            name="error_adapter",
            message="Error state",
            error_count=3,
            last_error="Connection failed",
        )

        assert status.error_count == 3
        assert status.last_error == "Connection failed"


class TestBaseAdapterLifecycle:
    """Test adapter lifecycle helpers."""

    def test_initial_state(self) -> None:
        """Test initial state is UNINITIALIZED."""
        adapter = MockAdapter()

        assert adapter.state == AdapterState.UNINITIALIZED

    def test_set_initializing(self) -> None:
        """Test setting INITIALIZING state."""
        adapter = MockAdapter()

        adapter._set_initializing()

        assert adapter.state == AdapterState.INITIALIZING

    def test_set_ready(self) -> None:
        """Test setting READY state."""
        adapter = MockAdapter()

        adapter._set_ready()

        assert adapter.state == AdapterState.READY

    def test_set_error(self) -> None:
        """Test setting ERROR state."""
        adapter = MockAdapter()

        adapter._set_error("Test error")

        assert adapter.state == AdapterState.ERROR
        assert adapter._error_count == 1
        assert adapter._last_error == "Test error"

    def test_set_shutting_down(self) -> None:
        """Test setting SHUTTING_DOWN state."""
        adapter = MockAdapter()

        adapter._set_shutting_down()

        assert adapter.state == AdapterState.SHUTTING_DOWN

    def test_get_status(self) -> None:
        """Test getting adapter status."""
        adapter = MockAdapter()
        adapter._set_ready()

        status = adapter.get_status()

        assert isinstance(status, AdapterStatus)
        assert status.state == AdapterState.READY
        assert status.name == "mock_adapter"

    def test_state_message(self) -> None:
        """Test state message generation."""
        adapter = MockAdapter()

        # UNINITIALIZED
        message = adapter._get_state_message()
        assert "not initialized" in message

        # READY
        adapter._set_ready()
        message = adapter._get_state_message()
        assert "ready for operation" in message

        # ERROR
        adapter._set_error("Test error")
        message = adapter._get_state_message()
        assert "error state" in message


class TestBaseAdapterEventSubscription:
    """Test event subscription helpers."""

    def test_subscribe_to_event(self) -> None:
        """Test subscribing to event."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)

        assert EventType.CONTENT_PUSHED in adapter.get_subscribed_events()
        assert event_bus.has_subscribers(EventType.CONTENT_PUSHED)

    def test_subscribe_with_custom_handler(self) -> None:
        """Test subscribing with custom handler."""
        adapter = MockAdapter()
        event_bus = EventBus()
        custom_handler = Mock()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.VIDEO_SUMMARIZED, handler=custom_handler)

        # Publish event
        event = Event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={},
        )
        event_bus.publish(event)

        # Custom handler should be called
        custom_handler.assert_called_once_with(event)

    def test_unsubscribe_from_event(self) -> None:
        """Test unsubscribing from event."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)
        adapter.unsubscribe_from_event(EventType.CONTENT_PUSHED)

        assert EventType.CONTENT_PUSHED not in adapter.get_subscribed_events()
        assert not event_bus.has_subscribers(EventType.CONTENT_PUSHED)

    def test_unsubscribe_from_all_events(self) -> None:
        """Test unsubscribing from all events."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)
        adapter.subscribe_to_event(EventType.VIDEO_SUMMARIZED)

        adapter.unsubscribe_from_all_events()

        assert len(adapter.get_subscribed_events()) == 0

    def test_default_event_handler(self) -> None:
        """Test default event handler."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)

        # Publish event
        event = Event(
            event_type=EventType.CONTENT_PUSHED,
            source="test",
            data={"key": "value"},
        )
        event_bus.publish(event)

        # Event should be handled
        assert adapter.get_event_count() == 1

    def test_subscribe_without_event_bus(self) -> None:
        """Test subscribing without event bus."""
        adapter = MockAdapter()

        # Should not raise error, just log warning
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)

        assert EventType.CONTENT_PUSHED not in adapter.get_subscribed_events()


class TestBaseAdapterConfigHelpers:
    """Test configuration helpers."""

    def test_validate_config_default(self) -> None:
        """Test default validate_config."""
        adapter = MockAdapter()

        # Default implementation always returns True
        assert adapter.validate_config({"any": "config"})

    def test_get_config_value(self) -> None:
        """Test getting config value."""
        adapter = MockAdapter()
        adapter.config = {"key1": "value1", "key2": 123}

        # Get existing value
        value = adapter.get_config_value("key1")
        assert value == "value1"

        # Get with default
        value = adapter.get_config_value("missing", default="default")
        assert value == "default"

    def test_get_config_value_required(self) -> None:
        """Test getting required config value."""
        adapter = MockAdapter()
        adapter.config = {"key": "value"}

        # Missing required key
        with pytest.raises(ValueError, match="Required config key"):
            adapter.get_config_value("missing", required=True)


class TestBaseAdapterErrorTracking:
    """Test error tracking helpers."""

    def test_record_error(self) -> None:
        """Test recording error."""
        adapter = MockAdapter()
        adapter._set_ready()

        adapter.record_error("Test error")

        # State should not change
        assert adapter.state == AdapterState.READY
        # But error should be tracked
        assert adapter._error_count == 1
        assert adapter._last_error == "Test error"

    def test_clear_errors(self) -> None:
        """Test clearing errors."""
        adapter = MockAdapter()
        adapter.record_error("Error 1")
        adapter.record_error("Error 2")

        adapter.clear_errors()

        assert adapter._error_count == 0
        assert adapter._last_error is None

    def test_multiple_errors(self) -> None:
        """Test tracking multiple errors."""
        adapter = MockAdapter()

        adapter.record_error("Error 1")
        adapter.record_error("Error 2")
        adapter.record_error("Error 3")

        assert adapter._error_count == 3
        assert adapter._last_error == "Error 3"


class TestBaseAdapterMetadata:
    """Test adapter metadata."""

    def test_get_metadata(self) -> None:
        """Test getting metadata."""
        adapter = MockAdapter()
        adapter._set_ready()

        metadata = adapter.get_metadata()

        assert metadata["name"] == "mock_adapter"
        assert metadata["type"] == "adapter"
        assert metadata["version"] == "1.0.0"
        assert metadata["state"] == "ready"

    def test_get_subscribed_events(self) -> None:
        """Test getting subscribed events."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)
        adapter.subscribe_to_event(EventType.VIDEO_SUMMARIZED)

        events = adapter.get_subscribed_events()

        assert len(events) == 2
        assert EventType.CONTENT_PUSHED in events
        assert EventType.VIDEO_SUMMARIZED in events


class TestMockAdapter:
    """Test MockAdapter functionality."""

    def test_mock_adapter_creation(self) -> None:
        """Test creating MockAdapter."""
        adapter = MockAdapter()

        assert adapter.name == "mock_adapter"
        assert adapter.state == AdapterState.UNINITIALIZED

    def test_mock_adapter_initialize(self) -> None:
        """Test MockAdapter initialization."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({"setting": "value"}, event_bus)

        assert adapter.state == AdapterState.READY
        assert adapter.config == {"setting": "value"}
        assert adapter.event_bus == event_bus

        # Should be recorded
        calls = adapter.get_calls_for_method("initialize")
        assert len(calls) == 1

    def test_mock_adapter_push_content(self) -> None:
        """Test MockAdapter push_content."""
        adapter = MockAdapter()

        result = adapter.push_content({"title": "Test"})

        assert result is True  # Default result

        # Should be recorded
        calls = adapter.get_calls_for_method("push_content")
        assert len(calls) == 1
        assert calls[0].args[0] == {"title": "Test"}

    def test_mock_adapter_sync_data(self) -> None:
        """Test MockAdapter sync_data."""
        adapter = MockAdapter()

        result = adapter.sync_data("history", {"data": "test"})

        assert result is True  # Default result

        # Should be recorded
        calls = adapter.get_calls_for_method("sync_data")
        assert len(calls) == 1

    def test_mock_adapter_handle_trigger(self) -> None:
        """Test MockAdapter handle_trigger."""
        adapter = MockAdapter()

        result = adapter.handle_trigger({"trigger": "data"})

        assert result == {"status": "success"}  # Default result

        # Should be recorded
        calls = adapter.get_calls_for_method("handle_trigger")
        assert len(calls) == 1

    def test_mock_adapter_set_results(self) -> None:
        """Test setting MockAdapter results."""
        adapter = MockAdapter()

        # Set custom results
        adapter.set_push_content_result(False)
        adapter.set_sync_data_result(False)
        adapter.set_handle_trigger_result({"status": "custom"})

        # Test results
        assert adapter.push_content({}) is False
        assert adapter.sync_data("test", {}) is False
        assert adapter.handle_trigger({}) == {"status": "custom"}

    def test_mock_adapter_simulate_error(self) -> None:
        """Test simulating errors."""
        adapter = MockAdapter()

        # Simulate error
        adapter.simulate_error("push_content", Exception("Network error"))

        # Should fail
        result = adapter.push_content({"test": "data"})
        assert result is False
        assert adapter._last_error == "Network error"

    def test_mock_adapter_event_handling(self) -> None:
        """Test MockAdapter event handling."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)

        # Publish event
        event = Event(
            event_type=EventType.CONTENT_PUSHED,
            source="test",
            data={"key": "value"},
        )
        event_bus.publish(event)

        # Should be handled
        assert adapter.get_event_count() == 1
        handled_events = adapter.get_handled_events()
        assert handled_events[0] == event

    def test_mock_adapter_disable_event_handling(self) -> None:
        """Test disabling event handling."""
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)

        # Disable handling
        adapter.set_event_handling(False)

        # Publish event
        event = Event(
            event_type=EventType.CONTENT_PUSHED,
            source="test",
            data={},
        )
        event_bus.publish(event)

        # Should not be handled
        assert adapter.get_event_count() == 0

    def test_mock_adapter_clear_history(self) -> None:
        """Test clearing history."""
        adapter = MockAdapter()

        adapter.push_content({"test": "1"})
        adapter.push_content({"test": "2"})

        # Clear history
        adapter.clear_history()

        assert len(adapter.get_call_history()) == 0


class TestAdapterTestMixin:
    """Test AdapterTestMixin utilities."""

    def test_create_mock_adapter(self) -> None:
        """Test creating mock adapter with mixin."""
        mixin = AdapterTestMixin()

        adapter = mixin.create_mock_adapter()

        assert isinstance(adapter, MockAdapter)

    def test_create_event_bus(self) -> None:
        """Test creating event bus with mixin."""
        mixin = AdapterTestMixin()

        event_bus = mixin.create_event_bus()

        assert isinstance(event_bus, EventBus)

    def test_create_test_event(self) -> None:
        """Test creating test event."""
        mixin = AdapterTestMixin()

        event = mixin.create_test_event(
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test_source",
            data={"key": "value"},
        )

        assert event.event_type == EventType.VIDEO_SUMMARIZED
        assert event.source == "test_source"
        assert event.data == {"key": "value"}

    def test_assert_adapter_state(self) -> None:
        """Test assert_adapter_state."""
        mixin = AdapterTestMixin()
        adapter = MockAdapter()
        adapter._set_ready()

        # Should pass
        mixin.assert_adapter_state(adapter, AdapterState.READY)

        # Should fail
        with pytest.raises(AssertionError):
            mixin.assert_adapter_state(adapter, AdapterState.ERROR)

    def test_assert_adapter_ready(self) -> None:
        """Test assert_adapter_ready."""
        mixin = AdapterTestMixin()
        adapter = MockAdapter()
        adapter._set_ready()

        mixin.assert_adapter_ready(adapter)

    def test_assert_adapter_error(self) -> None:
        """Test assert_adapter_error."""
        mixin = AdapterTestMixin()
        adapter = MockAdapter()
        adapter._set_error("Test error")

        mixin.assert_adapter_error(adapter)

    def test_assert_no_errors(self) -> None:
        """Test assert_no_errors."""
        mixin = AdapterTestMixin()
        adapter = MockAdapter()

        mixin.assert_no_errors(adapter)

        # With errors
        adapter.record_error("Test")
        with pytest.raises(AssertionError):
            mixin.assert_no_errors(adapter)

    def test_assert_method_called(self) -> None:
        """Test assert_method_called."""
        mixin = AdapterTestMixin()
        adapter = MockAdapter()

        adapter.push_content({"test": "data"})

        mixin.assert_method_called(adapter, "push_content")

        # Not called enough times
        with pytest.raises(AssertionError):
            mixin.assert_method_called(adapter, "push_content", min_calls=2)


class TestEventSubscriberMixin:
    """Test EventSubscriberMixin utilities."""

    def test_assert_event_subscribed(self) -> None:
        """Test assert_event_subscribed."""
        mixin = EventSubscriberMixin()
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)

        mixin.assert_event_subscribed(adapter, EventType.CONTENT_PUSHED)

        # Not subscribed
        with pytest.raises(AssertionError):
            mixin.assert_event_subscribed(adapter, EventType.VIDEO_SUMMARIZED)

    def test_assert_event_not_subscribed(self) -> None:
        """Test assert_event_not_subscribed."""
        mixin = EventSubscriberMixin()
        adapter = MockAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)

        mixin.assert_event_not_subscribed(adapter, EventType.CONTENT_PUSHED)

        # Subscribed
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)
        with pytest.raises(AssertionError):
            mixin.assert_event_not_subscribed(adapter, EventType.CONTENT_PUSHED)

    def test_publish_test_event(self) -> None:
        """Test publish_test_event."""
        mixin = EventSubscriberMixin()
        event_bus = EventBus()

        event = mixin.publish_test_event(
            event_bus=event_bus,
            event_type=EventType.VIDEO_SUMMARIZED,
            source="test",
            data={"key": "value"},
        )

        assert event.event_type == EventType.VIDEO_SUMMARIZED
        assert event.source == "test"


class TestFeishuAdapter:
    """Test FeishuAdapter placeholder."""

    def test_feishu_adapter_creation(self) -> None:
        """Test creating FeishuAdapter."""
        adapter = FeishuAdapter()

        assert adapter.name == "feishu"
        assert adapter.description == "Feishu (飞书) platform adapter for notifications and document sync"
        assert adapter.state == AdapterState.UNINITIALIZED

    def test_feishu_adapter_initialize(self) -> None:
        """Test FeishuAdapter initialization."""
        adapter = FeishuAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)

        assert adapter.state == AdapterState.READY
        assert adapter.event_bus == event_bus

    def test_feishu_adapter_placeholder_methods(self) -> None:
        """Test placeholder methods."""
        adapter = FeishuAdapter()

        # All methods should return False/not implemented
        assert adapter.push_content({}) is False
        assert adapter.sync_data("test", {}) is False
        assert adapter.handle_trigger({}) == {"status": "not_implemented"}

    def test_feishu_adapter_cleanup(self) -> None:
        """Test FeishuAdapter cleanup."""
        adapter = FeishuAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)
        adapter.subscribe_to_event(EventType.CONTENT_PUSHED)
        adapter.cleanup()

        assert adapter.state == AdapterState.UNINITIALIZED
        assert len(adapter.get_subscribed_events()) == 0