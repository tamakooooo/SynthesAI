---
name: synthesai
description: "SynthesAI: Transform videos/articles into structured knowledge cards with AI"
version: 1.2.0
author: SynthesAI Team
license: MIT
metadata:
  hermes:
    tags: [learning, video-summary, knowledge-card, vocabulary, feishu, ai, synthesai, bilibili-auth]
    related_skills: []
    platforms: [cli, telegram, discord, slack, matrix, signal, weixin]
    media_support: true
---

# SynthesAI Knowledge Assistant

Transform complex content into clear, actionable knowledge.

## ⚠️ Prerequisites: yutto Installation (Required for B站 Videos)

**Before summarizing B站 videos, install yutto:**

```bash
pip install yutto>=2.2.0
yutto --version  # Verify installation
```

> **Why yutto is required for B站:**
> - Handles WBI signature authentication automatically
> - Avoids yt-dlp CDN timeout errors
> - Provides stable, authenticated downloads

## What SynthesAI Does

| Feature | Input | Output |
|---------|-------|--------|
| **Video Summary** | B站/YouTube/抖音 URL | Structured summary + key frames + mindmap + tables |
| **Link Learning** | Article URL | Knowledge card + key concepts |
| **Vocabulary** | Text or URL | Visual word cards (PNG) |
| **Bilibili Auth** | QR code generation | Login QR image for user to scan |
| **Feishu Publish** | Video summary | Document with images, mindmap, tables |

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

## 🖼️ Sending Images via Hermes (QR Codes, Visual Cards)

**CRITICAL: Hermes messaging platforms automatically deliver images.**

When you generate an image (QR code, visual card), send it to the user using Hermes's `send_message` tool with the `MEDIA:<path>` prefix.

### Supported Image Formats

| Extension | Platform Support |
|-----------|-----------------|
| `.png` | All platforms |
| `.jpg` / `.jpeg` | All platforms |
| `.webp` | Telegram, Discord |
| `.gif` | Telegram, Discord |

### Supported Platforms for Media

- `telegram` ✅
- `discord` ✅
- `matrix` ✅
- `signal` ✅
- `weixin` ✅
- `yuanbao` ✅

**Note:** Slack, Email, SMS do NOT support MEDIA attachments via send_message.

### QR Code Login Workflow (with Image Delivery)

**User says:** "我要登录B站" or "帮我扫码登录"

**You should:**

1. **Generate QR Code Image**
```bash
la auth login --platform bilibili
```
This outputs the QR image path, e.g.: `/tmp/bilibili_login_qr.png`

2. **Send QR Image to User**
```json
{
  "action": "send",
  "target": "telegram",
  "message": "请用B站App扫描下方二维码登录:\nMEDIA:/tmp/bilibili_login_qr.png"
}
```

Or for Discord:
```json
{
  "action": "send",
  "target": "discord",
  "message": "请扫描二维码登录B站\nMEDIA:/tmp/bilibili_login_qr.png"
}
```

3. **Poll for Login Confirmation**
The CLI will show progress. When login succeeds, notify user:
```json
{
  "action": "send",
  "target": "telegram",
  "message": "✅ B站登录成功！现在可以下载视频了"
}
```

### Visual Knowledge Card Delivery

When vocabulary or link learning generates a visual card (PNG):

```json
{
  "action": "send",
  "target": "telegram",
  "message": "这是你的知识卡片:\nMEDIA:/tmp/knowledge_card.png"
}
```

### Multiple Media Files

You can send multiple images in one message:
```json
{
  "action": "send",
  "target": "telegram",
  "message": "知识卡片 + QR码:\nMEDIA:/tmp/card.png\nMEDIA:/tmp/qr.png"
}
```

### Complete Bilibili Login Example (Telegram)

```
User: 帮我登录B站

Step 1: Generate QR
$ la auth login --platform bilibili
Output: QR saved to /tmp/hermes/cache/bilibili_qr_abc123.png

Step 2: Send QR to user
send_message({
  "target": "telegram",
  "message": "请扫描下方二维码登录B站（有效期180秒）:\n\nMEDIA:/tmp/hermes/cache/bilibili_qr_abc123.png"
})

Step 3: User scans with Bilibili App

Step 4: Login succeeds
send_message({
  "target": "telegram",
  "message": "✅ B站登录成功！已保存登录凭证。\n\n现在可以下载B站视频了，发送视频链接即可。"
})
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

Publish knowledge cards to Feishu wiki with rich content:

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

### Feishu Document Features

When publishing to Feishu knowledge base, the document includes:

| Content Type | Feishu Block | Description |
|--------------|--------------|-------------|
| **Key Frames** | Image Block (block_type=27) | Screenshots at chapter timestamps |
| **Mindmap** | Whiteboard Block (block_type=43) | Interactive mindmap visualization |
| **Tables** | Table Block (block_type=31) | Markdown tables converted to proper table blocks |
| **Chapters** | Heading + Paragraph | Structured chapter content |

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