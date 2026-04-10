# Learning Assistant - API 使用示例

> 完整的 Python API 使用示例，涵盖所有核心功能
> 版本: v0.2.0 | 更新日期: 2026-04-10

---

## 📋 目录

- [快速开始](#快速开始)
- [视频总结 API](#视频总结-api)
- [链接学习 API](#链接学习-api)
- [单词学习 API](#单词学习-api)
- [历史记录 API](#历史记录-api)
- [高级用法](#高级用法)
- [最佳实践](#最佳实践)

---

## 快速开始

### 安装

```bash
pip install learning-assistant
```

### 基础导入

```python
# 方式 1: 便捷函数（推荐）
from learning_assistant.api import (
    summarize_video,
    process_link,
    extract_vocabulary,
    list_available_skills,
    get_recent_history,
)

# 方式 2: AgentAPI 类（完整控制）
from learning_assistant.api import AgentAPI

api = AgentAPI()
```

---

## 视频总结 API

### 1. 基础使用

```python
import asyncio
from learning_assistant.api import summarize_video

async def main():
    # 最简单的使用方式
    result = await summarize_video(
        url="https://www.bilibili.com/video/BV1234567890"
    )
    
    print(f"标题: {result['title']}")
    print(f"总结: {result['summary']['content']}")
    print(f"输出文件: {result['files']['summary_path']}")

asyncio.run(main())
```

### 2. 完整参数示例

```python
result = await summarize_video(
    url="https://www.youtube.com/watch?v=abc123",
    format="pdf",              # 输出格式: markdown (默认) 或 pdf
    language="en",             # 总结语言: zh (默认) 或 en
    output_dir="./my-notes",   # 自定义输出目录
    cookie_file="./cookies/youtube.txt",  # Cookie 文件（可选）
    word_timestamps=True,      # 启用词级时间戳
)

# 访问结果
print(f"视频时长: {result['metadata']['duration']}秒")
print(f"转录文本: {result['transcript'][:200]}...")
print(f"章节列表: {result['summary']['chapters']}")
```

### 3. 同步版本

```python
from learning_assistant.api import summarize_video_sync

# 在非异步环境中使用
result = summarize_video_sync(url="https://...")
print(result['title'])
```

### 4. 使用 AgentAPI 类

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# 异步调用
result = await api.summarize_video(
    url="https://...",
    format="markdown",
    language="zh"
)

# 访问结构化结果
print(result.title)
print(result.summary)
print(result.transcript)
print(result.files)
```

### 5. 批量处理示例

```python
import asyncio
from learning_assistant.api import summarize_video

async def process_batch(urls):
    """批量处理多个视频"""
    tasks = [
        summarize_video(url=url, generate_story=False)
        for url in urls
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"视频 {urls[i]} 处理失败: {result}")
        else:
            print(f"✅ {result['title']} - {result['files']['summary_path']}")

# 使用
urls = [
    "https://www.bilibili.com/video/BV1...",
    "https://www.youtube.com/watch?v=...",
    "https://www.douyin.com/video/...",
]

asyncio.run(process_batch(urls))
```

---

## 链接学习 API

### 1. 基础使用

```python
import asyncio
from learning_assistant.api import process_link

async def main():
    # 处理网页文章
    result = await process_link(
        url="https://example.com/article"
    )
    
    print(f"标题: {result['title']}")
    print(f"摘要: {result['summary']}")
    print(f"关键点: {result['key_points']}")
    print(f"阅读时间: {result['reading_time']}分钟")

asyncio.run(main())
```

### 2. 完整参数示例

```python
result = await process_link(
    url="https://blog.example.com/tech-post",
    provider="openai",         # LLM 提供者
    model="gpt-4",            # 模型选择
    output_dir="./links",     # 输出目录
    generate_quiz=True,       # 生成测验题
)

# 访问结果
print(f"字数: {result['word_count']}")
print(f"难度: {result['difficulty']}")
print(f"标签: {result['tags']}")
print(f"问答: {result['qa_pairs']}")
print(f"测验: {result['quiz']}")
```

### 3. 同步版本

```python
from learning_assistant.api import process_link_sync

result = process_link_sync(url="https://...")
print(result['title'])
```

### 4. 批量处理

```python
import asyncio
from learning_assistant.api import process_link

async def process_articles(urls):
    """批量处理多篇文章"""
    results = await asyncio.gather(
        *[process_link(url=url) for url in urls],
        return_exceptions=True
    )
    
    successful = [r for r in results if not isinstance(r, Exception)]
    print(f"成功处理 {len(successful)}/{len(urls)} 篇文章")
    
    return successful

# 使用
urls = [
    "https://blog1.example.com/post1",
    "https://blog2.example.com/post2",
    "https://news.example.com/article",
]

results = asyncio.run(process_articles(urls))
```

---

## 单词学习 API

### 1. 基础使用

```python
import asyncio
from learning_assistant.api import extract_vocabulary

async def main():
    # 从文本提取单词
    result = await extract_vocabulary(
        content="Machine learning is transforming industries across the globe..."
    )
    
    print(f"提取单词数: {len(result['vocabulary_cards'])}")
    
    # 查看单词卡
    for card in result['vocabulary_cards']:
        print(f"\n单词: {card['word']}")
        print(f"音标: {card['phonetic']['us']}")
        print(f"释义: {card['definition']['zh']}")
        print(f"例句: {card['example_sentences'][0]['sentence']}")

asyncio.run(main())
```

### 2. 完整参数示例

```python
result = await extract_vocabulary(
    content="Your text content here...",
    word_count=15,              # 提取单词数量 (1-50)
    difficulty="advanced",      # 难度: beginner/intermediate/advanced
    generate_story=True,        # 生成上下文故事
    output_dir="./vocab",       # 输出目录
    llm={                       # LLM 配置（可选）
        "provider": "openai",
        "model": "gpt-4"
    }
)

# 访问结果
print(f"难度分布: {result['statistics']['difficulty_distribution']}")

# 上下文故事
if result['context_story']:
    print(f"故事标题: {result['context_story']['title']}")
    print(f"故事内容: {result['context_story']['content']}")
    print(f"目标单词: {result['context_story']['target_words']}")
```

### 3. 从文件读取

```python
from pathlib import Path

# 读取文件内容
content = Path("article.txt").read_text(encoding="utf-8")

result = await extract_vocabulary(
    content=content,
    word_count=20,
    difficulty="intermediate"
)
```

### 4. 集成到其他模块

```python
import asyncio
from learning_assistant.api import process_link, extract_vocabulary

async def learn_from_url(url):
    """从URL学习：提取文章 → 学习单词"""
    
    # 1. 处理链接
    article = await process_link(url=url)
    print(f"文章标题: {article['title']}")
    
    # 2. 从摘要提取单词
    vocab = await extract_vocabulary(
        content=article['summary'],
        word_count=10,
        generate_story=True
    )
    
    print(f"学到 {len(vocab['vocabulary_cards'])} 个单词")
    
    return {
        "article": article,
        "vocabulary": vocab
    }

# 使用
result = asyncio.run(learn_from_url("https://..."))
```

---

## 历史记录 API

### 1. 查看最近记录

```python
from learning_assistant.api import get_recent_history

# 查看最近10条记录
records = get_recent_history(limit=10)

for record in records:
    print(f"[{record['timestamp']}] {record['module']}: {record['title']}")
    print(f"  URL: {record['url']}")
    print(f"  状态: {record['status']}")
```

### 2. 搜索历史

```python
from learning_assistant.api import search_history

# 搜索关键词
records = search_history(search="Python", limit=20)

print(f"找到 {len(records)} 条相关记录")
for record in records:
    print(f"- {record['title']}")
```

### 3. 使用 AgentAPI

```python
from learning_assistant.api import AgentAPI

api = AgentAPI()

# 查看最近记录
records = api.get_history(limit=10)

# 按模块筛选
video_records = api.get_history(module="video_summary", limit=20)

# 获取统计信息
stats = api.get_statistics()
print(f"总视频数: {stats.total_videos}")
print(f"总时长: {stats.total_duration}秒")
print(f"最常观看平台: {stats.most_watched_platform}")
```

---

## 高级用法

### 1. 使用不同的 LLM 提供者

```python
from learning_assistant.api import AgentAPI

# OpenAI
result = await summarize_video(
    url="https://...",
    llm={"provider": "openai", "model": "gpt-4-turbo"}
)

# Anthropic Claude
result = await summarize_video(
    url="https://...",
    llm={"provider": "anthropic", "model": "claude-3-opus-20240229"}
)

# DeepSeek
result = await summarize_video(
    url="https://...",
    llm={"provider": "deepseek", "model": "deepseek-chat"}
)
```

### 2. 自定义输出

```python
import asyncio
from learning_assistant.api import summarize_video

async def custom_output():
    result = await summarize_video(
        url="https://...",
        output_dir="./custom-output",
        format="markdown"
    )
    
    # 自定义处理输出
    summary_path = result['files']['summary_path']
    
    # 读取并处理
    from pathlib import Path
    content = Path(summary_path).read_text(encoding="utf-8")
    
    # 自定义处理逻辑
    processed_content = content.upper()  # 示例处理
    
    # 保存到新位置
    Path("./processed_summary.md").write_text(
        processed_content,
        encoding="utf-8"
    )

asyncio.run(custom_output())
```

### 3. 错误处理

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
        return result
        
    except VideoNotFoundError:
        print(f"❌ 视频不存在: {url}")
        
    except VideoDownloadError as e:
        print(f"❌ 下载失败: {e}")
        
    except TranscriptionError as e:
        print(f"❌ 转录失败: {e}")
        
    except LLMAPIError as e:
        print(f"❌ LLM 错误: {e}")
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
    
    return None

# 使用
result = asyncio.run(safe_summarize("https://..."))
if result:
    print("✅ 处理成功")
```

### 4. 进度监控

```python
import asyncio
from learning_assistant.api import summarize_video

async def with_progress(url):
    """带进度监控的视频处理"""
    
    # 定义进度回调
    def progress_callback(stage, message):
        print(f"[{stage}] {message}")
    
    result = await summarize_video(
        url=url,
        progress_callback=progress_callback  # (如果支持)
    )
    
    return result

asyncio.run(with_progress("https://..."))
```

---

## 最佳实践

### 1. 异步批处理

```python
import asyncio
from learning_assistant.api import summarize_video, process_link

async def batch_process(video_urls, article_urls):
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
    
    # 统计结果
    successes = sum(1 for r in results if not isinstance(r, Exception))
    print(f"成功: {successes}/{len(results)}")
    
    return results
```

### 2. 缓存管理

```python
from pathlib import Path
import hashlib

def get_cache_key(url):
    """生成缓存键"""
    return hashlib.md5(url.encode()).hexdigest()

def check_cache(url, cache_dir="./cache"):
    """检查缓存"""
    cache_key = get_cache_key(url)
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    
    if cache_file.exists():
        import json
        return json.loads(cache_file.read_text())
    return None

def save_cache(url, result, cache_dir="./cache"):
    """保存缓存"""
    cache_key = get_cache_key(url)
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    
    import json
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
```

### 3. 环境变量管理

```python
import os
from pathlib import Path

# 方式 1: 使用 .env 文件
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]

# 方式 2: 使用配置文件
import yaml

config_path = Path("config/settings.local.yaml")
if config_path.exists():
    config = yaml.safe_load(config_path.read_text())
    api_key = config["llm"]["openai"]["api_key"]
```

### 4. 日志记录

```python
import logging
from learning_assistant.api import summarize_video

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def logged_summarize(url):
    """带日志的视频总结"""
    logger.info(f"开始处理视频: {url}")
    
    try:
        result = await summarize_video(url=url)
        logger.info(f"处理成功: {result['title']}")
        return result
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise
```

---

## 完整示例项目

### 学习工作流

```python
import asyncio
from learning_assistant.api import (
    summarize_video,
    process_link,
    extract_vocabulary,
    get_recent_history,
)

async def learning_workflow():
    """完整的学习工作流"""
    
    print("📚 开始学习工作流...\n")
    
    # 1. 视频学习
    print("1️⃣ 观看视频并总结")
    video_result = await summarize_video(
        url="https://www.bilibili.com/video/BV1..."
    )
    print(f"   ✅ 视频标题: {video_result['title']}")
    print(f"   📄 总结文件: {video_result['files']['summary_path']}")
    
    # 2. 扩展阅读
    print("\n2️⃣ 扩展阅读")
    article_result = await process_link(
        url="https://blog.example.com/related-article"
    )
    print(f"   ✅ 文章标题: {article_result['title']}")
    print(f"   📊 关键点: {len(article_result['key_points'])}个")
    
    # 3. 单词学习
    print("\n3️⃣ 学习单词")
    combined_content = f"{video_result['summary']['content']}\n{article_result['summary']}"
    vocab_result = await extract_vocabulary(
        content=combined_content,
        word_count=10,
        generate_story=True
    )
    print(f"   ✅ 学习单词: {len(vocab_result['vocabulary_cards'])}个")
    
    # 4. 查看历史
    print("\n4️⃣ 学习历史")
    history = get_recent_history(limit=5)
    print(f"   ✅ 最近学习: {len(history)}条记录")
    
    print("\n🎉 学习完成！")
    
    return {
        "video": video_result,
        "article": article_result,
        "vocabulary": vocab_result,
        "history": history
    }

# 运行
result = asyncio.run(learning_workflow())
```

---

## 相关文档

- [配置指南](./CONFIGURATION.md)
- [API 参考](./api.md)
- [用户指南](./user-guide.md)
- [常见问题](./faq.md)

---

**版本**: v0.2.0  
**更新日期**: 2026-04-10  
**维护者**: Learning Assistant Team