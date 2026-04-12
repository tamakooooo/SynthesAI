---
name: vocabulary
description: |
  Extracts vocabulary from text content and generates comprehensive word cards with phonetics, definitions, examples, and contextual stories.

  Use when user:
  - Provides text content for vocabulary extraction
  - Asks to "extract words", "generate word cards", "create vocabulary list"
  - Mentions "单词学习", "词汇提取", "单词卡"
  - Wants to learn vocabulary from articles, videos, or text
  - Needs contextual stories for vocabulary retention

metadata:
  version: 2.0.0
  author: Learning Assistant Team
---

# Vocabulary Learning Skill

Extracts vocabulary from text content and generates comprehensive word cards with phonetics, definitions, examples, and contextual stories.

## Overview

This skill intelligently extracts important vocabulary from text and creates structured learning cards to help with vocabulary acquisition and retention.

**Key Features**:
- ✅ LLM-powered intelligent word extraction
- ✅ Multi-layer phonetic lookup (local dictionary → API → LLM fallback)
- ✅ Complete word cards with definitions, examples, synonyms
- ✅ Contextual story generation for memory retention
- ✅ **Visual knowledge card generation (Editorial style)**
- ✅ **PNG export with high-resolution (2x scaling)**
- ✅ Multiple difficulty levels (beginner/intermediate/advanced)
- ✅ Support for text input, files, or URLs

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| content | string | ✅* | - | Text content to extract words from |
| url | string | ✅* | - | URL to fetch content from (alternative to content) |
| file | Path | ✅* | - | Input file path (alternative to content/url) |
| word_count | integer | ❌ | 10 | Number of words to extract (1-50) |
| difficulty | string | ❌ | intermediate | Target difficulty (beginner/intermediate/advanced) |
| generate_story | boolean | ❌ | true | Generate contextual story |
| generate_card | boolean | ❌ | true | Generate visual knowledge card |
| output_dir | string | ❌ | ./outputs/vocabulary | Output directory |

*One of `content`, `url`, or `file` is required

## Quick Start

### Python API (Recommended)

```python
from learning_assistant.api import extract_vocabulary

# Basic usage - from text
result = await extract_vocabulary(
    content="Machine learning is transforming industries across the globe..."
)

# From URL (NEW!)
result = await extract_vocabulary(
    url="https://example.com/blog/article",
    word_count=15,
    difficulty="advanced"
)

# With options
result = await extract_vocabulary(
    content="Your text content here...",
    word_count=15,
    difficulty="advanced",
    generate_story=True
)

# Access results
print(f"Extracted {len(result['vocabulary_cards'])} words")
for card in result['vocabulary_cards']:
    print(f"- {card['word']}: {card['definition']['zh']}")
```

### Synchronous Version

```python
from learning_assistant.api import extract_vocabulary_sync

result = extract_vocabulary_sync(
    content="Your text content...",
    word_count=10
)
```

### CLI Usage

```bash
# From text
la vocabulary --text "Machine learning is revolutionizing..."

# From URL (NEW!)
la vocabulary --url "https://example.com/article"

# From file
la vocabulary --file article.txt

# With options
la vocabulary --url "https://example.com/blog" \
  --count 15 \
  --difficulty advanced \
  --no-story
```

## Output Format

Returns JSON object:

```json
{
  "status": "success",
  "content": "Machine learning is transforming...",
  "word_count": 10,
  "difficulty": "intermediate",
  "vocabulary_cards": [
    {
      "word": "transform",
      "phonetic": {
        "us": "/trænsˈfɔrm/",
        "uk": "/trænsˈfɔːm/"
      },
      "part_of_speech": "verb",
      "definition": {
        "zh": "改变，转变",
        "en": "to change completely the form or appearance"
      },
      "example_sentences": [
        {
          "sentence": "Machine learning is transforming industries.",
          "translation": "机器学习正在改变各行各业。",
          "context": "原文提取"
        },
        {
          "sentence": "The company transformed its business model.",
          "translation": "公司转变了其商业模式。",
          "context": "LLM生成"
        }
      ],
      "synonyms": ["change", "convert", "alter"],
      "antonyms": ["maintain", "preserve"],
      "related_words": ["transformation", "transformative"],
      "difficulty": "intermediate",
      "frequency": "high"
    }
  ],
  "context_story": {
    "title": "The Transformative Power of Technology",
    "content": "In recent years, machine learning has been transforming...",
    "word_count": 300,
    "difficulty": "intermediate",
    "target_words": ["transform", "revolution", "innovation", ...]
  },
  "statistics": {
    "total_words": 10,
    "difficulty_distribution": {
      "beginner": 3,
      "intermediate": 5,
      "advanced": 2
    }
  },
  "files": {
    "markdown_path": "./outputs/vocabulary_20260408.md",
    "html_path": "./outputs/vocabulary_20260408.html",
    "png_path": "./outputs/vocabulary_20260408.png"
  },
  "timestamp": "2026-04-08T10:30:00"
}
```

