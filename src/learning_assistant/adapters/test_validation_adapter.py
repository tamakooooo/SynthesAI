"""
Test Adapter for validation and integration testing.

This adapter is used to validate the adapter framework works correctly.
"""

import asyncio
import time
from typing import Any

from loguru import logger

from learning_assistant.core.base_adapter import AdapterState, BaseAdapter
from learning_assistant.core.event_bus import Event, EventBus, EventType


class TestValidationAdapter(BaseAdapter):
    """
    Test adapter for validating adapter framework functionality.

    Features:
    - Event processing tracking
    - Content push validation
    - Data sync testing
    - Error simulation capabilities
    """

    @property
    def name(self) -> str:
        return "test_validation"

    @property
    def description(self) -> str:
        return "Test adapter for framework validation"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize test adapter.

        Config options:
        - auto_subscribe: List of event types to auto-subscribe
        - simulate_init_error: Simulate initialization error
        """
        self._set_initializing()

        # Check for error simulation
        if config.get("simulate_init_error"):
            self._set_error("Simulated initialization error")
            return

        self.config = config
        self.event_bus = event_bus

        # Track processed events
        self._processed_events: list[Event] = []
        self._pushed_content: list[dict[str, Any]] = []
        self._synced_data: dict[str, list[dict[str, Any]]] = {}

        # Auto-subscribe to configured events
        auto_subscribe = config.get("auto_subscribe", [])
        for event_type_str in auto_subscribe:
            try:
                event_type = EventType(event_type_str)
                self.subscribe_to_event(event_type)
                logger.info(f"Auto-subscribed to {event_type.value}")
            except ValueError:
                logger.warning(f"Invalid event type: {event_type_str}")

        self._set_ready()
        logger.info(
            f"TestValidationAdapter initialized with {len(auto_subscribe)} subscriptions"
        )

    def push_content(self, content: dict[str, Any]) -> bool:
        """
        Push content (test implementation).

        Validates content structure and tracks pushes.
        """
        if self.state != AdapterState.READY:
            logger.warning(f"Cannot push content: adapter state is {self.state.value}")
            return False

        # Validate required fields
        if "title" not in content:
            self.record_error("Content missing required field: title")
            return False

        # Track push
        self._pushed_content.append(content)
        logger.info(f"Pushed content: {content.get('title', 'Untitled')}")

        return True

    def sync_data(self, data_type: str, data: dict[str, Any]) -> bool:
        """
        Sync data (test implementation).

        Tracks data syncs by type.
        """
        if self.state != AdapterState.READY:
            logger.warning(f"Cannot sync data: adapter state is {self.state.value}")
            return False

        # Initialize type list if needed
        if data_type not in self._synced_data:
            self._synced_data[data_type] = []

        # Track sync
        self._synced_data[data_type].append(data)
        logger.info(f"Synced {data_type} data")

        return True

    def handle_trigger(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        """
        Handle trigger (test implementation).

        Returns echo of trigger data with adapter info.
        """
        if self.state != AdapterState.READY:
            return {
                "status": "error",
                "message": f"Adapter state is {self.state.value}",
            }

        # Echo back trigger data with adapter info
        return {
            "status": "success",
            "adapter": self.name,
            "trigger_echo": trigger_data,
            "timestamp": time.time(),
        }

    def cleanup(self) -> None:
        """Cleanup test adapter."""
        self._set_shutting_down()

        # Clear tracked data
        self._processed_events.clear()
        self._pushed_content.clear()
        self._synced_data.clear()

        # Unsubscribe from all events
        self.unsubscribe_from_all_events()

        self.state = AdapterState.UNINITIALIZED
        logger.info("TestValidationAdapter cleanup complete")

    # Event handling

    def default_event_handler(self, event: Event) -> None:
        """
        Default event handler that tracks processed events.
        """
        super().default_event_handler(event)

        # Track event
        self._processed_events.append(event)
        logger.debug(f"Tracked event: {event.event_type.value}")

    # Query methods for testing

    def get_processed_events(self, event_type: EventType | None = None) -> list[Event]:
        """
        Get processed events, optionally filtered by type.

        Args:
            event_type: Event type to filter by (optional)

        Returns:
            List of processed events
        """
        if event_type is None:
            return self._processed_events.copy()

        return [e for e in self._processed_events if e.event_type == event_type]

    def get_event_count(self, event_type: EventType | None = None) -> int:
        """
        Get count of processed events.

        Args:
            event_type: Event type to filter by (optional)

        Returns:
            Number of processed events
        """
        return len(self.get_processed_events(event_type))

    def get_pushed_content(self) -> list[dict[str, Any]]:
        """
        Get all pushed content.

        Returns:
            List of pushed content dicts
        """
        return self._pushed_content.copy()

    def get_synced_data(
        self, data_type: str | None = None
    ) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
        """
        Get synced data, optionally filtered by type.

        Args:
            data_type: Data type to filter by (optional)

        Returns:
            Synced data dict or list for specific type
        """
        if data_type is None:
            return {k: v.copy() for k, v in self._synced_data.items()}

        return self._synced_data.get(data_type, []).copy()

    def clear_tracking_data(self) -> None:
        """Clear all tracking data."""
        self._processed_events.clear()
        self._pushed_content.clear()
        for data_list in self._synced_data.values():
            data_list.clear()


class AsyncTestAdapter(BaseAdapter):
    """
    Async test adapter for testing async event handling.
    """

    @property
    def name(self) -> str:
        return "async_test"

    @property
    def description(self) -> str:
        return "Async test adapter for async event handling"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """Initialize async test adapter."""
        self._set_initializing()
        self.config = config
        self.event_bus = event_bus
        self._async_events_processed: int = 0
        self._processing_delays: list[float] = []
        self._set_ready()

    def push_content(self, content: dict[str, Any]) -> bool:
        """Push content (async simulation)."""
        # Simulate async delay
        delay = self.config.get("push_delay", 0.01)
        time.sleep(delay)
        self._processing_delays.append(delay)
        return True

    def sync_data(self, data_type: str, data: dict[str, Any]) -> bool:
        """Sync data (async simulation)."""
        delay = self.config.get("sync_delay", 0.01)
        time.sleep(delay)
        return True

    def handle_trigger(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        """Handle trigger (async simulation)."""
        delay = self.config.get("trigger_delay", 0.01)
        time.sleep(delay)
        return {"status": "success", "async": True}

    def cleanup(self) -> None:
        """Cleanup async test adapter."""
        self._set_shutting_down()
        self.unsubscribe_from_all_events()
        self.state = AdapterState.UNINITIALIZED

    async def async_event_handler(self, event: Event) -> None:
        """
        Async event handler for testing async event bus.

        Args:
            event: Event to handle
        """
        # Simulate async processing
        delay = self.config.get("event_delay", 0.01)
        await asyncio.sleep(delay)

        self._async_events_processed += 1
        self._processing_delays.append(delay)
        logger.debug(f"Async handled event {event.event_type.value}")

    def get_async_event_count(self) -> int:
        """Get count of async events processed."""
        return self._async_events_processed

    def get_processing_delays(self) -> list[float]:
        """Get list of processing delays."""
        return self._processing_delays.copy()


class ErrorSimulationAdapter(BaseAdapter):
    """
    Adapter for testing error handling and recovery.
    """

    @property
    def name(self) -> str:
        return "error_simulation"

    @property
    def description(self) -> str:
        return "Adapter for testing error handling and recovery"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """Initialize error simulation adapter."""
        self._set_initializing()

        self.config = config
        self.event_bus = event_bus

        # Error simulation config
        self._error_rate = config.get("error_rate", 0.0)  # 0.0 to 1.0
        self._error_modes: dict[str, bool] = config.get("error_modes", {})

        # Track calls and errors
        self._op_call_count: dict[str, int] = {}
        self._op_error_count: dict[str, int] = {}

        self._set_ready()

    def _should_simulate_error(self, operation: str) -> bool:
        """
        Determine if error should be simulated for operation.

        Args:
            operation: Operation name

        Returns:
            True if should simulate error
        """
        # Check explicit error mode
        if self._error_modes.get(operation, False):
            return True

        # Check random error rate
        import random

        if self._error_rate > 0 and random.random() < self._error_rate:
            return True

        return False

    def _track_call(self, operation: str) -> None:
        """Track operation call."""
        self._op_call_count[operation] = self._op_call_count.get(operation, 0) + 1

    def _track_error(self, operation: str) -> None:
        """Track operation error."""
        self._op_error_count[operation] = self._op_error_count.get(operation, 0) + 1

    def push_content(self, content: dict[str, Any]) -> bool:
        """Push content with error simulation."""
        self._track_call("push_content")

        if self._should_simulate_error("push_content"):
            self._track_error("push_content")
            self.record_error("Simulated push_content error")
            return False

        return True

    def sync_data(self, data_type: str, data: dict[str, Any]) -> bool:
        """Sync data with error simulation."""
        self._track_call("sync_data")

        if self._should_simulate_error("sync_data"):
            self._track_error("sync_data")
            self.record_error("Simulated sync_data error")
            return False

        return True

    def handle_trigger(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        """Handle trigger with error simulation."""
        self._track_call("handle_trigger")

        if self._should_simulate_error("handle_trigger"):
            self._track_error("handle_trigger")
            self.record_error("Simulated handle_trigger error")
            return {"status": "error", "message": "Simulated error"}

        return {"status": "success"}

    def cleanup(self) -> None:
        """Cleanup error simulation adapter."""
        self._set_shutting_down()
        self.unsubscribe_from_all_events()
        self.state = AdapterState.UNINITIALIZED

    # Configuration methods

    def set_error_rate(self, rate: float) -> None:
        """
        Set error rate for random error simulation.

        Args:
            rate: Error rate (0.0 to 1.0)
        """
        self._error_rate = max(0.0, min(1.0, rate))

    def set_error_mode(self, operation: str, enabled: bool) -> None:
        """
        Enable or disable error mode for specific operation.

        Args:
            operation: Operation name
            enabled: Whether to simulate errors
        """
        self._error_modes[operation] = enabled

    # Query methods

    def get_call_count(self, operation: str | None = None) -> int:
        """
        Get call count for operation.

        Args:
            operation: Operation name (optional, returns total if None)

        Returns:
            Call count
        """
        if operation is None:
            return sum(self._op_call_count.values())

        return self._op_call_count.get(operation, 0)

    def get_error_count(self, operation: str | None = None) -> int:
        """
        Get error count for operation.

        Args:
            operation: Operation name (optional, returns total if None)

        Returns:
            Error count
        """
        if operation is None:
            return sum(self._op_error_count.values())

        return self._op_error_count.get(operation, 0)

    def get_error_rate(self, operation: str | None = None) -> float:
        """
        Get actual error rate for operation.

        Args:
            operation: Operation name (optional, returns overall rate if None)

        Returns:
            Error rate (0.0 to 1.0)
        """
        calls = self.get_call_count(operation)
        if calls == 0:
            return 0.0

        errors = self.get_error_count(operation)
        return errors / calls

    def reset_statistics(self) -> None:
        """Reset call and error statistics."""
        self._op_call_count.clear()
        self._op_error_count.clear()
        self.clear_errors()
