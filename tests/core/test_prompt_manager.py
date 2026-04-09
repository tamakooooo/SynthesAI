"""
Unit tests for PromptManager.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from learning_assistant.core.prompt_manager import PromptManager


class TestPromptManager:
    """Test PromptManager class."""

    def create_test_templates(self, tmpdir: Path) -> Path:
        """Create test template files."""
        templates_dir = tmpdir / "templates" / "prompts"
        templates_dir.mkdir(parents=True)

        # Create test template
        template_data = {
            "name": "test_template",
            "version": "1.0",
            "variables": {
                "input": {"type": "string", "required": True},
            },
            "output_schema": {"required": ["output"]},
            "system_prompt": "You are helpful.",
            "user_prompt": "Input: {{input}}",
        }

        template_file = templates_dir / "test_template.yaml"
        with open(template_file, "w", encoding="utf-8") as f:
            yaml.dump(template_data, f)

        return templates_dir

    def test_init(self) -> None:
        """Test PromptManager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            manager = PromptManager(template_dirs=[template_dir])

            assert len(manager.template_dirs) == 1
            assert manager.cache_enabled is True
            assert len(manager._template_cache) == 0

    def test_load_template(self) -> None:
        """Test loading template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))
            manager = PromptManager(template_dirs=[templates_dir])

            template = manager.load_template("test_template")

            assert template.name == "test_template"
            assert "test_template" in manager._template_cache

    def test_load_template_from_cache(self) -> None:
        """Test loading template from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))
            manager = PromptManager(template_dirs=[templates_dir])

            # First load
            template1 = manager.load_template("test_template")

            # Second load (from cache)
            template2 = manager.load_template("test_template")

            assert template1 is template2

    def test_load_template_not_found(self) -> None:
        """Test loading nonexistent template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            manager = PromptManager(template_dirs=[template_dir])

            with pytest.raises(
                FileNotFoundError, match="Template 'nonexistent' not found"
            ):
                manager.load_template("nonexistent")

    def test_render(self) -> None:
        """Test rendering template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))
            manager = PromptManager(template_dirs=[templates_dir])

            system_prompt, user_prompt = manager.render(
                "test_template",
                variables={"input": "test input"},
            )

            assert system_prompt == "You are helpful."
            assert "test input" in user_prompt

    def test_execute_without_llm_service(self) -> None:
        """Test executing without LLM service raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))
            manager = PromptManager(template_dirs=[templates_dir])

            with pytest.raises(ValueError, match="LLM service not configured"):
                manager.execute("test_template", variables={"input": "test"})

    def test_execute_with_llm_service(self) -> None:
        """Test executing with LLM service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))

            # Mock LLM service
            from learning_assistant.core.llm.base import LLMResponse

            mock_llm_service = Mock()
            mock_llm_service.call = Mock(
                return_value=LLMResponse(
                    content='{"output": "test result"}',
                    model="test-model",
                    usage={"total_tokens": 100},
                )
            )

            manager = PromptManager(
                template_dirs=[templates_dir],
                llm_service=mock_llm_service,
            )

            result = manager.execute(
                "test_template",
                variables={"input": "test input"},
                include_examples=False,
            )

            assert result == {"output": "test result"}
            mock_llm_service.call.assert_called_once()

    def test_execute_invalid_json(self) -> None:
        """Test executing with invalid JSON response."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))

            # Mock LLM service returns invalid JSON
            from learning_assistant.core.llm.base import LLMResponse

            mock_llm_service = Mock()
            mock_llm_service.call = Mock(
                return_value=LLMResponse(
                    content="not valid json",
                    model="test-model",
                    usage={"total_tokens": 10},
                )
            )

            manager = PromptManager(
                template_dirs=[templates_dir],
                llm_service=mock_llm_service,
            )

            with pytest.raises(ValueError, match="Invalid JSON output"):
                manager.execute(
                    "test_template",
                    variables={"input": "test"},
                )

    def test_list_templates(self) -> None:
        """Test listing templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))
            manager = PromptManager(template_dirs=[templates_dir])

            templates = manager.list_templates()

            assert len(templates) == 1
            assert templates[0]["name"] == "test_template"

    def test_clear_cache(self) -> None:
        """Test clearing cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))
            manager = PromptManager(template_dirs=[templates_dir])

            # Load template to cache
            manager.load_template("test_template")
            assert len(manager._template_cache) == 1

            # Clear cache
            manager.clear_cache()
            assert len(manager._template_cache) == 0

    def test_get_template_info(self) -> None:
        """Test getting template info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = self.create_test_templates(Path(tmpdir))
            manager = PromptManager(template_dirs=[templates_dir])

            info = manager.get_template_info("test_template")

            assert info["name"] == "test_template"
            assert info["version"] == "1.0"


class TestPromptManagerMultiDirectory:
    """Test PromptManager with multiple template directories."""

    def create_templates_in_dirs(self, tmpdir: Path) -> list[Path]:
        """Create templates in multiple directories."""
        dir1 = tmpdir / "prompts1"
        dir2 = tmpdir / "prompts2"
        dir1.mkdir()
        dir2.mkdir()

        # Template in dir1
        template1 = {
            "name": "template1",
            "version": "1.0",
            "variables": {"input": {"type": "string", "required": True}},
            "output_schema": {},
            "system_prompt": "System 1",
            "user_prompt": "{{input}}",
        }
        with open(dir1 / "template1.yaml", "w", encoding="utf-8") as f:
            yaml.dump(template1, f)

        # Template in dir2
        template2 = {
            "name": "template2",
            "version": "1.0",
            "variables": {"input": {"type": "string", "required": True}},
            "output_schema": {},
            "system_prompt": "System 2",
            "user_prompt": "{{input}}",
        }
        with open(dir2 / "template2.yaml", "w", encoding="utf-8") as f:
            yaml.dump(template2, f)

        return [dir1, dir2]

    def test_search_multiple_directories(self) -> None:
        """Test searching templates in multiple directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dirs = self.create_templates_in_dirs(Path(tmpdir))
            manager = PromptManager(template_dirs=dirs)

            # Load template from first directory
            template1 = manager.load_template("template1")
            assert template1.name == "template1"

            # Load template from second directory
            template2 = manager.load_template("template2")
            assert template2.name == "template2"

    def test_template_priority(self) -> None:
        """Test that earlier directory has priority."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dirs = self.create_templates_in_dirs(Path(tmpdir))

            # Create duplicate template in first directory
            template1_dup = {
                "name": "template2",
                "version": "2.0",  # Different version
                "variables": {"input": {"type": "string", "required": True}},
                "output_schema": {},
                "system_prompt": "System 1 override",
                "user_prompt": "{{input}}",
            }
            with open(dirs[0] / "template2.yaml", "w", encoding="utf-8") as f:
                yaml.dump(template1_dup, f)

            manager = PromptManager(template_dirs=dirs)

            # Should load from first directory (priority)
            template = manager.load_template("template2")
            assert template.version == "2.0"  # From first directory
