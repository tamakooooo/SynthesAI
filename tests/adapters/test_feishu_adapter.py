"""Tests for Feishu knowledge base adapter."""

import time
from unittest.mock import Mock, patch

import pytest

from learning_assistant.adapters.feishu._base import FeishuBaseClient
from learning_assistant.adapters.feishu.adapter import FeishuKnowledgeBaseAdapter
from learning_assistant.adapters.feishu.doc_client import FeishuDocClient
from learning_assistant.adapters.feishu.models import (
    FEISHU_TITLE_MAX_LENGTH,
    FeishuKnowledgeBaseConfig,
    trim_raw_response,
    truncate_title,
)
from learning_assistant.adapters.feishu.wiki_client import FeishuWikiClient
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.publishing.models import PublishBlock, PublishPayload


@pytest.fixture(autouse=True)
def clear_token_cache():
    FeishuBaseClient.clear_token_cache()
    yield
    FeishuBaseClient.clear_token_cache()


class TestFeishuKnowledgeBaseAdapter:
    def test_adapter_initialize_disabled(self) -> None:
        adapter = FeishuKnowledgeBaseAdapter()
        adapter.initialize({"enabled": False, "config": {}}, EventBus())
        assert adapter.state.value == "ready"
        assert adapter.get_subscribed_events() == []

    def test_adapter_initialize_enabled(self) -> None:
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
        result = adapter.push_content(
            {
                "module": "video_summary",
                "title": "Test",
                "summary": "Summary",
                "blocks": [],
                "metadata": {},
                "tags": [],
            }
        )
        assert result.success is False
        assert "not enabled" in result.message

    def test_adapter_skips_when_disabled(self) -> None:
        adapter = FeishuKnowledgeBaseAdapter()
        adapter.initialize({"enabled": False, "config": {}}, EventBus())
        result = adapter.push_content(
            {
                "module": "video_summary",
                "title": "Test",
                "summary": "Summary",
                "blocks": [],
                "metadata": {},
                "tags": [],
            }
        )
        assert result.success is False
        assert "disabled" in result.message

    def test_adapter_cleanup(self) -> None:
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
    def test_get_tenant_access_token_success(self) -> None:
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
            "expire": 7200,
        }
        mock_response.raise_for_status = Mock()

        with patch.object(client.session, "post", return_value=mock_response) as mocked:
            token = client._get_tenant_access_token()
            assert token == "test_token_123"
            mocked.assert_called_once()

    def test_get_tenant_access_token_cached(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id="cached_app",
            app_secret="cached_secret",
            space_id="s",
            root_node_token="t",
        )
        client = FeishuWikiClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "tenant_access_token": "cached_token",
            "expire": 7200,
        }
        mock_response.raise_for_status = Mock()

        with patch.object(client.session, "post", return_value=mock_response) as mocked:
            client._get_tenant_access_token()
            client._get_tenant_access_token()
            assert mocked.call_count == 1

    def test_get_tenant_access_token_missing_credentials(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id=None,
            app_secret=None,
            app_id_env="MISSING_APP_ID_VAR_XYZ",
            app_secret_env="MISSING_APP_SECRET_VAR_XYZ",
            space_id="test_space",
            root_node_token="test_token",
        )
        client = FeishuWikiClient(config)
        with pytest.raises(RuntimeError, match="Missing Feishu credentials"):
            client._get_tenant_access_token()

    def test_verify_configuration_success(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id="test_app",
            app_secret="test_secret",
            space_id="test_space",
            root_node_token="test_node",
        )
        client = FeishuWikiClient(config)
        with patch.object(client, "_get_tenant_access_token", return_value="tok"), \
             patch.object(client, "_list_nodes", return_value={"code": 0}), \
             patch.object(client, "_get_node", return_value={"code": 0}):
            result = client.verify_configuration()
            assert result["token_verified"] is True
            assert result["space_accessible"] is True
            assert result["root_node_accessible"] is True

    def test_build_url_without_space_domain(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True, app_id="a", app_secret="b", space_id="s", root_node_token="t"
        )
        client = FeishuWikiClient(config)
        assert client._build_url("node123") == "https://feishu.cn/wiki/node123"

    def test_build_url_with_space_domain(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id="a",
            app_secret="b",
            space_id="s",
            root_node_token="t",
            space_domain="example",
        )
        client = FeishuWikiClient(config)
        assert client._build_url("node123") == "https://example.feishu.cn/wiki/node123"


class TestFeishuDocClient:
    def test_create_document_success(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True, space_id="test_space", root_node_token="test_token"
        )
        client = FeishuDocClient(config)
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {"document": {"document_id": "doc_123"}},
        }
        mock_response.raise_for_status = Mock()
        with patch.object(client.session, "post", return_value=mock_response):
            result = client.create_document(token="test_token", title="Test Doc")
            assert result["data"]["document"]["document_id"] == "doc_123"

    def test_publish_document_success(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True, space_id="test_space", root_node_token="test_token"
        )
        client = FeishuDocClient(config)
        blocks = [{"type": "paragraph", "text": "Test content"}]
        with patch.object(
            client,
            "create_document",
            return_value={"code": 0, "data": {"document": {"document_id": "doc_123"}}},
        ), patch.object(client, "append_blocks", return_value=None):
            result = client.publish_document(token="test_token", title="Test", blocks=blocks)
            assert result.success is True
            assert result.document_id == "doc_123"


