"""
Compatibility wrapper for Feishu document write operations.
"""

import os
import uuid
from pathlib import Path
from typing import Any

import requests
from loguru import logger

from learning_assistant.adapters.feishu.models import FeishuKnowledgeBaseConfig, FeishuPublishResult


class FeishuDocClient:
    """Client for Feishu docx APIs."""

    def __init__(self, config: FeishuKnowledgeBaseConfig) -> None:
        self.config = config
        self.base_url = "https://open.feishu.cn/open-apis"

    def create_document(
        self,
        token: str,
        title: str,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/docx/v1/documents",
            headers={"Authorization": f"Bearer {token}"},
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
        """Append blocks to document, splitting into batches if over 50.

        Feishu API limits 50 children per request, so we split into multiple batches.
        """
        if not blocks:
            return

        # Feishu API limit: max 50 children per request
        MAX_BATCH_SIZE = 50

        # Split blocks into batches if needed
        batches = []
        for i in range(0, len(blocks), MAX_BATCH_SIZE):
            batches.append(blocks[i:i + MAX_BATCH_SIZE])

        logger.debug(f"append_blocks: {len(blocks)} blocks split into {len(batches)} batches")

        for batch_idx, batch in enumerate(batches):
            response = requests.post(
                f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "children": batch,
                    "client_token": str(uuid.uuid4()),
                },
                timeout=20,
            )
            if not response.ok:
                logger.error(f"append_blocks batch {batch_idx + 1} failed: {response.status_code} {response.text}")
            response.raise_for_status()
            self._raise_for_business_error(response.json())
            logger.debug(f"append_blocks batch {batch_idx + 1}/{len(batches)}: {len(batch)} blocks added")

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
                raw_response=created,
            )

        self.append_blocks(token=token, document_id=document_id, blocks=blocks)

        return FeishuPublishResult(
            success=True,
            message="Feishu docx document created",
            document_id=document_id,
            raw_response=created,
        )

    def _raise_for_business_error(self, payload: dict[str, Any]) -> None:
        if payload.get("code") not in (None, 0):
            raise RuntimeError(
                f"Feishu API error {payload.get('code')}: {payload.get('msg', 'unknown error')}"
            )

    # ── Image Upload Methods ──────────────────────────────────────────────

    def create_image_block(
        self,
        token: str,
        document_id: str,
        index: int | None = None,
    ) -> str | None:
        """Create an empty image block, return the block_id.

        Args:
            token: tenant_access_token
            document_id: Document ID
            index: Insert position (optional, append to end if None)

        Returns:
            The created image block_id, or None if failed
        """
        payload = {
            "children": [
                {
                    "block_type": 27,
                    "image": {},
                }
            ]
        }
        if index is not None:
            payload["index"] = index

        response = requests.post(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        children = result.get("data", {}).get("children", [])
        if children:
            block_id = children[0].get("block_id")
            logger.debug(f"Created image block: {block_id}")
            return block_id
        return None

    def upload_image(
        self,
        token: str,
        image_path: str,
        block_id: str,
    ) -> str | None:
        """Upload image to Feishu, return file_token.

        Args:
            token: tenant_access_token
            image_path: Local image file path
            block_id: The image block_id (used as parent_node)

        Returns:
            The file_token for the uploaded image, or None if failed
        """
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None

        file_size = path.stat().st_size
        file_name = path.name

        with open(path, "rb") as f:
            files = {
                "file": (file_name, f, "image/jpeg"),
            }
            data = {
                "file_name": file_name,
                "parent_type": "docx_image",
                "parent_node": block_id,
                "size": str(file_size),
            }
            headers = {
                "Authorization": f"Bearer {token}",
            }

            response = requests.post(
                f"{self.base_url}/drive/v1/medias/upload_all",
                headers=headers,
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
        """Bind uploaded image to the image block.

        Args:
            token: tenant_access_token
            document_id: Document ID
            block_id: The image block_id
            file_token: The file_token from upload_image()

        Returns:
            True if successful, False otherwise
        """
        response = requests.patch(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{block_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "replace_image": {
                    "token": file_token,
                }
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        logger.debug(f"Bound image token {file_token} to block {block_id}")
        return True

    # ── Whiteboard (Board) Block Methods ──────────────────────────────────────────────

    def create_whiteboard_block(
        self,
        token: str,
        document_id: str,
        index: int | None = None,
    ) -> str | None:
        """Create an empty whiteboard block, return the whiteboard_id (block.token).

        Args:
            token: tenant_access_token
            document_id: Document ID
            index: Insert position (optional, append to end if None)

        Returns:
            The whiteboard_id (block.token), or None if failed
        """
        payload = {
            "children": [
                {
                    "block_type": 43,  # 画板 Block
                    "board": {},
                }
            ]
        }
        if index is not None:
            payload["index"] = index

        response = requests.post(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        children = result.get("data", {}).get("children", [])
        if children:
            block = children[0]
            # whiteboard_id is in board.token for block_type=43
            board_data = block.get("board", {})
            whiteboard_id = board_data.get("token")
            block_id = block.get("block_id")
            logger.info(f"Created whiteboard block: block_id={block_id}, whiteboard_id={whiteboard_id}")
            return whiteboard_id
        return None

    def get_document_blocks(
        self,
        token: str,
        document_id: str,
    ) -> list[dict[str, Any]]:
        """Get all blocks in a document.

        Args:
            token: tenant_access_token
            document_id: Document ID

        Returns:
            List of blocks in the document
        """
        response = requests.get(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        blocks = result.get("data", {}).get("items", [])
        logger.debug(f"Retrieved {len(blocks)} blocks from document {document_id}")
        return blocks

    def find_whiteboard_block(
        self,
        token: str,
        document_id: str,
    ) -> str | None:
        """Find existing whiteboard block in document and return whiteboard_id.

        Args:
            token: tenant_access_token
            document_id: Document ID

        Returns:
            whiteboard_id (block.token) if found, None otherwise
        """
        blocks = self.get_document_blocks(token, document_id)
        for block in blocks:
            if block.get("block_type") == 43:
                whiteboard_id = block.get("token")
                logger.debug(f"Found whiteboard block: whiteboard_id={whiteboard_id}")
                return whiteboard_id
        return None
