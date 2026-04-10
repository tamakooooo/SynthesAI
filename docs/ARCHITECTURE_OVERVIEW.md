# SynthesAI - 项目架构总览

> **AI Agent 快速理解项目架构和设计模式的参考文档**

## 项目定位

**SynthesAI** - Synthesize Knowledge with AI Intelligence

- 🎯 **目标用户**：学习者、知识管理者、研究者
- 🚀 **核心价值**：将复杂内容转化为清晰知识（From Complexity to Clarity）
- 🤖 **AI Ready**：支持 Agent 自动化开发和扩展
- 📦 **插件化**：易于添加新学习场景
- 🔬 **知识综合**：视频、文章、单词 → 结构化学习材料

---

## 架构设计理念

### 设计原则

1. **模块化（Modularity）**
   - 每个学习场景独立模块
   - 插件化架构，动态加载
   - 模块间解耦，独立开发

2. **可扩展（Extensibility）**
   - Agent 可轻松添加新模块
   - 组件复用（LLM、Exporter、Auth）
   - 配置驱动，灵活调整

3. **异步优先（Async-First）**
   - 全异步架构
   - 支持并发处理
   - I/O 高效

4. **事件驱动（Event-Driven）**
   - EventBus 统一通信
   - 模块间松耦合
   - 便于监控和调试

5. **Agent-Friendly**
   - 清晰的接口定义
   - 详细的文档和示例
   - 遵循设计模式

---

## 四层架构详解

```
┌──────────────────────────────────────────────────────┐
│  Layer 1: CLI Interface (User Interaction)           │
│  - typer: 命令行框架                                  │
│  - rich: 富文本 UI                                    │
│  - 命令路由：link/video/vocabulary                    │
└──────────────────────────────────────────────────────┘
                         ↓ calls
┌──────────────────────────────────────────────────────┐
│  Layer 2: Plugin Management (Core Framework)         │
│  - PluginManager: 动态加载模块                        │
│  - EventBus: 模块间通信                               │
│  - Dependency Resolution: 自动依赖管理                │
└──────────────────────────────────────────────────────┘
                         ↓ loads
┌──────────────────────────────────────────────────────┐
│  Layer 3: Learning Modules (Feature Layer)           │
│  - LinkLearningModule: 网页内容总结                   │
│  - VideoSummaryModule: 视频内容总结                   │
│  - VocabularyModule: 词汇学习                         │
│  - [Future Modules]: Agent 可扩展                    │
└──────────────────────────────────────────────────────┘
                         ↓ uses
┌──────────────────────────────────────────────────────┐
│  Layer 4: Core Services (Foundation Layer)           │
│  - LLM Service: AI 能力（OpenAI/Claude/...）          │
│  - Exporters: 输出格式化（MD/HTML/PNG）                │
│  - Auth Manager: 认证（Bilibili/Douyin/...）          │
│  - History Manager: 历史记录                          │
│  - Prompt Manager: 提示词管理                         │
└──────────────────────────────────────────────────────┘
```

---

## Layer 1: CLI Interface

### 功能职责
- 用户命令解析
- 参数验证和转换
- 结果展示（Rich UI）
- 错误提示和帮助

### 核心文件
- `src/learning_assistant/cli.py` - CLI 入口

### Agent 开发指南
添加新命令的标准流程：
```python
# 1. 在 cli.py 中定义命令
@app.command("new_module")
def new_module_command(input_data: str, options: dict = None):
    """新模块命令"""
    # 2. 加载模块
    module = plugin_manager.get_plugin("new_module")

    # 3. 执行处理
    result = module.execute({"input": input_data, **options})

    # 4. 展示结果
    console.print(f"[green]✓ 处理完成[/green]")
    display_result(result)  # 使用 Rich 展示
```

---

## Layer 2: Plugin Management

### 功能职责
- 插件发现和加载
- 依赖检查和解决
- 模块初始化管理
- 生命周期管理

### 核心组件

#### PluginManager
**位置**：`src/learning_assistant/core/plugin_manager.py`

**功能**：
- 自动扫描 `modules/` 和 `adapters/` 目录
- 读取 `plugin.yaml` 配置
- 检查依赖（Python 包）
- 动态加载模块类

