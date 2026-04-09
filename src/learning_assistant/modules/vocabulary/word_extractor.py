"""
Word Extractor - Extract vocabulary from text using LLM.

This module uses LLM to intelligently extract important words from
text content and generate complete vocabulary cards.
"""

import asyncio
import json
from typing import Any

from loguru import logger

from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.prompt_manager import PromptManager
from learning_assistant.modules.vocabulary.models import (
    VocabularyCard,
    Phonetic,
    Definition,
    ExampleSentence,
)


class WordExtractor:
    """
    Word extractor using LLM.

    Extracts important words from text and generates vocabulary cards
    with phonetics, definitions, examples, synonyms, etc.

    Attributes:
        llm_service: LLM service instance
        prompt_manager: Prompt manager instance
    """

    def __init__(
        self,
        llm_service: LLMService,
        prompt_manager: PromptManager,
    ):
        """
        Initialize word extractor.

        Args:
            llm_service: LLM service instance
            prompt_manager: Prompt manager instance
        """
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

        logger.info("WordExtractor initialized")

    async def extract(
        self,
        content: str,
        word_count: int = 10,
        difficulty: str = "intermediate",
        llm_config: dict[str, Any] | None = None,
    ) -> list[VocabularyCard]:
        """
        Extract important words from content.

        Args:
            content: Text content to extract words from
            word_count: Number of words to extract
            difficulty: Target difficulty level
            llm_config: LLM configuration (temperature, max_tokens, etc.)

        Returns:
            List of VocabularyCard objects

        Raises:
            ValueError: If content is empty or invalid
            RuntimeError: If extraction fails
        """
        # Validate input
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        word_count = max(1, min(50, word_count))  # Clamp to [1, 50]

        logger.info(f"Extracting {word_count} words from {len(content)} characters")

        # Prepare LLM config
        llm_config = llm_config or {}
        temperature = llm_config.get("temperature", 0.3)
        max_tokens = llm_config.get("max_tokens", 4000)

        try:
            # Load prompt template
            template = self.prompt_manager.load_template("vocabulary_extraction")

            # Determine difficulty distribution based on target difficulty
            difficulty_distribution = self._get_difficulty_distribution(difficulty)

            # Render prompt
            system_prompt, user_prompt = template.render(
                {
                    "content": content,
                    "word_count": word_count,
                    "difficulty_distribution": difficulty_distribution,
                }
            )

            # Call LLM (wrap sync call in async)
            response = await asyncio.to_thread(
                self.llm_service.call,
                prompt=user_prompt,
                model=llm_config.get("model", self.llm_service.model),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Parse JSON response
            result = self._parse_llm_response(response.content)

            # Convert to VocabularyCard objects
            vocabulary_cards = self._convert_to_cards(
                result.get("vocabulary_cards", [])
            )

            logger.info(f"Successfully extracted {len(vocabulary_cards)} words")

            return vocabulary_cards

        except Exception as e:
            logger.error(f"Word extraction failed: {e}")
            raise RuntimeError(f"Word extraction failed: {e}") from e

    def _get_difficulty_distribution(self, difficulty: str) -> str:
        """
        Get difficulty distribution string based on target difficulty.

        Args:
            difficulty: Target difficulty level

        Returns:
            Difficulty distribution string
        """
        distributions = {
            "beginner": "beginner: 60%, intermediate: 30%, advanced: 10%",
            "intermediate": "beginner: 30%, intermediate: 50%, advanced: 20%",
            "advanced": "beginner: 10%, intermediate: 30%, advanced: 60%",
        }
        return distributions.get(difficulty, distributions["intermediate"])

    def _parse_llm_response(self, response: str) -> dict:
        """
        Parse LLM JSON response.

        Args:
            response: LLM response string

        Returns:
            Parsed dictionary

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            # Validate structure
            if "vocabulary_cards" not in data:
                raise ValueError("Missing 'vocabulary_cards' field in response")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {response[:500]}")
            raise ValueError(f"Invalid JSON response: {e}") from e

    def _convert_to_cards(self, cards_data: list[dict]) -> list[VocabularyCard]:
        """
        Convert list of dictionaries to VocabularyCard objects.

        Args:
            cards_data: List of card dictionaries

        Returns:
            List of VocabularyCard objects
        """
        vocabulary_cards = []

        for card_data in cards_data:
            try:
                # Parse phonetic
                phonetic_data = card_data.get("phonetic", {})
                phonetic = Phonetic(
                    us=phonetic_data.get("us"),
                    uk=phonetic_data.get("uk"),
                )

                # Parse definition
                definition_data = card_data.get("definition", {})
                definition = Definition(
                    zh=definition_data.get("zh", ""),
                    en=definition_data.get("en"),
                )

                # Parse example sentences
                example_sentences = []
                for ex_data in card_data.get("example_sentences", []):
                    example_sentences.append(
                        ExampleSentence(
                            sentence=ex_data.get("sentence", ""),
                            translation=ex_data.get("translation", ""),
                            context=ex_data.get("context", "LLM生成"),
                        )
                    )

                # Create vocabulary card
                card = VocabularyCard(
                    word=card_data.get("word", ""),
                    phonetic=phonetic,
                    part_of_speech=card_data.get("part_of_speech", ""),
                    definition=definition,
                    example_sentences=example_sentences,
                    synonyms=card_data.get("synonyms", []),
                    antonyms=card_data.get("antonyms", []),
                    related_words=card_data.get("related_words", []),
                    difficulty=card_data.get("difficulty", "intermediate"),
                    frequency=card_data.get("frequency", "medium"),
                )

                vocabulary_cards.append(card)

            except Exception as e:
                logger.warning(f"Failed to parse vocabulary card: {e}")
                logger.debug(f"Card data: {card_data}")
                continue

        return vocabulary_cards


# Convenience function
async def extract_vocabulary(
    content: str,
    word_count: int = 10,
    difficulty: str = "intermediate",
    llm_service: LLMService | None = None,
    prompt_manager: PromptManager | None = None,
) -> list[VocabularyCard]:
    """
    Convenience function to extract vocabulary.

    Args:
        content: Text content
        word_count: Number of words to extract
        difficulty: Target difficulty
        llm_service: LLM service (optional, will create if not provided)
        prompt_manager: Prompt manager (optional, will create if not provided)

    Returns:
        List of VocabularyCard objects
    """
    if llm_service is None or prompt_manager is None:
        raise ValueError("llm_service and prompt_manager are required")

    extractor = WordExtractor(llm_service, prompt_manager)
    return await extractor.extract(content, word_count, difficulty)
