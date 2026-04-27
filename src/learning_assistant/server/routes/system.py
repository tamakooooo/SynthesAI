"""
System endpoints - health check, readiness, etc.
"""

from loguru import logger

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from learning_assistant.adapters.feishu.adapter import FeishuKnowledgeBaseAdapter
from learning_assistant.adapters.feishu.models import FeishuKnowledgeBaseConfig
from learning_assistant.adapters.feishu.wiki_client import FeishuWikiClient
from learning_assistant.core.publishing.models import PublishBlock, PublishPayload
from learning_assistant.server.context import ServerContext

router = APIRouter(tags=["system"])


class FeishuCheckResponse(BaseModel):
    """Feishu connectivity check response."""

    configured: bool = Field(description="Whether Feishu adapter configuration is complete")
    adapter_loaded: bool = Field(description="Whether Feishu adapter plugin is loaded")
    enabled: bool = Field(description="Whether Feishu publishing is enabled")
    message: str = Field(description="Human readable status")
    config_summary: dict[str, str] = Field(description="Non-sensitive config summary")
    token_verified: bool = Field(default=False, description="Whether Feishu token exchange succeeded")
    space_accessible: bool = Field(default=False, description="Whether space_id is accessible")
    root_node_accessible: bool = Field(default=False, description="Whether root node token is accessible")


class FeishuPublishTestResponse(BaseModel):
    """Feishu test publish response."""

    success: bool = Field(description="Whether publish succeeded")
    message: str = Field(description="Publish status")
    node_token: str | None = Field(default=None, description="Published wiki node token")
    document_id: str | None = Field(default=None, description="Published document id")
    url: str | None = Field(default=None, description="Published document URL")


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns basic health status for monitoring.
    """
    return {"status": "healthy", "service": "synthesai-server"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Returns readiness status indicating if server can handle requests.
    """
    if not ServerContext.is_initialized():
        return {
            "status": "not_ready",
            "message": "ServerContext not initialized",
        }

    return {
        "status": "ready",
        "plugins_loaded": len(ServerContext.plugin_manager.plugins) if ServerContext.plugin_manager else 0,
    }


@router.get("/system/feishu/check", response_model=FeishuCheckResponse)
async def check_feishu_configuration():
    """Check Feishu knowledge base adapter configuration and load state."""
    if not ServerContext.is_initialized():
        raise HTTPException(status_code=503, detail="ServerContext not initialized")

    config_manager = ServerContext.get_config_manager()
    adapters_config = config_manager.adapters_model
    feishu_config = adapters_config.feishu.model_dump() if adapters_config else {}
    feishu_enabled = bool(feishu_config.get("enabled"))
    feishu_inner_config = feishu_config.get("config", {})

    required_fields = ["app_id_env", "app_secret_env", "space_id", "root_node_token"]
    configured = all(bool(feishu_inner_config.get(field)) for field in required_fields)

    plugin_manager = ServerContext.plugin_manager
    adapter = plugin_manager.get_plugin("feishu") if plugin_manager else None
    # Use class name comparison instead of isinstance due to dynamic plugin loading
    adapter_loaded = adapter is not None and type(adapter).__name__ == "FeishuKnowledgeBaseAdapter"

    message = "Feishu adapter ready for configuration validation"
    if not feishu_enabled:
        message = "Feishu adapter is disabled in adapters.yaml"
    elif not configured:
        message = "Feishu adapter is enabled but configuration is incomplete"
    elif not adapter_loaded:
        message = "Feishu adapter is configured but not loaded"

    return FeishuCheckResponse(
        configured=configured,
        adapter_loaded=adapter_loaded,
        enabled=feishu_enabled,
        message=message,
        token_verified=False,
        space_accessible=False,
        root_node_accessible=False,
        config_summary={
            "space_id": feishu_inner_config.get("space_id", ""),
            "root_node_token": feishu_inner_config.get("root_node_token", ""),
            "app_id_env": feishu_inner_config.get("app_id_env", ""),
            "app_secret_env": feishu_inner_config.get("app_secret_env", ""),
        },
    )


@router.post("/system/feishu/verify", response_model=FeishuCheckResponse)
async def verify_feishu_connection():
    """Verify Feishu adapter configuration and tenant token exchange."""
    response = await check_feishu_configuration()

    if not response.enabled or not response.configured:
        return response

    # Use the adapter's actual settings (which includes app_id/app_secret)
    plugin_manager = ServerContext.plugin_manager
    adapter = plugin_manager.get_plugin("feishu") if plugin_manager else None
    if not (adapter is not None and type(adapter).__name__ == "FeishuKnowledgeBaseAdapter"):
        response.message = "Feishu adapter not loaded"
        return response

    try:
        client = FeishuWikiClient(adapter.settings)
        verification = client.verify_configuration()
        response.token_verified = True
        response.space_accessible = bool(verification.get("space_accessible"))
        response.root_node_accessible = bool(verification.get("root_node_accessible"))
        response.message = "Feishu token and knowledge base access verification succeeded"
        return response
    except Exception as exc:
        response.token_verified = False
        response.space_accessible = False
        response.root_node_accessible = False
        response.message = f"Feishu verification failed: {exc}"
        return response


@router.post("/system/feishu/publish-test", response_model=FeishuPublishTestResponse)
async def publish_feishu_test_document():
    """Publish a small test document to Feishu knowledge base."""
    if not ServerContext.is_initialized():
        raise HTTPException(status_code=503, detail="ServerContext not initialized")

    plugin_manager = ServerContext.plugin_manager
    adapter = plugin_manager.get_plugin("feishu") if plugin_manager else None
    # Use class name comparison instead of isinstance due to dynamic plugin loading
    if not (adapter is not None and type(adapter).__name__ == "FeishuKnowledgeBaseAdapter"):
        raise HTTPException(status_code=404, detail="Feishu adapter not loaded")
    if not adapter.settings.enabled:
        raise HTTPException(status_code=400, detail="Feishu adapter is disabled")

    payload = PublishPayload(
        module="video_summary",
        title="SynthesAI Feishu Publish Test",
        summary="This is a test publication generated by the SynthesAI Feishu integration.",
        source_url=None,
        blocks=[
            PublishBlock(type="heading", text="Test Publish", level=2),
            PublishBlock(
                type="paragraph",
                text="If you can see this page in Feishu knowledge base, the publish chain is working.",
            ),
            PublishBlock(
                type="bullet_list",
                items=[
                    "tenant_access_token exchange succeeded",
                    "docx document creation succeeded",
                    "wiki move operation succeeded",
                ],
            ),
        ],
        tags=["feishu", "test"],
        metadata={"source": "system.feishu.publish-test"},
    )

    try:
        result = adapter.push_content(payload.model_dump(mode="json"))
        if not result.success:
            return FeishuPublishTestResponse(
                success=False,
                message=result.message,
            )
        return FeishuPublishTestResponse(
            success=True,
            message=result.message,
            node_token=result.node_token,
            document_id=result.document_id,
            url=result.url,
        )
    except Exception as exc:
        return FeishuPublishTestResponse(
            success=False,
            message=f"Feishu test publish failed: {exc}",
        )
