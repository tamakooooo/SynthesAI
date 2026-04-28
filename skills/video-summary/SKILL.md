---
name: video-summary
description: |
  Summarizes video content from URLs (B站/YouTube/抖音) and generates structured learning notes with transcripts.
  
  Use when user:
  - Provides video URLs (bilibili.com, youtube.com, douyin.com)
  - Asks to "summarize video", "analyze this video", "summarize this link"
  - Mentions "视频总结", "总结视频", "视频笔记"
  - Requests video learning notes or transcripts
  - Needs B站 authentication ("登录B站", "扫码登录")
metadata:
  version: 1.4.0
  author: Learning Assistant Team
  hermes:
    platforms: [cli, telegram, discord, slack, matrix, signal, weixin]
    media_support: true
---

# Video Summary Skill

Summarizes video content from URLs and generates structured learning notes with transcripts.

## ⚠️ Prerequisites: yutto Installation (Required for B站)

**Before using this skill for B站 videos, install yutto:**

```bash
pip install yutto>=2.2.0
```

| Platform | Downloader | Notes |
|----------|------------|-------|
| **B站** | yutto (CLI) | Required - handles WBI signature & CDN |
| **YouTube** | yt-dlp | Built-in |
| **抖音** | yt-dlp | Built-in |

> **Why yutto is mandatory for B站:**
> - B站 videos require WBI signature (yutto handles automatically)
> - yt-dlp often fails with SSL/CDN timeout errors
> - yutto provides stable, authenticated downloads

## ⚠️ Prerequisites: VideoCaptioner (For Free ASR)

**For free transcription, install VideoCaptioner:**

```bash
pip install videocaptioner
```

| ASR Backend | Description | Cost |
|-------------|-------------|------|
| `bijian` | B站必剪 | 免费 |
| `jianying` | 剪映 | 免费 |
| `faster-whisper` | 本地模型 | 免费 |

## 🔐 B站 Authentication (Required for Some Videos)

Some B站 videos require login cookies to download. Use QR code authentication:

### Generate Login QR

```bash
la auth login --platform bilibili
```

Output: QR image saved to `/tmp/bilibili_login_qr.png`

### Send QR to User (Hermes Agent)

For Hermes messaging platforms, use `send_message` with `MEDIA:<path>`:

```json
{
  "action": "send",
  "target": "telegram",
  "message": "请用B站App扫描下方二维码登录（有效期180秒）:\n\nMEDIA:/tmp/bilibili_login_qr.png"
}
```

### Supported Media Platforms

| Platform | QR Image Support |
|----------|-----------------|
| Telegram | ✅ `.png`, `.jpg`, `.gif` |
| Discord | ✅ `.png`, `.jpg`, `.gif` |
| Matrix | ✅ `.png`, `.jpg` |
| Signal | ✅ `.png`, `.jpg` |
| Weixin | ✅ `.png`, `.jpg` |
| Yuanbao | ✅ `.png`, `.jpg` |
| Slack | ❌ No MEDIA support |
| Email | ❌ No MEDIA support |

### Login Workflow

```
User: "我要下载B站视频，需要登录"

Step 1: Generate QR
$ la auth login --platform bilibili
→ QR saved: /tmp/bilibili_qr_abc123.png

Step 2: Send QR image
send_message({
  "target": "telegram",
  "message": "扫描二维码登录B站:\nMEDIA:/tmp/bilibili_qr_abc123.png"
})

Step 3: User scans → CLI confirms success

Step 4: Notify user
send_message({
  "target": "telegram", 
  "message": "✅ B站登录成功！现在可以下载视频了"
})
```

## HTTP API Usage (For Agents)

**Server Base URL**: `http://localhost:8000` (or your configured server address)

### Step 1: Submit Video Task

Video processing takes 3-10 minutes, so use async task queue:

```http
POST /api/v1/video/submit
Content-Type: application/json

{
  "url": "https://www.bilibili.com/video/BV...",
  "format": "markdown",
  "language": "zh"
}
```

**Response**:
```json
{
  "task_id": "video_abc123",
  "status": "pending",
  "message": "Task submitted successfully"
}
```

### Step 2: Check Progress

```http
GET /api/v1/video/{task_id}/status
```

**Response**:
```json
{
  "task_id": "video_abc123",
  "status": "running",
  "progress": 45.5,
  "message": "Transcribing audio..."
}
```

**Status values**: `pending` → `running` → `completed` / `failed` / `cancelled`

### Step 3: Get Result

```http
GET /api/v1/video/{task_id}/result
```

**Response** (when completed):
```json
{
  "status": "success",
  "url": "https://...",
  "title": "Video Title",
  "summary": {
    "content": "Summary content...",
    "key_points": ["Point 1", "Point 2"],
    "knowledge": ["Knowledge 1", "Knowledge 2"]
  },
  "transcript": "Full transcript...",
  "files": {
    "summary_path": "./outputs/summary.md",
    "subtitle_path": "./outputs/subtitle.srt"
  }
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | ✅ | - | Video URL (B站/YouTube/抖音) |
| format | string | ❌ | markdown | Output format (markdown/pdf/both) |
| language | string | ❌ | zh | Summary language (zh/en) |
| output_dir | string | ❌ | ./outputs | Output directory |
| cookie_file | string | ❌ | - | Cookie file for login-required videos |

## Supported Platforms

- B站
- YouTube
- 抖音

## ASR Engines

| Engine | Type | Cost | Quality |
|--------|------|------|---------|
| **videocaptioner** (默认) | CLI | 免费 | 高 |
| **siliconcloud** | API | 付费 | 极高 |
| **faster_whisper** | 本地 | 免费 | 中 |

**Configuration**:
```yaml
modules:
  video_summary:
    transcriber: "videocaptioner"  # 免费
    asr_engine: "bijian"           # videocaptioner backend
```

## Execution Flow

1. Submit task → get `task_id`
2. Poll status every 30-60 seconds until `status: completed`
3. Fetch result when completed

## Output Content

Video summary includes:

| Content | Description |
|---------|-------------|
| **Summary** | Video overview and key insights |
| **Chapters** | Timestamped sections with titles and summaries |
| **Key Frames** | Screenshots extracted at chapter timestamps |
| **Mindmap** | Visual structure of video content hierarchy |
| **Tables** | Markdown tables converted to proper format |
| **Q&A** | Potential questions and answers |

## Feishu Publishing Features

When enabled, video summaries are published to Feishu knowledge base with:

- **Key Frames**: Inserted as image blocks at correct positions
- **Mindmap**: Created in whiteboard block (block_type=43) with interactive nodes
- **Tables**: Converted to table blocks (block_type=31) with proper formatting

## Performance

| Duration | Total Time |
|----------|------------|
| 5 min    | ~3 min |
| 10 min   | ~4 min |
| 30 min   | ~8 min |

## Error Handling

- `404 TaskNotFound`: Task ID invalid or expired
- `400 TaskNotComplete`: Task still running, wait and retry
- `503 QueueFull`: Server busy, retry later

## Python API (Alternative)

```python
from learning_assistant.api import summarize_video

result = await summarize_video(url="https://www.bilibili.com/video/BV...")
```

## Related Skills

- [link-learning](../link-learning/SKILL.md) - Web article knowledge extraction
- [vocabulary](../vocabulary/SKILL.md) - Vocabulary extraction