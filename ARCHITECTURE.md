# Learning Assistant - 技术架构文档

> **版本**: v1.0
> **最后更新**: 2026-03-31
> **状态**: 规划完成，准备实施

---

## 📋 项目概览

**项目名称**: Learning Assistant (学习助手)

**定位**: 模块化、插件化、安全的 AI 驱动学习 CLI 工具平台

**核心理念**: 通过 AI 加速知识获取和整理，解决学习效率问题

**关键特性**:
- ✅ 完全插件化架构（模块 + 适配器）
- ✅ 配置驱动，零代码扩展
- ✅ 安全优先（官方 SDK，无第三方风险）
- ✅ 多平台集成（飞书、思源、Obsidian 等）
- ✅ MVP 快速验证

---

## 🎯 核心需求

### 模块1: 视频总结 (MVP 优先)

**输入**: 主流视频平台（B站、抖音、YouTube）+ 任意链接/文件

**处理流程**:
```
视频下载 → 音频提取 → ASR转录 → LLM总结 → 格式导出
```

**输出**:
- 结构化摘要（时间轴、章节、要点）
- 核心知识点提炼
- 可视化呈现（思维导图）
- 多格式导出（Markdown、PDF、JSON）

**技术栈**:
- 视频下载: `yt-dlp`
- 音频处理: `ffmpeg`
- ASR: `faster-whisper`
- LLM: 官方 SDK（OpenAI、Anthropic）
- 导出: `jinja2` 模板

---

### 模块2: 链接学习系统

**输入**: 网页文章、技术文档、学术资源、任意链接

**处理流程**:
```
网页抓取 → 内容解析 → LLM总结 → 知识卡片生成 → 问答/测验
```

**输出**:
- 知识卡片（标题、摘要、关键点、标签）
- 交互式问答
- 自动测验生成
- 学习路径推荐

**技术栈**:
- 网页抓取: `requests` + `BeautifulSoup4`
- 动态页面: `playwright` (可选)
- 内容解析: `trafilatura` 或 `readability-lxml`

---

### 模块3: 单词学习系统

**输入**: 从链接/内容自动提取单词

**处理流程**:
```
内容分析 → 单词识别 → 单词卡生成 → 短文创作
```

**输出**:
- 单词卡（单词、音标、释义、例句、关联词汇、用法）
- 上下文短文（巩固记忆）

**技术栈**:
- 单词提取: LLM + 规则匹配
- 音标查询: 本地词典或 API
- 例句生成: LLM

---

## 🏗️ 系统架构

### 整体架构图

```
┌────────────────────────────────────────────────────┐
│                   CLI Layer                         │
│              (Typer + Rich)                         │
└────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────┐
│                Core Engine                          │
│  ┌──────────────┐  ┌──────────────┐               │
│  │PluginManager │  │ EventBus     │               │
│  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐               │
│  │ConfigManager │  │ LLMService   │               │
│  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐               │
│  │HistoryManager│  │ TaskManager  │               │
│  └──────────────┘  └──────────────┘               │
└────────────────────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐       ┌──────────────────┐
│ Module Plugins   │       │ Adapter Plugins  │
│  (BaseModule)    │       │  (BaseAdapter)   │
├──────────────────┤       ├──────────────────┤
│ - Video Summary  │       │ - Feishu         │
│ - Link Learning  │       │ - Siyuan         │
│ - Vocabulary     │       │ - Obsidian       │
│ - Custom Module  │       │ - Custom Adapter │
└──────────────────┘       └──────────────────┘
```

---

### 插件化架构

**设计原则**: 一切皆插件

**插件类型**:
1. **模块插件 (Module)**: 核心功能单元
2. **适配器插件 (Adapter)**: 平台集成单元

**插件生命周期**:
```
发现 → 加载 → 初始化 → 执行 → 清理
```

**插件发现机制**:
- 内置插件: `modules/`, `adapters/` 目录
- 第三方插件: `plugins/` 目录
- pip 包: entry_points

**配置驱动**:
```yaml
# config/modules.yaml
modules:
  video_summary:
    enabled: true
    config:
      whisper_model: "base"

# config/adapters.yaml
adapters:
  feishu:
    enabled: true
    config:
      app_id_env: "FEISHU_APP_ID"
```

---

### 核心引擎组件

#### 1. PluginManager (插件管理器)

