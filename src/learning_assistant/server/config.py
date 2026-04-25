"""
Server configuration for SynthesAI HTTP API.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration."""

    enabled: bool = Field(default=True, description="Enable API key authentication")
    api_key_env: str = Field(
        default="SYNTHESAI_API_KEY", description="Environment variable for API key"
    )
    whitelist_paths: list[str] = Field(
        default=["/health", "/ready", "/docs", "/openapi.json"],
        description="Paths that don't require authentication",
    )


class TaskQueueConfig(BaseModel):
    """Task queue configuration."""

    max_concurrent: int = Field(default=3, description="Maximum concurrent tasks")
    max_queue_size: int = Field(default=100, description="Maximum queue size")
    result_ttl: int = Field(default=3600, description="Result TTL in seconds")


class TimeoutConfig(BaseModel):
    """Timeout configuration."""

    sync_request: int = Field(default=120, description="Sync request timeout (seconds)")
    task_polling: int = Field(default=10, description="Task status polling interval")


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    auth: AuthConfig = Field(default_factory=AuthConfig)
    task_queue: TaskQueueConfig = Field(default_factory=TaskQueueConfig)
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge nested server configuration dictionaries."""
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_server_config(config_path: Path | None = None) -> ServerConfig:
    """
    Load server configuration from YAML file.

    Args:
        config_path: Path to server.yaml. If None, uses default location.

    Returns:
        ServerConfig instance
    """
    if config_path is None:
        # Default: SYNTHESAI_CONFIG_DIR/server.yaml or config/server.yaml
        config_dir = os.environ.get("SYNTHESAI_CONFIG_DIR")
        if config_dir:
            config_dir_path = Path(config_dir)
        else:
            config_dir_path = Path("config")
        config_path = config_dir_path / "server.yaml"
    else:
        config_dir_path = config_path.parent

    merged_server_data: dict[str, Any] = {}

    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
        merged_server_data = _deep_merge_dict(merged_server_data, data.get("server", {}))

    local_settings_path = config_dir_path / "settings.local.yaml"
    if local_settings_path.exists():
        with local_settings_path.open(encoding="utf-8") as f:
            local_data: dict[str, Any] = yaml.safe_load(f) or {}
        merged_server_data = _deep_merge_dict(merged_server_data, local_data.get("server", {}))

    if merged_server_data:
        return ServerConfig(**merged_server_data)

    return ServerConfig()


def get_api_key(config: ServerConfig) -> str | None:
    """
    Get API key from environment variable.

    Args:
        config: Server configuration

    Returns:
        API key or None if not set
    """
    return os.environ.get(config.auth.api_key_env)


# Singleton config instance
_config: ServerConfig | None = None


def get_server_config() -> ServerConfig:
    """
    Get server configuration singleton.

    Returns:
        ServerConfig instance
    """
    global _config
    if _config is None:
        _config = load_server_config()
    return _config


def reset_server_config() -> None:
    """Reset cached server config so local overrides can take effect."""
    global _config
    _config = None
