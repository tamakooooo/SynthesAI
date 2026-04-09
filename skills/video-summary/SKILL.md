---
name: video-summary
description: |
  Summarizes video content from URLs (B站/YouTube/抖音) and generates structured learning notes with transcripts.
  
  Use when user:
  - Provides video URLs (bilibili.com, youtube.com, douyin.com)
  - Asks to "summarize video", "analyze this video", "summarize this link"
  - Mentions "视频总结", "总结视频", "视频笔记"
  - Requests video learning notes or transcripts
metadata:
  version: 1.0.0
  author: Learning Assistant Team
---

# Video Summary Skill

Summarizes video content from URLs and generates structured learning notes with transcripts.

## Supported Platforms

- B站
- YouTube
- 抖音

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | ✅ | - | Video URL (B站/YouTube/抖音) |
| format | string | ❌ | markdown | Output format (markdown/pdf) |
| language | string | ❌ | zh | Summary language (zh/en) |
| output_dir | string | ❌ | ./outputs | Output directory |
| cookie_file | string | ❌ | - | Cookie file path (for login-required videos) |
| word_timestamps | boolean | ❌ | false | Enable word-level timestamps |

## Quick Start

### Python API (Recommended)

```python
from learning_assistant.api import summarize_video

# Basic usage
result = await summarize_video(
    url="https://www.bilibili.com/video/BV..."
)

# With options
result = await summarize_video(
    url="https://www.youtube.com/watch?v=...",
    format="pdf",
    language="en",
    output_dir="./my-notes"
)
```

### Synchronous Version

```python
from learning_assistant.api import summarize_video_sync

result = summarize_video_sync(url="https://...")
```

## Output Format

Returns JSON object:

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
  },
  "metadata": {
    "duration": 900,
    "platform": "bilibili"
  }
}
```

## Execution Steps

1. **Download video** (yt-dlp) - Extract metadata and video file
2. **Extract audio** (FFmpeg) - Separate audio track, convert to MP3
3. **Transcribe** (BcutASR) - Upload audio, wait for transcription, download result
4. **Generate summary** (LLM) - Use prompt template, call LLM API, parse JSON
5. **Export output** - Render Markdown template, generate SRT subtitle file

## Performance

| Duration | Download | Audio | Transcribe | Summary | Total |
|----------|----------|-------|------------|---------|-------|
| 5 min    | 30s      | 15s   | 2 min      | 20s     | ~3 min |
| 10 min   | 45s      | 20s   | 3 min      | 30s     | ~4 min |
| 30 min   | 1 min    | 30s   | 6 min      | 45s     | ~8 min |

## Error Handling

```python
from learning_assistant.api import summarize_video
from learning_assistant.api.exceptions import (
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
)

try:
    result = await summarize_video(url="https://...")
except VideoNotFoundError:
    print("Video not found, check URL")
except VideoDownloadError:
    print("Download failed, may need cookie")
except TranscriptionError:
    print("Transcription failed, retry later")
except LLMAPIError:
    print("LLM error, check API key")
```

## Detailed Documentation

For more details, see:
- [API Guide](references/api-guide.md) - Complete API reference
- [Error Handling](references/error-handling.md) - Detailed error scenarios
- [Examples](references/examples.md) - More usage examples

## Best Practices

1. **Video Selection**: Choose clear audio, 5-30 minutes duration
2. **Cookie Config**: Use cookie file for login-required videos
3. **Error Handling**: Always catch exceptions
4. **Performance**: Batch process with rate limiting

## Related Skills

- [list-skills](../list-skills/SKILL.md) - List available skills
- [learning-history](../learning-history/SKILL.md) - View learning history

---

**Need help?**
- GitHub Issues: [learning-assistant/issues](https://github.com/yourname/learning-assistant/issues)
- Docs: [learning-assistant.readthedocs.io](https://learning-assistant.readthedocs.io)