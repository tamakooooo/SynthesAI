---
name: list-skills
description: |
  Lists all available Learning Assistant skills and their capabilities.
  
  Use when user:
  - Asks "what can you do", "what skills do you have", "show me your capabilities"
  - Wants to discover available functions
  - Mentions "列出技能", "可用功能", "技能列表"
  - Needs to check if a specific skill exists
metadata:
  version: 1.1.0
  author: Learning Assistant Team
---

# List Skills Skill

Lists all available Learning Assistant skills with descriptions and status.

## HTTP API Usage (For Agents)

**Server Base URL**: `http://localhost:8000` (or your configured server address)

```http
GET /api/v1/skills
```

**Response**:
```json
[
  {
    "name": "video-summary",
    "description": "Summarizes video content from URLs",
    "version": "1.0.0",
    "status": "available"
  },
  {
    "name": "link-learning",
    "description": "Extracts knowledge from web links",
    "version": "1.0.0",
    "status": "available"
  },
  {
    "name": "vocabulary",
    "description": "Extracts vocabulary from text",
    "version": "2.0.0",
    "status": "available"
  }
]
```

## Skill Status

| Status | Meaning |
|--------|---------|
| `available` | Skill is enabled and ready to use |
| `disabled` | Skill is disabled in configuration |
| `error` | Skill failed to load |

## Performance

Very fast (<10ms), can be called frequently.

## Python API (Alternative)

```python
from learning_assistant.api import list_available_skills
skills = list_available_skills()
```

## Related Skills

- [video-summary](../video-summary/SKILL.md) - Video summarization
- [learning-history](../learning-history/SKILL.md) - Learning history