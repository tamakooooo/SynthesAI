# Video Summary API Guide

Complete API reference for the video-summary skill.

## AgentAPI Class

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()
result = await api.summarize_video(url="https://...")
```

### Methods

#### `summarize_video(url, **options)`

Summarize video content.

**Parameters**:
- `url` (str, required): Video URL
- `format` (str, optional): Output format (markdown/pdf)
- `language` (str, optional): Summary language (zh/en)
- `output_dir` (str, optional): Output directory
- `cookie_file` (str, optional): Cookie file path
- `word_timestamps` (bool, optional): Enable word-level timestamps

**Returns**: `VideoSummaryResult` object

**Raises**:
- `VideoNotFoundError` - Video not found
- `VideoDownloadError` - Download failed
- `TranscriptionError` - Transcription failed
- `LLMAPIError` - LLM API error

---

## Convenience Functions

### `summarize_video(url, **options)`

Async video summary function (recommended).

```python
from learning_assistant.api import summarize_video

result = await summarize_video(
    url="https://www.bilibili.com/video/BV...",
    format="markdown",
    language="zh"
)

print(result["title"])
print(result["summary"]["content"])
```

**Returns**: `dict` with all result data

---

### `summarize_video_sync(url, **options)`

Synchronous version (for simple scripts).

```python
from learning_assistant.api import summarize_video_sync

result = summarize_video_sync(url="https://...")
```

**Warning**: Cannot be called inside async functions (will cause event loop error).

---

## Output Schema

### VideoSummaryResult

Pydantic model with validated fields:

```python
class VideoSummaryResult(BaseModel):
    status: str                    # "success" or "error"
    url: str                       # Video URL
    title: str                     # Video title
    summary: dict[str, Any]        # Summary content
    transcript: str                # Full transcript
    files: dict[str, str | None]   # Output file paths
    metadata: dict[str, Any]       # Video metadata
    timestamp: str                 # ISO 8601 timestamp
```

### Summary Structure

```python
summary = {
    "content": "Main summary text...",
    "key_points": [
        "Key point 1",
        "Key point 2",
        ...
    ],
    "knowledge": [
        "Knowledge point 1",
        "Knowledge point 2",
        ...
    ]
}
```

### Files Structure

```python
files = {
    "summary_path": "./outputs/video_summary.md",
    "subtitle_path": "./outputs/video_subtitle.srt"
}
```

### Metadata Structure

```python
metadata = {
    "duration": 900,              # Duration in seconds
    "platform": "bilibili",       # Platform name
    "uploader": "UP主",           # Uploader name
    "upload_date": "2026-03-15", # Upload date
    "view_count": 10000,         # View count (if available)
    "description": "..."         # Video description
}
```

---

## Platform-Specific Notes

### B站

**Features**:
- Full support
- Best transcription quality for Chinese
- Free via BcutASR

**Cookie**:
```python
result = await summarize_video(
    url="https://www.bilibili.com/video/BV...",
    cookie_file="data/cookies/bilibili.txt"
)
```

**How to get cookie**:
1. Login to bilibili.com
2. Open browser DevTools (F12)
3. Go to Network tab
4. Reload page
5. Find any request
6. Copy `Cookie` header
7. Save to `bilibili.txt`

---

### YouTube

**Features**:
- Full support
- Good for English videos
- May require cookie for age-restricted videos

**Cookie**:
```python
result = await summarize_video(
    url="https://www.youtube.com/watch?v=...",
    cookie_file="data/cookies/youtube.txt"
)
```

**How to get cookie**:
- Use browser extension (e.g., "Get cookies.txt")
- Or manually export from DevTools

---

### 抖音

**Features**:
- Basic support
- May need cookie for some videos
- Transcription quality varies

---

## Performance Optimization

### Caching

Video downloads and transcriptions are cached in `data/cache/`:

- Downloaded videos: `data/cache/downloads/`
- Extracted audio: `data/cache/audio/`
- Transcription results: `data/cache/transcripts/`

**Clear cache**:
```bash
rm -rf data/cache/*
```

---

### Batch Processing

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

videos = [
    "https://www.bilibili.com/video/BV1...",
    "https://www.youtube.com/watch?v=...",
]

for url in videos:
    result = await api.summarize_video(url=url)
    print(f"✅ {result.title}")
    
    # Rate limiting
    await asyncio.sleep(10)
```

---

## Configuration

### Environment Variables

```bash
# LLM API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="sk-..."

# Optional
export LEARNING_ASSISTANT_LOG_LEVEL="DEBUG"
export LEARNING_ASSISTANT_CONFIG_DIR="config"
```

### Config File

`config/settings.yaml`:

```yaml
modules:
  video_summary:
    enabled: true
    transcriber: "bcut"
    export_format: "markdown"
    cookie_file: "./data/cookies/bilibili.txt"
```

---

## Troubleshooting

### FFmpeg Not Found

**Error**: `RuntimeError: FFmpeg not found`

**Solution**:
```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Verify
ffmpeg -version
```

---

### API Key Invalid

**Error**: `ValueError: OpenAI API key not found`

**Solution**:
```bash
export OPENAI_API_KEY="sk-..."

# Or in .env file
echo "OPENAI_API_KEY=sk-..." >> .env
```

---

### Video Download Failed

**Error**: `VideoDownloadError: HTTP 403 Forbidden`

**Solution**:
```python
# Use cookie file
result = await summarize_video(
    url="https://...",
    cookie_file="data/cookies/bilibili.txt"
)
```

---

### Transcription Failed

**Error**: `TranscriptionError: Rate limit exceeded`

**Solution**:
- Wait a few minutes
- Retry later
- BcutASR has rate limits

---

## Advanced Usage

### Custom Output Template

```python
result = await summarize_video(
    url="https://...",
    output_dir="./custom-outputs",
    format="pdf"
)
```

### Word-Level Timestamps

```python
result = await summarize_video(
    url="https://...",
    word_timestamps=True
)

# Access word-level data
for word in result["metadata"]["words"]:
    print(f"{word['text']}: {word['start']}-{word['end']}")
```

### Direct AgentAPI Access

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# Get more control
result = await api.summarize_video(url="...")

# Access structured result
print(result.title)           # Direct attribute access
print(result.summary)         # Dict access
print(result.files)           # Dict access

# Export to dict
data = result.model_dump()
```

---

## Related Documentation

- [Error Handling](error-handling.md) - Detailed error scenarios
- [Examples](examples.md) - More usage examples
- [Agent Integration](../../docs/agent_integration.md) - Integration guide