# 插件开发教程

> 版本: v0.1.0 | 更新日期: 2026-03-31

本教程将指导你如何为 Learning Assistant 开发自定义模块和适配器。

## 目录

- [插件系统概览](#插件系统概览)
- [开发环境设置](#开发环境设置)
- [模块开发](#模块开发)
- [适配器开发](#适配器开发)
- [测试插件](#测试插件)
- [发布插件](#发布插件)

---

## 插件系统概览

Learning Assistant 采用双插件架构：

```
┌─────────────────────────────────────┐
│         CLI Layer (Typer)           │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│        Core Engine (PluginManager)   │
└──────┬─────────────────┬─────────────┘
       │                 │
  ┌────┴────┐       ┌────┴─────┐
  │ Modules │       │ Adapters │
  └─────────┘       └──────────┘
```

**模块 (Modules)**:
- 提供核心功能（如视频总结、链接学习）
- 继承 `BaseModule`
- 通过 YAML 配置文件声明

**适配器 (Adapters)**:
- 连接外部平台（如思源笔记、Obsidian）
- 继承 `BaseAdapter`
- 响应事件，推送内容

---

## 开发环境设置

### 1. Fork 并克隆仓库

```bash
# Fork 仓库到你的账户
# 然后克隆你的 fork
git clone https://github.com/YOUR_USERNAME/learning-assistant.git
cd learning-assistant

# 添加上游仓库
git remote add upstream https://github.com/original/learning-assistant.git
```

### 2. 创建开发分支

```bash
git checkout -b feature/my-awesome-module
```

### 3. 安装开发依赖

```bash
# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks（可选）
pre-commit install
```

### 4. 验证开发环境

```bash
# 运行测试
pytest

# 类型检查
mypy src/learning_assistant

# 代码格式化
black src/learning_assistant

# Linting
ruff check src/learning_assistant
```

---

## 模块开发

### 步骤 1: 创建模块目录

```bash
# 创建模块目录结构
mkdir -p src/learning_assistant/modules/my_module
touch src/learning_assistant/modules/my_module/__init__.py
touch src/learning_assistant/modules/my_module/plugin.yaml
```

### 步骤 2: 编写 plugin.yaml

`src/learning_assistant/modules/my_module/plugin.yaml`:
```yaml
name: "my_module"
version: "0.1.0"
description: "My custom module description"
author: "Your Name"
email: "your.email@example.com"

type: "module"  # module 或 adapter

# 模块配置
config:
  enabled: true
  priority: 10  # 加载优先级（数字越小越优先）

# 依赖（可选）
dependencies:
  modules: []  # 依赖的其他模块
  adapters: []  # 依赖的适配器

# CLI 命令（可选）
cli_commands:
  - name: "my-cmd"
    help: "My custom command"
```

### 步骤 3: 实现模块类

`src/learning_assistant/modules/my_module/__init__.py`:
```python
"""
My Module for Learning Assistant.

Provides custom functionality.
"""

from typing import Any

from loguru import logger

from learning_assistant.core.base_module import BaseModule
from learning_assistant.core.event_bus import EventBus


class MyModule(BaseModule):
    """
    My Custom Module.

    Provides custom functionality for learning.
    """

    def __init__(self) -> None:
        """Initialize my module."""
        self.config: dict[str, Any] = {}
        self.event_bus: EventBus | None = None

        logger.info("MyModule created")

    @property
    def name(self) -> str:
        """Module name."""
        return "my_module"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize my module.

        Args:
            config: Module configuration
            event_bus: Event bus instance
        """
        self.config = config
        self.event_bus = event_bus

        logger.info(f"MyModule initialized with config: {config}")

        # 订阅事件（可选）
        # event_bus.subscribe(EventType.VIDEO_SUMMARIZED, self.on_video_summarized)

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute my module's core functionality.

        Args:
            input_data: Input data dict

        Returns:
            Output data dict
        """
        logger.info(f"MyModule executing with input: {input_data}")

        # 实现你的功能逻辑
        result = self._do_something(input_data)

        return {
            "status": "success",
            "result": result,
        }

    def cleanup(self) -> None:
        """Cleanup module resources."""
        logger.info("MyModule cleanup")

    def register_cli_commands(self, cli_group: Any) -> None:
        """
        Register CLI commands for this module.

        Args:
            cli_group: Typer CLI group
        """
        import typer

        @cli_group.command(name="my-cmd")
        def my_command(
            input: str = typer.Option(..., help="Input parameter"),
            option: bool = typer.Option(False, help="Optional flag"),
        ) -> None:
            """My custom command description."""
            from rich import print

            print(f"[green]Executing my command with input: {input}[/green]")

            # 调用模块功能
            # result = self.execute({"input": input})

    def _do_something(self, data: dict[str, Any]) -> Any:
        """Private helper method."""
        # 实现具体逻辑
        return data
```

### 步骤 4: 注册模块

模块会被 PluginManager 自动发现和加载，无需手动注册。

### 步骤 5: 编写测试

`tests/modules/test_my_module.py`:
```python
"""Tests for MyModule."""

import pytest

from learning_assistant.core.event_bus import EventBus
from learning_assistant.modules.my_module import MyModule


class TestMyModule:
    """Test MyModule functionality."""

    def test_module_creation(self) -> None:
        """Test module creation."""
        module = MyModule()

        assert module.name == "my_module"

    def test_module_initialization(self) -> None:
        """Test module initialization."""
        module = MyModule()
        event_bus = EventBus()

        config = {"key": "value"}
        module.initialize(config, event_bus)

        assert module.config == config
        assert module.event_bus == event_bus

    def test_module_execute(self) -> None:
        """Test module execution."""
        module = MyModule()
        event_bus = EventBus()

        module.initialize({}, event_bus)

        result = module.execute({"input": "test"})

        assert result["status"] == "success"

    def test_module_cleanup(self) -> None:
        """Test module cleanup."""
        module = MyModule()
        event_bus = EventBus()

        module.initialize({}, event_bus)
        module.cleanup()

        # Cleanup should not raise exceptions
        assert True
```

---

## 适配器开发

### 步骤 1: 创建适配器目录

```bash
# 创建适配器目录结构
mkdir -p src/learning_assistant/adapters/my_adapter
touch src/learning_assistant/adapters/my_adapter/__init__.py
touch src/learning_assistant/adapters/my_adapter/adapter.py
touch src/learning_assistant/adapters/my_adapter/plugin.yaml
```

### 步骤 2: 编写 plugin.yaml

`src/learning_assistant/adapters/my_adapter/plugin.yaml`:
```yaml
name: "my_adapter"
version: "0.1.0"
description: "My custom adapter for external platform"
author: "Your Name"
email: "your.email@example.com"

type: "adapter"

# 适配器配置
config:
  enabled: true
  priority: 10

# 需要的配置字段
required_config:
  - "api_key"  # 必须配置的字段
  - "endpoint"
```

### 步骤 3: 实现适配器类

`src/learning_assistant/adapters/my_adapter/adapter.py`:
```python
"""
My Adapter for Learning Assistant.

Provides integration with external platform.
"""

from typing import Any

from loguru import logger

from learning_assistant.core.base_adapter import BaseAdapter
from learning_assistant.core.event_bus import Event, EventType


class MyAdapter(BaseAdapter):
    """
    My Custom Adapter.

    Integrates Learning Assistant with external platform.
    """

    def __init__(self) -> None:
        """Initialize my adapter."""
        super().__init__()

        self.api_key: str | None = None
        self.endpoint: str | None = None

        logger.info("MyAdapter created")

    @property
    def name(self) -> str:
        """Adapter name."""
        return "my_adapter"

    @property
    def description(self) -> str:
        """Adapter description."""
        return "My custom adapter for external platform integration"

    def initialize(self, config: dict[str, Any], event_bus: Any) -> None:
        """
        Initialize my adapter.

        Args:
            config: Adapter configuration
            event_bus: Event bus instance
        """
        logger.info(f"MyAdapter initializing with config: {config}")

        # 验证必需配置
        if not self.validate_config(config, ["api_key", "endpoint"]):
            self._last_error = "Missing required config fields"
            self.set_error("Missing required config fields")
            return

        # 调用父类初始化
        super().initialize(config, event_bus)

        # 保存配置
        self.api_key = config.get("api_key")
        self.endpoint = config.get("endpoint")

        # 订阅事件
        self.subscribe_to_event(EventType.VIDEO_SUMMARIZED, self.on_video_summarized)

        logger.info("MyAdapter initialized successfully")

    def push_content(self, content: dict[str, Any]) -> bool:
        """
        Push content to external platform.

        Args:
            content: Content to push

        Returns:
            True if successful, False otherwise
        """
        if not self.is_ready:
            logger.warning("MyAdapter not ready, cannot push content")
            return False

        logger.info(f"MyAdapter pushing content: {content}")

        try:
            # 实现推送到外部平台的逻辑
            # response = self._api_call(content)
            return True

        except Exception as e:
            logger.error(f"MyAdapter push failed: {e}")
            self.record_error(str(e))
            return False

    def sync_data(self, data_type: str, query: dict[str, Any]) -> Any:
        """
        Sync data from external platform.

        Args:
            data_type: Type of data to sync
            query: Query parameters

        Returns:
            Synced data
        """
        logger.info(f"MyAdapter syncing data: {data_type}")

        # 实现数据同步逻辑
        return None

    def handle_trigger(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        """
        Handle external trigger (e.g., webhook).

        Args:
            trigger_data: Trigger data from external source

        Returns:
            Response data
        """
        logger.info(f"MyAdapter handling trigger: {trigger_data}")

        # 实现触发器处理逻辑
        return {"status": "ok"}

    def cleanup(self) -> None:
        """Cleanup adapter resources."""
        logger.info("MyAdapter cleanup")

        # 取消事件订阅
        self.unsubscribe_from_all_events()

        # 清理资源
        self.api_key = None
        self.endpoint = None

        # 调用父类清理
        super().cleanup()

    def on_video_summarized(self, event: Event) -> None:
        """
        Handle VIDEO_SUMMARIZED event.

        Args:
            event: Event data
        """
        logger.info(f"MyAdapter received VIDEO_SUMMARIZED event: {event}")

        # 自动推送视频总结到外部平台
        content = event.data
        self.push_content(content)

    def _api_call(self, data: dict[str, Any]) -> Any:
        """Make API call to external platform."""
        # 实现 API 调用逻辑
        pass
```

### 步骤 4: 编写测试

`tests/adapters/test_my_adapter.py`:
```python
"""Tests for MyAdapter."""

import pytest

from learning_assistant.adapters.my_adapter import MyAdapter
from learning_assistant.core.event_bus import EventBus, Event, EventType


class TestMyAdapter:
    """Test MyAdapter functionality."""

    def test_adapter_creation(self) -> None:
        """Test adapter creation."""
        adapter = MyAdapter()

        assert adapter.name == "my_adapter"

    def test_adapter_initialization(self) -> None:
        """Test adapter initialization."""
        adapter = MyAdapter()
        event_bus = EventBus()

        config = {
            "api_key": "test-key",
            "endpoint": "https://api.example.com",
        }

        adapter.initialize(config, event_bus)

        assert adapter.is_ready
        assert adapter.api_key == "test-key"

    def test_adapter_initialization_missing_config(self) -> None:
        """Test adapter initialization with missing config."""
        adapter = MyAdapter()
        event_bus = EventBus()

        config = {}  # Missing required fields

        adapter.initialize(config, event_bus)

        assert not adapter.is_ready

    def test_adapter_push_content(self) -> None:
        """Test adapter push content."""
        adapter = MyAdapter()
        event_bus = EventBus()

        config = {
            "api_key": "test-key",
            "endpoint": "https://api.example.com",
        }

        adapter.initialize(config, event_bus)

        result = adapter.push_content({"title": "Test"})

        assert result is True

    def test_adapter_event_subscription(self) -> None:
        """Test adapter event subscription."""
        adapter = MyAdapter()
        event_bus = EventBus()

        config = {
            "api_key": "test-key",
            "endpoint": "https://api.example.com",
        }

        adapter.initialize(config, event_bus)

        # Should be subscribed to VIDEO_SUMMARIZED
        assert EventType.VIDEO_SUMMARIZED in adapter.get_subscribed_events()

    def test_adapter_cleanup(self) -> None:
        """Test adapter cleanup."""
        adapter = MyAdapter()
        event_bus = EventBus()

        config = {
            "api_key": "test-key",
            "endpoint": "https://api.example.com",
        }

        adapter.initialize(config, event_bus)
        adapter.cleanup()

        assert len(adapter.get_subscribed_events()) == 0
```

---

## 测试插件

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/modules/test_my_module.py

# 运行特定测试类
pytest tests/modules/test_my_module.py::TestMyModule

# 运行特定测试
pytest tests/modules/test_my_module.py::TestMyModule::test_module_execute

# 生成覆盖率报告
pytest --cov=src/learning_assistant/modules/my_module --cov-report=html
```

### 测试最佳实践

1. **测试所有公开方法**
2. **测试边界情况**
3. **测试错误处理**
4. **使用 Mock 隔离外部依赖**
5. **保持测试独立**

---

## 发布插件

### 1. 代码质量检查

```bash
# 类型检查
mypy src/learning_assistant/modules/my_module

# 代码格式化
black src/learning_assistant/modules/my_module

# Linting
ruff check src/learning_assistant/modules/my_module
```

### 2. 更新文档

- 更新 `README.md`
- 更新 `docs/api.md`
- 添加使用示例

### 3. 提交代码

```bash
# 提交更改
git add .
git commit -m "feat: add my_module for custom functionality"

# 推送到你的 fork
git push origin feature/my-awesome-module
```

### 4. 创建 Pull Request

1. 在 GitHub 上创建 Pull Request
2. 填写 PR 模板
3. 等待代码审查
4. 根据反馈修改

---

## 示例项目

查看现有模块和适配器作为参考：

**模块示例**:
- [VideoSummaryModule](../src/learning_assistant/modules/video_summary/)
- [LinkLearningModule](../src/learning_assistant/modules/link_learning/)
- [VocabularyLearningModule](../src/learning_assistant/modules/vocabulary/)

**适配器示例**:
- [TestValidationAdapter](../src/learning_assistant/adapters/test_validation_adapter.py)

---

## 下一步

- 📖 阅读 [API 文档](api.md)
- ❓ 查看 [常见问题](faq.md)
- 💬 加入社区讨论

---

**需要帮助？**
- GitHub Issues: [提交问题](https://github.com/yourname/learning-assistant/issues)
- 文档网站: [learning-assistant.readthedocs.io](https://learning-assistant.readthedocs.io)