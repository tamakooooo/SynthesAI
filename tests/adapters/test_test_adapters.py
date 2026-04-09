"""
Integration tests for Test Adapters.

Tests adapter framework functionality with actual adapter implementations.
"""

import asyncio
import time

import pytest

from learning_assistant.adapters.test_validation_adapter import (
    TestValidationAdapter,
    AsyncTestAdapter,
    ErrorSimulationAdapter,
)
from learning_assistant.core.base_adapter import AdapterState
from learning_assistant.core.event_bus import EventBus, Event, EventType


class TestTestValidationAdapter:
    """Test TestValidationAdapter functionality."""

    def test_adapter_initialization(self) -> None:
        """Test adapter initialization."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)

        assert adapter.state == AdapterState.READY
        assert adapter.event_bus == event_bus

    def test_adapter_initialization_with_auto_subscribe(self) -> None:
        """Test initialization with auto-subscribe."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()

        config = {
            "auto_subscribe": [
                "video.downloaded",
                "video.transcribed",
            ]
        }
        adapter.initialize(config, event_bus)

        assert adapter.state == AdapterState.READY
        assert len(adapter.get_subscribed_events()) == 2
        assert EventType.VIDEO_DOWNLOADED in adapter.get_subscribed_events()
        assert EventType.VIDEO_TRANSCRIBED in adapter.get_subscribed_events()

    def test_adapter_initialization_error_simulation(self) -> None:
        """Test initialization with error simulation."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()

        config = {"simulate_init_error": True}
        adapter.initialize(config, event_bus)

        assert adapter.state == AdapterState.ERROR
        assert adapter._last_error is not None

    def test_push_content_valid(self) -> None:
        """Test pushing valid content."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        content = {"title": "Test Content", "body": "Test body"}
        result = adapter.push_content(content)

        assert result is True
        assert len(adapter.get_pushed_content()) == 1
        assert adapter.get_pushed_content()[0] == content

    def test_push_content_invalid(self) -> None:
        """Test pushing invalid content."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Missing required 'title' field
        content = {"body": "Test body"}
        result = adapter.push_content(content)

        assert result is False
        assert len(adapter.get_pushed_content()) == 0
        assert adapter._error_count == 1

    def test_push_content_not_ready(self) -> None:
        """Test pushing content when adapter not ready."""
        adapter = TestValidationAdapter()

        # Adapter not initialized
        content = {"title": "Test"}
        result = adapter.push_content(content)

        assert result is False

    def test_sync_data(self) -> None:
        """Test syncing data."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        data = {"key": "value"}
        result = adapter.sync_data("history", data)

        assert result is True
        assert len(adapter.get_synced_data("history")) == 1

    def test_sync_data_multiple_types(self) -> None:
        """Test syncing multiple data types."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        adapter.sync_data("history", {"id": 1})
        adapter.sync_data("vocabulary", {"word": "test"})
        adapter.sync_data("history", {"id": 2})

        history_data = adapter.get_synced_data("history")
        assert len(history_data) == 2

        vocab_data = adapter.get_synced_data("vocabulary")
        assert len(vocab_data) == 1

    def test_handle_trigger(self) -> None:
        """Test handling trigger."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        trigger_data = {"action": "test"}
        response = adapter.handle_trigger(trigger_data)

        assert response["status"] == "success"
        assert response["adapter"] == "test_validation"
        assert response["trigger_echo"] == trigger_data
        assert "timestamp" in response

    def test_event_tracking(self) -> None:
        """Test event tracking."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        config = {"auto_subscribe": ["video.downloaded", "video.transcribed"]}
        adapter.initialize(config, event_bus)

        # Publish events
        event1 = Event(
            event_type=EventType.VIDEO_DOWNLOADED,
            source="test",
            data={"url": "test_url"},
        )
        event2 = Event(
            event_type=EventType.VIDEO_TRANSCRIBED,
            source="test",
            data={"duration": 10.0},
        )

        event_bus.publish(event1)
        event_bus.publish(event2)

        # Check event tracking
        assert adapter.get_event_count() == 2
        assert adapter.get_event_count(EventType.VIDEO_DOWNLOADED) == 1
        assert adapter.get_event_count(EventType.VIDEO_TRANSCRIBED) == 1

        processed = adapter.get_processed_events()
        assert len(processed) == 2
        assert event1 in processed
        assert event2 in processed

    def test_cleanup(self) -> None:
        """Test adapter cleanup."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        config = {"auto_subscribe": ["video.downloaded"]}
        adapter.initialize(config, event_bus)

        # Push some data
        adapter.push_content({"title": "Test"})
        adapter.sync_data("history", {"id": 1})

        # Cleanup
        adapter.cleanup()

        assert adapter.state == AdapterState.UNINITIALIZED
        assert len(adapter.get_subscribed_events()) == 0
        assert len(adapter.get_pushed_content()) == 0
        assert len(adapter.get_processed_events()) == 0

    def test_clear_tracking_data(self) -> None:
        """Test clearing tracking data."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Add tracking data
        adapter.push_content({"title": "Test"})
        adapter.sync_data("history", {"id": 1})

        # Clear tracking
        adapter.clear_tracking_data()

        assert len(adapter.get_pushed_content()) == 0
        assert len(adapter.get_synced_data("history")) == 0


class TestAsyncTestAdapter:
    """Test AsyncTestAdapter functionality."""

    def test_async_adapter_initialization(self) -> None:
        """Test async adapter initialization."""
        adapter = AsyncTestAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)

        assert adapter.state == AdapterState.READY
        assert adapter.get_async_event_count() == 0

    def test_async_adapter_with_delays(self) -> None:
        """Test async adapter with configured delays."""
        adapter = AsyncTestAdapter()
        event_bus = EventBus()

        config = {
            "push_delay": 0.05,
            "sync_delay": 0.03,
        }
        adapter.initialize(config, event_bus)

        start = time.time()
        adapter.push_content({"title": "Test"})
        elapsed = time.time() - start

        assert elapsed >= 0.05
        assert len(adapter.get_processing_delays()) == 1

    @pytest.mark.asyncio
    async def test_async_event_handler(self) -> None:
        """Test async event handling."""
        adapter = AsyncTestAdapter()
        event_bus = EventBus()

        config = {"event_delay": 0.01}
        adapter.initialize(config, event_bus)

        # Subscribe with async handler
        event_bus.subscribe(EventType.VIDEO_DOWNLOADED, adapter.async_event_handler)

        # Publish event
        event = Event(
            event_type=EventType.VIDEO_DOWNLOADED,
            source="test",
            data={},
        )

        await event_bus.publish_async(event)

        # Give time for async processing
        await asyncio.sleep(0.02)

        assert adapter.get_async_event_count() == 1

    def test_async_adapter_cleanup(self) -> None:
        """Test async adapter cleanup."""
        adapter = AsyncTestAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        adapter.cleanup()

        assert adapter.state == AdapterState.UNINITIALIZED


class TestErrorSimulationAdapter:
    """Test ErrorSimulationAdapter functionality."""

    def test_error_adapter_initialization(self) -> None:
        """Test error adapter initialization."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()

        adapter.initialize({}, event_bus)

        assert adapter.state == AdapterState.READY
        assert adapter.get_call_count() == 0
        assert adapter.get_error_count() == 0

    def test_error_mode_push_content(self) -> None:
        """Test error mode for push_content."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Enable error mode
        adapter.set_error_mode("push_content", True)

        # Push should fail
        result = adapter.push_content({"title": "Test"})

        assert result is False
        assert adapter.get_call_count("push_content") == 1
        assert adapter.get_error_count("push_content") == 1
        assert adapter.get_error_rate("push_content") == 1.0

    def test_error_mode_sync_data(self) -> None:
        """Test error mode for sync_data."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        adapter.set_error_mode("sync_data", True)

        result = adapter.sync_data("test", {})

        assert result is False
        assert adapter.get_error_count("sync_data") == 1

    def test_error_mode_handle_trigger(self) -> None:
        """Test error mode for handle_trigger."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        adapter.set_error_mode("handle_trigger", True)

        response = adapter.handle_trigger({})

        assert response["status"] == "error"
        assert adapter.get_error_count("handle_trigger") == 1

    def test_error_rate_simulation(self) -> None:
        """Test error rate simulation."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Set 100% error rate
        adapter.set_error_rate(1.0)

        # All calls should fail
        for _ in range(5):
            adapter.push_content({"title": "Test"})

        assert adapter.get_call_count("push_content") == 5
        assert adapter.get_error_count("push_content") == 5
        assert adapter.get_error_rate("push_content") == 1.0

    def test_error_rate_partial(self) -> None:
        """Test partial error rate."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Set 50% error rate (may not be exact due to randomness)
        adapter.set_error_rate(0.5)

        # Multiple calls
        for _ in range(100):
            adapter.push_content({"title": "Test"})

        # Should have some errors (approximately 50%)
        error_rate = adapter.get_error_rate("push_content")
        assert 0.3 < error_rate < 0.7  # Allow some variance

    def test_error_mode_override_rate(self) -> None:
        """Test that error mode overrides error rate."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Set 0% error rate but enable error mode
        adapter.set_error_rate(0.0)
        adapter.set_error_mode("push_content", True)

        # Should still fail due to error mode
        result = adapter.push_content({"title": "Test"})

        assert result is False

    def test_disable_error_mode(self) -> None:
        """Test disabling error mode."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Enable then disable
        adapter.set_error_mode("push_content", True)
        adapter.set_error_mode("push_content", False)

        result = adapter.push_content({"title": "Test"})

        assert result is True

    def test_reset_statistics(self) -> None:
        """Test resetting statistics."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Generate some calls and errors
        adapter.set_error_mode("push_content", True)
        adapter.push_content({"title": "Test"})
        adapter.push_content({"title": "Test2"})

        # Reset
        adapter.reset_statistics()

        assert adapter.get_call_count() == 0
        assert adapter.get_error_count() == 0
        assert adapter._error_count == 0

    def test_error_rate_clamping(self) -> None:
        """Test error rate is clamped to valid range."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Test clamping
        adapter.set_error_rate(1.5)
        assert adapter._error_rate == 1.0

        adapter.set_error_rate(-0.5)
        assert adapter._error_rate == 0.0

    def test_error_adapter_cleanup(self) -> None:
        """Test error adapter cleanup."""
        adapter = ErrorSimulationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        adapter.cleanup()

        assert adapter.state == AdapterState.UNINITIALIZED


class TestMultiAdapterIntegration:
    """Test multiple adapters working together."""

    def test_multiple_adapters_same_event_bus(self) -> None:
        """Test multiple adapters on same event bus."""
        event_bus = EventBus()

        # Create multiple adapters
        adapter1 = TestValidationAdapter()
        adapter2 = TestValidationAdapter()

        # Subscribe to different events
        config1 = {"auto_subscribe": ["video.downloaded"]}
        config2 = {"auto_subscribe": ["video.transcribed"]}

        adapter1.initialize(config1, event_bus)
        adapter2.initialize(config2, event_bus)

        # Publish events
        event_bus.publish(Event(EventType.VIDEO_DOWNLOADED, "test", {}))
        event_bus.publish(Event(EventType.VIDEO_TRANSCRIBED, "test", {}))

        # Check each adapter received correct events
        assert adapter1.get_event_count() == 1
        assert adapter1.get_event_count(EventType.VIDEO_DOWNLOADED) == 1

        assert adapter2.get_event_count() == 1
        assert adapter2.get_event_count(EventType.VIDEO_TRANSCRIBED) == 1

    def test_multiple_adapters_same_event(self) -> None:
        """Test multiple adapters subscribed to same event."""
        event_bus = EventBus()

        adapter1 = TestValidationAdapter()
        adapter2 = TestValidationAdapter()

        config = {"auto_subscribe": ["video.downloaded"]}

        adapter1.initialize(config, event_bus)
        adapter2.initialize(config, event_bus)

        # Publish event
        event_bus.publish(Event(EventType.VIDEO_DOWNLOADED, "test", {}))

        # Both adapters should receive event
        assert adapter1.get_event_count() == 1
        assert adapter2.get_event_count() == 1

    def test_adapter_isolation(self) -> None:
        """Test adapters are isolated from each other."""
        event_bus = EventBus()

        adapter1 = TestValidationAdapter()
        adapter2 = ErrorSimulationAdapter()

        adapter1.initialize({}, event_bus)
        adapter2.initialize({}, event_bus)

        # Adapter2 has error mode enabled
        adapter2.set_error_mode("push_content", True)

        # Adapter1 should work normally
        assert adapter1.push_content({"title": "Test1"}) is True

        # Adapter2 should fail
        assert adapter2.push_content({"title": "Test2"}) is False

        # Adapter1 should not be affected
        assert adapter1._error_count == 0

    def test_adapter_lifecycle_independence(self) -> None:
        """Test adapter lifecycle is independent."""
        event_bus = EventBus()

        adapter1 = TestValidationAdapter()
        adapter2 = TestValidationAdapter()

        adapter1.initialize({}, event_bus)
        adapter2.initialize({}, event_bus)

        # Cleanup adapter1
        adapter1.cleanup()

        # Adapter2 should still be ready
        assert adapter1.state == AdapterState.UNINITIALIZED
        assert adapter2.state == AdapterState.READY


class TestAdapterEventBusIntegration:
    """Test deep integration between adapters and event bus."""

    def test_adapter_unsubscribe_on_cleanup(self) -> None:
        """Test adapters unsubscribe from events on cleanup."""
        event_bus = EventBus()

        adapter = TestValidationAdapter()
        config = {"auto_subscribe": ["video.downloaded", "video.transcribed"]}
        adapter.initialize(config, event_bus)

        # Verify subscriptions
        assert event_bus.has_subscribers(EventType.VIDEO_DOWNLOADED)
        assert event_bus.has_subscribers(EventType.VIDEO_TRANSCRIBED)

        # Cleanup
        adapter.cleanup()

        # Should be unsubscribed
        assert not event_bus.has_subscribers(EventType.VIDEO_DOWNLOADED)
        assert not event_bus.has_subscribers(EventType.VIDEO_TRANSCRIBED)

    def test_adapter_event_propagation(self) -> None:
        """Test events propagate correctly through adapters."""
        event_bus = EventBus()

        # Create chain: adapter1 -> event -> adapter2
        adapter1 = TestValidationAdapter()
        adapter2 = TestValidationAdapter()

        adapter1.initialize({}, event_bus)
        config2 = {"auto_subscribe": ["adapter.content_pushed"]}
        adapter2.initialize(config2, event_bus)

        # When adapter1 pushes content, it should publish event
        # (if adapter framework supports this)
        adapter1.push_content({"title": "Test"})

        # For now, manually publish to test propagation
        event_bus.publish(
            Event(EventType.CONTENT_PUSHED, adapter1.name, {"title": "Test"})
        )

        # Adapter2 should receive the event
        assert adapter2.get_event_count(EventType.CONTENT_PUSHED) == 1

    def test_adapter_error_recovery_with_event_bus(self) -> None:
        """Test adapter error recovery using event bus."""
        event_bus = EventBus()

        adapter = ErrorSimulationAdapter()
        adapter.initialize({}, event_bus)

        # Subscribe to error events
        error_events: list[Event] = []

        def error_handler(event: Event) -> None:
            error_events.append(event)

        event_bus.subscribe(EventType.ERROR_OCCURRED, error_handler)

        # Simulate error
        adapter.set_error_mode("push_content", True)
        adapter.push_content({"title": "Test"})

        # Error should be recorded
        assert adapter.get_error_count("push_content") == 1

        # Recover
        adapter.set_error_mode("push_content", False)
        result = adapter.push_content({"title": "Test2"})

        assert result is True


class TestAdapterPerformance:
    """Test adapter performance characteristics."""

    def test_adapter_push_performance(self) -> None:
        """Test adapter push performance."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Measure time for 1000 pushes
        start = time.time()
        for i in range(1000):
            adapter.push_content({"title": f"Test {i}"})
        elapsed = time.time() - start

        # Should complete in reasonable time (<1 second)
        assert elapsed < 1.0
        assert len(adapter.get_pushed_content()) == 1000

    def test_adapter_event_throughput(self) -> None:
        """Test adapter event handling throughput."""
        event_bus = EventBus()

        adapter = TestValidationAdapter()
        config = {"auto_subscribe": ["video.downloaded"]}
        adapter.initialize(config, event_bus)

        # Measure time to process 100 events
        start = time.time()
        for i in range(100):
            event = Event(EventType.VIDEO_DOWNLOADED, "test", {"index": i})
            event_bus.publish(event)
        elapsed = time.time() - start

        # Should handle 100 events quickly
        assert elapsed < 0.5
        assert adapter.get_event_count() == 100

    def test_adapter_memory_efficiency(self) -> None:
        """Test adapter memory efficiency."""
        adapter = TestValidationAdapter()
        event_bus = EventBus()
        adapter.initialize({}, event_bus)

        # Push lots of content
        for i in range(10000):
            adapter.push_content({"title": f"Test {i}", "data": "x" * 100})

        # Should track all content
        assert len(adapter.get_pushed_content()) == 10000

        # Clear tracking should free memory
        adapter.clear_tracking_data()
        assert len(adapter.get_pushed_content()) == 0