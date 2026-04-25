"""
便捷函数 - 一行调用 Learning Assistant 功能.

提供简单的函数接口，无需实例化 AgentAPI 类。
适合快速脚本、Agent 简单调用、原型开发。

所有便捷函数内部使用 AgentAPI，确保一致性。

使用示例：
    # 视频总结
    from learning_assistant.api import summarize_video

    result = await summarize_video(url="https://...")
    print(result["summary"])

    # 列出技能
    from learning_assistant.api import list_available_skills

    skills = list_available_skills()
    for skill in skills:
        print(f"{skill['name']}: {skill['description']}")

    # 查看历史
    from learning_assistant.api import get_recent_history

    records = get_recent_history(limit=10)
"""

import asyncio
from typing import Any

from loguru import logger

from learning_assistant.api.agent_api import AgentAPI, get_api
from learning_assistant.api.schemas import (
    VideoSummaryResult,
    LinkSummaryResult,
    VocabularyResult,
)

# Shared instance for server usage (lazy loaded)
_shared_api_instance: AgentAPI | None = None


def get_shared_api() -> AgentAPI:
    """
    Get or create a shared AgentAPI instance.

    Used by server routes to avoid repeated initialization.
    The instance is created once and reused for all requests.

    Returns:
        Shared AgentAPI instance

    Example:
        >>> api = get_shared_api()
        >>> result = await api.summarize_video(url="https://...")
    """
    global _shared_api_instance
    if _shared_api_instance is None:
        logger.info("Creating shared AgentAPI instance")
        _shared_api_instance = AgentAPI()
    return _shared_api_instance


def reset_shared_api() -> None:
    """
    Reset the shared AgentAPI instance.

    Used for testing or when config changes require re-initialization.

    Example:
        >>> reset_shared_api()  # Clear instance
        >>> api = get_shared_api()  # Will create new instance
    """
    global _shared_api_instance
    _shared_api_instance = None
    logger.debug("Reset shared AgentAPI instance")


async def summarize_video(url: str, **options: Any) -> dict[str, Any]:
    """
    快速视频总结函数（异步）.

    这是最简单的视频总结方式，只需提供 URL 即可。
    返回结构化字典，包含总结、字幕、文件路径等。

    Args:
        url: 视频URL（支持 B站/YouTube/抖音）
        **options: 其他选项
            - format: 输出格式（markdown/pdf）
            - language: 总结语言（zh/en）
            - output_dir: 输出目录
            - cookie_file: Cookie 文件路径
            - word_timestamps: 是否启用词级时间戳

    Returns:
        结果字典，包含：
        - status: 状态（success/error）
        - url: 视频 URL
        - title: 视频标题
        - summary: 总结内容
        - transcript: 字幕文本
        - files: 输出文件路径
        - metadata: 视频元数据
        - timestamp: 时间戳

    Raises:
        VideoNotFoundError: 视频不存在
        VideoDownloadError: 下载失败
        TranscriptionError: 转录失败
        LLMAPIError: LLM 错误

    Example:
        >>> # 基本用法
        >>> result = await summarize_video("https://www.bilibili.com/video/BV...")
        >>> print(result["title"])
        >>> print(result["summary"]["content"])

        >>> # 完整参数
        >>> result = await summarize_video(
        ...     url="https://www.youtube.com/watch?v=...",
        ...     format="pdf",
        ...     language="en",
        ...     output_dir="./my-notes"
        ... )
    """
    logger.info(f"Quick video summary: {url}")

    api = get_api()
    result: VideoSummaryResult = await api.summarize_video(url=url, **options)

    return result.model_dump()


