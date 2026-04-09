"""
Configuration Manager for Learning Assistant.

This module handles loading, validation, and management of configuration files.
"""

import os
from pathlib import Path
from typing import Any, TypeVar

import yaml
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

T = TypeVar("T", bound=BaseModel)


class ConfigManager:
    """
    Configuration Manager for Learning Assistant.

    Handles:
    - YAML configuration loading
    - Pydantic validation
    - Environment variable override
    - Default configuration generation
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """
        Initialize ConfigManager.

        Args:
            config_dir: Configuration directory path (default: config/)
        """
        self.config_dir = config_dir or Path("config")
        self.settings_model: Settings | None = None
        self.modules_model: Modules | None = None
        self.adapters_model: Adapters | None = None
        logger.info(f"ConfigManager initialized with config_dir: {self.config_dir}")

    def load_all(self) -> None:
        """
        Load all configuration files.

        Loads:
        - settings.yaml (global settings)
        - settings.local.yaml (local overrides, if exists)
        - modules.yaml (module configurations)
        - adapters.yaml (adapter configurations)
        """
        logger.info("Loading all configurations")

        # Load settings.yaml
        settings_file = self.config_dir / "settings.yaml"
        if settings_file.exists():
            settings_dict = self._load_yaml_file(settings_file)

            # Load settings.local.yaml if exists (for API keys and local overrides)
            local_settings_file = self.config_dir / "settings.local.yaml"
            if local_settings_file.exists():
                logger.info("Found settings.local.yaml, merging with settings.yaml")
                local_settings_dict = self._load_yaml_file(local_settings_file)
                # Deep merge local settings (local overrides global)
                settings_dict = self._deep_merge(settings_dict, local_settings_dict)

            self.settings_model = self.validate_config(settings_dict, Settings)
            logger.info("Settings loaded and validated successfully")
        else:
            logger.warning(f"Settings file not found: {settings_file}")
            self.settings_model = Settings()

        # Load modules.yaml
        modules_file = self.config_dir / "modules.yaml"
        if modules_file.exists():
            modules_dict = self._load_yaml_file(modules_file)
            # Extract 'modules' key if present (YAML structure has top-level 'modules' key)
            if "modules" in modules_dict:
                modules_dict = modules_dict["modules"]
            self.modules_model = self.validate_config(modules_dict, Modules)
            logger.info("Modules loaded and validated successfully")
        else:
            logger.warning(f"Modules file not found: {modules_file}")
            self.modules_model = Modules()

        # Load adapters.yaml
        adapters_file = self.config_dir / "adapters.yaml"
        if adapters_file.exists():
            adapters_dict = self._load_yaml_file(adapters_file)
            # Extract 'adapters' key if present, keep 'event_bus' at top level
            if "adapters" in adapters_dict:
                adapters_inner = adapters_dict["adapters"]
                # Preserve event_bus at top level
                if "event_bus" in adapters_dict:
                    adapters_inner["event_bus"] = adapters_dict["event_bus"]
                adapters_dict = adapters_inner
            self.adapters_model = self.validate_config(adapters_dict, Adapters)
            logger.info("Adapters loaded and validated successfully")
        else:
            logger.warning(f"Adapters file not found: {adapters_file}")
            self.adapters_model = Adapters()

    def get_llm_config(self, provider: str | None = None) -> dict[str, Any]:
        """
        Get LLM provider configuration with API key resolution.

        API key priority:
        1. Environment variable (highest priority)
        2. Configuration file (api_key field in settings.yaml or settings.local.yaml)
        3. None (if not found)

        Args:
            provider: Provider name (openai, anthropic, deepseek)
                     If None, uses default_provider from settings

        Returns:
            LLM provider configuration dict with API key resolved

        Raises:
            ValueError: If provider not found or settings not loaded
        """
        if not self.settings_model:
            raise ValueError("Settings not loaded. Call load_all() first.")

        # Use default provider if not specified
        if provider is None:
            provider = self.settings_model.llm.default_provider

        # Get provider config
        if provider not in self.settings_model.llm.providers:
            raise ValueError(f"Provider '{provider}' not found in configuration")

        provider_config = self.settings_model.llm.providers[provider]

        # Convert to dict
        config_dict = provider_config.model_dump()

        # Resolve API key with priority: env var > config file > None
        api_key = None

        # 1. Try environment variable first (highest priority)
        api_key_env = provider_config.api_key_env
        if api_key_env:
            api_key = os.environ.get(api_key_env)
            if api_key:
                logger.debug(
                    f"API key for {provider} loaded from environment variable: {api_key_env}"
                )

        # 2. Try config file api_key field
        if not api_key and provider_config.api_key:
            api_key = provider_config.api_key
            logger.debug(f"API key for {provider} loaded from configuration file")

        # 3. Set api_key in config dict
        if api_key:
            config_dict["api_key"] = api_key
        else:
            logger.warning(
                f"API key for {provider} not found. "
                f"Set {api_key_env} environment variable or add 'api_key' to settings.yaml"
            )
            config_dict["api_key"] = None

        # Add cost tracking config
        config_dict["cost_tracking"] = (
            self.settings_model.llm.cost_tracking.model_dump()
        )

        return config_dict

    def get_plugin_config(self, plugin_name: str) -> dict[str, Any]:
        """
        Get plugin configuration by name (module or adapter).

        Args:
            plugin_name: Plugin name (e.g., 'video_summary', 'feishu')

        Returns:
            Plugin configuration dict

        Raises:
            ValueError: If plugin not found or configs not loaded
        """
        # Try to find in modules first
        if self.modules_model:
            if hasattr(self.modules_model, plugin_name):
                module_config = getattr(self.modules_model, plugin_name)
                return {
                    "enabled": module_config.enabled,
                    "priority": module_config.priority,
                    "config": module_config.config,
                }

        # Try to find in adapters
        if self.adapters_model:
            if hasattr(self.adapters_model, plugin_name):
                adapter_config = getattr(self.adapters_model, plugin_name)
                return {
                    "enabled": adapter_config.enabled,
                    "priority": adapter_config.priority,
                    "config": adapter_config.config,
                }

        raise ValueError(f"Plugin '{plugin_name}' not found in modules or adapters")

    def validate_config(self, config: dict[str, Any], schema: type[T]) -> T:
        """
        Validate configuration using Pydantic schema.

        Args:
            config: Configuration dict
            schema: Pydantic validation model class

        Returns:
            Validated configuration model

        Raises:
            ValidationError: If validation fails
        """
        try:
            validated = schema(**config)
            logger.info(f"Configuration validated successfully for {schema.__name__}")
            return validated
        except ValidationError as e:
            logger.error(f"Configuration validation failed for {schema.__name__}: {e}")
            raise

    def generate_default_config(self) -> None:
        """
        Generate default configuration files if they don't exist.
        """
        logger.info("Generating default configurations")

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Generate settings.yaml
        settings_file = self.config_dir / "settings.yaml"
        if not settings_file.exists():
            default_settings = Settings()
            self._write_yaml_file(settings_file, default_settings.model_dump())
            logger.info(f"Generated default settings.yaml at {settings_file}")

        # Generate modules.yaml
        modules_file = self.config_dir / "modules.yaml"
        if not modules_file.exists():
            default_modules = Modules()
            self._write_yaml_file(modules_file, default_modules.model_dump())
            logger.info(f"Generated default modules.yaml at {modules_file}")

        # Generate adapters.yaml
        adapters_file = self.config_dir / "adapters.yaml"
        if not adapters_file.exists():
            default_adapters = Adapters()
            self._write_yaml_file(adapters_file, default_adapters.model_dump())
            logger.info(f"Generated default adapters.yaml at {adapters_file}")

    def _load_yaml_file(self, file_path: Path) -> dict[str, Any]:
        """
        Load YAML file and return as dict.

        Args:
            file_path: Path to YAML file

        Returns:
            Configuration dict

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config is None:
                    logger.warning(f"YAML file is empty: {file_path}")
                    return {}
                # yaml.safe_load returns Any, assert it's a dict
                if not isinstance(config, dict):
                    raise ValueError(
                        f"Invalid YAML structure in {file_path}: expected dict"
                    )
                return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {file_path}: {e}")
            raise

    def _write_yaml_file(self, file_path: Path, config: dict[str, Any]) -> None:
        """
        Write configuration dict to YAML file.

        Args:
            file_path: Path to YAML file
            config: Configuration dict
        """
        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            logger.debug(f"Wrote configuration to {file_path}")

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Deep merge two dictionaries (override takes precedence).

        Args:
            base: Base dictionary
            override: Override dictionary (values take precedence)

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override value
                result[key] = value

        return result


