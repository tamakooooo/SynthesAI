"""
Vocabulary Learning Module.

This module provides comprehensive vocabulary extraction and learning
functionality including word extraction, phonetic lookup, card generation,
and contextual story creation.
"""

import asyncio
import os
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
from learning_assistant.modules.vocabulary.models import (
    VocabularyCard,
    VocabularyOutput,
    ContextStory,
)
from learning_assistant.modules.vocabulary.word_extractor import WordExtractor
from learning_assistant.modules.vocabulary.phonetic_lookup import PhoneticLookup
from learning_assistant.modules.vocabulary.story_generator import StoryGenerator


class VocabularyLearningModule(BaseModule):
    """
    Vocabulary Learning Module.

    Provides complete workflow:
    1. Extract important words from content
    2. Generate vocabulary cards with phonetics, definitions, examples
    3. Enrich phonetics if missing
    4. Generate contextual story (optional)
    5. Export to Markdown/JSON
    6. Save to history
    """

    def __init__(self) -> None:
        """Initialize vocabulary learning module."""
        self.config: dict[str, Any] = {}
        self.event_bus: EventBus | None = None

        # Components
        self.word_extractor: WordExtractor | None = None
        self.phonetic_lookup: PhoneticLookup | None = None
        self.story_generator: StoryGenerator | None = None
        self.exporter: MarkdownExporter | None = None
        self.llm_service: LLMService | None = None
        self.prompt_manager: PromptManager | None = None
        self.history_manager: HistoryManager | None = None

        logger.info("VocabularyLearningModule created")

    @property
    def name(self) -> str:
        """Module name."""
        return "vocabulary"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize vocabulary learning module.

        Args:
            config: Module configuration
            event_bus: Event bus instance
        """
        self.config = config
        self.event_bus = event_bus

        # Initialize components
        self._init_components()

        logger.info("VocabularyLearningModule initialized")

    def _init_components(self) -> None:
        """Initialize all components."""
        from learning_assistant.core.config_manager import ConfigManager

        # LLM service (must be initialized first)
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "openai")

        # Get API key with priority: env var > config file > global settings
        api_key = None
        api_key_env = f"{provider.upper()}_API_KEY"

        # 1. Try environment variable first (highest priority)
        api_key = os.environ.get(api_key_env)

        # 2. Try module config file
        if not api_key and "api_key" in llm_config:
            api_key = llm_config["api_key"]

        # 3. Try global settings via ConfigManager
        if not api_key:
            try:
                config_manager = ConfigManager()
                config_manager.load_all()
                global_llm_config = config_manager.get_llm_config(provider)
                api_key = global_llm_config.get("api_key")
            except Exception as e:
                logger.debug(f"Failed to get API key from global config: {e}")

        if not api_key:
            raise ValueError(
                f"API key not found. Set {api_key_env} environment variable, "
                f"add 'api_key' to vocabulary.llm config, "
                f"or configure it in settings.local.yaml"
            )

        # Build LLM kwargs with base_url from config
        llm_kwargs = {}
        if "base_url" in llm_config:
            llm_kwargs["base_url"] = llm_config["base_url"]
        if "timeout" in llm_config:
            llm_kwargs["timeout"] = llm_config["timeout"]

        self.llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            model=llm_config.get("model", "gpt-4"),
            max_retries=llm_config.get("max_retries", 3),
            **llm_kwargs,
        )

        # Prompt manager (requires llm_service)
        template_dirs = [Path("templates/prompts")]
        self.prompt_manager = PromptManager(
            template_dirs=template_dirs,
            llm_service=self.llm_service,
        )

        # Word extractor
        self.word_extractor = WordExtractor(
            llm_service=self.llm_service,
            prompt_manager=self.prompt_manager,
        )

        # Phonetic lookup
        phonetic_config = self.config.get("phonetic", {})
        local_dict_path = Path(
            phonetic_config.get("local_dictionary", "data/dictionaries/english.json")
        )
        api_url = phonetic_config.get(
            "api_url", "https://api.dictionaryapi.dev/api/v2/entries/en/"
        )

        self.phonetic_lookup = PhoneticLookup(
            local_dict_path=local_dict_path if local_dict_path.exists() else None,
            api_url=api_url,
            llm_service=self.llm_service,
        )

        # Story generator
        story_config = self.config.get("story", {})
        if story_config.get("enabled", True):
            self.story_generator = StoryGenerator(
                llm_service=self.llm_service,
                prompt_manager=self.prompt_manager,
            )

        # Exporter
        output_config = self.config.get("output", {})
        self.exporter = MarkdownExporter(
            template_dir=Path("templates/outputs"),
            template_name="vocabulary_card.md",
        )

        # History manager
        history_dir = Path(output_config.get("directory", "data/outputs/vocabulary"))
        self.history_manager = HistoryManager(
            history_dir=history_dir.parent / "history" / "vocabulary",
        )

        logger.debug("All components initialized")

    async def process(
        self,
        content: str,
        word_count: int = 10,
        difficulty: str = "intermediate",
        generate_story: bool = True,
    ) -> VocabularyOutput:
        """
        Process content and generate vocabulary cards.

        Args:
            content: Text content to extract words from
            word_count: Number of words to extract
            difficulty: Target difficulty level
            generate_story: Whether to generate contextual story

        Returns:
            VocabularyOutput object

        Raises:
            ValueError: If content is empty
            RuntimeError: If processing fails
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        logger.info(
            f"Processing content ({len(content)} chars), extracting {word_count} words"
        )

        try:
            # Step 1: Extract words and generate cards
            logger.info("Step 1/4: Extracting words...")
            vocabulary_cards = await self.word_extractor.extract(
                content=content,
                word_count=word_count,
                difficulty=difficulty,
                llm_config=self.config.get("llm", {}),
            )

            # Step 2: Enrich phonetics if missing
            logger.info("Step 2/4: Enriching phonetics...")
            await self._enrich_phonetics(vocabulary_cards)

            # Step 3: Generate story (optional)
            context_story = None
            if generate_story and self.story_generator and vocabulary_cards:
                logger.info("Step 3/4: Generating story...")
                words = [card.word for card in vocabulary_cards]
                context_story = await self.story_generator.generate(
                    words=words,
                    word_count=self.config.get("story", {}).get(
                        "default_word_count", 300
                    ),
                    difficulty=difficulty,
                    llm_config=self.config.get("llm", {}),
                )
            else:
                logger.info("Step 3/4: Skipping story generation")

            # Step 4: Generate statistics
            logger.info("Step 4/4: Generating statistics...")
            statistics = self._generate_statistics(vocabulary_cards)

            # Build output
            output = VocabularyOutput(
                vocabulary_cards=vocabulary_cards,
                context_story=context_story,
                statistics=statistics,
            )

            logger.info(
                f"Processing completed: {len(vocabulary_cards)} words extracted"
            )

            return output

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise RuntimeError(f"Processing failed: {e}") from e

    async def _enrich_phonetics(self, vocabulary_cards: list[VocabularyCard]) -> None:
        """
        Enrich phonetic transcriptions for cards missing them.

        Args:
            vocabulary_cards: List of vocabulary cards
        """
        if not self.phonetic_lookup:
            return

        for card in vocabulary_cards:
            # Skip if already has phonetics
            if card.phonetic.us or card.phonetic.uk:
                continue

            # Look up phonetic
            try:
                phonetic = await self.phonetic_lookup.lookup(card.word)
                card.phonetic = phonetic
            except Exception as e:
                logger.warning(f"Failed to lookup phonetic for '{card.word}': {e}")

    def _generate_statistics(
        self, vocabulary_cards: list[VocabularyCard]
    ) -> dict[str, Any]:
        """
        Generate statistics about extracted vocabulary.

        Args:
            vocabulary_cards: List of vocabulary cards

        Returns:
            Statistics dictionary
        """
        difficulty_dist = {"beginner": 0, "intermediate": 0, "advanced": 0}
        frequency_dist = {"high": 0, "medium": 0, "low": 0}
        pos_dist: dict[str, int] = {}

        for card in vocabulary_cards:
            # Difficulty distribution
            if card.difficulty in difficulty_dist:
                difficulty_dist[card.difficulty] += 1

            # Frequency distribution
            if card.frequency in frequency_dist:
                frequency_dist[card.frequency] += 1

            # Part of speech distribution
            pos = card.part_of_speech
            pos_dist[pos] = pos_dist.get(pos, 0) + 1

        return {
            "total_words": len(vocabulary_cards),
            "difficulty_distribution": difficulty_dist,
            "frequency_distribution": frequency_dist,
            "part_of_speech_distribution": pos_dist,
        }

    async def _export_and_save(
        self, output: VocabularyOutput, source: str
    ) -> dict[str, str]:
        """
        Export and save vocabulary output.

        Args:
            output: Vocabulary output
            source: Source text or file

        Returns:
            Dictionary of output file paths
        """
        output_dir = Path(
            self.config.get("output", {}).get("directory", "data/outputs/vocabulary")
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vocabulary_{timestamp}.md"
        output_path = output_dir / filename

        # Export to Markdown
        if self.exporter:
            self.exporter.export(
                data=output.to_dict(),
                output_path=output_path,
            )
            logger.info(f"Exported to: {output_path}")

        # Save to history
        if self.history_manager:
            self.history_manager.add_record(
                module=self.name,
                input=source[:200],  # Truncate for storage
                output=str(output_path),
                metadata={
                    "word_count": len(output.vocabulary_cards),
                    "difficulty": (
                        output.vocabulary_cards[0].difficulty
                        if output.vocabulary_cards
                        else "intermediate"
                    ),
                },
            )
            logger.info("Saved to history")

        return {"markdown_path": str(output_path)}

    def cleanup(self) -> None:
        """Cleanup module resources."""
        logger.info("VocabularyLearningModule cleanup completed")

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute vocabulary learning workflow (sync wrapper).

        Args:
            input_data: Input data containing content

        Returns:
            Vocabulary output as dict
        """
        content = input_data.get("content") or input_data.get("text")
        if not content:
            raise ValueError("Content/text is required")

        word_count = input_data.get("word_count", 10)
        difficulty = input_data.get("difficulty", "intermediate")
        generate_story = input_data.get("generate_story", True)

        # Run async process in event loop
        output = asyncio.run(
            self.process(
                content=content,
                word_count=word_count,
                difficulty=difficulty,
                generate_story=generate_story,
            )
        )

        # Export and save
        files = asyncio.run(self._export_and_save(output, content))

        # Return as dict
        result = output.to_dict()
        result["files"] = files
        result["status"] = "success"
        result["timestamp"] = datetime.now().isoformat()

        return result