def list_available_skills() -> list[dict[str, Any]]:
    """
    列出可用技能.

    返回所有已加载技能的信息列表。

    Returns:
        技能列表，每个技能是一个字典：
        - name: 技能名称
        - description: 技能描述
        - version: 版本号
        - status: 状态（available/disabled/error）

    Example:
        >>> skills = list_available_skills()
        >>> for skill in skills:
        ...     print(f"{skill['name']}: {skill['description']}")
        video-summary: 视频内容总结，生成学习笔记
        list-skills: 列出所有可用技能
        learning-history: 查看学习历史记录
    """
    logger.debug("Quick list skills")

    api = get_api()
    skills = api.list_skills()

    return [skill.model_dump() for skill in skills]


def get_recent_history(limit: int = 10) -> list[dict[str, Any]]:
    """
    获取最近学习记录.

    查询最近的学习历史记录。

    Args:
        limit: 返回记录数量，默认为 10

    Returns:
        记录列表，每条记录是一个字典：
        - id: 记录 ID
        - module: 模块名称
        - title: 视频标题
        - url: 视频 URL
        - timestamp: 时间戳
        - status: 状态

    Example:
        >>> records = get_recent_history(limit=5)
        >>> for record in records:
        ...     print(f"[{record['timestamp']}] {record['title']}")
    """
    logger.debug(f"Quick get history: limit={limit}")

    api = get_api()
    records = api.get_history(limit=limit)

    return [record.model_dump() for record in records]


