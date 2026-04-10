# Learning Assistant - 示例代码

> **实用的 Python 示例代码** - 快速上手 Learning Assistant API

**版本**: v0.2.0 | **更新日期**: 2026-04-10

---

## 📋 目录

- [快速开始](#快速开始)
- [示例脚本](#示例脚本)
- [使用方法](#使用方法)
- [常见问题](#常见问题)

---

## 快速开始

### 前置要求

1. **已安装 Learning Assistant**:
   ```bash
   pip install -e ".[dev]"
   ```

2. **已配置 API Key**:
   ```bash
   export OPENAI_API_KEY="your-key"
   ```

3. **已安装 FFmpeg** (视频处理):
   ```bash
   ffmpeg -version
   ```

### 运行第一个示例

```bash
# 运行基础示例
python examples/basic_usage.py
```

---

## 示例脚本

### 1. [basic_usage.py](basic_usage.py) - 基础使用示例

**适合**: 新手入门，快速了解 API 功能

**包含示例**:
- 基础视频总结
- 自定义选项（格式、语言、目录）
- 链接学习
- 单词提取
- 单词学习 + 上下文故事
- 列出可用技能
- 查看学习历史

**运行**:
```bash
python examples/basic_usage.py
```

**预计耗时**: 5-10 分钟

---

### 2. [batch_processing.py](batch_processing.py) - 批量处理示例

**适合**: 需要处理大量视频或文章的用户

**包含示例**:
- 串行处理 (不推荐)
- 并行处理 (推荐)
- 批量处理 + 错误处理
- 混合批量处理 (视频 + 文章)
- 限制并发数
- 进度跟踪
- 输出文件收集

**运行**:
```bash
python examples/batch_processing.py
```

**预计耗时**: 10-20 分钟

**性能对比**:
- 串行处理 5 个视频: ~15-20 分钟
- 并行处理 5 个视频: ~5-7 分钟 (节省 60-70% 时间)

---

### 3. [learning_workflow.py](learning_workflow.py) - 学习工作流示例

**适合**: 想要创建完整学习流程的用户

**包含示例**:
- 视频 → 单词提取
- 文章 → 单词提取
- 完整学习会话 (视频 + 多文章 + 单词)
- 创建学习笔记 (Markdown)
- 每日学习例行程序

**运行**:
```bash
python examples/learning_workflow.py
```

**预计耗时**: 15-30 分钟

**输出示例**:
```markdown
# 学习笔记 - 2026年04月10日

## 🎬 视频总结
...

## 📚 扩展阅读
...

## 📝 单词学习
...
```

---

## 使用方法

### 1. 直接运行

所有示例脚本都可以直接运行:

```bash
python examples/basic_usage.py
python examples/batch_processing.py
python examples/learning_workflow.py
```

### 2. 导入并使用

可以在自己的代码中导入示例函数:

```python
import asyncio
from examples.basic_usage import example_1_basic_video_summary

# 运行单个示例
result = asyncio.run(example_1_basic_video_summary())
```

### 3. 修改并自定义

复制示例代码到自己的项目中，根据需求修改:

```python
# 复制示例函数
async def my_custom_workflow():
    # 修改为实际 URL
    video_url = "https://www.bilibili.com/video/BV..."

    # 调整参数
    result = await summarize_video(
        url=video_url,
        format="pdf",
        language="en"
    )

    return result
```

---

## 示例输出

### 基础示例输出

```
============================================================
示例 1: 基础视频总结
============================================================

处理视频: https://www.bilibili.com/video/BV1G49MBLE4D

✅ 视频标题: Python 编程基础教程
✅ 平台: bilibili
✅ 时长: 600 秒
✅ 总结文件: data/outputs/python_tutorial_summary.md
✅ 字幕文件: data/outputs/python_tutorial_subtitle.srt

总结内容预览:
本视频介绍了 Python 编程的基础知识，包括变量、数据类型、控制流...
```

### 批量处理输出

```
============================================================
示例 2: 并行处理 (推荐)
============================================================

处理 3 个视频 (并行):

统计:
  成功: 3/3
  失败: 0/3
  总耗时: 120.5 秒
  平均耗时: 40.2 秒/视频
  性能提升: 4.0x

1. ✅ 成功: Python 编程基础
2. ✅ 成功: 机器学习入门
3. ✅ 成功: 深度学习实践
```

### 学习笔记输出

```markdown
# 学习笔记 - 2026年04月10日

## 🎬 视频总结

**标题**: Python 编程基础教程
**平台**: bilibili
**时长**: 600 秒

### 内容摘要

本视频介绍了 Python 编程的基础知识...

## 📚 扩展阅读

### 文章 1: Python 最佳实践

**来源**: example.com
**阅读时间**: 5 分钟
**难度**: intermediate

**摘要**: ...

## 📝 单词学习

### 1. algorithm

**音标**: /ˈælɡərɪðəm/
**释义**: 算法

**例句**:
- This algorithm is very efficient.
```

---

## 常见问题

### 1. 示例运行失败

**可能原因**:
- API Key 未配置
- 网络连接问题
- URL 无效或视频不存在

**解决方案**:
```bash
# 检查 API Key
echo $OPENAI_API_KEY

# 配置 API Key
export OPENAI_API_KEY="your-key"

# 或在 config/settings.local.yaml 中配置
```

### 2. 批量处理太慢

**解决方案**:
- 使用并行处理 (`asyncio.gather`)
- 调整并发数 (避免过载)
- 降低视频质量 (`quality: "medium"`)

**示例**:
```python
# 调整并发数
await example_5_limited_concurrency(urls, max_concurrent=5)
```

### 3. 内存不足

**解决方案**:
- 减少并发数
- 使用批量处理 + 清理缓存
- 限制视频时长

**示例**:
```python
# 限制并发数
max_concurrent = 2  # 降低到 2

# 清理缓存
import shutil
shutil.rmtree("data/cache")
```

### 4. API 成本过高

**解决方案**:
- 使用经济模型 (`gpt-3.5-turbo`)
- 减少输出 Token (`max_tokens: 1500`)
- 批量处理，减少重复调用

**配置**:
```yaml
llm:
  providers:
    openai:
      default_model: "gpt-3.5-turbo"  # 经济实惠

modules:
  video_summary:
    config:
      summary:
        max_tokens: 1500  # 减少输出
```

---

## 进阶用法

### 自定义示例脚本

创建自己的示例脚本:

```python
# my_example.py
import asyncio
from learning_assistant.api import summarize_video

async def my_workflow():
    """我的自定义工作流"""

    # 1. 处理视频
    result = await summarize_video(url="...")

    # 2. 自定义处理
    # ...

    return result

if __name__ == "__main__":
    asyncio.run(my_workflow())
```

### 集成到现有项目

```python
# your_project.py
from learning_assistant.api import AgentAPI

api = AgentAPI()

# 在项目中使用
result = await api.summarize_video(url="...")
```

---

## 相关文档

- **API 文档**: [docs/API_EXAMPLES.md](../docs/API_EXAMPLES.md)
- **最佳实践**: [docs/BEST_PRACTICES.md](../docs/BEST_PRACTICES.md)
- **配置指南**: [docs/CONFIGURATION.md](../docs/CONFIGURATION.md)
- **用户指南**: [docs/user-guide.md](../docs/user-guide.md)

---

## 获取帮助

如果遇到问题:

1. 查看文档: `docs/` 目录
2. 运行诊断: `la setup`
3. 提交 Issue: [GitHub Issues](https://github.com/yourname/learning-assistant/issues)

---

**版本**: v0.2.0
**更新日期**: 2026-04-10
**维护者**: Learning Assistant Team