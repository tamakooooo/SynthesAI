"""
Video summary endpoint - async task processing.

Video processing takes 3-10 minutes, so we use async task queue.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from learning_assistant.api.exceptions import (
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
)
from learning_assistant.server.config import ServerConfig, get_server_config
from learning_assistant.server.task_manager import TaskManager, TaskStatus
from learning_assistant.server.context import ServerContext

router = APIRouter(prefix="/api/v1/video", tags=["video"])


def get_config() -> ServerConfig:
    """Get server config dependency."""
    return get_server_config()


def get_task_manager() -> TaskManager:
    """Get task manager from app state."""
    # Will be set in main.py lifespan
    from learning_assistant.server.main import app
    return app.state.task_manager


class VideoSubmitRequest(BaseModel):
    """Request model for video task submission."""

    url: HttpUrl = Field(description="Video URL (B站/YouTube/抖音)")
    format: str = Field(
        default="markdown",
        description="Output format (markdown/pdf/both)",
    )
    language: str = Field(default="zh", description="Summary language (zh/en)")
    output_dir: str | None = Field(default=None, description="Output directory")
    cookie_file: str | None = Field(
        default=None,
        description="Cookie file for authenticated download",
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Additional detail")


class TaskSubmitResponse(BaseModel):
    """Response for task submission."""

    task_id: str = Field(description="Task ID for tracking")
    status: str = Field(description="Initial status")
    message: str = Field(description="Status message")


class TaskStatusResponse(BaseModel):
    """Response for task status query."""

    task_id: str
    status: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    progress: float
    message: str
    error: str | None


@router.post("/submit", response_model=TaskSubmitResponse)
async def submit_video_task(
    request: VideoSubmitRequest,
    config: ServerConfig = Depends(get_config),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    Submit a video summary task.

    Video processing takes 3-10 minutes, so returns a task_id
    for tracking progress.

    Use GET /api/v1/video/{task_id}/status to check progress.
    Use GET /api/v1/video/{task_id}/result to get result when complete.
    """
    input_data: dict[str, Any] = {
        "url": str(request.url),
        "options": {
            "format": request.format,
            "language": request.language,
        },
    }

    if request.output_dir:
        input_data["options"]["output_dir"] = request.output_dir
    if request.cookie_file:
        input_data["options"]["cookie_file"] = request.cookie_file

    try:
        task_id = task_manager.submit_task(
            task_type="video_summary",
            input_data=input_data,
        )

        return TaskSubmitResponse(
            task_id=task_id,
            status="pending",
            message="Task submitted successfully",
        )

    except RuntimeError as e:
        if "queue is full" in str(e):
            raise HTTPException(
                status_code=503,
                detail=ErrorResponse(
                    error="QueueFull",
                    message="Task queue is full, try again later",
                ).model_dump(),
            )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="SubmitError",
                message=str(e),
            ).model_dump(),
        )


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_video_task_status(
    task_id: str,
    config: ServerConfig = Depends(get_config),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    Get video task status and progress.

    Returns current status and progress percentage.
    """
    task = task_manager.get_task_status(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="TaskNotFound",
                message=f"Task {task_id} not found",
            ).model_dump(),
        )

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        created_at=task.created_at.isoformat(),
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        progress=task.progress,
        message=task.message,
        error=task.error,
    )


@router.get("/{task_id}/result")
async def get_video_task_result(
    task_id: str,
    config: ServerConfig = Depends(get_config),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    Get video task result.

    Returns the full result only if task is completed.
    """
    task = task_manager.get_task_status(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="TaskNotFound",
                message=f"Task {task_id} not found",
            ).model_dump(),
        )

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="TaskNotComplete",
                message=f"Task status is {task.status.value}, not completed",
            ).model_dump(),
        )

    return task.result


@router.delete("/{task_id}")
async def cancel_video_task(
    task_id: str,
    config: ServerConfig = Depends(get_config),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    Cancel a pending or running video task.

    Only works for tasks that haven't completed.
    """
    task = task_manager.get_task_status(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="TaskNotFound",
                message=f"Task {task_id} not found",
            ).model_dump(),
        )

    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="CannotCancel",
                message=f"Task is already {task.status.value}",
            ).model_dump(),
        )

    success = task_manager.cancel_task(task_id)
    return {"task_id": task_id, "cancelled": success, "message": "Task cancelled"}