# Pydantic validation models


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = "Learning Assistant"
    version: str = "0.1.0"
    log_level: str = "INFO"
    log_file: str = "logs/learning_assistant.log"


class LLMProviderConfig(BaseModel):
    """LLM provider configuration."""

    api_key: str | None = None  # Optional: API key from config file
    api_key_env: str = ""  # Environment variable name for API key
    default_model: str
    models: list[str] = Field(default_factory=list)
    base_url: str | None = None
    timeout: int = 30
    max_retries: int = 3


class CostTrackingConfig(BaseModel):
    """Cost tracking configuration."""

    enabled: bool = True
    daily_limit: float = 10.0
    monthly_limit: float = 100.0
    warning_threshold: float = 0.8


class LLMConfig(BaseModel):
    """LLM configuration."""

    default_provider: str = "openai"
    providers: dict[str, LLMProviderConfig] = Field(default_factory=dict)
    cost_tracking: CostTrackingConfig = CostTrackingConfig()


class CacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = True
    directory: str = "data/cache"
    expiry_days: int = 7
    max_size_mb: int = 500


class HistoryConfig(BaseModel):
    """History configuration."""

    enabled: bool = True
    directory: str = "data/history"
    max_records: int = 1000
    cleanup_days: int = 30


class TaskConfig(BaseModel):
    """Task configuration."""

    enabled: bool = True
    directory: str = "data/tasks"
    auto_resume: bool = False
    max_concurrent: int = 3


