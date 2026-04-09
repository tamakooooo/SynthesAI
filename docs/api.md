# API 文档

> 版本: v0.1.0 | 更新日期: 2026-03-31

## 核心 API

### BaseModule

所有功能模块的抽象基类。

```python
from learning_assistant.core.base_module import BaseModule

class MyModule(BaseModule):
    @property
    def name(self) -> str:
        return "my_module"
    
    def initialize(self, config: dict, event_bus: EventBus) -> None:
        pass
    
    def execute(self, input_data: dict) -> dict:
        pass
    
    def cleanup(self) -> None:
        pass
```

### BaseAdapter

所有平台适配器的抽象基类。

```python
from learning_assistant.core.base_adapter import BaseAdapter

class MyAdapter(BaseAdapter):
    def initialize(self, config: dict, event_bus: EventBus) -> None:
        pass
    
    def push_content(self, content: dict) -> bool:
        pass
    
    def sync_data(self, data_type: str, query: dict) -> Any:
        pass
    
    def handle_trigger(self, trigger_data: dict) -> dict:
        pass
```

### EventBus

事件总线，用于模块间通信。

```python
from learning_assistant.core.event_bus import EventBus, Event, EventType

event_bus = EventBus()

# 订阅事件
event_bus.subscribe(EventType.VIDEO_SUMMARIZED, handler)

# 发布事件
event_bus.publish(Event(
    type=EventType.VIDEO_SUMMARIZED,
    data={"video_id": "123"}
))
```

### LLMService

统一的 LLM 调用接口。

```python
from learning_assistant.core.llm.service import LLMService

llm = LLMService(provider="openai", api_key="sk-...")

response = llm.call(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4"
)
```

完整API文档请参考源代码和类型提示。
