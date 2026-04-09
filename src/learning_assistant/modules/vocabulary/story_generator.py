"""
Story Generator - Generate contextual stories containing target words.

This module creates engaging stories that naturally incorporate
target vocabulary words to help with memory retention.
"""

import asyncio
import json
from typing import Any

from loguru import logger

from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.prompt_manager import PromptManager
from learning_assistant.modules.vocabulary.models import ContextStory


class StoryGenerator:
    """
    Context story generator using LLM.

    Creates stories that naturally incorporate target vocabulary
    words to reinforce learning through contextual usage.

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
        Initialize story generator.

        Args:
            llm_service: LLM service instance
            prompt_manager: Prompt manager instance
        """
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

        logger.info("StoryGenerator initialized")

    async def generate(
        self,
        words: list[str],
        theme: str | None = None,
        word_count: int = 300,
        difficulty: str = "intermediate",
        llm_config: dict[str, Any] | None = None,
    ) -> ContextStory | None:
        """
        Generate a contextual story containing target words.

        Args:
            words: List of target words
            theme: Story theme (optional, auto-selected if not provided)
            word_count: Target word count for the story
            difficulty: Difficulty level
            llm_config: LLM configuration

        Returns:
            ContextStory object or None if generation fails

        Raises:
            ValueError: If words list is empty
        """
        # Validate input
        if not words:
            raise ValueError("Words list cannot be empty")

        word_count = max(100, min(1000, word_count))  # Clamp to [100, 1000]

        logger.info(f"Generating story for {len(words)} words, ~{word_count} words")

        # Prepare LLM config
        llm_config = llm_config or {}
        temperature = llm_config.get("temperature", 0.7)  # Higher temp for creativity
        max_tokens = llm_config.get("max_tokens", 2000)

        try:
            # Load prompt template
            template = self.prompt_manager.load_template("context_story")

            # Format words list
            words_str = ", ".join(words)

            # Render prompt
            system_prompt, user_prompt = template.render(
                {
                    "words": words_str,
                    "theme": theme or "",
                    "word_count": word_count,
                    "difficulty": difficulty,
                }
            )

            # Call LLM
            response = await asyncio.to_thread(
                self.llm_service.call,
                prompt=user_prompt,
                model=llm_config.get("model", self.llm_service.model),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Parse JSON response
            story_data = self._parse_llm_response(response.content)

            # Create ContextStory object
            story = ContextStory(
                title=story_data.get("title", "Vocabulary Story"),
                content=story_data.get("content", ""),
                word_count=story_data.get("word_count", 0),
                difficulty=story_data.get("difficulty", difficulty),
                target_words=story_data.get("target_words", words),
            )

            logger.info(f"Story generated: {story.title} ({story.word_count} words)")

            return story

        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return None

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
            # Extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            # Validate required fields
            if "title" not in data or "content" not in data:
                raise ValueError("Missing required fields (title or content)")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {response[:500]}")
            raise ValueError(f"Invalid JSON response: {e}") from e

    async def generate_multiple(
        self,
        words_list: list[list[str]],
        theme: str | None = None,
        word_count: int = 300,
        difficulty: str = "intermediate",
        llm_config: dict[str, Any] | None = None,
    ) -> list[ContextStory]:
        """
        Generate multiple stories for different word sets.

        Args:
            words_list: List of word lists
            theme: Story theme (optional)
            word_count: Target word count per story
            difficulty: Difficulty level
            llm_config: LLM configuration

        Returns:
            List of ContextStory objects
        """
        stories = []

        for words in words_list:
            story = await self.generate(
                words=words,
                theme=theme,
                word_count=word_count,
                difficulty=difficulty,
                llm_config=llm_config,
            )
            if story:
                stories.append(story)

        logger.info(f"Generated {len(stories)} stories")
        return stories


# Convenience function
async def generate_context_story(
    words: list[str],
    theme: str | None = None,
    word_count: int = 300,
    difficulty: str = "intermediate",
    llm_service: LLMService | None = None,
    prompt_manager: PromptManager | None = None,
) -> ContextStory | None:
    """
    Convenience function to generate context story.

    Args:
        words: List of target words
        theme: Story theme (optional)
        word_count: Target word count
        difficulty: Difficulty level
        llm_service: LLM service (required)
        prompt_manager: Prompt manager (required)

    Returns:
        ContextStory object or None
    """
    if llm_service is None or prompt_manager is None:
        raise ValueError("llm_service and prompt_manager are required")

    generator = StoryGenerator(llm_service, prompt_manager)
    return await generator.generate(words, theme, word_count, difficulty)
