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
  version: 1.2.0
  author: Learning Assistant Team
  hermes:
    platforms: [cli, telegram, discord, matrix, signal, weixin]
    media_support: true
---

# Link Learning Skill

Extracts knowledge from web links and generates structured knowledge cards with Q&A and quizzes.

## 🖼️ Visual Card Delivery (Hermes Agent)

Generated PNG knowledge cards can be sent via Hermes `send_message`:

```json
{
  "action": "send",
  "target": "telegram",
  "message": "这是你的知识卡片:\nMEDIA:/tmp/link_card.png"
}
```

**Supported Media Platforms**: Telegram, Discord, Matrix, Signal, Weixin, Yuanbao

## HTTP API Usage (For Agents)

**Server Base URL**: `http://localhost:8000` (or your configured server address)

### Single Request (Synchronous)

```http
POST /api/v1/link
Content-Type: application/json

{
  "url": "https://example.com/article",
  "provider": "openai",
  "generate_quiz": true
}
```

**Response** (15-45 seconds):
```json
{
  "status": "success",
  "url": "https://example.com/article",
  "title": "Understanding Machine Learning",
  "source": "example.com",
  "summary": "This article introduces...",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "tags": ["AI", "Machine Learning"],
  "word_count": 3500,
  "reading_time": "14分钟",
  "difficulty": "intermediate",
  "qa_pairs": [
    {
      "question": "What is machine learning?",
      "answer": "Machine learning is...",
      "difficulty": "medium"
    }
  ],
  "quiz": [
    {
      "type": "multiple_choice",
      "question": "Which is a typical application?",
      "options": ["A. Image classification", "B. Clustering"],
      "correct": "A"
    }
  ],
  "files": {
    "markdown_path": "./outputs/article.md"
  }
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | ✅ | - | Web URL to process |
| provider | string | ❌ | openai | LLM provider (openai/anthropic/deepseek) |
| model | string | ❌ | - | LLM model (uses default if not specified) |
| output_dir | string | ❌ | - | Output directory |
| generate_quiz | boolean | ❌ | true | Generate quiz questions |

## Supported Content Types

- News articles
- Blog posts
- Technical documentation
- Academic papers
- Tutorial pages

## Performance

| Metric | Value |
|--------|-------|
| Fetch time | <5s |
| LLM processing | <30s |
| Total time | 15-45s |

## Error Handling

- `400 ValidationError`: Invalid URL or missing content
- `500 InternalError`: Processing failed

## Python API (Alternative)

```python
from learning_assistant.api import process_link

result = await process_link(url="https://example.com/article")
print(result["title"])
```

## Related Skills

- [video-summary](../video-summary/SKILL.md) - Video content summarization
- [vocabulary](../vocabulary/SKILL.md) - Vocabulary extraction