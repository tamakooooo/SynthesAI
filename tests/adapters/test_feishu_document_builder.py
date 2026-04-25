"""
Tests for Feishu document block builder.
"""

from learning_assistant.adapters.feishu.document_builder import FeishuDocumentBuilder
from learning_assistant.core.publishing.models import PublishBlock, PublishPayload


def test_build_feishu_blocks_from_publish_payload() -> None:
    builder = FeishuDocumentBuilder()
    payload = PublishPayload(
        module="video_summary",
        title="Test",
        summary="Summary body",
        source_url="https://example.com",
        blocks=[
            PublishBlock(type="heading", text="Section", level=2),
            PublishBlock(type="bullet_list", items=["A", "B"]),
        ],
        metadata={"uploader": "tester"},
    )

    blocks = builder.build(payload)

    assert len(blocks) >= 5
    assert blocks[0]["block_type"] == 2
    assert blocks[1]["block_type"] == 4
    assert any(block["block_type"] == 12 for block in blocks)

