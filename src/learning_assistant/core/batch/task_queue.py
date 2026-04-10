"""
Task Queue for Batch Processing.

Provides priority-based task queue with:
- Priority levels (HIGH, NORMAL, LOW)
- Task deduplication
- Queue size management
"""

import heapq
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TaskPriority(Enum):
    """Task priority levels."""

    HIGH = 1
    NORMAL = 5
    LOW = 10


@dataclass(order=True)
class Task:
    """
    Task in the queue.

    Attributes:
        priority: Task priority (lower = higher priority)
        task_id: Unique task identifier
        func: Async function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        created_at: Task creation timestamp
    """

    priority: int
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    args: tuple = field(compare=False, default=())
    kwargs: dict = field(compare=False, default_factory=dict)
    created_at: float = field(compare=False, default_factory=time.time)


class TaskQueue:
    """
    Priority-based task queue.

    Features:
    - Priority-based ordering
    - Task deduplication
    - Size limits
    - Fast lookup by task_id

    Example:
        >>> queue = TaskQueue(max_size=1000)
        >>> queue.push("task1", some_async_func, priority=TaskPriority.HIGH)
        >>> task = queue.pop()
        >>> await task.func(*task.args, **task.kwargs)
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize task queue.

        Args:
            max_size: Maximum queue size
        """
        self.max_size = max_size
        self._heap: list[Task] = []
        self._task_ids: set[str] = set()
        self._total_pushed = 0
        self._total_popped = 0

    def push(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> bool:
        """
        Push a task to the queue.

        Args:
            task_id: Unique task identifier
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority

        Returns:
            True if task was added, False if duplicate or queue full
        """
        # Check if duplicate
        if task_id in self._task_ids:
            return False

        # Check if queue is full
        if len(self._heap) >= self.max_size:
            return False

        # Create task
        task = Task(
            priority=priority.value,
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
        )

        # Add to heap and set
        heapq.heappush(self._heap, task)
        self._task_ids.add(task_id)
        self._total_pushed += 1

        return True

    def pop(self) -> Task | None:
        """
        Pop the highest priority task from the queue.

        Returns:
            Task or None if queue is empty
        """
        if not self._heap:
            return None

        task = heapq.heappop(self._heap)
        self._task_ids.remove(task.task_id)
        self._total_popped += 1

        return task

    def peek(self) -> Task | None:
        """
        Peek at the highest priority task without removing it.

        Returns:
            Task or None if queue is empty
        """
        if not self._heap:
            return None

        return self._heap[0]

    def remove(self, task_id: str) -> bool:
        """
        Remove a task by ID.

        Args:
            task_id: Task ID to remove

        Returns:
            True if task was removed, False if not found
        """
        if task_id not in self._task_ids:
            return False

        # Remove from set
        self._task_ids.remove(task_id)

        # Rebuild heap without the task
        self._heap = [t for t in self._heap if t.task_id != task_id]
        heapq.heapify(self._heap)

        return True

    def clear(self) -> None:
        """Clear all tasks from the queue."""
        self._heap.clear()
        self._task_ids.clear()

    def __len__(self) -> int:
        """Get current queue size."""
        return len(self._heap)

    def __contains__(self, task_id: str) -> bool:
        """Check if task is in the queue."""
        return task_id in self._task_ids

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._heap) == 0

    @property
    def is_full(self) -> bool:
        """Check if queue is full."""
        return len(self._heap) >= self.max_size

    @property
    def stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        return {
            "current_size": len(self._heap),
            "max_size": self.max_size,
            "total_pushed": self._total_pushed,
            "total_popped": self._total_popped,
            "remaining": len(self._heap),
        }