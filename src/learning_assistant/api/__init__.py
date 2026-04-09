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

from learning_assistant.api.agent_api import AgentAPI
from learning_assistant.api.convenience import (
    summarize_video,
    list_available_skills,
    get_recent_history,
    summarize_video_sync,
    process_link,
    process_link_sync,
    extract_vocabulary,
    extract_vocabulary_sync,
)

__all__ = [
    "AgentAPI",
    "summarize_video",
    "list_available_skills",
    "get_recent_history",
    "summarize_video_sync",
    "process_link",
    "process_link_sync",
    "extract_vocabulary",
    "extract_vocabulary_sync",
]
