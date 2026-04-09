# 常见问题 (FAQ)

> 版本: v0.1.0 | 更新日期: 2026-03-31

## 安装相关

### Q: 如何安装 FFmpeg？

**A**: 
- Windows: `choco install ffmpeg`
- macOS: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`

### Q: 支持哪些 Python 版本？

**A**: Python 3.11 或更高版本。

## 配置相关

### Q: API Key 配置在哪里？

**A**: 通过环境变量配置：
```bash
export OPENAI_API_KEY="sk-..."
```

### Q: 支持哪些 LLM 提供商？

**A**: OpenAI、Anthropic、DeepSeek。

## 使用相关

### Q: 支持哪些视频平台？

**A**: B站、YouTube、抖音等主流平台。

### Q: 视频转录是免费的吗？

**A**: 是的，使用 BcutASR（B站必剪）免费云端服务。

### Q: 为什么视频下载失败？

**A**: 可能原因：
1. 视频需要登录 - 配置 Cookie
2. 网络问题 - 检查网络连接
3. 地区限制 - 使用代理

## 开发相关

### Q: 如何开发自定义模块？

**A**: 参考 [插件开发教程](plugin-development.md)。

### Q: 如何运行测试？

**A**: `pytest`

---

更多问题请提交 GitHub Issues。