**职责**:
- 发现和加载插件
- 管理插件生命周期
- 插件依赖管理
- 命令冲突检测

**关键方法**:
```python
discover_plugins() -> list[PluginMetadata]
load_plugin(name: str) -> BaseModule | BaseAdapter
get_plugin(name: str) -> Any
unload_plugin(name: str) -> None
```

---

#### 2. EventBus (事件总线)

**职责**:
- 模块和适配器解耦通信
- 发布-订阅模式
- 异步事件处理

**事件类型**:
```python
class EventType(Enum):
    VIDEO_DOWNLOADED = "video.downloaded"
    VIDEO_TRANSCRIBED = "video.transcribed"
    VIDEO_SUMMARIZED = "video.summarized"
    CONTENT_PUSHED = "adapter.content_pushed"
    ERROR_OCCURRED = "system.error"
```

**使用示例**:
```python
# 模块发布事件
event_bus.publish(Event(
    event_type=EventType.VIDEO_SUMMARIZED,
    source="video_summary",
    data={"output_path": "/path/to/summary.md"}
))

# 适配器订阅事件
event_bus.subscribe(
    EventType.VIDEO_SUMMARIZED,
    feishu_adapter.push_content
)
```

---

#### 3. ConfigManager (配置管理器)

**职责**:
- YAML 配置加载
- Pydantic 验证
- 环境变量覆盖
- 默认配置生成

**配置文件结构**:
```
config/
├── settings.yaml      # 全局设置
├── modules.yaml       # 模块配置
└── adapters.yaml      # 适配器配置
```

---

#### 4. LLMService (LLM 服务)

**职责**:
- 统一的 LLM 调用接口
- 多提供商支持
- 使用统计和成本控制
- 重试机制

**技术方案**: 官方 SDK + 最小适配层

**支持的提供商**:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- DeepSeek (deepseek-chat, deepseek-coder)
- 智谱 (GLM-4, GLM-4-Flash)

**实现代码**: 约 130 行，极简透明

**安全特性**:
- ✅ 直接使用官方 SDK
- ✅ 无第三方中间层
- ✅ 完全自主控制

---

#### 5. HistoryManager (历史管理器) - **新增**

**职责**:
- 学习历史持久化
- 避免重复处理
- 搜索和检索
- 学习统计

**数据存储结构**:
```
data/
├── history/
│   ├── videos.json      # 视频处理历史
│   ├── links.json       # 链接处理历史
│   └── vocabulary.json  # 单词卡历史
├── cache/
│   ├── downloads/       # 下载缓存
│   ├── transcripts/     # 转录结果缓存
│   └── summaries/       # 总结结果缓存
└── outputs/
    ├── summaries/       # 输出文件
    └── vocabulary/      # 单词卡文件
```

**关键方法**:
```python
add_record(module: str, input: str, output: str) -> None
check_duplicate(module: str, input: str) -> bool
search(keyword: str) -> list[dict]
get_statistics() -> dict
```

---

#### 6. TaskManager (任务管理器) - **新增**

**职责**:
- 异步任务状态管理
- 任务持久化
- 错误恢复机制
- 进度跟踪

**任务状态**:
```python
class TaskState:
    task_id: str
    module: str
    status: str  # pending, running, completed, interrupted, failed
    progress: float
    current_step: str
    created_at: float
    updated_at: float
    error: str | None
```

**错误恢复示例**:
```python
# 处理中断后保存状态
task_manager.mark_interrupted(task_id)
console.print("Task interrupted. Resume with: la resume <task_id>")

# 恢复任务
la resume abc123
# 从上次中断的步骤继续
```

---

### 模块和适配器接口

#### BaseModule (模块基类)

```python
class BaseModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """模块名称"""

    @abstractmethod
    def initialize(self, config: dict, event_bus: EventBus) -> None:
        """初始化模块"""

    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        """执行模块核心功能"""

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""

    def register_cli_commands(self, cli_group) -> None:
        """注册CLI命令（可选）"""
        pass
```

---

#### BaseAdapter (适配器基类)

```python
class BaseAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """适配器名称"""

    @abstractmethod
    def initialize(self, config: dict, event_bus: EventBus) -> None:
        """初始化适配器"""

    @abstractmethod
    def push_content(self, content: dict) -> bool:
        """推送内容到平台"""

    @abstractmethod
    def sync_data(self, data_type: str, data: dict) -> bool:
        """同步数据"""

    @abstractmethod
    def handle_trigger(self, trigger_data: dict) -> dict:
        """处理触发事件"""

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
```

