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
  version: 2.2.0
  author: Learning Assistant Team
  hermes:
    platforms: [cli, telegram, discord, matrix, signal, weixin]
    media_support: true
---

# Vocabulary Learning Skill

Extracts vocabulary from text content and generates comprehensive word cards with phonetics, definitions, examples, and contextual stories.

## 🖼️ Visual Card Delivery (Hermes Agent)

Generated PNG visual cards can be sent via Hermes `send_message`:

```json
{
  "action": "send",
  "target": "telegram",
  "message": "这是你的词汇学习卡片:\nMEDIA:/tmp/vocabulary_card.png"
}
```

**Supported Media Platforms**: Telegram, Discord, Matrix, Signal, Weixin, Yuanbao

## HTTP API Usage (For Agents)

**Server Base URL**: `http://localhost:8000` (or your configured server address)

### Single Request (Synchronous)

```http
POST /api/v1/vocabulary
Content-Type: application/json

{
  "content": "Machine learning is transforming industries across the globe...",
  "word_count": 10,
  "difficulty": "intermediate",
  "generate_story": true
}
```

Or from URL:
```http
POST /api/v1/vocabulary
Content-Type: application/json

{
  "url": "https://example.com/article",
  "word_count": 15,
  "difficulty": "advanced"
}
```

**Response** (20-60 seconds):
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
        "en": "to change completely"
      },
      "example_sentences": [
        {
          "sentence": "Machine learning is transforming industries.",
          "translation": "机器学习正在改变各行各业。"
        }
      ],
      "synonyms": ["change", "convert"],
      "difficulty": "intermediate"
    }
  ],
  "context_story": {
    "title": "The Transformative Power",
    "content": "In recent years..."
  },
  "files": {
    "markdown_path": "./outputs/vocabulary.md",
    "png_path": "./outputs/vocabulary.png"
  }
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| content | string | ✅* | - | Text content to extract from |
| url | string | ✅* | - | URL to fetch content from |
| word_count | integer | ❌ | 10 | Number of words (1-50) |
| difficulty | string | ❌ | intermediate | Level (beginner/intermediate/advanced) |
| generate_story | boolean | ❌ | true | Generate context story |

*One of `content` or `url` is required

## Key Features

- ✅ LLM-powered intelligent word extraction
- ✅ Multi-layer phonetic lookup
- ✅ Complete word cards with definitions, examples, synonyms
- ✅ Contextual story generation for memory retention
- ✅ Visual knowledge card (PNG export)

## Performance

| Metric | Value |
|--------|-------|
| Extraction | < 30s (10 words) |
| Story generation | < 20s |
| Total time | 20-60s |

## Error Handling

- `400 ValidationError`: Missing content/url or invalid parameters
- `500 InternalError`: Processing failed

## Python API (Alternative)

```python
from learning_assistant.api import extract_vocabulary

result = await extract_vocabulary(
    content="Your text...",
    word_count=10
)
```

## Related Skills

- [video-summary](../video-summary/SKILL.md) - Video content summarization
- [link-learning](../link-learning/SKILL.md) - Web article knowledge extraction