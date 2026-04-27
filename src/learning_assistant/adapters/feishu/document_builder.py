"""
Convert normalized publish payloads to Feishu docx blocks.
"""

from typing import Any

from loguru import logger

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
            elif block.type == "image":
                # Image blocks need special handling - return placeholder with path
                blocks.append(self._image_placeholder(block))
            elif block.type == "table":
                # Table blocks use Feishu block_type 31
                blocks.extend(self._table_blocks(block))
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

    def _image_placeholder(self, block: PublishBlock) -> dict[str, Any]:
        """Return a placeholder dict for image block (needs upload before inserting).

        The actual image upload and block creation is handled by wiki_client.
        This placeholder carries the image_path for later processing.
        """
        return {
            "block_type": 27,
            "image": {},
            "_image_path": block.image_path,  # Internal field for wiki_client to process
        }

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

    def _table_blocks(self, block: PublishBlock) -> list[dict[str, Any]]:
        """Build Feishu table blocks (block_type 31 + cells).

        Feishu table structure:
        1. Table block (block_type 31) with property containing row_size, column_size
        2. Table cell blocks (block_type 32) as children

        Since we can't directly insert cell content in one API call,
        we return a placeholder structure that wiki_client needs to process.
        """
        headers = block.table_headers or []
        rows = block.table_rows or []

        if not rows:
            return []

        # Calculate dimensions
        column_size = max(len(headers), max(len(row) for row in rows) if rows else 0)
        row_size = len(rows) + (1 if headers else 0)

        # Build table block with property
        table_block = {
            "block_type": 31,  # Table Block
            "table": {
                "cells": [],  # Will be filled after cell blocks are created
                "property": {
                    "row_size": row_size,
                    "column_size": column_size,
                },
            },
            "_table_data": {  # Internal fields for wiki_client to process
                "headers": headers,
                "rows": rows,
            },
        }

        return [table_block]

    def _text_element(self, text: str) -> dict[str, Any]:
        return {
            "text_run": {
                "content": text,
                "text_element_style": {},
            }
        }
