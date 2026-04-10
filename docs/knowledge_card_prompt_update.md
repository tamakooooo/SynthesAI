# 知识卡片系统 - Agent 开发指南

> 本文档帮助 AI Agent 理解和使用编辑风格知识卡片系统

## 系统概览

**编辑风格知识卡片系统**是 Learning Assistant 的可视化输出模块，用于将文本内容转化为专业的编辑风格信息图。

**核心组件**：
- `VisualCardGenerator` - 卡片生成器
- `link_summary.yaml` v2.0 - 提示词模板（Agent 必须遵循）
- HTML + PNG 双格式输出

**Agent 参与点**：
- ✅ 使用 VisualCardGenerator 生成卡片
- ✅ 设计新的卡片样式（专属模块）
- ✅ 优化提示词模板提升质量
- ✅ 扩展到其他模块

---

## 核心要点格式（关键！）

Agent 在调用 VisualCardGenerator 时，必须确保核心要点遵循以下格式：

### 格式规范

```json
{
  "key_points": [
    "关键词：详细描述",
    "关键词2：详细描述2"
  ]
}
```

### 格式要求

| 部分 | 要求 | 示例 |
|------|------|------|
| **关键词** | 3-8字，简洁明确 | "专为 NAS 用户" |
| **分隔符** | 中文冒号"："或英文冒号":" | "：" |
| **详细描述** | 15-30字，具体说明 | "针对网络附属存储场景优化，满足私人影音库需求" |

### 正则验证

Prompt Template 使用以下正则表达式验证格式：
```yaml
pattern: "^.{3,8}[：:].{15,30}$"
```

### Agent 常见错误

❌ **错误示例**：
```json
{
  "key_points": [
    "这是一个很长的要点描述没有关键词分离",
    "关键词太长超过八个字导致布局混乱：描述",
    "描述太短少于十五字信息不足：简短描述"
  ]
}
```

✅ **正确示例**：
```json
{
  "key_points": [
    "单文件输出：纯 HTML 自包含，零构建依赖，开箱即用",
    "双语设计：中文正文搭配英文展示标题，国际化视觉呈现",
    "一键导出：内置多分辨率 PNG/JPEG 导出，适配社交分享"
  ]
}
```

---

## Prompt Template v2.0 设计

### Agent 必须遵循的模板结构

**位置**：`templates/prompts/link_summary.yaml`

**关键部分**：

```yaml
template: |
  你是一位专业的内容总结助手。请分析以下网页内容，生成适合编辑风格知识卡片的内容。

  ## 任务要求

  1. **核心要点**：提取4-6个最重要的要点，**每个要点采用"关键词：详细描述"的格式**
     - 关关键词：简洁明确（3-8个字），适合作为卡片标题
     - 详细描述：具体内容说明（15-30个字），适合作为卡片内容

  ## 输出格式（JSON）
  ```json
  {
    "key_points": [
      "关键词：详细描述",
      "关键词2：详细描述2"
    ]
  }
  ```

json_schema:
  key_points:
    type: array
    items:
      type: string
      pattern: "^.{3,8}[：:].{15,30}$"
    minItems: 4
    maxItems: 6
```

### Agent 创建新 Prompt Template 时

如果 Agent 为其他模块创建知识卡片，必须遵循相同的设计：

1. ✅ 明确格式要求（"关键词：详细描述"）
2. ✅ 提供示例和反例
3. ✅ 添加正则验证
4. ✅ 限制数量（4-6个）
5. ✅ 解释用途（"适合卡片标题"、"适合卡片内容"）

---

## VisualCardGenerator 使用指南

### Agent 基础用法

```python
from learning_assistant.core.exporters.visual_card import VisualCardGenerator

# 初始化
generator = VisualCardGenerator(width=1200)

# 生成 HTML
html_content = generator.generate_card_html(
    title="文章标题",
    summary="300-500字的摘要",
    key_points=[
        "关键词：详细描述",
        "要点2：描述2",
    ],
    key_concepts=[
        {"term": "概念名", "definition": "50-150字解释"},
    ],
    tags=["标签1", "标签2"],
)

# 保存 HTML
Path("output.html").write_text(html_content, encoding="utf-8")

# 渲染为 PNG（需要 Playwright）
await generator.render_html_to_image(
    html_content=html_content,
    output_path=Path("output.png"),
    width=1200,
    scale=2.0,  # 2x 高分辨率
)
```

