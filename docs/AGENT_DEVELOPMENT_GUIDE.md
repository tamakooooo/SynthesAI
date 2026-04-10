# Learning Assistant - AI Agent 开发指南

> 本文档专为 AI Agent 设计，帮助 agent 快速理解项目架构并参与开发。

## 项目概览

**Learning Assistant** 是一个模块化、插件化的 AI 学习助手 CLI 工具，支持 Agent 集成。

**核心定位**：
- 📚 面向个人学习的知识管理工具
- 🔌 插件化架构，易于扩展新模块
- 🤖 Agent-ready，支持 AI 自动化工作流
- 📊 多模态输出（Markdown、知识卡片、PDF）

**技术栈**：
- Python 3.11+
- Typer CLI + Rich UI
- Async/await 异步架构
- Event Bus 事件系统
- Plugin Manager 插件管理

---

## 架构设计（Agent 必读）

### 1. 核心架构层次

```
┌─────────────────────────────────────────┐
│         CLI Layer (typer + rich)         │  用户交互层
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Plugin Manager + Event Bus          │  插件管理层
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│    Modules (video/link/vocabulary)       │  功能模块层
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│   Core Services (LLM/Exporter/Auth)      │  核心服务层
└─────────────────────────────────────────┘
```

### 2. Agent 参与开发的方式

Agent 可以在以下层次参与开发：

#### ✅ **模块层开发**（推荐）
- 创建新的学习模块（如读书笔记、课程总结）
- 扩展现有模块功能（如视频总结添加章节截图）
- 定义模块的 Prompt Template 和输出模板

#### ✅ **核心服务层扩展**
- 开发新的 LLM Provider（如 Claude、Gemini）
- 创建新的导出器（如 PDF、HTML、知识卡片）
- 实现新的认证 Provider（如 YouTube、Twitter）

#### ✅ **CLI 层优化**
- 添加新的命令和参数
- 优化交互体验和错误提示
- 设计批量处理工作流

---

## 核心组件（Agent 可复用）

### 1. LLM Service

**位置**：`src/learning_assistant/core/llm/service.py`

**Agent 使用示例**：
```python
from learning_assistant.core.llm.service import LLMService

# 初始化 LLM
llm = LLMService(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4",
)

# 调用 LLM（同步）
response = llm.call(
    prompt="Your prompt here",
    temperature=0.3,
    max_tokens=2000,
)

# 调用 LLM（异步）
response = await asyncio.to_thread(
    llm.call,
    prompt="Your prompt",
)
```

**可扩展点**：
- 新增 Provider：继承 `BaseLLMProvider`
- 支持新模型：在 `config/settings.yaml` 中配置

---

### 2. Prompt Manager

**位置**：`src/learning_assistant/core/prompt_manager.py`

**Agent 使用示例**：
```python
from learning_assistant.core.prompt_manager import PromptManager

# 初始化
prompt_manager = PromptManager(
    template_dirs=[Path("templates/prompts")],
    llm_service=llm_service,
)

# 加载模板
template = prompt_manager.load_template("link_summary")

# 渲染模板
system_prompt, user_prompt = template.render({
    "title": "GitHub - example/repo",
    "source": "github.com",
    "word_count": 500,
    "content": "Article content here...",
})

# 调用 LLM
response = llm_service.call(prompt=user_prompt)
```

**创建新模板**（Agent 常见任务）：
```yaml
# templates/prompts/new_module.yaml
name: new_module
version: 1.0
language: zh
description: 新模块的 LLM 提示词模板

template: |
  你是一位专业的助手。请分析以下内容：

  ## 输入内容
  标题：{{ title }}
  正文：{{ content }}

  ## 任务要求
  1. 提取核心要点
  2. 生成摘要

  ## 输出格式（JSON）
  ```json
  {
    "summary": "摘要内容",
    "key_points": ["要点1", "要点2"]
  }
  ```

variables:
  - name: title
    type: string
    required: true
  - name: content
    type: string
    required: true

output_format: json
json_schema:
  type: object
  properties:
    summary: {type: string}
    key_points: {type: array}
```

---

### 3. Markdown Exporter

**位置**：`src/learning_assistant/core/exporters/markdown.py`

**Agent 使用示例**：
```python
from learning_assistant.core.exporters import MarkdownExporter

# 初始化
exporter = MarkdownExporter(
    template_dir=Path("templates/outputs"),
    template_name="link_summary.md",
)

# 导出数据
exporter.export(
    data={
        "title": "Article Title",
        "summary": "Summary content...",
        "key_points": ["Point 1", "Point 2"],
    },
    output_path=Path("outputs/result.md"),
)
```

---

### 4. Visual Card Generator（新增）

**位置**：`src/learning_assistant/core/exporters/visual_card.py`

