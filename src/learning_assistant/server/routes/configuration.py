"""
Unified configuration endpoints for frontend-managed local settings.
"""

from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from learning_assistant.server.config import get_server_config, reset_server_config
from learning_assistant.server.context import ServerContext

router = APIRouter(prefix="/api/v1/configuration", tags=["configuration"])


class ProviderConfigItem(BaseModel):
    """Frontend-editable provider configuration."""

    name: str = Field(description="Provider name")
    api_key: str | None = Field(default=None, description="API key stored in local settings")
    api_key_env: str = Field(default="", description="Environment variable name for API key")
    default_model: str = Field(description="Default model")
    models: list[str] = Field(default_factory=list, description="Available model list")
    base_url: str | None = Field(default=None, description="Custom API base URL")


class FeishuConfigItem(BaseModel):
    """Frontend-editable Feishu knowledge base configuration."""

    enabled: bool = Field(default=False, description="Whether Feishu publishing is enabled")
    app_id: str | None = Field(default=None, description="Feishu app id (direct value)")
    app_id_env: str = Field(default="FEISHU_APP_ID", description="Env var for Feishu app id")
    app_secret: str | None = Field(default=None, description="Feishu app secret (direct value)")
    app_secret_env: str = Field(
        default="FEISHU_APP_SECRET",
        description="Env var for Feishu app secret",
    )
    space_id: str = Field(default="", description="Feishu knowledge base space id")
    root_node_token: str = Field(default="", description="Root node token for publishing")
    publish_modules: list[str] = Field(default_factory=list, description="Modules allowed to publish")
    title_template: str = Field(default="{module} | {title}", description="Document title template")
    overwrite_strategy: str = Field(default="create_new", description="Publication strategy")


class ModuleConfigItem(BaseModel):
    """Frontend-editable module config summary."""

    name: str
    enabled: bool
    priority: int


class ServerFrontendConfig(BaseModel):
    """Frontend-editable server config."""

    host: str
    port: int
    auth_enabled: bool
    api_key_env: str
    sync_request_timeout: int
    task_polling_timeout: int
    max_concurrent: int
    max_queue_size: int
    result_ttl: int


class FrontendConfigResponse(BaseModel):
    """Frontend configuration response."""

    file_path: str = Field(description="Managed local settings file path")
    exists: bool = Field(description="Whether local settings file exists")
    default_provider: str = Field(description="Default provider")
    providers: list[ProviderConfigItem] = Field(description="Provider configurations")
    feishu: FeishuConfigItem = Field(description="Feishu knowledge base configuration")
    modules: list[ModuleConfigItem] = Field(description="Module configurations")
    server: ServerFrontendConfig = Field(description="Server configuration")


class SaveFrontendConfigRequest(BaseModel):
    """Save frontend-managed configuration."""

    default_provider: str = Field(description="Default provider")
    providers: list[ProviderConfigItem] = Field(description="Provider configurations")
    feishu: FeishuConfigItem = Field(description="Feishu knowledge base configuration")
    modules: list[ModuleConfigItem] = Field(description="Module configurations")
    server: ServerFrontendConfig = Field(description="Server configuration")


class SaveFrontendConfigResponse(BaseModel):
    """Save frontend config response."""

    success: bool = Field(description="Save status")
    message: str = Field(description="Status message")
    config: FrontendConfigResponse | None = Field(default=None, description="Updated config")


def _get_local_settings_file() -> Path:
    """Resolve settings.local.yaml from the active configuration directory."""
    config_manager = ServerContext.get_config_manager()
    return config_manager.config_dir / "settings.local.yaml"


