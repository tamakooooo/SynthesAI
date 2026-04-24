"""
Query endpoints - skills, history, statistics.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query

from learning_assistant.api.schemas import (
    SkillInfo,
    HistoryRecord,
    LearningStatistics,
)
from learning_assistant.server.config import ServerConfig, get_server_config
from learning_assistant.server.middleware import verify_api_key_dependency
from learning_assistant.server.context import ServerContext

router = APIRouter(prefix="/api/v1", tags=["query"])


def get_config() -> ServerConfig:
    """Get server config dependency."""
    return get_server_config()


@router.get("/skills", response_model=list[SkillInfo])
async def list_skills(
    config: ServerConfig = Depends(get_config),
):
    """
    List all available skills/plugins.

    Returns information about all loaded modules.
    """
    api = ServerContext.get_api()
    return api.list_skills()


@router.get("/history", response_model=list[HistoryRecord])
async def get_history(
    limit: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None),
    module: str | None = Query(default=None),
    config: ServerConfig = Depends(get_config),
):
    """
    Get learning history records.

    Query parameters:
    - limit: Number of records to return
    - search: Search keyword
    - module: Filter by module name
    """
    api = ServerContext.get_api()
    return api.get_history(limit=limit, search=search, module=module)


@router.get("/statistics", response_model=LearningStatistics)
async def get_statistics(
    config: ServerConfig = Depends(get_config),
):
    """
    Get learning statistics.

    Returns aggregate statistics about learning history.
    """
    api = ServerContext.get_api()
    return api.get_statistics()