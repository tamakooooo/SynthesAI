"""Convert normalized publish payloads to Feishu docx blocks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learning_assistant.core.publishing.models import PublishBlock, PublishPayload


@dataclass
class TableData:
    """Structured table data for deferred creation via table API."""

    headers: list[str]
    rows: list[list[str]]
    anchor_text_block_index: int

    @property
    def row_size(self) -> int:
        return len(self.rows) + (1 if self.headers else 0)

    @property
    def column_size(self) -> int:
        widths = [len(self.headers)] if self.headers else []
        widths.extend(len(r) for r in self.rows)
        return max(widths) if widths else 0


@dataclass
class ImageData:
    """Local image to upload after document creation."""

    image_path: str
    anchor_text_block_index: int


@dataclass
class BuildResult:
    """Result of building Feishu blocks from a PublishPayload.

    text_blocks: created in initial document creation call
    images: uploaded and inserted after preceding text block
    tables: created via dedicated table API after preceding text block
    """

    text_blocks: list[dict[str, Any]] = field(default_factory=list)
    images: list[ImageData] = field(default_factory=list)
    tables: list[TableData] = field(default_factory=list)


class FeishuDocumentBuilder:
    """Build Feishu docx block payloads from PublishPayload."""

    def build(self, payload: PublishPayload) -> BuildResult:
        result = BuildResult()

        if payload.summary:
            result.text_blocks.append(self._paragraph_block(payload.summary))

        for block in payload.blocks:
            anchor = len(result.text_blocks) - 1
            if block.type == "heading":
                result.text_blocks.append(self._heading_block(block))
            elif block.type == "bullet_list":
                for item in block.items:
                    result.text_blocks.append(self._bullet_block(item))
            elif block.type == "quote":
                result.text_blocks.append(self._quote_block(block.text))
            elif block.type == "code":
                result.text_blocks.append(self._code_block(block))
            elif block.type == "image":
                if block.image_path:
                    result.images.append(
                        ImageData(image_path=block.image_path, anchor_text_block_index=anchor)
                    )
            elif block.type == "table":
                if block.table_rows or block.table_headers:
                    result.tables.append(
                        TableData(
                            headers=list(block.table_headers),
                            rows=[list(r) for r in block.table_rows],
                            anchor_text_block_index=anchor,
                        )
                    )
            else:
                result.text_blocks.append(self._paragraph_block(block.text))

        metadata_lines: list[str] = []
        if payload.source_url:
            metadata_lines.append(f"Source: {payload.source_url}")
        for key, value in payload.metadata.items():
            metadata_lines.append(f"{key}: {value}")
        if metadata_lines:
            result.text_blocks.append(
                self._heading_block(PublishBlock(type="heading", text="Metadata", level=2))
            )
            for line in metadata_lines:
                result.text_blocks.append(self._paragraph_block(line))

        return result

    def _heading_block(self, block: PublishBlock) -> dict[str, Any]:
        level = max(1, min(block.level, 9))
        return {
            "block_type": level + 2,
            "heading%d" % level: {
                "elements": [self._text_element(block.text)],
            },
        }

    def _paragraph_block(self, text: str) -> dict[str, Any]:
        return {
            "block_type": 2,
            "text": {
                "elements": [self._text_element(text)],
                "style": {},
            },
        }

    def _bullet_block(self, text: str) -> dict[str, Any]:
        return {
            "block_type": 12,
            "bullet": {
                "elements": [self._text_element(text)],
                "style": {},
            },
        }

    def _quote_block(self, text: str) -> dict[str, Any]:
        return {
            "block_type": 15,
            "quote": {
                "elements": [self._text_element(text)],
                "style": {},
            },
        }

    def _code_block(self, block: PublishBlock) -> dict[str, Any]:
        return {
            "block_type": 14,
            "code": {
                "elements": [self._text_element(block.text)],
                "style": {"language": block.language or "PlainText"},
            },
        }

    def _text_element(self, text: str) -> dict[str, Any]:
        return {
            "text_run": {
                "content": text,
                "text_element_style": {},
            }
        }
