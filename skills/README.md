# Learning Assistant Skills

> **Version**: v0.3.0
> **Last Updated**: 2026-04-11

Claude Code Skills for Learning Assistant - standardized, reusable capabilities following the Claude Code Skills Specification (2026).

---

## What are Skills?

Skills are modular, reusable capabilities packaged as standardized `SKILL.md` files. Each skill provides specialized instructions that Claude can automatically invoke when needed.

**Key Features**:
- ✅ **Progressive disclosure** - Lightweight metadata loads first, full content on demand
- ✅ **Automatic invocation** - Claude activates skills based on context matching
- ✅ **Slash command support** - Manual invocation via `/skill-name`
- ✅ **Composable** - Multiple skills can work together

---

## Available Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [video-summary](video-summary/SKILL.md) | Summarizes video content from URLs (B站/YouTube/抖音) | ✅ Available |
| [link-learning](link-learning/SKILL.md) | Extracts knowledge from web links and generates knowledge cards | ✅ Available |
| [vocabulary](vocabulary/SKILL.md) | Extracts vocabulary from text and generates visual knowledge cards | ✅ Available |
| [list-skills](list-skills/SKILL.md) | Lists all available Learning Assistant skills | ✅ Available |
| [learning-history](learning-history/SKILL.md) | Queries learning history records | ✅ Available |

---

## Quick Start

### For Claude Code Users

Skills are automatically discovered. Just mention what you need:

```
User: Summarize this video https://www.bilibili.com/video/BV...

Claude: [Automatically loads video-summary skill]
I'll summarize this video for you...
```

Or use slash commands:
```
/video-summary https://www.youtube.com/watch?v=...
/list-skills
/learning-history --limit 10
```

### For Python Developers

Call the Python API directly:

```python
from learning_assistant.api import summarize_video

# Video summary
result = await summarize_video(url="https://...")
print(result["title"])

# List skills
from learning_assistant.api import list_available_skills
skills = list_available_skills()

# View history
from learning_assistant.api import get_recent_history
records = get_recent_history(limit=10)
```

---

## Skill Structure

Each skill follows the Claude Code Skills standard:

```
skill-name/
├── SKILL.md                    # Required: Main skill file
└── references/                 # Optional: Detailed documentation
    ├── api-guide.md
    ├── examples.md
    └── error-handling.md
```

### SKILL.md Format

Every `SKILL.md` has two parts:

**1. YAML Frontmatter** (metadata):
```yaml
---
name: skill-name
description: |
  What the skill does + when to use it.
  Includes trigger phrases for automatic activation.
metadata:
  version: 1.0.0
  author: Your Name
---
```

**2. Markdown Body** (instructions):
```markdown
# Skill Name

Brief description and quick start.

## Inputs
- Parameters...

## Output
- Expected results...

## Examples
- Usage examples...
```

---

## Integration Guide

### Claude Code Integration

Skills are automatically loaded from:
- `~/.claude/skills/` (global)
- `.claude/skills/` (project-specific)
- `skills/` (current directory)

**Install these skills**:
```bash
# Clone Learning Assistant
git clone https://github.com/yourname/learning-assistant.git
cd learning-assistant

# Skills are in skills/ directory
# Claude Code will discover them automatically
```

### Custom Agent Integration

Use the Python API directly:

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# Use any skill
result = await api.summarize_video(url="...")
skills = api.list_skills()
records = api.get_history()
```

See [Agent Integration Guide](../docs/agent_integration.md) for details.

---

## Skill Discovery

Claude automatically discovers skills by reading the YAML frontmatter. The `description` field should include:

1. **What** the skill does
2. **When** to use it
3. **Trigger phrases** for automatic activation

**Example**:
```yaml
description: |
  Summarizes video content from URLs (B站/YouTube/抖音).
  
  Use when user:
  - Provides video URLs (bilibili.com, youtube.com, douyin.com)
  - Asks to "summarize video", "analyze this video"
  - Mentions "视频总结", "总结视频"
```

---

## Performance Characteristics

| Skill | Execution Time | Notes |
|-------|---------------|-------|
| video-summary | 3-14 min | Depends on video length |
| link-learning | 10-30s | Web fetching + processing |
| vocabulary | <60s | Word extraction + card generation |
| list-skills | <10ms | Very fast |
| learning-history | <100ms | Fast for most queries |

---

## Contributing

Want to create your own skills?

1. Create a new directory: `skills/your-skill-name/`
2. Create `SKILL.md` with YAML frontmatter + Markdown body
3. Include trigger phrases in description
4. Test with Claude Code

**Best Practices**:
- Keep SKILL.md under 500 lines
- Use `references/` for detailed content
- Include clear examples
- Add error handling guidance

---

## Troubleshooting

### Skills Not Loading

**Check**:
- File is named `SKILL.md` (case-sensitive)
- YAML frontmatter is valid
- `name` field matches folder name (kebab-case)
- No XML tags in frontmatter

### Skill Not Activating

**Verify**:
- `description` includes trigger phrases
- Trigger phrases match your request
- Skill status is "available"

### Python API Errors

**Solutions**:
```bash
# Check dependencies
pip install -e ".[dev]"

# Verify API keys
export OPENAI_API_KEY="sk-..."

# Test API
python -c "from learning_assistant.api import list_available_skills; print(list_available_skills())"
```

---

## Resources

- **Skills Documentation**: This directory
- **Agent Integration**: [docs/agent_integration.md](../docs/agent_integration.md)
- **API Reference**: [docs/api.md](../docs/api.md)
- **Claude Code Skills Spec**: [Anthropic Docs](https://docs.anthropic.com/claude-code/skills)

---

## Next Steps

1. **Explore Skills**: Read individual SKILL.md files
2. **Try Examples**: Use the quick start examples above
3. **Integrate**: Follow the integration guide
4. **Create Skills**: Build your own following the standard

---

**Need Help?**
- GitHub Issues: [learning-assistant/issues](https://github.com/yourname/learning-assistant/issues)
- Documentation: [learning-assistant.readthedocs.io](https://learning-assistant.readthedocs.io)