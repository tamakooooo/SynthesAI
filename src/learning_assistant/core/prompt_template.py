"""
Prompt Template for Learning Assistant.

This module provides structured prompt template management with YAML-based definitions.
"""

import json
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger
from pydantic import BaseModel


class PromptVariable(BaseModel):
    """Prompt variable definition."""

    type: str
    required: bool = True
    description: str = ""
    default: Any = None


class PromptTemplate:
    """
    Prompt template loaded from YAML file.

    Supports:
    - Variable interpolation with Jinja2
    - JSON Schema validation for output
    - Few-shot examples
    - System and user prompts
    """

    def __init__(self, template_path: Path) -> None:
        """
        Initialize prompt template from YAML file.

        Args:
            template_path: Path to YAML template file
        """
        self.template_path = template_path
        self.name: str = ""
        self.version: str = ""
        self.language: str = "zh"
        self.description: str = ""
        self.variables: dict[str, PromptVariable] = {}
        self.output_schema: dict[str, Any] = {}
        self.system_prompt: str = ""
        self.user_prompt_template: str = ""
        self.examples: list[dict[str, Any]] = []

        # Load template
        self._load_template()

        # Initialize Jinja2 environment
        template_dir = template_path.parent
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(
            f"PromptTemplate loaded: {self.name} v{self.version} ({self.language})"
        )

    def _load_template(self) -> None:
        """Load template from YAML file."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

        with open(self.template_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Parse template metadata
        self.name = data.get("name", "")
        self.version = data.get("version", "1.0")
        self.language = data.get("language", "zh")
        self.description = data.get("description", "")

        # Parse variables (supports both dict and list format)
        variables_data = data.get("variables", {})
        if isinstance(variables_data, list):
            # List format: [{name: ..., type: ..., ...}, ...]
            for var_def in variables_data:
                var_name = var_def.get("name")
                if var_name:
                    # Remove 'name' from var_def to avoid passing it to PromptVariable
                    var_copy = {k: v for k, v in var_def.items() if k != "name"}
                    self.variables[var_name] = PromptVariable(**var_copy)
        else:
            # Dict format: {var_name: {type: ..., ...}, ...}
            for var_name, var_def in variables_data.items():
                self.variables[var_name] = PromptVariable(**var_def)

        # Parse output schema
        self.output_schema = data.get("json_schema", data.get("output_schema", {}))

        # Parse prompts (support both 'template' and 'user_prompt' keys)
        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("template", data.get("user_prompt", ""))

        # Parse examples
        self.examples = data.get("examples", [])

    def render(
        self,
        variables: dict[str, Any],
        include_examples: bool = False,
    ) -> tuple[str, str]:
        """
        Render prompt with variables.

        Args:
            variables: Variable values for template rendering
            include_examples: Whether to include few-shot examples

        Returns:
            Tuple of (system_prompt, user_prompt)

        Raises:
            ValueError: If required variables are missing
        """
        # Validate required variables
        self._validate_variables(variables)

        # Merge with defaults
        merged_vars = self._merge_defaults(variables)

        # Render user prompt with Jinja2
        template = Template(self.user_prompt_template)
        user_prompt = template.render(**merged_vars)

        # Build system prompt
        system_prompt = self.system_prompt

        # Add examples if requested
        if include_examples and self.examples:
            examples_text = self._format_examples()
            system_prompt += f"\n\n## 示例\n\n{examples_text}"

        logger.debug(
            f"Rendered prompt: system={len(system_prompt)}, user={len(user_prompt)}"
        )

        return system_prompt, user_prompt

    def _validate_variables(self, variables: dict[str, Any]) -> None:
        """
        Validate that all required variables are provided.

        Args:
            variables: Provided variable values

        Raises:
            ValueError: If required variables are missing
        """
        missing_vars = []

        for var_name, var_def in self.variables.items():
            if var_def.required and var_name not in variables:
                if var_def.default is None:
                    missing_vars.append(var_name)

        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

    def _merge_defaults(self, variables: dict[str, Any]) -> dict[str, Any]:
        """
        Merge provided variables with defaults.

        Args:
            variables: Provided variable values

        Returns:
            Merged variables with defaults filled in
        """
        merged = {}

        for var_name, var_def in self.variables.items():
            if var_name in variables:
                merged[var_name] = variables[var_name]
            elif var_def.default is not None:
                merged[var_name] = var_def.default

        return merged

    def _format_examples(self) -> str:
        """
        Format examples for few-shot learning.

        Returns:
            Formatted examples text
        """
        if not self.examples:
            return ""

        formatted_examples = []

        for idx, example in enumerate(self.examples, start=1):
            input_data = example.get("input", {})
            output_data = example.get("output", {})

            example_text = f"### 示例 {idx}\n\n"
            example_text += "**输入**:\n"
            example_text += f"```json\n{json.dumps(input_data, ensure_ascii=False, indent=2)}\n```\n\n"
            example_text += "**输出**:\n"
            example_text += f"```json\n{json.dumps(output_data, ensure_ascii=False, indent=2)}\n```\n"

            formatted_examples.append(example_text)

        return "\n".join(formatted_examples)

    def validate_output(self, output: dict[str, Any]) -> bool:
        """
        Validate output against JSON schema.

        Args:
            output: Output data to validate

        Returns:
            True if valid, False otherwise
        """
        if not self.output_schema:
            logger.warning("No output schema defined, skipping validation")
            return True

        # Basic schema validation
        # In production, use jsonschema library for full validation
        required_fields = self.output_schema.get("required", [])

        for field in required_fields:
            if field not in output:
                logger.warning(f"Missing required field in output: {field}")
                return False

        return True

    def get_variable_info(self) -> dict[str, dict[str, Any]]:
        """
        Get information about template variables.

        Returns:
            Dictionary mapping variable names to their definitions
        """
        return {
            name: {
                "type": var.type,
                "required": var.required,
                "description": var.description,
                "default": var.default,
            }
            for name, var in self.variables.items()
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert template to dictionary representation.

        Returns:
            Dictionary with template metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "language": self.language,
            "description": self.description,
            "variables": self.get_variable_info(),
            "has_output_schema": bool(self.output_schema),
            "has_examples": bool(self.examples),
        }
