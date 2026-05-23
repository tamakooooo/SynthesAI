"""Feishu docx block / image / table / whiteboard low-level operations."""

from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from learning_assistant.adapters.feishu._base import FeishuBaseClient
from learning_assistant.adapters.feishu.models import (
    FeishuPublishResult,
    trim_raw_response,
)


class FeishuDocClient(FeishuBaseClient):
    """Client for Feishu docx APIs."""

    def create_document(self, token: str, title: str) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/docx/v1/documents",
            headers=self._auth_headers(token),
            json={"title": title},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload

    def append_blocks(
        self,
        token: str,
        document_id: str,
        blocks: list[dict[str, Any]],
    ) -> None:
        """Append blocks to document, splitting into batches if over 50."""
        if not blocks:
            return

        MAX_BATCH_SIZE = 50
        batches = [blocks[i : i + MAX_BATCH_SIZE] for i in range(0, len(blocks), MAX_BATCH_SIZE)]
        logger.debug(f"append_blocks: {len(blocks)} blocks in {len(batches)} batches")

        for batch_idx, batch in enumerate(batches):
            response = self.session.post(
                f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
                headers=self._auth_headers(token),
                json={"children": batch, "client_token": str(uuid.uuid4())},
                timeout=20,
            )
            if not response.ok:
                logger.error(
                    f"append_blocks batch {batch_idx + 1} failed: "
                    f"{response.status_code} {response.text}"
                )
            response.raise_for_status()
            self._raise_for_business_error(response.json())

    def publish_document(
        self,
        token: str,
        title: str,
        blocks: list[dict[str, Any]],
    ) -> FeishuPublishResult:
        created = self.create_document(token=token, title=title)
        document = created.get("data", {}).get("document", {})
        document_id = document.get("document_id")
        if not document_id:
            return FeishuPublishResult(
                success=False,
                message="Feishu docx creation succeeded but returned no document id",
                raw_response=trim_raw_response(created),
            )

        self.append_blocks(token=token, document_id=document_id, blocks=blocks)
        return FeishuPublishResult(
            success=True,
            message="Feishu docx document created",
            document_id=document_id,
            raw_response=trim_raw_response(created),
        )

    # ── Image upload ─────────────────────────────────────────────────────

    def create_image_block(
        self,
        token: str,
        document_id: str,
        index: int | None = None,
    ) -> str | None:
        payload: dict[str, Any] = {"children": [{"block_type": 27, "image": {}}]}
        if index is not None:
            payload["index"] = index

        response = self.session.post(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            headers=self._auth_headers(token),
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        children = result.get("data", {}).get("children", [])
        if children:
            return children[0].get("block_id")
        return None

    def upload_image(self, token: str, image_path: str, block_id: str) -> str | None:
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None

        file_size = path.stat().st_size
        max_bytes = self.config.max_image_upload_bytes
        if file_size > max_bytes:
            logger.warning(
                f"Image {path.name} ({file_size} bytes) exceeds limit "
                f"{max_bytes} bytes; skipping"
            )
            return None

        mime, _ = mimetypes.guess_type(str(path))
        mime = mime or "application/octet-stream"
        file_name = path.name

        with open(path, "rb") as f:
            files = {"file": (file_name, f, mime)}
            data = {
                "file_name": file_name,
                "parent_type": "docx_image",
                "parent_node": block_id,
                "size": str(file_size),
            }
            response = self.session.post(
                f"{self.base_url}/drive/v1/medias/upload_all",
                headers=self._auth_headers(token),
                files=files,
                data=data,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            self._raise_for_business_error(result)
            file_token = result.get("data", {}).get("file_token")
            logger.debug(f"Uploaded image: {file_name} -> {file_token}")
            return file_token

    def bind_image_to_block(
        self,
        token: str,
        document_id: str,
        block_id: str,
        file_token: str,
    ) -> bool:
        response = self.session.patch(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{block_id}",
            headers=self._auth_headers(token),
            json={"replace_image": {"token": file_token}},
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)
        return True

    def delete_block(self, token: str, document_id: str, block_id: str) -> bool:
        """Delete a block by id. Used to clean up orphaned image placeholders."""
        response = self.session.delete(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{block_id}",
            headers=self._auth_headers(token),
            timeout=20,
        )
        if response.status_code == 404:
            return False
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)
        return True

    # ── Table block ──────────────────────────────────────────────────────

    def create_table_block(
        self,
        token: str,
        document_id: str,
        row_size: int,
        column_size: int,
        index: int | None = None,
    ) -> tuple[str | None, list[str] | None]:
        payload: dict[str, Any] = {
            "children": [
                {
                    "block_type": 31,
                    "table": {
                        "property": {"row_size": row_size, "column_size": column_size}
                    },
                }
            ]
        }
        if index is not None:
            payload["index"] = index

        response = self.session.post(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            headers=self._auth_headers(token),
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        children = result.get("data", {}).get("children", [])
        if children:
            table_block = children[0]
            table_block_id = table_block.get("block_id")
            cell_ids = table_block.get("table", {}).get("cells", [])
            logger.info(
                f"Created table block id={table_block_id}, "
                f"rows={row_size}, cols={column_size}, cells={len(cell_ids)}"
            )
            return table_block_id, cell_ids
        return None, None

    def update_table_cell(
        self,
        token: str,
        document_id: str,
        cell_block_id: str,
        text: str,
    ) -> bool:
        response = self.session.patch(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{cell_block_id}",
            headers=self._auth_headers(token),
            json={
                "update_text_elements": {
                    "elements": [
                        {"text_run": {"content": text, "text_element_style": {}}}
                    ]
                }
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)
        return True

    def batch_update_table_cells(
        self,
        token: str,
        document_id: str,
        updates: list[tuple[str, str]],
    ) -> bool:
        """Update many table cells in one batch_update call.

        updates: list of (cell_block_id, text) pairs.
        """
        if not updates:
            return True

        requests_payload = [
            {
                "block_id": cell_id,
                "update_text_elements": {
                    "elements": [
                        {"text_run": {"content": text, "text_element_style": {}}}
                    ]
                },
            }
            for cell_id, text in updates
        ]

        response = self.session.patch(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/batch_update",
            headers=self._auth_headers(token),
            json={"requests": requests_payload},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)
        logger.info(f"Batch updated {len(updates)} table cells")
        return True

    # ── Whiteboard block ─────────────────────────────────────────────────

    def create_whiteboard_block(
        self,
        token: str,
        document_id: str,
        index: int | None = None,
    ) -> str | None:
        payload: dict[str, Any] = {"children": [{"block_type": 43, "board": {}}]}
        if index is not None:
            payload["index"] = index

        response = self.session.post(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            headers=self._auth_headers(token),
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        children = result.get("data", {}).get("children", [])
        if children:
            block = children[0]
            whiteboard_id = block.get("board", {}).get("token")
            logger.info(
                f"Created whiteboard block id={block.get('block_id')} "
                f"whiteboard_id={whiteboard_id}"
            )
            return whiteboard_id
        return None

    def get_document_blocks(self, token: str, document_id: str) -> list[dict[str, Any]]:
        response = self.session.get(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks",
            headers=self._auth_headers(token),
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)
        return result.get("data", {}).get("items", [])

    def find_whiteboard_block(self, token: str, document_id: str) -> str | None:
        for block in self.get_document_blocks(token, document_id):
            if block.get("block_type") == 43:
                return block.get("token")
        return None