class OutputConfig(BaseModel):
    """Output configuration."""

    default_format: str = "markdown"
    directory: str = "data/outputs"
    template_directory: str = "templates/outputs"
    auto_subdirs: bool = True


class PluginConfig(BaseModel):
    """Plugin configuration."""

    directories: list[str] = Field(
        default_factory=lambda: ["src/learning_assistant/modules"]
    )
    hot_reload: bool = False
    load_timeout: int = 5


class PerformanceConfig(BaseModel):
    """Performance configuration."""

    multiprocessing: bool = True
    worker_count: int = 4
    memory_limit_mb: int = 500


class SecurityConfig(BaseModel):
    """Security configuration."""

    validate_api_keys: bool = True
    encrypt_storage: bool = False
    allow_insecure: bool = False


class Settings(BaseModel):
    """Global settings configuration."""

    app: AppConfig = AppConfig()
    llm: LLMConfig = LLMConfig()
    cache: CacheConfig = CacheConfig()
    history: HistoryConfig = HistoryConfig()
    task: TaskConfig = TaskConfig()
    output: OutputConfig = OutputConfig()
    plugin: PluginConfig = PluginConfig()
    performance: PerformanceConfig = PerformanceConfig()
    security: SecurityConfig = SecurityConfig()


class ModuleConfig(BaseModel):
    """Module configuration base."""

    enabled: bool = False
    priority: int = 99
    config: dict[str, Any] = Field(default_factory=dict)


class Modules(BaseModel):
    """All modules configuration."""

    video_summary: ModuleConfig = ModuleConfig()
    link_learning: ModuleConfig = ModuleConfig()
    vocabulary: ModuleConfig = ModuleConfig()


class AdapterConfig(BaseModel):
    """Adapter configuration base."""

    enabled: bool = False
    priority: int = 99
    config: dict[str, Any] = Field(default_factory=dict)


class EventBusAdapterConfig(BaseModel):
    """Event bus adapter configuration."""

    enabled: bool = True
    subscriptions: dict[str, list[str]] = Field(default_factory=dict)
    retry: dict[str, Any] = Field(default_factory=dict)


class Adapters(BaseModel):
    """All adapters configuration."""

    feishu: AdapterConfig = AdapterConfig()
    siyuan: AdapterConfig = AdapterConfig()
    obsidian: AdapterConfig = AdapterConfig()
    event_bus: EventBusAdapterConfig = EventBusAdapterConfig()
