"""
Batch Task Manager for Learning Assistant.

Provides efficient batch processing with:
- Concurrent task execution with controlled parallelism
- Resource-aware scheduling
- Progress tracking and monitoring
- Error handling and retry mechanisms
- Memory-efficient processing
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from loguru import logger

from learning_assistant.core.batch.resource_monitor import ResourceMonitor
from learning_assistant.core.batch.task_queue import TaskPriority, TaskQueue


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """
    Result of task execution.

    Attributes:
        task_id: Task identifier
        status: Execution status
        result: Task result (if successful)
        error: Error message (if failed)
        duration: Execution duration in seconds
        memory_used_mb: Memory used during execution
    """

    task_id: str
    status: TaskStatus
    result: Any = None
    error: str | None = None
    duration: float = 0.0
    memory_used_mb: float = 0.0


@dataclass
class BatchStatistics:
    """
    Batch processing statistics.

    Attributes:
        total_tasks: Total number of tasks
        completed: Number of completed tasks
        failed: Number of failed tasks
        cancelled: Number of cancelled tasks
        total_duration: Total processing duration
        average_task_duration: Average task duration
        peak_memory_mb: Peak memory usage
        throughput: Tasks per second
    """

    total_tasks: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    total_duration: float = 0.0
    average_task_duration: float = 0.0
    peak_memory_mb: float = 0.0
    throughput: float = 0.0


class BatchTaskManager:
    """
    Batch task manager for efficient concurrent processing.

    Features:
    - Controlled concurrency with resource awareness
    - Priority-based scheduling
    - Progress tracking
    - Error handling and retries
    - Memory-efficient processing

    Example:
        >>> manager = BatchTaskManager(max_workers=4, memory_limit_mb=500)
        >>>
        >>> # Add tasks
        >>> for url in video_urls:
        ...     await manager.add_task(
        ...         task_id=f"video_{i}",
        ...         func=summarize_video,
        ...         args=(url,),
        ...         priority=TaskPriority.NORMAL
        ...     )
        >>>
        >>> # Process all tasks
        >>> results = await manager.process_all()
        >>>
        >>> # Check statistics
        >>> stats = manager.get_statistics()
    """

    def __init__(
        self,
        max_workers: int = 4,
        memory_limit_mb: float | None = 500,
        cpu_limit_percent: float | None = 80,
        retry_failed: bool = False,
        max_retries: int = 2,
    ):
        """
        Initialize batch task manager.

        Args:
            max_workers: Maximum concurrent workers
            memory_limit_mb: Memory limit in MB
            cpu_limit_percent: CPU limit percentage
            retry_failed: Whether to retry failed tasks
            max_retries: Maximum retry attempts
        """
        self.max_workers = max_workers
        self.retry_failed = retry_failed
        self.max_retries = max_retries

        # Initialize components
        self.task_queue = TaskQueue()
        self.resource_monitor = ResourceMonitor(
            memory_limit_mb=memory_limit_mb,
            cpu_limit_percent=cpu_limit_percent,
        )

        # Task tracking
        self._tasks: dict[str, TaskResult] = {}
        self._active_workers = 0
        self._is_processing = False
        self._start_time: float | None = None
        self._end_time: float | None = None

        # Callbacks
        self._progress_callback: Callable | None = None
        self._error_callback: Callable | None = None

        logger.info(
            f"BatchTaskManager initialized: max_workers={max_workers}, "
            f"memory_limit={memory_limit_mb}MB"
        )

    async def add_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> bool:
        """
        Add a task to the batch queue.

        Args:
            task_id: Unique task identifier
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority

        Returns:
            True if task was added, False if duplicate or queue full
        """
        success = self.task_queue.push(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
        )

        if success:
            # Initialize task result
            self._tasks[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.PENDING,
            )
            logger.debug(f"Task added: {task_id}")

        return success

    async def process_all(self) -> dict[str, TaskResult]:
        """
        Process all tasks in the queue.

        Returns:
            Dictionary of task_id -> TaskResult
        """
        if self._is_processing:
            raise RuntimeError("Batch processing already in progress")

        self._is_processing = True
        self._start_time = time.time()

        logger.info(f"Starting batch processing: {len(self.task_queue)} tasks")

        try:
            # Create worker tasks
            workers = [
                asyncio.create_task(self._worker(worker_id=i))
                for i in range(self.max_workers)
            ]

            # Wait for all workers to complete
            await asyncio.gather(*workers)

            self._end_time = time.time()

            logger.success(
                f"Batch processing completed: "
                f"{self._count_by_status(TaskStatus.COMPLETED)}/{len(self._tasks)} tasks"
            )

        finally:
            self._is_processing = False

        return self._tasks

    async def _worker(self, worker_id: int) -> None:
        """
        Worker coroutine that processes tasks from the queue.

        Args:
            worker_id: Worker identifier
        """
        logger.debug(f"Worker {worker_id} started")

        while True:
            # Get next task
            task = self.task_queue.pop()

            if task is None:
                # Queue is empty
                break

            # Check resources before processing
            if not self.resource_monitor.check_memory_available(required_mb=100):
                logger.warning(
                    f"Worker {worker_id}: Low memory, "
                    f"waiting before processing task {task.task_id}"
                )
                await asyncio.sleep(1)

            # Execute task
            await self._execute_task(task, worker_id)

            # Update progress
            if self._progress_callback:
                await self._call_progress_callback()

        logger.debug(f"Worker {worker_id} finished")

    async def _execute_task(self, task: Any, worker_id: int) -> None:
        """
        Execute a single task.

        Args:
            task: Task to execute
            worker_id: Worker identifier
        """
        task_id = task.task_id
        self._active_workers += 1

        # Update status
        self._tasks[task_id].status = TaskStatus.RUNNING

        logger.debug(f"Worker {worker_id} executing task: {task_id}")

        # Record start memory
        start_memory = self.resource_monitor.get_current_usage().memory_mb

        try:
            # Execute task
            start_time = time.time()

            result = await task.func(*task.args, **task.kwargs)

            duration = time.time() - start_time
            end_memory = self.resource_monitor.get_current_usage().memory_mb

            # Store result
            self._tasks[task_id].status = TaskStatus.COMPLETED
            self._tasks[task_id].result = result
            self._tasks[task_id].duration = duration
            self._tasks[task_id].memory_used_mb = end_memory - start_memory

            logger.debug(
                f"Task {task_id} completed in {duration:.2f}s, "
                f"memory: {end_memory - start_memory:.1f}MB"
            )

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")

            # Update result
            self._tasks[task_id].status = TaskStatus.FAILED
            self._tasks[task_id].error = str(e)

            # Retry if enabled
            if self.retry_failed:
                retry_count = getattr(task, "retry_count", 0)
                if retry_count < self.max_retries:
                    logger.info(f"Retrying task {task_id} (attempt {retry_count + 1})")
                    # Re-add to queue with retry count
                    # Note: In production, you'd track retry count properly
                    await self.add_task(
                        task_id=f"{task_id}_retry_{retry_count + 1}",
                        func=task.func,
                        args=task.args,
                        kwargs=task.kwargs,
                        priority=TaskPriority.HIGH,
                    )

            # Call error callback
            if self._error_callback:
                await self._error_callback(task_id, e)

        finally:
            self._active_workers -= 1

    async def _call_progress_callback(self) -> None:
        """Call progress callback with current statistics."""
        if self._progress_callback:
            stats = self.get_statistics()
            try:
                if asyncio.iscoroutinefunction(self._progress_callback):
                    await self._progress_callback(stats)
                else:
                    self._progress_callback(stats)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def set_progress_callback(self, callback: Callable) -> None:
        """
        Set progress callback.

        Args:
            callback: Async or sync function(stats)
        """
        self._progress_callback = callback

    def set_error_callback(self, callback: Callable) -> None:
        """
        Set error callback.

        Args:
            callback: Async or sync function(task_id, error)
        """
        self._error_callback = callback

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if task was cancelled
        """
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.CANCELLED
            return self.task_queue.remove(task_id)
        return False

    def get_statistics(self) -> BatchStatistics:
        """
        Get batch processing statistics.

        Returns:
            BatchStatistics snapshot
        """
        completed = self._count_by_status(TaskStatus.COMPLETED)
        failed = self._count_by_status(TaskStatus.FAILED)
        cancelled = self._count_by_status(TaskStatus.CANCELLED)

        # Calculate durations
        total_duration = 0.0
        if self._start_time:
            end = self._end_time or time.time()
            total_duration = end - self._start_time

        # Calculate average task duration
        completed_tasks = [
            t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED
        ]
        avg_duration = (
            sum(t.duration for t in completed_tasks) / len(completed_tasks)
            if completed_tasks
            else 0.0
        )

        # Get peak memory
        peak = self.resource_monitor.get_peak_usage()
        peak_memory = peak.memory_mb if peak else 0.0

        # Calculate throughput
        throughput = completed / total_duration if total_duration > 0 else 0.0

        return BatchStatistics(
            total_tasks=len(self._tasks),
            completed=completed,
            failed=failed,
            cancelled=cancelled,
            total_duration=total_duration,
            average_task_duration=avg_duration,
            peak_memory_mb=peak_memory,
            throughput=throughput,
        )

    def _count_by_status(self, status: TaskStatus) -> int:
        """Count tasks by status."""
        return sum(1 for t in self._tasks.values() if t.status == status)

    def clear(self) -> None:
        """Clear all tasks and reset state."""
        self.task_queue.clear()
        self._tasks.clear()
        self.resource_monitor.clear_history()
        self._start_time = None
        self._end_time = None
        logger.info("BatchTaskManager cleared")

    @property
    def is_processing(self) -> bool:
        """Check if processing is in progress."""
        return self._is_processing

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return len(self.task_queue)