# SynthesAI - Claude Code 项目指南

> **Synthesize Knowledge with AI Intelligence** - AI驱动的模块化学习助手

## 项目概述

SynthesAI 是一个模块化的 AI 学习助手，用于从多种来源合成知识：

| 功能模块 | 描述 | 入口 |
|---------|------|------|
| **Video Summary** | B站/YouTube/抖音视频总结 | `la video <url>` |
| **Link Learning** | 网页文章知识卡片生成 | `la link <url>` |
| **Vocabulary** | 单词提取+音标+Visual卡片 | `la vocab <text/url>` |

## 项目结构

```
SynthesAI/
├── src/learning_assistant/
│   ├── core/                # 核心引擎
│   │   ├── llm/             # LLM服务（OpenAI/Anthropic/DeepSeek）
│   │   ├── config_manager.py # 配置管理
│   │   ├── event_bus.py     # 事件总线
│   │   ├── prompt_manager.py # Prompt管理
│   │   ├── plugin_manager.py # 插件管理
│   │   └── exporters/       # 导出器（Markdown/PDF/Visual）
│   ├── modules/             # 学习模块
│   │   ├── video_summary/   # 视频总结模块
│   │   ├── link_learning/   # 链接学习模块
│   │   └ vocabulary/        # 词汇模块
│   ├── adapters/            # 外部适配器
│   │   └── feishu/          # 飞书知识库发布
│   ├── auth/                # 认证模块
│   │   └── providers/       # 平台认证（B站/抖音）
│   ├── api/                 # Agent API
│   │   └ agent_api.py       # 统一API入口
│   └── server/              # FastAPI服务
│       └── routes/          # HTTP路由
├── config/                  # 配置文件
│   ├── settings.yaml        # 全局配置
│   ├── settings.local.yaml  # 本地配置（敏感信息，不提交）
│   ├── modules.yaml         # 模块配置
│   └── adapters.yaml        # 适配器配置
├── templates/               # Prompt模板
│   ├── prompts/             # LLM prompt模板
│   └── outputs/             # 输出模板
├── skills/                  # Skill文档
└── tests/                   # 测试套件（652测试）
```

## 开发环境

```bash
# 安装依赖
pip install -e ".[dev,server]"

# 运行测试
pytest tests/

# 启动服务
uvicorn learning_assistant.server.main:app --reload
```

## 配置管理

### 配置优先级

1. 环境变量（最高）
2. `config/settings.local.yaml`
3. `config/settings.yaml`

### 敏感信息处理

**永远不要提交以下内容到 git：**

- `config/settings.local.yaml` - 包含 API key
- `config/cookies/*.txt` - 包含认证 cookie
- `.env` 文件

使用环境变量或 `settings.local.yaml` 存储敏感信息：

```yaml
# settings.local.yaml
llm:
  providers:
    openai:
      api_key_env: "OPENAI_API_KEY"  # 从环境变量读取
      # 或直接设置（仅本地）
      # api_key: "sk-..."  # 仅用于本地开发
```

## 核心模块使用

### LLM Service

```python
from learning_assistant.core.llm.service import LLMService

# 创建服务
service = LLMService(
    provider="openai",
    api_key="sk-...",
    model="gpt-4"
)

# 执行请求
response = service.execute(
    prompt="Summarize this content...",
    temperature=0.3
)
```

### Agent API（推荐）

```python
from learning_assistant.api.agent_api import AgentAPI

# 创建API实例
api = AgentAPI.create_with_api_key(
    provider="openai",
    api_key="sk-..."
)

# 视频总结
result = await api.summarize_video(
    url="https://www.bilibili.com/video/BV..."
)

# 链接学习
result = await api.process_link(
    url="https://example.com/article"
)

# 词汇提取
result = await api.extract_vocabulary(
    content="文本内容...",
    generate_card=True
)
```

## 模块开发

### 创建新模块

1. 在 `src/learning_assistant/modules/` 创建模块目录
2. 创建 `__init__.py` 和模块类
3. 创建 `plugin.yaml` 配置
4. 在 `config/modules.yaml` 注册

### plugin.yaml 格式

```yaml
name: my_module
type: module
version: 0.1.0
description: 模块描述
enabled: true
priority: 10

dependencies:
  - aiohttp>=3.9.0  # Python包依赖

config:
  llm:
    provider: openai
    model: gpt-4
  output:
    format: markdown
```

## Prompt 模板

Prompt模板位于 `templates/prompts/`，使用 Jinja2 格式：

```markdown
# templates/prompts/link_summary.md

## 概述
分析以下内容并生成知识摘要：

title: {{ title }}
source: {{ source }}
content: {{ content }}

## 输出格式
keyword: description
```

## 常用 CLI 命令

```bash
# 设置
la setup

# 视频总结
la video https://www.bilibili.com/video/BV...

# 链接学习
la link https://example.com/article

# 词汇提取
la vocab "文本内容..."

# B站登录
la auth login --platform bilibili

# 查看状态
la auth status --platform bilibili

# 启动服务
la server start
```

## 测试规范

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/modules/test_video_summary_module.py -v

# 运行覆盖率测试
pytest --cov=src/learning_assistant --cov-report=term-missing
```

## 飞书适配器

飞书适配器支持将内容发布到飞书知识库：

```python
from learning_assistant.adapters.feishu import FeishuAdapter

adapter = FeishuAdapter()
adapter.initialize({
    "app_id": "cli_...",
    "app_secret": "...",
    "space_id": "...",
    "root_node_token": "..."
})

# 发布文档
result = await adapter.publish(
    title="文档标题",
    content="文档内容..."
)
```

## Visual Knowledge Cards

SynthesAI 生成 Editorial 风格的视觉知识卡片：

- 宽度：1200px
- 颜色：Orange (#FF6B35) + Purple (#764BA2)
- 格式：HTML + PNG

```python
from learning_assistant.core.exporters.visual_card import VisualCardGenerator

generator = VisualCardGenerator(width=1200)
html = generator.generate_card_html(
    title="标题",
    summary="摘要",
    key_points=["要点1", "要点2"]
)

# 生成PNG（需要Playwright）
await generator.render_html_to_image(html, "output.png")
```

## 相关文档

- [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md)
- [Agent Development Guide](docs/AGENT_DEVELOPMENT_GUIDE.md)
- [API Reference](docs/api.md)
- [Skills Documentation](skills/README.md)