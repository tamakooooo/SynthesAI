"""
Compatibility wrapper for Feishu document write operations.
"""

import uuid
from typing import Any

import requests

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
        if not blocks:
            return

        response = requests.post(
            f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "children": blocks,
                "client_token": str(uuid.uuid4()),
            },
            timeout=20,
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
