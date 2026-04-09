# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.0] - 2026-03-31

### 新增

#### Agent 集成支持
- ✅ AgentAPI 类 - 标准化程序接口
- ✅ 便捷函数 - `summarize_video()`, `list_available_skills()`, `get_recent_history()`
- ✅ Skills 文档层 - video-summary, list-skills, learning-history
- ✅ Python API - Pydantic 数据模型
- ✅ Agent 集成指南

#### 链接学习模块
- ✅ ContentFetcher - 网页抓取（aiohttp + 可选 Playwright）
- ✅ ContentParser - 内容解析（trafilatura）
- ✅ LinkLearningModule - 完整工作流
- ✅ 知识卡片生成 - 摘要、要点、标签
- ✅ 问答生成 - 基于内容的问答对
- ✅ 测验生成 - 多选题测验
- ✅ 多格式导出 - Markdown/JSON

#### CLI 命令
- ✅ `la link <url>` - 链接学习命令
- ✅ 支持参数：provider、model、output、format、no-quiz
- ✅ 进度显示和结果展示

#### Python API
- ✅ `process_link()` - 异步链接处理
- ✅ `process_link_sync()` - 同步链接处理
- ✅ LinkSummaryResult 数据模型

#### 文档
- ✅ CLI 使用指南（3000字）
- ✅ Skills 文档（3000字）
- ✅ API 文档和示例
- ✅ 集成测试指南

### 变更

- 更新 README 添加 Agent 集成和链接学习模块说明
- 更新配置文件添加链接学习模块配置
- 项目版本更新到 0.2.0

### 技术细节

- 新增 `src/learning_assistant/modules/link_learning/` 目录
- 新增 `skills/link-learning/` 目录
- 新增依赖：trafilatura、aiohttp、python-dateutil
- 添加 24 个测试用例（14 个单元测试 + 10 个集成测试）

## [0.1.0] - 2026-03-31

### 新增

#### 核心引擎
- ✅ ConfigManager - 配置管理系统
- ✅ EventBus - 事件总线
- ✅ PluginManager - 插件管理器
- ✅ HistoryManager - 历史记录管理
- ✅ TaskManager - 任务状态管理

#### LLM 服务
- ✅ LLMService - 统一 LLM 调用接口
- ✅ OpenAI 适配器
- ✅ Anthropic 适配器
- ✅ DeepSeek 适配器
- ✅ 重试机制和成本控制

#### CLI
- ✅ Typer CLI 框架
- ✅ setup 命令 - 配置向导
- ✅ version 命令 - 版本信息
- ✅ list-plugins 命令 - 插件列表

#### 视频总结模块
- ✅ VideoDownloader - yt-dlp 视频下载
  - 支持 B站、YouTube、抖音
  - 进度回调和 Cookie 配置
- ✅ AudioExtractor - FFmpeg 音频提取
  - 多格式支持（MP3/WAV/AAC）
  - 质量优化和进度监控
- ✅ AudioTranscriber - 语音转录
  - **BcutASR** 集成（免费云端服务）
  - 多格式字幕导出（SRT/VTT/LRC/ASS）
  - 词级时间戳支持
  - 缓存机制

#### Prompt 模板系统
- ✅ PromptTemplate - YAML 模板类
- ✅ PromptManager - 模板管理器
- ✅ Jinja2 变量插值
- ✅ JSON Schema 验证

#### 导出器
- ✅ BaseExporter - 导出器基类
- ✅ MarkdownExporter - Markdown 导出
- ✅ PDFExporter - PDF 导出（可选）

#### 适配器框架
- ✅ BaseAdapter - 适配器基类
  - 生命周期状态机
  - 事件订阅机制
  - 错误追踪
- ✅ TestValidationAdapter - 测试适配器
- ✅ AsyncTestAdapter - 异步测试适配器
- ✅ ErrorSimulationAdapter - 错误模拟适配器
- ✅ 飞书适配器设计文档和骨架代码

### 测试

- ✅ 432 个单元测试
- ✅ 测试覆盖率 >80%
- ✅ 所有测试通过（100% 通过率）
- ✅ Mypy 类型检查通过
- ✅ Black 代码格式化通过
- ✅ Ruff 代码质量检查通过

### 文档

- ✅ README.md - 项目概述
- ✅ 用户使用指南
- ✅ 插件开发教程
- ✅ API 文档
- ✅ FAQ 文档
- ✅ CHANGELOG.md

### 安全

- ✅ API Key 从环境变量读取
- ✅ 只使用官方 SDK
- ✅ 无第三方中间层
- ✅ 本地数据自主控制

## [未来版本]

### [0.2.0] - 计划中

#### 新增
- 🔗 链接学习模块
- 📚 单词学习模块
- 🚀 飞书适配器完整实现
- 📝 思源笔记适配器

### [0.3.0] - 计划中

#### 新增
- Obsidian 适配器
- 批量处理功能
- 学习路径推荐
- Web UI（可选）

### [1.0.0] - 长期规划

#### 新增
- 插件市场
- 社区插件支持
- 多语言界面
- 企业级功能

---

[0.1.0]: https://github.com/yourname/learning-assistant/releases/tag/v0.1.0
