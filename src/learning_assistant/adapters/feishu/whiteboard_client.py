"""
Feishu whiteboard (board) API client for mindmap operations.

Whiteboard (画板) is different from mindnote (思维导图):
- mindnote: Independent mindmap file, API NOT publicly available
- whiteboard: Embedded in document as block_type=43, API supports mindmap nodes

This client uses board API to create mindmap nodes inside whiteboard blocks.

IMPORTANT: The board API returns actual node IDs (like "z1:1") different from
our custom IDs ("root", "root_0"). We must create nodes in batches and use
the returned IDs for parent-child relationships.
"""

import time
from typing import Any

import requests
from loguru import logger

from learning_assistant.adapters.feishu.models import FeishuKnowledgeBaseConfig


class FeishuWhiteboardClient:
    """Client for Feishu whiteboard (board) API operations."""

    def __init__(self, config: FeishuKnowledgeBaseConfig) -> None:
        self.config = config
        self.base_url = "https://open.feishu.cn/open-apis"

    def create_mindmap_nodes(
        self,
        token: str,
        whiteboard_id: str,
        structure: dict[str, Any],
    ) -> dict[str, Any]:
        """Create mindmap nodes in whiteboard from nested structure.

        Uses sequential batch creation:
        1. Create root node, get actual node_id from API
        2. Create level-1 children under root
        3. Create level-2+ children under their parent's actual id

        Args:
            token: tenant_access_token
            whiteboard_id: The whiteboard_id from document block (block_type=43)
            structure: Nested dict like {"root": "主题", "children": [...]}

        Returns:
            API response with created nodes info
        """
        root_text = structure.get("root", "主题")
        children = structure.get("children", [])

        logger.debug(f"create_mindmap_nodes: root='{root_text}', children_count={len(children)}, children_type={type(children)}")
        if children:
            logger.debug(f"First child: {children[0] if children else 'None'}")

        # Step 1: Create root node
        root_nodes = [{
            "type": "mind_map",
            "text": {"text": root_text},
            "mind_map_root": {
                "layout": "left_right",
                "type": "mind_map_round_rect",
                "line_style": "curve",
            },
        }]

        response = requests.post(
            f"{self.base_url}/board/v1/whiteboards/{whiteboard_id}/nodes",
            headers={"Authorization": f"Bearer {token}"},
            json={"nodes": root_nodes},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        # Get actual root node ID from API response
        root_ids = result.get("data", {}).get("ids", [])
        if not root_ids:
            logger.warning("Failed to get root node ID")
            return result

        root_node_id = root_ids[0]
        logger.info(f"Created mindmap root: '{root_text}' -> {root_node_id}")

        # Wait for whiteboard to process root node before creating children
        time.sleep(1)

        # Step 2: Create children level by level
        self._create_children_recursive(token, whiteboard_id, children, root_node_id, level=1)

        return result

    def _create_children_recursive(
        self,
        token: str,
        whiteboard_id: str,
        children: list[dict[str, Any]],
        parent_node_id: str,
        level: int,
    ) -> None:
        """Create child nodes under parent, then recursively create their children."""
        if not children:
            return

        # Build nodes for this level
        node_texts = []
        child_structures = []  # Track which children have nested children

        for i, child in enumerate(children):
            # Extract text based on level structure
            if isinstance(child, str):
                # Handle string children (simple text nodes)
                text = child
                nested = []
            elif isinstance(child, dict):
                if level == 1:
                    text = child.get("topic", "")
                elif level == 2:
                    text = child.get("subtopic", "")
                else:
                    text = child.get("detail", "")
                nested = child.get("children", child.get("details", []))
            else:
                text = str(child)
                nested = []

            if text:
                node_texts.append(text)
                if nested:
                    child_structures.append((i, text, nested))

        if not node_texts:
            return

        # Create nodes for this level
        # For MindMapNode, we must set parent_id in mind_map_node property
        nodes_payload = [
            {
                "type": "mind_map",
                "text": {"text": text},
                "mind_map_node": {
                    "parent_id": parent_node_id,
                    "z_index": i,  # Order by creation sequence
                }
            }
            for i, text in enumerate(node_texts)
        ]

        response = requests.post(
            f"{self.base_url}/board/v1/whiteboards/{whiteboard_id}/nodes",
            headers={"Authorization": f"Bearer {token}"},
            json={"nodes": nodes_payload},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        # Handle "doc is applying" error with retry
        error_code = result.get("code")
        if error_code == 4003101:
            logger.warning(f"Whiteboard not ready, waiting 2s and retrying...")
            time.sleep(2)
            response = requests.post(
                f"{self.base_url}/board/v1/whiteboards/{whiteboard_id}/nodes",
                headers={"Authorization": f"Bearer {token}"},
                json={"nodes": nodes_payload},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

        self._raise_for_business_error(result)

        # Get actual node IDs
        created_ids = result.get("data", {}).get("ids", [])
        logger.info(f"Created {len(created_ids)} mindmap nodes at level {level}: {node_texts} -> IDs: {created_ids}")

        # Recursively create nested children
        # Match IDs by order (API returns IDs in same order as input nodes)
        for idx, text, nested_children in child_structures:
            if idx < len(created_ids):
                child_node_id = created_ids[idx]
                # Add delay to avoid "doc is applying" rate limit error
                time.sleep(0.5)
                self._create_children_recursive(
                    token, whiteboard_id, nested_children, child_node_id, level + 1
                )

    def get_whiteboard_nodes(
        self,
        token: str,
        whiteboard_id: str,
        max_retries: int = 3,
    ) -> list[dict[str, Any]]:
        """Get all nodes in a whiteboard.

        Args:
            token: tenant_access_token
            whiteboard_id: The whiteboard_id
            max_retries: Max retries for "doc is applying" error

        Returns:
            List of nodes in the whiteboard
        """
        for attempt in range(max_retries + 1):
            response = requests.get(
                f"{self.base_url}/board/v1/whiteboards/{whiteboard_id}/nodes",
                headers={"Authorization": f"Bearer {token}"},
                timeout=20,
            )
            response.raise_for_status()
            result = response.json()

            # Handle "doc is applying" error with retry
            if result.get("code") == 4003101:
                if attempt < max_retries:
                    logger.warning(f"Whiteboard not ready for get_nodes, waiting 2s (attempt {attempt + 1})")
                    time.sleep(2)
                    continue

            self._raise_for_business_error(result)

            nodes = result.get("data", {}).get("nodes", [])
            logger.debug(f"Retrieved {len(nodes)} nodes from whiteboard {whiteboard_id}")
            return nodes

        return []  # Return empty if all retries failed

    def _raise_for_business_error(self, payload: dict[str, Any]) -> None:
        """Raise error if Feishu API returns business error."""
        if payload.get("code") not in (None, 0):
            raise RuntimeError(
                f"Feishu API error {payload.get('code')}: {payload.get('msg', 'unknown error')}"
            )