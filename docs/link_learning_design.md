# Link Learning Module 设计文档

## 概述

链接学习模块用于从网页文章、技术文档、学术资源中提取知识，生成结构化的知识卡片，并提供交互式问答和测验功能。

## 1. 核心功能

### 1.1 功能列表

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 网页抓取 | 从 URL 获取网页内容 | P0 (核心) |
| 内容解析 | 提取正文、标题、元数据 | P0 (核心) |
| 知识卡片生成 | 结构化知识点总结 | P0 (核心) |
| 标签提取 | 自动生成内容标签 | P1 (重要) |
| 交互式问答 | 基于内容的问答 | P1 (重要) |
| 测验生成 | 自动生成测验题 | P2 (可选) |
| 学习路径推荐 | 推荐相关学习资源 | P2 (可选) |

### 1.2 输入输出

**输入**:
- URL（网页链接）
- 可选：抓取配置（超时、代理、Cookie）
- 可选：解析配置（内容类型、语言）

**输出**:
```json
{
  "title": "文章标题",
  "url": "原始链接",
  "source": "来源网站",
  "summary": "200字摘要",
  "key_points": [
    "要点1",
    "要点2",
    "要点3"
  ],
  "tags": ["技术", "Python", "AI"],
  "word_count": 5000,
  "reading_time": "15分钟",
  "difficulty": "intermediate",
  "created_at": "2026-03-31T10:00:00Z",
  "qa_pairs": [
    {
      "question": "问题1",
      "answer": "答案1"
    }
  ],
  "quiz": [
    {
      "type": "multiple_choice",
      "question": "测验题1",
      "options": ["A", "B", "C", "D"],
      "correct": "A"
    }
  ]
}
```

---

## 2. 技术栈选择

### 2.1 网页抓取

#### 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **requests + BeautifulSoup** | 简单快速、无依赖 | 不支持动态页面 | 静态页面 |
| **trafilatura** | 专为内容提取设计、准确率高 | 仅支持正文提取 | 新闻/博客文章 |
| **readability-lxml** | Mozilla 的 Readability 移植 | 需要 lxml | 通用网页 |
| **playwright** | 支持动态页面、浏览器模拟 | 重、慢、需安装浏览器 | SPA/动态加载页面 |
| **Firecrawl** | 现代化抓取工具、支持多种格式 | 需要 API Key（有免费额度） | 生产环境推荐 |

#### 最终方案

**主方案**: `trafilatura` (静态页面)
**备用方案**: `playwright` (动态页面，可选)

```python
# requirements.txt 新增依赖
trafilatura>=1.6.0        # 内容提取
playwright>=1.40.0        # 动态页面（可选）
beautifulsoup4>=4.12.0    # HTML 解析（备用）
lxml>=5.0.0               # XML 解析
```

### 2.2 内容解析

**工具**: `trafilatura`

**功能**:
- 自动识别正文内容
- 提取标题、作者、日期
- 移除广告、导航栏、评论区
- 支持多种格式输出（JSON、Markdown、XML）

**示例**:
```python
from trafilatura import fetch_url, extract

url = "https://example.com/article"
html = fetch_url(url)
content = extract(
    html,
    output_format="json",
    include_comments=False,
    include_tables=True,
    favor_precision=True  # 优先精确度
)
```

### 2.3 LLM 处理

使用现有的 `LLMService`，设计专用 Prompt 模板。

---

## 3. 数据模型设计

### 3.1 核心数据类

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import list, Optional


@dataclass
class LinkContent:
    """抓取的原始内容"""
    url: str
    title: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    content: str                    # 正文内容
    html: Optional[str] = None      # 原始 HTML
    source: str                     # 来源网站
    word_count: int
    language: str = "zh"            # zh/en


@dataclass
class KnowledgeCard:
    """知识卡片"""
    title: str
    url: str
    source: str
    summary: str                    # 200字摘要
    key_points: list[str]           # 核心要点（3-5个）
    tags: list[str]                 # 自动生成的标签
    word_count: int
    reading_time: str               # 预估阅读时间
    difficulty: str                 # beginner/intermediate/advanced
    created_at: datetime
    qa_pairs: list[QAPair] = field(default_factory=list)
    quiz: list[QuizQuestion] = field(default_factory=list)


