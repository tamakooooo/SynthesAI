"""
Server context for managing shared instances.

In server mode, we need shared instances of ConfigManager and AgentAPI
to avoid repeated initialization on every request.
"""

from typing import Any

from loguru import logger

from learning_assistant.api.agent_api import AgentAPI
from learning_assistant.core.config_manager import ConfigManager
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.plugin_manager import PluginManager


class ServerContext:
    """
    Server context managing shared instances.

    Initialized once at server startup, reused for all requests.
    """

    config_manager: ConfigManager | None = None
    plugin_manager: PluginManager | None = None
    event_bus: EventBus | None = None
    shared_api: AgentAPI | None = None
    _initialized: bool = False

    @classmethod
    def _resolve_config_path(cls, config_dir: str | None = None):
        """Resolve active configuration directory."""
        from pathlib import Path
        import os

        if config_dir:
            return Path(config_dir)

        env_config = os.environ.get("SYNTHESAI_CONFIG_DIR")
        if env_config:
            return Path(env_config)

        return Path("config")

    @classmethod
    def _build_combined_plugin_config(cls) -> dict[str, Any]:
        """Build merged module and adapter config for plugin initialization."""
        if cls.config_manager is None:
            raise RuntimeError("ConfigManager not available")

        modules_model = cls.config_manager.modules_model
        adapters_model = cls.config_manager.adapters_model
        if modules_model is None or adapters_model is None:
            raise RuntimeError("Plugin configuration not loaded")

        modules_config = modules_model.model_dump()
        adapters_config = adapters_model.model_dump()
        adapter_subscriptions = adapters_config.get("event_bus", {}).get("subscriptions", {})

        combined_plugin_config = dict(modules_config)
        for adapter_name, adapter_config in adapters_config.items():
            if adapter_name == "event_bus":
                continue
            adapter_payload = dict(adapter_config)
            adapter_payload["subscriptions"] = adapter_subscriptions.get(adapter_name, [])
            combined_plugin_config[adapter_name] = adapter_payload

        return combined_plugin_config

    @classmethod
    def initialize(cls, config_dir: str | None = None) -> None:
        """
        Initialize shared instances at server startup.

        Args:
            config_dir: Optional custom config directory path
        """
        if cls._initialized:
            logger.warning("ServerContext already initialized, skipping")
            return

        logger.info("Initializing ServerContext...")

        # Determine config directory
        from pathlib import Path

        config_path = cls._resolve_config_path(config_dir)

        # Initialize ConfigManager
        cls.config_manager = ConfigManager(config_path)
        cls.config_manager.load_all()
        logger.info(f"Config loaded from {config_path}")

        # Initialize EventBus
        cls.event_bus = EventBus()

        # Initialize PluginManager
        plugin_dirs = [
            config_path.parent / "src" / "learning_assistant" / "modules",
            config_path.parent / "src" / "learning_assistant" / "adapters",
            Path("plugins"),
        ]
        cls.plugin_manager = PluginManager(plugin_dirs=plugin_dirs)
        cls.plugin_manager.discover_plugins()

        # Load and initialize plugins
        combined_plugin_config = cls._build_combined_plugin_config()
        for plugin_name in cls.plugin_manager.plugins.keys():
            cls.plugin_manager.load_plugin(plugin_name)
        cls.plugin_manager.initialize_all(combined_plugin_config, cls.event_bus)
        logger.info(f"Plugins initialized: {len(cls.plugin_manager.plugins)}")

        # Initialize shared AgentAPI (reuse existing initialization)
        cls.shared_api = AgentAPI(config_path)
        logger.info("AgentAPI instance created")

        cls._initialized = True
        logger.info("ServerContext initialization complete")

    @classmethod
    def get_api(cls) -> AgentAPI:
        """
        Get shared AgentAPI instance.

        Raises:
            RuntimeError: If context not initialized

        Returns:
            Shared AgentAPI instance
        """
        if not cls._initialized:
            raise RuntimeError("ServerContext not initialized")
        if cls.shared_api is None:
            raise RuntimeError("AgentAPI not available")
        return cls.shared_api

    @classmethod
    def get_config_manager(cls) -> ConfigManager:
        """
        Get shared ConfigManager instance.

        Raises:
            RuntimeError: If context not initialized

        Returns:
            Shared ConfigManager instance
        """
        if not cls._initialized:
            raise RuntimeError("ServerContext not initialized")
        if cls.config_manager is None:
            raise RuntimeError("ConfigManager not available")
        return cls.config_manager

    @classmethod
    def reload_plugins(cls) -> None:
        """Reload plugins using the active configuration directory."""
        if not cls._initialized:
            raise RuntimeError("ServerContext not initialized")
        if cls.config_manager is None or cls.plugin_manager is None or cls.event_bus is None:
            raise RuntimeError("ServerContext is missing required components")

        logger.info("Reloading plugins in ServerContext")
        cls.config_manager.load_all()
        cls.plugin_manager.cleanup_all()
        cls.plugin_manager.plugins.clear()
        cls.plugin_manager.discover_plugins()

        combined_plugin_config = cls._build_combined_plugin_config()
        for plugin_name in cls.plugin_manager.plugins.keys():
            cls.plugin_manager.load_plugin(plugin_name)
        cls.plugin_manager.initialize_all(combined_plugin_config, cls.event_bus)
        cls.shared_api = AgentAPI(cls.config_manager.config_dir)
        logger.info(f"Plugins reloaded: {len(cls.plugin_manager.loaded_plugins)}")

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if context is initialized."""
        return cls._initialized

    @classmethod
    def reset(cls) -> None:
        """Reset context (for testing)."""
        cls.config_manager = None
        cls.plugin_manager = None
        cls.event_bus = None
        cls.shared_api = None
        cls._initialized = False
        logger.debug("ServerContext reset")
