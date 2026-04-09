# Vocabulary Learning Module 设计文档

## 概述

单词学习模块用于从链接或内容中自动提取单词，生成结构化的单词卡片，并创建上下文短文巩固记忆。

## 1. 核心功能

### 1.1 功能列表

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 单词提取 | 从内容中识别重要单词 | P0 (核心) |
| 单词卡生成 | 生成完整单词卡（音标、释义、例句） | P0 (核心) |
| 例句生成 | 基于上下文生成例句 | P0 (核心) |
| 音标查询 | 获取单词音标 | P1 (重要) |
| 关联词汇 | 生成同义词、反义词、相关词 | P1 (重要) |
| 上下文短文 | 创建包含单词的短文巩固记忆 | P1 (重要) |
| 单词测验 | 生成单词测验题 | P2 (可选) |
| 记忆曲线追踪 | 跟踪单词记忆状态 | P2 (可选) |

### 1.2 输入输出

**输入**:
- 内容文本（文章、总结等）
- 可选：目标语言（英语、日语等）
- 可选：单词难度级别
- 可选：提取数量限制

**输出**:
```json
{
  "vocabulary_cards": [
    {
      "word": "ubiquitous",
      "phonetic": {
        "us": "/juˈbɪkwɪtəs/",
        "uk": "/juˈbɪkwɪtəs/"
      },
      "part_of_speech": "adj",
      "definition": {
        "zh": "无处不在的，普遍存在的",
        "en": "present, appearing, or found everywhere"
      },
      "example_sentences": [
        {
          "sentence": "Smartphones have become ubiquitous in modern society.",
          "translation": "智能手机在现代社会无处不在。",
          "context": "从原文提取"
        },
        {
          "sentence": "The ubiquitous nature of social media...",
          "translation": "社交媒体无处不在的特性...",
          "context": "LLM生成"
        }
      ],
      "synonyms": ["omnipresent", "pervasive", "universal"],
      "antonyms": ["rare", "scarce", "limited"],
      "related_words": ["ubiquity", "ubiquitously"],
      "difficulty": "advanced",
      "frequency": "medium",
      "memory_status": "new",
      "created_at": "2026-03-31T10:00:00Z"
    }
  ],
  "context_story": {
    "title": "The Ubiquitous Technology",
    "content": "一篇包含所有提取单词的短文...",
    "word_count": 300,
    "difficulty": "intermediate"
  },
  "quiz": [
    {
      "type": "definition",
      "word": "ubiquitous",
      "question": "What does 'ubiquitous' mean?",
      "options": ["...", "...", "...", "..."],
      "correct": "A"
    }
  ],
  "statistics": {
    "total_words": 10,
    "difficulty_distribution": {
      "beginner": 3,
      "intermediate": 5,
      "advanced": 2
    }
  }
}
```

---

## 2. 技术栈选择

### 2.1 单词提取

#### 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **LLM 提取** | 理解上下文、准确率高 | 成本高、速度慢 | 通用场景 |
| **词频统计 + 规则** | 快速、免费 | 准确率低、无上下文理解 | 简单场景 |
| **NLTK/spacy** | 专业 NLP、支持词性标注 | 需要模型、复杂 | 学术场景 |
| **混合方案** | 平衡准确率和效率 | 实现复杂 | 生产环境 |

#### 最终方案

**主方案**: LLM 提取（理解上下文）
**备用方案**: 词频统计 + 规则过滤（快速提取）

```python
# requirements.txt 新增依赖
nltk>=3.8.0               # NLP工具（可选）
spacy>=3.7.0              # 高级NLP（可选）
```

### 2.2 音标查询

#### 方案对比

| 方案 | 数据源 | 优点 | 缺点 |
|------|--------|------|------|
| **本地词典** | JSON/数据库 | 快速、免费 | 需要维护数据 |
| **在线API** | Free Dictionary API | 免费、数据完整 | 依赖网络 |
| **LLM生成** | GPT-4 | 准确、支持多语言 | 成本高 |
| **混合方案** | 本地 + API + LLM | 平衡性能和准确率 | 实现复杂 |

#### 最终方案

**优先级顺序**:
1. 本地词典查询（快速、免费）
2. Free Dictionary API（补充）
3. LLM 生成（兜底）

