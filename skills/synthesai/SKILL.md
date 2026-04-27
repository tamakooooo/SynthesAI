---
name: synthesai
description: "SynthesAI: Transform videos/articles into structured knowledge cards with AI"
version: 1.0.0
author: SynthesAI Team
license: MIT
metadata:
  hermes:
    tags: [learning, video-summary, knowledge-card, vocabulary, feishu, ai, synthesai]
    related_skills: []
    platforms: [cli, telegram, discord, slack]
---

# SynthesAI Knowledge Assistant

Transform complex content into clear, actionable knowledge.

## What SynthesAI Does

| Feature | Input | Output |
|---------|-------|--------|
| **Video Summary** | B站/YouTube/抖音 URL | Structured summary + key frames |
| **Link Learning** | Article URL | Knowledge card + key concepts |
| **Vocabulary** | Text or URL | Visual word cards (PNG) |

## Quick Commands

### Video Summary
```
la video <url>
```
Examples:
- `la video https://www.bilibili.com/video/BV1G49MBLE4D`
- `la video https://www.youtube.com/watch?v=...`

### Link Learning
```
la link <url>
```
Extracts: Summary, Key Points, Key Concepts, Tags

### Vocabulary Extraction
```
la vocab <text>
```
Or from URL:
```
la vocab --url <url>
```

### Bilibili Login
```
la auth login --platform bilibili
```
Scan QR code → cookies saved automatically

### Feishu Publish
```
la feishu publish <title> <content>
```

## Prerequisites

### Installation

```bash
pip install synthesai
```

### Configuration

Set API key:
```bash
export OPENAI_API_KEY="sk-..."
```

Or create `~/.synthesai/config.yaml`:

```yaml
llm:
  providers:
    openai:
      api_key_env: OPENAI_API_KEY
      default_model: gpt-4
```

## Usage Workflow

### 1. User requests video summary

**User says:** "帮我总结这个B站视频 https://www.bilibili.com/video/BV..."

**You should:**
1. Run: `la video <url>`
2. Return the summary result to user

### 2. User requests article analysis

**User says:** "分析这篇文章 https://example.com/article"

**You should:**
1. Run: `la link <url>`
2. Return: title, summary, key points, key concepts

### 3. User requests vocabulary extraction

**User says:** "从这段文字提取生词..."

**You should:**
1. Run: `la vocab <text>`
2. Return: word list, phonetics, visual card path

### 4. User needs Bilibili login

**User says:** "我要下载B站视频，需要登录"

**You should:**
1. Run: `la auth login --platform bilibili`
2. Generate QR image and send to user
3. Poll for scan confirmation
4. Notify user when login succeeds

## Visual Knowledge Cards

SynthesAI generates Editorial-style cards:

- **Width**: 1200px (social media optimized)
- **Colors**: Orange (#FF6B35) + Purple (#764BA2)
- **Formats**: HTML + PNG

Card can be sent as image to user via messaging platforms.

## Feishu Integration

Publish knowledge cards to Feishu wiki:

```yaml
# Configure in settings.local.yaml
adapters:
  feishu:
    config:
      app_id: "cli_..."
      app_secret: "..."
      space_id: "..."
      root_node_token: "..."
```

Then:
```
la feishu publish "标题" "内容..."
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| B站下载失败 | `la auth login --platform bilibili` |
| API错误 | Check API key in config |
| 无输出 | Verify URL is valid |

## Related Resources

- GitHub: https://github.com/tamakooooo/SynthesAI
- Docs: See `CLAUDE.md` for full documentation