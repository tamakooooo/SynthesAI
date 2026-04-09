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
  version: 1.0.0
  author: Learning Assistant Team
---

# Learning History Skill

Queries learning history records from Learning Assistant.

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | int | ❌ | 10 | Number of records to return |
| search | string | ❌ | - | Search keyword (title match) |
| module | string | ❌ | - | Filter by module (video_summary/link_learning) |

## Quick Start

### Python API

```python
from learning_assistant.api import get_recent_history

# Get recent 10 records
records = get_recent_history(limit=10)

for record in records:
    print(f"[{record['timestamp']}] {record['title']}")
```

### Using AgentAPI

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# Get history with filters
records = api.get_history(
    limit=20,
    search="Python",
    module="video_summary"
)
```

## Output Format

Returns list of dictionaries:

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

## Record Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique record identifier |
| module | string | Module name (video_summary/link_learning) |
| title | string | Video title or learning topic |
| url | string | Video URL or resource link |
| timestamp | string | ISO 8601 timestamp |
| status | string | Status (completed/in_progress/failed) |

## Use Cases

### 1. View Recent Learning

```python
from learning_assistant.api import get_recent_history

records = get_recent_history(limit=5)

print("📚 Recent learning:")
for record in records:
    status_emoji = "✅" if record['status'] == 'completed' else "⏳"
    print(f"{status_emoji} {record['title']}")
```

### 2. Search History

Find previously learned content:

```python
from learning_assistant.api import get_recent_history

def find_previous_learning(topic: str):
    records = get_recent_history(search=topic)
    
    if records:
        print(f"Found {len(records)} records about '{topic}':")
        for record in records:
            print(f"  - {record['title']}")
    else:
        print(f"No records found for '{topic}'")

# Usage
find_previous_learning("Python")
```

### 3. Module Filtering

Filter by specific learning type:

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# Only video summaries
video_records = api.get_history(module="video_summary")

# Only link learning
link_records = api.get_history(module="link_learning")
```

### 4. Learning Statistics

Calculate learning statistics:

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

def show_learning_stats():
    records = api.get_history(limit=1000)  # Get many records
    
    total = len(records)
    completed = len([r for r in records if r.status == 'completed'])
    
    print(f"📊 Learning Statistics:")
    print(f"  Total records: {total}")
    print(f"  Completed: {completed}")
    print(f"  Success rate: {completed/total*100:.1f}%")

show_learning_stats()
```

### 5. Learning Streak Check

Check learning continuity:

```python
from learning_assistant.api import get_recent_history
from datetime import datetime, timedelta

def check_learning_streak():
    records = get_recent_history(limit=7)
    
    if len(records) < 7:
        print("⚠️ You've been learning less recently. Keep it up!")
    else:
        print("✅ Great learning habit! Keep going!")

check_learning_streak()
```

## Performance

- Query performance: O(n) where n = total records
- Recommend `limit` ≤ 1000 to avoid performance issues
- Search uses simple string matching (no regex)

## Data Retention

- History records stored locally in `data/history/history.json`
- Records persist indefinitely by default
- Can manually clean old records:

```bash
# Clean records older than 30 days
find data/history -mtime +30 -type f -delete
```

## Privacy

All history data stored locally, never uploaded to cloud.

## Error Handling

```python
from learning_assistant.api import get_recent_history

try:
    records = get_recent_history(limit=10)
except Exception as e:
    print(f"Failed to get history: {e}")
    records = []  # Fallback
```

## Advanced Usage

### Export History

```python
import json
from learning_assistant.api import get_recent_history

records = get_recent_history(limit=1000)

# Export to JSON
with open('learning_history_export.json', 'w') as f:
    json.dump(records, f, indent=2)

print("History exported!")
```

### History Analysis

```python
from learning_assistant.api import AgentAPI
from collections import Counter

api = AgentAPI()
records = api.get_history(limit=100)

# Most common platforms
platforms = [r.url.split('/')[2] for r in records]
platform_counts = Counter(platforms)

print("Most watched platforms:")
for platform, count in platform_counts.most_common(5):
    print(f"  {platform}: {count} videos")
```

## Related Skills

- [video-summary](../video-summary/SKILL.md) - Creates history records
- [list-skills](../list-skills/SKILL.md) - List available skills

---

**Need help?**
- GitHub Issues: [learning-assistant/issues](https://github.com/yourname/learning-assistant/issues)