**API**:
- Free Dictionary API: https://dictionaryapi.dev/
- 有道词典 API（可选，需要 API Key）

```python
# 示例：Free Dictionary API
import requests

def get_phonetic(word: str) -> dict:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "us": data[0]["phonetics"][0].get("text", ""),
            "uk": data[0]["phonetics"][1].get("text", "")
        }
    return {}
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
class Phonetic:
    """音标"""
    us: Optional[str] = None    # 美式音标
    uk: Optional[str] = None    # 英式音标


@dataclass
class Definition:
    """释义"""
    zh: str                     # 中文释义
    en: Optional[str] = None    # 英文释义


@dataclass
class ExampleSentence:
    """例句"""
    sentence: str               # 例句
    translation: str            # 翻译
    context: str                # 上下文（原文提取/LLM生成）
    source: Optional[str] = None  # 来源


@dataclass
class VocabularyCard:
    """单词卡"""
    word: str                   # 单词
    phonetic: Phonetic          # 音标
    part_of_speech: str         # 词性（noun/verb/adj/adv/etc）
    definition: Definition      # 释义
    example_sentences: list[ExampleSentence]  # 例句（至少2个）
    synonyms: list[str] = field(default_factory=list)  # 同义词
    antonyms: list[str] = field(default_factory=list)  # 反义词
    related_words: list[str] = field(default_factory=list)  # 相关词
    difficulty: str             # beginner/intermediate/advanced
    frequency: str              # high/medium/low（词频）
    memory_status: str = "new"  # new/learning/mastered
    created_at: datetime
    last_reviewed: Optional[datetime] = None
    review_count: int = 0


@dataclass
class ContextStory:
    """上下文短文"""
    title: str                  # 短文标题
    content: str                # 短文内容（包含所有单词）
    word_count: int             # 字数
    difficulty: str             # 难度
    target_words: list[str]     # 目标单词列表


@dataclass
class VocabularyQuiz:
    """单词测验"""
    type: str                   # definition/spelling/usage/fill_blank
    word: str                   # 单词
    question: str               # 问题
    options: Optional[list[str]] = None
    correct: str                # 正确答案
    explanation: Optional[str] = None


@dataclass
class VocabularyOutput:
    """单词学习输出"""
    vocabulary_cards: list[VocabularyCard]
    context_story: Optional[ContextStory] = None
    quiz: list[VocabularyQuiz] = field(default_factory=list)
    statistics: dict            # 统计信息
```

### 3.2 Prompt 模板

**文件**: `templates/prompts/vocabulary_extraction.yaml`

