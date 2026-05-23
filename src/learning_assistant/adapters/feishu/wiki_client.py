"""Feishu wiki publish orchestration."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from loguru import logger

from learning_assistant.adapters.feishu._base import FeishuBaseClient
from learning_assistant.adapters.feishu.doc_client import FeishuDocClient
from learning_assistant.adapters.feishu.document_builder import (
    BuildResult,
    ImageData,
    TableData,
)
from learning_assistant.adapters.feishu.models import (
    FeishuKnowledgeBaseConfig,
    FeishuPublishResult,
    trim_raw_response,
    truncate_title,
)
from learning_assistant.adapters.feishu.whiteboard_client import FeishuWhiteboardClient
from learning_assistant.core.publishing.models import PublishPayload


class FeishuWikiClient(FeishuBaseClient):
    """Orchestrate Feishu doc creation, content writing, wiki move."""

    def __init__(self, config: FeishuKnowledgeBaseConfig) -> None:
        super().__init__(config)
        self.doc_client = FeishuDocClient(config)
        self.whiteboard_client = FeishuWhiteboardClient(config)

    # ── Public entry point ──────────────────────────────────────────────

    def publish(
        self,
        payload: PublishPayload,
        build_result: BuildResult,
    ) -> FeishuPublishResult:
        """Create docx, embed mindmap, upload images, fill tables, move to wiki."""
        token = self._get_tenant_access_token()
        raw_title = self.config.title_template.format(
            module=payload.module, title=payload.title
        )
        title = truncate_title(raw_title)
        if title != raw_title:
            logger.info(f"Title truncated from {len(raw_title)} to {len(title)} chars")

        logger.info(
            f"Publishing: {len(build_result.text_blocks)} text, "
            f"{len(build_result.images)} images, {len(build_result.tables)} tables"
        )

        doc_result = self.doc_client.publish_document(
            token=token, title=title, blocks=build_result.text_blocks
        )
        if not doc_result.success or not doc_result.document_id:
            return doc_result

        document_id = doc_result.document_id

        self._embed_mindmap(token, document_id, payload)
        offset_state = {"value": 0}
        self._insert_images_safe(token, document_id, build_result.images, offset_state)
        self._insert_tables_safe(token, document_id, build_result.tables, offset_state)

        return self._finalize_wiki_move(token, document_id)

    # ── Mindmap with fallback ───────────────────────────────────────────

    def _embed_mindmap(
        self,
        token: str,
        document_id: str,
        payload: PublishPayload,
    ) -> None:
        structure = payload.mindmap_structure
        if not structure:
            return

        try:
            whiteboard_id = self.doc_client.create_whiteboard_block(token, document_id)
            if not whiteboard_id:
                raise RuntimeError("Whiteboard creation returned no id")

            time.sleep(self.config.whiteboard_init_wait_seconds)
            self.whiteboard_client.create_mindmap_nodes(token, whiteboard_id, structure)
            logger.info(f"Mindmap rendered in whiteboard {whiteboard_id}")
            return
        except Exception as exc:
            logger.warning(
                f"Whiteboard mindmap failed ({exc}), falling back to inline blocks"
            )

        try:
            fallback_blocks = self._mindmap_as_blocks(
                structure, decorate=self.config.mindmap_inline_decorations
            )
            if fallback_blocks:
                self.doc_client.append_blocks(
                    token=token, document_id=document_id, blocks=fallback_blocks
                )
                logger.info(f"Mindmap rendered as {len(fallback_blocks)} inline blocks")
        except Exception as exc:
            logger.error(f"Mindmap inline fallback also failed: {exc}")

    @staticmethod
    def _mindmap_as_blocks(
        structure: dict[str, Any],
        *,
        decorate: bool = True,
    ) -> list[dict[str, Any]]:
        """Render mindmap as heading/bullet blocks (fallback when whiteboard fails).

        decorate=True keeps emoji/box-drawing prefixes; pass False for plain text.
        """
        root = structure.get("root", "")
        children = structure.get("children", [])

        heading_text = "🧠 思维导图" if decorate else "思维导图"
        root_prefix = "📌 " if decorate else ""
        branch_prefix = "├─ " if decorate else ""
        leaf_prefix = "• " if decorate else "- "

        blocks: list[dict[str, Any]] = [
            {
                "block_type": 4,
                "heading2": {
                    "elements": [
                        {"text_run": {"content": heading_text, "text_element_style": {}}}
                    ]
                },
            }
        ]
        if root:
            blocks.append(
                {
                    "block_type": 5,
                    "heading3": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": f"{root_prefix}{root}",
                                    "text_element_style": {},
                                }
                            }
                        ]
                    },
                }
            )

        for child in children:
            if isinstance(child, str):
                topic, sub_children = child, []
            elif isinstance(child, dict):
                topic = child.get("topic", "")
                sub_children = child.get("children", [])
            else:
                continue
            if not topic:
                continue

            blocks.append(
                {
                    "block_type": 6,
                    "heading4": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": f"{branch_prefix}{topic}",
                                    "text_element_style": {},
                                }
                            }
                        ]
                    },
                }
            )
            for sub_child in sub_children:
                if isinstance(sub_child, str):
                    text = sub_child
                elif isinstance(sub_child, dict):
                    subtopic = sub_child.get("subtopic", "")
                    details = sub_child.get("details", [])
                    text = f"{leaf_prefix}{subtopic}"
                    if details:
                        text += f" ({', '.join(str(d) for d in details[:3])})"
                else:
                    continue
                if text:
                    blocks.append(
                        {
                            "block_type": 12,
                            "bullet": {
                                "elements": [
                                    {"text_run": {"content": text, "text_element_style": {}}}
                                ],
                                "style": {},
                            },
                        }
                    )
        return blocks

    # ── Image insertion (per-image try/except, parallel upload) ─────────

    def _insert_images_safe(
        self,
        token: str,
        document_id: str,
        images: list[ImageData],
        offset_state: dict[str, int],
    ) -> None:
        if not images:
            return

        # Phase 1: create empty image blocks sequentially to preserve order.
        placeholders: list[tuple[ImageData, str]] = []
        for image in images:
            try:
                insert_index = self._anchor_to_insert_index(
                    image.anchor_text_block_index, offset_state["value"]
                )
                image_block_id = self.doc_client.create_image_block(
                    token, document_id, index=insert_index
                )
                if not image_block_id:
                    logger.warning(f"Failed to create image block for {image.image_path}")
                    continue
                placeholders.append((image, image_block_id))
                offset_state["value"] += 1
            except Exception as exc:
                logger.error(f"Skipping image block creation for {image.image_path}: {exc}")

        if not placeholders:
            return

        # Phase 2: upload + bind in parallel.
        workers = max(1, min(self.config.upload_concurrency, len(placeholders)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    self._upload_and_bind_image, token, document_id, image, block_id
                ): (image, block_id)
                for image, block_id in placeholders
            }
            for future in as_completed(futures):
                image, block_id = futures[future]
                try:
                    success = future.result()
                except Exception as exc:
                    logger.error(f"Image task crashed for {image.image_path}: {exc}")
                    success = False
                if not success:
                    self._cleanup_orphan_block(token, document_id, block_id)

    def _upload_and_bind_image(
        self,
        token: str,
        document_id: str,
        image: ImageData,
        block_id: str,
    ) -> bool:
        try:
            file_token = self.doc_client.upload_image(token, image.image_path, block_id)
            if not file_token:
                logger.warning(f"Failed to upload image {image.image_path}")
                return False
            self.doc_client.bind_image_to_block(
                token, document_id, block_id, file_token
            )
            logger.info(f"Image inserted: {image.image_path}")
            return True
        except Exception as exc:
            logger.error(f"Skipping image {image.image_path}: {exc}")
            return False

    def _cleanup_orphan_block(
        self,
        token: str,
        document_id: str,
        block_id: str,
    ) -> None:
        try:
            self.doc_client.delete_block(token, document_id, block_id)
            logger.debug(f"Cleaned up orphan image block {block_id}")
        except Exception as exc:
            logger.warning(f"Failed to clean up orphan block {block_id}: {exc}")

    # ── Table insertion (per-table try/except, batch cell update) ───────

    def _insert_tables_safe(
        self,
        token: str,
        document_id: str,
        tables: list[TableData],
        offset_state: dict[str, int],
    ) -> None:
        for table in tables:
            try:
                if table.row_size == 0 or table.column_size == 0:
                    continue

                insert_index = self._anchor_to_insert_index(
                    table.anchor_text_block_index, offset_state["value"]
                )
                table_block_id, cell_ids = self.doc_client.create_table_block(
                    token=token,
                    document_id=document_id,
                    row_size=table.row_size,
                    column_size=table.column_size,
                    index=insert_index,
                )
                if not table_block_id or not cell_ids:
                    logger.warning("Table block creation failed; falling back to bullets")
                    self._table_fallback_bullets(token, document_id, table)
                    continue

                all_rows = ([table.headers] if table.headers else []) + table.rows
                updates: list[tuple[str, str]] = []
                cell_idx = 0
                for row in all_rows:
                    for col_idx in range(table.column_size):
                        if cell_idx >= len(cell_ids):
                            break
                        text = row[col_idx] if col_idx < len(row) else ""
                        updates.append((cell_ids[cell_idx], text))
                        cell_idx += 1

                self._update_cells_safe(token, document_id, updates)
                offset_state["value"] += 1
            except Exception as exc:
                logger.error(f"Skipping table: {exc}")

    def _update_cells_safe(
        self,
        token: str,
        document_id: str,
        updates: list[tuple[str, str]],
    ) -> None:
        if not updates:
            return
        try:
            self.doc_client.batch_update_table_cells(token, document_id, updates)
            return
        except Exception as exc:
            logger.warning(f"Batch cell update failed ({exc}), retrying one by one")

        for cell_id, text in updates:
            try:
                self.doc_client.update_table_cell(token, document_id, cell_id, text)
            except Exception as exc:
                logger.warning(f"Cell {cell_id} update failed: {exc}")

    def _table_fallback_bullets(
        self,
        token: str,
        document_id: str,
        table: TableData,
    ) -> None:
        lines: list[str] = []
        if table.headers:
            lines.append("| " + " | ".join(table.headers) + " |")
        for row in table.rows:
            lines.append("| " + " | ".join(row) + " |")

        bullet_blocks = [
            {
                "block_type": 12,
                "bullet": {
                    "elements": [{"text_run": {"content": line, "text_element_style": {}}}],
                    "style": {},
                },
            }
            for line in lines
        ]
        self.doc_client.append_blocks(token=token, document_id=document_id, blocks=bullet_blocks)

    @staticmethod
    def _anchor_to_insert_index(anchor: int, offset: int) -> int:
        if anchor < 0:
            return offset
        return anchor + 1 + offset

    # ── Wiki move + polling ─────────────────────────────────────────────

    def _finalize_wiki_move(self, token: str, document_id: str) -> FeishuPublishResult:
        move_response = self._move_doc_to_wiki(token, document_id)
        data = move_response.get("data", {})
        wiki_token = data.get("wiki_token")
        task_id = data.get("task_id")
        trimmed = trim_raw_response(move_response)

        if wiki_token:
            return FeishuPublishResult(
                success=True,
                message="Published to Feishu knowledge base",
                node_token=wiki_token,
                document_id=document_id,
                url=self._build_url(wiki_token),
                raw_response=trimmed,
            )

        if task_id:
            node_token = self._poll_for_node_token(token, document_id)
            if node_token:
                return FeishuPublishResult(
                    success=True,
                    message="Published to Feishu knowledge base",
                    node_token=node_token,
                    document_id=document_id,
                    url=self._build_url(node_token),
                    raw_response=trimmed,
                )
            return FeishuPublishResult(
                success=True,
                message="Published to Feishu knowledge base (docx URL fallback)",
                node_token=task_id,
                document_id=document_id,
                url=self._build_docx_url(document_id),
                raw_response=trimmed,
            )

        return FeishuPublishResult(
            success=False,
            message="Unexpected response from Feishu move API",
            document_id=document_id,
            raw_response=trimmed,
        )

    def _move_doc_to_wiki(self, token: str, document_id: str) -> dict[str, Any]:
        space_id = self.config.resolve_space_id()
        root_node_token = self.config.resolve_root_node_token()
        response = self.session.post(
            f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes/move_docs_to_wiki",
            headers=self._auth_headers(token),
            json={
                "parent_wiki_token": root_node_token,
                "obj_type": "docx",
                "obj_token": document_id,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload

    def _poll_for_node_token(self, token: str, document_id: str) -> str | None:
        """Poll wiki nodes with exponential backoff up to poll_max_wait_seconds."""
        space_id = self.config.resolve_space_id()
        root_node_token = self.config.resolve_root_node_token()
        deadline = time.time() + self.config.poll_max_wait_seconds
        backoff = self.config.poll_initial_backoff
        attempt = 0

        while time.time() < deadline:
            attempt += 1
            time.sleep(backoff)
            backoff = min(backoff * 2, self.config.poll_max_backoff)

            response = self.session.get(
                f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes",
                headers=self._auth_headers(token),
                params={"parent_node_token": root_node_token, "page_size": 50},
                timeout=30,
            )
            response.raise_for_status()
            items = response.json().get("data", {}).get("items", [])
            for node in items:
                if node.get("obj_token") == document_id:
                    node_token = node.get("node_token")
                    logger.info(
                        f"Found wiki node for doc {document_id} on attempt {attempt}: {node_token}"
                    )
                    return node_token

        logger.warning(f"Polling timed out for document_id={document_id}")
        return None

    # ── URL builders ────────────────────────────────────────────────────

    def _build_url(self, node_token: str) -> str | None:
        if self.config.space_domain:
            return f"https://{self.config.space_domain}.feishu.cn/wiki/{node_token}"
        return f"https://feishu.cn/wiki/{node_token}"

    def _build_docx_url(self, document_id: str) -> str | None:
        if self.config.space_domain:
            return f"https://{self.config.space_domain}.feishu.cn/docx/{document_id}"
        return f"https://feishu.cn/docx/{document_id}"

    # ── Verification ────────────────────────────────────────────────────

    def verify_configuration(self) -> dict[str, Any]:
        token = self._get_tenant_access_token()
        nodes_response = self._list_nodes(token)
        verification: dict[str, Any] = {
            "token_verified": True,
            "space_accessible": True,
            "root_node_accessible": False,
            "space_response": nodes_response,
        }
        root_node_token = self.config.resolve_root_node_token()
        if root_node_token:
            verification["root_node_response"] = self._get_node(token, root_node_token)
            verification["root_node_accessible"] = True
        return verification

    def _list_nodes(self, token: str) -> dict[str, Any]:
        space_id = self.config.resolve_space_id()
        response = self.session.get(
            f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes",
            headers=self._auth_headers(token),
            params={"page_size": 1},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload

    def _get_node(self, token: str, node_token: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/wiki/v2/spaces/get_node",
            headers=self._auth_headers(token),
            params={"token": node_token},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload
