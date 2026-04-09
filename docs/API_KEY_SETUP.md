# API Key Configuration - Quick Reference

## ✅ Configuration Complete

Your API keys are now managed through configuration files!

## 📝 What Changed

### Before
```bash
# Had to set environment variable every time
export OPENAI_API_KEY="sk-xxxxx"
la video https://example.com/video
```

### After
```bash
# API key saved in config file - no environment variable needed!
la video https://example.com/video
```

## 🔧 Configuration Files

### `config/settings.yaml` (Public - Committed to Git)
- Contains public settings and templates
- Environment variable names (e.g., `api_key_env: "OPENAI_API_KEY"`)
- Default models, timeouts, etc.

### `config/settings.local.yaml` (Private - NOT Committed)
- Contains real API keys
- Your personal settings
- **Already created with your API key!**

## 🔐 Security

- ✅ `settings.local.yaml` is in `.gitignore` - won't be committed
- ✅ Cookie files in `config/cookies/` are also ignored
- ✅ File permissions set automatically

## 🎯 Priority Order

When loading API keys, the system checks:

1. **Environment variable** (highest priority) - `OPENAI_API_KEY`
2. **settings.local.yaml** - `api_key: "sk-xxxxx"`
3. **settings.yaml** (lowest priority) - `api_key: "sk-xxxxx"`

## 📚 Documentation

- Full guide: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- Example file: [config/settings.local.yaml.example](config/settings.local.yaml.example)

## 🚀 Quick Start

```bash
# 1. Edit config/settings.local.yaml (already done for you!)
# 2. Run any command - API key is automatically loaded
la video https://www.bilibili.com/video/BV1JPXrBjENo
la auth login --platform bilibili
la link https://example.com/article
```

## 💡 Tips

- For production/CI: use environment variables
- For local development: use `settings.local.yaml`
- Never commit `settings.local.yaml` or `config/cookies/*.txt`

---

Your API key is now configured and ready to use! 🎉