---
name: learning-history
description: |
  Queries learning history records including video summaries and learning activities.
  
  Use when user:
  - Asks "what have I learned", "show my history", "recent learning"
  - Wants to search past learning records
  - Mentions "学习历史", "最近学习", "历史记录"
  - Requests to review or find previous learning content
metadata:
  version: 1.1.0
  author: Learning Assistant Team
---

# Learning History Skill

Queries learning history records from Learning Assistant.

## HTTP API Usage (For Agents)

**Server Base URL**: `http://localhost:8000` (or your configured server address)

### Get Recent History

```http
GET /api/v1/history?limit=10
```

### Search History

```http
GET /api/v1/history?search=Python&limit=20
```

### Filter by Module

```http
GET /api/v1/history?module=video_summary&limit=10
```

**Response**:
```json
[
  {
    "id": "rec_001",
    "module": "video_summary",
    "title": "Python Programming Tutorial",
    "url": "https://www.bilibili.com/video/BV...",
    "timestamp": "2026-03-31T10:00:00",
    "status": "completed"
  }
]
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | int | ❌ | 10 | Number of records (1-100) |
| search | string | ❌ | - | Search keyword (title match) |
| module | string | ❌ | - | Filter by module (video_summary/link_learning/vocabulary) |

### Get Statistics

```http
GET /api/v1/statistics
```

**Response**:
```json
{
  "total_records": 50,
  "video_summaries": 30,
  "link_learning": 15,
  "vocabulary": 5,
  "success_rate": 0.95
}
```

## Record Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique record identifier |
| module | string | Module name |
| title | string | Video title or learning topic |
| url | string | Video URL or resource link |
| timestamp | string | ISO 8601 timestamp |
| status | string | Status (completed/in_progress/failed) |

## Performance

- Query performance: O(n) where n = total records
- Recommend `limit` ≤ 100

## Python API (Alternative)

```python
from learning_assistant.api import get_recent_history
records = get_recent_history(limit=10)
```

## Related Skills

- [video-summary](../video-summary/SKILL.md) - Creates history records
- [list-skills](../list-skills/SKILL.md) - List available skills