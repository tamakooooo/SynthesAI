"""
Tests for Task Queue.
"""

import asyncio

import pytest

from learning_assistant.core.batch.task_queue import Task, TaskPriority, TaskQueue


class TestTaskQueue:
    """Test TaskQueue functionality."""

    def test_init(self):
        """Test queue initialization."""
        queue = TaskQueue(max_size=100)
        assert queue.max_size == 100
        assert len(queue) == 0
        assert queue.is_empty

    def test_push_task(self):
        """Test pushing a task to queue."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        success = queue.push(
            task_id="task1",
            func=dummy_func,
            priority=TaskPriority.NORMAL,
        )

        assert success is True
        assert len(queue) == 1
        assert "task1" in queue

    def test_push_duplicate_task(self):
        """Test pushing duplicate task."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        # Push first time
        success1 = queue.push("task1", dummy_func)
        assert success1 is True

        # Push duplicate
        success2 = queue.push("task1", dummy_func)
        assert success2 is False

        assert len(queue) == 1

    def test_push_to_full_queue(self):
        """Test pushing to full queue."""
        queue = TaskQueue(max_size=2)

        async def dummy_func():
            pass

        # Fill queue
        queue.push("task1", dummy_func)
        queue.push("task2", dummy_func)

        # Try to push to full queue
        success = queue.push("task3", dummy_func)
        assert success is False
        assert len(queue) == 2

    def test_pop_task(self):
        """Test popping a task from queue."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        # Push task
        queue.push("task1", dummy_func, args=(1, 2), kwargs={"key": "value"})

        # Pop task
        task = queue.pop()

        assert task is not None
        assert task.task_id == "task1"
        assert task.args == (1, 2)
        assert task.kwargs == {"key": "value"}
        assert len(queue) == 0

    def test_pop_from_empty_queue(self):
        """Test popping from empty queue."""
        queue = TaskQueue()

        task = queue.pop()

        assert task is None

    def test_priority_ordering(self):
        """Test task priority ordering."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        # Push tasks with different priorities
        queue.push("low", dummy_func, priority=TaskPriority.LOW)
        queue.push("high", dummy_func, priority=TaskPriority.HIGH)
        queue.push("normal", dummy_func, priority=TaskPriority.NORMAL)

        # Pop should return HIGH priority first
        task1 = queue.pop()
        assert task1.task_id == "high"
        assert task1.priority == TaskPriority.HIGH.value

        task2 = queue.pop()
        assert task2.task_id == "normal"
        assert task2.priority == TaskPriority.NORMAL.value

        task3 = queue.pop()
        assert task3.task_id == "low"
        assert task3.priority == TaskPriority.LOW.value

    def test_peek_task(self):
        """Test peeking at a task."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        queue.push("task1", dummy_func)

        # Peek should not remove task
        task = queue.peek()
        assert task is not None
        assert task.task_id == "task1"
        assert len(queue) == 1

    def test_peek_empty_queue(self):
        """Test peeking at empty queue."""
        queue = TaskQueue()

        task = queue.peek()
        assert task is None

    def test_remove_task(self):
        """Test removing a task by ID."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        queue.push("task1", dummy_func)
        queue.push("task2", dummy_func)

        # Remove task1
        success = queue.remove("task1")
        assert success is True
        assert len(queue) == 1
        assert "task1" not in queue
        assert "task2" in queue

    def test_remove_nonexistent_task(self):
        """Test removing a nonexistent task."""
        queue = TaskQueue()

        success = queue.remove("nonexistent")
        assert success is False

    def test_clear_queue(self):
        """Test clearing the queue."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        queue.push("task1", dummy_func)
        queue.push("task2", dummy_func)

        queue.clear()

        assert len(queue) == 0
        assert queue.is_empty

    def test_stats(self):
        """Test queue statistics."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        # Push and pop some tasks
        queue.push("task1", dummy_func)
        queue.push("task2", dummy_func)
        queue.pop()

        stats = queue.stats

        assert stats["current_size"] == 1
        assert stats["total_pushed"] == 2
        assert stats["total_popped"] == 1
        assert stats["remaining"] == 1

    def test_is_full(self):
        """Test is_full property."""
        queue = TaskQueue(max_size=2)

        async def dummy_func():
            pass

        assert queue.is_full is False

        queue.push("task1", dummy_func)
        queue.push("task2", dummy_func)

        assert queue.is_full is True

    def test_task_ordering_with_same_priority(self):
        """Test FIFO ordering for tasks with same priority."""
        queue = TaskQueue()

        async def dummy_func():
            pass

        # Push tasks with same priority
        queue.push("task1", dummy_func, priority=TaskPriority.NORMAL)
        queue.push("task2", dummy_func, priority=TaskPriority.NORMAL)
        queue.push("task3", dummy_func, priority=TaskPriority.NORMAL)

        # Should pop in FIFO order
        assert queue.pop().task_id == "task1"
        assert queue.pop().task_id == "task2"
        assert queue.pop().task_id == "task3"


class TestTask:
    """Test Task dataclass."""

    def test_task_creation(self):
        """Test task creation."""
        async def dummy_func():
            pass

        task = Task(
            priority=5,
            task_id="test",
            func=dummy_func,
            args=(1, 2),
            kwargs={"key": "value"},
        )

        assert task.priority == 5
        assert task.task_id == "test"
        assert task.func == dummy_func
        assert task.args == (1, 2)
        assert task.kwargs == {"key": "value"}
        assert task.created_at > 0

    def test_task_comparison(self):
        """Test task comparison by priority."""
        async def dummy_func():
            pass

        task1 = Task(priority=1, task_id="high", func=dummy_func)
        task2 = Task(priority=5, task_id="normal", func=dummy_func)
        task3 = Task(priority=10, task_id="low", func=dummy_func)

        assert task1 < task2
        assert task2 < task3
        assert task1 < task3