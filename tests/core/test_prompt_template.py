"""
Unit tests for PromptTemplate.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from learning_assistant.core.prompt_template import PromptTemplate, PromptVariable


class TestPromptVariable:
    """Test PromptVariable dataclass."""

    def test_create_variable(self) -> None:
        """Test creating a PromptVariable instance."""
        var = PromptVariable(
            type="string",
            required=True,
            description="Test variable",
            default=None,
        )

        assert var.type == "string"
        assert var.required is True
        assert var.description == "Test variable"
        assert var.default is None

    def test_variable_with_default(self) -> None:
        """Test variable with default value."""
        var = PromptVariable(
            type="string",
            required=False,
            description="Optional variable",
            default="default_value",
        )

        assert var.required is False
        assert var.default == "default_value"


class TestPromptTemplate:
    """Test PromptTemplate class."""

    def create_test_template(self, tmpdir: Path) -> Path:
        """Create a test template file."""
        template_data = {
            "name": "test_template",
            "version": "1.0",
            "language": "zh",
            "description": "Test template",
            "variables": {
                "title": {
                    "type": "string",
                    "required": True,
                    "description": "Video title",
                },
                "content": {
                    "type": "string",
                    "required": True,
                    "description": "Video content",
                },
                "language": {
                    "type": "string",
                    "required": False,
                    "default": "zh",
                    "description": "Output language",
                },
            },
            "output_schema": {
                "type": "object",
                "required": ["title", "summary"],
            },
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "Title: {{title}}\n\nContent: {{content}}\n\nLanguage: {{language}}",
            "examples": [
                {
                    "input": {"title": "Test", "content": "Test content"},
                    "output": {"title": "Test", "summary": "Test summary"},
                }
            ],
        }

        template_file = tmpdir / "test_template.yaml"
        with open(template_file, "w", encoding="utf-8") as f:
            yaml.dump(template_data, f)

        return template_file

    def test_load_template(self) -> None:
        """Test loading template from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            assert template.name == "test_template"
            assert template.version == "1.0"
            assert template.language == "zh"
            assert len(template.variables) == 3
            assert "title" in template.variables
            assert "content" in template.variables
            assert "language" in template.variables

    def test_render_template(self) -> None:
        """Test rendering template with variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            system_prompt, user_prompt = template.render(
                variables={"title": "Test Video", "content": "Test content"}
            )

            assert system_prompt == "You are a helpful assistant."
            assert "Test Video" in user_prompt
            assert "Test content" in user_prompt
            assert "Language: zh" in user_prompt  # Default value

    def test_render_with_custom_language(self) -> None:
        """Test rendering with custom language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            system_prompt, user_prompt = template.render(
                variables={
                    "title": "Test Video",
                    "content": "Test content",
                    "language": "en",
                }
            )

            assert "Language: en" in user_prompt

    def test_missing_required_variable(self) -> None:
        """Test that missing required variable raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            with pytest.raises(ValueError, match="Missing required variables"):
                template.render(variables={"title": "Test Video"})

    def test_validate_output_success(self) -> None:
        """Test successful output validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            output = {"title": "Test", "summary": "Test summary"}
            is_valid = template.validate_output(output)

            assert is_valid is True

    def test_validate_output_missing_field(self) -> None:
        """Test output validation with missing field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            output = {"title": "Test"}  # Missing 'summary'
            is_valid = template.validate_output(output)

            assert is_valid is False

    def test_get_variable_info(self) -> None:
        """Test getting variable information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            var_info = template.get_variable_info()

            assert "title" in var_info
            assert var_info["title"]["type"] == "string"
            assert var_info["title"]["required"] is True

    def test_to_dict(self) -> None:
        """Test converting template to dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            template_dict = template.to_dict()

            assert template_dict["name"] == "test_template"
            assert template_dict["version"] == "1.0"
            assert template_dict["language"] == "zh"
            assert template_dict["has_output_schema"] is True
            assert template_dict["has_examples"] is True

    def test_template_file_not_found(self) -> None:
        """Test that missing template file raises error."""
        with pytest.raises(FileNotFoundError):
            PromptTemplate(Path("nonexistent.yaml"))

    def test_render_with_examples(self) -> None:
        """Test rendering with examples included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_test_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            system_prompt, user_prompt = template.render(
                variables={"title": "Test", "content": "Test content"},
                include_examples=True,
            )

            assert "## 示例" in system_prompt
            assert "示例 1" in system_prompt


class TestPromptTemplateConditionals:
    """Test template conditionals and loops."""

    def create_conditional_template(self, tmpdir: Path) -> Path:
        """Create template with conditional logic."""
        template_data = {
            "name": "conditional_template",
            "version": "1.0",
            "variables": {
                "title": {"type": "string", "required": True},
                "tags": {"type": "list", "required": False, "default": []},
            },
            "output_schema": {},
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": """Title: {{title}}

{% if tags %}
Tags:
{% for tag in tags %}
- {{tag}}
{% endfor %}
{% endif %}
""",
        }

        template_file = tmpdir / "conditional.yaml"
        with open(template_file, "w", encoding="utf-8") as f:
            yaml.dump(template_data, f)

        return template_file

    def test_conditional_rendering(self) -> None:
        """Test conditional template rendering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = self.create_conditional_template(Path(tmpdir))
            template = PromptTemplate(template_file)

            # Without tags
            _, user_prompt = template.render(variables={"title": "Test"})
            assert "Tags:" not in user_prompt

            # With tags
            _, user_prompt = template.render(
                variables={"title": "Test", "tags": ["Python", "AI"]}
            )
            assert "Tags:" in user_prompt
            assert "- Python" in user_prompt
            assert "- AI" in user_prompt
