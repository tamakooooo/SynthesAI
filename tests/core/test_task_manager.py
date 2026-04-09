"""
Unit tests for TaskManager.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from learning_assistant.core.task_manager import TaskManager, TaskState, TaskStatus


class TestTaskState:
    """Test TaskState class."""

    def test_create_task_state(self) -> None:
        """Test creating a task state."""
        now = datetime.now()
        task = TaskState(
            task_id="test-id",
            module="video_summary",
            status=TaskStatus.PENDING,
            progress=0.0,
            current_step="initialized",
            created_at=now,
            updated_at=now,
        )

        assert task.task_id == "test-id"
        assert task.module == "video_summary"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0
        assert task.current_step == "initialized"
        assert task.error is None
        assert task.metadata == {}

    def test_to_dict(self) -> None:
        """Test converting task state to dictionary."""
        now = datetime.now()
        task = TaskState(
            task_id="test-id",
            module="video_summary",
            status=TaskStatus.RUNNING,
            progress=50.0,
            current_step="downloading",
            created_at=now,
            updated_at=now,
            error=None,
            metadata={"key": "value"},
        )

        data = task.to_dict()

        assert data["task_id"] == "test-id"
        assert data["module"] == "video_summary"
        assert data["status"] == "running"
        assert data["progress"] == 50.0
        assert data["current_step"] == "downloading"
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        assert data["error"] is None
        assert data["metadata"] == {"key": "value"}

    def test_from_dict(self) -> None:
        """Test creating task state from dictionary."""
        now = datetime.now()
        data = {
            "task_id": "test-id",
            "module": "video_summary",
            "status": "failed",
            "progress": 30.0,
            "current_step": "transcribing",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "error": "Network error",
            "metadata": {"key": "value"},
        }

        task = TaskState.from_dict(data)

        assert task.task_id == "test-id"
        assert task.module == "video_summary"
        assert task.status == TaskStatus.FAILED
        assert task.progress == 30.0
        assert task.current_step == "transcribing"
        assert task.created_at.isoformat() == now.isoformat()
        assert task.updated_at.isoformat() == now.isoformat()
        assert task.error == "Network error"
        assert task.metadata == {"key": "value"}

    def test_to_dict_from_dict_roundtrip(self) -> None:
        """Test to_dict and from_dict roundtrip."""
        now = datetime.now()
        original = TaskState(
            task_id="test-id",
            module="video_summary",
            status=TaskStatus.COMPLETED,
            progress=100.0,
            current_step="finished",
            created_at=now,
            updated_at=now,
            error=None,
            metadata={"duration": 600},
        )

        data = original.to_dict()
        restored = TaskState.from_dict(data)

        assert restored.task_id == original.task_id
        assert restored.module == original.module
        assert restored.status == original.status
        assert restored.progress == original.progress
        assert restored.current_step == original.current_step
        assert restored.created_at.isoformat() == original.created_at.isoformat()
        assert restored.updated_at.isoformat() == original.updated_at.isoformat()
        assert restored.error == original.error
        assert restored.metadata == original.metadata


class TestTaskManager:
    """Test TaskManager class."""

    def test_init_default_dir(self) -> None:
        """Test initialization with default directory."""
        manager = TaskManager()

        assert manager.task_dir == Path("data/tasks")
        assert manager.tasks == {}

    def test_init_custom_dir(self) -> None:
        """Test initialization with custom directory."""
        manager = TaskManager(task_dir=Path("custom/tasks"))

        assert manager.task_dir == Path("custom/tasks")

    def test_create_task(self) -> None:
        """Test creating a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(
                module="video_summary", metadata={"url": "https://example.com/video"}
            )

            assert task_id is not None
            assert len(task_id) == 36  # UUID format

            # Check task was created
            assert task_id in manager.tasks

            task = manager.tasks[task_id]
            assert task.module == "video_summary"
            assert task.status == TaskStatus.PENDING
            assert task.progress == 0.0
            assert task.metadata == {"url": "https://example.com/video"}

    def test_update_progress(self) -> None:
        """Test updating task progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")

            # Update progress
            manager.update_progress(task_id, step="downloading", progress=30.0)

            task = manager.get_task(task_id)
            assert task is not None
            assert task.current_step == "downloading"
            assert task.progress == 30.0
            assert task.status == TaskStatus.RUNNING  # Auto-updated to RUNNING

    def test_update_progress_clamp_values(self) -> None:
        """Test that progress is clamped to [0, 100]."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")

            # Test negative value
            manager.update_progress(task_id, step="test", progress=-10.0)
            task = manager.get_task(task_id)
            assert task is not None
            assert task.progress == 0.0

            # Test value > 100
            manager.update_progress(task_id, step="test", progress=150.0)
            task = manager.get_task(task_id)
            assert task is not None
            assert task.progress == 100.0

    def test_mark_completed(self) -> None:
        """Test marking task as completed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")
            manager.mark_completed(task_id)

            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.COMPLETED
            assert task.progress == 100.0

    def test_mark_interrupted(self) -> None:
        """Test marking task as interrupted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")
            manager.update_progress(task_id, step="processing", progress=50.0)
            manager.mark_interrupted(task_id)

            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.INTERRUPTED
            assert task.progress == 50.0  # Progress preserved

    def test_mark_failed(self) -> None:
        """Test marking task as failed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")
            manager.mark_failed(task_id, error="Network error")

            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.FAILED
            assert task.error == "Network error"

    def test_resume_task(self) -> None:
        """Test resuming an interrupted task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")
            manager.mark_interrupted(task_id)
            manager.resume_task(task_id)

            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.PENDING

    def test_resume_non_interrupted_task(self) -> None:
        """Test resuming a non-interrupted task (should fail)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")
            # Don't mark as interrupted
            manager.resume_task(task_id)

            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.PENDING  # Still pending, not changed

    def test_get_task(self) -> None:
        """Test getting task by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            task_id = manager.create_task(module="video_summary")

            task = manager.get_task(task_id)

            assert task is not None
            assert task.task_id == task_id

    def test_get_task_not_found(self) -> None:
        """Test getting non-existent task."""
        manager = TaskManager()

        task = manager.get_task("non-existent-id")

        assert task is None

    def test_get_active_tasks(self) -> None:
        """Test getting active tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            # Create tasks with different statuses
            id1 = manager.create_task(module="video_summary")  # PENDING
            id2 = manager.create_task(module="video_summary")
            manager.update_progress(id2, step="running", progress=50.0)  # RUNNING

            id3 = manager.create_task(module="video_summary")
            manager.mark_completed(id3)  # COMPLETED

            id4 = manager.create_task(module="video_summary")
            manager.mark_interrupted(id4)  # INTERRUPTED

            active_tasks = manager.get_active_tasks()

            # Should include PENDING, RUNNING, INTERRUPTED
            assert len(active_tasks) == 3
            active_ids = {task.task_id for task in active_tasks}
            assert id1 in active_ids
            assert id2 in active_ids
            assert id4 in active_ids
            assert id3 not in active_ids

    def test_get_tasks_by_module(self) -> None:
        """Test getting tasks by module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            # Create tasks for different modules
            id1 = manager.create_task(module="video_summary")
            id2 = manager.create_task(module="video_summary")
            id3 = manager.create_task(module="link_learning")

            video_tasks = manager.get_tasks_by_module("video_summary")

            assert len(video_tasks) == 2
            task_ids = {task.task_id for task in video_tasks}
            assert id1 in task_ids
            assert id2 in task_ids
            assert id3 not in task_ids

    def test_cleanup_completed_tasks(self) -> None:
        """Test cleaning up completed tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            # Create tasks
            id1 = manager.create_task(module="video_summary")
            manager.mark_completed(id1)

            # Manually add old completed task
            old_task = TaskState(
                task_id="old-task-id",
                module="video_summary",
                status=TaskStatus.COMPLETED,
                progress=100.0,
                current_step="finished",
                created_at=datetime.now() - timedelta(days=10),
                updated_at=datetime.now() - timedelta(days=10),
            )
            manager.tasks["old-task-id"] = old_task

            # Cleanup old tasks (keep 7 days)
            manager.cleanup_completed_tasks(keep_days=7)

            # Old task should be removed
            assert "old-task-id" not in manager.tasks
            assert id1 in manager.tasks

    def test_save_and_load_tasks(self) -> None:
        """Test saving and loading tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = TaskManager(task_dir=Path(tmpdir))

            # Create tasks
            task_id = manager1.create_task(
                module="video_summary", metadata={"url": "https://example.com/video"}
            )
            manager1.update_progress(task_id, step="downloading", progress=30.0)

            # Create new manager and load
            manager2 = TaskManager(task_dir=Path(tmpdir))
            manager2.load_tasks()

            # Check tasks loaded
            assert task_id in manager2.tasks

            task = manager2.tasks[task_id]
            assert task.module == "video_summary"
            assert task.progress == 30.0
            assert task.current_step == "downloading"
            assert task.metadata == {"url": "https://example.com/video"}

    def test_load_empty_tasks(self) -> None:
        """Test loading when tasks file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))
            manager.load_tasks()

            assert manager.tasks == {}


class TestTaskManagerIntegration:
    """Test TaskManager integration scenarios."""

    def test_full_workflow(self) -> None:
        """Test full workflow: create, update, complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            # Create task
            task_id = manager.create_task(
                module="video_summary", metadata={"url": "https://example.com/video"}
            )

            # Update progress
            manager.update_progress(task_id, step="downloading", progress=30.0)
            manager.update_progress(task_id, step="transcribing", progress=60.0)
            manager.update_progress(task_id, step="summarizing", progress=90.0)

            # Complete task
            manager.mark_completed(task_id)

            # Verify final state
            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.COMPLETED
            assert task.progress == 100.0

            # Get statistics
            active = manager.get_active_tasks()
            assert len(active) == 0  # No active tasks after completion

    def test_error_recovery_workflow(self) -> None:
        """Test error recovery: create, fail, resume."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            # Create task
            task_id = manager.create_task(module="video_summary")

            # Update progress
            manager.update_progress(task_id, step="downloading", progress=50.0)

            # Simulate failure
            manager.mark_failed(task_id, error="Network error")

            # Check failed
            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.FAILED
            assert task.error == "Network error"

    def test_interrupt_resume_workflow(self) -> None:
        """Test interrupt and resume workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(task_dir=Path(tmpdir))

            # Create and start task
            task_id = manager.create_task(module="video_summary")
            manager.update_progress(task_id, step="processing", progress=50.0)

            # Interrupt
            manager.mark_interrupted(task_id)

            # Check interrupted
            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.INTERRUPTED

            # Resume
            manager.resume_task(task_id)
            task = manager.get_task(task_id)
            assert task is not None
            assert task.status == TaskStatus.PENDING

            # Check it's in active tasks
            active = manager.get_active_tasks()
            assert len(active) == 1
