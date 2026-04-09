"""
Unit tests for PluginManager.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from learning_assistant.core.base_adapter import BaseAdapter, AdapterState
from learning_assistant.core.base_module import BaseModule
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.plugin_manager import PluginManager, PluginMetadata


# Create concrete test classes
class TestModule(BaseModule):
    """Test module implementation."""

    @property
    def name(self) -> str:
        return "test_module"

    def initialize(self, config: dict, event_bus: EventBus) -> None:
        pass

    def execute(self, input_data: dict) -> dict:
        return {"result": "success"}

    def cleanup(self) -> None:
        pass


class TestAdapter(BaseAdapter):
    """Test adapter implementation."""

    @property
    def name(self) -> str:
        return "test_adapter"

    def initialize(self, config: dict, event_bus: EventBus) -> None:
        self._set_initializing()
        self.config = config
        self.event_bus = event_bus
        self._set_ready()

    def push_content(self, content: dict) -> bool:
        return True

    def sync_data(self, data_type: str, data: dict) -> bool:
        return True

    def handle_trigger(self, trigger_data: dict) -> dict:
        return {}

    def cleanup(self) -> None:
        self._set_shutting_down()
        self.unsubscribe_from_all_events()
        self.state = AdapterState.UNINITIALIZED


@pytest.fixture
def temp_plugin_dir(tmp_path: Path) -> Path:
    """Create temporary plugin directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    return plugin_dir


@pytest.fixture
def plugin_manager(temp_plugin_dir: Path) -> PluginManager:
    """Create PluginManager with temporary directory."""
    return PluginManager(plugin_dirs=[temp_plugin_dir])


@pytest.fixture
def sample_plugin_yaml(temp_plugin_dir: Path) -> Path:
    """Create sample plugin.yaml file."""
    plugin_subdir = temp_plugin_dir / "test_plugin"
    plugin_subdir.mkdir()

    yaml_content = {
        "name": "test_plugin",
        "type": "module",
        "version": "1.0.0",
        "description": "Test plugin",
        "enabled": True,
        "priority": 1,
        "config": {"setting": "value"},
        "dependencies": [],
        "cli_commands": ["test"],
        "class_name": "TestModule",
        "module_name": "test_plugin",
    }

    yaml_path = plugin_subdir / "plugin.yaml"
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f)

    # Create Python module
    py_path = plugin_subdir / "test_plugin.py"
    py_path.write_text("""
from learning_assistant.core.base_module import BaseModule

class TestModule(BaseModule):
    @property
    def name(self):
        return "test_plugin"

    def initialize(self, config, event_bus):
        pass

    def execute(self, input_data):
        return {}

    def cleanup(self):
        pass
""")

    return yaml_path


class TestPluginMetadata:
    """Test PluginMetadata dataclass."""

    def test_metadata_creation_minimal(self) -> None:
        """Test creating metadata with minimal fields."""
        metadata = PluginMetadata(
            name="test",
            type="module",
            version="1.0.0",
            description="Test plugin",
        )

        assert metadata.name == "test"
        assert metadata.type == "module"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"
        assert metadata.enabled is True
        assert metadata.priority == 99
        assert metadata.config == {}
        assert metadata.dependencies == []

    def test_metadata_creation_full(self) -> None:
        """Test creating metadata with all fields."""
        metadata = PluginMetadata(
            name="test",
            type="adapter",
            version="2.0.0",
            description="Full test",
            enabled=False,
            priority=1,
            config={"key": "value"},
            dependencies=["other_plugin"],
            cli_commands=["cmd1", "cmd2"],
            path=Path("/tmp/test"),
            class_name="TestClass",
            module_name="test_module",
        )

        assert metadata.enabled is False
        assert metadata.priority == 1
        assert metadata.config == {"key": "value"}
        assert len(metadata.dependencies) == 1
        assert len(metadata.cli_commands) == 2


class TestPluginManagerInit:
    """Test PluginManager initialization."""

    def test_init_default_dirs(self) -> None:
        """Test initialization with default directories."""
        manager = PluginManager()

        assert len(manager.plugin_dirs) == 3
        assert manager.plugins == {}
        assert manager.loaded_plugins == {}

    def test_init_custom_dirs(self, temp_plugin_dir: Path) -> None:
        """Test initialization with custom directories."""
        manager = PluginManager(plugin_dirs=[temp_plugin_dir])

        assert len(manager.plugin_dirs) == 1
        assert manager.plugin_dirs[0] == temp_plugin_dir