---

## 🛠️ 技术选型

### 核心框架

| 组件 | 选择 | 版本 | 理由 |
|------|------|------|------|
| CLI 框架 | **Typer** | ≥0.9.0 | 类型提示驱动，现代 CLI，Rich 集成 |
| 配置管理 | **PyYAML + Pydantic** | ≥6.0, ≥2.0 | 验证 + 类型安全 |
| 插件加载 | **importlib + entry_points** | 标准库 | 完全控制，轻量 |
| 日志 | **loguru** | ≥0.7.0 | 简单易用，功能强大 |

---

### 视频处理

| 组件 | 选择 | 版本 | 理由 |
|------|------|------|------|
| 视频下载 | **yt-dlp** | 最新 | 支持所有主流平台 |
| 音频处理 | **ffmpeg** | 系统依赖 | 工业标准 |
| ASR | **faster-whisper** | ≥0.10.0 | 速度快 5-10 倍，免费 |

---

### LLM 集成

| 组件 | 选择 | 版本 | 理由 |
|------|------|------|------|
| OpenAI | **openai** | ≥1.0.0 | 官方 SDK |
| Anthropic | **anthropic** | ≥0.18.0 | 官方 SDK |
| 统一接口 | **自定义** | - | 130 行代码，完全控制 |

**不使用**: ~~LiteLLM~~ (投毒风险)

---

### 网页处理

| 组件 | 选择 | 版本 | 理由 |
|------|------|------|------|
| HTTP 请求 | **requests** | ≥2.31.0 | 简单可靠 |
| HTML 解析 | **beautifulsoup4** | ≥4.12.0 | 强大的解析能力 |
| 内容提取 | **trafilatura** | ≥1.6.0 | 专注于正文提取 |
| 动态页面 | **playwright** | ≥1.40.0 (可选) | 处理 JavaScript 渲染 |

---

### 数据处理

| 组件 | 选择 | 版本 | 理由 |
|------|------|------|------|
| 模板引擎 | **jinja2** | ≥3.1.0 | 灵活的输出格式 |
| JSON 处理 | **orjson** | ≥3.9.0 | 快速 JSON 序列化 |
| 文件监听 | **watchdog** | ≥3.0.0 (可选) | 文件变化监听 |

---

### 测试和质量

| 组件 | 选择 | 版本 | 理由 |
|------|------|------|------|
| 测试框架 | **pytest** | ≥7.4.0 | 标准 Python 测试 |
| 异步测试 | **pytest-asyncio** | ≥0.21.0 | 异步支持 |
| 覆盖率 | **pytest-cov** | ≥4.1.0 | 覆盖率报告 |
| 代码格式化 | **black** | ≥23.0.0 | 统一代码风格 |
| Linting | **ruff** | ≥0.1.0 | 快速全面 |
| 类型检查 | **mypy** | ≥1.5.0 | 静态类型检查 |

---

## 📅 实施计划

### 阶段划分

**阶段 1 (Week 1-2)**: 核心引擎骨架
**阶段 2 (Week 3-4)**: 视频总结完整实现
**阶段 3 (Week 5-6)**: 适配器框架 + 测试完善

---

### Week 1: 核心引擎 (第 1-7 天)

#### Day 1-2: 项目初始化

**任务**:
- [x] 创建项目结构
- [x] 配置 `pyproject.toml`
- [x] 设置开发工具 (black, ruff, mypy)
- [x] 创建配置文件骨架

**交付物**:
```
learning_assistant/
├── pyproject.toml          ✅
├── .gitignore              ✅
├── README.md               ✅
├── src/learning_assistant/
│   ├── __init__.py         ✅
│   ├── core/               ✅
│   ├── modules/            ✅
│   ├── adapters/           ✅
│   └── cli.py              ✅
├── config/
│   ├── settings.yaml       ✅
│   ├── modules.yaml        ✅
│   └── adapters.yaml       ✅
└── tests/                  ✅
```

---

#### Day 3-4: ConfigManager 实现

**任务**:
- [ ] YAML 配置加载
- [ ] Pydantic 验证模型
- [ ] 环境变量覆盖
- [ ] 默认配置生成
- [ ] 单元测试

