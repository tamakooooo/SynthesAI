"""Feishu adapter models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from learning_assistant.core.publishing.models import PublishPayload


FEISHU_TITLE_MAX_LENGTH = 256


class FeishuKnowledgeBaseConfig(BaseModel):
    """Feishu knowledge base adapter configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    app_id: str | None = None
    app_id_env: str = "FEISHU_APP_ID"
    app_secret: str | None = None
    app_secret_env: str = "FEISHU_APP_SECRET"
    space_id: str = ""
    space_id_env: str = "FEISHU_SPACE_ID"
    root_node_token: str = ""
    root_node_token_env: str = "FEISHU_ROOT_NODE_TOKEN"
    publish_modules: list[str] = Field(default_factory=list)
    title_template: str = "{module} | {title}"
    subscriptions: list[str] = Field(default_factory=list)
    space_domain: str = ""
    upload_concurrency: int = 4
    max_image_upload_bytes: int = 20 * 1024 * 1024
    whiteboard_init_wait_seconds: float = 3.0
    poll_max_wait_seconds: float = 60.0
    poll_initial_backoff: float = 1.0
    poll_max_backoff: float = 10.0
    mindmap_inline_decorations: bool = True

    def resolve_space_id(self, env_lookup: Any = None) -> str:
        import os

        lookup = env_lookup or os.environ.get
        return self.space_id or lookup(self.space_id_env) or ""

    def resolve_root_node_token(self, env_lookup: Any = None) -> str:
        import os

        lookup = env_lookup or os.environ.get
        return self.root_node_token or lookup(self.root_node_token_env) or ""


class FeishuPublishResult(BaseModel):
    """Feishu publication result."""

    success: bool
    message: str
    node_token: str | None = None
    document_id: str | None = None
    url: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class FeishuPublishRequest(BaseModel):
    """Feishu publication request."""

    payload: PublishPayload
    parent_node_token: str


def truncate_title(title: str, max_length: int = FEISHU_TITLE_MAX_LENGTH) -> str:
    """Truncate a title to Feishu's docx title length limit (256 chars)."""
    if len(title) <= max_length:
        return title
    if max_length <= 3:
        return title[:max_length]
    return title[: max_length - 3] + "..."


def trim_raw_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep only top-level diagnostic fields from a Feishu API response.

    Drops large nested `data` payloads (block lists, node lists, etc.) while
    preserving the bits useful for debugging: code, msg, request_id, and a
    shallow projection of important id fields.
    """
    if not isinstance(payload, dict):
        return {}

    trimmed: dict[str, Any] = {}
    for key in ("code", "msg", "request_id"):
        if key in payload:
            trimmed[key] = payload[key]

    data = payload.get("data")
    if isinstance(data, dict):
        shallow: dict[str, Any] = {}
        for key in ("wiki_token", "task_id", "node_token", "document_id"):
            if key in data:
                shallow[key] = data[key]
        if shallow:
            trimmed["data"] = shallow
    return trimmed
