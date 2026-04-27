# SynthesAI

> **Synthesize Knowledge with AI Intelligence**
>
> **智能整合，知识精炼** - AI驱动的模块化学习助手

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-652%20passed-brightgreen.svg)](https://github.com/tamakooooo/SynthesAI)
[![Coverage](https://img.shields.io/badge/coverage-%3E80%25-green.svg)](https://github.com/tamakooooo/SynthesAI)

---

## 🎯 What is SynthesAI?

**SynthesAI** synthesizes knowledge from multiple sources into structured learning materials:

- 📹 **Videos** → Structured summaries with key frames
- 📝 **Articles** → Knowledge cards and key concepts
- 📚 **Vocabulary** → Visual learning cards with phonetics

**From Complexity to Clarity** - Transform complex content into clear, actionable knowledge.

---

## ✨ Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Video Summary** | B站/YouTube/抖音视频总结，支持免费ASR转录 | ✅ Available |
| **Link Learning** | 网页文章知识卡片生成，问答测验 | ✅ Available |
| **Vocabulary** | 单词提取+音标查询+Visual知识卡片（PNG） | ✅ Available |
| **Visual Cards** | Editorial风格知识卡片（1200px，Claude配色） | ✅ Available |
| **Multi-LLM** | OpenAI、Anthropic、DeepSeek支持 | ✅ Available |
| **Agent Ready** | 完整Agent开发文档+自动化流程 | ✅ Available |

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/tamakooooo/SynthesAI.git
cd SynthesAI

# Install dependencies
pip install -e ".[dev]"
```

### ⚠️ Important: yutto Installation (Required for B站 Videos)

**yutto is a dedicated B站 downloader that handles WBI signatures and CDN issues automatically.**

```bash
# Install yutto (B站视频下载必备)
pip install yutto>=2.2.0

# Verify installation
yutto --version
```

> **Why yutto is required:**
> - B站 uses WBI signature authentication (yutto handles this automatically)
> - yt-dlp often fails with CDN timeout errors on B站
> - yutto provides more stable downloads for B站 videos

### Setup Configuration

```bash
la setup
```

### Basic Usage

#### 1. Video Summary

```python
from learning_assistant.api import summarize_video

# Summarize video
result = await summarize_video(
    url="https://www.bilibili.com/video/BV1G49MBLE4D"
)

print(f"Title: {result.title}")
print(f"Summary: {result.summary[:200]}...")
```

#### 2. Link Learning

```python
from learning_assistant.api import process_link

# Extract knowledge from article
result = await process_link(
    url="https://example.com/article",
    generate_quiz=True
)

print(f"Key points: {len(result.key_points)}")
```

#### 3. Vocabulary Extraction

```python
from learning_assistant.api import extract_vocabulary

# From text
result = await extract_vocabulary(
    content="Machine learning is transforming...",
    word_count=10,
    generate_card=True  # Generate visual card
)

# From URL
result = await extract_vocabulary(
    url="https://example.com/blog",
    generate_card=True
)

# Output: HTML + PNG visual card
print(f"PNG card: {result.files['png_path']}")
```

---

## 📚 Documentation

### For Users

- **[Skills Documentation](skills/README.md)** - Complete skills guide
- **[Video Summary Skill](skills/video-summary/SKILL.md)** - Video processing workflow
- **[Link Learning Skill](skills/link-learning/SKILL.md)** - Web content extraction
- **[Vocabulary Skill](skills/vocabulary/SKILL.md)** - Word extraction + visual cards
- **[CHANGELOG](CHANGELOG.md)** - Version history

### For Developers

- **[Agent Documentation](docs/AGENT_DOCUMENTATION_INDEX.md)** - Complete agent guide
- **[Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md)** - Four-layer architecture
- **[Agent Development Guide](docs/AGENT_DEVELOPMENT_GUIDE.md)** - Module development workflow
- **[API Reference](docs/api.md)** - Python API documentation

---

## 🎨 Visual Knowledge Cards

SynthesAI generates **Editorial-style** visual knowledge cards:

- **1200px width** - Optimized for social media
- **Claude colors** - Orange (#FF6B35) + Purple (#764BA2)
- **High resolution** - 2x scaling for crisp display
- **Multiple formats** - HTML + PNG output

**Example outputs**:
- Vocabulary cards: Hero + Story + Word List + Word Focus panels
- Link cards: Summary + Key Points + Key Concepts panels

See [skills/vocabulary/SKILL.md](skills/vocabulary/SKILL.md) for visual card documentation.

---

## 🤖 Agent Development

**SynthesAI is designed for AI Agent automation**:

### Key Features

- ✅ **Asynchronous architecture** - `async def` + `await` pattern
- ✅ **Type annotations** - Full Python type hints
- ✅ **Configuration-driven** - No hardcoded values
- ✅ **Component reuse** - LLMService, PromptManager, VisualCardGenerator
- ✅ **Prompt engineering** - Standardized `keyword: description` format

### Agent Workflow

1. Read [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) (required)
2. Follow [Agent Development Guide](docs/AGENT_DEVELOPMENT_GUIDE.md)
3. Use [Prompt Engineering Guide](docs/knowledge_card_prompt_update.md)
4. Implement with standard patterns

---

## 🛠️ Architecture

**Four-layer modular architecture**:

```
┌─────────────────────────────────────┐
│   Skills Layer (CLI + API)          │  User interface
│   - video-summary, link-learning    │
│   - vocabulary                       │
├─────────────────────────────────────┤
│   Modules Layer                      │  Core functionality
│   - video_summary, link_learning     │
│   - vocabulary                        │
├─────────────────────────────────────┤
│   Core Layer                         │  Shared services
│   - LLMService, EventBus,            │
│     PromptManager, Exporters         │
├─────────────────────────────────────┤
│   Adapters Layer                     │  External integrations
│   - Feishu, Obsidian, SiYuan         │
└─────────────────────────────────────┘
```

See [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) for detailed documentation.

---

## 📦 Project Structure

```
SynthesAI/
├── src/learning_assistant/
│   ├── core/                # Core engines
│   ├── modules/             # Learning modules
│   ├── adapters/            # External integrations
│   └── api/                 # Agent API
├── skills/                  # Skill documentation
│   ├── video-summary/
│   ├── link-learning/
│   └── vocabulary/
├── docs/                    # User & developer docs
├── config/                  # Configuration files
├── templates/               # Prompt templates
└── tests/                   # Test suite (652 tests)
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific module tests
pytest tests/modules/vocabulary/
```

**Test coverage**: >80% (652 tests passing)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙋 Support

- **GitHub Issues**: [tamakooooo/SynthesAI/issues](https://github.com/tamakooooo/SynthesAI/issues)
- **Documentation**: [skills/](skills/) directory
- **Agent Guide**: [docs/AGENT_DOCUMENTATION_INDEX.md](docs/AGENT_DOCUMENTATION_INDEX.md)

---

**Built with ❤️ by SynthesAI Team**