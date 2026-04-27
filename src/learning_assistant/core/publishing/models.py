"""
Shared publishing payloads for adapter integrations.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


PublishBlockType = Literal["heading", "paragraph", "bullet_list", "quote", "code", "image", "table"]


class PublishBlock(BaseModel):
    """Structured content block for adapter publishing."""

    type: PublishBlockType
    text: str = ""
    level: int = 1
    items: list[str] = Field(default_factory=list)
    language: str | None = None
    # Image support fields
    image_path: str | None = None  # Local image path for upload
    image_token: str | None = None  # Feishu file_token after upload
    # Table support fields
    table_rows: list[list[str]] = Field(default_factory=list)  # Table data as rows of cells
    table_headers: list[str] = Field(default_factory=list)  # Optional header row


class PublishPayload(BaseModel):
    """Normalized content payload for external publication."""

    module: str
    title: str
    summary: str | None = None
    source_url: str | None = None
    blocks: list[PublishBlock] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime | None = None
    # Mindmap support fields
    mindmap_structure: dict[str, Any] | None = None  # Mindmap tree structure
    mindmap_url: str | None = None  # Generated mindmap URL
