# Link Learning Module - CLI 使用指南

> **版本**: v0.2.0
> **更新日期**: 2026-03-31
> **状态**: ✅ CLI 命令已完成

---

## 📋 概述

`la link` 命令用于从网页链接提取知识，生成结构化的知识卡片，包含摘要、要点、问答和测验。

---

## 🚀 快速开始

### 基本用法

```bash
la link <url>
```

### 示例

```bash
# 从网页生成知识卡片
la link https://example.com/article

# 使用特定 LLM 提供者
la link https://example.com/article --provider openai --model gpt-4

# 保存到文件
la link https://example.com/article --output article.md

# 使用 JSON 格式保存
la link https://example.com/article --output article.json --format json

# 跳过测验生成（更快）
la link https://example.com/article --no-quiz
```

---

## 📝 命令参数

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `url` | str | 要处理的网页 URL | `https://example.com/article` |

### 可选参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--provider` | `-p` | str | `openai` | LLM 提供者（openai/anthropic/deepseek） |
| `--model` | `-m` | str | `gpt-4` | LLM 模型 |
| `--output` | `-o` | str | None | 输出文件路径 |
| `--format` | `-f` | str | `markdown` | 输出格式（markdown/json） |
| `--no-quiz` | | bool | `False` | 跳过测验生成 |

---

## 📊 输出内容

### 控制台输出

```
Processing web link: https://example.com/article
Initializing...
Fetching and analyzing content...

✓ Knowledge card generated successfully!

┌─────────────── Knowledge Card ───────────────┐
│ Field          │ Value                        │
├────────────────┼──────────────────────────────┤
│ Title          │ Understanding Machine Learning│
│ Source         │ example.com                   │
│ URL            │ https://example.com/article   │
│ Word Count     │ 3500                          │
│ Reading Time   │ 14分钟                        │
│ Difficulty     │ intermediate                  │
│ Tags           │ AI, Machine Learning, Tutorial│
└────────────────┴──────────────────────────────┘

Summary:
机器学习是人工智能的核心技术，本文介绍了机器学习的基本概念...

Key Points:
  1. 机器学习的定义和应用场景
  2. 监督学习和无监督学习的区别
  3. 常见算法及其选择标准

Q&A Pairs:
  Q1: 什么是机器学习？
  A1: 机器学习是让计算机从数据中学习模式的技术...

Quiz:
  Q1: 以下哪个是监督学习的典型应用？
    A. 图像分类
    B. 聚类分析
    C. 异常检测
    D. 降维
  Answer: A

Processed at: 2026-03-31 14:30:00
```

---

### Markdown 输出格式

```markdown
# Understanding Machine Learning

**Source**: example.com
**URL**: https://example.com/article
**Word Count**: 3500
**Reading Time**: 14分钟
**Difficulty**: intermediate
**Created**: 2026-03-31 14:30:00

## Summary

机器学习是人工智能的核心技术，本文介绍了机器学习的基本概念...

## Key Points

1. 机器学习的定义和应用场景
2. 监督学习和无监督学习的区别
3. 常见算法及其选择标准

## Tags

AI, Machine Learning, Tutorial

## Q&A

### Q1: 什么是机器学习？

**A1**: 机器学习是让计算机从数据中学习模式的技术...

### Q2: 监督学习和无监督学习的区别是什么？

**A2**: 监督学习使用标签数据，无监督学习不需要标签...

## Quiz

### Q1: 以下哪个是监督学习的典型应用？

- A. 图像分类
- B. 聚类分析
- C. 异常检测
- D. 降维

**Answer**: A
```

---

### JSON 输出格式

```json
{
  "title": "Understanding Machine Learning",
  "url": "https://example.com/article",
  "source": "example.com",
  "summary": "机器学习是人工智能的核心技术...",
  "key_points": [
    "机器学习的定义和应用场景",
    "监督学习和无监督学习的区别",
    "常见算法及其选择标准"
  ],
  "tags": ["AI", "Machine Learning", "Tutorial"],
  "word_count": 3500,
  "reading_time": "14分钟",
  "difficulty": "intermediate",
  "created_at": "2026-03-31T14:30:00",
  "qa_pairs": [
    {
      "question": "什么是机器学习？",
      "answer": "机器学习是让计算机从数据中学习模式的技术...",
      "difficulty": "medium"
    }
  ],
  "quiz": [
    {
      "type": "multiple_choice",
      "question": "以下哪个是监督学习的典型应用？",
      "options": ["图像分类", "聚类分析", "异常检测", "降维"],
      "correct": "A",
      "explanation": null
    }
  ]
}
```

