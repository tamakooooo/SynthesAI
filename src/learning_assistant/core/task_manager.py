"""
Task Manager for Learning Assistant.

This module handles asynchronous task state management and error recovery.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger


class TaskStatus(Enum):
    """
    Task status enum.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    FAILED = "failed"


@dataclass
class TaskState:
    """
    Task state structure.
    """

    task_id: str
    module: str
    status: TaskStatus
    progress: float  # 0.0 to 100.0
    current_step: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert task state to dictionary."""
        return {
            "task_id": self.task_id,
            "module": self.module,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskState":
        """Create task state from dictionary."""
        return cls(
            task_id=data["task_id"],
            module=data["module"],
            status=TaskStatus(data["status"]),
            progress=data["progress"],
            current_step=data["current_step"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class TaskManager:
    """
    Task Manager for Learning Assistant.

    Handles:
    - Asynchronous task state management
    - Task persistence
    - Error recovery mechanism
    - Progress tracking
    """

    def __init__(self, task_dir: Path | None = None) -> None:
        """
        Initialize TaskManager.

        Args:
            task_dir: Task directory path (default: data/tasks/)
        """
        self.task_dir = task_dir or Path("data/tasks")
        self.tasks: dict[str, TaskState] = {}
        logger.info(f"TaskManager initialized with task_dir: {self.task_dir}")

    def create_task(self, module: str, metadata: dict[str, Any] | None = None) -> str:
        """
        Create a new task.

        Args:
            module: Module name
            metadata: Task metadata

        Returns:
            Task ID
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create task state
        now = datetime.now()
        task = TaskState(
            task_id=task_id,
            module=module,
            status=TaskStatus.PENDING,
            progress=0.0,
            current_step="initialized",
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        # Add to tasks dict
        self.tasks[task_id] = task

        logger.info(f"Created task: task_id={task_id}, module={module}")

        # Auto-save after creation
        self.save_tasks()

        return task_id

    def update_progress(
        self,
        task_id: str,
        step: str,
        progress: float,
    ) -> None:
        """
        Update task progress.

        Args:
            task_id: Task ID
            step: Current step name
            progress: Progress percentage (0.0 to 100.0)
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return

        # Update progress
        task.current_step = step
        task.progress = min(100.0, max(0.0, progress))  # Clamp to [0, 100]
        task.updated_at = datetime.now()

        # Auto-update status to RUNNING if pending
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.RUNNING

        logger.debug(f"Updated task {task_id}: step={step}, progress={progress:.1f}%")

        # Auto-save progress
        self.save_tasks()

    def mark_completed(self, task_id: str) -> None:
        """
        Mark task as completed.

        Args:
            task_id: Task ID
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return

        task.status = TaskStatus.COMPLETED
        task.progress = 100.0
        task.updated_at = datetime.now()

        logger.info(f"Task completed: {task_id}")
        self.save_tasks()

    def mark_interrupted(self, task_id: str) -> None:
        """
        Mark task as interrupted.

        Args:
            task_id: Task ID
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return

        task.status = TaskStatus.INTERRUPTED
        task.updated_at = datetime.now()

        logger.info(f"Task interrupted: {task_id}")
        self.save_tasks()

    def mark_failed(self, task_id: str, error: str) -> None:
        """
        Mark task as failed with error message.

        Args:
            task_id: Task ID
            error: Error message
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return

        task.status = TaskStatus.FAILED
        task.error = error
        task.updated_at = datetime.now()

        logger.error(f"Task failed: {task_id}, error={error}")
        self.save_tasks()

    def resume_task(self, task_id: str) -> None:
        """
        Resume an interrupted task.

        Args:
            task_id: Task ID
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return

        if task.status != TaskStatus.INTERRUPTED:
            logger.warning(f"Task {task_id} is not interrupted (status: {task.status})")
            return

        # Reset status to pending
        task.status = TaskStatus.PENDING
        task.updated_at = datetime.now()

        logger.info(f"Resuming task: {task_id}")
        self.save_tasks()

    def get_task(self, task_id: str) -> TaskState | None:
        """
        Get task state by ID.

        Args:
            task_id: Task ID

        Returns:
            Task state or None if not found
        """
        return self.tasks.get(task_id)

    def get_active_tasks(self) -> list[TaskState]:
        """
        Get all active tasks (running or interrupted).

        Returns:
            List of active task states
        """
        active_tasks = [
            task
            for task in self.tasks.values()
            if task.status
            in (TaskStatus.RUNNING, TaskStatus.INTERRUPTED, TaskStatus.PENDING)
        ]

        logger.debug(f"Found {len(active_tasks)} active tasks")
        return active_tasks

    def get_tasks_by_module(self, module: str) -> list[TaskState]:
        """
        Get all tasks for a module.

        Args:
            module: Module name

        Returns:
            List of task states
        """
        return [task for task in self.tasks.values() if task.module == module]

    def cleanup_completed_tasks(self, keep_days: int = 7) -> None:
        """
        Cleanup completed tasks older than specified days.

        Args:
            keep_days: Number of days to keep completed tasks
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=keep_days)
        removed_count = 0

        # Filter out old completed/failed tasks
        tasks_to_keep = {}
        for task_id, task in self.tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                if task.updated_at >= cutoff_date:
                    tasks_to_keep[task_id] = task
                else:
                    removed_count += 1
            else:
                tasks_to_keep[task_id] = task

        self.tasks = tasks_to_keep

        logger.info(
            f"Cleaned up {removed_count} completed tasks older than {keep_days} days"
        )

        if removed_count > 0:
            self.save_tasks()

    def load_tasks(self) -> None:
        """
        Load tasks from disk.
        """
        tasks_file = self.task_dir / "tasks.json"

        if not tasks_file.exists():
            logger.info("Tasks file does not exist, starting fresh")
            return

        try:
            with open(tasks_file, encoding="utf-8") as f:
                data = json.load(f)

            # Clear existing tasks
            self.tasks.clear()

            # Load tasks from JSON
            for task_data in data:
                task = TaskState.from_dict(task_data)
                self.tasks[task.task_id] = task

            logger.info(f"Loaded {len(self.tasks)} tasks from disk")

        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")

    def save_tasks(self) -> None:
        """
        Save tasks to disk.
        """
        # Ensure directory exists
        self.task_dir.mkdir(parents=True, exist_ok=True)

        tasks_file = self.task_dir / "tasks.json"

        try:
            # Convert tasks to list of dicts
            data = [task.to_dict() for task in self.tasks.values()]

            # Write to file
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(self.tasks)} tasks to disk")

        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
