"""
Unit tests for HistoryManager.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from learning_assistant.core.history_manager import HistoryManager, HistoryRecord


class TestHistoryRecord:
    """Test HistoryRecord class."""

    def test_create_record(self) -> None:
        """Test creating a history record."""
        record = HistoryRecord(
            record_id="test-id",
            module="video_summary",
            input="https://example.com/video",
            output="output.md",
            timestamp=datetime.now(),
            metadata={"duration": 600},
        )

        assert record.record_id == "test-id"
        assert record.module == "video_summary"
        assert record.input == "https://example.com/video"
        assert record.output == "output.md"
        assert record.metadata == {"duration": 600}

    def test_to_dict(self) -> None:
        """Test converting record to dictionary."""
        timestamp = datetime.now()
        record = HistoryRecord(
            record_id="test-id",
            module="video_summary",
            input="https://example.com/video",
            output="output.md",
            timestamp=timestamp,
            metadata={"key": "value"},
        )

        data = record.to_dict()

        assert data["record_id"] == "test-id"
        assert data["module"] == "video_summary"
        assert data["input"] == "https://example.com/video"
        assert data["output"] == "output.md"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["metadata"] == {"key": "value"}

    def test_from_dict(self) -> None:
        """Test creating record from dictionary."""
        timestamp = datetime.now()
        data = {
            "record_id": "test-id",
            "module": "video_summary",
            "input": "https://example.com/video",
            "output": "output.md",
            "timestamp": timestamp.isoformat(),
            "metadata": {"key": "value"},
        }

        record = HistoryRecord.from_dict(data)

        assert record.record_id == "test-id"
        assert record.module == "video_summary"
        assert record.input == "https://example.com/video"
        assert record.output == "output.md"
        assert record.timestamp.isoformat() == timestamp.isoformat()
        assert record.metadata == {"key": "value"}

    def test_to_dict_from_dict_roundtrip(self) -> None:
        """Test to_dict and from_dict roundtrip."""
        original = HistoryRecord(
            record_id="test-id",
            module="video_summary",
            input="https://example.com/video",
            output="output.md",
            timestamp=datetime.now(),
            metadata={"key": "value"},
        )

        data = original.to_dict()
        restored = HistoryRecord.from_dict(data)

        assert restored.record_id == original.record_id
        assert restored.module == original.module
        assert restored.input == original.input
        assert restored.output == original.output
        assert restored.timestamp.isoformat() == original.timestamp.isoformat()
        assert restored.metadata == original.metadata


class TestHistoryManager:
    """Test HistoryManager class."""

    def test_init_default_dir(self) -> None:
        """Test initialization with default directory."""
        manager = HistoryManager()

        assert manager.history_dir == Path("data/history")
        assert manager.records == {}
        assert manager._cache == {}

    def test_init_custom_dir(self) -> None:
        """Test initialization with custom directory."""
        manager = HistoryManager(history_dir=Path("custom/history"))

        assert manager.history_dir == Path("custom/history")

    def test_add_record(self) -> None:
        """Test adding a history record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            record_id = manager.add_record(
                module="video_summary",
                input="https://example.com/video",
                output="output.md",
                metadata={"duration": 600},
            )

            assert record_id is not None
            assert len(record_id) == 36  # UUID format

            # Check record was added
            assert "video_summary" in manager.records
            assert len(manager.records["video_summary"]) == 1

            record = manager.records["video_summary"][0]
            assert record.module == "video_summary"
            assert record.input == "https://example.com/video"
            assert record.output == "output.md"

    def test_check_duplicate_found(self) -> None:
        """Test duplicate detection when duplicate exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            # Add a record
            manager.add_record(
                module="video_summary",
                input="https://example.com/video",
                output="output.md",
            )

            # Check duplicate
            is_duplicate = manager.check_duplicate(
                module="video_summary", input="https://example.com/video"
            )

            assert is_duplicate is True

    def test_check_duplicate_not_found(self) -> None:
        """Test duplicate detection when no duplicate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            # Add a record
            manager.add_record(
                module="video_summary",
                input="https://example.com/video1",
                output="output.md",
            )

            # Check different input
            is_duplicate = manager.check_duplicate(
                module="video_summary", input="https://example.com/video2"
            )

            assert is_duplicate is False

    def test_get_record_by_id(self) -> None:
        """Test getting record by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            record_id = manager.add_record(
                module="video_summary",
                input="https://example.com/video",
                output="output.md",
            )

            record = manager.get_record(record_id)

            assert record is not None
            assert record.record_id == record_id
            assert record.input == "https://example.com/video"

    def test_get_record_not_found(self) -> None:
        """Test getting non-existent record."""
        manager = HistoryManager()

        record = manager.get_record("non-existent-id")

        assert record is None

    def test_search_by_keyword(self) -> None:
        """Test searching records by keyword."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            # Add multiple records
            manager.add_record(
                module="video_summary",
                input="https://youtube.com/video1",
                output="Python tutorial",
            )
            manager.add_record(
                module="video_summary",
                input="https://bilibili.com/video2",
                output="Java basics",
            )

            # Search for "python"
            results = manager.search("python")

            assert len(results) == 1
            assert "Python" in results[0].output

    def test_search_no_results(self) -> None:
        """Test searching with no results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            manager.add_record(
                module="video_summary",
                input="https://example.com/video",
                output="output.md",
            )

            results = manager.search("nonexistent")

            assert len(results) == 0

    def test_get_statistics(self) -> None:
        """Test getting statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            # Add multiple records
            manager.add_record(
                module="video_summary",
                input="https://example.com/video1",
                output="output1.md",
            )
            manager.add_record(
                module="video_summary",
                input="https://example.com/video2",
                output="output2.md",
            )
            manager.add_record(
                module="link_learning",
                input="https://example.com/article",
                output="output3.md",
            )

            stats = manager.get_statistics()

            assert stats["total_records"] == 3
            assert stats["by_module"]["video_summary"] == 2
            assert stats["by_module"]["link_learning"] == 1
            assert "video_summary" in stats["modules"]
            assert "link_learning" in stats["modules"]

    def test_cleanup_old_records(self) -> None:
        """Test cleaning up old records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            # Add recent record
            manager.add_record(
                module="video_summary",
                input="https://example.com/recent",
                output="output.md",
            )

            # Add old record manually
            old_record = HistoryRecord(
                record_id="old-id",
                module="video_summary",
                input="https://example.com/old",
                output="output.md",
                timestamp=datetime.now() - timedelta(days=60),
            )
            manager.records["video_summary"].append(old_record)

            # Cleanup old records
            manager.cleanup_old_records(days=30)

            # Check old record was removed
            assert len(manager.records["video_summary"]) == 1
            assert (
                manager.records["video_summary"][0].input
                == "https://example.com/recent"
            )

    def test_save_and_load_history(self) -> None:
        """Test saving and loading history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = HistoryManager(history_dir=Path(tmpdir))

            # Add records
            record_id = manager1.add_record(
                module="video_summary",
                input="https://example.com/video",
                output="output.md",
                metadata={"key": "value"},
            )

            # Create new manager and load
            manager2 = HistoryManager(history_dir=Path(tmpdir))
            manager2.load_history()

            # Check records loaded
            assert "video_summary" in manager2.records
            assert len(manager2.records["video_summary"]) == 1

            record = manager2.records["video_summary"][0]
            assert record.record_id == record_id
            assert record.input == "https://example.com/video"
            assert record.metadata == {"key": "value"}

    def test_load_empty_history(self) -> None:
        """Test loading when history file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))
            manager.load_history()

            assert manager.records == {}


class TestHistoryManagerIntegration:
    """Test HistoryManager integration scenarios."""

    def test_full_workflow(self) -> None:
        """Test full workflow: add, search, get stats, cleanup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            # Add records
            id1 = manager.add_record(
                module="video_summary",
                input="https://youtube.com/python",
                output="Python tutorial summary",
            )
            manager.add_record(
                module="video_summary",
                input="https://youtube.com/java",
                output="Java basics summary",
            )

            # Check duplicates
            assert manager.check_duplicate(
                "video_summary", "https://youtube.com/python"
            )
            assert not manager.check_duplicate(
                "video_summary", "https://youtube.com/new"
            )

            # Search
            results = manager.search("python")
            assert len(results) == 1

            # Get statistics
            stats = manager.get_statistics()
            assert stats["total_records"] == 2

            # Get record by ID
            record = manager.get_record(id1)
            assert record is not None
            assert record.input == "https://youtube.com/python"

    def test_cache_mechanism(self) -> None:
        """Test that cache is used for record lookups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_dir=Path(tmpdir))

            # Add record
            record_id = manager.add_record(
                module="video_summary",
                input="https://example.com/video",
                output="output.md",
            )

            # Get record (should be cached)
            record1 = manager.get_record(record_id)
            assert record1 is not None

            # Get again (should come from cache)
            record2 = manager.get_record(record_id)
            assert record2 is not None
            assert record1 is record2  # Same object reference