---

## ⚙️ 配置

### 配置文件位置

`config/modules.yaml`

### 配置示例

```yaml
link_learning:
  enabled: true
  priority: 2

  config:
    fetcher:
      timeout: 30
      max_retries: 3
      retry_delay: 2
      use_playwright: false

    parser:
      engine: "trafilatura"
      include_comments: false
      include_tables: true
      favor_precision: true
      min_content_length: 200

    llm:
      provider: "openai"
      model: "gpt-4"
      temperature: 0.3
      max_tokens: 2000

    output:
      format: ["markdown", "json"]
      directory: "data/outputs/link"
      save_history: true

    features:
      generate_qa: true
      generate_quiz: true
      extract_tags: true
      estimate_difficulty: true
```

---

## 🛠️ 高级用法

### 1. 使用不同的 LLM 提供者

```bash
# 使用 Anthropic Claude
la link https://example.com/article --provider anthropic --model claude-3-opus-20240229

# 使用 DeepSeek
la link https://example.com/article --provider deepseek --model deepseek-chat
```

### 2. 批量处理

```bash
# 从文件读取多个 URL
cat urls.txt | xargs -I {} la link {}

# 使用 Shell 脚本
for url in $(cat urls.txt); do
  la link "$url" --output "output/$(echo $url | md5sum | cut -d' ' -f1).md"
done
```

### 3. 自定义输出

```bash
# 仅生成摘要和要点（跳过问答和测验）
la link https://example.com/article --no-quiz

# JSON 格式输出（便于程序处理）
la link https://example.com/article --output result.json --format json
```

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 网页抓取时间 | <5s |
| 内容解析时间 | <1s |
| LLM 处理时间 | <30s |
| 总处理时间 | <40s |
| 内存占用 | <150MB |

---

## 🔍 故障排查

### 常见错误

#### 1. 网页抓取失败

```
Error: Failed to fetch URL
```

**解决方案**:
- 检查 URL 是否正确
- 检查网络连接
- 尝试使用代理：修改 `config/modules.yaml` 中的 `fetcher.proxy`

#### 2. 内容解析失败

```
Error: Content too short: 50 words (min: 200)
```

**解决方案**:
- 网页内容太少
- 降低 `parser.min_content_length` 配置值

#### 3. LLM API 错误

```
Error: Invalid API key
```

**解决方案**:
- 运行 `la setup` 检查 API Key
- 设置环境变量：`export OPENAI_API_KEY=your-key`

---

## 📚 相关命令

```bash
# 查看帮助
la link --help

# 查看已安装插件
la list-plugins

# 查看历史记录
la history

# 查看版本
la version
```

---

## 🎯 最佳实践

### 1. 选择合适的 URL

- ✅ 新闻文章、博客、技术文档
- ✅ 学术论文、教程
- ❌ 首页、导航页
- ❌ 登录页面、付费墙内容

### 2. 优化性能

- 使用 `--no-quiz` 跳过测验生成（快 30%）
- 使用较小的 LLM 模型（如 `gpt-3.5-turbo`）
- 批量处理时使用后台模式

### 3. 输出管理

- 使用 `--output` 保存结果
- 使用 JSON 格式便于程序处理
- 定期清理 `data/outputs/link/` 目录

---

## 🚧 限制

### 当前限制

1. **不支持动态页面**（默认）- 如需支持，安装 Playwright
2. **不支持付费墙内容** - 需要登录的内容无法访问
3. **最小内容长度** - 默认 200 字，低于此长度会报错
4. **语言支持** - 主要支持中英文，其他语言效果可能不佳

### 解决方案

- **动态页面**: 安装 Playwright 并启用
  ```bash
  pip install playwright
  playwright install
  ```
  然后修改配置 `fetcher.use_playwright: true`

---

## 📞 反馈

如有问题或建议，请提交 Issue:
- GitHub: https://github.com/yourname/learning-assistant/issues

---

**最后更新**: 2026-03-31
**版本**: v0.2.0
**作者**: Learning Assistant Team