**Agent 使用示例**：
```python
from learning_assistant.core.exporters.visual_card import VisualCardGenerator

# 初始化
generator = VisualCardGenerator(width=1200)

# 生成 HTML
html_content = generator.generate_card_html(
    title="文章标题",
    summary="300-500字的摘要内容",
    key_points=[
        "关键词：详细描述",
        "要点2：说明2",
    ],
    key_concepts=[
        {"term": "概念名", "definition": "50-150字解释"},
    ],
    tags=["标签1", "标签2"],
    source="github.com",
    url="https://github.com/example",
)

# 渲染为 PNG（需要 Playwright）
await generator.render_html_to_image(
    html_content=html_content,
    output_path=Path("output/card.png"),
    width=1200,
    scale=2.0,
)
```

**Agent 设计要点**：
- ✅ 核心要点格式：**关键词：详细描述**（关键！）
- ✅ 关关键词：3-8字（适合卡片标题）
- ✅ 详细描述：15-30字（适合卡片内容）
- ✅ 关键概念：2-3个，每个 50-150字定义
- ✅ 标签：3-5个

---

## 开发新模块流程（Agent 标准流程）

### Step 1: 定义模块结构

```python
# src/learning_assistant/modules/new_module/__init__.py

class NewModule(BaseModule):
    """新学习模块"""

    def __init__(self):
        self.config: dict[str, Any] = {}
        self.event_bus: EventBus | None = None

        # 组件（Agent 可复用）
        self.llm_service: LLMService | None = None
        self.prompt_manager: PromptManager | None = None
        self.exporter: MarkdownExporter | None = None

    @property
    def name(self) -> str:
        return "new_module"

    def initialize(self, config: dict, event_bus: EventBus):
        """初始化模块"""
        self.config = config
        self.event_bus = event_bus
        self._init_components()

    def _init_components(self):
        """初始化组件（Agent 模板代码）"""
        # 1. LLM Service
        llm_config = self.config.get("llm", {})
        self.llm_service = LLMService(
            provider=llm_config.get("provider", "openai"),
            api_key=self._get_api_key(),
            model=llm_config.get("model", "gpt-4"),
        )

        # 2. Prompt Manager
        self.prompt_manager = PromptManager(
            template_dirs=[Path("templates/prompts")],
            llm_service=self.llm_service,
        )

        # 3. Exporter
        output_config = self.config.get("output", {})
        self.exporter = MarkdownExporter(
            template_dir=Path("templates/outputs"),
            template_name="new_module.md",
        )

    async def process(self, input_data: dict) -> dict:
        """核心处理流程"""
        # 1. 加载提示词模板
        template = self.prompt_manager.load_template("new_module")
        system_prompt, user_prompt = template.render(input_data)

        # 2. 调用 LLM
        response = await asyncio.to_thread(
            self.llm_service.call,
            prompt=user_prompt,
        )

        # 3. 解析结果
        result_data = self._parse_response(response.content)

        # 4. 导出
        await self._export(result_data)

        return result_data

    def cleanup(self):
        """清理资源"""
        pass
```

### Step 2: 创建 Prompt Template

Agent 在 `templates/prompts/new_module.yaml` 创建模板（参考上面示例）。

### Step 3: 创建输出模板

Agent 在 `templates/outputs/new_module.md` 创建 Jinja2 模板：
```markdown
# {{ title }}

**来源**: {{ source }}
**生成时间**: {{ created_at }}

---

## 内容摘要

{{ summary }}

---

## 核心要点

{% for point in key_points %}
{{ loop.index }}. {{ point }}
{% endfor %}

---

*由 Learning Assistant 自动生成*
```

### Step 4: 创建配置文件

Agent 在 `config/modules.yaml` 添加配置：
```yaml
new_module:
  enabled: true

  llm:
    provider: openai
    model: gpt-4
    temperature: 0.3
    max_tokens: 2000

  output:
    save_history: true
    output_dir: "data/outputs/new_module"
```

### Step 5: 创建 plugin.yaml

Agent 在 `src/learning_assistant/modules/new_module/plugin.yaml` 创建：
```yaml
name: new_module
type: module
version: 1.0.0
description: 新学习模块

dependencies:
  - trafilatura>=1.6.0

entry_point: learning_assistant.modules.new_module:NewModule

commands:
  - name: new
    description: 处理新模块内容
    example: "la new <input>"
```

### Step 6: 添加 CLI 命令

Agent 在 `src/learning_assistant/cli.py` 添加命令：
```python
@app.command("new")
def new_command(input_data: str):
    """新模块命令"""
    module = plugin_manager.get_plugin("new_module")
    result = module.execute({"input": input_data})
    # 显示结果...
```

---

## Agent 最佳实践

### 1. 遵循现有模块模式
- ✅ 参考 `link_learning` 或 `video_summary` 的实现
- ✅ 使用相同的组件初始化流程
- ✅ 保持异步架构一致性