**关键代码**:
```python
# src/learning_assistant/core/config_manager.py
class ConfigManager:
    def load_all(self) -> None: ...
    def get_llm_config(self) -> dict: ...
    def get_plugin_config(self, name: str) -> dict: ...
```

---

#### Day 5: EventBus 实现

**任务**:
- [ ] 事件类型定义
- [ ] 订阅/发布机制
- [ ] 异步事件支持
- [ ] 单元测试

**关键代码**:
```python
# src/learning_assistant/core/event_bus.py
class EventBus:
    def subscribe(self, event_type: EventType, handler: Callable) -> None: ...
    def publish(self, event: Event) -> None: ...
    async def publish_async(self, event: Event) -> None: ...
```

---

#### Day 6-7: PluginManager 实现

**任务**:
- [ ] 目录扫描发现插件
- [ ] importlib 动态加载
- [ ] 生命周期管理
- [ ] 依赖检查
- [ ] 单元测试

**关键代码**:
```python
# src/learning_assistant/core/plugin_manager.py
class PluginManager:
    def discover_plugins(self) -> list[PluginMetadata]: ...
    def load_plugin(self, name: str) -> BaseModule | BaseAdapter: ...
    def unload_plugin(self, name: str) -> None: ...
```

---

### Week 2: LLM服务 + CLI基础

#### Day 1-3: LLMService 实现

**任务**:
- [ ] BaseLLMProvider 基类
- [ ] OpenAI 适配器
- [ ] Anthropic 适配器
- [ ] DeepSeek 适配器
- [ ] 统一 LLMService
- [ ] 单元测试

**关键文件**:
```
src/learning_assistant/core/llm/
├── base.py              # 基类定义
├── service.py           # 统一服务
└── providers/
    ├── openai.py        # OpenAI 适配器
    ├── anthropic.py     # Anthropic 适配器
    └── deepseek.py      # DeepSeek 适配器
```

---

#### Day 4-5: CLI 入口

**任务**:
- [ ] Typer 命令定义
- [ ] 插件命令动态注册
- [ ] Rich 输出集成
- [ ] setup 引导命令
- [ ] 测试 CLI

**关键代码**:
```python
# src/learning_assistant/cli.py
@app.command()
def video(url: str, output_format: str = "markdown"): ...

@app.command()
def setup(): ...

@app.command()
def list_plugins(): ...
```

---

#### Day 6-7: HistoryManager + TaskManager

**任务**:
- [ ] 历史记录持久化
- [ ] 缓存机制
- [ ] 任务状态管理
- [ ] 错误恢复机制
- [ ] 单元测试

**关键代码**:
```python
# src/learning_assistant/core/history_manager.py
class HistoryManager:
    def add_record(self, module: str, input: str, output: str) -> None: ...
    def check_duplicate(self, module: str, input: str) -> bool: ...

# src/learning_assistant/core/task_manager.py
class TaskManager:
    def create_task(self, module: str, input: dict) -> str: ...
    def update_progress(self, task_id: str, step: str, progress: float) -> None: ...
    def resume_task(self, task_id: str) -> None: ...
```

---

### Week 3: 视频下载 + ASR转录

#### Day 1-3: 视频下载器

**任务**:
- [ ] yt-dlp 集成
- [ ] 多平台支持测试 (B站、YouTube、抖音)
- [ ] 进度回调
- [ ] 错误处理
- [ ] Cookie 配置

**关键代码**:
```python
# src/learning_assistant/modules/video_summary/downloader.py
class VideoDownloader:
    def download(self, url: str, output_path: Path) -> Path: ...
    def get_video_info(self, url: str) -> dict: ...
```

---

#### Day 4-5: 音频提取

**任务**:
- [ ] FFmpeg 音频提取
- [ ] 格式转换
- [ ] 音频质量优化
- [ ] 测试

---

#### Day 6-7: Whisper 转录

**任务**:
- [ ] faster-whisper 集成
- [ ] 进度回调
- [ ] 字幕格式化
- [ ] 模型下载管理
- [ ] 测试

**关键代码**:
```python
# src/learning_assistant/modules/video_summary/transcriber.py
class AudioTranscriber:
    def transcribe(self, audio_path: Path) -> list[dict]: ...
```

---

### Week 4: LLM总结 + 导出

