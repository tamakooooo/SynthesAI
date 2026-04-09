"""
History Manager for Learning Assistant.

This module handles learning history persistence and management.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger


class HistoryRecord:
    """
    History record structure.
    """

    def __init__(
        self,
        record_id: str,
        module: str,
        input: str,
        output: str,
        timestamp: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.record_id = record_id
        self.module = module
        self.input = input
        self.output = output
        self.timestamp = timestamp
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "record_id": self.record_id,
            "module": self.module,
            "input": self.input,
            "output": self.output,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryRecord":
        """Create record from dictionary."""
        return cls(
            record_id=data["record_id"],
            module=data["module"],
            input=data["input"],
            output=data["output"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class HistoryManager:
    """
    History Manager for Learning Assistant.

    Handles:
    - Learning history persistence
    - Duplicate detection
    - Search and retrieval
    - Learning statistics
    """

    def __init__(self, history_dir: Path | None = None) -> None:
        """
        Initialize HistoryManager.

        Args:
            history_dir: History directory path (default: data/history/)
        """
        self.history_dir = history_dir or Path("data/history")
        self.records: dict[str, list[HistoryRecord]] = {}
        self._cache: dict[str, HistoryRecord] = {}  # Cache for fast lookup
        logger.info(f"HistoryManager initialized with history_dir: {self.history_dir}")

    def add_record(
        self,
        module: str,
        input: str,
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add a history record.

        Args:
            module: Module name
            input: Input data (URL, file path, etc.)
            output: Output data (file path, summary, etc.)
            metadata: Additional metadata

        Returns:
            Record ID
        """
        # Generate unique record ID
        record_id = str(uuid.uuid4())

        # Create record
        record = HistoryRecord(
            record_id=record_id,
            module=module,
            input=input,
            output=output,
            timestamp=datetime.now(),
            metadata=metadata,
        )

        # Add to records dict
        if module not in self.records:
            self.records[module] = []
        self.records[module].append(record)

        # Add to cache
        self._cache[record_id] = record

        logger.info(
            f"Added history record: module={module}, record_id={record_id}, input={input}"
        )

        # Auto-save after adding
        self.save_history()

        return record_id

    def check_duplicate(self, module: str, input: str) -> bool:
        """
        Check if input has been processed before.

        Args:
            module: Module name
            input: Input data

        Returns:
            True if duplicate found, False otherwise
        """
        if module not in self.records:
            return False

        # Check if input exists in module records
        for record in self.records[module]:
            if record.input == input:
                logger.debug(f"Duplicate found: module={module}, input={input}")
                return True

        return False

    def get_record(self, record_id: str) -> HistoryRecord | None:
        """
        Get record by ID.

        Args:
            record_id: Record ID

        Returns:
            HistoryRecord or None
        """
        # Check cache first
        if record_id in self._cache:
            return self._cache[record_id]

        # Search in records
        for module_records in self.records.values():
            for record in module_records:
                if record.record_id == record_id:
                    self._cache[record_id] = record  # Cache for future lookups
                    return record

        return None

    def search(self, keyword: str) -> list[HistoryRecord]:
        """
        Search history records by keyword.

        Args:
            keyword: Search keyword

        Returns:
            List of matching records
        """
        results = []
        keyword_lower = keyword.lower()

        for module_records in self.records.values():
            for record in module_records:
                # Search in input, output, and metadata
                if (
                    keyword_lower in record.input.lower()
                    or keyword_lower in record.output.lower()
                    or any(
                        keyword_lower in str(v).lower()
                        for v in record.metadata.values()
                    )
                ):
                    results.append(record)

        logger.info(f"Search for '{keyword}' found {len(results)} results")
        return results

    def get_statistics(self) -> dict[str, Any]:
        """
        Get learning statistics.

        Returns:
            Statistics dict (total records, by module, etc.)
        """
        total_records = sum(len(records) for records in self.records.values())

        # Count by module
        by_module = {module: len(records) for module, records in self.records.items()}

        # Get recent records (last 7 days)
        recent_count = 0
        seven_days_ago = datetime.now() - timedelta(days=7)
        for module_records in self.records.values():
            for record in module_records:
                if record.timestamp >= seven_days_ago:
                    recent_count += 1

        return {
            "total_records": total_records,
            "by_module": by_module,
            "recent_records_7days": recent_count,
            "modules": list(self.records.keys()),
        }

    def cleanup_old_records(self, days: int = 30) -> None:
        """
        Cleanup records older than specified days.

        Args:
            days: Number of days to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0

        for module in list(self.records.keys()):
            # Filter out old records
            original_count = len(self.records[module])
            self.records[module] = [
                record
                for record in self.records[module]
                if record.timestamp >= cutoff_date
            ]
            removed_count += original_count - len(self.records[module])

            # Remove empty module entries
            if not self.records[module]:
                del self.records[module]

        logger.info(f"Cleaned up {removed_count} old records (older than {days} days)")

        # Save after cleanup
        if removed_count > 0:
            self.save_history()

    def load_history(self) -> None:
        """
        Load history from disk.
        """
        history_file = self.history_dir / "history.json"

        if not history_file.exists():
            logger.info("History file does not exist, starting fresh")
            return

        try:
            with open(history_file, encoding="utf-8") as f:
                data = json.load(f)

            # Clear existing records
            self.records.clear()
            self._cache.clear()

            # Load records from JSON
            for module, records_data in data.items():
                self.records[module] = [
                    HistoryRecord.from_dict(record_data) for record_data in records_data
                ]

            logger.info(
                f"Loaded {sum(len(r) for r in self.records.values())} history records from disk"
            )

        except Exception as e:
            logger.error(f"Failed to load history: {e}")

    def save_history(self) -> None:
        """
        Save history to disk.
        """
        # Ensure directory exists
        self.history_dir.mkdir(parents=True, exist_ok=True)

        history_file = self.history_dir / "history.json"

        try:
            # Convert records to dict
            data = {
                module: [record.to_dict() for record in records]
                for module, records in self.records.items()
            }

            # Write to file
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Saved {sum(len(r) for r in self.records.values())} history records to disk"
            )

        except Exception as e:
            logger.error(f"Failed to save history: {e}")
