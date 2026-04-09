"""
Adapter Test Framework for Learning Assistant.

This module provides testing utilities for adapter development.
"""

from dataclasses import dataclass, field
from typing import Any, Callable
from unittest.mock import Mock

from loguru import logger

from learning_assistant.core.base_adapter import BaseAdapter, AdapterState, AdapterStatus
from learning_assistant.core.event_bus import EventBus, Event, EventType


@dataclass
class AdapterCallRecord:
    """
    Record of a method call on MockAdapter.
    """

    method_name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    result: Any
    timestamp: float


class MockAdapter(BaseAdapter):
    """
    Mock adapter for testing purposes.

    Features:
    - Tracks all method calls
    - Simulates configurable responses
    - Event subscription tracking
    - Error simulation
    """

    def __init__(self) -> None:
        """Initialize mock adapter."""
        super().__init__()
        self._call_history: list[AdapterCallRecord] = []

        # Configurable responses
        self._push_content_result: bool = True
        self._sync_data_result: bool = True
        self._handle_trigger_result: dict[str, Any] = {"status": "success"}

        # Error simulation
        self._simulate_errors: dict[str, Exception] = {}

        # Event handling
        self._event_handling_enabled: bool = True
        self._handled_events: list[Event] = []

        logger.info("MockAdapter created for testing")

    @property
    def name(self) -> str:
        return "mock_adapter"

    @property
    def description(self) -> str:
        return "Mock adapter for testing"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """Initialize mock adapter."""
        self._record_call("initialize", (config, event_bus), {})

        # Check for simulated error
        if "initialize" in self._simulate_errors:
            self._set_error(str(self._simulate_errors["initialize"]))
            return

        # Normal initialization
        self.config = config
        self.event_bus = event_bus
        self._set_ready()

    def push_content(self, content: dict[str, Any]) -> bool:
        """Push content (mock)."""
        self._record_call("push_content", (content,), {})

        # Check for simulated error
        if "push_content" in self._simulate_errors:
            self.record_error(str(self._simulate_errors["push_content"]))
            return False

        return self._push_content_result

    def sync_data(self, data_type: str, data: dict[str, Any]) -> bool:
        """Sync data (mock)."""
        self._record_call("sync_data", (data_type, data), {})

        # Check for simulated error
        if "sync_data" in self._simulate_errors:
            self.record_error(str(self._simulate_errors["sync_data"]))
            return False

        return self._sync_data_result

    def handle_trigger(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        """Handle trigger (mock)."""
        self._record_call("handle_trigger", (trigger_data,), {})

        # Check for simulated error
        if "handle_trigger" in self._simulate_errors:
            self.record_error(str(self._simulate_errors["handle_trigger"]))
            return {"status": "error"}

        return self._handle_trigger_result

    def cleanup(self) -> None:
        """Cleanup (mock)."""
        self._record_call("cleanup", (), {})
        self._set_shutting_down()
        self.unsubscribe_from_all_events()
        self.state = AdapterState.UNINITIALIZED

    def default_event_handler(self, event: Event) -> None:
        """Default event handler (mock)."""
        if not self._event_handling_enabled:
            return

        # Record the event
        self._handled_events.append(event)

        # Call parent implementation
        super().default_event_handler(event)

    # Test control methods

    def _record_call(
        self, method_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> None:
        """
        Record a method call.

        Args:
            method_name: Method name
            args: Positional arguments
            kwargs: Keyword arguments
        """
        import time

        # Determine result (for calls that return values)
        result_map = {
            "push_content": self._push_content_result,
            "sync_data": self._sync_data_result,
            "handle_trigger": self._handle_trigger_result,
        }
        result = result_map.get(method_name, None)

        record = AdapterCallRecord(
            method_name=method_name,
            args=args,
            kwargs=kwargs,
            result=result,
            timestamp=time.time(),
        )
        self._call_history.append(record)

    def set_push_content_result(self, result: bool) -> None:
        """
        Set the result for push_content calls.

        Args:
            result: Result to return
        """
        self._push_content_result = result

    def set_sync_data_result(self, result: bool) -> None:
        """
        Set the result for sync_data calls.

        Args:
            result: Result to return
        """
        self._sync_data_result = result

    def set_handle_trigger_result(self, result: dict[str, Any]) -> None:
        """
        Set the result for handle_trigger calls.

        Args:
            result: Result to return
        """
        self._handle_trigger_result = result

    def simulate_error(self, method_name: str, exception: Exception) -> None:
        """
        Simulate an error for a specific method.

        Args:
            method_name: Method to simulate error for
            exception: Exception to simulate
        """
        self._simulate_errors[method_name] = exception

    def clear_simulated_errors(self) -> None:
        """Clear all simulated errors."""
        self._simulate_errors.clear()

    def set_event_handling(self, enabled: bool) -> None:
        """
        Enable or disable event handling.

        Args:
            enabled: Whether to handle events
        """
        self._event_handling_enabled = enabled

    # Query methods for test assertions

    def get_call_history(self) -> list[AdapterCallRecord]:
        """
        Get call history.

        Returns:
            List of call records
        """
        return self._call_history.copy()

    def get_calls_for_method(self, method_name: str) -> list[AdapterCallRecord]:
        """
        Get calls for a specific method.

        Args:
            method_name: Method name

        Returns:
            List of call records for the method
        """
        return [
            call for call in self._call_history if call.method_name == method_name
        ]

    def get_last_call(self) -> AdapterCallRecord | None:
        """
        Get last call record.

        Returns:
            Last call record or None
        """
        if self._call_history:
            return self._call_history[-1]
        return None

    def get_handled_events(self) -> list[Event]:
        """
        Get handled events.

        Returns:
            List of handled events
        """
        return self._handled_events.copy()

    def get_event_count(self) -> int:
        """
        Get number of handled events.

        Returns:
            Number of events handled
        """
        return len(self._handled_events)

    def clear_history(self) -> None:
        """Clear all history."""
        self._call_history.clear()
        self._handled_events.clear()


class AdapterTestMixin:
    """
    Mixin providing common test utilities for adapter testing.
    """

    def create_mock_adapter(self) -> MockAdapter:
        """
        Create a MockAdapter instance.

        Returns:
            MockAdapter instance
        """
        return MockAdapter()

    def create_event_bus(self) -> EventBus:
        """
        Create an EventBus instance.

        Returns:
            EventBus instance
        """
        return EventBus()

    def create_test_event(
        self,
        event_type: EventType = EventType.CONTENT_PUSHED,
        source: str = "test_source",
        data: dict[str, Any] | None = None,
    ) -> Event:
        """
        Create a test event.

        Args:
            event_type: Event type
            source: Event source
            data: Event data

        Returns:
            Event instance
        """
        return Event(
            event_type=event_type,
            source=source,
            data=data or {},
        )

    def assert_adapter_state(
        self, adapter: BaseAdapter, expected_state: AdapterState
    ) -> None:
        """
        Assert adapter state.

        Args:
            adapter: Adapter to check
            expected_state: Expected state
        """
        assert adapter.state == expected_state, (
            f"Expected state {expected_state.value}, got {adapter.state.value}"
        )

    def assert_adapter_ready(self, adapter: BaseAdapter) -> None:
        """
        Assert adapter is ready.

        Args:
            adapter: Adapter to check
        """
        self.assert_adapter_state(adapter, AdapterState.READY)

    def assert_adapter_error(self, adapter: BaseAdapter) -> None:
        """
        Assert adapter is in error state.

        Args:
            adapter: Adapter to check
        """
        self.assert_adapter_state(adapter, AdapterState.ERROR)

    def assert_no_errors(self, adapter: BaseAdapter) -> None:
        """
        Assert adapter has no errors.

        Args:
            adapter: Adapter to check
        """
        status = adapter.get_status()
        assert status.error_count == 0, f"Adapter has {status.error_count} errors"

    def assert_method_called(
        self, mock_adapter: MockAdapter, method_name: str, min_calls: int = 1
    ) -> None:
        """
        Assert method was called at least min_calls times.

        Args:
            mock_adapter: MockAdapter instance
            method_name: Method name
            min_calls: Minimum number of calls
        """
        calls = mock_adapter.get_calls_for_method(method_name)
        assert len(calls) >= min_calls, (
            f"Expected at least {min_calls} calls to {method_name}, got {len(calls)}"
        )


class EventSubscriberMixin:
    """
    Mixin providing utilities for testing event subscription.
    """

    def assert_event_subscribed(
        self, adapter: BaseAdapter, event_type: EventType
    ) -> None:
        """
        Assert adapter is subscribed to event type.

        Args:
            adapter: Adapter to check
            event_type: Event type
        """
        subscribed = adapter.get_subscribed_events()
        assert event_type in subscribed, (
            f"Adapter not subscribed to {event_type.value}"
        )

    def assert_event_not_subscribed(
        self, adapter: BaseAdapter, event_type: EventType
    ) -> None:
        """
        Assert adapter is not subscribed to event type.

        Args:
            adapter: Adapter to check
            event_type: Event type
        """
        subscribed = adapter.get_subscribed_events()
        assert event_type not in subscribed, (
            f"Adapter is subscribed to {event_type.value}"
        )

    def assert_event_handled(
        self, mock_adapter: MockAdapter, event_type: EventType, min_count: int = 1
    ) -> None:
        """
        Assert event was handled by mock adapter.

        Args:
            mock_adapter: MockAdapter instance
            event_type: Event type
            min_count: Minimum number of times
        """
        events = mock_adapter.get_handled_events()
        matching = [e for e in events if e.event_type == event_type]
        assert len(matching) >= min_count, (
            f"Expected at least {min_count} {event_type.value} events handled, "
            f"got {len(matching)}"
        )

    def publish_test_event(
        self,
        event_bus: EventBus,
        event_type: EventType = EventType.CONTENT_PUSHED,
        source: str = "test_source",
        data: dict[str, Any] | None = None,
    ) -> Event:
        """
        Publish a test event.

        Args:
            event_bus: EventBus instance
            event_type: Event type
            source: Event source
            data: Event data

        Returns:
            Published event
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
        )
        event_bus.publish(event)
        return event