### Agent 参数规范

| 参数 | 类型 | 要求 | 示例 |
|------|------|------|------|
| `title` | string | 简洁标题 | "bili-sync：Rust + Tokio 驱动的 B站视频同步工具" |
| `summary` | string | 300-500字摘要 | 一段完整文字 |
| `key_points` | list[string] | 4-6个，格式"关键词：描述" | ["单文件输出：纯 HTML 自包含..."] |
| `key_concepts` | list[dict] | 2-3个，每个50-150字 | [{"term": "Tokio", "definition": "Rust异步运行时..."}] |
| `tags` | list[string] | 3-5个标签 | ["Rust", "哔哩哔哩", "NAS"] |

---

## 卡片布局映射（Agent 必读）

Agent 需要理解数据如何映射到卡片布局：

```
┌─────────────────────────────────────────────┐
│  顶部栏                                      │
│  KNOWLEDGE CARD · LINK SUMMARY  |  GitHub   │  ← source
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  标题                                        │  ← title
│  bili-sync：Rust + Tokio 驱动的...          │
└─────────────────────────────────────────────┘
┌──────┬──────┬──────┬──────┬──────┬──────┐
│  卡片1 │  卡片2 │  卡片3 │  卡片4 │  卡片5 │  卡片6 │  ← key_points[:6]
│  关键词│  关键词│  关键词│  关键词│  关键词│  关键词│     (关键词作标题)
│  描述  │  描述  │  描述  │  描述  │  描述  │  描述  │     (描述作内容)
└──────┴──────┴──────┴──────┴──────┴──────┘
┌─────────────────────┬─────────────────────┐
│  深色面板（左）       │  浅色面板（右）       │
│  内容摘要            │  核心洞察             │
│  summary 字段        │  key_points[:3]      │
│                     │                     │
│  关键概念            │  ① 关键词            │
│  key_concepts       │     描述             │
│  - 概念名：定义       │  ② 关键词            │
│  - 概念名：定义       │     描述             │
│                     │  ③ 关键词            │
│                     │     描述             │
└─────────────────────┴─────────────────────┘
┌─────────────────────────────────────────────┐
│  底部高亮条                                  │
│  关键词 · #Rust · #哔哩哔哩 · #NAS           │  ← tags
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  页脚                                        │
│  https://github.com/...  |  Learning Assist │  ← url
└─────────────────────────────────────────────┘
```

### Agent 理解要点

1. **框架网格卡片**：key_points 前 6 个，关键词作为卡片标题
2. **深色面板**：summary + key_concepts（概念定义）
3. **浅色面板**：key_points 前 3 个，带编号展示（核心洞察）
4. **底部高亮条**：tags，带 # 符号

---

## Agent 开发工作流

### 场景 1：为链接总结生成卡片

```python
# Agent 自动化流程

# 1. 抓取内容
html = await content_fetcher.fetch(url)
content = content_parser.parse(html)

# 2. LLM 处理（遵循 v2.0 模板）
template = prompt_manager.load_template("link_summary")
prompt = template.render(content)
response = llm_service.call(prompt)

# 3. 解析结果（自动验证格式）
card_data = parse_llm_response(response)  # key_points 已验证格式

# 4. 生成卡片
generator = VisualCardGenerator(width=1200)
html = generator.generate_card_html(**card_data)

# 5. 渲染 PNG
await generator.render_html_to_image(
    html_content=html,
    output_path=Path("output.png"),
)

# 完成！
```

### 场景 2：为其他模块生成卡片

