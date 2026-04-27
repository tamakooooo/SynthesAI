"""
Tests for Feishu knowledge base adapter.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from learning_assistant.adapters.feishu.adapter import FeishuKnowledgeBaseAdapter
from learning_assistant.adapters.feishu.wiki_client import FeishuWikiClient
from learning_assistant.adapters.feishu.doc_client import FeishuDocClient
from learning_assistant.adapters.feishu.models import FeishuKnowledgeBaseConfig, FeishuPublishResult
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.publishing.models import PublishPayload, PublishBlock


class TestFeishuKnowledgeBaseAdapter:
    """Tests for FeishuKnowledgeBaseAdapter."""

    def test_adapter_initialize_disabled(self) -> None:
        """Test adapter initialization when disabled."""
        adapter = FeishuKnowledgeBaseAdapter()

        adapter.initialize({"enabled": False, "config": {}}, EventBus())

        assert adapter.state.value == "ready"
        assert adapter.get_subscribed_events() == []

    def test_adapter_initialize_enabled(self) -> None:
        """Test adapter initialization when enabled."""
        adapter = FeishuKnowledgeBaseAdapter()

        config = {
            "enabled": True,
            "config": {
                "app_id_env": "FEISHU_APP_ID",
                "app_secret_env": "FEISHU_APP_SECRET",
                "space_id": "test_space",
                "root_node_token": "test_token",
                "publish_modules": ["video_summary"],
            },
        }

        adapter.initialize(config, EventBus())

        assert adapter.state.value == "ready"
        assert adapter.settings.enabled is True
        assert adapter.wiki_client is not None

    def test_adapter_skips_unconfigured_module(self) -> None:
        """Test adapter skips content for unconfigured module."""
        adapter = FeishuKnowledgeBaseAdapter()
        adapter.initialize(
            {
                "enabled": True,
                "config": {
                    "publish_modules": ["link_learning"],
                    "app_id_env": "FEISHU_APP_ID",
                    "app_secret_env": "FEISHU_APP_SECRET",
                    "space_id": "test",
                    "root_node_token": "test",
                },
            },
            EventBus(),
        )

        pushed = adapter.push_content(
            {
                "module": "video_summary",
                "title": "Test",
                "summary": "Summary",
                "blocks": [],
                "metadata": {},
                "tags": [],
            }
        )

        assert pushed is False

    def test_adapter_skips_when_disabled(self) -> None:
        """Test adapter skips content when disabled."""
        adapter = FeishuKnowledgeBaseAdapter()
        adapter.initialize({"enabled": False, "config": {}}, EventBus())

        pushed = adapter.push_content(
            {
                "module": "video_summary",
                "title": "Test",
                "summary": "Summary",
                "blocks": [],
                "metadata": {},
                "tags": [],
            }
        )

        assert pushed is False

    def test_adapter_cleanup(self) -> None:
        """Test adapter cleanup."""
        adapter = FeishuKnowledgeBaseAdapter()
        adapter.initialize(
            {
                "enabled": True,
                "config": {
                    "publish_modules": ["video_summary"],
                    "app_id_env": "FEISHU_APP_ID",
                    "app_secret_env": "FEISHU_APP_SECRET",
                    "space_id": "test",
                    "root_node_token": "test",
                },
            },
            EventBus(),
        )

        adapter.cleanup()

        assert adapter.wiki_client is None


class TestFeishuWikiClient:
    """Tests for FeishuWikiClient."""

    def test_get_tenant_access_token_success(self) -> None:
        """Test successful token exchange."""
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id="test_app_id",
            app_secret="test_app_secret",
            space_id="test_space",
            root_node_token="test_token",
        )
        client = FeishuWikiClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "tenant_access_token": "test_token_123",
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.post', return_value=mock_response):
            token = client._get_tenant_access_token()

            assert token == "test_token_123"

    def test_get_tenant_access_token_missing_credentials(self) -> None:
        """Test token exchange with missing credentials."""
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id=None,
            app_secret=None,
            app_id_env="MISSING_APP_ID",
            app_secret_env="MISSING_APP_SECRET",
            space_id="test_space",
            root_node_token="test_token",
        )
        client = FeishuWikiClient(config)

        with pytest.raises(RuntimeError, match="Missing Feishu credentials"):
            client._get_tenant_access_token()

    def test_verify_configuration_success(self) -> None:
        """Test configuration verification."""
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id="test_app",
            app_secret="test_secret",
            space_id="test_space",
            root_node_token="test_node",
        )
        client = FeishuWikiClient(config)

        mock_token_response = Mock()
        mock_token_response.json.return_value = {"code": 0, "tenant_access_token": "token"}
        mock_token_response.raise_for_status = Mock()

        mock_nodes_response = Mock()
        mock_nodes_response.json.return_value = {"code": 0, "data": {"items": []}}
        mock_nodes_response.raise_for_status = Mock()

        mock_node_response = Mock()
        mock_node_response.json.return_value = {"code": 0, "data": {"node": {}}}
        mock_node_response.raise_for_status = Mock()

        with patch('requests.post', return_value=mock_token_response), \
             patch.object(client, '_list_nodes', return_value={"code": 0}), \
             patch.object(client, '_get_node', return_value={"code": 0}):
            result = client.verify_configuration()

            assert result["token_verified"] is True
            assert result["space_accessible"] is True


class TestFeishuDocClient:
    """Tests for FeishuDocClient."""

    def test_create_document_success(self) -> None:
        """Test successful document creation."""
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            space_id="test_space",
            root_node_token="test_token",
        )
        client = FeishuDocClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "document": {
                    "document_id": "doc_123",
                }
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.post', return_value=mock_response):
            result = client.create_document(token="test_token", title="Test Doc")

            assert result["data"]["document"]["document_id"] == "doc_123"

    def test_publish_document_success(self) -> None:
        """Test successful document publishing."""
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            space_id="test_space",
            root_node_token="test_token",
        )
        client = FeishuDocClient(config)

        blocks = [
            {"type": "paragraph", "text": "Test content"},
        ]

        # Mock create_document and append_blocks
        with patch.object(client, 'create_document', return_value={
            "code": 0,
            "data": {"document": {"document_id": "doc_123"}}
        }), \
             patch.object(client, 'append_blocks', return_value=None):
            result = client.publish_document(token="test_token", title="Test", blocks=blocks)

            assert result.success is True
            assert result.document_id == "doc_123"


class TestFeishuDocumentBuilder:
    """Tests for FeishuDocumentBuilder."""

    def test_build_from_payload(self) -> None:
        """Test building blocks from PublishPayload."""
        from learning_assistant.adapters.feishu.document_builder import FeishuDocumentBuilder

        builder = FeishuDocumentBuilder()

        payload = PublishPayload(
            module="video_summary",
            title="Test Video",
            summary="This is a test summary.",
            source_url="https://example.com/video",
            blocks=[
                PublishBlock(type="heading", text="Introduction", level=2),
                PublishBlock(type="paragraph", text="Main content here."),
                PublishBlock(type="bullet_list", items=["Point 1", "Point 2"]),
            ],
            tags=["test", "video"],
            metadata={"duration": "5:00"},
        )

        # build() expects PublishPayload object, not dict
        blocks = builder.build(payload)

        assert len(blocks) > 0
        # Check that summary is included (it's the first block)
        assert blocks[0]["block_type"] == 2  # paragraph
        # Check that heading is included
        heading_blocks = [b for b in blocks if b.get("block_type") == 4]  # heading2
        assert len(heading_blocks) >= 1