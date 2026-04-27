"""
Feishu adapter models.
"""

from typing import Any

from pydantic import BaseModel, Field

from learning_assistant.core.publishing.models import PublishPayload


class FeishuKnowledgeBaseConfig(BaseModel):
    """Feishu knowledge base adapter configuration."""

    enabled: bool = False
    app_id: str | None = None  # Direct app_id value (optional)
    app_id_env: str = "FEISHU_APP_ID"  # Environment variable name (fallback)
    app_secret: str | None = None  # Direct app_secret value (optional)
    app_secret_env: str = "FEISHU_APP_SECRET"  # Environment variable name (fallback)
    space_id: str = ""
    root_node_token: str = ""
    publish_modules: list[str] = Field(default_factory=list)
    overwrite_strategy: str = "create_new"
    title_template: str = "{module} | {title}"
    subscriptions: list[str] = Field(default_factory=list)
    space_domain: str = ""  # Feishu space domain for URL generation (e.g., "yn9l1n0vua")


class FeishuPublishResult(BaseModel):
    """Feishu publication result."""

    success: bool
    message: str
    node_token: str | None = None
    document_id: str | None = None
    url: str | None = None  # Published document URL
    raw_response: dict[str, Any] = Field(default_factory=dict)


class FeishuPublishRequest(BaseModel):
    """Feishu publication request."""

    payload: PublishPayload
    parent_node_token: str
