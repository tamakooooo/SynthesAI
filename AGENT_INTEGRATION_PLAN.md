# Agent 集成支持实施计划（最小化版）

> **版本**: v0.2.0
> **周期**: 3天（Day 43-45）
> **策略**: Skills（精简文档）+ Python API 层
> **优先级**: Claude Code / Nanobot > 自定义 Agent

---

## 🎯 项目目标

让 Claude Code、Nanobot 和其他 Agent 框架都能使用 Learning Assistant 的技能：

| Agent 框架 | 集成方式 | 优先级 | 预计完成 |
|-----------|---------|--------|---------|
| **Claude Code** | Skills + Python API | ⭐⭐⭐ | Day 45 |
| **Nanobot** | Skills + Python API | ⭐⭐⭐ | Day 45 |
| **自定义 Agent** | Python API | ⭐⭐⭐ | Day 45 |

---

## 🏗️ 架构设计

### 目录结构（精简版）

```
skills/                          # Skills 文档层
├── README.md                    # Skills 总览
├── video-summary.md             # video-summary Skill（单文件）
├── list-skills.md               # list-skills Skill（单文件）
└── learning-history.md          # learning-history Skill（单文件）

src/learning_assistant/api/      # Python API 层
├── __init__.py                  # 导出接口
├── agent_api.py                 # 核心接口类
├── convenience.py               # 快捷函数
├── schemas.py                   # 输出 Schema
└── exceptions.py                # 统一异常

tests/api/                       # API 测试
└── test_api.py                  # 综合测试

docs/agent_integration.md        # 集成文档
```

---

## 📅 Day 43: Skills 层

### 任务清单

- [ ] 创建 `skills/` 目录
- [ ] 创建 `skills/README.md`
- [ ] 创建 3个 Skill 文档（单文件）

### 交付物

#### `skills/README.md`

```markdown
# Learning Assistant Skills

## 可用 Skills

| Skill | 描述 | 状态 |
|-------|------|------|
| [video-summary](video-summary.md) | 视频内容总结 | ✅ 可用 |
| [list-skills](list-skills.md) | 列出可用技能 | ✅ 可用 |
| [learning-history](learning-history.md) | 查看学习历史 | ✅ 可用 |

## 如何使用

### 直接调用 Python API（推荐）

```python
from learning_assistant.api import summarize_video

result = await summarize_video(url="https://...")
print(result["summary"])
```

### 使用 AgentAPI 类

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()
result = await api.summarize_video(url="https://...")
```
```

#### `skills/video-summary.md`

```markdown
---
name: video-summary
version: 1.0.0
description: 总结视频内容并生成学习笔记
---

# Video Summary

## 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| url | string | ✅ | - | 视频URL |
| format | string | ❌ | markdown | 输出格式 |
| language | string | ❌ | zh | 语言（zh/en） |

## 输出

```json
{
  "status": "success",
  "url": "https://...",
  "title": "视频标题",
  "summary": {"content": "...", "key_points": []},
  "transcript": "字幕文本",
  "files": {"summary_path": "...", "subtitle_path": "..."}
}
```

## 使用示例

```python
from learning_assistant.api import summarize_video

# 基本用法
result = await summarize_video(url="https://www.bilibili.com/video/BV...")

# 完整参数
result = await summarize_video(
    url="https://www.youtube.com/watch?v=...",
    format="pdf",
    language="en"
)

print(result["summary"]["content"])
```

## 错误处理

```python
from learning_assistant.api import summarize_video
from learning_assistant.api.exceptions import VideoNotFoundError

try:
    result = await summarize_video(url="https://...")
except VideoNotFoundError:
    print("视频不存在")
except Exception as e:
    print(f"处理失败: {e}")
```

**常见错误**：
- `VideoNotFoundError` - 视频不存在
- `VideoDownloadError` - 下载失败（需配置 Cookie）
- `TranscriptionError` - 转录失败（等待重试）
- `LLMAPIError` - LLM 错误（检查 API Key）
```

#### `skills/list-skills.md`

```markdown
---
name: list-skills
version: 1.0.0
description: 列出所有可用技能
---

# List Skills