class TestPluginManagerDiscovery:
    """Test plugin discovery functionality."""

    def test_discover_empty_directory(self, plugin_manager: PluginManager) -> None:
        """Test discovering from empty directory."""
        discovered = plugin_manager.discover_plugins()

        assert discovered == []
        assert plugin_manager.plugins == {}

    def test_discover_from_yaml(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test discovering plugin from plugin.yaml."""
        discovered = plugin_manager.discover_plugins()

        assert len(discovered) == 1
        assert "test_plugin" in plugin_manager.plugins

        metadata = plugin_manager.plugins["test_plugin"]
        assert metadata.name == "test_plugin"
        assert metadata.type == "module"
        assert metadata.version == "1.0.0"
        assert metadata.priority == 1

    def test_discover_invalid_yaml(
        self, plugin_manager: PluginManager, temp_plugin_dir: Path
    ) -> None:
        """Test discovering with invalid plugin.yaml."""
        plugin_subdir = temp_plugin_dir / "bad_plugin"
        plugin_subdir.mkdir()

        # Create invalid YAML
        yaml_path = plugin_subdir / "plugin.yaml"
        yaml_path.write_text("invalid: yaml: content: [")

        discovered = plugin_manager.discover_plugins()

        # Should handle error gracefully
        assert discovered == []

    def test_discover_missing_required_field(
        self, plugin_manager: PluginManager, temp_plugin_dir: Path
    ) -> None:
        """Test discovering with missing required field in plugin.yaml."""
        plugin_subdir = temp_plugin_dir / "incomplete_plugin"
        plugin_subdir.mkdir()

        # Create YAML without required 'type' field
        yaml_content = {
            "name": "incomplete",
            "version": "1.0.0",
            "description": "Missing type",
        }

        yaml_path = plugin_subdir / "plugin.yaml"
        with yaml_path.open("w", encoding="utf-8") as f:
            yaml.dump(yaml_content, f)

        discovered = plugin_manager.discover_plugins()

        # Should skip plugin with missing required field
        assert discovered == []

    def test_discover_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test discovering from non-existent directory."""
        nonexistent = tmp_path / "nonexistent"
        manager = PluginManager(plugin_dirs=[nonexistent])

        # Should handle gracefully
        discovered = manager.discover_plugins()
        assert discovered == []


class TestPluginManagerLoad:
    """Test plugin loading functionality."""

    def test_load_plugin_from_yaml(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test loading plugin discovered from YAML."""
        # Discover first
        plugin_manager.discover_plugins()

        # Load plugin
        plugin = plugin_manager.load_plugin("test_plugin")

        assert plugin is not None
        assert "test_plugin" in plugin_manager.loaded_plugins
        assert isinstance(plugin, BaseModule)

    def test_load_already_loaded(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test loading plugin that's already loaded."""
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        # Load again
        plugin = plugin_manager.load_plugin("test_plugin")

        # Should return existing instance
        assert plugin is not None

    def test_load_nonexistent_plugin(self, plugin_manager: PluginManager) -> None:
        """Test loading plugin that doesn't exist."""
        plugin = plugin_manager.load_plugin("nonexistent")

        assert plugin is None

    def test_load_disabled_plugin(
        self, plugin_manager: PluginManager, temp_plugin_dir: Path
    ) -> None:
        """Test loading disabled plugin."""
        plugin_subdir = temp_plugin_dir / "disabled_plugin"
        plugin_subdir.mkdir()

        yaml_content = {
            "name": "disabled",
            "type": "module",
            "version": "1.0.0",
            "description": "Disabled plugin",
            "enabled": False,
            "class_name": "TestModule",
            "module_name": "test_module",
        }

        yaml_path = plugin_subdir / "plugin.yaml"
        with yaml_path.open("w", encoding="utf-8") as f:
            yaml.dump(yaml_content, f)

        # Create Python module
        py_path = plugin_subdir / "test_module.py"
        py_path.write_text("""
from learning_assistant.core.base_module import BaseModule

class TestModule(BaseModule):
    @property
    def name(self):
        return "disabled"

    def initialize(self, config, event_bus):
        pass

    def execute(self, input_data):
        return {}

    def cleanup(self):
        pass
""")

        plugin_manager.discover_plugins()
        plugin = plugin_manager.load_plugin("disabled")

        assert plugin is None


class TestPluginManagerUnload:
    """Test plugin unloading functionality."""

    def test_unload_plugin(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test unloading a loaded plugin."""
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        # Unload
        plugin_manager.unload_plugin("test_plugin")

        assert "test_plugin" not in plugin_manager.loaded_plugins

    def test_unload_nonexistent_plugin(self, plugin_manager: PluginManager) -> None:
        """Test unloading plugin that's not loaded."""
        # Should not raise error
        plugin_manager.unload_plugin("nonexistent")

    def test_unload_calls_cleanup(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test that unloading calls cleanup method."""
        plugin_manager.discover_plugins()
        plugin = plugin_manager.load_plugin("test_plugin")

        # Mock cleanup
        plugin.cleanup = Mock()

        plugin_manager.unload_plugin("test_plugin")

        plugin.cleanup.assert_called_once()


class TestPluginManagerDependencies:
    """Test dependency checking functionality."""

    def test_check_dependencies_none(self, plugin_manager: PluginManager) -> None:
        """Test checking dependencies when none specified."""
        metadata = PluginMetadata(
            name="test",
            type="module",
            version="1.0.0",
            description="Test",
            dependencies=[],
        )

        result = plugin_manager.check_dependencies(metadata)

        assert result is True

    def test_check_dependencies_satisfied(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test checking satisfied dependencies."""
        # Load dependency first
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        # Create plugin with dependency
        dependent = PluginMetadata(
            name="dependent",
            type="adapter",
            version="1.0.0",
            description="Dependent plugin",
            dependencies=["test_plugin"],
        )

        result = plugin_manager.check_dependencies(dependent)

        assert result is True

    def test_check_dependencies_not_found(self, plugin_manager: PluginManager) -> None:
        """Test checking dependency that doesn't exist."""
        metadata = PluginMetadata(
            name="test",
            type="module",
            version="1.0.0",
            description="Test",
            dependencies=["nonexistent"],
        )

        result = plugin_manager.check_dependencies(metadata)

        assert result is False

    def test_check_dependencies_not_loaded(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test checking dependency that's discovered but not loaded."""
        plugin_manager.discover_plugins()

        # Create plugin with dependency (test_plugin is discovered but not loaded)
        dependent = PluginMetadata(
            name="dependent",
            type="adapter",
            version="1.0.0",
            description="Dependent plugin",
            dependencies=["test_plugin"],
        )

        result = plugin_manager.check_dependencies(dependent)

        assert result is False


class TestPluginManagerCommandConflicts:
    """Test CLI command conflict detection."""

    def test_check_conflicts_none(self, plugin_manager: PluginManager) -> None:
        """Test checking conflicts when no commands specified."""
        metadata = PluginMetadata(
            name="test",
            type="module",
            version="1.0.0",
            description="Test",
            cli_commands=[],
        )

        conflicts = plugin_manager.check_command_conflicts(metadata)

        assert conflicts == []

    def test_check_conflicts_no_conflict(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test checking conflicts with no conflict."""
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        # Create plugin with different command
        new_plugin = PluginMetadata(
            name="new",
            type="module",
            version="1.0.0",
            description="New",
            cli_commands=["different"],
        )

        conflicts = plugin_manager.check_command_conflicts(new_plugin)

        assert conflicts == []

    def test_check_conflicts_found(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test checking conflicts and finding conflict."""
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        # Create plugin with same command
        conflicting = PluginMetadata(
            name="conflicting",
            type="module",
            version="1.0.0",
            description="Conflicting",
            cli_commands=["test"],  # Same as test_plugin
        )

        conflicts = plugin_manager.check_command_conflicts(conflicting)

        assert len(conflicts) == 1
        assert "test" in conflicts


class TestPluginManagerInitialize:
    """Test plugin initialization functionality."""

    def test_initialize_all(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test initializing all loaded plugins."""
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        event_bus = EventBus()
        config = {"plugins": {"test_plugin": {"setting": "value"}}}

        plugin_manager.initialize_all(config, event_bus)

        # Should not raise error

    def test_initialize_all_with_priority(
        self, plugin_manager: PluginManager, temp_plugin_dir: Path
    ) -> None:
        """Test initialization respects priority order."""
        # Create two plugins with different priorities
        for name, priority in [("low", 99), ("high", 1)]:
            plugin_subdir = temp_plugin_dir / name
            plugin_subdir.mkdir()

            yaml_content = {
                "name": name,
                "type": "module",
                "version": "1.0.0",
                "description": f"{name} priority plugin",
                "priority": priority,
                "class_name": "TestModule",
                "module_name": name,
            }

            yaml_path = plugin_subdir / "plugin.yaml"
            with yaml_path.open("w", encoding="utf-8") as f:
                yaml.dump(yaml_content, f)

            py_path = plugin_subdir / f"{name}.py"
            py_path.write_text(f"""
from learning_assistant.core.base_module import BaseModule

class TestModule(BaseModule):
    @property
    def name(self):
        return "{name}"

    def initialize(self, config, event_bus):
        pass

    def execute(self, input_data):
        return {{}}

    def cleanup(self):
        pass
""")

        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("high")
        plugin_manager.load_plugin("low")

        event_bus = EventBus()
        config = {}

        # Initialize should respect priority
        plugin_manager.initialize_all(config, event_bus)


class TestPluginManagerCleanup:
    """Test plugin cleanup functionality."""

    def test_cleanup_all(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test cleaning up all loaded plugins."""
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        plugin_manager.cleanup_all()

        assert plugin_manager.loaded_plugins == {}

    def test_cleanup_calls_cleanup_method(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test that cleanup calls plugin cleanup method."""
        plugin_manager.discover_plugins()
        plugin = plugin_manager.load_plugin("test_plugin")

        # Mock cleanup
        plugin.cleanup = Mock()

        plugin_manager.cleanup_all()

        plugin.cleanup.assert_called_once()


class TestPluginManagerHelperMethods:
    """Test PluginManager helper methods."""

    def test_get_plugin(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test getting loaded plugin."""
        plugin_manager.discover_plugins()
        loaded = plugin_manager.load_plugin("test_plugin")

        plugin = plugin_manager.get_plugin("test_plugin")

        assert plugin is loaded

    def test_get_plugin_not_loaded(self, plugin_manager: PluginManager) -> None:
        """Test getting plugin that's not loaded."""
        plugin = plugin_manager.get_plugin("nonexistent")

        assert plugin is None

    def test_get_all_plugins(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test getting all loaded plugins."""
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("test_plugin")

        all_plugins = plugin_manager.get_all_plugins()

        assert len(all_plugins) == 1
        assert "test_plugin" in all_plugins


class TestPluginManagerIntegration:
    """Integration tests for PluginManager."""

    def test_full_workflow(
        self, plugin_manager: PluginManager, sample_plugin_yaml: Path
    ) -> None:
        """Test complete plugin workflow."""
        # Discover
        discovered = plugin_manager.discover_plugins()
        assert len(discovered) == 1

        # Load
        plugin = plugin_manager.load_plugin("test_plugin")
        assert plugin is not None

        # Initialize
        event_bus = EventBus()
        config = {}
        plugin_manager.initialize_all(config, event_bus)

        # Get
        loaded = plugin_manager.get_plugin("test_plugin")
        assert loaded is plugin

        # Cleanup
        plugin_manager.cleanup_all()
        assert len(plugin_manager.loaded_plugins) == 0

    def test_multiple_plugins(
        self, plugin_manager: PluginManager, temp_plugin_dir: Path
    ) -> None:
        """Test managing multiple plugins."""
        # Create two plugins
        for name in ["plugin1", "plugin2"]:
            plugin_subdir = temp_plugin_dir / name
            plugin_subdir.mkdir()

            yaml_content = {
                "name": name,
                "type": "module",
                "version": "1.0.0",
                "description": f"Plugin {name}",
                "class_name": "TestModule",
                "module_name": name,
            }

            yaml_path = plugin_subdir / "plugin.yaml"
            with yaml_path.open("w", encoding="utf-8") as f:
                yaml.dump(yaml_content, f)

            py_path = plugin_subdir / f"{name}.py"
            py_path.write_text(f"""
from learning_assistant.core.base_module import BaseModule

class TestModule(BaseModule):
    @property
    def name(self):
        return "{name}"

    def initialize(self, config, event_bus):
        pass

    def execute(self, input_data):
        return {{}}

    def cleanup(self):
        pass
""")

        # Discover and load
        plugin_manager.discover_plugins()
        plugin_manager.load_plugin("plugin1")
        plugin_manager.load_plugin("plugin2")

        all_plugins = plugin_manager.get_all_plugins()
        assert len(all_plugins) == 2