## Execution Steps

1. **Word Extraction** (LLM) - Analyze content, identify important words based on frequency, importance, and context
2. **Phonetic Lookup** (Multi-layer) - Fetch phonetics via local dictionary → API → LLM fallback
3. **Card Generation** (LLM) - Generate complete word cards with definitions, examples, synonyms
4. **Story Creation** (LLM, optional) - Create contextual story containing target words
5. **Visual Card Generation** (HTML+PNG, optional) - Generate Editorial-style visual knowledge card
   - Build HTML template with word grid, story, and detail panels
   - Render PNG image using Playwright (2x scaling for high DPI)
6. **Export** - Save to Markdown/JSON/HTML/PNG format with history tracking

## Performance

| Metric | Value |
|--------|-------|
| Extraction time | < 30s (10 words) |
| Phonetic lookup | < 2s per word (cached: instant) |
| Story generation | < 20s (300 words) |
| Total time | < 60s for typical use case |
| Memory usage | < 100MB |

## Configuration

Default configuration in `config/modules.yaml`:

```yaml
vocabulary:
  enabled: true
  priority: 3

  config:
    extraction:
      word_count: 10
      difficulty_distribution:
        beginner: 30%
        intermediate: 50%
        advanced: 20%
      min_word_length: 3
      exclude_stopwords: true

    phonetic:
      lookup_order: [local, api, llm]
      local_dictionary: "data/dictionaries/english.json"
      api_url: "https://api.dictionaryapi.dev/api/v2/entries/en/"

    llm:
      provider: "openai"
      model: "gpt-4"
      temperature: 0.3
      max_tokens: 2000

    story:
      enabled: true
      default_word_count: 300
      default_difficulty: "intermediate"

    output:
      format: [markdown, json]
      directory: "data/outputs/vocabulary"
      save_history: true
```

## Advanced Usage

### Using Different LLM Providers

```python
# OpenAI GPT-4
result = await extract_vocabulary(
    content="Your text...",
    llm={"provider": "openai", "model": "gpt-4-turbo"}
)

# Anthropic Claude
result = await extract_vocabulary(
    content="Your text...",
    llm={"provider": "anthropic", "model": "claude-3-opus-20240229"}
)

# DeepSeek
result = await extract_vocabulary(
    content="Your text...",
    llm={"provider": "deepseek", "model": "deepseek-chat"}
)
```

### Batch Processing

```python
import asyncio
from learning_assistant.api import extract_vocabulary

texts = [
    "Text 1 content...",
    "Text 2 content...",
    "Text 3 content...",
]

async def process_batch():
    tasks = [
        extract_vocabulary(content=text, word_count=5, generate_story=False)
        for text in texts
    ]
    results = await asyncio.gather(*tasks)

    total_words = sum(len(r['vocabulary_cards']) for r in results)
    print(f"Total words extracted: {total_words}")

asyncio.run(process_batch())
```

### Custom Output Directory

```python
result = await extract_vocabulary(
    content="Your text...",
    output_dir="./my-vocabulary-cards"
)

print(f"Saved to: {result['files']['markdown_path']}")
```

## Limitations

1. **Language Support**: Optimized for English, basic support for other languages
2. **Phonetic Accuracy**: Depends on dictionary data availability
3. **Content Length**: Very long texts (>10,000 words) may need splitting
4. **Story Quality**: Story coherence depends on LLM model capability
5. **URL Fetching**: Some websites may block fetching (403 errors) - use alternative sources or provide text directly

## URL Support Notes