@dataclass
class QAPair:
    """问答对"""
    question: str
    answer: str
    difficulty: str = "medium"


@dataclass
class QuizQuestion:
    """测验题"""
    type: str                       # multiple_choice/true_false/fill_blank
    question: str
    options: Optional[list[str]] = None
    correct: str                    # 正确答案
    explanation: Optional[str] = None
```

### 3.2 Prompt 模板

**文件**: `templates/prompts/link_summary.yaml`

```yaml
name: link_summary
version: 1.0
language: zh
description: 网页内容总结和知识卡片生成

template: |
  你是一位专业的知识整理助手。请分析以下网页内容，生成结构化的知识卡片。

  ## 网页内容
  标题：{{ title }}
  来源：{{ source }}
  字数：{{ word_count }}
  正文：
  {{ content }}

  ## 任务要求
  1. **摘要**：生成200字左右的摘要，概括核心内容
  2. **核心要点**：提取3-5个最重要的知识点
  3. **标签**：生成3-5个相关标签（技术领域、主题、难度等）
  4. **难度评估**：评估内容难度（beginner/intermediate/advanced）
  5. **问答生成**：生成3个基于内容的问答对
  6. **测验题**：生成2个测验题（多选题）

  ## 输出格式（JSON）
  请严格按照以下 JSON Schema 输出：
  ```json
  {
    "summary": "200字摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "tags": ["标签1", "标签2", "标签3"],
    "difficulty": "intermediate",
    "qa_pairs": [
      {
        "question": "问题1",
        "answer": "答案1",
        "difficulty": "medium"
      }
    ],
    "quiz": [
      {
        "type": "multiple_choice",
        "question": "测验题1",
        "options": ["A", "B", "C", "D"],
        "correct": "A",
        "explanation": "解释"
      }
    ]
  }
  ```

  ## 注意事项
  - 摘要应准确概括内容，不要添加原文没有的信息
  - 核心要点应是最重要的知识点，不是细节
  - 标签应简洁准确，便于分类和检索
  - 问答和测验应基于原文内容，不要引入外部知识

variables:
  - name: title
    type: string
    required: true
    description: 网页标题
  - name: source
    type: string
    required: true
    description: 来源网站
  - name: word_count
    type: integer
    required: true
    description: 字数
  - name: content
    type: string
    required: true
    description: 正文内容

output_format: json
json_schema:
  type: object
  properties:
    summary:
      type: string
      minLength: 100
      maxLength: 300
    key_points:
      type: array
      items:
        type: string
      minItems: 3
      maxItems: 5
    tags:
      type: array
      items:
        type: string
      minItems: 3
      maxItems: 5
    difficulty:
      type: string
      enum: [beginner, intermediate, advanced]
    qa_pairs:
      type: array
      items:
        type: object
        properties:
          question:
            type: string
          answer:
            type: string
          difficulty:
            type: string
            enum: [easy, medium, hard]
    quiz:
      type: array
      items:
        type: object
        properties:
          type:
            type: string
            enum: [multiple_choice, true_false, fill_blank]
          question:
            type: string
          options:
            type: array
            items:
              type: string
          correct:
            type: string
          explanation:
            type: string
  required: [summary, key_points, tags, difficulty, qa_pairs, quiz]
```

---

## 4. 模块架构设计

### 4.1 类结构

```python
class LinkLearningModule(BaseModule):
    """链接学习模块"""

    def __init__(self):
        self.content_fetcher: ContentFetcher
        self.content_parser: ContentParser
        self.prompt_manager: PromptManager
        self.llm_service: LLMService
        self.exporter: MarkdownExporter
        self.history_manager: HistoryManager

    @property
    def name(self) -> str:
        return "link_learning"

    def initialize(self, config: dict, event_bus: EventBus) -> None:
        """初始化模块"""
        pass

    async def process(self, url: str, options: dict) -> KnowledgeCard:
        """
        处理链接，生成知识卡片

        Args:
            url: 网页链接
            options: 处理选项

        Returns:
            知识卡片
        """
        pass


