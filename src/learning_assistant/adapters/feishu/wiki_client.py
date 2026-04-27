"""
Feishu wiki API client.
"""

import os
import time
from pathlib import Path
from typing import Any

import requests
from loguru import logger

from learning_assistant.adapters.feishu.models import (
    FeishuKnowledgeBaseConfig,
    FeishuPublishResult,
)
from learning_assistant.core.publishing.models import PublishPayload


class FeishuWikiClient:
    """Thin client for Feishu wiki node APIs."""

    def __init__(self, config: FeishuKnowledgeBaseConfig) -> None:
        self.config = config
        self.base_url = "https://open.feishu.cn/open-apis"

    def publish(self, payload: PublishPayload, blocks: list[dict[str, Any]]) -> FeishuPublishResult:
        """Create a docx file, upload images, create mindmap, move to wiki."""
        token = self._get_tenant_access_token()
        title = self.config.title_template.format(module=payload.module, title=payload.title)

        # Step 1: Create docx document
        from learning_assistant.adapters.feishu.doc_client import FeishuDocClient
        doc_client = FeishuDocClient(self.config)

        # Track images with their position in original blocks
        # Images should be inserted after the text block that precedes them
        image_info = []  # (text_blocks_index_to_insert_after, image_path)
        text_blocks = []

        # First, separate blocks and track where each image should go
        # The image should appear after the block immediately before it
        text_block_count = 0  # Count of text blocks seen so far
        for i, block in enumerate(blocks):
            image_path = block.get("_image_path")
            if image_path:
                # This image should appear after the text block at position (text_block_count - 1)
                # But if it's the first block, there's no preceding text block
                if text_block_count > 0:
                    preceding_text_idx = text_block_count - 1
                else:
                    preceding_text_idx = -1  # Insert at beginning
                image_info.append((preceding_text_idx, image_path))
            else:
                text_blocks.append(block)
                text_block_count += 1

        logger.info(f"Publishing {len(text_blocks)} text blocks and {len(image_info)} image blocks")
        for preceding_idx, img_path in image_info:
            logger.debug(f"Image '{Path(img_path).name}' should appear after text block {preceding_idx}")

        # Create document with text blocks only
        doc_result = doc_client.publish_document(
            token=token,
            title=title,
            blocks=text_blocks,
        )
        if not doc_result.success or not doc_result.document_id:
            return doc_result

        document_id = doc_result.document_id

        # Step 2: Create mindmap in whiteboard if structure provided
        mindmap_url = None
        whiteboard_id = None
        if payload.mindmap_structure:
            try:
                # Create whiteboard block in document
                whiteboard_id = doc_client.create_whiteboard_block(token, document_id)
                if whiteboard_id:
                    # Wait for whiteboard initialization before creating nodes
                    # Feishu whiteboard needs time to be ready after creation
                    time.sleep(3)
                    # Use whiteboard API to create mindmap nodes
                    from learning_assistant.adapters.feishu.whiteboard_client import FeishuWhiteboardClient
                    wb_client = FeishuWhiteboardClient(self.config)
                    logger.debug(f"Creating mindmap with structure: {payload.mindmap_structure}")
                    wb_client.create_mindmap_nodes(token, whiteboard_id, payload.mindmap_structure)
                    # Build whiteboard URL
                    mindmap_url = self._build_whiteboard_url(whiteboard_id)
                    logger.info(f"Mindmap created in whiteboard: {whiteboard_id}")
                else:
                    logger.info("Whiteboard creation failed, using fallback document structure blocks")
            except Exception as e:
                logger.warning(f"Failed to create mindmap in whiteboard: {e}, using fallback document structure blocks")

        # Step 3: Process images at correct positions
        # Insert images after their preceding text block
        # Track cumulative offset as each image adds a new block
        offset = 0
        for preceding_idx, image_path in image_info:
            try:
                # Calculate insertion index: preceding_idx + 1 (after the block) + offset (from previous images)
                # preceding_idx is -1 for images at the very beginning (should go at index 0)
                if preceding_idx < 0:
                    insert_index = 0
                else:
                    insert_index = preceding_idx + 1 + offset

                logger.debug(f"Inserting image at index {insert_index} (preceding_idx={preceding_idx}, offset={offset})")

                image_block_id = doc_client.create_image_block(token, document_id, index=insert_index)
                if not image_block_id:
                    logger.warning(f"Failed to create image block for {image_path}")
                    continue
                file_token = doc_client.upload_image(token, image_path, image_block_id)
                if not file_token:
                    logger.warning(f"Failed to upload image {image_path}")
                    continue
                doc_client.bind_image_to_block(token, document_id, image_block_id, file_token)
                logger.info(f"Image uploaded at position {insert_index}: {image_path}")
                offset += 1  # Each image adds one block
            except Exception as e:
                logger.error(f"Failed to process image {image_path}: {e}")

        # Step 4: Move to wiki space
        move_response = self._move_doc_to_wiki(token, document_id)
        data = move_response.get("data", {})
        wiki_token = data.get("wiki_token")
        task_id = data.get("task_id")
        logger.debug(f"Move to wiki response: data={data}, wiki_token={wiki_token}, task_id={task_id}")

        # Build result
        if wiki_token:
            url = self._build_url(wiki_token)
            return FeishuPublishResult(
                success=True,
                message="Published to Feishu knowledge base",
                node_token=wiki_token,
                document_id=document_id,
                url=url,
                raw_response=move_response,
            )

        if task_id:
            node_token = self._poll_for_node_token(token, document_id, max_wait=60)
            if node_token:
                url = self._build_url(node_token)
                return FeishuPublishResult(
                    success=True,
                    message="Published to Feishu knowledge base",
                    node_token=node_token,
                    document_id=document_id,
                    url=url,
                    raw_response=move_response,
                )
            fallback_url = self._build_docx_url(document_id)
            logger.info(f"Poll did not find node_token, returning docx fallback URL: {fallback_url}")
            return FeishuPublishResult(
                success=True,
                message="Published to Feishu knowledge base (docx URL)",
                node_token=task_id,
                document_id=document_id,
                url=fallback_url,
                raw_response=move_response,
            )

        return FeishuPublishResult(
            success=False,
            message="Unexpected response from Feishu move API",
            document_id=document_id,
            raw_response=move_response,
        )

    def _create_and_link_mindmap(
        self,
        token: str,
        payload: PublishPayload,
    ) -> str | None:
        """Create mindmap from structure and return URL."""
        from learning_assistant.adapters.feishu.mindmap_client import FeishuMindmapClient

        mindmap_client = FeishuMindmapClient(self.config)
        mindmap_title = f"{payload.title} - 思维导图"

        mindmap_token, mindmap_url = mindmap_client.build_mindmap_from_structure(
            token=token,
            title=mindmap_title,
            structure=payload.mindmap_structure,
        )

        if mindmap_token:
            # Move mindmap to wiki as well
            try:
                mindmap_client.move_to_wiki(token, mindmap_token)
                logger.info(f"Mindmap moved to wiki: {mindmap_token}")
            except Exception as e:
                logger.warning(f"Failed to move mindmap to wiki: {e}")

        return mindmap_url

    def _add_mindmap_as_blocks(
        self,
        structure: dict[str, Any],
        blocks: list[dict[str, Any]],
    ) -> None:
        """Add mindmap structure as heading/bullet blocks in document."""
        root = structure.get("root", "")
        children = structure.get("children", [])

        # Add mindmap heading
        blocks.append({
            "block_type": 4,  # heading 2
            "heading2": {"elements": [{"text_run": {"content": "🧠 思维导图", "text_element_style": {}}}]},
        })

        # Add root topic
        blocks.append({
            "block_type": 5,  # heading 3
            "heading3": {"elements": [{"text_run": {"content": f"📌 {root}", "text_element_style": {}}}]},
        })

        # Add children as bullet lists
        for child in children:
            # Handle both dict and string children
            if isinstance(child, str):
                topic = child
                sub_children = []
            elif isinstance(child, dict):
                topic = child.get("topic", "")
                sub_children = child.get("children", [])
            else:
                continue

            if not topic:
                continue

            # Level 1: topic as heading 4
            blocks.append({
                "block_type": 6,  # heading 4
                "heading4": {"elements": [{"text_run": {"content": f"├─ {topic}", "text_element_style": {}}}]},
            })

            # Level 2: subtopics as bullets
            subtopic_texts = []
            for sub_child in sub_children:
                # Handle both dict and string sub_children
                if isinstance(sub_child, str):
                    subtopic = sub_child
                    details = []
                elif isinstance(sub_child, dict):
                    subtopic = sub_child.get("subtopic", "")
                    details = sub_child.get("details", [])
                else:
                    continue

                if subtopic:
                    text = f"• {subtopic}"
                    if details:
                        text += f" ({', '.join(details[:3])})"
                    subtopic_texts.append(text)

            if subtopic_texts:
                for text in subtopic_texts:
                    blocks.append({
                        "block_type": 12,  # bullet
                        "bullet": {"elements": [{"text_run": {"content": text, "text_element_style": {}}}], "style": {}},
                    })

    def verify_configuration(self) -> dict[str, Any]:
        """Verify token exchange and basic wiki accessibility."""
        token = self._get_tenant_access_token()
        nodes_response = self._list_nodes(token)
        verification: dict[str, Any] = {
            "token_verified": True,
            "space_accessible": True,
            "root_node_accessible": False,
            "space_response": nodes_response,
        }
        if self.config.root_node_token:
            node_response = self._get_node(token, self.config.root_node_token)
            verification["root_node_accessible"] = True
            verification["root_node_response"] = node_response
        return verification

    def _get_tenant_access_token(self) -> str:
        """Get tenant access token from Feishu API."""
        app_id = self.config.app_id or os.environ.get(self.config.app_id_env)
        app_secret = self.config.app_secret or os.environ.get(self.config.app_secret_env)
        if not app_id or not app_secret:
            raise RuntimeError(
                "Missing Feishu credentials. "
                f"Set app_id/app_secret in config or set {self.config.app_id_env}/{self.config.app_secret_env} env vars."
            )

        response = requests.post(
            f"{self.base_url}/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        token = payload.get("tenant_access_token")
        if not token:
            raise RuntimeError(f"Failed to obtain Feishu tenant access token: {payload}")
        return token

    def _move_doc_to_wiki(self, token: str, document_id: str) -> dict[str, Any]:
        """Move docx document to wiki space."""
        response = requests.post(
            f"{self.base_url}/wiki/v2/spaces/{self.config.space_id}/nodes/move_docs_to_wiki",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parent_wiki_token": self.config.root_node_token,
                "obj_type": "docx",
                "obj_token": document_id,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload

    def _poll_for_node_token(self, token: str, document_id: str, max_wait: int = 60) -> str | None:
        """Poll wiki nodes to find the actual node_token for document.

        Args:
            token: tenant_access_token
            document_id: Document ID to find
            max_wait: Maximum wait time in seconds (default 60)

        Returns:
            node_token if found, None otherwise
        """
        for attempt in range(max_wait):
            time.sleep(1)
            response = requests.get(
                f"{self.base_url}/wiki/v2/spaces/{self.config.space_id}/nodes",
                headers={"Authorization": f"Bearer {token}"},
                params={"parent_node_token": self.config.root_node_token, "page_size": 50},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            items = data.get("items", [])
            logger.debug(f"Poll attempt {attempt+1}/{max_wait}: found {len(items)} nodes, looking for document_id={document_id}")
            for node in items:
                if node.get("obj_token") == document_id:
                    node_token = node.get("node_token")
                    logger.info(f"Found matching node: obj_token={document_id}, node_token={node_token}")
                    return node_token
        logger.warning(f"Poll completed after {max_wait}s, document_id={document_id} not found in wiki nodes")
        return None

    def _build_url(self, node_token: str) -> str | None:
        """Build Feishu wiki URL from node_token."""
        if self.config.space_domain:
            return f"https://{self.config.space_domain}.feishu.cn/wiki/{node_token}"
        return None

    def _build_docx_url(self, document_id: str) -> str | None:
        """Build Feishu docx URL from document_id (fallback when wiki node not ready)."""
        if self.config.space_domain:
            return f"https://{self.config.space_domain}.feishu.cn/docx/{document_id}"
        return None

    def _build_whiteboard_url(self, whiteboard_id: str) -> str | None:
        """Build Feishu whiteboard URL from whiteboard_id."""
        if self.config.space_domain:
            return f"https://{self.config.space_domain}.feishu.cn/board/{whiteboard_id}"
        return None

    def _list_nodes(self, token: str) -> dict[str, Any]:
        """List nodes in wiki space."""
        response = requests.get(
            f"{self.base_url}/wiki/v2/spaces/{self.config.space_id}/nodes",
            headers={"Authorization": f"Bearer {token}"},
            params={"page_size": 1},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload

    def _get_node(self, token: str, node_token: str) -> dict[str, Any]:
        """Get specific node info."""
        response = requests.get(
            f"{self.base_url}/wiki/v2/spaces/get_node",
            headers={"Authorization": f"Bearer {token}"},
            params={"token": node_token},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload

    def _raise_for_business_error(self, payload: dict[str, Any]) -> None:
        """Raise error if Feishu API returns business error."""
        if payload.get("code") not in (None, 0):
            raise RuntimeError(
                f"Feishu API error {payload.get('code')}: {payload.get('msg', 'unknown error')}"
            )