When using `url` parameter:
- Content is fetched using aiohttp (fast, simple HTTP client)
- Trafilatura extracts clean text from HTML
- Minimum content length: 100 characters (configurable)
- Some websites with anti-bot measures may return 403/404 errors
- Alternative: Manually copy-paste text and use `content` parameter

## Error Handling

```python
from learning_assistant.api import extract_vocabulary

try:
    result = await extract_vocabulary(content="Your text...")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"Processing failed: {e}")
```

## Examples

### Example 1: Technical Article

```python
result = await extract_vocabulary(
    content="""
    Machine learning algorithms have revolutionized data analysis.
    Neural networks, a subset of machine learning, mimic the human brain's
    architecture to process complex patterns...
    """,
    word_count=10,
    difficulty="advanced"
)

# Expected output: Technical vocabulary like "neural networks", "architecture",
# "patterns", "algorithms", etc.
```

### Example 2: News Article

```python
result = await extract_vocabulary(
    content="""
    The global economy faces unprecedented challenges as inflation rates
    continue to rise. Central banks are implementing monetary policies...
    """,
    word_count=8,
    difficulty="intermediate"
)

# Expected output: General vocabulary like "unprecedented", "inflation",
# "monetary", "policies", etc.
```

### Example 3: Story Generation Only

```python
# Extract words first
words_result = await extract_vocabulary(
    content="Your text...",
    word_count=10,
    generate_story=False
)

# Generate story with specific theme
from learning_assistant.modules.vocabulary.story_generator import StoryGenerator

story = await story_generator.generate(
    words=[card['word'] for card in words_result['vocabulary_cards']],
    theme="Science Fiction",
    word_count=500,
    difficulty="intermediate"
)
```

## Visual Knowledge Cards

### Overview

The vocabulary module generates Editorial-style visual knowledge cards suitable for sharing and learning. These cards feature:

- **Editorial Layout**: Magazine-style design with careful typography
- **Claude Colors**: Orange (#FF6B35) and purple (#764BA2) accent colors
- **1200px Width**: Optimized for social media and presentation
- **High Resolution**: 2x scaling for crisp display on high DPI devices

### Card Layout

```
┌─────────────────────────────────────────┐
│ Hero Section                             │
│ 核心单词大字展示 (48px Playfair Display) │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ Story Section (深色面板)                  │
│ 上下文故事（英文为主 + 重点单词中文释义）   │
└─────────────────────────────────────────┘
┌─────────────────────┬───────────────────┐
│ Word List (左侧)    │ Word Focus (右侧) │
│ 10个单词简要展示     │ 6个单词详细解释   │
│ (序号+单词+音标+    │ (序号+单词+释义   │
│  词性+释义)         │  +例句)           │
└─────────────────────┴───────────────────┘
┌─────────────────────────────────────────┐
│ Bottom Bar + Footer                      │
│ 统计信息 + SynthesAI branding             │
└─────────────────────────────────────────┘
```

### Generation Options

```python
result = await extract_vocabulary(
    content="Your text...",
    generate_card=True,  # Enable visual card generation
)

# Access generated files
html_path = result['files']['html_path']
png_path = result['files']['png_path']
```

### Requirements

Visual card generation requires **Playwright** for PNG rendering:

```bash
pip install playwright
playwright install chromium
```

If Playwright is not installed, HTML cards will still be generated (can be opened in browser for manual screenshot).

### Card Sizes

| Component | Size |
|-----------|------|
| Card width | 1200px (fixed) |
| Hero font | 48px Playfair Display |
| Story font | 14px Noto Sans SC |
| Word list font | 17px (words) + 13px (info) |
| Word focus font | 17px (words) + 13px (defs) |
| PNG resolution | 2400x2500px (2x scaling) |
| PNG file size | ~180KB (high quality) |

## Related Skills

- **video-summary** - Extract vocabulary from video transcriptions
- **link-learning** - Extract vocabulary from web articles
- **video-summary** → **vocabulary** pipeline - Full learning workflow

## See Also

- [User Guide](../../docs/vocabulary_user_guide.md) - Detailed usage documentation
- [API Reference](../../docs/api.md) - Complete API documentation
- [Configuration Guide](../../docs/CONFIGURATION.md) - Configuration options

---

**Version**: 2.0.0
**Last Updated**: 2026-04-11
**Maintainer**: Learning Assistant Team