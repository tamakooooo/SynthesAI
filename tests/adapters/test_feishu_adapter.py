"""
Tests for Feishu knowledge base adapter.
"""

from learning_assistant.adapters.feishu.adapter import FeishuKnowledgeBaseAdapter
from learning_assistant.core.event_bus import EventBus


def test_feishu_adapter_initialize_disabled() -> None:
    adapter = FeishuKnowledgeBaseAdapter()

    adapter.initialize({"enabled": False, "config": {}}, EventBus())

    assert adapter.state.value == "ready"
    assert adapter.get_subscribed_events() == []


def test_feishu_adapter_skips_unconfigured_module() -> None:
    adapter = FeishuKnowledgeBaseAdapter()
    adapter.initialize(
        {
            "enabled": True,
            "config": {
                "publish_modules": ["link_learning"],
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
