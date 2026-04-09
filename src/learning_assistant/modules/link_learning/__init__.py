"""
Link Learning Module for Learning Assistant.

This module provides web content analysis and knowledge card generation.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from learning_assistant.core.base_module import BaseModule
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.exporters import MarkdownExporter
from learning_assistant.core.history_manager import HistoryManager
from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.prompt_manager import PromptManager
from learning_assistant.modules.link_learning.content_fetcher import ContentFetcher
from learning_assistant.modules.link_learning.content_parser import ContentParser
from learning_assistant.modules.link_learning.models import (
    KnowledgeCard,
    LinkContent,
    QAPair,
    QuizQuestion,
)


class LinkLearningModule(BaseModule):
    """
    Link Learning Module.

    Provides complete workflow:
    1. Fetch web content from URL
    2. Parse and extract content
    3. Generate knowledge card with LLM
    4. Export to Markdown/PDF
    5. Save to history
    """

    def __init__(self) -> None:
        """Initialize link learning module."""
        self.config: dict[str, Any] = {}
        self.event_bus: EventBus | None = None

        # Components
        self.content_fetcher: ContentFetcher | None = None
        self.content_parser: ContentParser | None = None
        self.prompt_manager: PromptManager | None = None
        self.exporter: MarkdownExporter | None = None
        self.llm_service: LLMService | None = None
        self.history_manager: HistoryManager | None = None

        logger.info("LinkLearningModule created")

    @property
    def name(self) -> str:
        """Module name."""
        return "link_learning"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize link learning module.

        Args:
            config: Module configuration
            event_bus: Event bus instance
        """
        self.config = config
        self.event_bus = event_bus

        # Initialize components
        self._init_components()

        logger.info("LinkLearningModule initialized")

    def _init_components(self) -> None:
        """Initialize all components."""
        import os

        # LLM service (must be initialized first for PromptManager)
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "openai")

        # Get API key from environment
        api_key_env = f"{provider.upper()}_API_KEY"
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"API key not found: {api_key_env}")

        # Build LLM kwargs with base_url from config
        llm_kwargs = {}
        if "base_url" in llm_config:
            llm_kwargs["base_url"] = llm_config["base_url"]
        if "timeout" in llm_config:
            llm_kwargs["timeout"] = llm_config["timeout"]

        self.llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            model=llm_config.get("model", "kimi-k2.5"),
            max_retries=llm_config.get("max_retries", 3),
            **llm_kwargs,
        )

        # Content fetcher
        fetcher_config = self.config.get("fetcher", {})
        self.content_fetcher = ContentFetcher(
            timeout=fetcher_config.get("timeout", 30),
            max_retries=fetcher_config.get("max_retries", 3),
            retry_delay=fetcher_config.get("retry_delay", 2),
            use_playwright=fetcher_config.get("use_playwright", False),
            user_agent=fetcher_config.get("user_agent"),
            proxy=fetcher_config.get("proxy"),
        )

        # Content parser
        parser_config = self.config.get("parser", {})
        self.content_parser = ContentParser(
            engine=parser_config.get("engine", "trafilatura"),
            include_comments=parser_config.get("include_comments", False),
            include_tables=parser_config.get("include_tables", True),
            favor_precision=parser_config.get("favor_precision", True),
            min_content_length=parser_config.get("min_content_length", 200),
        )

        # Prompt manager (requires llm_service)
        template_dirs = [Path("templates/prompts")]
        self.prompt_manager = PromptManager(
            template_dirs=template_dirs,
            llm_service=self.llm_service,
        )

        # Exporter
        output_config = self.config.get("output", {})
        self.exporter = MarkdownExporter(
            template_dir=Path("templates/outputs"),
            template_name="link_summary.md",
        )

        # History manager
        self.history_manager = HistoryManager(
            history_dir=Path("data/history/link"),
        )

        logger.debug("All components initialized")

    async def process(
        self, url: str, options: dict[str, Any] | None = None
    ) -> KnowledgeCard:
        """
        Process URL and generate knowledge card.

        Args:
            url: Web URL to process
            options: Processing options

        Returns:
            Knowledge card

        Raises:
            ValueError: If URL is invalid
            RuntimeError: If processing fails
        """
        if not url or not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {url}")

        options = options or {}
        logger.info(f"Processing URL: {url}")

        try:
            # Step 1: Fetch content
            logger.info("Step 1: Fetching web content...")
            html = await self.content_fetcher.fetch(url)

            # Step 2: Parse content
            logger.info("Step 2: Parsing web content...")
            link_content = self.content_parser.parse(html, url)

            # Step 3: Generate knowledge card with LLM
            logger.info("Step 3: Generating knowledge card...")
            knowledge_card = await self._generate_knowledge_card(link_content)

            # Step 4: Export
            if self.config.get("output", {}).get("save_history", True):
                logger.info("Step 4: Exporting and saving...")
                await self._export_and_save(knowledge_card)

            logger.info(f"Processing completed: {url}")
            return knowledge_card

        except Exception as e:
            logger.error(f"Processing failed for {url}: {e}")
            raise RuntimeError(f"Processing failed: {e}") from e

    async def _generate_knowledge_card(
        self, link_content: LinkContent
    ) -> KnowledgeCard:
        """
        Generate knowledge card from link content using LLM.

        Args:
            link_content: Parsed link content

        Returns:
            Knowledge card
        """

        # Load prompt template
        template = self.prompt_manager.load_template("link_summary")

        # Fill template variables
        system_prompt, user_prompt = template.render(
            {
                "title": link_content.title,
                "source": link_content.source,
                "word_count": link_content.word_count,
                "content": link_content.content,
            }
        )

        # Call LLM (synchronous call wrapped in async)
        llm_config = self.config.get("llm", {})
        response = await asyncio.to_thread(
            self.llm_service.call,
            prompt=user_prompt,
            model=llm_config.get("model", "kimi-k2.5"),
            temperature=llm_config.get("temperature", 0.3),
            max_tokens=llm_config.get("max_tokens", 2000),
        )

        # Parse JSON response
        card_data = self._parse_llm_response(response.content)

        # Convert qa_pairs and quiz to objects
        qa_pairs = [
            QAPair(
                question=qa["question"],
                answer=qa["answer"],
                difficulty=qa.get("difficulty", "medium"),
            )
            for qa in card_data.get("qa_pairs", [])
        ]

        quiz = [
            QuizQuestion(
                type=q["type"],
                question=q["question"],
                correct=q["correct"],
                options=q.get("options"),
                explanation=q.get("explanation"),
            )
            for q in card_data.get("quiz", [])
        ]

        # Build knowledge card
        knowledge_card = KnowledgeCard(
            title=link_content.title,
            url=link_content.url,
            source=link_content.source,
            summary=card_data["summary"],
            key_points=card_data["key_points"],
            tags=card_data["tags"],
            word_count=link_content.word_count,
            reading_time=self._estimate_reading_time(link_content.word_count),
            difficulty=card_data["difficulty"],
            created_at=datetime.now(),
            qa_pairs=qa_pairs,
            quiz=quiz,
        )

        return knowledge_card

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM JSON response.

        Args:
            response: LLM response string

        Returns:
            Parsed dictionary

        Raises:
            ValueError: If JSON parsing fails
        """
        import json

        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            # Validate required fields
            required_fields = ["summary", "key_points", "tags", "difficulty"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}") from e

    def _estimate_reading_time(self, word_count: int) -> str:
        """
        Estimate reading time based on word count.

        Args:
            word_count: Word count

        Returns:
            Reading time string (e.g., "15分钟")
        """
        # Average reading speed: 200-250 words per minute for Chinese
        # 250-300 words per minute for English
        reading_speed = 250  # words per minute
        minutes = max(1, word_count // reading_speed)

        if minutes < 60:
            return f"{minutes}分钟"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}小时{remaining_minutes}分钟"

    async def _export_and_save(self, knowledge_card: KnowledgeCard) -> None:
        """
        Export and save knowledge card.

        Args:
            knowledge_card: Knowledge card to export
        """
        # Export to Markdown
        output_dir = Path("data/outputs/link")
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            f"{knowledge_card.title[:50]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        output_path = output_dir / filename

        self.exporter.export(
            data=knowledge_card.to_dict(),
            output_path=output_path,
        )
        logger.info(f"Exported to: {output_path}")

        # Save to history
        self.history_manager.add_record(
            module=self.name,
            input=knowledge_card.url,
            output=str(output_path),
            metadata={
                "title": knowledge_card.title,
                "source": knowledge_card.source,
                "word_count": knowledge_card.word_count,
                "difficulty": knowledge_card.difficulty,
            },
        )
        logger.info("Saved to history")

    def cleanup(self) -> None:
        """Cleanup module resources."""
        logger.info("LinkLearningModule cleanup completed")

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute link learning workflow (sync wrapper).

        Args:
            input_data: Input data containing URL

        Returns:
            Knowledge card as dict
        """

        url = input_data.get("url")
        if not url:
            raise ValueError("URL is required")

        # Run async process in event loop
        knowledge_card = asyncio.run(self.process(url))

        # Return as dict
        return knowledge_card.to_dict()