**Agent 使用**：
```python
# 加载所有插件
plugin_manager.discover_plugins()

# 加载特定插件
plugin_manager.load_plugin("link_learning")

# 初始化插件
plugin_manager.initialize_all(config_manager)

# 获取插件实例
module = plugin_manager.get_plugin("link_learning")
```

#### EventBus
**位置**：`src/learning_assistant/core/event_bus.py`

**功能**：
- 模块间通信
- 事件订阅和发布
- 历史记录追踪

**Agent 使用**：
```python
# 发布事件
event_bus.emit("link.processed", data={"url": "...", "result": "..."})

# 订阅事件
event_bus.on("video.downloaded", handler=on_video_downloaded)

# 查询历史
history = event_bus.get_history(event_type="link.processed")
```

---

## Layer 3: Learning Modules

### 模块接口（BaseModule）

**位置**：`src/learning_assistant/core/base_module.py`

**接口定义**：
```python
class BaseModule(ABC):
    """所有学习模块的基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """模块名称"""
        pass

    @abstractmethod
    def initialize(self, config: dict, event_bus: EventBus) -> None:
        """初始化模块"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass

    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        """执行模块任务（同步包装）"""
        pass
```

### 现有模块

#### 1. LinkLearningModule（链接总结）

**位置**：`src/learning_assistant/modules/link_learning/`

**功能**：
- 抓取网页内容
- 提取关键信息
- 生成知识卡片（编辑风格）
- 导出 Markdown + HTML + PNG

**Agent 可扩展点**：
- 新增导出格式（PDF、Anki）
- 新增内容解析器（PDF、DOCX）
- 新增知识卡片样式

#### 2. VideoSummaryModule（视频总结）

**位置**：`src/learning_assistant/modules/video_summary/`

**功能**：
- 下载视频（B站、YouTube）
- 提取音频并转录
- 生成章节总结
- 导出 Markdown

**Agent 可扩展点**：
- 新增视频源（抖音、快手）
- 新增转录服务（Whisper API）
- 新增章节截图功能
- 新增视频知识卡片

#### 3. VocabularyModule（词汇学习）

**位置**：`src/learning_assistant/modules/vocabulary/`

**功能**：
- 从文本提取词汇
- 查询词义和发音
- 生成记忆故事
- 导出词汇卡片

**Agent 可扩展点**：
- 新增词汇源（文献、论文）
- 新增记忆算法
- 新增词汇卡片样式
- Anki 导出支持

---

## Layer 4: Core Services

### 1. LLM Service

**位置**：`src/learning_assistant/core/llm/`

**架构**：
```
LLMService (统一接口)
    ↓
BaseLLMProvider (抽象基类)
    ↓
OpenAIProvider / AnthropicProvider / CustomProvider
```

**Agent 使用**：
```python
# 初始化（配置驱动）
llm_config = config_manager.get_llm_config("openai")
llm_service = LLMService(
    provider="openai",
    api_key=llm_config["api_key"],
    model="gpt-4",
    base_url=llm_config.get("base_url"),
)

# 调用（异步包装）
response = await asyncio.to_thread(
    llm_service.call,
    prompt="Your prompt",
    temperature=0.3,
)
```

**Agent 可扩展点**：
- 新增 Provider（Anthropic Claude、Google Gemini）
- 新增模型配置
- 新增调用策略（批处理、重试）

### 2. Prompt Manager

**位置**：`src/learning_assistant/core/prompt_manager.py`

**功能**：
- YAML 模板管理
- Jinja2 变量渲染
- JSON Schema 验证
- LLM 输出解析

**Agent 使用**：
```python
# 加载模板
template = prompt_manager.load_template("link_summary")

# 渲染（填充变量）
system_prompt, user_prompt = template.render({
    "title": "GitHub Repo",
    "content": "...",
})

# 自动解析 LLM 返回的 JSON
result = template.parse_llm_response(response.content)
```

**Agent 开发模板**：
创建 `templates/prompts/new_template.yaml`：
```yaml
name: new_template
version: 1.0
language: zh
description: Agent 创建的新提示词模板

template: |
  你是一位专业的助手。请分析：

  ## 输入
  {{ input }}

  ## 输出格式（JSON）
  ```json
  {
    "result": "分析结果"
  }
  ```

variables:
  - name: input
    type: string
    required: true

output_format: json
json_schema:
  type: object
  properties:
    result: {type: string}
```

### 3. Exporters（导出器）

**位置**：`src/learning_assistant/core/exporters/`