#### Day 1-3: Prompt 模板系统

**任务**:
- [ ] Prompt 模板设计
- [ ] 结构化输出
- [ ] JSON 解析验证
- [ ] 多语言支持
- [ ] 测试

**关键文件**:
```
templates/prompts/
├── video_summary.yaml      # 视频总结 prompt
├── link_summary.yaml       # 链接总结 prompt
└── vocabulary_extract.yaml # 单词提取 prompt
```

---

#### Day 4-5: 导出器

**任务**:
- [ ] Jinja2 模板
- [ ] Markdown 输出
- [ ] PDF 转换 (可选)
- [ ] 多格式支持
- [ ] 测试

**关键代码**:
```python
# src/learning_assistant/modules/video_summary/exporter.py
class Exporter:
    def export_markdown(self, summary: dict, template: str) -> Path: ...
    def export_pdf(self, markdown_path: Path) -> Path: ...
```

---

#### Day 6-7: 模块集成和完整测试

**任务**:
- [ ] 组合所有组件
- [ ] 端到端测试
- [ ] CLI 命令实现
- [ ] 文档编写
- [ ] MVP 发布准备

---

### Week 5: 适配器框架

#### Day 1-2: BaseAdapter 完善

**任务**:
- [ ] 抽象接口细化
- [ ] 事件订阅机制
- [ ] 测试框架

---

#### Day 3-5: Mock 适配器

**任务**:
- [ ] 创建测试适配器
- [ ] 验证事件总线
- [ ] 集成测试

---

#### Day 6-7: 飞书适配器准备

**任务**:
- [ ] 研究飞书 API
- [ ] 设计集成方案
- [ ] 创建骨架

---

### Week 6: 测试和文档

#### Day 1-3: 全面测试

**任务**:
- [ ] 单元测试覆盖率 >80%
- [ ] 集成测试
- [ ] 端到端测试
- [ ] 性能测试

---

#### Day 4-5: 文档编写

**任务**:
- [ ] README 完整文档
- [ ] ARCHITECTURE.md
- [ ] CONTRIBUTING.md
- [ ] 插件开发指南
- [ ] FAQ

---

#### Day 6-7: MVP 发布

**任务**:
- [ ] 打包发布 (pip)
- [ ] 示例演示
- [ ] Bug 修复
- [ ] 收集反馈

---

## 🔧 关键实现细节

### 数据存储设计

#### 历史记录结构

```json
// data/history/videos.json
{
  "records": [
    {
      "id": "abc123",
      "module": "video_summary",
      "input": "https://bilibili.com/video/BV123",
      "output": "/data/outputs/summaries/video_20260331.md",
      "timestamp": "2026-03-31T10:30:00Z",
      "metadata": {
        "title": "视频标题",
        "duration": 1800,
        "platform": "bilibili"
      }
    }
  ]
}
```

---

#### 缓存策略

```python
class CacheManager:
    def get_transcript_cache(self, video_id: str) -> dict | None:
        """获取转录缓存（7天有效期）"""
        cache_file = Path(f"data/cache/transcripts/{video_id}.json")
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < 7 * 24 * 3600:  # 7天
                return json.load(cache_file.open())
        return None
```

---

### Prompt 模板设计

#### 视频总结 Prompt

```yaml
# templates/prompts/video_summary.yaml
system_prompt: |
  You are a learning assistant. Analyze video transcripts and create structured summaries.

user_prompt: |
  Analyze the following video transcript and provide:

  1. **Core Theme**: One sentence describing the main topic
  2. **Chapters**: Timeline breakdown with titles
  3. **Key Points**: 5-10 bullet points of essential knowledge
  4. **Knowledge Map**: Important concepts and relationships
  5. **Learning Suggestions**: Recommended further reading/practice

  Transcript:
  {transcript}

  Output format: JSON with keys: theme, chapters, key_points, knowledge_map, suggestions
```

---

### 任务状态管理

#### 任务生命周期

```
pending → running → completed
                ↓
            interrupted → resumed → completed
                ↓
              failed
```

#### 错误恢复机制

