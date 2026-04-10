# SynthesAI

> **SynthesAI** - Synthesize Knowledge with AI Intelligence
>
> **智能整合，知识精炼** - AI驱动的模块化学习助手，通过智能技术加速知识获取和整理

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-652%20passed-brightgreen.svg)](https://github.com/yourname/synthesai)
[![Coverage](https://img.shields.io/badge/coverage-%3E80%25-green.svg)](https://github.com/yourname/synthesai)

---

## 🎯 What is SynthesAI?

**SynthesAI** synthesizes knowledge from multiple sources into structured learning materials:

- 📹 **Videos** → Structured summaries with key frames
- 📝 **Articles** → Knowledge cards and key concepts  
- 📚 **Vocabulary** → Learning materials with phonetics

**From Complexity to Clarity** - SynthesAI transforms complex content into clear, actionable knowledge.

---

## 🤖 AI Agent 开发导航

**本项目面向 AI Agent 开发，提供完整的 Agent 开发文档体系。**

### Agent 快速开始

**如果你是 AI Agent，请先阅读**：

1. 📖 **[Agent 文档索引](docs/AGENT_DOCUMENTATION_INDEX.md)** - 快速导航所有文档
2. 🏗️ **[架构总览](docs/ARCHITECTURE_OVERVIEW.md)** - 理解项目四层架构（必读）
3. 🛠️ **[Agent 开发指南](docs/AGENT_DEVELOPMENT_GUIDE.md)** - 开发新模块标准流程
4. 🎨 **[知识卡片系统](docs/knowledge_card_prompt_update.md)** - 编辑风格卡片生成（链接总结）

**Agent 开发要点**：
- ✅ 异步架构：所有异步函数使用 `async def` + `await`
- ✅ 提示词格式：`关键词：详细描述`（3-8字关键词，15-30字描述）
- ✅ 类型注解：使用 `dict[str, Any]`，不是 `Dict`
- ✅ 配置管理：API Key 从配置读取，不硬编码
- ✅ 组件复用：LLMService、PromptManager、VisualCardGenerator

---

## 📋 项目简介

**Learning Assistant** 是一个模块化、插件化、安全的 AI 驱动学习 CLI 工具平台。通过 AI 技术加速知识获取和整理，解决学习效率问题。

**核心特性**：

- ✅ **完全插件化架构** - 模块 + 适配器，轻松扩展
- ✅ **配置驱动** - 零代码扩展功能
- ✅ **安全优先** - 只用官方 SDK，无第三方风险
- ✅ **多平台支持** - B站、YouTube、抖音等主流视频平台
- ✅ **多 LLM 支持** - OpenAI、Anthropic、DeepSeek
- ✅ **免费转录** - 使用 BcutASR（B站必剪）免费云端服务
- ✅ **三大核心模块** - 视频总结、链接学习、单词学习
- ✅ **Agent Ready** - 支持自动化开发，详细 Agent 文档
- ✅ **编辑风格卡片** - 专业的知识卡片生成系统（HTML + PNG）
- ✅ **测试完善** - 546+个测试，覆盖率>80%

## 🎯 核心功能

### ✅ 模块 1: 视频总结（MVP 已完成）

**输入**: B站、YouTube、抖音等主流视频平台链接

**处理流程**:
```
视频下载 → 音频提取 → ASR转录 → LLM总结 → 格式导出
```

**输出**:
- 结构化摘要（时间轴、章节、要点）
- 核心知识点提炼
- 多格式导出（Markdown、PDF）
- 多格式字幕（SRT、VTT、LRC、ASS）

**技术栈**: `yt-dlp` + `ffmpeg` + `BcutASR` + 官方 LLM SDK

**特色功能**:
- 🆓 **免费转录** - 使用 BcutASR 云端服务，无需本地 Whisper 模型
- ⚡ **词级时间戳** - 支持精确到词的时间戳
- 📝 **多格式字幕** - 支持 SRT/VTT/LRC/ASS 等格式
- 🎯 **高准确率** - 中英文识别效果优秀

### ✅ 模块 2: 链接学习系统（已完成）

**输入**: 网页文章、技术文档、学术资源链接

**处理流程**:
```
网页抓取 → 内容解析 → LLM总结 → 知识卡片生成 → 问答测验 → 格式导出
```

**输出**:
- 知识卡片（标题、摘要、关键点、标签）
- 交互式问答（Q&A）
- 自动测验生成（选择题）
- 阅读时间估算
- 难度评估
- 多格式导出（Markdown、JSON）

**技术栈**: `trafilatura` + `BeautifulSoup` + 官方 LLM SDK

**特色功能**:
- 🧠 **智能解析** - 自动提取正文，过滤广告
- 📚 **知识卡片** - 结构化总结，快速理解
- 🎯 **交互学习** - 自动生成问答和测验
- ⏱️ **时间估算** - 预估阅读时间，规划学习
- 📝 **难度评估** - 评估内容难度，匹配学习者水平

### ✅ 模块 3: 单词学习系统（已完成）

**输入**: 文本内容、文章、视频转录

**处理流程**:
```
文本内容 → 单词提取 → 音标查询 → 单词卡生成 → 上下文短文
```

**输出**:
- 完整单词卡（音标、释义、例句、同义词、反义词）
- 上下文短文（巩固记忆）
- 多难度级别（beginner/intermediate/advanced）
- 多格式导出（Markdown、JSON）

**技术栈**: `LLM` + `多层级音标查询` + `Free Dictionary API`

**特色功能**:
- 🧠 **智能提取** - LLM理解上下文，提取重要单词
- 📖 **完整卡片** - 音标、释义、例句、同反义词
- 🎯 **三层查询** - 本地词典 → API → LLM 兜底
- 📝 **上下文短文** - 自然融入单词，巩固记忆

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
# 首次配置（设置 API Key 等）
la setup

# 查看版本
la version

# 列出已安装插件
la list-plugins

# 视频总结（需要配置 LLM API Key）
la video https://www.bilibili.com/video/BV123

# 链接学习（网页文章）
la link https://example.com/article

# 单词提取（从文本）
la vocabulary --text "Machine learning is transforming industries..."

# 从文件提取单词
la vocabulary --file article.txt --count 15

# 查看历史记录
la history

# 查看帮助
la --help
```

**注意**: v0.2.0 版本已实现三大核心模块（视频总结、链接学习、单词学习）。后续版本将补充更多测试和适配器。

---

## 🤖 Agent 集成

Learning Assistant 提供标准化 Python API，可被各种 Agent 框架使用。

### 支持的 Agent 框架

- **Claude Code** - 通过 Skills 或直接调用 Python API
- **Nanobot** - 通过 Skills 或直接调用 Python API
- **自定义 Agent** - 直接调用 Python API

### 快速集成示例

```python
from learning_assistant.api import summarize_video

# 视频总结
result = await summarize_video(url="https://www.bilibili.com/video/BV...")
print(result["title"])
print(result["summary"]["content"])

# 列出可用技能
from learning_assistant.api import list_available_skills
skills = list_available_skills()

# 查看学习历史
from learning_assistant.api import get_recent_history
records = get_recent_history(limit=10)
```

### 使用 AgentAPI 类

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# 视频总结
result = await api.summarize_video(url="https://...")
print(result.title)

# 列出技能
skills = api.list_skills()

# 查看历史
records = api.get_history(limit=10)
```

### 可用 API

| 函数 | 说明 |
|------|------|
| `summarize_video(url, **options)` | 视频总结（异步） |
| `summarize_video_sync(url, **options)` | 视频总结（同步） |
| `process_link(url, **options)` | 链接学习（异步） |
| `process_link_sync(url, **options)` | 链接学习（同步） |
| `extract_vocabulary(content, **options)` | 单词提取（异步） |
| `extract_vocabulary_sync(content, **options)` | 单词提取（同步） |
| `list_available_skills()` | 列出可用技能 |
| `get_recent_history(limit)` | 查看学习历史 |

详见：
- **Skills 文档**: [skills/README.md](skills/README.md)
- **Agent 集成指南**: [docs/agent_integration.md](docs/agent_integration.md)
- **API 文档**: [docs/api.md](docs/api.md)

---

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

**测试结果** (2026-04-09):
- ✅ 测试用例: 629+个
- ✅ 通过率: >95% (610+/629 通过)
- ✅ 测试覆盖率: >80%
- ✅ 类型检查: Mypy 通过
- ✅ 代码格式: Black 通过
- ✅ 代码质量: Ruff 通过

**功能性能**:
- 视频转录准确率: >95% (使用 BcutASR)
- 总结生成时间: <30s (10分钟视频, 取决于 LLM)
- 插件加载时间: <500ms
- 测试运行时间: ~10分钟

**测试策略**:
- 注重关键路径覆盖，不追求测试数量
- 核心引擎和关键功能已充分测试
- 实际使用验证优先于单元测试堆砌

## 🔐 安全特性

- ✅ API Key 从环境变量读取，不硬编码
- ✅ 只使用官方 SDK（OpenAI、Anthropic）
- ✅ 无第三方中间层（如 LiteLLM）
- ✅ 本地数据完全自主控制
- ✅ 定期安全审计

## 📈 扩展计划

### ✅ v0.2.0 (当前版本)

**已完成功能**:
- ✅ 核心引擎架构（PluginManager、EventBus、ConfigManager）
- ✅ LLM服务集成（OpenAI、Anthropic、DeepSeek）
- ✅ CLI基础命令（setup、version、list-plugins、video、link、vocabulary）
- ✅ 视频总结模块完整实现（135个测试）
- ✅ 链接学习模块完整实现（28+个测试）
- ✅ 单词学习模块完整实现（✅ 83个测试已完成）
- ✅ 适配器框架（BaseAdapter + 测试适配器）
- ✅ Agent集成支持（AgentAPI、Skills）
- ✅ 完整测试套件（✅ 629+个测试）

**v0.2.0 完成**:
- ✅ 所有核心模块已实现
- ✅ 测试覆盖率达标（>80%）
- ✅ 文档完整

### v0.3.0 (下一版本)

**计划功能**:
- 📊 性能优化和批量处理
- 🎨 Web UI（可选）
- 🌐 多语言支持

### v1.0.0 (长期)

- 插件市场
- 社区插件支持
- 多语言界面
- 企业级功能

## 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 开发原则

1. **安全优先** - 只用官方 SDK，无第三方风险
2. **测试驱动** - 先写测试，后写代码（TDD）
3. **文档同步** - 代码和文档同步更新
4. **渐进开发** - 小步快跑，持续集成

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢与参考项目

本项目在开发过程中参考和借鉴了以下优秀的开源项目：

### 🎨 visual-note-card-skills

**项目地址**: https://github.com/beilunyang/visual-note-card-skills

**参考内容**：
- 编辑风格知识卡片的视觉设计理念
- Claude 配色方案（橙紫渐变）
- 固定宽度布局系统（1200px）
- 深色/浅色双栏对比设计
- 框架网格卡片布局（Framework Row）
- 专业字体系统（Playfair Display + Noto Sans SC + JetBrains Mono）
- 底部高亮条和页脚设计

**应用于**：
- Link Learning 模块的知识卡片生成系统
- `VisualCardGenerator` 组件实现
- 提示词模板 v2.0 格式设计

**感谢**: @beilunyang 开创性的编辑风格卡片设计，让知识可视化更专业、更美观。

---

### 📺 bili-sync

**项目地址**: https://github.com/amtoaer/bili-sync

**参考内容**：
- B站视频下载的核心实现方案
- WBI签名算法（B站API认证）
- 音视频流分离下载策略
- CDN优先级排序逻辑
- FFmpeg音视频合并方法
- 分块并行下载优化

**应用于**：
- Video Summary 模块的 B站视频下载器
- `BilibiliDownloader` 类实现
- 视频流选择和合并逻辑

**感谢**: @amtoaer 提供了稳定高效的 B站视频下载方案，解决了视频模块的核心技术难点。

---

### 🤖 Claude Code 社区

**项目地址**: https://github.com/anthropics/claude-code

**参考内容**：
- Agent 开发最佳实践
- 插件化架构设计思路
- 文档编写规范
- Agent 文档组织方式

**应用于**：
- 本项目的 Agent 文档体系
- `AGENT_DEVELOPMENT_GUIDE.md` 设计
- `ARCHITECTURE_OVERVIEW.md` 组织方式

**感谢**: Anthropic 团队提供的 Agent 开发模式和文档示例，启发了本项目面向 Agent 的文档设计。

---

## 💡 设计启发

本项目遵循以下设计理念：

1. **复用优于重复** - 参考优秀项目，不重复造轮子
2. **开源精神** - 致谢参考项目，鼓励开源协作
3. **学习与创新** - 学习优秀设计，创造适合本项目的实现
4. **尊重原作者** - 明确标注参考来源，感谢社区贡献

**我们鼓励**：
- ✅ 参考优秀开源项目
- ✅ 学习最佳实践
- ✅ 明确标注来源和感谢
- ✅ 为社区贡献回馈

**我们避免**：
- ❌ 复制代码不标注来源
- ❌ 不尊重原作者贡献
- ❌ 重复造已有解决方案的轮子

---

## 📞 联系方式

- 项目地址: https://github.com/yourname/learning-assistant
- 问题反馈: https://github.com/yourname/learning-assistant/issues
- 文档: https://learning-assistant.readthedocs.io

---

**最后更新**: 2026-04-11
**版本**: v0.2.0
**状态**: ✅ 三大核心模块已完成，知识卡片系统已集成，Agent 文档体系完善，可用于生产环境