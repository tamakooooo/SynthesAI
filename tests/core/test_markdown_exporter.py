"""
Unit tests for MarkdownExporter.
"""

import tempfile
from pathlib import Path

import pytest

from learning_assistant.core.exporters.markdown import MarkdownExporter


class TestMarkdownExporter:
    """Test MarkdownExporter class."""

    def test_init(self) -> None:
        """Test MarkdownExporter initialization."""
        exporter = MarkdownExporter()

        assert exporter.template_dir == Path("templates/outputs")
        assert exporter.template_name == "video_summary.md"

    def test_init_custom_template(self) -> None:
        """Test initialization with custom template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            exporter = MarkdownExporter(
                template_dir=template_dir, template_name="custom.md"
            )

            assert exporter.template_dir == template_dir
            assert exporter.template_name == "custom.md"

    def test_export_to_string_default_template(self) -> None:
        """Test exporting to string with default template."""
        exporter = MarkdownExporter()

        data = {
            "title": "Test Video",
            "duration_estimate": "15分钟",
            "summary": "This is a test summary.",
            "key_points": [
                {"point": "Key point 1", "importance": "high", "timestamp": "00:01:30"}
            ],
            "chapters": [
                {
                    "title": "Chapter 1",
                    "start_time": "00:00:00",
                    "end_time": "00:05:00",
                    "summary": "Chapter 1 summary",
                }
            ],
            "action_items": [
                {"action": "Action 1", "priority": "high"},
                {"action": "Action 2", "priority": "low"},
            ],
            "topics": ["Python", "AI", "Testing"],
        }

        result = exporter.export_to_string(data)

        assert "# Test Video" in result
        assert "15分钟" in result
        assert "This is a test summary." in result
        assert "Key point 1" in result
        assert "Chapter 1" in result
        assert "Action 1" in result
        assert "Python" in result

    def test_export_to_file(self) -> None:
        """Test exporting to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.md"

            exporter = MarkdownExporter()

            data = {
                "title": "Test Video",
                "summary": "Test summary",
                "key_points": [],
                "chapters": [],
            }

            exporter.export(data, output_path)

            assert output_path.exists()

            content = output_path.read_text(encoding="utf-8")
            assert "# Test Video" in content
            assert "Test summary" in content

    def test_export_with_missing_optional_fields(self) -> None:
        """Test exporting with missing optional fields."""
        exporter = MarkdownExporter()

        data = {
            "title": "Minimal Video",
            "summary": "Minimal summary",
            "key_points": [],
            "chapters": [],
        }

        result = exporter.export_to_string(data)

        assert "# Minimal Video" in result
        assert "Minimal summary" in result
        # Optional fields should not cause errors
        assert "行动建议" not in result  # No action_items
        assert "主题标签" not in result  # No topics

    def test_export_with_high_priority_items(self) -> None:
        """Test exporting with different priority levels."""
        exporter = MarkdownExporter()

        data = {
            "title": "Test",
            "summary": "Summary",
            "key_points": [
                {"point": "High priority", "importance": "high"},
                {"point": "Medium priority", "importance": "medium"},
                {"point": "Low priority", "importance": "low"},
            ],
            "chapters": [],
            "action_items": [
                {"action": "Important task", "priority": "high"},
                {"action": "Normal task", "priority": "medium"},
            ],
        }

        result = exporter.export_to_string(data)

        assert "⭐ High priority" in result
        assert "Medium priority" in result
        assert "Low priority" in result
        assert "Important task" in result
        assert "Normal task" in result

    def test_ensure_output_dir(self) -> None:
        """Test that output directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "output.md"

            exporter = MarkdownExporter()

            data = {
                "title": "Test",
                "summary": "Summary",
                "key_points": [],
                "chapters": [],
            }

            exporter.export(data, output_path)

            assert output_path.parent.exists()
            assert output_path.exists()


class TestMarkdownExporterFormatting:
    """Test Markdown formatting details."""

    def test_chapter_timestamps(self) -> None:
        """Test chapter timestamp formatting."""
        exporter = MarkdownExporter()

        data = {
            "title": "Test",
            "summary": "Summary",
            "key_points": [],
            "chapters": [
                {
                    "title": "Chapter 1",
                    "start_time": "00:00:00",
                    "end_time": "00:05:00",
                    "summary": "Summary",
                }
            ],
        }

        result = exporter.export_to_string(data)

        assert "00:00:00" in result
        assert "00:05:00" in result

    def test_multiple_key_points(self) -> None:
        """Test multiple key points."""
        exporter = MarkdownExporter()

        data = {
            "title": "Test",
            "summary": "Summary",
            "key_points": [
                {"point": "Point 1", "importance": "high"},
                {"point": "Point 2", "importance": "high"},
                {"point": "Point 3", "importance": "medium"},
            ],
            "chapters": [],
        }

        result = exporter.export_to_string(data)

        assert "Point 1" in result
        assert "Point 2" in result
        assert "Point 3" in result

    def test_topics_formatting(self) -> None:
        """Test topics tag formatting."""
        exporter = MarkdownExporter()

        data = {
            "title": "Test",
            "summary": "Summary",
            "key_points": [],
            "chapters": [],
            "topics": ["Python", "AI", "Machine Learning"],
        }

        result = exporter.export_to_string(data)

        assert "`Python`" in result
        assert "`AI`" in result
        assert "`Machine Learning`" in result