**现有导出器**：
- `MarkdownExporter` - Markdown 文档导出
- `VisualCardGenerator` - 编辑风格知识卡片（HTML + PNG）

**Agent 使用**：
```python
# Markdown 导出
exporter = MarkdownExporter(
    template_dir=Path("templates/outputs"),
    template_name="link_summary.md",
)
exporter.export(data=result_data, output_path=Path("output.md"))

# 知识卡片导出
generator = VisualCardGenerator(width=1200)
await generator.render_html_to_image(
    html_content=html,
    output_path=Path("card.png"),
    scale=2.0,
)
```

**Agent 可扩展点**：
- 新增 PDFExporter（PDF 生成）
- 新增 AnkiExporter（Anki 卡片）
- 新增 MindMapExporter（思维导图）

### 4. Auth Manager

**位置**：`src/learning_assistant/auth/`

**架构**：
```
AuthManager (统一认证管理)
    ↓
BaseAuthProvider (抽象基类)
    ↓
BilibiliAuthProvider / DouyinAuthProvider / CustomProvider
```

**Agent 使用**：
```python
# 认证（自动扫码）
auth_manager = AuthManager()
await auth_manager.login("bilibili")

# 使用 cookies
cookies = auth_manager.get_cookies("bilibili")
```

**Agent 可扩展点**：
- 新增 YouTubeAuthProvider
- 新增 TwitterAuthProvider
- 新增 OAuth 认证支持

### 5. History Manager

**位置**：`src/learning_assistant/core/history_manager.py`

**功能**：
- 处理历史记录
- JSON 存储和检索
- 支持查询和过滤

**Agent 使用**：
```python
history_manager = HistoryManager(
    history_dir=Path("data/history/link"),
)

# 添加记录
history_manager.add_record(
    module="link_learning",
    input="https://github.com/...",
    output="data/outputs/link/result.md",
    metadata={"title": "...", "word_count": 500},
)

# 查询历史
records = history_manager.get_records(module="link_learning")
```

---

## 配置系统

### 配置层次

```
config/
├── settings.yaml          # 全局设置（LLM、Auth、Logging）
├── settings.local.yaml    # 本地覆盖（API Keys）
├── modules.yaml           # 模块配置（每个模块的参数）
└── adapters.yaml          # 适配器配置
```

### ConfigManager

**位置**：`src/learning_assistant/core/config_manager.py`

**Agent 使用**：
```python
# 加载所有配置
config_manager = ConfigManager()
config_manager.load_all()

# 获取全局设置
settings = config_manager.get_settings()

# 获取模块配置
module_config = config_manager.get_module_config("link_learning")

# 获取 LLM 配置
llm_config = config_manager.get_llm_config("openai")

# 验证配置
config_manager.validate_config(schema, config)
```

---

## 数据流示例

### 链接总结完整流程

```
用户输入: la link https://github.com/example/repo
    ↓
CLI Layer: 解析命令和参数
    ↓
PluginManager: 加载 LinkLearningModule
    ↓
LinkLearningModule.process()
    ↓
    Step 1: ContentFetcher.fetch(url) → HTML
    ↓
    Step 2: ContentParser.parse(html) → {title, content, word_count}
    ↓
    Step 3: PromptManager.render(template, data) → prompt
    ↓
    Step 4: LLMService.call(prompt) → JSON response
    ↓
    Step 5: Parse JSON → KnowledgeCard
    ↓
    Step 6: MarkdownExporter.export() → .md
    ↓
    Step 7: VisualCardGenerator.render() → .html + .png
    ↓
    Step 8: HistoryManager.add_record() → history.json
    ↓
返回结果给用户
```

---

## 插件系统详解

### plugin.yaml 结构

```yaml
name: link_learning              # 插件名称（唯一）
type: module                     # 类型：module/adapter
version: 1.0.0                   # 版本号
description: 网页内容总结模块     # 描述

dependencies:                    # Python 包依赖
  - trafilatura>=1.6.0
  - aiohttp>=3.9.0

entry_point: learning_assistant.modules.link_learning:LinkLearningModule

commands:                        # CLI 命令定义
  - name: link
    description: 处理网页链接
    example: "la link https://github.com/example"
```

### 插件生命周期

```
1. Discover → 扫描 plugin.yaml
2. Load → 检查依赖，加载模块类
3. Initialize → 初始化组件（LLM、Exporter、...）
4. Ready → 等待调用
5. Execute → 处理任务
6. Cleanup → 清理资源
```

