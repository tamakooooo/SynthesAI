---
name: link-learning
description: |
  Extracts knowledge from web links and generates structured knowledge cards with Q&A and quizzes.

  Use when user:
  - Provides article/blog URLs
  - Asks to "summarize this article", "analyze this page", "extract knowledge from link"
  - Mentions "链接学习", "知识卡片", "文章总结"
  - Requests learning cards or Q&A generation from web content
metadata:
  version: 1.0.0
  author: Learning Assistant Team
---

# Link Learning Skill

Extracts knowledge from web links and generates structured knowledge cards with Q&A and quizzes.

## Supported Content Types

- News articles
- Blog posts
- Technical documentation
- Academic papers
- Tutorial pages

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | ✅ | - | Web URL to process |
| provider | string | ❌ | openai | LLM provider (openai/anthropic/deepseek) |
| model | string | ❌ | gpt-4 | LLM model to use |
| output_dir | string | ❌ | ./outputs | Output directory |
| generate_quiz | boolean | ❌ | true | Generate quiz questions |
| format | string | ❌ | markdown | Output format (markdown/json) |

## Quick Start

### Python API (Recommended)

```python
from learning_assistant.api import process_link

# Basic usage
result = await process_link(
    url="https://example.com/article"
)

# With options
result = await process_link(
    url="https://blog.example.com/tutorial",
    provider="openai",
    model="gpt-4",
    generate_quiz=True,
    output_dir="./my-notes"
)

# Access results
print(result["title"])
print(result["summary"])
for point in result["key_points"]:
    print(f"- {point}")
```

### Synchronous Version

```python
from learning_assistant.api import process_link_sync

result = process_link_sync(url="https://example.com/article")
```

### CLI Usage

```bash
# Basic usage
la link https://example.com/article

# With options
la link https://example.com/article \
  --provider openai \
  --model gpt-4 \
  --output article.md

# JSON output
la link https://example.com/article \
  --output article.json \
  --format json

# Skip quiz generation
la link https://example.com/article --no-quiz
```

## Output Format

Returns JSON object:

```json
{
  "status": "success",
  "url": "https://example.com/article",
  "title": "Understanding Machine Learning",
  "source": "example.com",
  "summary": "This article introduces machine learning concepts...",
  "key_points": [
    "Machine learning definition and applications",
    "Supervised vs unsupervised learning",
    "Common algorithms and selection criteria"
  ],
  "tags": ["AI", "Machine Learning", "Tutorial"],
  "word_count": 3500,
  "reading_time": "14分钟",
  "difficulty": "intermediate",
  "qa_pairs": [
    {
      "question": "What is machine learning?",
      "answer": "Machine learning is a technique that allows computers to learn patterns from data...",
      "difficulty": "medium"
    }
  ],
  "quiz": [
    {
      "type": "multiple_choice",
      "question": "Which is a typical application of supervised learning?",
      "options": ["A. Image classification", "B. Clustering", "C. Anomaly detection", "D. Dimensionality reduction"],
      "correct": "A",
      "explanation": "Image classification uses labeled data to train models..."
    }
  ],
  "files": {
    "markdown_path": "./outputs/article.md",
    "json_path": "./outputs/article.json"
  },
  "timestamp": "2026-03-31T10:00:00"
}
```

## Execution Steps

1. **Fetch content** (aiohttp/trafilatura) - Download HTML, handle retries, support proxies
2. **Parse content** (trafilatura) - Extract main content, title, author, remove ads/noise
3. **Generate knowledge card** (LLM) - Use prompt template, call LLM API, parse JSON
4. **Create Q&A** (LLM) - Generate question-answer pairs based on content
5. **Generate quiz** (LLM) - Create quiz questions with multiple choice options
6. **Export output** - Render Markdown/JSON template, save to file

## Performance

| Metric | Value |
|--------|-------|
| Fetch time | <5s |
| Parse time | <1s |
| LLM processing | <30s |
| Total time | <40s |
| Memory usage | <150MB |

## Configuration

Default configuration in `config/modules.yaml`:

```yaml
link_learning:
  enabled: true
  priority: 2

  config:
    fetcher:
      timeout: 30
      max_retries: 3
      use_playwright: false

    parser:
      engine: "trafilatura"
      include_comments: false
      include_tables: true
      min_content_length: 200

    llm:
      provider: "openai"
      model: "gpt-4"
      temperature: 0.3
      max_tokens: 2000

    features:
      generate_qa: true
      generate_quiz: true
      extract_tags: true
      estimate_difficulty: true
```

## Advanced Usage

### Using Different LLM Providers

```python
# Anthropic Claude
result = await process_link(
    url="https://example.com/article",
    provider="anthropic",
    model="claude-3-opus-20240229"
)

# DeepSeek
result = await process_link(
    url="https://example.com/article",
    provider="deepseek",
    model="deepseek-chat"
)
```

### Custom Output

```python
# Save to custom directory
result = await process_link(
    url="https://example.com/article",
    output_dir="./my-knowledge-base"
)

# JSON format for programmatic processing
result = await process_link(
    url="https://example.com/article",
    format="json"
)
```

### Batch Processing

```python
import asyncio
from learning_assistant.api import process_link

urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]

# Process concurrently
tasks = [process_link(url) for url in urls]
results = await asyncio.gather(*tasks)

for result in results:
    print(f"{result['title']}: {result['word_count']} words")
```

## Limitations

1. **Dynamic pages** - Requires Playwright for JavaScript-rendered content (optional dependency)
2. **Paywalls** - Cannot access content behind authentication or paywalls
3. **Minimum length** - Default minimum 200 words
4. **Language support** - Optimized for Chinese and English

### Enabling Dynamic Page Support

```bash
# Install Playwright
pip install playwright
playwright install

# Update configuration
# config/modules.yaml
link_learning:
  config:
    fetcher:
      use_playwright: true
```

## Error Handling

```python
from learning_assistant.api import process_link

try:
    result = await process_link(url="https://example.com/article")
except ValueError as e:
    print(f"Invalid URL: {e}")
except RuntimeError as e:
    print(f"Processing failed: {e}")
```

## Examples

### Example 1: Technical Blog

```python
result = await process_link(
    url="https://blog.python.org/2024/01/new-features.html"
)

print(f"Title: {result['title']}")
print(f"Difficulty: {result['difficulty']}")
print(f"Key Points: {len(result['key_points'])}")
```

### Example 2: News Article

```python
result = await process_link(
    url="https://news.example.com/tech/ai-breakthrough",
    generate_quiz=False  # Skip quiz for faster processing
)

print(result['summary'])
```

### Example 3: Academic Paper

```python
result = await process_link(
    url="https://arxiv.org/abs/2401.12345",
    model="gpt-4",  # Use most capable model
    output_dir="./papers"
)

# Access generated files
print(f"Markdown: {result['files']['markdown_path']}")
```

## Related Skills

- **video-summary** - Summarize video content from URLs
- **vocabulary-learning** - Extract vocabulary from content (planned)

## See Also

- [CLI Guide](../../docs/link_learning_cli_guide.md) - Full CLI documentation
- [API Reference](../../docs/api.md) - Complete API documentation
- [Architecture](../../docs/ARCHITECTURE.md) - System architecture

---

**Version**: 1.0.0
**Last Updated**: 2026-03-31
**Maintainer**: Learning Assistant Team