"""
LLM configuration endpoints - manage providers, models, and settings.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from learning_assistant.server.config import get_server_config
from learning_assistant.server.context import ServerContext

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


class ProviderInfo(BaseModel):
    """Provider information."""

    name: str = Field(description="Provider name")
    default_model: str = Field(description="Default model")
    models: list[str] = Field(description="Available models")
    base_url: str | None = Field(default=None, description="API base URL")
    configured: bool = Field(description="Whether API key is configured")


class LLMConfigResponse(BaseModel):
    """LLM configuration response."""

    default_provider: str = Field(description="Current default provider")
    providers: list[ProviderInfo] = Field(description="Available providers")


class UpdateLLMConfigRequest(BaseModel):
    """Request to update LLM configuration."""

    provider: str | None = Field(default=None, description="Provider to configure")
    base_url: str | None = Field(default=None, description="New base URL")
    default_model: str | None = Field(default=None, description="New default model")
    api_key: str | None = Field(default=None, description="API key (optional, for client-side storage)")


class UpdateLLMConfigResponse(BaseModel):
    """Response after updating LLM config."""

    success: bool = Field(description="Update success status")
    message: str = Field(description="Status message")
    config: LLMConfigResponse | None = Field(default=None, description="Updated config")


class SetAPIKeyRequest(BaseModel):
    """Request to set API key for a provider."""

    provider: str = Field(description="Provider name (openai, anthropic, deepseek)")
    api_key: str = Field(description="API key value")


class SetAPIKeyResponse(BaseModel):
    """Response after setting API key."""

    success: bool = Field(description="Success status")
    message: str = Field(description="Status message")


# Config directory for settings
CONFIG_DIR = Path("config")


def get_llm_config() -> dict[str, Any]:
    """Get LLM configuration from settings."""
    config_manager = ServerContext.get_config_manager()
    settings = config_manager.settings_model
    return settings.llm.model_dump() if hasattr(settings, 'llm') else {}


@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config_endpoint():
    """
    Get current LLM configuration.

    Returns:
        LLM configuration with providers and models
    """
    llm_config = get_llm_config()

    default_provider = llm_config.get("default_provider", "openai")
    providers_config = llm_config.get("providers", {})

    providers: list[ProviderInfo] = []
    for name, cfg in providers_config.items():
        # Check if API key is configured (either in config or env)
        api_key = cfg.get("api_key")
        api_key_env = cfg.get("api_key_env", "")
        import os
        has_key = bool(api_key) or bool(os.environ.get(api_key_env))

        providers.append(ProviderInfo(
            name=name,
            default_model=cfg.get("default_model", ""),
            models=cfg.get("models", []),
            base_url=cfg.get("base_url"),
            configured=has_key,
        ))

    return LLMConfigResponse(
        default_provider=default_provider,
        providers=providers,
    )


@router.get("/models/{provider}", response_model=list[str])
async def get_provider_models(provider: str):
    """
    Get available models for a specific provider.

    Args:
        provider: Provider name (openai, anthropic, deepseek)

    Returns:
        List of available models
    """
    llm_config = get_llm_config()
    providers_config = llm_config.get("providers", {})

    if provider not in providers_config:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

    return providers_config[provider].get("models", [])


@router.post("/config", response_model=UpdateLLMConfigResponse)
async def update_llm_config(request: UpdateLLMConfigRequest):
    """
    Update LLM configuration.

    Note: This updates the runtime config. For persistent changes,
    modify config/settings.yaml or config/settings.local.yaml.

    Args:
        request: Update request

    Returns:
        Update result
    """
    try:
        config_manager = ServerContext.get_config_manager()

        # Get current settings
        settings = config_manager.settings_model
        llm_config = settings.llm.model_dump() if hasattr(settings, 'llm') else {}

        if request.provider:
            # Validate provider exists
            if request.provider not in llm_config.get("providers", {}):
                raise HTTPException(
                    status_code=400,
                    detail=f"Provider '{request.provider}' not found"
                )

            # Update default provider
            if request.provider and not request.base_url and not request.default_model:
                llm_config["default_provider"] = request.provider

            # Update provider-specific settings
            if request.base_url:
                llm_config["providers"][request.provider]["base_url"] = request.base_url

            if request.default_model:
                llm_config["providers"][request.provider]["default_model"] = request.default_model

        # Build response
        providers_config = llm_config.get("providers", {})
        providers: list[ProviderInfo] = []
        for name, cfg in providers_config.items():
            import os
            api_key = cfg.get("api_key")
            api_key_env = cfg.get("api_key_env", "")
            has_key = bool(api_key) or bool(os.environ.get(api_key_env))

            providers.append(ProviderInfo(
                name=name,
                default_model=cfg.get("default_model", ""),
                models=cfg.get("models", []),
                base_url=cfg.get("base_url"),
                configured=has_key,
            ))

        return UpdateLLMConfigResponse(
            success=True,
            message="LLM configuration updated (runtime)",
            config=LLMConfigResponse(
                default_provider=llm_config.get("default_provider", "openai"),
                providers=providers,
            ),
        )

    except Exception as e:
        return UpdateLLMConfigResponse(
            success=False,
            message=f"Failed to update config: {str(e)}",
        )


@router.post("/test")
async def test_llm_connection(
    provider: str = "openai",
    model: str | None = None,
):
    """
    Test LLM connection with current configuration.

    Args:
        provider: Provider to test
        model: Specific model to test (optional)

    Returns:
        Test result
    """
    try:
        from learning_assistant.core.llm.service import LLMService
        import os

        llm_config = get_llm_config()

        # Get provider config
        provider_config = llm_config.get("providers", {}).get(provider, {})
        test_model = model or provider_config.get("default_model", "")

        # Get API key from config or environment
        api_key = provider_config.get("api_key")
        if not api_key:
            # Try environment variable
            api_key_env = provider_config.get("api_key_env", f"{provider.upper()}_API_KEY")
            api_key = os.environ.get(api_key_env)

        if not api_key:
            return {
                "success": False,
                "message": f"No API key configured for {provider}. Please add it in settings.",
            }

        # Get base URL if configured
        base_url = provider_config.get("base_url")

        # Create LLM service and test
        llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            model=test_model,
            base_url=base_url,
        )

        # Simple test call
        response = llm_service.call("Say 'OK' if you can hear me.", max_tokens=10)

        return {
            "success": True,
            "message": f"Connection successful with {provider}/{test_model}",
            "response": response.content[:50],
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
        }


@router.get("/models/{provider}/available")
async def get_available_models_dynamic(provider: str, api_key: str | None = None):
    """
    Dynamically fetch available models from provider API.

    Args:
        provider: Provider name (openai, anthropic, deepseek)
        api_key: API key from frontend (optional, overrides config)

    Returns:
        List of available models from API
    """
    try:
        from learning_assistant.core.llm.service import LLMService
        import os

        llm_config = get_llm_config()
        provider_config = llm_config.get("providers", {}).get(provider, {})

        # Get API key: frontend parameter > config > environment
        if not api_key:
            api_key = provider_config.get("api_key")
        if not api_key:
            api_key_env = provider_config.get("api_key_env", f"{provider.upper()}_API_KEY")
            api_key = os.environ.get(api_key_env)

        if not api_key:
            raise HTTPException(
                status_code=400,
                detail=f"No API key configured for {provider}"
            )

        # Get base URL if configured
        base_url = provider_config.get("base_url")
        default_model = provider_config.get("default_model", "")

        # Create service and get models
        llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            model=default_model,
            base_url=base_url,
        )

        models = llm_service.get_available_models()

        return models

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get models: {str(e)}"
        )


@router.post("/apikey", response_model=SetAPIKeyResponse)
async def set_provider_api_key(request: SetAPIKeyRequest):
    """
    Set API key for a specific provider.

    Saves the API key to config/settings.local.yaml file.
    This is the recommended way to configure LLM API keys via WebUI.

    Args:
        request: Provider name and API key

    Returns:
        Success status
    """
    try:
        # Validate provider
        llm_config = get_llm_config()
        if request.provider not in llm_config.get("providers", {}):
            raise HTTPException(
                status_code=400,
                detail=f"Provider '{request.provider}' not found"
            )

        # Load or create settings.local.yaml
        local_settings_file = CONFIG_DIR / "settings.local.yaml"
        local_settings: dict[str, Any] = {}

        if local_settings_file.exists():
            with open(local_settings_file, "r", encoding="utf-8") as f:
                local_settings = yaml.safe_load(f) or {}

        # Ensure llm.providers structure exists
        if "llm" not in local_settings:
            local_settings["llm"] = {}
        if "providers" not in local_settings["llm"]:
            local_settings["llm"]["providers"] = {}

        # Set API key for the provider
        if request.provider not in local_settings["llm"]["providers"]:
            local_settings["llm"]["providers"][request.provider] = {}

        local_settings["llm"]["providers"][request.provider]["api_key"] = request.api_key

        # Save to file
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(local_settings_file, "w", encoding="utf-8") as f:
            yaml.dump(local_settings, f, default_flow_style=False, allow_unicode=True)

        # Reload configuration
        config_manager = ServerContext.get_config_manager()
        config_manager.load_all()

        return SetAPIKeyResponse(
            success=True,
            message=f"API key saved for {request.provider} in settings.local.yaml",
        )

    except Exception as e:
        return SetAPIKeyResponse(
            success=False,
            message=f"Failed to save API key: {str(e)}",
        )


@router.delete("/apikey/{provider}", response_model=SetAPIKeyResponse)
async def delete_provider_api_key(provider: str):
    """
    Remove API key for a specific provider.

    Args:
        provider: Provider name

    Returns:
        Success status
    """
    try:
        local_settings_file = CONFIG_DIR / "settings.local.yaml"

        if not local_settings_file.exists():
            return SetAPIKeyResponse(
                success=True,
                message="No local settings file found",
            )

        with open(local_settings_file, "r", encoding="utf-8") as f:
            local_settings = yaml.safe_load(f) or {}

        # Remove API key
        if "llm" in local_settings and "providers" in local_settings["llm"]:
            if provider in local_settings["llm"]["providers"]:
                if "api_key" in local_settings["llm"]["providers"][provider]:
                    del local_settings["llm"]["providers"][provider]["api_key"]

                    # Save updated file
                    with open(local_settings_file, "w", encoding="utf-8") as f:
                        yaml.dump(local_settings, f, default_flow_style=False, allow_unicode=True)

                    # Reload configuration
                    config_manager = ServerContext.get_config_manager()
                    config_manager.load_all()

        return SetAPIKeyResponse(
            success=True,
            message=f"API key removed for {provider}",
        )

    except Exception as e:
        return SetAPIKeyResponse(
            success=False,
            message=f"Failed to remove API key: {str(e)}",
        )
