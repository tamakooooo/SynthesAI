# Learning Assistant 示例演示

> **版本**: v0.1.0 (MVP)
> **更新日期**: 2026-03-31

本文档提供 Learning Assistant 的完整使用示例和演示。

---

## 目录

- [快速演示](#快速演示)
- [视频总结示例](#视频总结示例)
- [CLI 命令示例](#cli-命令示例)
- [输出示例](#输出示例)
- [故障排除示例](#故障排除示例)

---

## 快速演示

### 5 分钟快速上手

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

# 5. 处理第一个视频
la video https://www.bilibili.com/video/BV1GJ411x7h7
```

---

## 视频总结示例

### 示例 1: B站视频总结

**视频**: Python 编程教程

```bash
# 基本用法
la video https://www.bilibili.com/video/BV1GJ411x7h7

# 高级用法：指定输出格式和目录
la video https://www.bilibili.com/video/BV1GJ411x7h7 \
  --format markdown \
  --output ./my-notes \
  --language zh
```

**预期输出**:
```
2026-03-31 20:00:00 | INFO | Step 1/5: Downloading video...
2026-03-31 20:00:30 | INFO | Video downloaded: Python编程教程.mp4
2026-03-31 20:00:30 | INFO | Step 2/5: Extracting audio...
2026-03-31 20:01:00 | INFO | Audio extracted: audio.mp3
2026-03-31 20:01:00 | INFO | Step 3/5: Transcribing audio...
2026-03-31 20:05:00 | INFO | Transcription completed
2026-03-31 20:05:00 | INFO | Step 4/5: Generating summary...
2026-03-31 20:05:30 | INFO | Summary generated
2026-03-31 20:05:30 | INFO | Step 5/5: Exporting output...
2026-03-31 20:05:35 | INFO | Export completed

Output files:
- Summary: ./data/outputs/python_tutorial_summary.md
- Subtitle: ./data/outputs/python_tutorial_subtitle.srt
```

---

### 示例 2: YouTube 视频总结

**视频**: Machine Learning Tutorial

```bash
# YouTube 视频
la video https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 使用 Cookie（如果需要登录）
la video https://www.youtube.com/watch?v=dQw4w9WgXcQ \
  --cookie ./data/cookies/youtube.txt
```

---

### 示例 3: 抖音视频总结

```bash
# 抖音视频
la video https://www.douyin.com/video/1234567890
```

---

## CLI 命令示例

### 1. 查看版本

```bash
la version
```

**输出**:
```
Learning Assistant v0.1.0
Python: 3.11.9
Platform: Windows-10
```

---

### 2. 列出已安装插件

```bash
la list-plugins
```

**输出**:
```
Loaded Modules (1):
  - video_summary (enabled)

Loaded Adapters (1):
  - test_validation (enabled)
```

---

### 3. 查看历史记录

```bash
# 查看最近10条记录
la history --limit 10

# 搜索关键词
la history --search "Python"

# 查看特定类型
la history --type video_summary
```

**输出**:
```
Recent Video Summaries:
1. [2026-03-31] Python编程教程 - BV1GJ411x7h7
2. [2026-03-30] Machine Learning Basics - youtube.com/watch?v=abc123
3. [2026-03-29] 数据结构详解 - BV1234567890
```

---

### 4. 首次配置向导

```bash
la setup
```

**交互式输出**:
```
Welcome to Learning Assistant Setup Wizard!

Step 1: Choose LLM Provider
? Select default LLM provider:
  > OpenAI
  > Anthropic
  > DeepSeek

Step 2: Configure API Key
? Enter OpenAI API Key: sk-...

Step 3: Set Output Directory
? Output directory [./data/outputs]: ./my-notes

Step 4: Choose Default Format
? Export format:
  > markdown
  > pdf
  > both

Configuration saved to config/settings.yaml
Setup complete! You can now use 'la video' to process videos.
```

---

## 输出示例

### Markdown 输出示例

**文件**: `python_tutorial_summary.md`

```markdown
# Python编程基础教程 学习笔记

## 📌 基本信息
- **视频时长**: 15分钟
- **上传者**: Python大师
- **平台**: B站
- **观看日期**: 2026-03-31

## 📝 视频摘要
本视频介绍了 Python 编程的基础知识，包括变量、数据类型、控制流、函数等核心概念。适合编程初学者入门学习。

## 🎯 核心要点

### 1. Python 环境搭建
- 下载并安装 Python 3.11+
- 配置环境变量
- 安装虚拟环境管理工具

### 2. 基础语法
- **变量定义**: `x = 10`
- **数据类型**: int, float, str, bool, list, dict
- **控制流**: if-else, for, while

### 3. 函数定义
- 函数语法: `def function_name(params):`
- 参数传递: 位置参数、关键字参数
- 返回值: `return result`

## 💡 关键知识点

- **Python 特点**: 简洁易读、跨平台、丰富的库
- **适用场景**: Web开发、数据分析、机器学习、自动化脚本
- **学习路径**: 基础语法 → 数据结构 → 面向对象 → 项目实战

## 🔗 相关资源
- [视频链接](https://www.bilibili.com/video/BV1GJ411x7h7)
- [Python 官网](https://www.python.org/)
- [Python 文档](https://docs.python.org/)
```

---

### 字幕输出示例

**文件**: `python_tutorial_subtitle.srt`

```srt
1
00:00:00,000 --> 00:00:05,000
大家好，欢迎来到 Python 编程基础教程

2
00:00:05,000 --> 00:00:10,000
今天我们将学习 Python 的基本语法和概念

3
00:00:10,000 --> 00:00:15,000
首先，让我们看看如何安装 Python

4
00:00:15,000 --> 00:00:20,000
访问 python.org，下载最新版本
```

---

## 故障排除示例

### 示例 1: FFmpeg 未安装

**错误**:
```
RuntimeError: FFmpeg not found. Please install FFmpeg first.
```

**解决**:
```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# 验证安装
ffmpeg -version
```

---

### 示例 2: API Key 无效

**错误**:
```
ValueError: OpenAI API key not found. Set OPENAI_API_KEY environment variable.
```

**解决**:
```bash
# 设置环境变量
export OPENAI_API_KEY="sk-..."

# 或在 .env 文件中配置
echo "OPENAI_API_KEY=sk-..." >> .env
```

---

### 示例 3: 视频下载失败

**错误**:
```
RuntimeError: Video download failed: HTTP Error 403: Forbidden
```

**解决**:
```bash
# 配置 Cookie
la video https://www.bilibili.com/video/BV... \
  --cookie ./data/cookies/bilibili.txt

# 或在配置文件中设置
# config/modules.yaml:
# video_summary:
#   cookie_file: "./data/cookies/bilibili.txt"
```

---

## 性能参考

### 处理时间参考

| 视频时长 | 下载时间 | 音频提取 | 转录时间 | 总结生成 | 总耗时 |
|---------|---------|---------|---------|---------|--------|
| 5分钟   | 30秒    | 15秒    | 2分钟   | 20秒    | ~3分钟 |
| 10分钟  | 45秒    | 20秒    | 3分钟   | 30秒    | ~4分钟 |
| 30分钟  | 1分钟   | 30秒    | 6分钟   | 45秒    | ~8分钟 |
| 60分钟  | 2分钟   | 45秒    | 10分钟  | 60秒    | ~14分钟 |

**注**: 时间仅供参考，实际取决于网络速度、CPU性能、LLM响应速度等。

---

## 最佳实践示例

### 1. 批量处理视频

```bash
# 创建批量处理脚本
cat > process_videos.sh << 'EOF'
#!/bin/bash

videos=(
  "https://www.bilibili.com/video/BV1GJ411x7h7"
  "https://www.youtube.com/watch?v=abc123"
  "https://www.douyin.com/video/1234567890"
)

for video in "${videos[@]}"; do
  echo "Processing: $video"
  la video "$video"
  sleep 60  # 等待 60 秒避免 API 限流
done
EOF

chmod +x process_videos.sh
./process_videos.sh
```

---

### 2. 自动化学习流程

```bash
# 每日学习自动化脚本
cat > daily_learning.sh << 'EOF'
#!/bin/bash

# 1. 处理新视频
la video https://www.bilibili.com/video/BV...

# 2. 查看历史记录
la history --limit 5

# 3. 搜索特定主题
la history --search "Python"

# 4. 整理输出文件
mv ./data/outputs/*.md ./my-learning-notes/
EOF

chmod +x daily_learning.sh
```

---

### 3. 定期清理缓存

```bash
# 清理超过 7 天的缓存
find ./data/cache -mtime +7 -type f -delete

# 清理超过 30 天的历史记录
find ./data/history -mtime +30 -type f -delete
```

---

## 下一步

- 📖 阅读 [用户使用指南](user-guide.md)
- 🔌 学习 [插件开发教程](plugin-development.md)
- ❓ 查看 [常见问题](faq.md)
- 📝 查看 [更新日志](../CHANGELOG.md)

---

**需要帮助？**
- GitHub Issues: [提交问题](https://github.com/yourname/learning-assistant/issues)
- 文档网站: [learning-assistant.readthedocs.io](https://learning-assistant.readthedocs.io)

---

**最后更新**: 2026-03-31
**版本**: v0.1.0 (MVP)