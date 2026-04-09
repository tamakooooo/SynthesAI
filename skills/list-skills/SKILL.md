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
  version: 1.0.0
  author: Learning Assistant Team
---

# List Skills Skill

Lists all available Learning Assistant skills with descriptions and status.

## Inputs

No parameters required.

## Quick Start

### Python API

```python
from learning_assistant.api import list_available_skills

skills = list_available_skills()

for skill in skills:
    print(f"- {skill['name']}: {skill['description']}")
```

### Using AgentAPI

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()
skills = api.list_skills()

# Check if skill is available
skill_names = [s.name for s in skills]

if "video-summary" in skill_names:
    print("✅ video-summary is available")
```

## Output Format

Returns list of dictionaries:

```json
[
  {
    "name": "video-summary",
    "description": "Summarizes video content from URLs",
    "version": "1.0.0",
    "status": "available"
  },
  {
    "name": "list-skills",
    "description": "Lists all available skills",
    "version": "1.0.0",
    "status": "available"
  },
  {
    "name": "learning-history",
    "description": "Views learning history records",
    "version": "1.0.0",
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

## Use Cases

### 1. Skill Discovery

Help users discover available capabilities:

```python
from learning_assistant.api import list_available_skills

def show_capabilities():
    skills = list_available_skills()
    
    response = "Learning Assistant provides these skills:\n\n"
    
    for skill in skills:
        if skill['status'] == 'available':
            response += f"✅ {skill['name']}: {skill['description']}\n"
    
    return response
```

### 2. Availability Check

Check if a specific skill is available before using:

```python
from learning_assistant.api import list_available_skills

def check_skill_availability(skill_name: str):
    skills = list_available_skills()
    skill_names = [s['name'] for s in skills]
    
    return skill_name in skill_names

# Usage
if check_skill_availability("video-summary"):
    # Use the skill
    result = await summarize_video(url="...")
else:
    print("video-summary skill not available")
```

### 3. Agent Initialization

Agent can discover available skills at startup:

```python
from learning_assistant.api import list_available_skills

def initialize_agent():
    skills = list_available_skills()
    
    print("Agent initialized with skills:")
    for skill in skills:
        print(f"  - {skill['name']} ({skill['status']})")
    
    return skills
```

## Performance

This skill executes very fast (<10ms), can be called frequently.

## Error Handling

Rarely fails, but handle gracefully:

```python
from learning_assistant.api import list_available_skills

try:
    skills = list_available_skills()
except Exception as e:
    print(f"Failed to list skills: {e}")
    skills = []  # Fallback to empty list
```

## Related Skills

- [video-summary](../video-summary/SKILL.md) - Video summarization
- [learning-history](../learning-history/SKILL.md) - Learning history

---

**Need help?**
- GitHub Issues: [learning-assistant/issues](https://github.com/yourname/learning-assistant/issues)