# Learning Assistant Skills

> **Version**: v0.3.1
> **Last Updated**: 2026-04-25

Claude Code Skills for Learning Assistant - standardized, reusable capabilities following the Claude Code Skills Specification (2026).

---

## What are Skills?

Skills are modular, reusable capabilities packaged as standardized `SKILL.md` files. Each skill provides specialized instructions that Claude can automatically invoke when needed.

**Key Features**:
- ✅ **HTTP API based** - Skills use HTTP endpoints, easy for agents to call
- ✅ **Automatic invocation** - Claude activates skills based on context matching
- ✅ **Slash command support** - Manual invocation via `/skill-name`
- ✅ **Composable** - Multiple skills can work together

---

## Available Skills

| Skill | Description | API Endpoint | Status |
|-------|-------------|--------------|--------|
| [video-summary](video-summary/SKILL.md) | Summarizes video content (B站/YouTube/抖音) | `/api/v1/video/submit` (async) | ✅ Available |
| [link-learning](link-learning/SKILL.md) | Extracts knowledge from web links | `/api/v1/link` (sync) | ✅ Available |
| [vocabulary](vocabulary/SKILL.md) | Extracts vocabulary from text/URL | `/api/v1/vocabulary` (sync) | ✅ Available |
| [list-skills](list-skills/SKILL.md) | Lists all available skills | `/api/v1/skills` | ✅ Available |
| [learning-history](learning-history/SKILL.md) | Queries learning history | `/api/v1/history` | ✅ Available |

---

## Quick Start (For Agents)

**Server Base URL**: `http://localhost:8000`

### Video Summary (Async - 3-10 min)

```http
POST /api/v1/video/submit
Content-Type: application/json

{"url": "https://www.bilibili.com/video/BV..."}
```

Returns `task_id`, then poll `/api/v1/video/{task_id}/status` for progress.

### Link Learning (Sync - 15-45s)

```http
POST /api/v1/link
Content-Type: application/json

{"url": "https://example.com/article"}
```

### Vocabulary (Sync - 20-60s)

```http
POST /api/v1/vocabulary
Content-Type: application/json

{"content": "Your text here...", "word_count": 10}
```

---

## Performance Characteristics

| Skill | Execution Time | Type |
|-------|---------------|------|
| video-summary | 3-14 min | Async (task queue) |
| link-learning | 15-45s | Sync |
| vocabulary | 20-60s | Sync |
| list-skills | <10ms | Sync |
| learning-history | <100ms | Sync |

---

## Skill Structure

Each skill follows the Claude Code Skills standard:

```
skill-name/
├── SKILL.md                    # Required: Main skill file
└── references/                 # Optional: Detailed documentation
```

### SKILL.md Format

**YAML Frontmatter** (metadata):
```yaml
---
name: skill-name
description: |
  What the skill does + when to use it.
  Includes trigger phrases for automatic activation.
metadata:
  version: 1.0.0
---
```

**Markdown Body** (instructions):
- HTTP API usage with endpoints
- Request/Response formats
- Parameters and examples

---

## Resources

- **Skills Documentation**: This directory
- **API Reference**: `/api/v1/*` endpoints
- **Claude Code Skills Spec**: [Anthropic Docs](https://docs.anthropic.com/claude-code/skills)

---

**Need Help?**
- GitHub Issues: [learning-assistant/issues](https://github.com/yourname/learning-assistant/issues)