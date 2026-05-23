"""Feishu knowledge base adapter."""

from __future__ import annotations

from typing import Any

from loguru import logger

from learning_assistant.adapters.feishu.document_builder import FeishuDocumentBuilder
from learning_assistant.adapters.feishu.models import (
    FeishuKnowledgeBaseConfig,
    FeishuPublishResult,
)
from learning_assistant.adapters.feishu.wiki_client import FeishuWikiClient
from learning_assistant.core.base_adapter import AdapterState, BaseAdapter
from learning_assistant.core.event_bus import Event, EventBus, EventType
from learning_assistant.core.publishing.models import PublishPayload


_DEPRECATED_CONFIG_KEYS = {"overwrite_strategy"}


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

        raw_settings = dict(config.get("config", {}))
        for key in list(raw_settings.keys()):
            if key in _DEPRECATED_CONFIG_KEYS:
                logger.warning(f"Ignoring deprecated Feishu config key: {key}")
                raw_settings.pop(key)
        if "subscriptions" in config:
            raw_settings["subscriptions"] = config["subscriptions"]

        enabled = config.get("enabled", True)
        self.settings = FeishuKnowledgeBaseConfig(enabled=enabled, **raw_settings)
        self.config = config

        if not self.settings.enabled:
            logger.info("Feishu adapter disabled, skipping subscriptions")
            self._set_ready()
            return

        self._warn_on_incomplete_config()
        self.wiki_client = FeishuWikiClient(self.settings)
        self._subscribe_publish_events()
        self._set_ready()

    def _warn_on_incomplete_config(self) -> None:
        if not self.settings.resolve_space_id():
            logger.warning(
                "Feishu space_id empty (config + "
                f"${self.settings.space_id_env} both missing); publishing will fail"
            )
        if not self.settings.resolve_root_node_token():
            logger.warning(
                "Feishu root_node_token empty (config + "
                f"${self.settings.root_node_token_env} both missing); "
                "wiki move will fail"
            )
        if not self.settings.space_domain:
            logger.warning(
                "Feishu space_domain not set; URLs will use feishu.cn fallback"
            )

    def push_content(self, content: dict[str, Any]) -> FeishuPublishResult:
        payload = PublishPayload.model_validate(content)
        if not self.settings.enabled:
            return FeishuPublishResult(success=False, message="Feishu adapter disabled")
        if payload.module not in self.settings.publish_modules:
            return FeishuPublishResult(
                success=False,
                message=f"Module {payload.module} not enabled for publishing",
            )
        if not self.wiki_client:
            raise RuntimeError("Feishu wiki client not initialized")

        build_result = self.document_builder.build(payload)
        result = self.wiki_client.publish(payload, build_result)

        if result.success and self.event_bus:
            self._emit_publish_events(payload, result)

        return result

    def _emit_publish_events(
        self,
        payload: PublishPayload,
        result: FeishuPublishResult,
    ) -> None:
        event_data = {
            "module": payload.module,
            "title": payload.title,
            "source_url": payload.source_url,
            "node_token": result.node_token,
            "document_id": result.document_id,
            "url": result.url,
        }
        for event_type in (EventType.CONTENT_PUSHED, EventType.FEISHU_PUBLISHED):
            self.event_bus.publish(
                Event(event_type=event_type, source=self.name, data=event_data)
            )

    def sync_data(self, data_type: str, data: dict[str, Any]) -> bool:
        if data_type != "publish_payload":
            logger.debug(f"Unsupported Feishu sync data type: {data_type}")
            return False
        return self.push_content(data).success

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
            logger.debug(f"Event {event.event_type.value} has no publish payload")
            return

        try:
            result = self.push_content(payload_data)
            if result.success:
                logger.info(f"Feishu publish succeeded: {result.url or result.node_token}")
            else:
                logger.warning(f"Feishu publish failed: {result.message}")
        except Exception as exc:
            self._set_error(str(exc))
            logger.error(f"Feishu publish exception for {event.event_type.value}: {exc}")
