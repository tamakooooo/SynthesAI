# Learning Assistant

> **模块化 AI 学习助手** - 通过 AI 加速知识获取和整理

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 项目简介

**Learning Assistant** 是一个模块化、插件化、安全的 AI 驱动学习 CLI 工具平台。通过 AI 技术加速知识获取和整理，解决学习效率问题。

**核心特性**：

- ✅ **完全插件化架构** - 模块 + 适配器，轻松扩展
- ✅ **配置驱动** - 零代码扩展功能
- ✅ **安全优先** - 只用官方 SDK，无第三方风险
- ✅ **多平台集成** - 飞书、思源、Obsidian 等
- ✅ **MVP 快速验证** - 视频总结功能优先实现

## 🎯 核心功能

### 模块 1: 视频总结（MVP 优先）

**输入**: B站、YouTube、抖音等主流视频平台链接

**处理流程**:
```
视频下载 → 音频提取 → ASR转录 → LLM总结 → 格式导出
```

**输出**:
- 结构化摘要（时间轴、章节、要点）
- 核心知识点提炼
- 多格式导出（Markdown、PDF、JSON）

**技术栈**: `yt-dlp` + `ffmpeg` + `faster-whisper` + 官方 LLM SDK

### 模块 2: 链接学习系统

**输入**: 网页文章、技术文档、学术资源链接

**输出**:
- 知识卡片（标题、摘要、关键点、标签）
- 交互式问答
- 自动测验生成
- 学习路径推荐

### 模块 3: 单词学习系统

**输入**: 从链接/内容自动提取单词

**输出**:
- 单词卡（单词、音标、释义、例句、关联词汇）
- 上下文短文（巩固记忆）

## 🏗️ 系统架构

```
CLI Layer (Typer + Rich)
         ↓
Core Engine (PluginManager, EventBus, ConfigManager, LLMService)
         ↓
Module Plugins (Video Summary, Link Learning, Vocabulary)
         ↓
Adapter Plugins (Feishu, Siyuan, Obsidian)
```

详见 [ARCHITECTURE.md](ARCHITECTURE.md)

## 🚀 快速开始

### 系统要求

- Python 3.11+
- Git
- FFmpeg（视频处理）
- OpenAI/Anthropic/DeepSeek API Key

### 安装

```bash
# 克隆项目
git clone https://github.com/yourname/learning-assistant.git
cd learning-assistant

# 安装依赖（开发模式）
pip install -e ".[dev]"

# 首次配置
la setup
```

### 使用示例

```bash
# 视频总结
la video https://www.bilibili.com/video/BV123

# 链接学习
la link https://example.com/article

# 单词提取
la vocabulary https://example.com/article

# 查看历史
la history

# 列出插件
la list-plugins

# 查看版本
la version
```

## 📂 项目结构

```
learning_assistant/
├── pyproject.toml              # 项目配置
├── README.md                   # 项目说明
├── ARCHITECTURE.md             # 架构文档
├── CONTRIBUTING.md             # 贡献指南
│
├── src/learning_assistant/     # 源代码
│   ├── cli.py                  # CLI 入口
│   ├── core/                   # 核心引擎
│   │   ├── plugin_manager.py
│   │   ├── event_bus.py
│   │   ├── config_manager.py
│   │   ├── history_manager.py
│   │   ├── task_manager.py
│   │   └── llm/                # LLM 服务
│   │       ├── service.py
│   │       └── providers/
│   │           ├── openai.py
│   │           ├── anthropic.py
│   │           └── deepseek.py
│   ├── modules/                # 功能模块
│   │   ├── video_summary/
│   │   ├── link_learning/
│   │   └── vocabulary/
│   ├── adapters/               # 平台适配器
│   │   ├── feishu/
│   │   ├── siyuan/
│   │   └── obsidian/
│   └── utils/                  # 工具库
│
├── config/                     # 配置文件
│   ├── settings.yaml           # 全局设置
│   ├── modules.yaml            # 模块配置
│   └── adapters.yaml           # 适配器配置
│
├── templates/                  # 模板文件
│   ├── prompts/                # Prompt 模板
│   └── outputs/                # 输出模板
│
├── data/                       # 数据目录
│   ├── history/                # 历史记录
│   ├── cache/                  # 缓存
│   └── outputs/                # 输出文件
│
├── tests/                      # 测试
│   ├── core/
│   ├── modules/
│   └── integration/
│
└── docs/                       # 文档
```

## 🔧 配置

### 环境变量

```bash
# LLM API Keys (必须配置)
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# 可选配置
export LEARNING_ASSISTANT_LOG_LEVEL="INFO"
```

### 配置文件

所有配置文件位于 `config/` 目录，详见 [ARCHITECTURE.md](ARCHITECTURE.md) 的配置管理部分。

## 🧪 开发

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/core/test_config_manager.py

# 生成覆盖率报告
pytest --cov=learning_assistant --cov-report=html

# 类型检查
mypy src/learning_assistant

# 代码格式化
black src/learning_assistant

# Linting
ruff check src/learning_assistant
```

### 开发流程

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

## 📊 性能指标

- 视频转录准确率: >95%
- 总结生成时间: <30s (10分钟视频)
- 缓存命中率: >60%
- 测试覆盖率: >80%
- 插件加载时间: <500ms

## 🔐 安全特性

- ✅ API Key 从环境变量读取，不硬编码
- ✅ 只使用官方 SDK（OpenAI、Anthropic）
- ✅ 无第三方中间层（如 LiteLLM）
- ✅ 本地数据完全自主控制
- ✅ 定期安全审计

## 📈 扩展计划

### v0.2.0 (短期)

- 链接学习模块
- 单词学习模块
- 飞书适配器
- 思源笔记适配器

### v0.3.0 (中期)

- Obsidian 适配器
- Web UI（可选）
- 批量处理
- 学习路径推荐

### v1.0.0 (长期)

- 插件市场
- 社区插件支持
- 多语言界面

## 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 开发原则

1. **安全优先** - 只用官方 SDK，无第三方风险
2. **测试驱动** - 先写测试，后写代码（TDD）
3. **文档同步** - 代码和文档同步更新
4. **渐进开发** - 小步快跑，持续集成

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 📞 联系方式

- 项目地址: https://github.com/yourname/learning-assistant
- 问题反馈: https://github.com/yourname/learning-assistant/issues
- 文档: https://learning-assistant.readthedocs.io

---

**最后更新**: 2026-03-31
**版本**: v0.1.0 (MVP)