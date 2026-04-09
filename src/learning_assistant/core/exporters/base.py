"""
Base Exporter for Learning Assistant.

This module defines the abstract base class for all output exporters.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseExporter(ABC):
    """
    Abstract base class for output exporters.

    Each exporter (Markdown, PDF, HTML) must implement these methods.
    """

    def __init__(self, template_dir: Path | None = None) -> None:
        """
        Initialize exporter.

        Args:
            template_dir: Directory containing export templates
        """
        self.template_dir = template_dir or Path("templates/outputs")

    @abstractmethod
    def export(
        self,
        data: dict[str, Any],
        output_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Export data to file.

        Args:
            data: Data to export (usually structured summary)
            output_path: Output file path
            **kwargs: Additional export parameters
        """
        pass

    @abstractmethod
    def export_to_string(self, data: dict[str, Any], **kwargs: Any) -> str:
        """
        Export data to string.

        Args:
            data: Data to export
            **kwargs: Additional export parameters

        Returns:
            Exported content as string
        """
        pass

    def ensure_output_dir(self, output_path: Path) -> None:
        """
        Ensure output directory exists.

        Args:
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
