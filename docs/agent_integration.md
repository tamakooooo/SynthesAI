# Agent 集成指南

> **版本**: v0.2.0
> **更新日期**: 2026-03-31

本文档介绍如何将 Learning Assistant 集成到各种 Agent 框架中。

---

## 目录

- [快速开始](#快速开始)
- [Claude Code 集成](#claude-code-集成)
- [Nanobot 集成](#nanobot-集成)
- [自定义 Agent 集成](#自定义-agent-集成)
- [API 参考](#api-参考)
- [最佳实践](#最佳实践)

---

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourname/learning-assistant.git
cd learning-assistant

# 安装依赖
pip install -e ".[dev]"

# 配置 API Key
export OPENAI_API_KEY="sk-..."
```

### 5 分钟集成示例

```python
from learning_assistant.api import summarize_video

# 视频总结
result = await summarize_video(url="https://www.bilibili.com/video/BV...")
print(result["summary"]["content"])

# 列出技能
from learning_assistant.api import list_available_skills
skills = list_available_skills()

# 查看历史
from learning_assistant.api import get_recent_history
records = get_recent_history(limit=10)
```

---

## Claude Code 集成

### 方式 1: 直接调用 Python API

Claude Code 可以直接调用 Learning Assistant 的 Python API：

```python
from learning_assistant.api import summarize_video

async def handle_user_request(user_message: str):
    """处理用户消息."""
    # 提取视频 URL
    if "bilibili.com" in user_message or "youtube.com" in user_message:
        url = extract_url(user_message)

        # 调用 Learning Assistant
        result = await summarize_video(url=url)

        # 返回结果
        return f"""
视频总结完成！

标题: {result['title']}

总结:
{result['summary']['content']}

核心要点:
{chr(10).join(f'- {p}' for p in result['summary']['key_points'])}

总结文件: {result['files']['summary_path']}
字幕文件: {result['files']['subtitle_path']}
        """
```

### 方式 2: 读取 Skills 文档

Claude Code 可以读取 `skills/` 目录下的文档了解如何使用：

```
用户: 帮我总结这个视频 https://www.bilibili.com/video/BV...

Claude: 我看到你提供了一个 B站视频链接。让我使用 Learning Assistant 的 video-summary skill 来总结它。

[Claude 读取 skills/video-summary.md 了解参数]

[调用 Python API]
from learning_assistant.api import summarize_video
result = await summarize_video(url="https://www.bilibili.com/video/BV...")

[返回结果]
视频总结完成！标题是"Python 编程基础教程"，主要内容包括：
- Python 环境搭建
- 基础语法
- 函数定义

完整总结已保存到: ./outputs/python_tutorial_summary.md
```

---

## Nanobot 集成

### 方式 1: 作为 Nanobot Skill

将 Learning Assistant 封装为 Nanobot skill：

```python
# nanobot_skills/learning_assistant.py

from learning_assistant.api import summarize_video, list_available_skills

async def video_summary_skill(url: str, language: str = "zh"):
    """
    Nanobot skill: 视频总结.

    Args:
        url: 视频URL
        language: 语言（zh/en）

    Returns:
        总结结果
    """
    result = await summarize_video(url=url, language=language)

    return {
        "title": result["title"],
        "summary": result["summary"]["content"],
        "key_points": result["summary"]["key_points"],
        "files": result["files"],
    }

async def list_skills_skill():
    """Nanobot skill: 列出技能."""
    skills = list_available_skills()
    return [skill["name"] for skill in skills]

# Nanobot skill 注册
SKILLS = {
    "video_summary": video_summary_skill,
    "list_skills": list_skills_skill,
}
```

### 方式 2: 直接在对话中使用

```python
from nanobot import Nanobot
from learning_assistant.api import summarize_video

bot = Nanobot()

@bot.on_message
async def handle_message(message):
    """处理消息."""
    if "视频链接" in message.text:
        url = extract_url(message.text)

        # 调用 Learning Assistant
        result = await summarize_video(url=url)

        # 回复用户
        await bot.reply(
            f"视频总结完成！\n\n"
            f"标题: {result['title']}\n\n"
            f"总结:\n{result['summary']['content']}"
        )
```

---

## 自定义 Agent 集成

### 使用 AgentAPI 类

```python
from learning_assistant.api import AgentAPI

class MyAgent:
    """自定义 Agent."""

    def __init__(self):
        self.api = AgentAPI()

    async def process_video_request(self, url: str):
        """处理视频请求."""
        try:
            result = await self.api.summarize_video(url=url)

            return {
                "success": True,
                "title": result.title,
                "summary": result.summary,
                "files": result.files,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def show_skills(self):
        """展示可用技能."""
        skills = self.api.list_skills()

        print("可用技能:")
        for skill in skills:
            print(f"- {skill.name}: {skill.description}")

    async def show_history(self):
        """展示历史记录."""
        records = self.api.get_history(limit=10)

        print("最近学习:")
        for record in records:
            print(f"- {record.title}")
```

### 使用便捷函数

```python
from learning_assistant.api import summarize_video, list_available_skills

# 最简单的方式
result = await summarize_video(url="https://...")
skills = list_available_skills()
```

### 错误处理示例

```python
from learning_assistant.api import summarize_video
from learning_assistant.api.exceptions import (
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
)

async def safe_video_summary(url: str):
    """安全的视频总结（完整错误处理）."""
    try:
        result = await summarize_video(url=url)
        return {"status": "success", "data": result}

    except VideoNotFoundError:
        return {"status": "error", "message": "视频不存在，请检查 URL"}

    except VideoDownloadError as e:
        return {
            "status": "error",
            "message": f"下载失败: {e}。可能需要配置 Cookie。",
        }

    except TranscriptionError as e:
        return {"status": "error", "message": f"转录失败: {e}。请稍后重试。"}

    except LLMAPIError as e:
        return {"status": "error", "message": f"LLM 错误: {e}。请检查 API Key。"}

    except Exception as e:
        return {"status": "error", "message": f"未知错误: {e}"}
```

---

## API 参考

### 主要函数

#### `summarize_video(url, **options)`

视频总结（异步）。

**参数**:
- `url` (str): 视频 URL
- `format` (str): 输出格式（markdown/pdf）
- `language` (str): 语言（zh/en）
- `output_dir` (str): 输出目录
- `cookie_file` (str): Cookie 文件路径
- `word_timestamps` (bool): 词级时间戳

**返回**: `dict`

**异常**: `VideoNotFoundError`, `VideoDownloadError`, `TranscriptionError`, `LLMAPIError`

**示例**:
```python
result = await summarize_video(
    url="https://www.bilibili.com/video/BV...",
    format="markdown",
    language="zh"
)
```

#### `list_available_skills()`

列出可用技能。

**返回**: `list[dict]`

**示例**:
```python
skills = list_available_skills()
for skill in skills:
    print(skill["name"])
```

#### `get_recent_history(limit)`

获取最近历史记录。

**参数**:
- `limit` (int): 返回数量

**返回**: `list[dict]`

**示例**:
```python
records = get_recent_history(limit=10)
```

#### `summarize_video_sync(url, **options)`

视频总结（同步版本）。

**示例**:
```python
result = summarize_video_sync(url="https://...")
```

### AgentAPI 类

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# 方法
await api.summarize_video(url, **options)  # 视频总结
api.list_skills()                           # 列出技能
api.get_history(limit, search, module)      # 查看历史
api.get_statistics()                        # 获取统计
```

---

## 最佳实践

### 1. 错误处理

始终捕获异常：

```python
from learning_assistant.api import summarize_video
from learning_assistant.api.exceptions import VideoNotFoundError

try:
    result = await summarize_video(url=url)
except VideoNotFoundError:
    print("视频不存在")
except Exception as e:
    print(f"处理失败: {e}")
```

### 2. 异步 vs 同步

- **异步** (`summarize_video`): 推荐，性能更好
- **同步** (`summarize_video_sync`): 简单脚本使用

### 3. 性能优化

- 使用缓存避免重复处理
- 批量处理时注意 API 限制
- 合理设置 `limit` 参数

### 4. 日志记录

```python
from loguru import logger

# Learning Assistant 使用 loguru 记录日志
# 配置日志级别
import os
os.environ["LEARNING_ASSISTANT_LOG_LEVEL"] = "DEBUG"
```

### 5. Cookie 配置

某些视频需要登录：

```python
result = await summarize_video(
    url="https://www.bilibili.com/video/BV...",
    cookie_file="data/cookies/bilibili.txt"
)
```

---

## 相关文档

- [Skills 文档](../skills/README.md) - 所有 Skills 详细说明
- [API 文档](api.md) - 完整 API 参考
- [用户指南](user-guide.md) - 使用指南

---

## 示例项目

查看完整示例：

- [Claude Code 示例](../examples/claude_code_integration.py)
- [Nanobot 示例](../examples/nanobot_integration.py)
- [自定义 Agent 示例](../examples/custom_agent.py)

---

## 支持

遇到问题？

- 查看 [FAQ](faq.md)
- 提交 [GitHub Issue](https://github.com/yourname/learning-assistant/issues)
- 阅读 [文档](https://learning-assistant.readthedocs.io)

---

**最后更新**: 2026-03-31
**版本**: v0.2.0