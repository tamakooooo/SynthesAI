"""
Task manager for async video processing.

Video summary tasks can take 3-10 minutes, so they need
async processing with task queue and status tracking.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine

from loguru import logger

from learning_assistant.server.config import TaskQueueConfig


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Task information."""

    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: float = 0.0
    message: str = ""
    result: dict[str, Any] | None = None
    error: str | None = None
    input_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
        }


class TaskManager:
    """
    In-memory task manager for async video processing.

    Uses asyncio for background task execution.
    Suitable for single-server deployment.
    """

    def __init__(self, config: TaskQueueConfig):
        self.config = config
        self.tasks: dict[str, TaskInfo] = {}
        self.queue: asyncio.Queue[str] = asyncio.Queue(
            maxsize=config.max_queue_size
        )
        self.active_tasks: int = 0
        self._worker_task: asyncio.Task | None = None

    async def start_worker(self) -> None:
        """Start background worker."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("TaskManager worker started")

    async def stop_worker(self) -> None:
        """Stop background worker."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            logger.info("TaskManager worker stopped")

    async def _worker_loop(self) -> None:
        """Worker loop for processing tasks."""
        while True:
            try:
                task_id = await self.queue.get()

                if self.active_tasks >= self.config.max_concurrent:
                    # Put back in queue if at capacity
                    await asyncio.sleep(1)
                    await self.queue.put(task_id)
                    continue

                task_info = self.tasks.get(task_id)
                if not task_info:
                    logger.warning(f"Task {task_id} not found")
                    continue

                if task_info.status == TaskStatus.CANCELLED:
                    continue

                # Start processing
                self.active_tasks += 1
                task_info.status = TaskStatus.RUNNING
                task_info.started_at = datetime.now()
                task_info.message = "Processing started"

                try:
                    await self._process_task(task_info)
                    task_info.status = TaskStatus.COMPLETED
                    task_info.completed_at = datetime.now()
                    task_info.progress = 1.0
                    task_info.message = "Processing completed"
                except asyncio.CancelledError:
                    task_info.status = TaskStatus.CANCELLED
                    task_info.message = "Task cancelled"
                except Exception as e:
                    task_info.status = TaskStatus.FAILED
                    task_info.error = str(e)
                    task_info.message = f"Processing failed: {e}"
                    logger.error(f"Task {task_id} failed: {e}")

                finally:
                    self.active_tasks -= 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")

    async def _process_task(self, task_info: TaskInfo) -> None:
        """Process a video summary task."""
        from learning_assistant.server.context import ServerContext

        api = ServerContext.get_api()
        url = task_info.input_data.get("url")
        options = task_info.input_data.get("options", {})

        task_info.message = "Downloading video..."
        task_info.progress = 0.1

        result = await api.summarize_video(url=url, **options)

        task_info.result = result.model_dump()
        task_info.message = "Summary generated"

    def submit_task(
        self,
        task_type: str,
        input_data: dict[str, Any],
        processor: Callable[..., Coroutine[Any, Any, Any]] | None = None,
    ) -> str:
        """
        Submit a new task.

        Args:
            task_type: Type of task (e.g., "video_summary")
            input_data: Input data for the task
            processor: Optional custom processor function

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task_info = TaskInfo(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            input_data=input_data,
            message="Task submitted",
        )

        self.tasks[task_id] = task_info

        # Add to queue
        try:
            self.queue.put_nowait(task_id)
            logger.info(f"Task {task_id} submitted")
        except asyncio.QueueFull:
            # Remove from tasks if queue is full
            del self.tasks[task_id]
            raise RuntimeError("Task queue is full")

        return task_id

    def get_task_status(self, task_id: str) -> TaskInfo | None:
        """Get task status."""
        return self.tasks.get(task_id)

    def get_task_result(self, task_id: str) -> dict[str, Any] | None:
        """Get task result if completed."""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.result
        return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.tasks.get(task_id)
        if task and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            task.status = TaskStatus.CANCELLED
            task.message = "Task cancelled by user"
            logger.info(f"Task {task_id} cancelled")
            return True
        return False

    def cleanup_old_tasks(self) -> int:
        """Remove tasks older than TTL."""
        now = datetime.now()
        ttl_seconds = self.config.result_ttl
        removed = 0

        for task_id, task in list(self.tasks.items()):
            if task.completed_at:
                age = (now - task.completed_at).total_seconds()
                if age > ttl_seconds:
                    del self.tasks[task_id]
                    removed += 1

        logger.info(f"Cleaned up {removed} old tasks")
        return removed