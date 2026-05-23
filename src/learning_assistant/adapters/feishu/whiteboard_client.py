"""Feishu whiteboard (board) API client for mindmap operations.

Whiteboard (画板) is the embedded board block (block_type=43) inside a docx.
Mindmap nodes are created via /board/v1/whiteboards/{id}/nodes.
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger

from learning_assistant.adapters.feishu._base import FeishuBaseClient


class FeishuWhiteboardClient(FeishuBaseClient):
    """Client for Feishu whiteboard (board) API operations."""

    DOC_APPLYING_CODE = 4003101

    def create_mindmap_nodes(
        self,
        token: str,
        whiteboard_id: str,
        structure: dict[str, Any],
    ) -> dict[str, Any]:
        """Create mindmap nodes in whiteboard from nested structure."""
        root_text = structure.get("root", "主题")
        children = structure.get("children", [])

        root_nodes = [
            {
                "type": "mind_map",
                "text": {"text": root_text},
                "mind_map_root": {
                    "layout": "left_right",
                    "type": "mind_map_round_rect",
                    "line_style": "curve",
                },
            }
        ]

        result = self._post_nodes_with_retry(token, whiteboard_id, root_nodes)
        root_ids = result.get("data", {}).get("ids", [])
        if not root_ids:
            logger.warning("Failed to get root mindmap node ID")
            return result

        root_node_id = root_ids[0]
        logger.info(f"Created mindmap root '{root_text}' -> {root_node_id}")
        time.sleep(1)
        self._create_children_recursive(token, whiteboard_id, children, root_node_id, level=1)
        return result

    def _create_children_recursive(
        self,
        token: str,
        whiteboard_id: str,
        children: list[Any],
        parent_node_id: str,
        level: int,
    ) -> None:
        if not children:
            return

        node_texts: list[str] = []
        child_structures: list[tuple[int, str, list[Any]]] = []

        for i, child in enumerate(children):
            if isinstance(child, str):
                text, nested = child, []
            elif isinstance(child, dict):
                if level == 1:
                    text = child.get("topic", "")
                elif level == 2:
                    text = child.get("subtopic", "")
                else:
                    text = child.get("detail", "")
                nested = child.get("children", child.get("details", []))
            else:
                text, nested = str(child), []

            if text:
                node_texts.append(text)
                if nested:
                    child_structures.append((i, text, nested))

        if not node_texts:
            return

        nodes_payload = [
            {
                "type": "mind_map",
                "text": {"text": text},
                "mind_map_node": {"parent_id": parent_node_id, "z_index": i},
            }
            for i, text in enumerate(node_texts)
        ]

        result = self._post_nodes_with_retry(token, whiteboard_id, nodes_payload)
        created_ids = result.get("data", {}).get("ids", [])
        logger.info(f"Created {len(created_ids)} mindmap nodes at level {level}")

        for idx, _text, nested_children in child_structures:
            if idx < len(created_ids):
                time.sleep(0.5)
                self._create_children_recursive(
                    token, whiteboard_id, nested_children, created_ids[idx], level + 1
                )

    def _post_nodes_with_retry(
        self,
        token: str,
        whiteboard_id: str,
        nodes_payload: list[dict[str, Any]],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """POST mindmap nodes, retrying on transient 'doc is applying' error."""
        backoff = 1.0
        for attempt in range(max_retries + 1):
            response = self.session.post(
                f"{self.base_url}/board/v1/whiteboards/{whiteboard_id}/nodes",
                headers=self._auth_headers(token),
                json={"nodes": nodes_payload},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            if result.get("code") == self.DOC_APPLYING_CODE and attempt < max_retries:
                logger.warning(
                    f"Whiteboard not ready, retrying in {backoff:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(backoff)
                backoff *= 2
                continue
            self._raise_for_business_error(result)
            return result
        return {}

    def get_whiteboard_nodes(
        self,
        token: str,
        whiteboard_id: str,
        max_retries: int = 3,
    ) -> list[dict[str, Any]]:
        backoff = 1.0
        for attempt in range(max_retries + 1):
            response = self.session.get(
                f"{self.base_url}/board/v1/whiteboards/{whiteboard_id}/nodes",
                headers=self._auth_headers(token),
                timeout=20,
            )
            response.raise_for_status()
            result = response.json()
            if result.get("code") == self.DOC_APPLYING_CODE and attempt < max_retries:
                logger.warning(f"Whiteboard not ready for get_nodes, retrying in {backoff:.1f}s")
                time.sleep(backoff)
                backoff *= 2
                continue
            self._raise_for_business_error(result)
            return result.get("data", {}).get("nodes", [])
        return []