```yaml
name: vocabulary_extraction
version: 1.0
language: zh
description: 从内容中提取重要单词并生成单词卡

template: |
  你是一位专业的词汇教学助手。请从以下内容中提取重要的英语单词，并为每个单词生成完整的单词卡。

  ## 内容
  {{ content }}

  ## 提取要求
  1. **单词数量**: 提取 {{ word_count }} 个重要单词
  2. **难度分布**:
     - {{ difficulty_distribution }}
  3. **选择标准**:
     - 高频词汇（常用词优先）
     - 关键概念词（对理解内容重要）
     - 学术词汇（如果是学术内容）
     - 避免过于简单或过于罕见的词

  ## 单词卡内容要求
  对于每个单词，请提供以下信息：

  ### 必填字段
  - **单词**: 英文单词
  - **词性**: noun/verb/adj/adv/prep/etc
  - **释义**:
    - 中文释义（准确、简洁）
    - 英文释义（可选）
  - **例句**（至少2个）:
    - 例句1：从原文提取（如果有）
    - 例句2：LLM生成的新例句
    - 每个例句提供中文翻译
  - **难度**: beginner/intermediate/advanced
  - **词频**: high/medium/low

  ### 可选字段
  - **音标**: 美式和英式音标（IPA）
  - **同义词**: 2-3个同义词
  - **反义词**: 1-2个反义词（如果有）
  - **相关词**: 词根、派生词

  ## 输出格式（JSON）
  请严格按照以下 JSON Schema 输出：
  ```json
  {
    "vocabulary_cards": [
      {
        "word": "example",
        "phonetic": {
          "us": "/ɪgˈzæmpəl/",
          "uk": "/ɪgˈzæmpəl/"
        },
        "part_of_speech": "noun",
        "definition": {
          "zh": "例子，实例",
          "en": "a thing characteristic of its kind"
        },
        "example_sentences": [
          {
            "sentence": "This is an example.",
            "translation": "这是一个例子。",
            "context": "原文提取"
          },
          {
            "sentence": "Can you give me an example?",
            "translation": "你能给我一个例子吗？",
            "context": "LLM生成"
          }
        ],
        "synonyms": ["instance", "case", "sample"],
        "antonyms": [],
        "related_words": ["exemplify", "exemplary"],
        "difficulty": "beginner",
        "frequency": "high"
      }
    ]
  }
  ```

  ## 注意事项
  - 单词选择应平衡实用性和难度
  - 释义应准确，避免误导性翻译
  - 例句应自然、实用，避免生造句子
  - 音标使用 IPA 国际音标
  - 同义词和反义词应准确，不要随意填写

variables:
  - name: content
    type: string
    required: true
    description: 要提取单词的内容
  - name: word_count
    type: integer
    required: true
    default: 10
    description: 要提取的单词数量
  - name: difficulty_distribution
    type: string
    required: false
    default: "beginner: 30%, intermediate: 50%, advanced: 20%"
    description: 难度分布

output_format: json
json_schema:
  type: object
  properties:
    vocabulary_cards:
      type: array
      items:
        type: object
        properties:
          word:
            type: string
          phonetic:
            type: object
            properties:
              us:
                type: string
              uk:
                type: string
          part_of_speech:
            type: string
          definition:
            type: object
            properties:
              zh:
                type: string
              en:
                type: string
          example_sentences:
            type: array
            items:
              type: object
              properties:
                sentence:
                  type: string
                translation:
                  type: string
                context:
                  type: string
            minItems: 2
          synonyms:
            type: array
            items:
              type: string
          antonyms:
            type: array
            items:
              type: string
          related_words:
            type: array
            items:
              type: string
          difficulty:
            type: string
            enum: [beginner, intermediate, advanced]
          frequency:
            type: string
            enum: [high, medium, low]
        required: [word, part_of_speech, definition, example_sentences, difficulty, frequency]
  required: [vocabulary_cards]
```

**文件**: `templates/prompts/context_story.yaml`

```yaml
name: context_story
version: 1.0
language: zh
description: 生成包含目标单词的上下文短文

template: |
  你是一位专业的英语写作教师。请创作一篇包含以下单词的短文，帮助学习者巩固记忆。

  ## 目标单词
  {{ words }}

  ## 短文要求
  1. **主题**: {{ theme }}（或自动选择合适主题）
  2. **长度**: {{ word_count }} 字左右
  3. **难度**: {{ difficulty }}
  4. **内容要求**:
     - 所有目标单词自然融入短文
     - 句子通顺、逻辑连贯
     - 故事有趣、易于记忆
     - 避免生硬堆砌单词

  ## 输出格式（JSON）
  ```json
  {
    "title": "短文标题",
    "content": "短文内容...",
    "word_count": 300,
    "difficulty": "intermediate"
  }
  ```

  ## 注意事项
  - 单词使用应自然，符合语境
  - 故事应有连贯性，不要碎片化
  - 避免过于复杂或过于简单的句子
  - 可以添加适量的简单词汇作为连接

variables:
  - name: words
    type: array
    required: true
    description: 目标单词列表
  - name: theme
    type: string
    required: false
    description: 短文主题
  - name: word_count
    type: integer
    required: true
    default: 300
    description: 短文字数
  - name: difficulty
    type: string
    required: true
    default: "intermediate"
    description: 短文难度

output_format: json
```

---

## 4. 模块架构设计

### 4.1 类结构

