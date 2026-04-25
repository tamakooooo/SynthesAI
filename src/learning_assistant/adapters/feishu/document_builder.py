"""
Convert normalized publish payloads to Feishu docx blocks.
"""

from typing import Any

from learning_assistant.core.publishing.models import PublishBlock, PublishPayload


class FeishuDocumentBuilder:
    """Build Feishu docx block payloads from PublishPayload."""

    def build(self, payload: PublishPayload) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []

        if payload.summary:
            blocks.append(self._paragraph_block(payload.summary))

        for block in payload.blocks:
            if block.type == "heading":
                blocks.append(self._heading_block(block))
            elif block.type == "bullet_list":
                for item in block.items:
                    blocks.append(self._bullet_block(item))
            elif block.type == "quote":
                blocks.append(self._quote_block(block.text))
            elif block.type == "code":
                blocks.append(self._code_block(block))
            else:
                blocks.append(self._paragraph_block(block.text))

        metadata_lines = []
        if payload.source_url:
            metadata_lines.append(f"Source: {payload.source_url}")
        for key, value in payload.metadata.items():
            metadata_lines.append(f"{key}: {value}")
        if metadata_lines:
            blocks.append(self._heading_block(PublishBlock(type="heading", text="Metadata", level=2)))
            for line in metadata_lines:
                blocks.append(self._paragraph_block(line))

        return blocks

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
