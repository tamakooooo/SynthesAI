# 链接学习模块 - 用户指南

> **版本**: v0.2.0
> **最后更新**: 2026-04-08

## 📋 目录

- [简介](#简介)
- [快速开始](#快速开始)
- [CLI 使用](#cli-使用)
- [Python API 使用](#python-api-使用)
- [功能详解](#功能详解)
- [配置选项](#配置选项)
- [示例](#示例)
- [常见问题](#常见问题)
- [故障排除](#故障排除)

---

## 简介

链接学习模块是 Learning Assistant 的核心功能之一，能够从网页链接中提取知识，生成结构化的知识卡片、问答对和测验题。

**核心功能**:
- ✅ 网页内容抓取和解析
- ✅ 智能知识提取
- ✅ 生成结构化摘要
- ✅ 创建问答对
- ✅ 自动生成测验题
- ✅ 多格式导出（Markdown、JSON）

**支持的网站类型**:
- 新闻网站
- 技术博客
- 学术文章
- 技术文档
- 教程页面

---

## 快速开始

### 前置要求

1. **Python 3.11+**
2. **API Key** - OpenAI / Anthropic / DeepSeek 任意一个
3. **网络连接** - 访问目标网页

### 设置 API Key

```bash
# OpenAI
export OPENAI_API_KEY="sk-your-key-here"

# 或 Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 或 DeepSeek
export DEEPSEEK_API_KEY="sk-your-key-here"
```

### 第一次使用

```bash
# 使用默认配置
la link https://example.com/article

# 输出将保存到 data/outputs/link/ 目录
```

---

## CLI 使用

### 基本命令

```bash
la link <URL> [OPTIONS]
```

### 参数说明

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `--provider` | `-p` | openai | LLM 提供者 (openai/anthropic/deepseek) |
| `--model` | `-m` | gpt-4 | LLM 模型名称 |
| `--output` | `-o` | - | 输出文件路径 |
| `--format` | `-f` | markdown | 输出格式 (markdown/json) |
| `--no-quiz` | - | false | 跳过测验生成 |

### 使用示例

#### 1. 基本用法

```bash
# 使用默认设置
la link https://example.com/article
```

#### 2. 指定 LLM 提供者和模型

```bash
# 使用 Anthropic Claude
la link https://example.com/article \
  --provider anthropic \
  --model claude-3-opus-20240229

# 使用 DeepSeek
la link https://example.com/article \
  --provider deepseek \
  --model deepseek-chat
```

#### 3. 自定义输出

```bash
# 指定输出文件
la link https://example.com/article \
  --output my-article.md

# JSON 格式输出
la link https://example.com/article \
  --format json \
  --output article.json
```

#### 4. 跳过测验生成（加快速度）

```bash
la link https://example.com/article --no-quiz
```

### 输出位置

默认输出目录：`data/outputs/link/`

文件命名格式：`{标题前50字符}_{时间戳}.md`

示例：`Understanding_Machine_Learning_20260408_100500.md`

---

## Python API 使用

### 安装

```bash
pip install learning-assistant
```

### 基本用法

```python
from learning_assistant.api import process_link

# 异步调用
async def main():
    result = await process_link(
        url="https://example.com/article"
    )
    print(result["title"])
    print(result["summary"])

# 同步调用
from learning_assistant.api import process_link_sync

result = process_link_sync(url="https://example.com/article")
print(result["title"])
```

### 完整参数

```python
result = await process_link(
    url="https://example.com/article",
    provider="openai",           # LLM 提供者
    model="gpt-4",               # 模型名称
    output_dir="./my-notes",     # 输出目录
    generate_quiz=True,          # 是否生成测验
)
```

### 返回数据结构

```python
{
    "status": "success",
    "url": "https://example.com/article",
    "title": "文章标题",
    "source": "example.com",
    "summary": "200字左右的摘要...",
    "key_points": [
        "要点1",
        "要点2",
        "要点3"
    ],
    "tags": ["标签1", "标签2", "标签3"],
    "word_count": 3500,
    "reading_time": "14分钟",
    "difficulty": "intermediate",
    "qa_pairs": [
        {
            "question": "问题1?",
            "answer": "答案1",
            "difficulty": "medium"
        }
    ],
    "quiz": [
        {
            "type": "multiple_choice",
            "question": "问题?",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "correct": "A",
            "explanation": "解释..."
        }
    ],
    "files": {
        "markdown_path": "./outputs/article.md"
    },
    "timestamp": "2026-04-08T10:00:00"
}
```

### 高级用法

#### 1. 批量处理多个链接

```python
import asyncio
from learning_assistant.api import process_link

urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3",
]

async def process_batch():
    tasks = [process_link(url, generate_quiz=False) for url in urls]
    results = await asyncio.gather(*tasks)

    for result in results:
        print(f"{result['title']}: {result['word_count']} words")

asyncio.run(process_batch())
```

#### 2. 使用不同 LLM 提供者

```python
# OpenAI GPT-4
result = await process_link(
    url="https://example.com/article",
    provider="openai",
    model="gpt-4-turbo-preview"
)

# Anthropic Claude
result = await process_link(
    url="https://example.com/article",
    provider="anthropic",
    model="claude-3-opus-20240229"
)

# DeepSeek
result = await process_link(
    url="https://example.com/article",
    provider="deepseek",
    model="deepseek-chat"
)
```

#### 3. 自定义输出目录

```python
result = await process_link(
    url="https://example.com/article",
    output_dir="./my-knowledge-base"
)

print(f"保存到: {result['files']['markdown_path']}")
```

---

## 功能详解

### 1. 内容抓取

**支持的协议**:
- HTTP/HTTPS

**特性**:
- 自动重试（最多3次）
- 超时处理（默认30秒）
- 自动处理重定向
- 支持 Gzip 压缩

**限制**:
- 不支持需要登录的页面
- 不支持 JavaScript 动态加载的内容（除非启用 Playwright）

### 2. 内容解析

**解析引擎**: trafilatura

**提取内容**:
- 标题（title、og:title、h1）
- 正文内容
- 作者（可选）
- 发布日期（可选）

**过滤内容**:
- 导航栏
- 广告
- 侧边栏
- 评论区（可配置）

### 3. 知识提取

**LLM 分析**:
- 生成 200 字摘要
- 提取 3-5 个核心要点
- 生成 3-5 个标签
- 评估内容难度

**问答对生成**:
- 3-5 个问题
- 详细答案
- 难度分级

**测验题生成**:
- 多选题（4个选项）
- 正确答案
- 答案解释

### 4. 导出格式

#### Markdown 格式

```markdown
# 文章标题

**来源**: example.com
**URL**: https://example.com/article
**字数**: 3500
**阅读时间**: 14分钟
**难度**: intermediate

## 摘要

这是文章的摘要内容...

## 核心要点

1. 要点1
2. 要点2
3. 要点3

## 标签

#标签1 #标签2 #标签3

## 问答

### Q1: 问题?

**答案**: 答案内容

**难度**: medium

## 测验

### 问题?

A. 选项1
B. 选项2
C. 选项3
D. 选项4

**正确答案**: A

**解释**: 解释内容...
```

#### JSON 格式

完整的 JSON 结构，便于程序化处理。

---

## 配置选项

配置文件位置：`config/modules.yaml`

```yaml
link_learning:
  enabled: true
  priority: 2

  config:
    # 内容抓取配置
    fetcher:
      timeout: 30              # 超时时间（秒）
      max_retries: 3           # 最大重试次数
      retry_delay: 2           # 重试延迟（秒）
      use_playwright: false    # 是否启用 Playwright（动态页面）
      user_agent: null         # 自定义 User-Agent
      proxy: null              # 代理服务器

    # 内容解析配置
    parser:
      engine: "trafilatura"    # 解析引擎
      include_comments: false  # 是否包含评论
      include_tables: true     # 是否包含表格
      favor_precision: true    # 偏好精确提取
      min_content_length: 200  # 最小内容长度（字）

    # LLM 配置
    llm:
      provider: "openai"       # LLM 提供者
      model: "gpt-4"           # 模型名称
      temperature: 0.3         # 温度参数
      max_tokens: 2000         # 最大 token 数

    # 功能开关
    features:
      generate_qa: true        # 生成问答对
      generate_quiz: true      # 生成测验题
      extract_tags: true       # 提取标签
      estimate_difficulty: true # 评估难度

    # 输出配置
    output:
      format:
        - "markdown"           # 输出格式
        - "json"
      directory: "data/outputs/link"  # 输出目录
      save_history: true       # 保存历史记录
```

### 配置示例

#### 1. 启用动态页面支持

```yaml
link_learning:
  config:
    fetcher:
      use_playwright: true
```

**安装 Playwright**:
```bash
pip install playwright
playwright install
```

#### 2. 使用代理

```yaml
link_learning:
  config:
    fetcher:
      proxy: "http://proxy.example.com:8080"
```

#### 3. 调整内容提取精度

```yaml
link_learning:
  config:
    parser:
      favor_precision: true     # 更精确（可能遗漏部分内容）
      # favor_precision: false  # 更全面（可能包含噪音）
```

---

## 示例

### 示例 1: 技术博客总结

```bash
la link https://blog.python.org/2024/01/new-features.html
```

输出示例：
- **标题**: Python 3.13 New Features
- **要点**: 5个关键新特性
- **问答**: 3个问题详解
- **测验**: 5道多选题

### 示例 2: 新闻文章分析

```bash
la link https://news.example.com/tech/ai-breakthrough \
  --provider anthropic \
  --model claude-3-opus-20240229
```

### 示例 3: 批量处理技术文档

```python
import asyncio
from learning_assistant.api import process_link

docs = [
    "https://docs.python.org/3/tutorial/index.html",
    "https://docs.python.org/3/library/stdtypes.html",
    "https://docs.python.org/3/library/functions.html",
]

async def process_docs():
    results = []
    for url in docs:
        result = await process_link(url, generate_quiz=False)
        results.append(result)
        print(f"[OK] {result['title']}")

    return results

results = asyncio.run(process_docs())
print(f"处理了 {len(results)} 篇文档")
```

---

## 常见问题

### Q1: 支持 JavaScript 动态加载的内容吗？

**A**: 默认不支持。需要启用 Playwright:

```bash
pip install playwright
playwright install
```

然后在配置中启用：
```yaml
fetcher:
  use_playwright: true
```

### Q2: 内容抓取失败怎么办？

**可能原因**:
1. 网络连接问题
2. 网站限制访问
3. 需要登录
4. 动态加载内容

**解决方案**:
1. 检查网络连接
2. 尝试使用代理
3. 使用 Playwright 模式
4. 手动复制内容到文本文件

### Q3: LLM 生成的质量不高怎么办？

**解决方案**:
1. 使用更强大的模型（GPT-4、Claude 3 Opus）
2. 调整 temperature 参数
3. 增加 max_tokens
4. 分段处理长文章

### Q4: 支持哪些语言？

**A**:
- 中文（优化）
- 英文（优化）
- 其他语言（基本支持）

### Q5: 生成的文件保存在哪里？

**A**: 默认保存在 `data/outputs/link/` 目录，可通过配置修改。

### Q6: 如何查看历史记录？

**A**: 使用 CLI 命令：
```bash
la history --module link_learning
```

---

## 故障排除

### 错误: "API key not found"

**解决方案**:
```bash
export OPENAI_API_KEY="sk-your-key"
```

### 错误: "Failed to fetch URL"

**可能原因**:
1. URL 无效
2. 网络问题
3. 网站限制

**调试步骤**:
```bash
# 测试 URL 是否可访问
curl -I https://example.com/article

# 检查网络
ping example.com
```

### 错误: "Content parsing failed"

**可能原因**:
1. 内容太短（少于 200 字）
2. 内容格式不支持

**解决方案**:
```yaml
parser:
  min_content_length: 100  # 降低最小长度限制
```

### 错误: "LLM API error"

**可能原因**:
1. API Key 无效
2. 账户余额不足
3. 模型不存在

**调试步骤**:
```bash
# 测试 API Key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 性能问题

**症状**: 处理速度慢

**优化建议**:
1. 使用更快的模型（GPT-3.5-turbo）
2. 禁用测验生成（`--no-quiz`）
3. 减少重试次数
4. 启用缓存

---

## 相关链接

- [CLI 完整文档](link_learning_cli_guide.md)
- [API 参考](api.md)
- [架构设计](link_learning_design.md)
- [集成测试](../tests/modules/link_learning/)

---

**版本**: v0.2.0
**最后更新**: 2026-04-08
**维护者**: Learning Assistant Team