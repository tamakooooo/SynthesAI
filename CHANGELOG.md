# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.1] - 2026-04-24

### 修复

#### B站二维码登录
- 🔧 修复二维码登录流程：后端直接返回登录URL而非base64图像
- 🔧 修复前端二次编码导致二维码内容错误的问题
- 🔧 添加 `QRStatus.ERROR` 枚举成员，修复轮询异常

#### 视频下载稳定性
- 🔧 集成 yutto 作为 B站下载优先选择（解决CDN超时问题）
- 🔧 优化 yt-dlp 下载策略：增加超时时间、重试次数
- 🔧 修复音频流下载失败导致视频文件缺少音频的问题

### 新增

#### yutto 集成
- ✅ 自动检测 yutto CLI 可用性
- ✅ B站下载优先级：yutto CLI > yt-dlp (fallback)
- ✅ 自动从 cookie 文件提取 SESSDATA 和 bili_jct
- ✅ 支持 `--auth` 参数传递认证信息

#### Docker 优化
- ✅ Dockerfile 更新：添加 curl、ca-certificates
- ✅ 依赖验证：确保 yutto、yt-dlp 正确安装
- ✅ 创建必要目录结构

### 变更

- VideoDownloader 新增 `_download_with_yutto()` 方法
- Dockerfile 优化系统依赖安装流程
- pyproject.toml 已包含 `yutto>=2.2.0` 依赖

### 技术细节

- 修改 `src/learning_assistant/server/routes/auth.py` - 返回URL而非base64
- 修改 `src/learning_assistant/auth/models.py` - 添加 QRStatus.ERROR
- 修改 `src/learning_assistant/modules/video_summary/downloader.py` - yutto集成
- 修改 `docker/Dockerfile` - 依赖和目录优化

---

## [0.3.0] - 2026-04-11

### 新增

#### 单词学习模块 - 可视化知识卡片
- ✅ VocabularyCardGenerator - Editorial风格知识卡片生成器
- ✅ HTML模板 - vocabulary_card_template_v2.html
- ✅ PNG渲染 - Playwright高质量图片输出
- ✅ 新布局设计：
  - Hero Section（核心单词大字展示）
  - Story Section（上下文故事，英文为主+中文释义）
  - Word List Panel（左侧：10个单词+音标+词性+释义）
  - Word Focus Panel（右侧：6个重点单词详解）
  - Editorial配色（Claude橙紫色调）
- ✅ 紧凑布局优化（页面高度1250px）
- ✅ 音标显示支持（US/UK音标）

#### 单词学习模块 - 核心功能
- ✅ WordExtractor - LLM驱动的单词提取
- ✅ PhoneticLookup - 多源音标查询（本地字典+API+LLM）
- ✅ StoryGenerator - 上下文故事生成
- ✅ VocabularyCard - 完整单词卡片数据模型
- ✅ ContextStory - 故事数据模型
- ✅ 统计分析 - 难度、频率、词性分布

#### CLI命令
- ✅ `la vocab <content>` - 单词学习命令（计划中）
- ✅ 支持参数：word_count, difficulty, generate_story

### 变更

- 更新 VocabularyLearningModule 集成 VocabularyCardGenerator
- 优化卡片布局（多次迭代改进）
- 修复PNG裁剪问题
- 清理测试文件

### 技术细节

- 新增 `src/learning_assistant/modules/vocabulary/vocabulary_card_generator.py`
- 新增 `src/learning_assistant/modules/vocabulary/vocabulary_card_template_v2.html`
- 新增依赖：Playwright（可选，用于PNG渲染）
- 添加单元测试和集成测试

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

### [0.4.0] - 待发布

#### 已实现功能
- ✅ 飞书知识库发布完整实现
  - FeishuKnowledgeBaseAdapter、FeishuWikiClient、FeishuDocClient
  - 支持 video_summary、link_learning、vocabulary 三模块
- ✅ Web UI 完整实现（8个页面）
  - ConfigPage、VideoPage、LinkPage、VocabularyPage
  - HistoryPage、SettingsPage、LoginPage、StatisticsPage
- ✅ 配置系统完善（settings.yaml + settings.local.yaml）
- ✅ B站 cookie API 验证（调用 nav API 确认有效性，获取用户名）
- ✅ Web UI 飞书测试发布结果详细展示（node_token、document_id、成功/失败状态）
- ✅ 集成测试完善
  - tests/auth/test_bilibili_auth.py（10个测试）
  - tests/server/test_routes.py（8个测试）
  - tests/adapters/test_feishu_adapter.py（11个测试）

### [0.5.0] - 功能增强

#### 新增功能
- 🚀 FasterWhisperASR 本地转录引擎（离线支持）
- 🚀 更多视频平台支持（抖音、YouTube 优化）
- 🚀 知识卡片模板多样化

#### 稳定性改进
- 🔧 错误恢复机制（自动重试、降级策略）
- 🔧 下载超时处理增强
- 🔧 日志和诊断工具完善

---

[0.1.0]: https://github.com/yourname/learning-assistant/releases/tag/v0.1.0