def _read_local_settings() -> dict:
    """Read local settings file."""
    local_settings_file = _get_local_settings_file()
    if not local_settings_file.exists():
        return {}

    with local_settings_file.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _merge_dict(base: dict, override: dict) -> dict:
    """Deep merge override into base without dropping unrelated keys."""
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def _build_frontend_config_response() -> FrontendConfigResponse:
    """Build frontend config response from effective settings and local overrides."""
    config_manager = ServerContext.get_config_manager()
    settings = config_manager.settings_model
    adapters = config_manager.adapters_model
    modules = config_manager.modules_model
    if settings is None:
        raise HTTPException(status_code=500, detail="Settings not loaded")
    if adapters is None:
        raise HTTPException(status_code=500, detail="Adapters not loaded")
    if modules is None:
        raise HTTPException(status_code=500, detail="Modules not loaded")

    local_settings = _read_local_settings()
    local_providers = local_settings.get("llm", {}).get("providers", {})

    providers: list[ProviderConfigItem] = []
    for name, provider in settings.llm.providers.items():
        local_provider = local_providers.get(name, {})
        provider_dict = provider.model_dump()
        providers.append(
            ProviderConfigItem(
                name=name,
                api_key=local_provider.get("api_key"),
                api_key_env=provider_dict.get("api_key_env", ""),
                default_model=provider_dict.get("default_model", ""),
                models=provider_dict.get("models", []),
                base_url=provider_dict.get("base_url"),
            )
        )

    feishu_adapter = adapters.feishu.model_dump()
    feishu_config = feishu_adapter.get("config", {})
    server_config = get_server_config()
    local_settings_file = _get_local_settings_file()
    module_items = modules.model_dump().items()

    return FrontendConfigResponse(
        file_path=str(local_settings_file),
        exists=local_settings_file.exists(),
        default_provider=settings.llm.default_provider,
        providers=providers,
        feishu=FeishuConfigItem(
            enabled=feishu_adapter.get("enabled", False),
            app_id=feishu_config.get("app_id"),
            app_id_env=feishu_config.get("app_id_env", "FEISHU_APP_ID"),
            app_secret=feishu_config.get("app_secret"),
            app_secret_env=feishu_config.get("app_secret_env", "FEISHU_APP_SECRET"),
            space_id=feishu_config.get("space_id", ""),
            root_node_token=feishu_config.get("root_node_token", ""),
            publish_modules=feishu_config.get("publish_modules", []),
            title_template=feishu_config.get("title_template", "{module} | {title}"),
            overwrite_strategy=feishu_config.get("overwrite_strategy", "create_new"),
        ),
        modules=[
            ModuleConfigItem(
                name=name,
                enabled=bool(module.get("enabled", True)),
                priority=int(module.get("priority", 99)),
            )
            for name, module in module_items
        ],
        server=ServerFrontendConfig(
            host=server_config.host,
            port=server_config.port,
            auth_enabled=server_config.auth.enabled,
            api_key_env=server_config.auth.api_key_env,
            sync_request_timeout=server_config.timeouts.sync_request,
            task_polling_timeout=server_config.timeouts.task_polling,
            max_concurrent=server_config.task_queue.max_concurrent,
            max_queue_size=server_config.task_queue.max_queue_size,
            result_ttl=server_config.task_queue.result_ttl,
        ),
    )


@router.get("", response_model=FrontendConfigResponse)
async def get_frontend_configuration():
    """Get the unified frontend-managed configuration."""
    return _build_frontend_config_response()


