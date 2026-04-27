"""
Feishu mindmap API client.
"""

from typing import Any

import requests
from loguru import logger

from learning_assistant.adapters.feishu.models import FeishuKnowledgeBaseConfig


class FeishuMindmapClient:
    """Client for Feishu mindmap operations."""

    def __init__(self, config: FeishuKnowledgeBaseConfig) -> None:
        self.config = config
        self.base_url = "https://open.feishu.cn/open-apis"

    def create_mindmap(self, token: str, title: str) -> str | None:
        """Create a new mindmap file via Drive API.

        Args:
            token: tenant_access_token
            title: Mindmap title

        Returns:
            mindmap_token (obj_token), or None if failed
        """
        # Use folder token if available, otherwise use root
        folder_token = self.config.root_node_token or ""

        response = requests.post(
            f"{self.base_url}/drive/v1/files",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": title,
                "type": "file",
                "file_type": "mindmap",
                "folder_token": folder_token,
            },
            timeout=20,
        )
        if response.status_code == 404:
            # Try alternative: create via wiki node creation
            logger.warning("Drive API 404, trying wiki node creation")
            return self._create_mindmap_via_wiki(token, title)

        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        file = result.get("data", {}).get("file", {})
        mindmap_token = file.get("token")
        logger.info(f"Created mindmap: {title} -> {mindmap_token}")
        return mindmap_token

    def _create_mindmap_via_wiki(self, token: str, title: str) -> str | None:
        """Create mindmap via wiki node creation API."""
        response = requests.post(
            f"{self.base_url}/wiki/v2/spaces/{self.config.space_id}/nodes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parent_wiki_token": self.config.root_node_token,
                "obj_type": "mindmap",
                "title": title,
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        node = result.get("data", {}).get("node", {})
        mindmap_token = node.get("obj_token")
        logger.info(f"Created mindmap via wiki: {title} -> {mindmap_token}")
        return mindmap_token

    def create_node(
        self,
        token: str,
        mindmap_token: str,
        parent_node_token: str,
        text: str,
    ) -> str | None:
        """Create a single node in mindmap.

        Args:
            token: tenant_access_token
            mindmap_token: The mindmap file token
            parent_node_token: Parent node token (root node token for first level)
            text: Node text content

        Returns:
            Created node_token, or None if failed
        """
        response = requests.post(
            f"{self.base_url}/mindmap/v1/mindmaps/{mindmap_token}/nodes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parent_node_token": parent_node_token,
                "nodes": [
                    {
                        "content": {"text": text},
                    }
                ],
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        nodes = result.get("data", {}).get("nodes", [])
        if nodes:
            node_token = nodes[0].get("node_token")
            logger.debug(f"Created node: '{text}' -> {node_token}")
            return node_token
        return None

    def batch_create_nodes(
        self,
        token: str,
        mindmap_token: str,
        parent_node_token: str,
        node_texts: list[str],
    ) -> list[str]:
        """Batch create nodes under parent.

        Args:
            token: tenant_access_token
            mindmap_token: The mindmap file token
            parent_node_token: Parent node token
            node_texts: List of node text contents

        Returns:
            List of created node_tokens
        """
        nodes_payload = [{"content": {"text": text}} for text in node_texts]

        response = requests.post(
            f"{self.base_url}/mindmap/v1/mindmaps/{mindmap_token}/nodes/batch_create",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parent_node_token": parent_node_token,
                "nodes": nodes_payload,
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        created_nodes = result.get("data", {}).get("nodes", [])
        node_tokens = [n.get("node_token") for n in created_nodes if n.get("node_token")]
        logger.debug(f"Batch created {len(node_tokens)} nodes under {parent_node_token}")
        return node_tokens

    def get_root_node(self, token: str, mindmap_token: str) -> str | None:
        """Get the root node token of a mindmap.

        Args:
            token: tenant_access_token
            mindmap_token: The mindmap file token

        Returns:
            Root node_token, or None if failed
        """
        response = requests.get(
            f"{self.base_url}/mindmap/v1/mindmaps/{mindmap_token}/nodes",
            headers={"Authorization": f"Bearer {token}"},
            params={"page_size": 1},
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)

        nodes = result.get("data", {}).get("nodes", [])
        if nodes:
            root_token = nodes[0].get("node_token")
            logger.debug(f"Root node token: {root_token}")
            return root_token
        return None

    def build_mindmap_from_structure(
        self,
        token: str,
        title: str,
        structure: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        """Build complete mindmap from nested structure dict.

        Args:
            token: tenant_access_token
            title: Mindmap title
            structure: Nested dict like {"root": "主题", "children": [...]}

        Returns:
            (mindmap_token, mindmap_url)
        """
        # Step 1: Create mindmap file
        mindmap_token = self.create_mindmap(token, title)
        if not mindmap_token:
            logger.error("Failed to create mindmap file")
            return None, None

        # Step 2: Get root node
        root_node_token = self.get_root_node(token, mindmap_token)
        if not root_node_token:
            logger.error("Failed to get root node")
            return mindmap_token, None

        # Step 3: Update root node text
        root_text = structure.get("root", title)
        # Root node already has title, we may need to update it
        # For simplicity, we'll create children under root

        # Step 4: Build tree recursively
        children = structure.get("children", [])
        self._build_tree_recursive(token, mindmap_token, root_node_token, children)

        # Step 5: Build URL
        url = self._build_mindmap_url(mindmap_token)
        logger.info(f"Mindmap built successfully: {url}")
        return mindmap_token, url

    def _build_tree_recursive(
        self,
        token: str,
        mindmap_token: str,
        parent_token: str,
        children: list[dict[str, Any]],
        level: int = 1,
    ) -> None:
        """Recursively build mindmap tree structure."""
        if not children:
            return

        # Extract text from children based on level
        # Level 1: {"topic": "...", "children": [...]}
        # Level 2: {"subtopic": "...", "children": [...]} or {"subtopic": "...", "details": [...]}
        # Level 3+: {"detail": "..."} or plain strings
        node_texts = []
        child_structures = []

        for child in children:
            if level == 1:
                text = child.get("topic", "")
            elif level == 2:
                text = child.get("subtopic", "")
            else:
                text = child.get("detail", "") if isinstance(child, dict) else str(child)

            if text:
                node_texts.append(text)
                # Get nested children
                nested = child.get("children", child.get("details", []))
                if nested:
                    child_structures.append((text, nested))

        # Batch create nodes at this level
        if node_texts:
            node_tokens = self.batch_create_nodes(token, mindmap_token, parent_token, node_texts)

            # Build children for each created node
            # Match tokens with texts by order
            for i, (text, nested_children) in enumerate(child_structures):
                if i < len(node_tokens):
                    child_token = node_tokens[i]
                    self._build_tree_recursive(
                        token, mindmap_token, child_token, nested_children, level + 1
                    )

    def _build_mindmap_url(self, mindmap_token: str) -> str | None:
        """Build mindmap URL from token."""
        if self.config.space_domain and mindmap_token:
            return f"https://{self.config.space_domain}.feishu.cn/mindmap/{mindmap_token}"
        return None

    def move_to_wiki(
        self,
        token: str,
        mindmap_token: str,
    ) -> dict[str, Any]:
        """Move mindmap to wiki space.

        Args:
            token: tenant_access_token
            mindmap_token: The mindmap file token

        Returns:
            Move API response
        """
        response = requests.post(
            f"{self.base_url}/wiki/v2/spaces/{self.config.space_id}/nodes/move_docs_to_wiki",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parent_wiki_token": self.config.root_node_token,
                "obj_type": "mindmap",
                "obj_token": mindmap_token,
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        self._raise_for_business_error(result)
        logger.info(f"Mindmap moved to wiki: {mindmap_token}")
        return result

    def _raise_for_business_error(self, payload: dict[str, Any]) -> None:
        """Raise error if Feishu API returns business error."""
        if payload.get("code") not in (None, 0):
            raise RuntimeError(
                f"Feishu API error {payload.get('code')}: {payload.get('msg', 'unknown error')}"
            )