---

## Agent 开发模式

### Pattern 1: 创建新模块

**步骤**：
1. 创建目录 `src/learning_assistant/modules/new_module/`
2. 实现 `BaseModule` 接口
3. 创建 `plugin.yaml`
4. 创建 Prompt Template `templates/prompts/new_module.yaml`
5. 创建 Output Template `templates/outputs/new_module.md`
6. 配置 `config/modules.yaml`
7. 添加 CLI 命令
8. 测试

### Pattern 2: 扩展现有模块

**步骤**：
1. 识别扩展点（如导出器）
2. 创建新组件（如 PDFExporter）
3. 在模块中集成
4. 更新配置
5. 测试
6. 文档

### Pattern 3: 创建新 Provider

**步骤**：
1. 继承 BaseLLMProvider 或 BaseAuthProvider
2. 实现接口方法
3. 注册到 Provider Manager
4. 配置 API Key
5. 测试
6. 文档

### Pattern 4: 优化 Prompt

**步骤**：
1. 分析现有输出质量
2. 设计新的 Prompt Template
3. 添加格式验证（JSON Schema）
4. 测试新模板
5. 对比效果
6. 更新文档

---

## 关键设计决策

### 1. 为什么使用异步架构？
- ✅ I/O 操作多（网络请求、文件读写）
- ✅ 支持并发处理（批量任务）
- ✅ 提升性能和响应速度

### 2. 为什么使用 EventBus？
- ✅ 模块间解耦
- ✅ 易于监控和调试
- ✅ 支持扩展（订阅事件）

### 3. 为什么使用 PluginManager？
- ✅ 动态加载模块
- ✅ 依赖自动解决
- ✅ 易于扩展新模块

### 4. 为什么使用 ConfigManager？
- ✅ 集中配置管理
- ✅ 支持环境覆盖
- ✅ Schema 验证

### 5. 为什么分离 Prompt Template？
- ✅ 易于调整和优化
- ✅ 支持多语言
- ✅ 便于测试和版本管理

---

## Agent 开发注意事项

### ⚠️ 异步编程
- 必须使用 `async def` 和 `await`
- 不能在 async 函数中使用 `asyncio.run()`
- 使用 `asyncio.to_thread()` 包装同步调用

### ⚠️ 类型注解
- 使用 `dict[str, Any]` 而不是 `Dict`
- 使用 `Path` 对象，不是字符串
- 使用 `list[str]` 而不是 `List`

### ⚠️ 配置管理
- API Key 必须从配置或环境变量读取
- 不要硬编码任何配置
- 使用 ConfigManager 验证配置

### ⚠️ 错误处理
- 每个关键步骤添加日志
- 使用 try-except 捕获异常
- 提供用户友好的错误消息
- 记录到 history

### ⚠️ 文件路径
- 使用 `Path` 对象
- 跨平台兼容（Windows/Linux/Mac）
- 使用相对路径（相对于项目根目录）

---

## 测试策略

### 单元测试
- 位置：`tests/modules/`, `tests/core/`
- 使用 pytest + pytest-asyncio
- Mock LLM 调用

### 集成测试
- 测试完整工作流
- 测试模块间交互
- 测试配置加载

### E2E 测试
- 测试 CLI 命令
- 测试真实场景（真实 URL、视频）

---

## 性能优化

### 1. 并发处理
```python
# 批量处理多个链接
results = await asyncio.gather(
    module.process(url1),
    module.process(url2),
    module.process(url3),
)
```

### 2. 缓存
- Prompt Template 缓存
- LLM 配置缓存
- 历史记录缓存

### 3. 增量处理
- 历史记录分页
- 大文件分段处理
- LLM Token 限制处理

---

## 未来架构演进

### Phase 1: Agent 集成
- Agent 自动开发新模块
- Agent 自动优化 Prompt
- Agent 自动测试和验证

### Phase 2: 知识库
- 知识索引和搜索
- 知识图谱构建
- 跨模块知识关联

### Phase 3: 协作
- 多用户协作
- 知识分享
- 版本控制

### Phase 4: AI 深度集成
- 自动内容推荐
- 学习路径规划
- 智能问答

---

**Agent 理解架构后，可参考 AGENT_DEVELOPMENT_GUIDE.md 开始开发。**