class ContentFetcher:
    """内容抓取器"""

    async def fetch(self, url: str, config: dict) -> str:
        """
        抓取网页 HTML

        Args:
            url: 网页链接
            config: 抓取配置

        Returns:
            HTML 内容
        """
        pass


class ContentParser:
    """内容解析器"""

    def parse(self, html: str, url: str) -> LinkContent:
        """
        解析网页内容

        Args:
            html: HTML 内容
            url: 原始链接

        Returns:
            结构化的链接内容
        """
        pass
```

### 4.2 处理流程

```
┌─────────────┐
│ 输入 URL    │
└─────────────┘
       │
       ▼
┌─────────────┐
│ Content     │  1. 抓取网页 HTML
│ Fetcher     │  2. 处理动态页面（可选）
│             │  3. 错误处理和重试
└─────────────┘
       │
       ▼
┌─────────────┐
│ Content     │  1. 提取正文内容
│ Parser      │  2. 提取元数据（标题、作者、日期）
│             │  3. 移除噪音（广告、导航栏）
│             │  4. 计算字数和阅读时间
└─────────────┘
       │
       ▼
┌─────────────┐
│ Prompt      │  1. 选择 Prompt 模板
│ Manager     │  2. 填充变量（title, content, etc）
│             │  3. 生成结构化 Prompt
└─────────────┘
       │
       ▼
┌─────────────┐
│ LLM         │  1. 调用 LLM API
│ Service     │  2. 获取 JSON 输出
│             │  3. 验证 JSON Schema
└─────────────┘
       │
       ▼
┌─────────────┐
│ Knowledge   │  1. 构建知识卡片对象
│ Card        │  2. 添加元数据
│ Builder     │  3. 验证数据完整性
└─────────────┘
       │
       ▼
┌─────────────┐
│ Exporter    │  1. 导出 Markdown
│             │  2. 导出 PDF（可选）
│             │  3. 保存到历史记录
└─────────────┘
       │
       ▼
┌─────────────┐
│ 输出结果    │  返回 KnowledgeCard
└─────────────┘
```

---

## 5. 配置设计

### 5.1 模块配置

**文件**: `config/modules.yaml`

```yaml
modules:
  link_learning:
    enabled: true
    priority: 10
    description: "链接学习模块"

    config:
      # 抓取配置
      fetcher:
        timeout: 30                    # 超时时间（秒）
        max_retries: 3                 # 最大重试次数
        retry_delay: 2                 # 重试延迟（秒）
        use_playwright: false          # 是否使用 Playwright（动态页面）
        user_agent: "Mozilla/5.0..."   # User-Agent
        proxy: null                    # 代理服务器（可选）

      # 解析配置
      parser:
        engine: "trafilatura"          # 解析引擎
        include_comments: false        # 是否包含评论
        include_tables: true           # 是否包含表格
        favor_precision: true          # 优先精确度
        min_content_length: 200        # 最小内容长度

      # LLM 配置
      llm:
        provider: "openai"             # LLM 提供者
        model: "gpt-4"                 # 模型
        temperature: 0.3               # 温度（低温度保证稳定性）
        max_tokens: 2000               # 最大输出 tokens

      # 输出配置
      output:
        format: ["markdown", "json"]   # 输出格式
        directory: "data/outputs/link" # 输出目录
        save_history: true             # 是否保存历史

      # 功能开关
      features:
        generate_qa: true              # 是否生成问答
        generate_quiz: true            # 是否生成测验
        extract_tags: true             # 是否提取标签
        estimate_difficulty: true      # 是否评估难度
```

---

## 6. 接口设计

### 6.1 CLI 命令

```bash
# 基础用法
la link https://example.com/article

# 高级选项
la link https://example.com/article \
  --provider openai \
  --model gpt-4 \
  --no-quiz \
  --output pdf \
  --save

# 查看历史
la link-history

# 批量处理
la link-batch urls.txt
```

### 6.2 Python API

```python
from learning_assistant.api import process_link

# 异步调用
result = await process_link(
    url="https://example.com/article",
    options={
        "provider": "openai",
        "model": "gpt-4",
        "generate_quiz": True
    }
)

# 同步调用
from learning_assistant.api import process_link_sync
result = process_link_sync(url="https://...")

