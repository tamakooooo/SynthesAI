"""
Feishu wiki API client.
"""

import os
from typing import Any

import requests

from learning_assistant.adapters.feishu.models import (
    FeishuKnowledgeBaseConfig,
    FeishuPublishRequest,
    FeishuPublishResult,
)
from learning_assistant.core.publishing.models import PublishPayload


class FeishuWikiClient:
    """Thin client for Feishu wiki node APIs."""

    def __init__(self, config: FeishuKnowledgeBaseConfig) -> None:
        self.config = config
        self.base_url = "https://open.feishu.cn/open-apis"

    def publish(self, payload: PublishPayload, blocks: list[dict[str, Any]]) -> FeishuPublishResult:
        """Create a docx file, then move it into the Feishu knowledge base."""
        token = self._get_tenant_access_token()
        title = self.config.title_template.format(module=payload.module, title=payload.title)
        from learning_assistant.adapters.feishu.doc_client import FeishuDocClient

        doc_client = FeishuDocClient(self.config)
        doc_result = doc_client.publish_document(
            token=token,
            title=title,
            blocks=blocks,
        )
        if not doc_result.success or not doc_result.document_id:
            return doc_result

        move_response = self._move_doc_to_wiki(
            token=token,
            request=FeishuPublishRequest(
                payload=payload,
                parent_node_token=self.config.root_node_token,
            ),
            document_id=doc_result.document_id,
        )
        data = move_response.get("data", {})
        if "wiki_token" in data:
            return FeishuPublishResult(
                success=True,
                message="Published to Feishu knowledge base",
                node_token=data.get("wiki_token"),
                document_id=doc_result.document_id,
                raw_response=move_response,
            )
        if "task_id" in data:
            return FeishuPublishResult(
                success=True,
                message="Feishu knowledge base move task submitted",
                node_token=data.get("task_id"),
                document_id=doc_result.document_id,
                raw_response=move_response,
            )

        return FeishuPublishResult(
            success=bool(data.get("applied")),
            message="Feishu knowledge base move permission applied"
            if data.get("applied")
            else "Unexpected response from Feishu knowledge base move API",
            document_id=doc_result.document_id,
            raw_response=move_response,
        )

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
        app_id = os.environ.get(self.config.app_id_env)
        app_secret = os.environ.get(self.config.app_secret_env)
        if not app_id or not app_secret:
            raise RuntimeError(
                "Missing Feishu credentials. "
                f"Set {self.config.app_id_env} and {self.config.app_secret_env}."
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

    def _move_doc_to_wiki(
        self,
        token: str,
        request: FeishuPublishRequest,
        document_id: str,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/wiki/v2/spaces/{self.config.space_id}/nodes/move_docs_to_wiki",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parent_wiki_token": request.parent_node_token,
                "obj_type": "docx",
                "obj_token": document_id,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        return payload

    def _list_nodes(self, token: str) -> dict[str, Any]:
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
        if payload.get("code") not in (None, 0):
            raise RuntimeError(
                f"Feishu API error {payload.get('code')}: {payload.get('msg', 'unknown error')}"
            )