def search_history(search: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    搜索历史记录.

    根据关键词搜索学习历史记录。

    Args:
        search: 搜索关键词
        limit: 返回记录数量，默认为 10

    Returns:
        记录列表

    Example:
        >>> records = search_history(search="Python")
        >>> print(f"Found {len(records)} records about Python")
    """
    logger.debug(f"Quick search history: search={search}")

    api = get_api()
    records = api.get_history(limit=limit, search=search)

    return [record.model_dump() for record in records]


def get_statistics() -> dict[str, Any]:
    """
    获取学习统计信息.

    返回总体学习统计数据。

    Returns:
        统计字典，包含：
        - total_videos: 总视频数
        - total_duration: 总学习时长（秒）
        - most_watched_platform: 最常观看的平台
        - recent_activity: 最近活动记录

    Example:
        >>> stats = get_statistics()
        >>> print(f"Total videos: {stats['total_videos']}")
        >>> print(f"Total duration: {stats['total_duration']} seconds")
    """
    logger.debug("Quick get statistics")

    api = get_api()
    stats = api.get_statistics()

    return stats.model_dump()


def summarize_video_sync(url: str, **options: Any) -> dict[str, Any]:
    """
    同步版本的视频总结.

    适用于不支持异步的场景（如简单脚本）。
    内部使用 asyncio.run() 调用异步函数。

    注意：不能在异步函数内部调用此函数，会导致事件循环错误。

    Args:
        url: 视频URL
        **options: 其他选项（同 summarize_video）

    Returns:
        结果字典

    Example:
        >>> # 在普通脚本中使用
        >>> result = summarize_video_sync("https://...")
        >>> print(result["title"])
    """
    logger.info(f"Sync video summary: {url}")

    return asyncio.run(summarize_video(url, **options))


async def process_link(url: str, **options: Any) -> dict[str, Any]:
    """
    快速链接学习函数（异步）.

    这是最简单的链接处理方式，只需提供 URL 即可。
    返回结构化字典，包含知识卡片、问答、测验等。

    Args:
        url: 网页URL
        **options: 其他选项
            - provider: LLM 提供者（openai/anthropic/deepseek）
            - model: LLM 模型
            - output_dir: 输出目录
            - generate_quiz: 是否生成测验（默认 True）

    Returns:
        结果字典，包含：
        - status: 状态（success/error）
        - url: 原始URL
        - title: 文章标题
        - summary: 摘要
        - key_points: 核心要点
        - tags: 标签
        - word_count: 字数
        - reading_time: 阅读时间
        - difficulty: 难度
        - qa_pairs: 问答对
        - quiz: 测验题
        - files: 输出文件路径
        - timestamp: 时间戳

    Raises:
        ValueError: URL 无效或 API key 未设置
        RuntimeError: 处理失败

    Example:
        >>> # 基本用法
        >>> result = await process_link("https://example.com/article")
        >>> print(result["title"])
        >>> print(result["summary"])

        >>> # 完整参数
        >>> result = await process_link(
        ...     url="https://example.com/article",
        ...     provider="openai",
        ...     model="gpt-4",
        ...     generate_quiz=False
        ... )
    """
    logger.info(f"Quick link processing: {url}")

    api = get_api()
    result: LinkSummaryResult = await api.process_link(url=url, **options)

    return result.model_dump()


def process_link_sync(url: str, **options: Any) -> dict[str, Any]:
    """
    同步版本的链接学习.

    适用于不支持异步的场景（如简单脚本）。
    内部使用 asyncio.run() 调用异步函数。

    注意：不能在异步函数内部调用此函数，会导致事件循环错误。

    Args:
        url: 网页URL
        **options: 其他选项（同 process_link）

    Returns:
        结果字典

    Example:
        >>> # 在普通脚本中使用
        >>> result = process_link_sync("https://example.com/article")
        >>> print(result["title"])
    """
    logger.info(f"Sync link processing: {url}")

    return asyncio.run(process_link(url, **options))


async def extract_vocabulary(
    content: str,
    word_count: int = 10,
    difficulty: str = "intermediate",
    generate_story: bool = True,
    **options: Any,
) -> dict[str, Any]:
    """
    快速单词学习函数（异步）.

    这是最简单的单词提取方式，只需提供内容即可。
    返回结构化字典，包含单词卡、例句、上下文短文等。

    Args:
        content: 文本内容
        word_count: 提取单词数量（1-50）
        difficulty: 目标难度（beginner/intermediate/advanced）
        generate_story: 是否生成上下文短文
        **options: 其他选项
            - provider: LLM 提供者
            - model: LLM 模型
            - output_dir: 输出目录

    Returns:
        结果字典，包含：
        - status: 状态（success/error）
        - content: 源内容（前200字符）
        - vocabulary_cards: 单词卡列表
        - context_story: 上下文短文
        - statistics: 统计信息
        - files: 输出文件路径
        - timestamp: 时间戳

    Raises:
        ValueError: 内容为空或参数无效
        RuntimeError: 处理失败

    Example:
        >>> # 基本用法
        >>> result = await extract_vocabulary(
        ...     content="Machine learning is transforming industries..."
        ... )
        >>> print(f"Extracted {len(result['vocabulary_cards'])} words")

        >>> # 完整参数
        >>> result = await extract_vocabulary(
        ...     content="Your text here...",
        ...     word_count=15,
        ...     difficulty="advanced",
        ...     generate_story=False
        ... )
    """
    logger.info(f"Quick vocabulary extraction: {word_count} words")

    api = get_api()
    result: VocabularyResult = await api.extract_vocabulary(
        content=content,
        word_count=word_count,
        difficulty=difficulty,
        generate_story=generate_story,
        **options,
    )

    return result.model_dump()


def extract_vocabulary_sync(
    content: str,
    word_count: int = 10,
    difficulty: str = "intermediate",
    generate_story: bool = True,
    **options: Any,
) -> dict[str, Any]:
    """
    同步版本的单词学习.

    适用于不支持异步的场景（如简单脚本）。
    内部使用 asyncio.run() 调用异步函数。

    注意：不能在异步函数内部调用此函数，会导致事件循环错误。

    Args:
        content: 文本内容
        word_count: 提取单词数量
        difficulty: 目标难度
        generate_story: 是否生成短文
        **options: 其他选项（同 extract_vocabulary）

    Returns:
        结果字典

    Example:
        >>> # 在普通脚本中使用
        >>> result = extract_vocabulary_sync(content="Your text...")
        >>> print(f"Extracted {len(result['vocabulary_cards'])} words")
    """
    logger.info(f"Sync vocabulary extraction: {word_count} words")

    return asyncio.run(
        extract_vocabulary(
            content,
            word_count,
            difficulty,
            generate_story,
            **options,
        )
    )
