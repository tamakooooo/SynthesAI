"""
SynthesAI Integration Tests.

Tests end-to-end workflows across multiple components.
Requires proper configuration and API keys for full testing.

Run with: pytest tests/integration/ -v -m integration
"""

import pytest
from pathlib import Path


@pytest.fixture
def test_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory for integration tests."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal settings.yaml
    settings_file = config_dir / "settings.yaml"
    settings_file.write_text("""
app:
  name: SynthesAI Test
  version: 0.3.0
  log_level: INFO

llm:
  default_provider: openai
  providers:
    openai:
      api_key_env: OPENAI_API_KEY
      default_model: gpt-3.5-turbo
      models:
        - gpt-3.5-turbo
        - gpt-4

cache:
  enabled: true
  directory: data/cache

history:
  enabled: true
  directory: data/history
""")

    return config_dir


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory for integration tests."""
    data_dir = tmp_path / "data"
    (data_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (data_dir / "cache").mkdir(parents=True, exist_ok=True)
    (data_dir / "history").mkdir(parents=True, exist_ok=True)
    return data_dir


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    @pytest.mark.integration
    def test_config_manager_load_all(self, test_config_dir: Path):
        """Test ConfigManager loads all configuration files."""
        from learning_assistant.core.config_manager import ConfigManager

        manager = ConfigManager(config_dir=test_config_dir)
        manager.load_all()

        assert manager.settings_model is not None
        assert manager.settings_model.app.name == "SynthesAI Test"
        assert manager.settings_model.llm.default_provider == "openai"

    @pytest.mark.integration
    def test_config_manager_get_llm_config(self, test_config_dir: Path):
        """Test ConfigManager retrieves LLM configuration."""
        import os
        from learning_assistant.core.config_manager import ConfigManager

        manager = ConfigManager(config_dir=test_config_dir)
        manager.load_all()

        # Test without API key
        llm_config = manager.get_llm_config("openai")
        assert llm_config.get("default_model") == "gpt-3.5-turbo"

        # Test with environment variable
        original_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key-123"
        try:
            llm_config = manager.get_llm_config("openai")
            assert llm_config.get("api_key") == "test-key-123"
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)


class TestEventBusIntegration:
    """Integration tests for EventBus."""

    @pytest.mark.integration
    def test_event_bus_subscribe_and_publish(self):
        """Test EventBus event subscription and publishing."""
        from learning_assistant.core.event_bus import EventBus, EventHandler

        bus = EventBus()
        received_events = []

        def handler(event):
            received_events.append(event)

        bus.subscribe("test.event", handler)
        bus.publish("test.event", {"data": "test_value"})

        assert len(received_events) == 1
        assert received_events[0].data == {"data": "test_value"}

    @pytest.mark.integration
    def test_event_bus_multiple_handlers(self):
        """Test EventBus with multiple handlers for same event."""
        from learning_assistant.core.event_bus import EventBus

        bus = EventBus()
        results = []

        bus.subscribe("test.multi", lambda e: results.append(("handler1", e.data)))
        bus.subscribe("test.multi", lambda e: results.append(("handler2", e.data)))

        bus.publish("test.multi", {"value": 42})

        assert len(results) == 2
        assert results[0][0] == "handler1"
        assert results[1][0] == "handler2"


class TestPluginManagerIntegration:
    """Integration tests for PluginManager."""

    @pytest.mark.integration
    def test_plugin_manager_discover_modules(self):
        """Test PluginManager discovers built-in modules."""
        from learning_assistant.core.plugin_manager import PluginManager
        from pathlib import Path

        plugin_dirs = [
            Path("src/learning_assistant/modules"),
        ]

        manager = PluginManager(plugin_dirs=plugin_dirs)
        manager.discover_plugins()

        # Should discover video_summary, link_learning, vocabulary
        discovered_names = list(manager.plugins.keys())
        assert "video_summary" in discovered_names
        assert "link_learning" in discovered_names
        assert "vocabulary" in discovered_names


class TestBatchProcessingIntegration:
    """Integration tests for batch processing."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_manager_task_flow(self):
        """Test BatchTaskManager task flow without external dependencies."""
        import asyncio
        from learning_assistant.core.batch import BatchTaskManager, TaskPriority

        manager = BatchTaskManager(max_workers=2)

        # Define simple async function
        async def simple_task(value: int) -> int:
            await asyncio.sleep(0.1)
            return value * 2

        # Add tasks
        await manager.add_task(
            task_id="task_1",
            func=simple_task,
            args=(5,),
            priority=TaskPriority.NORMAL,
        )
        await manager.add_task(
            task_id="task_2",
            func=simple_task,
            args=(10,),
            priority=TaskPriority.HIGH,
        )

        # Process all
        results = await manager.process_all()

        # Verify results
        assert results["task_1"].status.value == "completed"
        assert results["task_1"].result == 10
        assert results["task_2"].status.value == "completed"
        assert results["task_2"].result == 20

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_manager_statistics(self):
        """Test BatchTaskManager statistics tracking."""
        import asyncio
        from learning_assistant.core.batch import BatchTaskManager

        manager = BatchTaskManager(max_workers=2)

        async def quick_task() -> str:
            return "done"

        for i in range(5):
            await manager.add_task(task_id=f"task_{i}", func=quick_task)

        await manager.process_all()
        stats = manager.get_statistics()

        assert stats.total_tasks == 5
        assert stats.completed == 5
        assert stats.failed == 0
        assert stats.throughput > 0


class TestHistoryManagerIntegration:
    """Integration tests for HistoryManager."""

    @pytest.mark.integration
    def test_history_manager_save_and_load(self, test_data_dir: Path):
        """Test HistoryManager saves and loads records."""
        from learning_assistant.core.history_manager import HistoryManager
        from datetime import datetime

        manager = HistoryManager(history_dir=test_data_dir / "history")

        # Save a record
        record = {
            "id": "test_001",
            "type": "link",
            "url": "https://example.com",
            "title": "Test Article",
            "created_at": datetime.now().isoformat(),
        }
        manager.save_record(record)

        # Load records
        records = manager.get_records()
        assert len(records) == 1
        assert records[0]["title"] == "Test Article"


class TestEndToEndWorkflow:
    """End-to-end workflow tests requiring external services."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    async def test_full_link_workflow(self, test_data_dir: Path):
        """Test complete link learning workflow with real API."""
        import os
        from learning_assistant.modules.link_learning import LinkLearningModule
        from learning_assistant.core.event_bus import EventBus

        # Skip if no API key
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        module = LinkLearningModule()
        config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
            },
            "output": {
                "directory": str(test_data_dir / "outputs"),
            },
            "features": {
                "generate_quiz": False,
            },
        }

        event_bus = EventBus()
        module.initialize(config, event_bus)

        # Process a simple URL
        result = await module.process("https://example.com")

        assert result.title
        assert result.summary
        assert len(result.key_points) >= 1
        assert result.url == "https://example.com"


# Mark module for pytest
pytest.os = pytest.importorskip("os")