# 批量处理
urls = ["https://...", "https://..."]
results = await process_link_batch(urls)
```

### 6.3 Skills 接口

**文件**: `skills/link-learning.md`

```markdown
# link-learning

从网页链接提取知识，生成结构化的知识卡片。

## 参数
- `url`: 网页链接（必需）
- `provider`: LLM 提供者（可选，默认 openai）
- `model`: LLM 模型（可选）
- `generate_quiz`: 是否生成测验（可选，默认 true）

## 返回
- 知识卡片（JSON）
- Markdown 文件
- 历史记录
```

---

## 7. 测试计划

### 7.1 单元测试

| 测试类 | 测试内容 | 测试数量 |
|--------|----------|----------|
| `TestContentFetcher` | 抓取功能、错误处理、重试机制 | 20 |
| `TestContentParser` | 解析准确性、元数据提取、噪音移除 | 30 |
| `TestPromptManager` | 模板加载、变量填充、JSON 验证 | 15 |
| `TestKnowledgeCardBuilder` | 数据构建、验证、完整性检查 | 20 |
| `TestLinkLearningModule` | 完整流程、集成测试 | 25 |

**总计**: 约 110 个单元测试

### 7.2 集成测试

- 抓取真实网页（新闻、博客、技术文档）
- 处理不同语言内容（中文、英文）
- 处理不同格式（静态页面、动态页面）
- 测试 LLM 输出准确性
- 测试导出格式

### 7.3 性能测试

- 抓取速度: <5s（静态页面）、<10s（动态页面）
- 处理时间: <30s（包含 LLM 调用）
- 内存占用: <200MB
- 并发处理: 支持同时处理 3-5 个链接

---

## 8. 实现计划

### 8.1 开发时间表

| 天数 | 任务 | 预计时间 |
|------|------|----------|
| Day 1-2 | ContentFetcher 实现 + 测试 | 8小时 |
| Day 3-4 | ContentParser 实现 + 测试 | 8小时 |
| Day 5 | Prompt 模板设计 + 数据模型 | 6小时 |
| Day 6-7 | LLM 处理 + 知识卡片构建 | 10小时 |
| Day 8 | 导出器 + 历史管理 | 6小时 |
| Day 9-10 | CLI 命令 + Python API | 8小时 |
| Day 11-12 | 测试完善 + 文档 | 10小时 |

**总计**: 约 56 小时（2周）

### 8.2 里程碑

- **Milestone 1**: 抓取和解析功能完成（Day 4）
- **Milestone 2**: LLM 处理完成（Day 7）
- **Milestone 3**: 模块集成完成（Day 10）
- **Milestone 4**: 测试和文档完成（Day 12）

---

## 9. 风险评估

### 9.1 技术风险

| 风险 | 影响 | 解决方案 |
|------|------|----------|
| 网页反爬机制 | 抓取失败 | 使用 Cookie、代理、User-Agent |
| 动态页面加载 | 内容缺失 | Playwright 浏览器模拟 |
| 内容提取不准确 | 知识卡片质量低 | 多引擎对比、人工验证 |
| LLM 输出不稳定 | JSON 格式错误 | 严格的 JSON Schema、重试机制 |
| 网络超时 | 处理失败 | 重试机制、缓存、降级处理 |

### 9.2 依赖风险

- `trafilatura`: 成熟稳定，风险低
- `playwright`: 依赖浏览器，安装复杂（可选依赖）

---

## 10. 未来扩展

### 10.1 短期扩展（v0.3.0）

- 支持更多内容源（GitHub、知乎、微信公众号）
- 批量处理优化
- 内容去重和相似度检测
- 学习路径推荐

### 10.2 长期扩展（v1.0.0）

- 多语言支持（自动检测语言）
- 知识图谱构建
- 与其他模块联动（单词提取）
- 社区贡献的解析规则

---

## 11. 参考资料

### 11.1 工具文档

- **trafilatura**: https://trafilatura.readthedocs.io/
- **playwright**: https://playwright.dev/python/
- **readability-lxml**: https://github.com/buriy/python-readability

### 11.2 API 设计参考

- **现有视频总结模块**: `src/learning_assistant/modules/video_summary/`

---

**设计完成日期**: 2026-03-31
**版本**: v1.0
**状态**: 设计完成，待实现