```python
# Agent 创建视频总结卡片

# 1. 准备数据（遵循相同格式）
video_data = {
    "title": "视频标题",
    "summary": "视频内容摘要（300-500字）",
    "key_points": [
        "核心概念：解释说明",
        "技术要点：详细描述",
        "实战应用：具体内容",
        "优化技巧：实践建议",
    ],
    "key_concepts": [
        {"term": "概念", "definition": "详细定义"},
    ],
    "tags": ["视频", "教程", "技术"],
    "source": "bilibili",
    "url": "https://bilibili.com/video/BV...",
}

# 2. 生成卡片
generator = VisualCardGenerator(width=1200)
html = generator.generate_card_html(**video_data)

# 3. 渲染 PNG
await generator.render_html_to_image(html, output_path)
```

### 场景 3：优化提示词模板

```yaml
# Agent 优化 link_summary.yaml

# 1. 添加更多示例
template: |
  ## 核心要点格式要求

  **正确示例**：
  - "单文件输出：纯 HTML 自包含，零构建依赖，开箱即用"
  - "双语设计：中文正文搭配英文展示标题，国际化视觉呈现"

  **错误示例**：
  - ❌ "这是一个很长的要点描述没有关键词分离"
  - ❌ "关键词太长超过八个字导致布局混乱：描述"

  **关键**：关键词3-8字，描述15-30字，用冒号分隔

# 2. 加强验证
json_schema:
  key_points:
    items:
      pattern: "^.{3,8}[：:].{15,30}$"
      # Agent 可以添加更多验证规则
```

---

## Agent 注意事项

### ⚠️ 格式一致性

- ✅ 所有 key_points 必须遵循"关键词：描述"
- ✅ 不能混用不同格式
- ✅ 使用正则验证确保格式

### ⚠️ 内容长度限制

| 字段 | 最小 | 最大 | Agent 必须遵守 |
|------|------|------|---------------|
| summary | 300字 | 500字 | ⚠️ 太短信息不足，太长布局混乱 |
| key_points 关键词 | 3字 | 8字 | ⚠️ 关键词太短不明确，太长标题溢出 |
| key_points 描述 | 15字 | 30字 | ⚠️ 描述太短不具体，太长卡片溢出 |
| key_concepts 定义 | 50字 | 150字 | ⚠️ 定义太短不完整，太长布局混乱 |
| tags | 3个 | 5个 | ⚠️ 太少分类不足，太多底部拥挤 |

### ⚠️ 异步渲染

```python
# ❌ 错误：不能在 async 函数中调用 asyncio.run()
async def export():
    asyncio.run(generator.render_html_to_image(...))  # 错误！

# ✅ 正确：直接 await
async def export():
    await generator.render_html_to_image(...)  # 正确
```

### ⚠️ Playwright 安装

如果 Agent 需要渲染 PNG，必须先安装：
```bash
pip install playwright
playwright install chromium
```

如果未安装，系统会自动 fallback 到 HTML 输出。

---

## Agent 扩展建议

### 1. 为其他模块设计专属卡片

Agent 可以为不同模块创建不同的卡片样式：

- **视频模块**：添加视频缩略图、时长、章节
- **词汇模块**：添加发音、词源、例句
- **课程模块**：添加课程大纲、学习路径

**创建专属生成器**：
```python
# src/learning_assistant/core/exporters/video_card.py

class VideoCardGenerator(VisualCardGenerator):
    """视频专属卡片生成器"""

    def generate_video_card(
        self,
        title: str,
        duration: str,
        thumbnail_path: Path,
        chapters: list[dict],
        ...
    ):
        # 扩展基础功能
        html = self._generate_video_html(...)
        return html
```

### 2. 添加新配色方案

Agent 可以设计新的配色方案：

```python
# Claude 风格（默认）
COLORS = {
    "primary": "#FF6B35",     # Orange
    "accent": "#764BA2",      # Purple
}

# Agent 新配色（如科技蓝）
COLORS = {
    "primary": "#1E88E5",     # Tech Blue
    "accent": "#00ACC1",      # Cyan
}
```

### 3. 支持多语言

Agent 可以创建多语言模板：
```python
# 英文版
generator.generate_card_html(
    title="Title in English",
    summary="Summary in English...",
    key_points=[
        "Keyword: Description",
        "Key Point 2: Description 2",
    ],
    language="en",  # 新参数
)
```

