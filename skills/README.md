# Learning Assistant Skills

> **Version**: v0.3.2
> **Last Updated**: 2026-04-27

Claude Code Skills for Learning Assistant - standardized, reusable capabilities following the Claude Code Skills Specification (2026).

---

## ⚠️ Prerequisites: yutto Installation (Required for B站 Videos)

**Before using video-summary for B站 videos, install yutto:**

```bash
pip install yutto>=2.2.0
yutto --version  # Verify installation
```

| Platform | Downloader | Notes |
|----------|------------|-------|
| **B站** | yutto CLI | Required - handles WBI signature & CDN |
| **YouTube** | yt-dlp | Built-in |
| **抖音** | yt-dlp | Built-in |

> **Why yutto is mandatory for B站:**
> - B站 videos require WBI signature (yutto handles automatically)
> - yt-dlp often fails with SSL/CDN timeout errors
> - yutto provides stable, authenticated downloads

---

## What are Skills?

Skills are modular, reusable capabilities packaged as standardized `SKILL.md` files. Each skill provides specialized instructions that Claude can automatically invoke when needed.

**Key Features**:
- ✅ **HTTP API based** - Skills use HTTP endpoints, easy for agents to call
- ✅ **Automatic invocation** - Claude activates skills based on context matching
- ✅ **Slash command support** - Manual invocation via `/skill-name`
- ✅ **Composable** - Multiple skills can work together
- ✅ **Hermes Agent compatible** - Works with Hermes messaging platforms
- ✅ **Media support** - QR codes and visual cards can be sent as images

---

## Available Skills

| Skill | Description | API Endpoint | Status |
|-------|-------------|--------------|--------|
| [video-summary](video-summary/SKILL.md) | Summarizes video content (B站/YouTube/抖音) + QR auth | `/api/v1/video/submit` (async) | ✅ Available |
| [link-learning](link-learning/SKILL.md) | Extracts knowledge from web links | `/api/v1/link` (sync) | ✅ Available |
| [vocabulary](vocabulary/SKILL.md) | Extracts vocabulary from text/URL | `/api/v1/vocabulary` (sync) | ✅ Available |
| [list-skills](list-skills/SKILL.md) | Lists all available skills | `/api/v1/skills` | ✅ Available |
| [learning-history](learning-history/SKILL.md) | Queries learning history | `/api/v1/history` | ✅ Available |
| [synthesai](synthesai/SKILL.md) | Hermes Agent integration guide | - | ✅ Available |

---

## 🔐 Authentication Skills

### B站 Login (QR Code)

For videos requiring login, use QR authentication:

```bash
la auth login --platform bilibili
```

**Hermes Agent**: Send QR image with `send_message`:
```json
{
  "action": "send",
  "target": "telegram",
  "message": "扫描二维码登录:\nMEDIA:/tmp/bilibili_qr.png"
}
```

**Supported Media Platforms**: Telegram, Discord, Matrix, Signal, Weixin, Yuanbao

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