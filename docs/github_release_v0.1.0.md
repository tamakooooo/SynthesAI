# GitHub Release v0.1.0 发布指南

> **版本**: v0.1.0 (MVP)
> **发布日期**: 2026-03-31
> **状态**: 准备发布

---

## 发布信息

### 标签信息
- **标签名称**: `v0.1.0`
- **标签消息**: `Learning Assistant v0.1.0 - MVP Release`

### Release 标题
```
Learning Assistant v0.1.0 (MVP) - 首个正式版本发布 🎉
```

---

## 发布说明

### 🎯 项目简介

**Learning Assistant** 是一个模块化、插件化、安全的 AI 驱动学习 CLI 工具平台。通过 AI 技术加速知识获取和整理，解决学习效率问题。

### ✨ 核心特性

- ✅ **完全插件化架构** - 模块 + 适配器，轻松扩展
- ✅ **配置驱动** - 零代码扩展功能
- ✅ **安全优先** - 只用官方 SDK，无第三方风险
- ✅ **多平台支持** - B站、YouTube、抖音等主流视频平台
- ✅ **多 LLM 支持** - OpenAI、Anthropic、DeepSeek
- ✅ **免费转录** - 使用 BcutASR（B站必剪）免费云端服务
- ✅ **测试完善** - 432个测试全部通过，覆盖率>80%

### 📦 本次发布内容

#### 核心引擎
- ConfigManager - 配置管理系统
- EventBus - 事件总线
- PluginManager - 插件管理器
- HistoryManager - 历史记录管理
- TaskManager - 任务状态管理

#### LLM 服务
- LLMService - 统一 LLM 调用接口
- OpenAI / Anthropic / DeepSeek 适配器
- 重试机制和成本控制

#### CLI 工具
- Typer CLI 框架
- setup / version / list-plugins 命令
- Rich 输出美化

#### 视频总结模块（核心功能）
- VideoDownloader - yt-dlp 视频下载（支持 B站、YouTube、抖音）
- AudioExtractor - FFmpeg 音频提取
- AudioTranscriber - BcutASR 语音转录（免费云端服务）
- 多格式字幕导出（SRT/VTT/LRC/ASS）
- 词级时间戳支持
- PromptTemplate - YAML 模板系统
- MarkdownExporter / PDFExporter - 多格式导出

#### 适配器框架
- BaseAdapter - 生命周期管理、事件订阅、错误追踪
- TestValidationAdapter / AsyncTestAdapter / ErrorSimulationAdapter

**注意**: 飞书适配器已在 v0.2.0 中移除，后续版本将实现思源笔记和 Obsidian 适配器。

#### 测试和质量
- 432 个单元测试（100% 通过率）
- 测试覆盖率 >80%
- Mypy 类型检查通过
- Black 代码格式化通过
- Ruff 代码质量检查通过

#### 文档
- README.md - 项目概述
- 用户使用指南 (docs/user-guide.md)
- 插件开发教程 (docs/plugin-development.md)
- API 文档 (docs/api.md)
- FAQ 文档 (docs/faq.md)
- CHANGELOG.md

### 🔐 安全特性

- ✅ API Key 从环境变量读取，不硬编码
- ✅ 只使用官方 SDK（OpenAI、Anthropic）
- ✅ 无第三方中间层（如 LiteLLM）
- ✅ 本地数据完全自主控制
- ✅ 定期安全审计

### 📊 性能指标

- 视频转录准确率: >95% (使用 BcutASR)
- 总结生成时间: <30s (10分钟视频, 取决于 LLM)
- 插件加载时间: <500ms
- 测试运行时间: ~8分40秒

### 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/yourname/learning-assistant.git
cd learning-assistant

# 安装依赖
pip install -e ".[dev]"

# 首次配置
la setup

# 开始使用
la video https://www.bilibili.com/video/BV123
```

### 📖 文档资源

- **README**: [README.md](README.md)
- **用户指南**: [docs/user-guide.md](docs/user-guide.md)
- **插件开发**: [docs/plugin-development.md](docs/plugin-development.md)
- **API 文档**: [docs/api.md](docs/api.md)
- **常见问题**: [docs/faq.md](docs/faq.md)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

### 🎯 下一步计划

**v0.2.0 (下一版本)**:
- 🔗 链接学习模块
- 📚 单词学习模块
- ⚡ 批量处理功能
- 📊 性能优化

**v0.3.0 (中期)**:
- Obsidian 适配器
- 批量处理功能
- 学习路径推荐
- Web UI（可选）

### 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## Assets（上传文件）

发布时需要上传以下文件：

1. **Wheel 包**: `dist/learning_assistant-0.1.0-py3-none-any.whl` (82KB)
2. **源码包**: `dist/learning_assistant-0.1.0.tar.gz` (26MB)

---

## 发布步骤

### 方式 1: GitHub Web UI

1. 访问 https://github.com/yourname/learning-assistant/releases/new
2. 选择标签: `v0.1.0`（如果没有，点击 "Create new tag"）
3. Release 标题: `Learning Assistant v0.1.0 (MVP) - 首个正式版本发布 🎉`
4. 描述: 复制上面的 "发布说明" 内容
5. 上传 Assets:
   - `dist/learning_assistant-0.1.0-py3-none-any.whl`
   - `dist/learning_assistant-0.1.0.tar.gz`
6. 选择 "This is a pre-release"（可选，因为这是 MVP）
7. 点击 "Publish release"

### 方式 2: GitHub CLI

```bash
# 创建标签
git tag -a v0.1.0 -m "Learning Assistant v0.1.0 - MVP Release"
git push origin v0.1.0

# 创建 Release
gh release create v0.1.0 \
  --title "Learning Assistant v0.1.0 (MVP) - 首个正式版本发布 🎉" \
  --notes-file docs/github_release_v0.1.0.md \
  dist/learning_assistant-0.1.0-py3-none-any.whl \
  dist/learning_assistant-0.1.0.tar.gz
```

---

## 发布后检查清单

- [ ] 标签已创建并推送到 GitHub
- [ ] Release 已发布
- [ ] Assets 已上传
- [ ] README.md 中的下载链接已更新（如果有）
- [ ] CHANGELOG.md 中的链接已更新
- [ ] 社交媒体/社区公告已发布（可选）

---

**最后更新**: 2026-03-31
**版本**: v0.1.0 (MVP)