```python
# 处理中断
try:
    # Step 1: Download
    task_manager.update_progress(task_id, "downloading", 10)
    video_path = downloader.download(url)

    # Step 2: Transcribe
    task_manager.update_progress(task_id, "transcribing", 40)
    transcript = transcriber.transcribe(video_path)

    # Step 3: Summarize
    task_manager.update_progress(task_id, "summarizing", 70)
    summary = llm.call(prompt)

    task_manager.update_progress(task_id, "completed", 100)

except NetworkError:
    task_manager.mark_interrupted(task_id)
    console.print(f"[red]Network error. Resume with: la resume {task_id}[/red]")
```

---

## 📦 项目结构

```
learning_assistant/
├── pyproject.toml              # 项目配置
├── README.md                   # 项目说明
├── ARCHITECTURE.md             # 架构文档
├── CONTRIBUTING.md             # 贡献指南
│
├── src/learning_assistant/     # 源代码
│   ├── __init__.py
│   ├── cli.py                  # CLI 入口
│   │
│   ├── core/                   # 核心引擎
│   │   ├── plugin_manager.py
│   │   ├── event_bus.py
│   │   ├── config_manager.py
│   │   ├── history_manager.py  # 新增
│   │   ├── task_manager.py     # 新增
│   │   ├── base_module.py
│   │   ├── base_adapter.py
│   │   └── llm/                # LLM 服务
│   │       ├── base.py
│   │       ├── service.py
│   │       └── providers/
│   │           ├── openai.py
│   │           ├── anthropic.py
│   │           └── deepseek.py
│   │
│   ├── modules/                # 功能模块
│   │   ├── video_summary/
│   │   │   ├── plugin.yaml
│   │   │   ├── module.py
│   │   │   ├── downloader.py
│   │   │   ├── transcriber.py
│   │   │   ├── summarizer.py
│   │   │   └── exporter.py
│   │   ├── link_learning/
│   │   └── vocabulary/
│   │
│   ├── adapters/               # 平台适配器
│   │   ├── feishu/
│   │   ├── siyuan/
│   │   └── obsidian/
│   │
│   └── utils/                  # 工具库
│       ├── downloader.py       # 通用下载器
│       ├── scraper.py          # 网页抓取
│       └── exporter.py         # 导出工具
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
│   ├── conftest.py
│   ├── core/
│   ├── modules/
│   └── integration/
│
└── docs/                       # 文档
    ├── user_guide.md
    ├── plugin_development.md
    └── api_reference.md
```

---

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourname/learning-assistant.git
cd learning-assistant

# 安装依赖
pip install -e .

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
```

---

## 📊 性能指标

### 目标

- 视频转录准确率: >95%
- 总结生成时间: <30s (10分钟视频)
- 缓存命中率: >60%
- 测试覆盖率: >80%
- 插件加载时间: <500ms

---

## 🔐 安全考虑

### 数据安全

- ✅ API Key 从环境变量读取，不硬编码
- ✅ 本地数据加密存储（可选）
- ✅ 无第三方数据上传
- ✅ 完全本地运行

### 依赖安全

- ✅ 只使用官方 SDK
- ✅ 定期安全审计
- ✅ 最小依赖原则
- ✅ 依赖锁定 (uv.lock)

---

## 📈 扩展计划

### 短期 (v0.2.0)

- [ ] 链接学习模块
- [ ] 单词学习模块
- [ ] 飞书适配器
- [ ] 思源笔记适配器

### 中期 (v0.3.0)

- [ ] Obsidian 适配器
- [ ] Web UI (可选)
- [ ] 批量处理
- [ ] 学习路径推荐

### 长期 (v1.0.0)

- [ ] 插件市场
- [ ] 社区插件支持
- [ ] 多语言界面
- [ ] 移动端支持 (可选)

---

## 🤝 贡献指南

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

- 使用 black 格式化
- 使用 ruff 检查
- 使用 mypy 类型检查
- 测试覆盖率 >80%
- 遵循 Conventional Commits

---

## 📝 更新日志

### v0.1.0 (2026-03-31)

- ✅ 核心引擎实现
- ✅ 视频总结模块 MVP
- ✅ 官方 SDK LLM 集成
- ✅ 插件化架构
- ✅ 基础 CLI 功能

---

## 📄 许可证

MIT License

---

## 📞 联系方式

- 项目地址: https://github.com/yourname/learning-assistant
- 问题反馈: https://github.com/yourname/learning-assistant/issues
- 文档: https://learning-assistant.readthedocs.io

---

**最后更新**: 2026-03-31
**维护者**: Your Name