### 2. Prompt Template 设计
- ✅ 明确输出格式（JSON Schema）
- ✅ 提供清晰的任务说明
- ✅ 使用变量化模板（便于复用）
- ✅ 添加格式验证（minLength/maxLength）

### 3. 输出模板设计
- ✅ 使用 Jinja2 模板引擎
- ✅ 结构化展示内容
- ✅ 添加元信息（时间、来源等）
- ✅ 保持美观和易读性

### 4. 错误处理
- ✅ 在所有关键步骤添加日志
- ✅ 使用 try-except 捕获异常
- ✅ 提供用户友好的错误消息
- ✅ 记录到 history 便于追踪

### 5. 测试
- ✅ 创建单元测试（tests/modules/）
- ✅ 测试 LLM 调用（使用 mock）
- ✅ 测试输出导出
- ✅ 测试完整工作流

---

## Agent 常见任务清单

### ✅ 创建新模块
1. 创建模块目录结构
2. 实现 BaseModule 接口
3. 创建 Prompt Template
4. 创建输出模板
5. 配置模块参数
6. 添加 CLI 命令
7. 编写单元测试
8. 编写文档

### ✅ 扩展现有模块
1. 识别扩展点（如导出器、新功能）
2. 修改模块代码
3. 更新 Prompt Template（如需要）
4. 更新配置文件
5. 更新测试
6. 更新文档

### ✅ 创建新导出器
1. 继承 BaseExporter
2. 实现导出逻辑
3. 支持多种格式（可选）
4. 添加配置选项
5. 编写测试
6. 集成到模块

### ✅ 优化 Prompt
1. 分析现有输出质量
2. 调整提示词内容
3. 添加格式验证
4. 测试新提示词
5. 对比效果
6. 更新文档

---

## Agent 快速参考

### 关键文件位置
- **模块代码**：`src/learning_assistant/modules/<module>/`
- **Prompt 模板**：`templates/prompts/<template>.yaml`
- **输出模板**：`templates/outputs/<template>.md`
- **配置文件**：`config/modules.yaml`, `config/settings.yaml`
- **CLI 命令**：`src/learning_assistant/cli.py`
- **核心组件**：`src/learning_assistant/core/`
- **测试文件**：`tests/modules/`, `tests/core/`

### 常用命令
```bash
# 运行链接总结
la link https://github.com/example/repo

# 运行视频总结
la video https://bilibili.com/video/BV123456

# 运行词汇学习
la vocabulary hello world

# 测试
pytest tests/modules/test_link_learning.py

# 安装依赖
pip install playwright
playwright install chromium
```

### 重要提示
- ⚠️ 所有异步函数必须使用 `async def` 和 `await`
- ⚠️ LLM API Key 必须从环境变量或配置文件读取
- ⚠️ 不要硬编码任何敏感信息
- ⚠️ 使用类型注解（`dict[str, Any]`）
- ⚠️ 添加详细的日志记录

---

## Agent 需要知道的限制

1. **LLM 调用限制**
   - 需要配置 API Key
   - 有 rate limit
   - 有 token 限制

2. **异步架构**
   - 不能在 async 函数中使用 `asyncio.run()`
   - 必须使用 `await`

3. **文件路径**
   - 使用 `Path` 对象，不是字符串
   - 跨平台兼容（Windows/Linux/Mac）

4. **配置管理**
   - 配置在 `config/` 目录
   - 使用 ConfigManager 加载
   - 遵循 YAML Schema

---

## Agent 开发建议

### 推荐工作流
1. **理解需求** → 阅读 module 的设计文档
2. **参考现有** → 查看 link_learning 或 video_summary 实现
3. **复用组件** → 使用 LLMService、PromptManager、Exporter
4. **增量开发** → 先实现核心功能，再扩展
5. **测试验证** → 编写测试，验证每个步骤
6. **文档更新** → 更新模块文档和 Agent 指南

### 避免
- ❌ 不要修改核心架构（除非必要）
- ❌ 不要破坏现有模块的兼容性
- ❌ 不要硬编码配置或密钥
- ❌ 不要跳过测试
- ❌ 不要忽略日志和错误处理

---

## 后续扩展方向（Agent 可贡献）

1. **新学习模块**
   - 读书笔记总结
   - 课程知识提炼
   - 论文快速概览
   - 技术文档摘要

2. **新导出格式**
   - PDF 知识卡片
   - Interactive HTML
   - Anki 卡片导出
   - 思维导图生成

3. **新 LLM Provider**
   - Anthropic Claude
   - Google Gemini
   - 本地模型（Ollama）

4. **新功能**
   - 批量处理工作流
   - 知识库索引和搜索
   - 定期更新和同步
   - 协作和分享功能

---

**Agent 开发愉快！如有问题，参考现有模块实现或询问项目维护者。**