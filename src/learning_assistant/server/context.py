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
        import os

        if config_dir:
            config_path = Path(config_dir)
        else:
            env_config = os.environ.get("SYNTHESAI_CONFIG_DIR")
            if env_config:
                config_path = Path(env_config)
            else:
                config_path = Path("config")

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
        modules_config = cls.config_manager.modules_model.model_dump()
        for plugin_info in cls.plugin_manager.plugins:
            cls.plugin_manager.load_plugin(plugin_info.name)
        cls.plugin_manager.initialize_all(modules_config, cls.event_bus)
        logger.info(f"Plugins initialized: {len(cls.plugin_manager.plugins)}")

        # Initialize shared AgentAPI (reuse existing initialization)
        cls.shared_api = AgentAPI()
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