```python
class VocabularyLearningModule(BaseModule):
    """单词学习模块"""

    def __init__(self):
        self.word_extractor: WordExtractor
        self.phonetic_lookup: PhoneticLookup
        self.prompt_manager: PromptManager
        self.llm_service: LLMService
        self.story_generator: StoryGenerator
        self.exporter: VocabularyExporter
        self.history_manager: HistoryManager

    @property
    def name(self) -> str:
        return "vocabulary"

    def initialize(self, config: dict, event_bus: EventBus) -> None:
        """初始化模块"""
        pass

    async def process(
        self,
        content: str,
        options: dict
    ) -> VocabularyOutput:
        """
        从内容提取单词并生成单词卡

        Args:
            content: 文本内容
            options: 处理选项

        Returns:
            单词学习输出
        """
        pass


class WordExtractor:
    """单词提取器"""

    async def extract(
        self,
        content: str,
        word_count: int,
        difficulty: str
    ) -> list[str]:
        """
        从内容提取重要单词

        Args:
            content: 文本内容
            word_count: 提取数量
            difficulty: 难度分布

        Returns:
            单词列表
        """
        pass


class PhoneticLookup:
    """音标查询器"""

    def lookup(self, word: str) -> Phonetic:
        """
        查询单词音标

        Args:
            word: 单词

        Returns:
            音标对象
        """
        pass

    def _lookup_local(self, word: str) -> Optional[Phonetic]:
        """本地词典查询"""
        pass

    def _lookup_api(self, word: str) -> Optional[Phonetic]:
        """在线API查询"""
        pass

    def _lookup_llm(self, word: str) -> Phonetic:
        """LLM生成（兜底）"""
        pass


class StoryGenerator:
    """短文生成器"""

    async def generate(
        self,
        words: list[str],
        theme: Optional[str],
        word_count: int,
        difficulty: str
    ) -> ContextStory:
        """
        生成包含目标单词的短文

        Args:
            words: 目标单词列表
            theme: 短文主题（可选）
            word_count: 字数
            difficulty: 难度

        Returns:
            上下文短文
        """
        pass
```

### 4.2 处理流程

```
┌─────────────┐
│ 输入内容    │  文章/总结/视频转录
└─────────────┘
       │
       ▼
┌─────────────┐
│ Word        │  1. LLM 提取重要单词
│ Extractor   │  2. 词频统计（可选）
│             │  3. 难度分类
└─────────────┘
       │
       ▼
┌─────────────┐
│ Phonetic    │  1. 本地词典查询（优先）
│ Lookup      │  2. Free Dictionary API
│             │  3. LLM 生成（兜底）
└─────────────┘
       │
       ▼
┌─────────────┐
│ Prompt      │  1. 填充单词列表
│ Manager     │  2. 生成单词卡 Prompt
│             │  3. 调用 LLM API
└─────────────┘
       │
       ▼
┌─────────────┐
│ LLM         │  1. 生成完整单词卡
│ Service     │  2. JSON 输出
│             │  3. Schema 验证
└─────────────┘
       │
       ▼
┌─────────────┐
│ Story       │  1. 选择单词列表
│ Generator   │  2. 生成上下文短文
│             │  3. LLM 创作
└─────────────┘
       │
       ▼
┌─────────────┐
│ Quiz        │  1. 生成测验题（可选）
│ Generator   │  2. 多种题型
│             │  3. 答案验证
└─────────────┘
       │
       ▼
┌─────────────┐
│ Exporter    │  1. 导出 Markdown
│             │  2. 导出 Anki 格式（可选）
│             │  3. 保存历史记录
└─────────────┘
       │
       ▼
┌─────────────┐
│ 输出结果    │  VocabularyOutput
└─────────────┘
```

---

## 5. 配置设计

### 5.1 模块配置

**文件**: `config/modules.yaml`

```yaml
modules:
  vocabulary:
    enabled: true
    priority: 15
    description: "单词学习模块"

    config:
      # 单词提取配置
      extraction:
        word_count: 10              # 默认提取单词数量
        difficulty_distribution:    # 难度分布
          beginner: 30%
          intermediate: 50%
          advanced: 20%
        min_word_length: 3          # 最小单词长度
        exclude_stopwords: true     # 排除停用词

      # 音标查询配置
      phonetic:
        lookup_order:               # 查询优先级
          - local                   # 本地词典
          - api                     # Free Dictionary API
          - llm                     # LLM生成
        local_dictionary: "data/dictionaries/english.json"
        api_url: "https://api.dictionaryapi.dev/api/v2/entries/en/"

      # LLM 配置
      llm:
        provider: "openai"
        model: "gpt-4"
        temperature: 0.5            # 略高温度保证创造性
        max_tokens: 3000

      # 上下文短文配置
      story:
        enabled: true               # 是否生成短文
        word_count: 300             # 短文字数
        difficulty: "intermediate"
        theme: null                 # 自动选择主题

      # 测验配置
      quiz:
        enabled: true
        types:                      # 测验题型
          - definition              # 释义题
          - spelling                # 拼写题
          - usage                   # 用法题
        count_per_word: 1           # 每个单词的测验题数

      # 输出配置
      output:
        format: ["markdown", "json", "anki"]
        directory: "data/outputs/vocabulary"
        save_history: true

      # 记忆追踪（可选）
      memory_tracking:
        enabled: false              # 是否启用记忆追踪
        review_algorithm: "spaced_repetition"
        retention_threshold: 0.8
```

