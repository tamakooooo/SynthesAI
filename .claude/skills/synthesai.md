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
---

# SynthesAI Knowledge Assistant

Transform complex content into clear, actionable knowledge.

## What SynthesAI Does

| Feature | Input | Output |
|---------|-------|--------|
| **Video Summary** | B站/YouTube/抖音 URL | Structured summary + key frames |
| **Link Learning** | Article URL | Knowledge card + key concepts |
| **Vocabulary** | Text or URL | Visual word cards (PNG) |

## Available Tools

| Tool | Description |
|------|-------------|
| `synthesai_summarize_video` | Summarize video from URL |
| `synthesai_process_link` | Extract knowledge from article URL |
| `synthesai_extract_vocabulary` | Extract vocabulary with visual cards |
| `synthesai_feishu_publish` | Publish content to Feishu knowledge base |
| `synthesai_bilibili_login` | Get Bilibili QR code for authentication |

## Installation

```bash
pip install synthesai
```

Or clone and install:

```bash
git clone https://github.com/tamakooooo/SynthesAI.git
cd SynthesAI
pip install -e ".[dev,server]"
```

## Quick Start

### 1. Setup

```bash
# Initialize configuration
synthesai setup

# Or use alias
la setup
```

### 2. Configure LLM

Set API key via environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

Or in `~/.synthesai/config.yaml`:

```yaml
llm:
  providers:
    openai:
      api_key_env: OPENAI_API_KEY
      base_url: https://api.openai.com/v1
      default_model: gpt-4
```

### 3. Bilibili Authentication (Optional)

For B站 videos with authentication:

```bash
la auth login --platform bilibili
```

Scan QR code with Bilibili App. Cookies saved to `~/.synthesai/cookies/bilibili_cookies.txt`.

## Usage Examples

### Video Summary

```python
# Use API
from synthesai.api import AgentAPI

api = AgentAPI()
result = await api.summarize_video(
    url="https://www.bilibili.com/video/BV1G49MBLE4D"
)

print(f"Title: {result.title}")
print(f"Summary: {result.summary}")
print(f"Key Frames: {len(result.key_frames)}")
```

Or via CLI:

```bash
la video https://www.bilibili.com/video/BV1G49MBLE4D
```

### Link Learning

```python
result = await api.process_link(
    url="https://example.com/article",
    generate_quiz=True
)

print(f"Key Points: {result.key_points}")
print(f"Key Concepts: {result.key_concepts}")
```

CLI:

```bash
la link https://example.com/article
```

### Vocabulary Extraction

```python
result = await api.extract_vocabulary(
    content="Machine learning transforms...",
    generate_card=True
)

# Output includes PNG visual card
print(f"Words: {result.words}")
print(f"PNG Card: {result.files['png_path']}")
```

CLI:

```bash
la vocab "Machine learning transforms how we..."
```

### Feishu Publishing

```python
# Configure Feishu adapter
api.configure_feishu(
    app_id="cli_...",
    app_secret="...",
    space_id="...",
    root_node_token="..."
)

# Publish to knowledge base
result = await api.feishu_publish(
    title="Knowledge Card Title",
    content="Summary content...",
    blocks=[
        {"type": "heading", "text": "Key Points"},
        {"type": "bullet_list", "items": ["Point 1", "Point 2"]}
    ]
)
```

## Visual Knowledge Cards

SynthesAI generates **Editorial-style** visual cards:

- **1200px width** - Social media optimized
- **Claude colors** - Orange (#FF6B35) + Purple (#764BA2)
- **Multiple formats** - HTML + PNG output

Card types:
- **Vocabulary cards**: Hero + Story + Word List + Word Focus panels
- **Link cards**: Summary + Key Points + Key Concepts panels

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `FEISHU_APP_ID` | Feishu app ID |
| `FEISHU_APP_SECRET` | Feishu app secret |

### Config File Structure

```yaml
# ~/.synthesai/config.yaml
app:
  log_level: INFO

llm:
  default_provider: openai
  providers:
    openai:
      api_key_env: OPENAI_API_KEY
      default_model: gpt-4

modules:
  video_summary:
    enabled: true
  link_learning:
    enabled: true
  vocabulary:
    enabled: true

adapters:
  feishu:
    enabled: true
    config:
      app_id_env: FEISHU_APP_ID
      app_secret_env: FEISHU_APP_SECRET
```

## API Reference

### AgentAPI Methods

```python
class AgentAPI:
    # Video
    async def summarize_video(url: str) -> VideoResult

    # Link
    async def process_link(url: str, generate_quiz: bool = False) -> LinkResult

    # Vocabulary
    async def extract_vocabulary(
        content: str | None,
        url: str | None,
        generate_card: bool = False
    ) -> VocabularyResult

    # Feishu
    async def feishu_publish(
        title: str,
        content: str,
        blocks: list[dict]
    ) -> PublishResult

    # Auth
    def get_bilibili_qr() -> QRSession
    def check_bilibili_status(key: str) -> AuthResult
```

### Result Types

```python
@dataclass
class VideoResult:
    title: str
    summary: str
    key_frames: list[KeyFrame]
    transcript: str
    duration: int

@dataclass
class LinkResult:
    title: str
    url: str
    summary: str
    key_points: list[str]
    key_concepts: list[KeyConcept]
    tags: list[str]

@dataclass
class VocabularyResult:
    words: list[WordEntry]
    story: str
    files: dict[str, str]  # html_path, png_path
```

## Troubleshooting

### B站视频下载失败

1. Check authentication: `la auth status --platform bilibili`
2. Re-login if expired: `la auth login --platform bilibili`
3. Use cookies: Ensure `~/.synthesai/cookies/bilibili_cookies.txt` exists

### LLM API Errors

1. Verify API key is set correctly
2. Check base_url if using custom endpoint
3. Test with: `la config show`

### Visual Card Generation Failed

1. Install Pillow: `pip install Pillow`
2. For PNG: Install Playwright: `pip install playwright && playwright install chromium`

## Related Resources

- **GitHub**: https://github.com/tamakooooo/SynthesAI
- **Documentation**: [CLAUDE.md](CLAUDE.md)
- **Architecture**: [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md)
- **API Guide**: [docs/api.md](docs/api.md)