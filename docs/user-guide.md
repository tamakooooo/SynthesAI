# Learning Assistant 用户使用指南

> 版本: v0.1.0 (MVP) | 更新日期: 2026-03-31

## 目录

- [快速开始](#快速开始)
- [安装指南](#安装指南)
- [配置指南](#配置指南)
- [基本使用](#基本使用)
- [视频总结功能](#视频总结功能)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)

---

## 快速开始

### 系统要求

- **Python**: 3.11 或更高版本
- **操作系统**: Windows / macOS / Linux
- **FFmpeg**: 用于音视频处理
- **API Key**: OpenAI / Anthropic / DeepSeek 任选其一

### 5分钟快速上手

```bash
# 1. 克隆项目
git clone https://github.com/yourname/learning-assistant.git
cd learning-assistant

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 配置 API Key
export OPENAI_API_KEY="your-api-key-here"

# 4. 首次配置
la setup

# 5. 开始使用
la video https://www.bilibili.com/video/BV1234567890
```

---

## 安装指南

### 1. 安装 Python 3.11+

**Windows**:
```bash
# 从 python.org 下载安装包
https://www.python.org/downloads/

# 或使用 winget
winget install Python.Python.3.11
```

**macOS**:
```bash
# 使用 Homebrew
brew install python@3.11
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev
```

### 2. 安装 FFmpeg

**Windows**:
```bash
# 使用 Chocolatey
choco install ffmpeg

# 或从官网下载
https://ffmpeg.org/download.html
```

**macOS**:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install ffmpeg
```

**验证安装**:
```bash
ffmpeg -version
```

### 3. 安装 Learning Assistant

**方法一：从源码安装（推荐）**
```bash
# 克隆仓库
git clone https://github.com/yourname/learning-assistant.git
cd learning-assistant

# 创建虚拟环境（推荐）
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e ".[dev]"
```

**方法二：从 PyPI 安装（即将支持）**
```bash
pip install learning-assistant
```

### 4. 验证安装

```bash
# 检查版本
la version

# 运行测试
pytest

# 检查插件
la list-plugins
```

---

## 配置指南

### 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
# LLM API Keys（至少配置一个）
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="sk-..."

# 可选配置
export LEARNING_ASSISTANT_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export LEARNING_ASSISTANT_CONFIG_DIR="config"  # 配置目录路径
```

### 配置文件

配置文件位于 `config/` 目录：

**`config/settings.yaml`** - 全局设置
```yaml
app:
  name: "Learning Assistant"
  version: "0.1.0"
  log_level: "INFO"

llm:
  default_provider: "openai"  # openai, anthropic, deepseek

  providers:
    openai:
      model: "gpt-4"
      api_key_env: "OPENAI_API_KEY"

    anthropic:
      model: "claude-3-opus-20240229"
      api_key_env: "ANTHROPIC_API_KEY"

    deepseek:
      model: "deepseek-chat"
      api_key_env: "DEEPSEEK_API_KEY"

modules:
  video_summary:
    enabled: true
    transcriber: "bcut"
    word_timestamps: false
    export_format: "markdown"

adapters:
  # 适配器功能已停止开发，保留基础框架用于测试
```

**`config/modules.yaml`** - 模块配置
```yaml
video_summary:
  download_dir: "data/downloads"
  audio_dir: "data/audio"
  output_dir: "data/outputs"

  # 转录配置
  transcriber: "bcut"  # 使用 BcutASR（免费）
  word_timestamps: false

  # 导出配置
  export_format: "markdown"  # markdown, pdf, both
  export_template: "video_summary.md"
```

### 首次配置向导

运行配置向导：

```bash
la setup
```

这将引导你完成：
1. 选择默认 LLM 提供商
2. 配置 API Key
3. 设置下载和输出目录
4. 选择默认配置

---

## 基本使用

### CLI 命令概览

```bash
la [OPTIONS] COMMAND [ARGS]...

Commands:
  setup        首次配置向导
  version      显示版本信息
  list-plugins 列出已安装插件
  video        视频总结命令
  history      查看历史记录
```

### 常用命令

#### 1. 查看版本

```bash
la version
```

输出示例：
```
Learning Assistant v0.1.0
Python: 3.11.9
Platform: Windows-10
```

#### 2. 列出插件

```bash
la list-plugins
```

输出示例：
```
Loaded Modules (3):
  - video_summary (enabled)
  - link_learning (enabled)
  - vocabulary (enabled)

Loaded Adapters (1):
  - test_validation (enabled)  # 测试适配器
```

#### 3. 查看历史记录

```bash
la history

# 查看最近10条
la history --limit 10

# 搜索关键词
la history --search "Python"
```

---

## 视频总结功能

### 基本用法

```bash
# 总结 B站视频
la video https://www.bilibili.com/video/BV1234567890

# 总结 YouTube 视频
la video https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 总结抖音视频
la video https://www.douyin.com/video/1234567890
```

### 高级选项

```bash
# 指定输出格式
la video https://example.com/video --format pdf

# 指定语言
la video https://example.com/video --language en

# 指定输出目录
la video https://example.com/video --output ./my-summaries

# 启用词级时间戳
la video https://example.com/video --word-timestamps

# 只导出字幕
la video https://example.com/video --subtitle-only --format srt
```

### 处理流程

视频总结功能执行以下步骤：

```
1. 下载视频 (yt-dlp)
   ├─ 提取视频信息
   └─ 下载视频文件

2. 提取音频 (FFmpeg)
   ├─ 分离音频轨道
   └─ 转换为 MP3 格式

3. 语音转录 (BcutASR)
   ├─ 上传音频文件
   ├─ 等待转录完成
   └─ 下载转录结果

4. 生成总结 (LLM)
   ├─ 使用 Prompt 模板
   ├─ 调用 LLM API
   └─ 解析 JSON 结果

5. 导出输出 (Markdown/PDF)
   ├─ 渲染模板
   └─ 保存文件
```

### 输出示例

**Markdown 输出** (`data/outputs/video_summary.md`):
```markdown
# [视频标题] 学习笔记

## 📌 基本信息
- **视频时长**: 15分钟
- **上传者**: UP主名称
- **平台**: B站
- **观看日期**: 2026-03-31

## 📝 视频摘要
本视频介绍了...

## 🎯 核心要点

### 1. 第一个要点
- 详细内容...
- 示例说明...

### 2. 第二个要点
- 详细内容...

## 💡 关键知识点
- 知识点1: 解释
- 知识点2: 解释

## 🔗 相关资源
- [视频链接](https://...)
```

**字幕文件** (`data/outputs/video_subtitle.srt`):
```
1
00:00:00,000 --> 00:00:05,000
大家好，欢迎来到...

2
00:00:05,000 --> 00:00:10,000
今天我们要讲的是...
```

### Cookie 配置（可选）

某些视频可能需要登录才能下载：

**B站 Cookie**:
1. 登录 B站
2. 使用浏览器开发者工具导出 Cookie
3. 保存为 `data/cookies/bilibili.txt`

**使用 Cookie**:
```bash
la video https://www.bilibili.com/video/BV... \
  --cookie data/cookies/bilibili.txt
```

或配置文件：
```yaml
# config/modules.yaml
video_summary:
  cookie_file: "data/cookies/bilibili.txt"
```

---

## 故障排除

### 常见问题

#### 1. FFmpeg 未找到

**错误信息**:
```
RuntimeError: FFmpeg not found. Please install FFmpeg first.
```

**解决方法**:
```bash
# 安装 FFmpeg（参见安装指南）
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

#### 2. API Key 无效

**错误信息**:
```
ValueError: OpenAI API key not found. Set OPENAI_API_KEY environment variable.
```

**解决方法**:
```bash
# 设置环境变量
export OPENAI_API_KEY="sk-..."

# 或在 .env 文件中配置
echo "OPENAI_API_KEY=sk-..." >> .env
```

#### 3. 视频下载失败

**可能原因**:
- 视频需要登录（配置 Cookie）
- 视频不存在或已删除
- 网络连接问题
- 地区限制

**解决方法**:
```bash
# 1. 配置 Cookie
la video https://... --cookie data/cookies/bilibili.txt

# 2. 尝试其他视频
la video https://www.youtube.com/watch?v=...

# 3. 检查网络
ping www.bilibili.com
```

#### 4. 转录失败

**错误信息**:
```
RuntimeError: BcutASR transcription failed: Rate limit exceeded
```

**解决方法**:
- BcutASR 有频率限制，等待几分钟后重试
- 或使用其他转录服务（将在后续版本支持）

#### 5. 内存不足

**错误信息**:
```
MemoryError: Unable to allocate array
```

**解决方法**:
```bash
# 1. 关闭其他程序
# 2. 使用较小的视频
# 3. 增加虚拟内存（Windows）
```

### 日志调试

启用详细日志：

```bash
# 设置日志级别
export LEARNING_ASSISTANT_LOG_LEVEL="DEBUG"

# 运行命令
la video https://...
```

日志文件位置：`logs/learning_assistant.log`

### 获取帮助

- **文档**: [https://learning-assistant.readthedocs.io](https://learning-assistant.readthedocs.io)
- **Issues**: [https://github.com/yourname/learning-assistant/issues](https://github.com/yourname/learning-assistant/issues)
- **FAQ**: [docs/faq.md](faq.md)

---

## 最佳实践

### 1. API Key 管理

- ✅ 使用环境变量存储 API Key
- ✅ 不要将 API Key 提交到版本控制
- ✅ 定期轮换 API Key
- ✅ 为不同环境使用不同的 Key

### 2. 视频选择

- ✅ 选择内容清晰、语音标准的视频
- ✅ 避免背景噪音大的视频
- ✅ 优先选择字幕完整的视频
- ✅ 注意视频时长（建议 5-30 分钟）

### 3. 输出管理

- ✅ 定期清理 `data/outputs/` 目录
- ✅ 使用版本控制管理学习笔记
- ✅ 分类整理输出文件

### 4. 性能优化

- ✅ 使用缓存避免重复下载
- ✅ 批量处理时注意 API 调用限制
- ✅ 合理设置并发数

### 5. 学习建议

- ✅ 先观看视频，再查看总结
- ✅ 结合字幕和总结学习
- ✅ 标记重点内容
- ✅ 定期复习学习笔记

---

## 下一步

- 📖 阅读 [API 文档](api.md)
- 🔌 学习 [插件开发](plugin-development.md)
- ❓ 查看 [常见问题](faq.md)
- 📝 查看 [更新日志](../CHANGELOG.md)

---

**需要帮助？**
- GitHub Issues: [提交问题](https://github.com/yourname/learning-assistant/issues)
- 文档网站: [learning-assistant.readthedocs.io](https://learning-assistant.readthedocs.io)