---

## 6. 接口设计

### 6.1 CLI 命令

```bash
# 从内容提取单词
la vocabulary --content "文章内容..."

# 从文件提取单词
la vocabulary --file article.txt

# 从链接提取单词（联动 LinkLearning 模块）
la vocabulary --link https://example.com/article

# 从视频总结提取单词（联动 VideoSummary 模块）
la vocabulary --video https://bilibili.com/video/BV123

# 高级选项
la vocabulary --content "..." \
  --word-count 15 \
  --difficulty intermediate \
  --no-story \
  --output anki \
  --save

# 查看单词历史
la vocabulary-history

# 复习单词（启用记忆追踪时）
la vocabulary-review
```

### 6.2 Python API

```python
from learning_assistant.api import extract_vocabulary

# 从内容提取
result = await extract_vocabulary(
    content="文章内容...",
    options={
        "word_count": 10,
        "difficulty": "intermediate",
        "generate_story": True
    }
)

# 从链接提取（联动 LinkLearning）
result = await extract_vocabulary(
    link="https://example.com/article",
    options={...}
)

# 从视频提取（联动 VideoSummary）
result = await extract_vocabulary(
    video_url="https://bilibili.com/video/BV123",
    options={...}
)

# 批量处理
contents = ["内容1", "内容2", "内容3"]
results = await extract_vocabulary_batch(contents)
```

### 6.3 Skills 接口

**文件**: `skills/vocabulary-learning.md`

```markdown
# vocabulary-learning

从内容中提取单词并生成单词卡，支持多种来源（文本、链接、视频）。

## 参数
- `content`: 文本内容（可选）
- `link`: 网页链接（可选，联动 LinkLearning）
- `video_url`: 视频链接（可选，联动 VideoSummary）
- `word_count`: 提取数量（可选，默认 10）
- `difficulty`: 难度级别（可选）
- `generate_story`: 是否生成短文（可选，默认 true）

## 返回
- 单词卡列表
- 上下文短文
- 测验题（可选）
- Anki 格式文件（可选）
```

---

## 7. 测试计划

### 7.1 单元测试

| 测试类 | 测试内容 | 测试数量 |
|--------|----------|----------|
| `TestWordExtractor` | 单词提取准确性、难度分类、数量控制 | 25 |
| `TestPhoneticLookup` | 本地查询、API查询、LLM生成、兜底逻辑 | 30 |
| `TestPromptManager` | 模板加载、变量填充、JSON验证 | 15 |
| `TestStoryGenerator` | 短文生成、单词融合、难度控制 | 20 |
| `TestQuizGenerator` | 测验题生成、题型多样性、答案验证 | 15 |
| `TestVocabularyExporter` | Markdown导出、Anki格式、JSON导出 | 20 |
| `TestVocabularyLearningModule` | 完整流程、模块联动 | 25 |

**总计**: 约 130 个单元测试

### 7.2 集成测试

- 从不同来源提取单词（文本、链接、视频）
- 测试不同难度分布
- 测试音标查询准确性
- 测试短文生成质量
- 测试与其他模块联动（LinkLearning、VideoSummary）
- 测试导出格式（Markdown、Anki）

### 7.3 性能测试

- 提取速度: <10s（提取单词）
- 单词卡生成: <20s（包含 LLM 调用）
- 短文生成: <15s
- 音标查询: <1s/word（本地/API）
- 内存占用: <150MB

---

