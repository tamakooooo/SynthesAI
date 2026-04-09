"""
Prompt Manager for Learning Assistant.

This module provides centralized prompt template management with caching and LLM integration.
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.prompt_template import PromptTemplate


class PromptManager:
    """
    Prompt Manager for template-based LLM interactions.

    Features:
    - Template loading and caching
    - Multi-directory template search
    - LLM service integration
    - Structured output validation
    """

    def __init__(
        self,
        template_dirs: list[Path] | None = None,
        llm_service: LLMService | None = None,
        cache_enabled: bool = True,
    ) -> None:
        """
        Initialize PromptManager.

        Args:
            template_dirs: List of directories to search for templates
            llm_service: LLM service for prompt execution
            cache_enabled: Whether to cache loaded templates
        """
        self.template_dirs = template_dirs or [Path("templates/prompts")]
        self.llm_service = llm_service
        self.cache_enabled = cache_enabled

        # Template cache
        self._template_cache: dict[str, PromptTemplate] = {}

        logger.info(
            f"PromptManager initialized with {len(self.template_dirs)} template directories"
        )

    def load_template(self, template_name: str) -> PromptTemplate:
        """
        Load a prompt template by name.

        Searches template directories in order for:
        - {template_name}.yaml
        - {template_name}/{template_name}.yaml

        Args:
            template_name: Name of the template to load

        Returns:
            Loaded PromptTemplate instance

        Raises:
            FileNotFoundError: If template not found in any directory
        """
        # Check cache first
        if self.cache_enabled and template_name in self._template_cache:
            logger.debug(f"Template loaded from cache: {template_name}")
            return self._template_cache[template_name]

        # Search for template file
        template_path = self._find_template(template_name)

        if template_path is None:
            raise FileNotFoundError(
                f"Template '{template_name}' not found in: "
                f"{', '.join(str(d) for d in self.template_dirs)}"
            )

        # Load template
        template = PromptTemplate(template_path)

        # Cache template
        if self.cache_enabled:
            self._template_cache[template_name] = template

        logger.info(f"Loaded template: {template_name} from {template_path}")

        return template

    def _find_template(self, template_name: str) -> Path | None:
        """
        Find template file in template directories.

        Args:
            template_name: Name of template to find

        Returns:
            Path to template file or None if not found
        """
        for template_dir in self.template_dirs:
            # Try direct file
            template_file = template_dir / f"{template_name}.yaml"
            if template_file.exists():
                return template_file

            # Try subdirectory
            template_file = template_dir / template_name / f"{template_name}.yaml"
            if template_file.exists():
                return template_file

        return None

    def render(
        self,
        template_name: str,
        variables: dict[str, Any],
        include_examples: bool = False,
    ) -> tuple[str, str]:
        """
        Render a prompt template with variables.

        Args:
            template_name: Name of template to render
            variables: Variable values for rendering
            include_examples: Whether to include few-shot examples

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        template = self.load_template(template_name)
        return template.render(variables, include_examples=include_examples)

    def execute(
        self,
        template_name: str,
        variables: dict[str, Any],
        include_examples: bool = True,
        validate_output: bool = True,
        **llm_kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a prompt template with LLM.

        Args:
            template_name: Name of template to execute
            variables: Variable values for rendering
            include_examples: Whether to include few-shot examples
            validate_output: Whether to validate output against schema
            **llm_kwargs: Additional arguments for LLM call

        Returns:
            Parsed JSON output from LLM

        Raises:
            ValueError: If LLM service not configured or output invalid
        """
        if self.llm_service is None:
            raise ValueError("LLM service not configured")

        # Load and render template
        template = self.load_template(template_name)
        system_prompt, user_prompt = template.render(
            variables, include_examples=include_examples
        )

        logger.info(f"Executing prompt template: {template_name}")

        # Call LLM (synchronous)
        response = self.llm_service.call(
            prompt=user_prompt,
            system_prompt=system_prompt,
            **llm_kwargs,
        )

        # Extract content from LLMResponse
        content = response.content

        # Clean Markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            # Remove opening ```json or ```
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        # Parse JSON output
        try:
            output: dict[str, Any] = json.loads(content)
            logger.info(f"LLM returned JSON keys: {list(output.keys())}")
            logger.info(
                f"Full LLM output: {json.dumps(output, ensure_ascii=False, indent=2)}"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM output as JSON: {e}")
            raise ValueError(f"Invalid JSON output: {content}") from e

        # Normalize field names (Chinese to English mapping)
        field_mapping = {
            "视频标题": "title",
            "标题": "title",
            "视频概述": "summary",
            "概述": "summary",
            "核心结论": "summary",
            "总结": "summary",
            "关键要点": "key_points",
            "关键点": "key_points",
            "章节": "chapters",
            "章节总结": "chapters",
            "行动建议": "action_items",
            "主题标签": "topics",
            "时长估计": "duration_estimate",
        }
        normalized_output = {}
        for key, value in output.items():
            # Use mapped name if exists, otherwise use original
            normalized_key = field_mapping.get(key, key)
            normalized_output[normalized_key] = value
            if normalized_key != key:
                logger.debug(f"Mapped field: {key} → {normalized_key}")

        # Update output with normalized keys
        output = normalized_output

        # Convert chapters from dict to array if needed
        if "chapters" in output:
            logger.debug(f"chapters type: {type(output['chapters'])}")
            logger.debug(
                f"chapters content: {json.dumps(output['chapters'], ensure_ascii=False, indent=2)}"
            )

            if isinstance(output["chapters"], dict):
                chapters_array = []
                for chapter_title, chapter_data in output["chapters"].items():
                    if isinstance(chapter_data, dict):
                        chapter_item = {
                            "title": chapter_title,
                            "summary": chapter_data.get(
                                "主要内容", chapter_data.get("summary", "")
                            ),
                            "start_time": chapter_data.get("start_time", "00:00"),
                        }
                        chapters_array.append(chapter_item)
                    else:
                        chapters_array.append(
                            {
                                "title": chapter_title,
                                "summary": str(chapter_data),
                                "start_time": "00:00",
                            }
                        )
                output["chapters"] = chapters_array
                logger.debug(
                    f"Converted chapters from dict to array: {len(chapters_array)} chapters"
                )
            elif isinstance(output["chapters"], list):
                # Normalize array items
                normalized_chapters = []
                for idx, item in enumerate(output["chapters"]):
                    logger.debug(f"Chapter {idx}: {item}")
                    if isinstance(item, dict):
                        # Try to find title field - check multiple possible keys
                        title = None
                        for key in ["title", "章节标题", "章节名称", "chapter_title"]:
                            if key in item and item[key]:
                                title = item[key]
                                break

                        if not title:
                            title = ""

                        # Try to find summary field
                        summary = None
                        for key in [
                            "summary",
                            "内容",
                            "主要内容",
                            "关键信息",
                            "chapter_summary",
                        ]:
                            if key in item and item[key]:
                                summary = item[key]
                                break

                        if not summary:
                            summary = ""

                        start_time = item.get("start_time", "00:00")

                        # Handle summary as array
                        if isinstance(summary, list):
                            summary = " ".join(str(s) for s in summary)

                        logger.debug(
                            f"  → title={title}, summary length={len(summary) if summary else 0}"
                        )

                        normalized_chapters.append(
                            {
                                "title": str(title),
                                "summary": str(summary),
                                "start_time": str(start_time),
                            }
                        )
                output["chapters"] = normalized_chapters
                logger.debug(f"Normalized {len(normalized_chapters)} chapters")

        # Convert key_points from dict to array if needed
        if "key_points" in output and isinstance(output["key_points"], dict):
            points_array = []
            for point_title, point_data in output["key_points"].items():
                if isinstance(point_data, dict):
                    points_array.append(
                        {
                            "point": point_title,
                            "importance": point_data.get("importance", "medium"),
                        }
                    )
                else:
                    points_array.append({"point": point_title, "importance": "medium"})
            output["key_points"] = points_array
            logger.debug(
                f"Converted key_points from dict to array: {len(points_array)} points"
            )

        # Validate output
        if validate_output:
            if not template.validate_output(output):
                logger.warning("Output validation failed, but continuing...")

        logger.debug(f"Final output keys: {list(output.keys())}")
        logger.debug(
            f"Final output sample: {json.dumps({k: v for k, v in list(output.items())[:3]}, ensure_ascii=False, indent=2)}"
        )

        return output

    def list_templates(self) -> list[dict[str, Any]]:
        """
        List all available templates.

        Returns:
            List of template metadata dictionaries
        """
        templates = []

        for template_dir in self.template_dirs:
            if not template_dir.exists():
                continue

            # Find all YAML files
            for yaml_file in template_dir.glob("*.yaml"):
                try:
                    template = PromptTemplate(yaml_file)
                    templates.append(template.to_dict())
                except Exception as e:
                    logger.warning(f"Failed to load template {yaml_file}: {e}")

            # Find templates in subdirectories
            for subdir in template_dir.iterdir():
                if subdir.is_dir():
                    yaml_file = subdir / f"{subdir.name}.yaml"
                    if yaml_file.exists():
                        try:
                            template = PromptTemplate(yaml_file)
                            templates.append(template.to_dict())
                        except Exception as e:
                            logger.warning(f"Failed to load template {yaml_file}: {e}")

        logger.info(f"Found {len(templates)} templates")
        return templates

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        logger.info("Template cache cleared")

    def get_template_info(self, template_name: str) -> dict[str, Any]:
        """
        Get information about a template.

        Args:
            template_name: Name of template

        Returns:
            Template metadata dictionary
        """
        template = self.load_template(template_name)
        return template.to_dict()