## 使用示例

```python
from learning_assistant.api import list_available_skills

skills = list_available_skills()
for skill in skills:
    print(f"- {skill['name']}: {skill['description']}")
```

**输出**：
```
- video-summary: 视频内容总结
- list-skills: 列出可用技能
- learning-history: 查看学习历史
```
```

#### `skills/learning-history.md`

```markdown
---
name: learning-history
version: 1.0.0
description: 查看学习历史记录
---

# Learning History

## 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | ❌ | 10 | 返回数量 |
| search | string | ❌ | - | 搜索关键词 |

## 使用示例

```python
from learning_assistant.api import get_recent_history

# 查看最近10条
records = get_recent_history(limit=10)

# 搜索关键词
records = get_recent_history(search="Python")

for record in records:
    print(f"[{record['timestamp']}] {record['title']}")
```
```

---

## 📅 Day 44: Python API 层

### 任务清单

- [ ] 创建 `src/learning_assistant/api/` 目录
- [ ] 实现 5个文件
  - [ ] `__init__.py`
  - [ ] `agent_api.py`
  - [ ] `convenience.py`
  - [ ] `schemas.py`
  - [ ] `exceptions.py`

### 交付物

#### `src/learning_assistant/api/__init__.py`

```python
"""Learning Assistant Agent API."""

from learning_assistant.api.agent_api import AgentAPI
from learning_assistant.api.convenience import (
    summarize_video,
    list_available_skills,
    get_recent_history,
)

__all__ = [
    "AgentAPI",
    "summarize_video",
    "list_available_skills",
    "get_recent_history",
]
```

#### `src/learning_assistant/api/agent_api.py`

```python
"""Agent API - 标准化接口."""

from typing import Any
from pathlib import Path
from datetime import datetime

from learning_assistant import PluginManager
from learning_assistant.core.history_manager import HistoryManager
from learning_assistant.api.schemas import VideoSummaryResult, SkillInfo, HistoryRecord


class AgentAPI:
    """Learning Assistant Agent API."""

    def __init__(self, config_path: Path | None = None):
        self.plugin_manager = PluginManager(config_path)
        self.plugin_manager.load_all()
        self.history_manager = HistoryManager()

    async def summarize_video(
        self,
        url: str,
        format: str = "markdown",
        language: str = "zh",
        output_dir: str | None = None,
        **kwargs: Any,
    ) -> VideoSummaryResult:
        """总结视频内容."""
        video_module = self.plugin_manager.get_module("video_summary")
        result = await video_module.run(
            url=url, format=format, language=language, output_dir=output_dir, **kwargs
        )

        return VideoSummaryResult(
            status="success",
            url=url,
            title=result.get("metadata", {}).get("title", ""),
            summary=result.get("summary", {}),
            transcript=result.get("transcript", ""),
            files={
                "summary_path": result.get("summary_path"),
                "subtitle_path": result.get("subtitle_path"),
            },
            metadata=result.get("metadata", {}),
            timestamp=datetime.now().isoformat(),
        )

    def list_skills(self) -> list[SkillInfo]:
        """列出所有可用技能."""
        modules = self.plugin_manager.list_modules()
        return [
            SkillInfo(
                name=module.name,
                description=module.description,
                version=module.version,
                status="available" if module.enabled else "disabled",
            )
            for module in modules
        ]

    def get_history(
        self, limit: int = 10, search: str | None = None, module: str | None = None
    ) -> list[HistoryRecord]:
        """获取学习历史记录."""
        records = self.history_manager.get_records(limit=limit, search=search, module=module)
        return [
            HistoryRecord(
                id=record.id,
                module=record.module,
                title=record.title,
                url=record.url,
                timestamp=record.timestamp.isoformat(),
                status=record.status,
            )
            for record in records
        ]
```

#### `src/learning_assistant/api/convenience.py`

```python
"""便捷函数 - 一行调用."""

import asyncio
from typing import Any

from learning_assistant.api.agent_api import AgentAPI


async def summarize_video(url: str, **options: Any) -> dict[str, Any]:
    """视频总结（异步）."""
    api = AgentAPI()
    result = await api.summarize_video(url=url, **options)
    return result.model_dump()