@router.post("", response_model=SaveFrontendConfigResponse)
async def save_frontend_configuration(request: SaveFrontendConfigRequest):
    """Persist frontend-managed configuration into settings.local.yaml."""
    try:
        config_manager = ServerContext.get_config_manager()
        settings = config_manager.settings_model
        if settings is None:
            raise HTTPException(status_code=500, detail="Settings not loaded")

        allowed_providers = set(settings.llm.providers.keys())
        request_provider_names = [provider.name for provider in request.providers]

        if request.default_provider not in allowed_providers:
            raise HTTPException(status_code=400, detail="Invalid default provider")

        unknown_providers = [name for name in request_provider_names if name not in allowed_providers]
        if unknown_providers:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown providers: {', '.join(sorted(unknown_providers))}",
            )

        local_settings = _read_local_settings()
        local_settings.setdefault("llm", {})
        local_settings["llm"]["default_provider"] = request.default_provider
        existing_providers = local_settings["llm"].get("providers", {})
        updated_providers: dict[str, dict[str, object]] = {}

        for provider in request.providers:
            provider_payload: dict[str, object] = dict(existing_providers.get(provider.name, {}))
            provider_payload["api_key_env"] = provider.api_key_env
            provider_payload["default_model"] = provider.default_model
            if provider.models:
                provider_payload["models"] = provider.models
            if provider.base_url:
                provider_payload["base_url"] = provider.base_url
            elif "base_url" in provider_payload:
                provider_payload.pop("base_url", None)
            if provider.api_key:
                provider_payload["api_key"] = provider.api_key
            else:
                provider_payload.pop("api_key", None)

            updated_providers[provider.name] = provider_payload

        local_settings["llm"]["providers"] = _merge_dict(existing_providers, updated_providers)

        existing_adapters = local_settings.get("adapters", {})
        feishu_config_data: dict[str, object] = {
            "app_id_env": request.feishu.app_id_env,
            "app_secret_env": request.feishu.app_secret_env,
            "space_id": request.feishu.space_id,
            "root_node_token": request.feishu.root_node_token,
            "publish_modules": request.feishu.publish_modules,
            "title_template": request.feishu.title_template,
            "overwrite_strategy": request.feishu.overwrite_strategy,
        }
        if request.feishu.app_id:
            feishu_config_data["app_id"] = request.feishu.app_id
        if request.feishu.app_secret:
            feishu_config_data["app_secret"] = request.feishu.app_secret

        local_settings["adapters"] = _merge_dict(
            existing_adapters,
            {
                "feishu": {
                "enabled": request.feishu.enabled,
                "priority": 1,
                "config": feishu_config_data,
                }
            },
        )

        local_settings["event_bus"] = _merge_dict(
            local_settings.get("event_bus", {}),
            {
                "subscriptions": _merge_dict(
                    local_settings.get("event_bus", {}).get("subscriptions", {}),
                    {
                        "feishu": [
                            {
                                "video_summary": "video.summarized",
                                "link_learning": "link.processed",
                                "vocabulary": "vocabulary.extracted",
                            }[module]
                            for module in request.feishu.publish_modules
                            if module in {"video_summary", "link_learning", "vocabulary"}
                        ]
                    },
                )
            },
        )

        existing_modules = local_settings.get("modules", {})
        local_settings["modules"] = _merge_dict(
            existing_modules,
            {
                module.name: _merge_dict(
                    existing_modules.get(module.name, {}),
                    {
                        "enabled": module.enabled,
                        "priority": module.priority,
                    },
                )
                for module in request.modules
            },
        )
        local_settings["server"] = _merge_dict(local_settings.get("server", {}), {
            "host": request.server.host,
            "port": request.server.port,
            "auth": {
                "enabled": request.server.auth_enabled,
                "api_key_env": request.server.api_key_env,
            },
            "task_queue": {
                "max_concurrent": request.server.max_concurrent,
                "max_queue_size": request.server.max_queue_size,
                "result_ttl": request.server.result_ttl,
            },
            "timeouts": {
                "sync_request": request.server.sync_request_timeout,
                "task_polling": request.server.task_polling_timeout,
            },
        })

        local_settings_file = _get_local_settings_file()
        local_settings_file.parent.mkdir(parents=True, exist_ok=True)
        with local_settings_file.open("w", encoding="utf-8") as file:
            yaml.dump(local_settings, file, default_flow_style=False, allow_unicode=True, sort_keys=False)

        ServerContext.reload_plugins()
        reset_server_config()

        return SaveFrontendConfigResponse(
            success=True,
            message=f"Configuration saved to {local_settings_file}",
            config=_build_frontend_config_response(),
        )

    except HTTPException:
        raise
    except Exception as exc:
        return SaveFrontendConfigResponse(
            success=False,
            message=f"Failed to save configuration: {exc}",
        )