class TestFeishuDocumentBuilder:
    def test_build_from_payload(self) -> None:
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
        result = builder.build(payload)
        assert len(result.text_blocks) > 0
        assert result.text_blocks[0]["block_type"] == 2
        heading_blocks = [b for b in result.text_blocks if b.get("block_type") == 4]
        assert len(heading_blocks) >= 1

    def test_build_collects_images_and_tables(self) -> None:
        from learning_assistant.adapters.feishu.document_builder import FeishuDocumentBuilder

        builder = FeishuDocumentBuilder()
        payload = PublishPayload(
            module="video_summary",
            title="With media",
            blocks=[
                PublishBlock(type="paragraph", text="Intro"),
                PublishBlock(type="image", image_path="/tmp/a.jpg"),
                PublishBlock(type="paragraph", text="Mid"),
                PublishBlock(
                    type="table",
                    table_headers=["a", "b"],
                    table_rows=[["1", "2"], ["3", "4"]],
                ),
            ],
        )
        result = builder.build(payload)
        assert len(result.images) == 1
        assert result.images[0].image_path == "/tmp/a.jpg"
        assert result.images[0].anchor_text_block_index == 0
        assert len(result.tables) == 1
        assert result.tables[0].row_size == 3
        assert result.tables[0].column_size == 2
        assert result.tables[0].anchor_text_block_index == 1


class TestFeishuWikiClientPublish:
    """Integration-style tests for FeishuWikiClient.publish."""

    def _make_client(self) -> FeishuWikiClient:
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id="test_app",
            app_secret="test_secret",
            space_id="test_space",
            root_node_token="root_token",
        )
        return FeishuWikiClient(config)

    def test_publish_happy_path(self) -> None:
        from learning_assistant.adapters.feishu.document_builder import (
            BuildResult,
            ImageData,
        )

        client = self._make_client()
        build_result = BuildResult(
            text_blocks=[{"block_type": 2, "text": {}}],
            images=[ImageData(image_path="/tmp/a.jpg", anchor_text_block_index=0)],
            tables=[],
        )
        payload = PublishPayload(module="video_summary", title="Hello", blocks=[])

        doc_result = Mock()
        doc_result.success = True
        doc_result.document_id = "doc_xyz"

        with patch.object(client, "_get_tenant_access_token", return_value="tok"), \
             patch.object(client.doc_client, "publish_document", return_value=doc_result), \
             patch.object(client.doc_client, "create_image_block", return_value="blk_img_1"), \
             patch.object(client.doc_client, "upload_image", return_value="file_token_1"), \
             patch.object(client.doc_client, "bind_image_to_block", return_value=True), \
             patch.object(
                 client,
                 "_move_doc_to_wiki",
                 return_value={"data": {"wiki_token": "wiki_node_1"}},
             ):
            result = client.publish(payload, build_result)
            assert result.success is True
            assert result.node_token == "wiki_node_1"
            assert result.url and "wiki_node_1" in result.url

    def test_publish_image_failure_cleans_up_orphan(self) -> None:
        from learning_assistant.adapters.feishu.document_builder import (
            BuildResult,
            ImageData,
        )

        client = self._make_client()
        build_result = BuildResult(
            text_blocks=[{"block_type": 2, "text": {}}],
            images=[ImageData(image_path="/tmp/bad.jpg", anchor_text_block_index=0)],
            tables=[],
        )
        payload = PublishPayload(module="video_summary", title="Hello", blocks=[])

        doc_result = Mock()
        doc_result.success = True
        doc_result.document_id = "doc_xyz"

        delete_calls: list[str] = []

        def fake_delete(_token: str, _doc: str, block_id: str) -> bool:
            delete_calls.append(block_id)
            return True

        with patch.object(client, "_get_tenant_access_token", return_value="tok"), \
             patch.object(client.doc_client, "publish_document", return_value=doc_result), \
             patch.object(client.doc_client, "create_image_block", return_value="blk_img_1"), \
             patch.object(client.doc_client, "upload_image", return_value=None), \
             patch.object(client.doc_client, "delete_block", side_effect=fake_delete), \
             patch.object(
                 client,
                 "_move_doc_to_wiki",
                 return_value={"data": {"wiki_token": "wiki_node_1"}},
             ):
            result = client.publish(payload, build_result)
            assert result.success is True
            assert delete_calls == ["blk_img_1"]

    def test_publish_falls_back_to_inline_mindmap(self) -> None:
        from learning_assistant.adapters.feishu.document_builder import BuildResult

        client = self._make_client()
        build_result = BuildResult(text_blocks=[], images=[], tables=[])
        payload = PublishPayload(
            module="video_summary",
            title="Mindmap",
            blocks=[],
            mindmap_structure={
                "root": "Topic",
                "children": [{"topic": "Branch", "children": ["leaf"]}],
            },
        )

        doc_result = Mock()
        doc_result.success = True
        doc_result.document_id = "doc_xyz"
        appended: list[list[dict]] = []

        def capture_append(*, token: str, document_id: str, blocks: list) -> None:
            appended.append(blocks)

        with patch.object(client, "_get_tenant_access_token", return_value="tok"), \
             patch.object(client.doc_client, "publish_document", return_value=doc_result), \
             patch.object(
                 client.doc_client,
                 "create_whiteboard_block",
                 side_effect=RuntimeError("whiteboard down"),
             ), \
             patch.object(client.doc_client, "append_blocks", side_effect=capture_append), \
             patch.object(
                 client,
                 "_move_doc_to_wiki",
                 return_value={"data": {"wiki_token": "wn"}},
             ):
            result = client.publish(payload, build_result)
            assert result.success is True
            assert appended, "expected inline fallback blocks to be appended"
            assert any(b.get("block_type") == 4 for b in appended[0])


