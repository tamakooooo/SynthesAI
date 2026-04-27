"""
Feishu knowledge base adapter.
"""

from typing import Any

from loguru import logger

from learning_assistant.adapters.feishu.document_builder import FeishuDocumentBuilder
from learning_assistant.adapters.feishu.models import FeishuKnowledgeBaseConfig, FeishuPublishResult
from learning_assistant.adapters.feishu.wiki_client import FeishuWikiClient
from learning_assistant.core.base_adapter import AdapterState, BaseAdapter
from learning_assistant.core.event_bus import Event, EventBus, EventType
from learning_assistant.core.publishing.models import PublishPayload


class FeishuKnowledgeBaseAdapter(BaseAdapter):
    """Publish module outputs to Feishu knowledge base."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = FeishuKnowledgeBaseConfig()
        self.wiki_client: FeishuWikiClient | None = None
        self.document_builder = FeishuDocumentBuilder()

    @property
    def name(self) -> str:
        return "feishu"

    @property
    def description(self) -> str:
        return "Feishu (飞书) platform adapter for notifications and document sync"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        self._set_initializing()
        self.event_bus = event_bus
        settings_payload = dict(config.get("config", {}))
        if "subscriptions" in config:
            settings_payload["subscriptions"] = config["subscriptions"]
        enabled = config.get("enabled", True)
        self.settings = FeishuKnowledgeBaseConfig(enabled=enabled, **settings_payload)
        self.config = config

        if not self.settings.enabled:
            logger.info("Feishu adapter disabled in adapters.yaml, skipping subscriptions")
            self._set_ready()
            return

        self.wiki_client = FeishuWikiClient(self.settings)
        self._subscribe_publish_events()
        self._set_ready()

    def push_content(self, content: dict[str, Any]) -> FeishuPublishResult:
        """Push content to Feishu knowledge base.

        Args:
            content: PublishPayload as dict

        Returns:
            FeishuPublishResult with success status, url, etc.
        """
        payload = PublishPayload.model_validate(content)
        if not self.settings.enabled:
            logger.debug("Feishu adapter disabled, skipping content push")
            return FeishuPublishResult(success=False, message="Feishu adapter disabled")
        if payload.module not in self.settings.publish_modules:
            logger.debug(f"Module {payload.module} not enabled for Feishu publishing")
            return FeishuPublishResult(success=False, message=f"Module {payload.module} not enabled for publishing")
        if not self.wiki_client:
            raise RuntimeError("Feishu wiki client not initialized")

        blocks = self.document_builder.build(payload)
        result = self.wiki_client.publish(payload, blocks)
        if result.success and self.event_bus:
            self.event_bus.publish(
                Event(
                    event_type=EventType.CONTENT_PUSHED,
                    source=self.name,
                    data={
                        "module": payload.module,
                        "title": payload.title,
                        "node_token": result.node_token,
                        "document_id": result.document_id,
                        "url": result.url,
                    },
                )
            )
        return result

    def sync_data(self, data_type: str, data: dict[str, Any]) -> bool:
        if data_type != "publish_payload":
            logger.debug(f"Unsupported Feishu sync data type: {data_type}")
            return False
        result = self.push_content(data)
        return result.success

    def handle_trigger(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        return {"status": "not_implemented", "trigger": trigger_data}

    def cleanup(self) -> None:
        self._set_shutting_down()
        for event_type in list(self.get_subscribed_events()):
            self.unsubscribe_from_event(event_type)
        self.wiki_client = None
        self.state = AdapterState.UNINITIALIZED

    def _subscribe_publish_events(self) -> None:
        subscribed_events = {
            EventType.VIDEO_SUMMARIZED,
            EventType.LINK_PROCESSED,
            EventType.VOCABULARY_EXTRACTED,
        }

        configured = set(self.settings.subscriptions)
        if configured:
            subscribed_events = {
                event_type
                for event_type in subscribed_events
                if event_type.value in configured
            }

        for event_type in subscribed_events:
            self.subscribe_to_event(event_type, self._handle_publish_event)

    def _handle_publish_event(self, event: Event) -> None:
        payload_data = event.data.get("publish_payload")
        if not payload_data:
            logger.debug(f"Event {event.event_type.value} has no publish payload, skipping")
            return

        try:
            result = self.push_content(payload_data)
            if result.success:
                logger.info(f"Feishu publish succeeded: {result.url or result.node_token}")
                # Add feishu_url to event result data
                result_data = event.data.get("result")
                if result_data and isinstance(result_data, dict):
                    result_data["feishu_url"] = result.url
                    result_data["feishu_node_token"] = result.node_token
            else:
                logger.warning(f"Feishu publish failed: {result.message}")
        except Exception as exc:
            self._set_error(str(exc))
            logger.error(f"Feishu publish failed for {event.event_type.value}: {exc}")