## 8. 实现计划

### 8.1 开发时间表

| 天数 | 任务 | 预计时间 |
|------|------|----------|
| Day 1-2 | WordExtractor 实现 + 测试 | 8小时 |
| Day 3 | PhoneticLookup 实现（本地+API） | 6小时 |
| Day 4 | Prompt 模板设计 + 数据模型 | 6小时 |
| Day 5-6 | LLM 处理 + 单词卡构建 | 10小时 |
| Day 7 | StoryGenerator 实现 + 测试 | 6小时 |
| Day 8 | QuizGenerator 实现（可选） | 4小时 |
| Day 9 | Exporter + Anki 格式支持 | 6小时 |
| Day 10 | 模块联动（LinkLearning、VideoSummary） | 6小时 |
| Day 11-12 | CLI 命令 + Python API | 8小时 |
| Day 13-14 | 测试完善 + 文档 | 10小时 |

**总计**: 约 66 小时（2周）

### 8.2 里程碑

- **Milestone 1**: 单词提取完成（Day 2）
- **Milestone 2**: 单词卡生成完成（Day 6）
- **Milestone 3**: 短文生成完成（Day 7）
- **Milestone 4**: 导出和联动完成（Day 10）
- **Milestone 5**: 测试和文档完成（Day 14）

---

## 9. 风险评估

### 9.1 技术风险

| 风险 | 影响 | 解决方案 |
|------|------|----------|
| 单词提取不准确 | 学习效果差 | LLM提取 + 词频统计双重验证 |
| 音标查询失败 | 单词卡不完整 | 三级查询机制（本地→API→LLM） |
| LLM输出格式错误 | 解析失败 | JSON Schema验证 + 重试 |
| 短文生成质量低 | 记忆效果差 | Prompt优化 + 质量评分 |
| 模块联动失败 | 功能受限 | 错误处理 + 降级方案 |

### 9.2 数据风险

- 本地词典不完整: 使用 API 补充
- API 限制: 缓存机制 + 本地词典
- 停用词误提取: 过滤机制

---

## 10. 未来扩展

### 10.1 短期扩展（v0.3.0）

- 支持更多语言（日语、韩语、法语等）
- Anki 完整导出（带音频）
- 单词发音生成（TTS）
- 记忆曲线追踪（Spaced Repetition）
- 单词本管理（分组、标签）

### 10.2 长期扩展（v1.0.0）

- 单词图谱（关联关系可视化）
- 个性化学习路径
- 社区单词库
- 游戏化学习（测验、挑战）
- 移动端支持

---

## 11. 模块联动设计

### 11.1 与 LinkLearning 联动

```python
# 用户请求：从链接提取单词
result = await extract_vocabulary(
    link="https://example.com/article"
)

# 内部流程：
# 1. 调用 LinkLearning 模块获取知识卡片
link_result = await process_link(url="https://...")

# 2. 从知识卡片的内容中提取单词
vocab_result = await extract_vocabulary(
    content=link_result.summary + "\n" + link_result.key_points
)

# 3. 合并元数据
vocab_result.source_url = link
vocab_result.source_title = link_result.title
```

### 11.2 与 VideoSummary 联动

```python
# 用户请求：从视频提取单词
result = await extract_vocabulary(
    video_url="https://bilibili.com/video/BV123"
)

# 内部流程：
# 1. 调用 VideoSummary 模块获取总结
video_result = await summarize_video(url="https://...")

# 2. 从转录文本和总结中提取单词
vocab_result = await extract_vocabulary(
    content=video_result.transcript + "\n" + video_result.summary
)

# 3. 合并元数据
vocab_result.source_video = video_url
vocab_result.source_title = video_result.title
```

---

## 12. 参考资料

### 12.1 工具文档

- **Free Dictionary API**: https://dictionaryapi.dev/
- **NLTK**: https://www.nltk.org/
- **spaCy**: https://spacy.io/
- **Anki**: https://apps.ankiweb.net/

### 12.2 API 设计参考

- **现有视频总结模块**: `src/learning_assistant/modules/video_summary/`
- **链接学习模块设计**: `docs/link_learning_design.md`

---

**设计完成日期**: 2026-03-31
**版本**: v1.0
**状态**: 设计完成，待实现