class TestTruncateTitle:
    def test_below_limit_unchanged(self) -> None:
        assert truncate_title("hello") == "hello"

    def test_exactly_at_limit_unchanged(self) -> None:
        title = "a" * FEISHU_TITLE_MAX_LENGTH
        assert truncate_title(title) == title

    def test_one_over_limit_truncated_with_ellipsis(self) -> None:
        title = "a" * (FEISHU_TITLE_MAX_LENGTH + 1)
        result = truncate_title(title)
        assert len(result) == FEISHU_TITLE_MAX_LENGTH
        assert result.endswith("...")

    def test_mixed_cjk_truncated_by_char_count(self) -> None:
        # 256 Chinese chars + 1 -> still truncated by len()
        title = "测" * (FEISHU_TITLE_MAX_LENGTH + 5)
        result = truncate_title(title)
        assert len(result) == FEISHU_TITLE_MAX_LENGTH
        assert result.endswith("...")

    def test_short_max_length_no_ellipsis(self) -> None:
        assert truncate_title("abcdef", max_length=3) == "abc"


class TestDeprecatedConfigKeys:
    def test_overwrite_strategy_filtered_with_warning(self) -> None:
        adapter = FeishuKnowledgeBaseAdapter()
        adapter.initialize(
            {
                "enabled": True,
                "config": {
                    "overwrite_strategy": "skip",
                    "publish_modules": ["video_summary"],
                    "app_id_env": "FEISHU_APP_ID",
                    "app_secret_env": "FEISHU_APP_SECRET",
                    "space_id": "test",
                    "root_node_token": "test",
                },
            },
            EventBus(),
        )
        # extra="forbid" would have raised if the key wasn't filtered out.
        assert adapter.state.value == "ready"
        assert not hasattr(adapter.settings, "overwrite_strategy")


class TestTokenCacheExpiry:
    def test_token_refetched_when_within_refresh_buffer(self) -> None:
        config = FeishuKnowledgeBaseConfig(
            enabled=True,
            app_id="expiring_app",
            app_secret="expiring_secret",
            space_id="s",
            root_node_token="t",
        )
        client = FeishuWikiClient(config)

        responses = [
            {"code": 0, "tenant_access_token": "tok_a", "expire": 7200},
            {"code": 0, "tenant_access_token": "tok_b", "expire": 7200},
        ]

        def fake_post(*_args, **_kwargs):
            payload = responses.pop(0)
            mock = Mock()
            mock.json.return_value = payload
            mock.raise_for_status = Mock()
            return mock

        with patch.object(client.session, "post", side_effect=fake_post):
            token_first = client._get_tenant_access_token()
            assert token_first == "tok_a"

            # Manually expire cached entry to inside the refresh buffer.
            cache_key = (config.app_id, config.app_secret)
            FeishuBaseClient._token_cache[cache_key] = ("tok_a", time.time() + 60)

            token_second = client._get_tenant_access_token()
            assert token_second == "tok_b"


class TestTrimRawResponse:
    def test_keeps_top_level_diagnostic_fields(self) -> None:
        payload = {
            "code": 0,
            "msg": "ok",
            "request_id": "req-123",
            "data": {
                "wiki_token": "wn1",
                "task_id": "tid",
                "items": [{"big": "x" * 1000}] * 100,
            },
        }
        trimmed = trim_raw_response(payload)
        assert trimmed["code"] == 0
        assert trimmed["msg"] == "ok"
        assert trimmed["request_id"] == "req-123"
        assert trimmed["data"] == {"wiki_token": "wn1", "task_id": "tid"}
        assert "items" not in trimmed["data"]

    def test_handles_non_dict(self) -> None:
        assert trim_raw_response(None) == {}  # type: ignore[arg-type]
        assert trim_raw_response("not a dict") == {}  # type: ignore[arg-type]
