# Configuration Guide - API Key Management

## Overview

Learning Assistant supports flexible API key management through configuration files and environment variables.

## Configuration Files

### 1. `config/settings.yaml` (Public Configuration)

This file contains:
- Default settings (log level, cache, etc.)
- LLM provider configurations (models, base URLs, timeouts)
- Environment variable names for API keys

**This file is committed to git** - do NOT put real API keys here.

### 2. `config/settings.local.yaml` (Private Configuration)

This file contains:
- Real API keys
- Local overrides (custom models, base URLs, etc.)

**This file is NOT committed to git** - it's ignored via `.gitignore`.

## Setup Instructions

### Quick Start

1. **Copy the example file**:
   ```bash
   cd config
   cp settings.local.yaml.example settings.local.yaml
   ```

2. **Edit `settings.local.yaml`** and add your API keys:
   ```yaml
   llm:
     default_provider: "openai"

     providers:
       openai:
         api_key: "sk-your-real-api-key-here"
         base_url: "https://api.tamako.online/v1"  # Optional custom endpoint
         default_model: "kimi-k2.5"
   ```

3. **Done!** No environment variables needed.

### Environment Variables (Optional)

You can still use environment variables. Priority order:

1. **Environment variables** (highest priority)
2. **settings.local.yaml** (medium priority)
3. **settings.yaml** (lowest priority)

Example:
```bash
# Option 1: Environment variable (overrides config file)
export OPENAI_API_KEY="sk-your-api-key"
la video https://example.com/video

# Option 2: Configuration file (no environment variable needed)
# Just set api_key in settings.local.yaml
la video https://example.com/video
```

## Configuration Examples

### OpenAI (or compatible endpoints)

```yaml
llm:
  providers:
    openai:
      api_key: "sk-xxxxx"
      base_url: "https://api.openai.com/v1"  # Default
      # OR custom endpoint:
      # base_url: "https://api.tamako.online/v1"
      default_model: "gpt-4o"
```

### Anthropic

```yaml
llm:
  providers:
    anthropic:
      api_key: "sk-ant-xxxxx"
      default_model: "claude-3-5-sonnet-20241022"
```

### DeepSeek

```yaml
llm:
  providers:
    deepseek:
      api_key: "sk-xxxxx"
      base_url: "https://api.deepseek.com/v1"
      default_model: "deepseek-chat"
```

## Security Best Practices

1. **Never commit `settings.local.yaml`** - it's in `.gitignore` for a reason
2. **Use environment variables in production** - more secure for CI/CD
3. **Restrict file permissions**:
   ```bash
   chmod 600 config/settings.local.yaml
   ```
4. **Rotate API keys** if they're accidentally committed

## Multiple Environments

You can create different config files for different environments:

```bash
# Development
config/settings.local.yaml

# Production (use environment variables)
export OPENAI_API_KEY="sk-prod-key"
```

## Authentication Cookies

Video platform authentication cookies are also stored locally:

- Location: `config/cookies/`
- Files: `bilibili_cookies.txt`, etc.
- **Not committed to git**

Use the auth command to manage cookies:
```bash
la auth login --platform bilibili
la auth status --platform bilibili
la auth logout --platform bilibili
```

## Troubleshooting

### API Key Not Found

```
Error: API key not found
```

**Solution**: Add API key to `config/settings.local.yaml`:
```yaml
llm:
  providers:
    openai:
      api_key: "sk-your-key-here"
```

### Configuration Not Loading

Check that files exist:
```bash
ls -la config/
# Should see:
# settings.yaml
# settings.local.yaml
```

### Environment Variable Override

If you set both environment variable AND config file, environment variable wins:
```bash
export OPENAI_API_KEY="sk-from-env"
# This will be used even if settings.local.yaml has a different key
```

## File Structure

```
config/
├── settings.yaml              # Public config (committed)
├── settings.local.yaml        # Private config with API keys (NOT committed)
├── settings.local.yaml.example # Template for settings.local.yaml
├── modules.yaml               # Module configurations
├── adapters.yaml              # Adapter configurations
└── cookies/                   # Authentication cookies (NOT committed)
    ├── bilibili_cookies.txt
    └── .gitkeep
```

## Summary

- **Use `settings.local.yaml` for API keys** - easy, persistent, secure
- **Or use environment variables** - good for production/CI
- **Never commit sensitive files** - protected by `.gitignore`
- **Priority: env vars > settings.local.yaml > settings.yaml**