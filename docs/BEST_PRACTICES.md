# Best Practices Guide

> **最佳实践指南** - 提高 Learning Assistant 使用效率和质量的实用建议

**版本**: v0.2.0 | **更新日期**: 2026-04-10

---

## 📋 目录

- [性能优化](#性能优化)
- [成本控制](#成本控制)
- [质量提升](#质量提升)
- [工作流程](#工作流程)
- [常见陷阱](#常见陷阱)
- [最佳示例](#最佳示例)

---

## 性能优化

### 1. 批量处理视频

**错误方式** (串行处理):

```python
import asyncio

async def slow_processing():
    # 逐个处理，效率低
    for url in urls:
        result = await summarize_video(url)
        print(result['title'])
```

**正确方式** (并行处理):

```python
import asyncio
from learning_assistant.api import summarize_video

async def fast_processing(urls):
    # 并发处理，效率高
    tasks = [summarize_video(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计成功/失败
    successes = sum(1 for r in results if not isinstance(r, Exception))
    print(f"成功处理: {successes}/{len(urls)}")

    return results

# 使用
urls = [
    "https://www.bilibili.com/video/BV1...",
    "https://www.youtube.com/watch?v=...",
]
results = asyncio.run(fast_processing(urls))
```

**性能对比**:
- 串行处理 5 个视频: ~15-20 分钟
- 并行处理 5 个视频: ~5-7 分钟 (节省 60-70% 时间)

### 2. 使用缓存避免重复处理

**场景**: 同一个视频多次总结

**推荐做法**:

```python
from pathlib import Path
import hashlib
import json

def get_cache_key(url):
    """生成缓存键"""
    return hashlib.md5(url.encode()).hexdigest()

def check_cache(url, cache_dir="data/cache"):
    """检查缓存"""
    cache_key = get_cache_key(url)
    cache_file = Path(cache_dir) / f"{cache_key}.json"

    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None

def save_cache(url, result, cache_dir="data/cache"):
    """保存缓存"""
    cache_key = get_cache_key(url)
    cache_file = Path(cache_dir) / f"{cache_key}.json"

    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

# 使用
async def smart_summarize(url):
    # 先检查缓存
    cached = check_cache(url)
    if cached:
        print(f"✅ 使用缓存: {cached['title']}")
        return cached

    # 无缓存，执行处理
    result = await summarize_video(url)

    # 保存缓存
    save_cache(url, result)

    return result
```

### 3. 调整并发 Worker 数量

**根据 CPU 核数调整**:

```yaml
# config/settings.yaml
performance:
  multiprocessing: true
  worker_count: 4  # 根据实际情况调整
```

**建议值**:
- 2 核 CPU: `worker_count = 2`
- 4 核 CPU: `worker_count = 3-4`
- 8 核 CPU: `worker_count = 6-8`
- 16 核 CPU: `worker_count = 10-12`

**注意**: Worker 数量过多会导致资源竞争，反而降低性能。

### 4. 选择合适的视频质量

**下载质量配置**:

```yaml
download:
  quality: "medium"  # 推荐: medium
```

**质量对比**:

| 质量 | 下载速度 | 文件大小 | 转录准确率 | 推荐场景 |
|------|---------|---------|-----------|---------|
| best | 慢 (10-20 分钟) | 大 (500MB-1GB) | 高 (>95%) | 重要视频，需要高精度 |
| medium | 快 (5-10 分钟) | 中 (100-300MB) | 高 (>90%) | **日常使用，推荐** |
| worst | 极快 (<5 分钟) | 小 (<100MB) | 中 (80-85%) | 快速预览，不重要视频 |

**建议**:
- 大部分情况使用 `medium`
- 重要课程、技术视频使用 `best`
- 快速测试使用 `worst`

---

## 成本控制

### 1. 设置预算限额

**配置限额**:

```yaml
llm:
  cost_tracking:
    enabled: true
    daily_limit: 10.0      # 每日限额 $10
    monthly_limit: 100.0   # 每月限额 $100
    warning_threshold: 0.8 # 达到 80% 时警告
```

**监控成本**:

```bash
# 查看历史记录和成本
la history --stats

# 或使用 API
from learning_assistant.api import AgentAPI

api = AgentAPI()
stats = api.get_statistics()
print(f"总视频数: {stats.total_videos}")
print(f"总成本估算: ${stats.estimated_cost}")
```

### 2. 选择经济实惠的模型

**模型成本对比** (OpenAI):

| 模型 | 价格 (每 1K tokens) | 质量 | 推荐场景 |
|------|-------------------|------|---------|
| gpt-4o | $0.005 (输入) / $0.015 (输出) | 最高 | 重要总结，复杂分析 |
| gpt-4-turbo | $0.01 / $0.03 | 高 | 技术视频，学术论文 |
| gpt-3.5-turbo | $0.0005 / $0.0015 | 中 | **日常使用，推荐** |
| kimi-k2.5 | 自定义端点 | 高 | **经济实惠，推荐** |

**建议配置**:

```yaml
llm:
  default_provider: "openai"
  providers:
    openai:
      default_model: "gpt-3.5-turbo"  # 经济实惠
      # 或使用自定义端点
      base_url: "https://api.tamako.online/v1"
      default_model: "kimi-k2.5"
```

### 3. 控制输出长度

**减少输出 Token 数量**:

```yaml
modules:
  video_summary:
    config:
      summary:
        max_tokens: 1500  # 降低到 1500 (默认 2000)
```

**影响**:
- 2000 tokens: 约 1500 字中文总结 (详细)
- 1500 tokens: 约 1100 字中文总结 (适中，**推荐**)
- 1000 tokens: 约 750 字中文总结 (简洁)

**建议**:
- 一般视频: `max_tokens = 1500`
- 重要视频: `max_tokens = 2000`
- 快速预览: `max_tokens = 1000`

### 4. 批量处理减少 API 调用

**错误方式** (多个单词分别查询):

```python
# 低效: 每个单词单独查询
for word in ["machine", "learning", "transform"]:
    result = await extract_vocabulary(content=word)
```

**正确方式** (一次查询多个单词):

```python
# 高效: 一次查询提取多个单词
combined_text = "Machine learning is transforming industries..."
result = await extract_vocabulary(
    content=combined_text,
    word_count=10  # 一次提取 10 个单词
)

# 只调用一次 LLM API，节省成本
```

---

## 质量提升

### 1. 选择合适的 Whisper 模型

**Whisper 模型对比**:

| 模型 | 准确率 | 速度 | 内存占用 | 推荐场景 |
|------|-------|------|---------|---------|
| tiny | 75-80% | 极快 | <1GB | 快速测试，不重要 |
| base | 85-90% | 快 | ~1GB | **日常使用，推荐** |
| small | 90-95% | 中 | ~2GB | 重要视频，需要高精度 |
| medium | 95-98% | 慢 | ~5GB | 专业用途，学术研究 |
| large | >98% | 很慢 | ~10GB | 最高精度，专业转录 |

**配置**:

```yaml
transcription:
  model: "base"  # 推荐: base
  language: "auto"
  vad: true      # 启用语音活动检测
```

**建议**:
- 大部分情况使用 `base`
- 技术课程、学术视频使用 `small`
- 最高精度要求使用 `medium` (需要足够内存)

### 2. 启用 VAD (语音活动检测)

**VAD 的作用**:
- 过滤静音片段
- 提高转录准确率
- 减少无关内容

**配置**:

```yaml
transcription:
  vad: true  # 强烈推荐启用
```

**效果对比**:
- 无 VAD: 包含静音、背景音，准确率 85%
- 启用 VAD: 只转录语音，准确率 90-95%

### 3. 调整 LLM 温度参数

**温度参数说明**:
- `temperature = 0.0`: 最确定性，输出稳定 (推荐用于总结)
- `temperature = 0.3`: 较稳定，允许轻微变化 (**推荐默认值**)
- `temperature = 0.7`: 中等，允许创造性输出
- `temperature = 1.0`: 高创造性，输出多变 (不推荐用于总结)

**配置**:

```yaml
llm:
  providers:
    openai:
      temperature: 0.3  # 推荐: 0.3
```

**不同场景建议**:
- 视频总结: `temperature = 0.3` (稳定，准确)
- 单词学习: `temperature = 0.5` (允许变化)
- 链接学习: `temperature = 0.3` (稳定)
- 故事生成: `temperature = 0.7` (创造性)

### 4. 使用词级时间戳

**启用词级时间戳**:

```python
result = await summarize_video(
    url="https://...",
    word_timestamps=True  # 启用词级时间戳
)

# 输出更精确的时间信息
for word_info in result['transcript_words']:
    print(f"{word_info['word']}: {word_info['start']}-{word_info['end']}")
```

**优势**:
- 精确到每个词的时间
- 生成高质量字幕 (SRT、VTT)
- 方便定位关键内容

**劣势**:
- 转录时间稍长 (+10-20%)
- 输出数据量大

**建议**: 需要精确字幕时启用，一般情况可不启用。

---

## 工作流程

### 1. 标准学习流程

**推荐流程**:

```python
import asyncio
from learning_assistant.api import (
    summarize_video,
    process_link,
    extract_vocabulary,
    get_recent_history,
)

async def standard_workflow():
    """标准学习工作流"""

    # 1. 视频学习
    video_result = await summarize_video(
        url="https://www.bilibili.com/video/BV...",
        format="markdown"
    )
    print(f"✅ 视频总结完成: {video_result['title']}")

    # 2. 扩展阅读
    article_result = await process_link(
        url="https://blog.example.com/article"
    )
    print(f"✅ 文章总结完成: {article_result['title']}")

    # 3. 单词学习 (从视频和文章内容)
    combined_content = f"{video_result['summary']['content']}\n{article_result['summary']}"
    vocab_result = await extract_vocabulary(
        content=combined_content,
        word_count=10,
        generate_story=True
    )
    print(f"✅ 单词提取完成: {len(vocab_result['vocabulary_cards'])} 个单词")

    # 4. 查看学习历史
    history = get_recent_history(limit=10)
    print(f"✅ 最近学习: {len(history)} 条记录")

    return {
        "video": video_result,
        "article": article_result,
        "vocabulary": vocab_result,
        "history": history,
    }

# 运行
result = asyncio.run(standard_workflow())
```

### 2. 错误处理流程

**完善的错误处理**:

```python
import asyncio
from learning_assistant.api import summarize_video
from learning_assistant.api.exceptions import (
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
)

async def safe_summarize(url):
    """安全的视频总结，包含完整错误处理"""

    try:
        result = await summarize_video(url=url)
        return {"status": "success", "data": result}

    except VideoNotFoundError:
        return {"status": "error", "message": "视频不存在"}

    except VideoDownloadError as e:
        return {"status": "error", "message": f"下载失败: {e}"}

    except TranscriptionError as e:
        return {"status": "error", "message": f"转录失败: {e}"}

    except LLMAPIError as e:
        return {"status": "error", "message": f"LLM 错误: {e}"}

    except Exception as e:
        return {"status": "error", "message": f"未知错误: {e}"}

# 使用
result = asyncio.run(safe_summarize("https://..."))
if result["status"] == "success":
    print(f"✅ 成功: {result['data']['title']}")
else:
    print(f"❌ 失败: {result['message']}")
```

### 3. 批量处理流程

**批量处理多个任务**:

```python
import asyncio
from learning_assistant.api import summarize_video, process_link

async def batch_workflow(video_urls, article_urls):
    """批量处理视频和文章"""

    # 并发处理所有任务
    video_tasks = [summarize_video(url) for url in video_urls]
    article_tasks = [process_link(url) for url in article_urls]

    # 等待所有任务完成
    results = await asyncio.gather(
        *video_tasks,
        *article_tasks,
        return_exceptions=True
    )

    # 分类结果
    video_results = results[:len(video_urls)]
    article_results = results[len(video_urls):]

    # 统计
    video_success = sum(1 for r in video_results if not isinstance(r, Exception))
    article_success = sum(1 for r in article_results if not isinstance(r, Exception))

    print(f"视频处理: {video_success}/{len(video_urls)}")
    print(f"文章处理: {article_success}/{len(article_urls)}")

    return {
        "videos": video_results,
        "articles": article_results,
    }

# 使用
videos = ["https://...", "https://..."]
articles = ["https://...", "https://..."]
results = asyncio.run(batch_workflow(videos, articles))
```

---

## 常见陷阱

### 1. ❌ 在循环中调用异步函数

**错误做法**:

```python
# ❌ 错误: 在循环中调用异步函数但不等待
for url in urls:
    summarize_video(url)  # 不等待，无法获取结果

# ❌ 错误: 使用 sync 版本在异步环境中
async def bad_example():
    for url in urls:
        result = summarize_video_sync(url)  # 阻塞异步环境
```

**正确做法**:

```python
# ✅ 正确: 使用 asyncio.gather
async def good_example(urls):
    tasks = [summarize_video(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. ❌ 不处理异常

**错误做法**:

```python
# ❌ 错误: 不处理异常
result = await summarize_video(url)  # 可能抛出异常
print(result['title'])  # 如果异常，这行不会执行
```

**正确做法**:

```python
# ✅ 正确: 完整错误处理
try:
    result = await summarize_video(url)
    print(result['title'])
except Exception as e:
    print(f"处理失败: {e}")
    # 记录失败 URL，稍后重试
```

### 3. ❌ 使用错误的模型参数

**错误做法**:

```python
# ❌ 错误: temperature 过高，输出不稳定
result = await summarize_video(
    url=url,
    llm={"temperature": 1.0}  # 总结任务不应使用高温度
)
```

**正确做法**:

```python
# ✅ 正确: 使用合适的温度参数
result = await summarize_video(
    url=url,
    llm={"temperature": 0.3}  # 总结任务推荐 0.3
)
```

### 4. ❌ 不使用缓存

**错误做法**:

```python
# ❌ 错误: 每次都重新处理相同视频
async def bad_workflow():
    # 第一次处理
    result1 = await summarize_video(url)
    # 第二次处理同一个视频
    result2 = await summarize_video(url)  # 重复消耗成本和时间
```

**正确做法**:

```python
# ✅ 正确: 使用缓存
async def good_workflow(url):
    cached = check_cache(url)
    if cached:
        return cached

    result = await summarize_video(url)
    save_cache(url, result)
    return result
```

### 5. ❌ 不验证 API Key

**错误做法**:

```python
# ❌ 错误: 不检查 API Key 是否配置
result = await summarize_video(url)  # 可能因 API Key 缺失而失败
```

**正确做法**:

```python
# ✅ 正确: 先验证配置
import os
from learning_assistant.api import summarize_video

async def safe_workflow(url):
    # 检查 API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ API Key 未配置")
        return None

    try:
        result = await summarize_video(url)
        return result
    except Exception as e:
        print(f"处理失败: {e}")
        return None
```

---

## 最佳示例

### 1. 完整的生产级代码

```python
"""
生产级视频总结脚本
包含: 缓存、错误处理、日志、成本控制
"""
import asyncio
import logging
from pathlib import Path
import hashlib
import json
from datetime import datetime
from learning_assistant.api import summarize_video
from learning_assistant.api.exceptions import (
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """生产级视频处理器"""

    def __init__(self, cache_dir="data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, url):
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()

    def _check_cache(self, url):
        """检查缓存"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            logger.info(f"✅ 使用缓存: {url}")
            return json.loads(cache_file.read_text())
        return None

    def _save_cache(self, url, result):
        """保存缓存"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2)
        )
        logger.info(f"✅ 缓存已保存: {url}")

    async def process(self, url, skip_cache=False):
        """处理单个视频"""
        logger.info(f"开始处理: {url}")

        # 检查缓存
        if not skip_cache:
            cached = self._check_cache(url)
            if cached:
                return cached

        # 处理视频
        try:
            result = await summarize_video(
                url=url,
                format="markdown",
                language="zh"
            )

            # 保存缓存
            self._save_cache(url, result)

            logger.info(f"✅ 处理成功: {result['title']}")
            return result

        except VideoNotFoundError:
            logger.error(f"❌ 视频不存在: {url}")
            return None

        except VideoDownloadError as e:
            logger.error(f"❌ 下载失败: {e}")
            return None

        except TranscriptionError as e:
            logger.error(f"❌ 转录失败: {e}")
            return None

        except LLMAPIError as e:
            logger.error(f"❌ LLM 错误: {e}")
            return None

        except Exception as e:
            logger.error(f"❌ 未知错误: {e}")
            return None

    async def batch_process(self, urls, max_concurrent=3):
        """批量处理视频"""
        logger.info(f"批量处理: {len(urls)} 个视频")

        # 分批处理，控制并发数
        batches = [
            urls[i:i + max_concurrent]
            for i in range(0, len(urls), max_concurrent)
        ]

        all_results = []
        for batch in batches:
            tasks = [self.process(url) for url in batch]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)

        # 统计
        successes = sum(1 for r in all_results if r is not None)
        logger.info(f"✅ 处理完成: {successes}/{len(urls)}")

        return all_results

# 使用
async def main():
    processor = VideoProcessor()

    urls = [
        "https://www.bilibili.com/video/BV1...",
        "https://www.youtube.com/watch?v=...",
    ]

    results = await processor.batch_process(urls, max_concurrent=3)

    # 输出统计
    for i, result in enumerate(results):
        if result:
            print(f"{i+1}. ✅ {result['title']}")
        else:
            print(f"{i+1}. ❌ 处理失败")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 学习笔记整理脚本

```python
"""
学习笔记整理脚本
整合视频、文章、单词学习
"""
import asyncio
from pathlib import Path
from datetime import datetime
from learning_assistant.api import (
    summarize_video,
    process_link,
    extract_vocabulary,
)

async def create_learning_note(video_url, article_urls):
    """创建综合学习笔记"""

    # 1. 处理视频
    print("🎬 处理视频...")
    video_result = await summarize_video(
        url=video_url,
        format="markdown"
    )

    # 2. 处理相关文章
    print("📚 处理文章...")
    article_results = await asyncio.gather(
        *[process_link(url) for url in article_urls]
    )

    # 3. 提取单词
    print("📝 提取单词...")
    combined_content = "\n\n".join([
        video_result['summary']['content'],
        *[r['summary'] for r in article_results]
    ])

    vocab_result = await extract_vocabulary(
        content=combined_content,
        word_count=15,
        generate_story=True
    )

    # 4. 整理笔记
    note_path = Path(f"data/outputs/learning_note_{datetime.now().strftime('%Y%m%d')}.md")
    note_content = f"""# 学习笔记 - {datetime.now().strftime('%Y年%m月%d日')}

## 🎬 视频总结

**标题**: {video_result['title']}
**平台**: {video_result['metadata']['platform']}
**时长**: {video_result['metadata']['duration']} 秒

### 内容摘要

{video_result['summary']['content']}

### 关键章节

"""

    for chapter in video_result['summary']['chapters']:
        note_content += f"""
#### {chapter['title']}

> ⏱️ {chapter['start_time']}

{chapter['summary']}
"""

    note_content += "\n\n## 📚 扩展阅读\n\n"

    for i, article in enumerate(article_results):
        note_content += f"""
### 文章 {i+1}: {article['title']}

**来源**: {article['source']}
**阅读时间**: {article['reading_time']} 分钟
**难度**: {article['difficulty']}

**摘要**: {article['summary']}

**关键点**:
"""
        for point in article['key_points']:
            note_content += f"- {point}\n"

    note_content += "\n\n## 📝 单词学习\n\n"

    for card in vocab_result['vocabulary_cards']:
        note_content += f"""
### {card['word']}

**音标**: {card['phonetic']['us']}
**释义**: {card['definition']['zh']}
**例句**: {card['example_sentences'][0]['sentence']}
"""

    if vocab_result['context_story']:
        note_content += f"""

## 📖 上下文故事

{vocab_result['context_story']['content']}

**目标单词**: {', '.join(vocab_result['context_story']['target_words'])}
"""

    # 5. 保存笔记
    note_path.parent.mkdir(exist_ok=True)
    note_path.write_text(note_content, encoding="utf-8")

    print(f"✅ 学习笔记已保存: {note_path}")

    return note_path

# 使用
async def main():
    note = await create_learning_note(
        video_url="https://www.bilibili.com/video/BV1...",
        article_urls=[
            "https://blog.example.com/post1",
            "https://news.example.com/article",
        ]
    )

    print(f"🎉 学习笔记创建完成!")

asyncio.run(main())
```

---

## 相关文档

- [API 使用示例](./API_EXAMPLES.md)
- [配置指南](./CONFIGURATION.md)
- [用户指南](./user-guide.md)
- [常见问题](./faq.md)

---

**版本**: v0.2.0
**更新日期**: 2026-04-10
**维护者**: Learning Assistant Team