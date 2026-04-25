"""
Learning Assistant Agent API.

提供标准化接口供 Agent 框架使用。

支持的调用方式：
1. 直接调用便捷函数（推荐）
2. 使用 AgentAPI 类
3. 集成到 Agent 框架

使用示例：
    from learning_assistant.api import summarize_video

    result = await summarize_video(url="https://...")
    print(result["summary"])
"""

from learning_assistant.api.agent_api import AgentAPI, get_api, reset_api
from learning_assistant.api.convenience import (
    summarize_video,
    list_available_skills,
    get_recent_history,
    summarize_video_sync,
    process_link,
    process_link_sync,
    extract_vocabulary,
    extract_vocabulary_sync,
    get_shared_api,
    reset_shared_api,
)
from learning_assistant.api.helpers import (
    detect_content_type,
    get_platform,
    is_video_url,
    is_article_url,
    suggest_module,
)

__all__ = [
    "AgentAPI",
    "get_api",
    "reset_api",
    "summarize_video",
    "list_available_skills",
    "get_recent_history",
    "summarize_video_sync",
    "process_link",
    "process_link_sync",
    "extract_vocabulary",
    "extract_vocabulary_sync",
    "get_shared_api",
    "reset_shared_api",
    "detect_content_type",
    "get_platform",
    "is_video_url",
    "is_article_url",
    "suggest_module",
]
