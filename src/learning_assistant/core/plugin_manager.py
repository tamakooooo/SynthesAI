"""
Plugin Manager for Learning Assistant.

This module handles discovery, loading, and management of plugins (modules and adapters).
"""

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from learning_assistant.core.base_adapter import BaseAdapter
from learning_assistant.core.base_module import BaseModule


@dataclass
class PluginMetadata:
    """
    Plugin metadata structure.
    """

    name: str
    type: str  # "module" or "adapter"
    version: str
    description: str
    enabled: bool = True
    priority: int = 99
    config: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    cli_commands: list[str] = field(default_factory=list)
    path: Path | None = None
    class_name: str = ""
    module_name: str = ""  # Python module name for import


class PluginManager:
    """
    Plugin Manager for Learning Assistant.

    Handles:
    - Plugin discovery (directory scanning)
    - Plugin loading (importlib dynamic loading)
    - Lifecycle management (initialize, execute, cleanup)
    - Dependency checking
    - Command conflict detection
    """

    def __init__(self, plugin_dirs: list[Path] | None = None) -> None:
        """
        Initialize PluginManager.

        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or [
            Path("src/learning_assistant/modules"),
            Path("src/learning_assistant/adapters"),
            Path("plugins"),
        ]
        self.plugins: dict[str, PluginMetadata] = {}
        self.loaded_plugins: dict[str, BaseModule | BaseAdapter] = {}
        logger.info(f"PluginManager initialized with directories: {self.plugin_dirs}")

    def discover_plugins(self) -> list[PluginMetadata]:
        """
        Discover all plugins in configured directories.

        Searches for:
        - plugin.yaml files (explicit plugin definition)
        - Python modules with plugin classes (auto-discovery)

        Returns:
            List of discovered plugin metadata
        """
        logger.info("Discovering plugins")
        discovered = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue

            logger.debug(f"Scanning directory: {plugin_dir}")

            # Look for plugin.yaml files
            for plugin_yaml in plugin_dir.rglob("plugin.yaml"):
                try:
                    metadata = self._load_plugin_yaml(plugin_yaml)
                    if metadata:
                        discovered.append(metadata)
                        self.plugins[metadata.name] = metadata
                        logger.info(
                            f"Discovered plugin: {metadata.name} ({metadata.type}) from {plugin_yaml}"
                        )
                except Exception as e:
                    logger.error(f"Failed to load plugin.yaml {plugin_yaml}: {e}")

            # Look for Python modules without plugin.yaml (auto-discovery)
            for py_file in plugin_dir.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                # Skip if already has plugin.yaml
                if py_file.parent.joinpath("plugin.yaml").exists():
                    continue

                # Try to auto-discover
                try:
                    metadata = self._auto_discover_plugin(py_file)
                    if metadata:
                        discovered.append(metadata)
                        self.plugins[metadata.name] = metadata
                        logger.info(
                            f"Auto-discovered plugin: {metadata.name} ({metadata.type}) from {py_file}"
                        )
                except Exception as e:
                    logger.debug(f"Failed to auto-discover from {py_file}: {e}")

        logger.info(f"Discovered {len(discovered)} plugins total")
        return discovered

    def load_plugin(self, name: str) -> BaseModule | BaseAdapter | None:
        """
        Load a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Loaded plugin instance or None if failed
        """
        logger.info(f"Loading plugin: {name}")

        # Check if already loaded
        if name in self.loaded_plugins:
            logger.warning(f"Plugin {name} already loaded")
            return self.loaded_plugins[name]

        # Get plugin metadata
        if name not in self.plugins:
            logger.error(f"Plugin {name} not found in discovered plugins")
            return None

        metadata = self.plugins[name]

        # Check if plugin is enabled
        if not metadata.enabled:
            logger.warning(f"Plugin {name} is disabled")
            return None

        # Check dependencies
        if not self.check_dependencies(metadata):
            logger.error(f"Plugin {name} dependencies not satisfied")
            return None

        # Check command conflicts
        conflicts = self.check_command_conflicts(metadata)
        if conflicts:
            logger.error(
                f"Plugin {name} has CLI command conflicts: {', '.join(conflicts)}"
            )
            return None

        # Load plugin class
        try:
            plugin_class = self._load_plugin_class(metadata)
            if plugin_class is None:
                logger.error(f"Failed to load plugin class for {name}")
                return None

            # Instantiate plugin
            plugin_instance = plugin_class()

            # Store loaded plugin
            self.loaded_plugins[name] = plugin_instance
            logger.info(f"Successfully loaded plugin: {name}")

            return plugin_instance

        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            return None

    def unload_plugin(self, name: str) -> None:
        """
        Unload a plugin by name.

        Args:
            name: Plugin name
        """
        logger.info(f"Unloading plugin: {name}")

        if name not in self.loaded_plugins:
            logger.warning(f"Plugin {name} not loaded")
            return

        # Call cleanup
        try:
            plugin = self.loaded_plugins[name]
            plugin.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up plugin {name}: {e}")

        # Remove from loaded plugins
        del self.loaded_plugins[name]
        logger.info(f"Successfully unloaded plugin: {name}")

    def get_plugin(self, name: str) -> BaseModule | BaseAdapter | None:
        """
        Get a loaded plugin instance by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not loaded
        """
        return self.loaded_plugins.get(name)

    def get_all_plugins(self) -> dict[str, BaseModule | BaseAdapter]:
        """
        Get all loaded plugin instances.

        Returns:
            Dict of plugin name to plugin instance
        """
        return self.loaded_plugins

    def check_dependencies(self, plugin: PluginMetadata) -> bool:
        """
        Check if plugin dependencies are satisfied.

        Args:
            plugin: Plugin metadata

        Returns:
            True if dependencies are satisfied, False otherwise
        """
        if not plugin.dependencies:
            logger.debug(f"Plugin {plugin.name} has no dependencies")
            return True

        logger.debug(f"Checking dependencies for {plugin.name}: {plugin.dependencies}")

        for dep_name in plugin.dependencies:
            # Check if dependency is discovered
            if dep_name not in self.plugins:
                logger.error(
                    f"Plugin {plugin.name} depends on {dep_name}, but {dep_name} not found"
                )
                return False

            # Check if dependency is loaded
            if dep_name not in self.loaded_plugins:
                logger.error(
                    f"Plugin {plugin.name} depends on {dep_name}, but {dep_name} not loaded"
                )
                return False

        logger.debug(f"All dependencies satisfied for {plugin.name}")
        return True

    def check_command_conflicts(self, plugin: PluginMetadata) -> list[str]:
        """
        Check for CLI command conflicts.

        Args:
            plugin: Plugin metadata

        Returns:
            List of conflicting command names
        """
        if not plugin.cli_commands:
            return []

        conflicts = []

        # Check against already loaded plugins
        for loaded_name, _loaded_plugin in self.loaded_plugins.items():
            loaded_metadata = self.plugins.get(loaded_name)
            if loaded_metadata and loaded_metadata.cli_commands:
                for cmd in plugin.cli_commands:
                    if cmd in loaded_metadata.cli_commands:
                        conflicts.append(cmd)
                        logger.warning(
                            f"CLI command conflict: '{cmd}' already registered by {loaded_name}"
                        )

        return conflicts

    def initialize_all(self, config: dict[str, Any], event_bus: Any) -> None:
        """
        Initialize all loaded plugins.

        Args:
            config: Configuration dict
            event_bus: EventBus instance
        """
        logger.info("Initializing all plugins")

        # Sort plugins by priority (lower number = higher priority)
        sorted_plugins = sorted(
            self.loaded_plugins.items(),
            key=lambda x: self.plugins.get(
                x[0], PluginMetadata("", "", "", "", priority=99)
            ).priority,
        )

        for name, plugin in sorted_plugins:
            try:
                # Get plugin config (modules and adapters are at top level)
                plugin_data = config.get(name, {})
                if isinstance(plugin, BaseAdapter):
                    if plugin_data.get("enabled") is False:
                        logger.info(f"Skipping disabled adapter: {name}")
                        continue
                    plugin_config = plugin_data
                else:
                    # Extract 'config' sub-key if present (for modules.yaml structure)
                    plugin_config = plugin_data.get("config", plugin_data)

                # Initialize plugin
                plugin.initialize(plugin_config, event_bus)
                logger.info(f"Initialized plugin: {name}")

            except Exception as e:
                logger.error(f"Failed to initialize plugin {name}: {e}")

    def cleanup_all(self) -> None:
        """
        Cleanup all loaded plugins.
        """
        logger.info("Cleaning up all plugins")

        # Cleanup in reverse order of initialization
        sorted_plugins = sorted(
            self.loaded_plugins.items(),
            key=lambda x: self.plugins.get(
                x[0], PluginMetadata("", "", "", "", priority=99)
            ).priority,
            reverse=True,
        )

        for name, plugin in sorted_plugins:
            try:
                plugin.cleanup()
                logger.info(f"Cleaned up plugin: {name}")
            except Exception as e:
                logger.error(f"Failed to cleanup plugin {name}: {e}")

        # Clear loaded plugins
        self.loaded_plugins.clear()
        logger.info("All plugins cleaned up")

    def _load_plugin_yaml(self, yaml_path: Path) -> PluginMetadata | None:
        """
        Load plugin metadata from plugin.yaml file.

        Args:
            yaml_path: Path to plugin.yaml file

        Returns:
            PluginMetadata or None if failed
        """
        try:
            with yaml_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning(f"Empty plugin.yaml: {yaml_path}")
                return None

            # Validate required fields
            required_fields = ["name", "type", "version", "description"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in {yaml_path}")
                    return None

            # Create metadata
            metadata = PluginMetadata(
                name=data["name"],
                type=data["type"],
                version=data["version"],
                description=data["description"],
                enabled=data.get("enabled", True),
                priority=data.get("priority", 99),
                config=data.get("config", {}),
                dependencies=data.get("dependencies", []),
                cli_commands=data.get("cli_commands", []),
                path=yaml_path.parent,
                class_name=data.get("class_name", ""),
                module_name=data.get("module_name", ""),
            )

            return metadata

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse plugin.yaml {yaml_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load plugin.yaml {yaml_path}: {e}")
            return None

    def _auto_discover_plugin(self, py_file: Path) -> PluginMetadata | None:
        """
        Auto-discover plugin from Python file by inspecting classes.

        Args:
            py_file: Path to Python file

        Returns:
            PluginMetadata or None if not a plugin
        """
        spec = None
        module_added = False
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"temp_plugin_{py_file.stem}", py_file
            )
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            module_added = True
            spec.loader.exec_module(module)

            # Look for plugin classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a plugin class
                if isinstance(attr, type) and issubclass(
                    attr, (BaseModule, BaseAdapter)
                ):
                    # Skip base classes
                    if attr in (BaseModule, BaseAdapter):
                        continue

                    # Determine plugin type
                    plugin_type = (
                        "module" if issubclass(attr, BaseModule) else "adapter"
                    )

                    # Create temporary instance to get name
                    try:
                        temp_instance = attr()
                        plugin_name = temp_instance.name
                    except Exception:
                        plugin_name = (
                            attr.__name__.lower()
                            .replace("module", "")
                            .replace("adapter", "")
                        )

                    # Create metadata
                    metadata = PluginMetadata(
                        name=plugin_name,
                        type=plugin_type,
                        version="0.1.0",
                        description=f"Auto-discovered {plugin_type}: {plugin_name}",
                        enabled=True,
                        priority=99,
                        path=py_file.parent,
                        class_name=attr.__name__,
                        module_name=py_file.stem,
                    )

                    return metadata

            # No plugin class found
            return None

        except Exception as e:
            logger.debug(f"Failed to auto-discover from {py_file}: {e}")
            return None

        finally:
            # Clean up temp module from sys.modules in all cases
            if module_added and spec is not None and spec.name in sys.modules:
                del sys.modules[spec.name]

    def _load_plugin_class(
        self, metadata: PluginMetadata
    ) -> type[BaseModule | BaseAdapter] | None:
        """
        Load plugin class from metadata.

        Args:
            metadata: Plugin metadata

        Returns:
            Plugin class or None if failed
        """
        try:
            # If module_name is specified, import from that module
            if metadata.module_name:
                if metadata.path is None:
                    logger.error(f"No path specified for plugin {metadata.name}")
                    return None

                module_path = metadata.path / f"{metadata.module_name}.py"
                if not module_path.exists():
                    module_path = metadata.path / "__init__.py"

                if not module_path.exists():
                    logger.error(
                        f"Module file not found for plugin {metadata.name}: {module_path}"
                    )
                    return None

                # Load module
                spec = importlib.util.spec_from_file_location(
                    f"plugin_{metadata.name}", module_path
                )
                if spec is None or spec.loader is None:
                    logger.error(f"Failed to create module spec for {metadata.name}")
                    return None

                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)

                # Get plugin class
                if metadata.class_name:
                    plugin_class = getattr(module, metadata.class_name, None)
                else:
                    # Try to find plugin class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(
                            attr, (BaseModule, BaseAdapter)
                        ):
                            if attr not in (BaseModule, BaseAdapter):
                                plugin_class = attr
                                break
                    else:
                        logger.error(
                            f"No plugin class found in module for {metadata.name}"
                        )
                        return None

                if plugin_class is None:
                    logger.error(
                        f"Plugin class '{metadata.class_name}' not found for {metadata.name}"
                    )
                    return None

                # Type assertion: we've verified it's a BaseModule or BaseAdapter subclass
                assert isinstance(plugin_class, type) and issubclass(
                    plugin_class, (BaseModule, BaseAdapter)
                )
                return plugin_class

            else:
                logger.error(f"No module_name specified for plugin {metadata.name}")
                return None

        except Exception as e:
            logger.error(f"Failed to load plugin class for {metadata.name}: {e}")
            return None
