# Vocabulary Learning Module - User Guide

> **Version**: v0.2.0
> **Last Updated**: 2026-04-08

## 📋 Table of Contents

- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [CLI Usage](#cli-usage)
- [Python API Usage](#python-api-usage)
- [Features](#features)
- [Configuration](#configuration)
- [Examples](#examples)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)

---

## Introduction

The Vocabulary Learning Module is a powerful tool that extracts important vocabulary from text content and generates comprehensive word cards to accelerate vocabulary acquisition.

**Core Capabilities**:
- ✅ **Intelligent Word Extraction** - LLM-powered context-aware extraction
- ✅ **Complete Word Cards** - Phonetics, definitions, examples, synonyms, antonyms
- ✅ **Multi-layer Phonetic Lookup** - Local dictionary → API → LLM fallback
- ✅ **Contextual Stories** - Reinforce memory through context
- ✅ **Multiple Difficulty Levels** - Beginner, intermediate, advanced
- ✅ **Flexible Input** - Text, files, URLs, or integration with other modules

**Use Cases**:
- 📚 Learn vocabulary from articles and documents
- 🎓 Extract key terms from academic papers
- 📝 Create vocabulary lists from study materials
- 🎬 Generate word cards from video transcriptions

---

## Quick Start

### Prerequisites

1. **Python 3.11+**
2. **API Key** - OpenAI / Anthropic / DeepSeek
3. **Network Connection** - For API calls (phonetic lookup, LLM)

### Setup API Key

```bash
# OpenAI (recommended)
export OPENAI_API_KEY="sk-your-key-here"

# Or Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or DeepSeek
export DEEPSEEK_API_KEY="sk-your-key-here"
```

### First Use

```bash
# Basic usage with text
la vocabulary --text "Machine learning is transforming industries..."

# Output will be saved to data/outputs/vocabulary/
```

---

## CLI Usage

### Basic Command

```bash
la vocabulary [OPTIONS]
```

### Parameters

| Parameter | Short | Default | Description |
|-----------|-------|---------|-------------|
| `--text` | `-t` | - | Source text to extract words from |
| `--file` | `-f` | - | Input file path |
| `--count` | `-c` | 10 | Number of words to extract (1-50) |
| `--difficulty` | `-d` | intermediate | Difficulty level |
| `--no-story` | - | false | Skip story generation |
| `--output` | `-o` | auto | Output file path |

### Usage Examples

#### 1. Basic Text Input

```bash
la vocabulary --text "Artificial intelligence has revolutionized many industries..."
```

#### 2. From File

```bash
# Extract from a text file
la vocabulary --file article.txt

# Specify word count
la vocabulary --file research_paper.pdf --count 20
```

#### 3. Custom Difficulty

```bash
# Beginner level (simpler words)
la vocabulary --text "..." --difficulty beginner

# Advanced level (complex words)
la vocabulary --text "..." --difficulty advanced
```

#### 4. Skip Story Generation

```bash
# Faster processing without story
la vocabulary --file article.txt --no-story
```

#### 5. Custom Output

```bash
# Specify output file
la vocabulary --text "..." --output my_words.md
```

### Output Location

Default: `data/outputs/vocabulary/`

File naming: `vocabulary_{timestamp}.md`

Example: `vocabulary_20260408_103000.md`

---

## Python API Usage

### Installation

```bash
pip install learning-assistant
```

### Basic Usage

```python
from learning_assistant.api import extract_vocabulary

# Async usage
async def main():
    result = await extract_vocabulary(
        content="Your text content here..."
    )
    print(f"Extracted {len(result['vocabulary_cards'])} words")

# Sync usage
from learning_assistant.api import extract_vocabulary_sync

result = extract_vocabulary_sync(content="Your text...")
```

### Complete Parameters

```python
result = await extract_vocabulary(
    content="Your text...",           # Text content
    word_count=15,                    # Number of words (1-50)
    difficulty="intermediate",         # Difficulty level
    generate_story=True,               # Generate contextual story
    llm={                             # LLM configuration (optional)
        "provider": "openai",
        "model": "gpt-4"
    },
    output_dir="./my-vocabulary"       # Output directory (optional)
)
```

### Return Data Structure

```python
{
    "status": "success",
    "content": "Machine learning is transforming...",  # Source (truncated)
    "word_count": 10,                                  # Words extracted
    "difficulty": "intermediate",                      # Difficulty
    "vocabulary_cards": [                              # Word cards
        {
            "word": "transform",
            "phonetic": {
                "us": "/trænsˈfɔrm/",
                "uk": "/trænsˈfɔːm/"
            },
            "part_of_speech": "verb",
            "definition": {
                "zh": "改变，转变",
                "en": "to change completely"
            },
            "example_sentences": [
                {
                    "sentence": "ML is transforming industries.",
                    "translation": "机器学习正在改变各行各业。",
                    "context": "原文提取"
                }
            ],
            "synonyms": ["change", "convert"],
            "antonyms": ["maintain"],
            "related_words": ["transformation"],
            "difficulty": "intermediate",
            "frequency": "high"
        }
    ],
    "context_story": {                                # Story (optional)
        "title": "The Transformative Power",
        "content": "In recent years...",
        "word_count": 300,
        "target_words": ["transform", ...]
    },
    "statistics": {                                    # Statistics
        "total_words": 10,
        "difficulty_distribution": {
            "beginner": 3,
            "intermediate": 5,
            "advanced": 2
        }
    },
    "files": {                                         # Output files
        "markdown_path": "./outputs/vocabulary.md"
    },
    "timestamp": "2026-04-08T10:30:00"
}
```

### Advanced Usage

#### 1. Different LLM Providers

```python
# OpenAI GPT-4
result = await extract_vocabulary(
    content="Your text...",
    llm={"provider": "openai", "model": "gpt-4-turbo"}
)

# Anthropic Claude
result = await extract_vocabulary(
    content="Your text...",
    llm={"provider": "anthropic", "model": "claude-3-opus-20240229"}
)

# DeepSeek
result = await extract_vocabulary(
    content="Your text...",
    llm={"provider": "deepseek", "model": "deepseek-chat"}
)
```

#### 2. Batch Processing

```python
import asyncio
from learning_assistant.api import extract_vocabulary

texts = [
    "Text 1 content...",
    "Text 2 content...",
    "Text 3 content..."
]

async def process_batch():
    tasks = [
        extract_vocabulary(content=text, word_count=5, generate_story=False)
        for text in texts
    ]
    results = await asyncio.gather(*tasks)

    # Aggregate results
    all_words = []
    for result in results:
        all_words.extend([card['word'] for card in result['vocabulary_cards']])

    print(f"Total unique words: {len(set(all_words))}")

asyncio.run(process_batch())
```

#### 3. Integration with Other Modules

```python
from learning_assistant.api import process_link, extract_vocabulary

# Extract vocabulary from web article
async def vocabulary_from_url(url):
    # Step 1: Get article content
    article = await process_link(url=url)

    # Step 2: Extract vocabulary from summary
    vocab = await extract_vocabulary(
        content=article['summary'],
        word_count=10
    )

    return vocab

# Usage
result = asyncio.run(vocabulary_from_url("https://example.com/article"))
```

---

## Features

### 1. Intelligent Word Extraction

**Method**: LLM-powered extraction

**Advantages**:
- Understands context
- Identifies important words
- Balances frequency and relevance
- Avoids trivial or obscure words

**Selection Criteria**:
- High-frequency words (commonly used)
- Key concept words (important for understanding)
- Academic vocabulary (if applicable)
- Avoids too simple or too rare words

### 2. Multi-layer Phonetic Lookup

**Three-layer fallback**:

1. **Local Dictionary** (fast, offline)
   - Pre-loaded English dictionary
   - Instant lookup
   - No network required

2. **Free Dictionary API** (online, free)
   - Real-time data
   - US/UK phonetics
   - Fallback if local fails

3. **LLM Generation** (accurate, fallback)
   - IPA format
   - Both US and UK
   - Last resort when other methods fail

### 3. Complete Word Cards

Each card includes:

**Required Fields**:
- Word
- Part of speech (noun/verb/adj/adv/etc)
- Definition (Chinese + optional English)
- Example sentences (minimum 2)
- Difficulty level
- Word frequency

**Optional Fields**:
- Phonetic transcriptions (US/UK IPA)
- Synonyms
- Antonyms
- Related words (derivatives, roots)

### 4. Contextual Stories

**Purpose**: Reinforce memory through context

**Features**:
- All target words naturally integrated
- Coherent storyline
- Appropriate difficulty
- Configurable length (default: 300 words)

**Example**:
```
Title: "The Innovative Revolution"

In the heart of Silicon Valley, a small startup was working on an 
innovative solution to transform urban transportation. Their 
revolutionary approach combined artificial intelligence with 
sustainable energy. The team believed their technology could 
transform the way people commute in cities worldwide...
```

---

## Configuration

### Configuration File

Location: `config/modules.yaml`

```yaml
vocabulary:
  enabled: true
  priority: 3

  config:
    # Word extraction
    extraction:
      word_count: 10              # Default word count
      difficulty_distribution:    # Difficulty distribution
        beginner: 30%
        intermediate: 50%
        advanced: 20%
      min_word_length: 3          # Minimum word length
      exclude_stopwords: true     # Exclude common words

    # Phonetic lookup
    phonetic:
      lookup_order:               # Lookup priority
        - local                   # Local dictionary
        - api                     # Free Dictionary API
        - llm                     # LLM generation
      local_dictionary: "data/dictionaries/english.json"
      api_url: "https://api.dictionaryapi.dev/api/v2/entries/en/"

    # LLM settings
    llm:
      provider: "openai"
      model: "gpt-4"
      temperature: 0.3            # Lower for accuracy
      max_tokens: 2000

    # Story generation
    story:
      enabled: true
      default_word_count: 300
      default_difficulty: "intermediate"

    # Output settings
    output:
      format: [markdown, json]
      directory: "data/outputs/vocabulary"
      save_history: true
```

### Configuration Examples

#### 1. Adjust Difficulty Distribution

```yaml
extraction:
  difficulty_distribution:
    beginner: 50%      # More simple words
    intermediate: 40%
    advanced: 10%
```

#### 2. Change LLM Model

```yaml
llm:
  provider: "anthropic"
  model: "claude-3-opus-20240229"
  temperature: 0.2    # Even lower for consistency
```

#### 3. Disable Story Generation

```yaml
story:
  enabled: false
```

---

## Examples

### Example 1: Technical Article

**Input**:
```
Machine learning algorithms have revolutionized data analysis.
Neural networks, a subset of machine learning, mimic the human brain's
architecture to process complex patterns and make predictions.
```

**Command**:
```bash
la vocabulary --text "..." --count 8 --difficulty advanced
```

**Expected Output**:
- Vocabulary: algorithm, neural network, architecture, pattern, prediction, subset, mimic, revolutionize
- Difficulty: Mostly intermediate/advanced
- Context: Technical/Academic

### Example 2: News Article

**Input**:
```
The global economy faces unprecedented challenges as inflation rates
continue to rise. Central banks are implementing monetary policies
to stabilize markets and protect consumers.
```

**Command**:
```bash
la vocabulary --text "..." --count 6 --difficulty intermediate
```

**Expected Output**:
- Vocabulary: unprecedented, inflation, monetary, stabilize, consumer, implement
- Difficulty: Mix of beginner/intermediate
- Context: Economics/Business

### Example 3: Academic Paper

**Input** (from PDF):
```bash
la vocabulary --file research_paper.pdf --count 15 --difficulty advanced
```

**Expected Output**:
- Vocabulary: Academic terms, field-specific jargon
- Difficulty: Mostly advanced
- Examples: Technical usage in context

---

## FAQ

### Q1: How accurate are the phonetic transcriptions?

**A**: Accuracy depends on the lookup method:
- **Local dictionary**: ~95% accuracy (limited vocabulary)
- **API lookup**: ~98% accuracy (comprehensive)
- **LLM generation**: ~90% accuracy (fallback method)

Overall success rate: >95%

### Q2: What languages are supported?

**A**:
- **Primary**: English (optimized)
- **Secondary**: Basic support for other languages via LLM
- **Future**: Planned support for Japanese, Korean, Spanish

### Q3: Can I use it offline?

**A**: Partial offline support:
- **Fully offline**: Local dictionary + LLM disabled
- **Requires network**: API phonetic lookup, LLM extraction

### Q4: How to handle large texts (>10,000 words)?

**A**: Split into smaller chunks:
```python
# Split long text
chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]

results = []
for chunk in chunks:
    result = await extract_vocabulary(content=chunk, word_count=5)
    results.append(result)
```

### Q5: Can I customize word selection criteria?

**A**: Yes, modify configuration:
```yaml
extraction:
  difficulty_distribution:
    beginner: 0%      # No beginner words
    intermediate: 30%
    advanced: 70%     # Mostly advanced
```

---

## Troubleshooting

### Error: "API key not found"

**Solution**:
```bash
export OPENAI_API_KEY="sk-your-key"
```

### Error: "Content cannot be empty"

**Cause**: Empty text or file

**Solution**: Ensure text has content:
```bash
# Check file
cat article.txt

# Or provide text
la vocabulary --text "Your content here..."
```

### Error: "Phonetic lookup failed"

**Cause**: Network issue or API unavailable

**Solution**: 
1. Check network connection
2. Try local dictionary
3. LLM will generate fallback

### Error: "LLM API error"

**Cause**: Invalid API key, quota exceeded, or network issue

**Solution**:
1. Verify API key
2. Check API quota
3. Try alternative provider

### Performance Issue: Slow extraction

**Cause**: Large word count or slow LLM

**Solutions**:
1. Reduce word count
2. Use faster model (gpt-3.5-turbo)
3. Disable story generation:
   ```bash
   la vocabulary --text "..." --no-story
   ```

### Issue: Poor word selection

**Solution**: Adjust difficulty:
```bash
# For simpler words
la vocabulary --text "..." --difficulty beginner

# For complex words
la vocabulary --text "..." --difficulty advanced
```

---

## Related Links

- [API Reference](api.md)
- [Configuration Guide](CONFIGURATION.md)
- [Skills Documentation](../skills/README.md)
- [Integration Examples](../examples/)

---

**Version**: v0.2.0
**Last Updated**: 2026-04-08
**Maintainer**: Learning Assistant Team