---

## Agent 测试验证

### 测试 Prompt 格式

```python
# Agent 测试正则验证
import re

pattern = r"^.{3,8}[：:].{15,30}$"

# 测试数据
test_points = [
    "单文件输出：纯 HTML 自包含，零构建依赖，开箱即用",  # ✅ 正确
    "这是一个很长的要点描述没有关键词分离",              # ❌ 错误
]

for point in test_points:
    if re.match(pattern, point):
        print(f"✅ {point}")
    else:
        print(f"❌ {point}")
```

### 测试卡片生成

```python
# Agent 测试完整流程
def test_card_generation():
    generator = VisualCardGenerator(width=1200)

    html = generator.generate_card_html(
        title="Test Title",
        summary="This is a test summary with 300-500 characters...",
        key_points=[
            "Keyword1: Description with 15-30 chars",
            "Keyword2: Another description here",
        ],
        tags=["test", "demo"],
    )

    assert len(html) > 0
    assert "Keyword1" in html
    print("✅ Test passed")
```

---

## Agent 调试技巧

### 1. 查看 HTML 输出

```python
# Agent 保存 HTML 查看布局
Path("test.html").write_text(html)
# 在浏览器中打开 test.html 查看效果
```

### 2. 检查格式解析

```python
# Agent 检查要点解析是否正确
generator._build_framework_cards(key_points)
# 查看生成的卡片 HTML
```

### 3. 测试 PNG 渲染

```python
# Agent 测试 PNG 渲染
await generator.render_html_to_image(
    html_content=test_html,
    output_path=Path("test.png"),
    width=1200,
    scale=2.0,
)
# 检查 PNG 文件大小和尺寸
```

---

## Agent 文件清单

**核心组件**：
- `src/learning_assistant/core/exporters/visual_card.py` - VisualCardGenerator
- `templates/prompts/link_summary.yaml` - 提示词模板 v2.0
- `templates/outputs/link_summary.md` - Markdown 输出模板

**配置文件**：
- `config/modules.yaml` - link_learning 配置
- `config/settings.yaml` - Playwright 依赖配置

**测试文件**：
- `data/outputs/link/*.html` - 生成的 HTML 卡片
- `data/outputs/link/*.png` - 生成的 PNG 图片
- `docs/knowledge_card_prompt_update.md` - 本文档

---

## Agent 成功案例

### 案例 1：链接总结生成

```bash
# Agent 运行命令
la link https://github.com/beilunyang/visual-note-card-skills

# Agent 生成的输出
✅ Markdown: GitHub - beilunyang_...md
✅ HTML卡片: GitHub - beilunyang_...html
✅ PNG图片: GitHub - beilunyang_...png (658KB, 2400px宽度)
```

### 案例 2：格式验证

```json
// Agent 生成的 JSON（符合格式）
{
  "key_points": [
    "单文件输出：纯 HTML 自包含，零构建依赖，开箱即用",
    "双语设计：中文正文搭配英文展示标题，国际化视觉呈现",
    "一键导出：内置多分辨率 PNG/JPEG 导出，适配社交分享",
    "固定版式：编辑风格网格系统，暗/亮面板对比，信息层级清晰",
    "框架结构：M×P×D×G 四卡框架行，结构化提炼核心概念",
    "配色可定制：默认青橙主题，支持用户指定配色方案保持对比度"
  ]
}
```

✅ 所有要点符合格式：关键词（3-8字） + 冒号 + 描述（15-30字）

---

## Agent 下一步工作

### 可探索方向

1. ✅ 为视频模块创建视频卡片样式
2. ✅ 为词汇模块创建词汇卡片样式
3. ✅ 设计新的配色方案（主题化）
4. ✅ 支持多语言（英文、日文等）
5. ✅ 添加交互元素（折叠、点击展开）
6. ✅ 支持动态数据（实时更新）

---

**Agent 开发知识卡片系统愉快！遵循格式规范，生成高质量卡片。**