def list_available_skills() -> list[dict[str, Any]]:
    """列出可用技能."""
    api = AgentAPI()
    skills = api.list_skills()
    return [skill.model_dump() for skill in skills]


def get_recent_history(limit: int = 10) -> list[dict[str, Any]]:
    """获取最近学习记录."""
    api = AgentAPI()
    records = api.get_history(limit=limit)
    return [record.model_dump() for record in records]


def summarize_video_sync(url: str, **options: Any) -> dict[str, Any]:
    """视频总结（同步）."""
    return asyncio.run(summarize_video(url, **options))
```

#### `src/learning_assistant/api/schemas.py`

```python
"""输出 Schema - Pydantic 模型."""

from typing import Any
from pydantic import BaseModel


class VideoSummaryResult(BaseModel):
    """视频总结结果."""
    status: str
    url: str
    title: str
    summary: dict[str, Any]
    transcript: str
    files: dict[str, str | None]
    metadata: dict[str, Any]
    timestamp: str


class SkillInfo(BaseModel):
    """技能信息."""
    name: str
    description: str
    version: str
    status: str


class HistoryRecord(BaseModel):
    """历史记录."""
    id: str
    module: str
    title: str
    url: str
    timestamp: str
    status: str
```

#### `src/learning_assistant/api/exceptions.py`

```python
"""统一异常."""


class LearningAssistantError(Exception):
    """基础异常."""
    pass


class VideoNotFoundError(LearningAssistantError):
    """视频不存在."""
    pass


class VideoDownloadError(LearningAssistantError):
    """下载失败."""
    pass


class TranscriptionError(LearningAssistantError):
    """转录失败."""
    pass


class LLMAPIError(LearningAssistantError):
    """LLM 错误."""
    pass
```

---

## 📅 Day 45: 测试和文档

### 任务清单

- [ ] 编写 API 测试
- [ ] 编写集成文档
- [ ] 更新主 README
- [ ] 更新版本号

### 交付物

#### `tests/api/test_api.py`

```python
"""API 综合测试."""

import pytest
from learning_assistant.api import summarize_video, list_available_skills


@pytest.mark.asyncio
async def test_summarize_video():
    """测试视频总结."""
    result = await summarize_video(url="https://www.bilibili.com/video/BV1GJ411x7h7")

    assert result["status"] == "success"
    assert "summary" in result
    assert result["url"] == "https://www.bilibili.com/video/BV1GJ411x7h7"


def test_list_available_skills():
    """测试列出技能."""
    skills = list_available_skills()

    assert len(skills) > 0
    assert any(s["name"] == "video-summary" for s in skills)
```

#### `docs/agent_integration.md`

```markdown
# Agent 集成指南

## 快速开始

### Python 调用

```python
from learning_assistant.api import summarize_video

result = await summarize_video(url="https://...")
print(result["summary"])
```

### Claude Code / Nanobot

查看 [Skills 文档](../skills/README.md)了解如何使用。

## API 参考

- `summarize_video(url, **options)` - 视频总结
- `list_available_skills()` - 列出技能
- `get_recent_history(limit)` - 查看历史

## 完整文档

- [Skills 文档](../skills/README.md)
- [API 文档](api.md)
```

#### 更新 `README.md`

在主 README 中添加：

```markdown
## Agent 集成

Learning Assistant 支持多种 Agent 框架：

- **Claude Code / Nanobot**: 使用 [Skills](skills/README.md)
- **自定义 Agent**: 使用 [Python API](docs/agent_integration.md)

### 快速示例

```python
from learning_assistant.api import summarize_video

result = await summarize_video(url="https://...")
print(result["summary"])
```
```

---

## ✅ 验收标准

- [ ] 3个 Skills 文档创建（单文件）
- [ ] Python API 5个文件实现
- [ ] 基本测试通过
- [ ] 集成文档完成
- [ ] README 更新
- [ ] 版本号更新到 v0.2.0

---

## 🚀 开始实施

**Day 43**: 创建 Skills 文档
**Day 44**: 实现 Python API
**Day 45**: 测试和文档

准备就绪！