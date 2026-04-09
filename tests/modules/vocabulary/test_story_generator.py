"""
Tests for Vocabulary Learning Module - Story Generator.

Tests the contextual story generation for vocabulary retention.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from learning_assistant.modules.vocabulary.story_generator import StoryGenerator
from learning_assistant.modules.vocabulary.models import ContextStory


class TestStoryGeneratorInit:
    """Test StoryGenerator initialization."""

    def test_init_success(self):
        """Test successful initialization."""
        mock_llm = Mock()
        mock_prompt_manager = Mock()

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        assert generator.llm_service == mock_llm
        assert generator.prompt_manager == mock_prompt_manager


class TestStoryGeneratorGenerate:
    """Test story generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful story generation."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm_response = '''
        {
            "title": "The Transformative Power",
            "content": "In recent years, machine learning has been transforming industries across the globe...",
            "word_count": 300,
            "difficulty": "intermediate",
            "target_words": ["transform", "revolution", "innovation"]
        }
        '''
        mock_llm.call.return_value = mock_llm_response
        mock_prompt_manager.render.return_value = "Rendered prompt"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await generator.generate(
            words=["transform", "revolution", "innovation"],
            word_count=300,
            difficulty="intermediate"
        )

        assert result is not None
        assert result.title == "The Transformative Power"
        assert "machine learning" in result.content
        assert result.word_count == 300
        assert len(result.target_words) == 3

    @pytest.mark.asyncio
    async def test_generate_empty_words_list(self):
        """Test generation with empty words list."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        with pytest.raises(ValueError, match="Words list cannot be empty"):
            await generator.generate(words=[], word_count=300)

    @pytest.mark.asyncio
    async def test_generate_word_count_clamping(self):
        """Test that word count is clamped to valid range."""
        mock_llm = AsyncMock()
        mock_llm.call.return_value = '{"title": "Test", "content": "Content", "word_count": 100}'
        mock_prompt_manager = Mock()
        mock_prompt_manager.render.return_value = "Prompt"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        # Test upper bound (should clamp to 1000)
        await generator.generate(words=["test"], word_count=2000)

        # Test lower bound (should clamp to 100)
        await generator.generate(words=["test"], word_count=50)

    @pytest.mark.asyncio
    async def test_generate_with_custom_theme(self):
        """Test generation with custom theme."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '''
        {
            "title": "Space Adventure",
            "content": "The spaceship transformed into a new form...",
            "word_count": 200,
            "difficulty": "intermediate",
            "target_words": ["transform"]
        }
        '''
        mock_prompt_manager.render.return_value = "Prompt with theme"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await generator.generate(
            words=["transform"],
            theme="Science Fiction",
            word_count=200
        )

        assert result is not None
        assert result.title == "Space Adventure"

    @pytest.mark.asyncio
    async def test_generate_llm_invalid_json(self):
        """Test handling LLM returning invalid JSON."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = "Not a valid JSON"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await generator.generate(words=["test"], word_count=300)

        # Should return None on parse error
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_llm_error(self):
        """Test handling LLM API error."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.side_effect = Exception("API error")

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await generator.generate(words=["test"], word_count=300)

        # Should return None on error
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_llm_missing_fields(self):
        """Test handling LLM returning JSON with missing required fields."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        # Missing 'content' field
        mock_llm.call.return_value = '{"title": "Test"}'

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await generator.generate(words=["test"], word_count=300)

        # Should return None when required fields are missing
        assert result is None


class TestStoryGeneratorPromptHandling:
    """Test prompt template handling."""

    @pytest.mark.asyncio
    async def test_uses_prompt_template(self):
        """Test that generation uses prompt template."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '''
        {
            "title": "Test",
            "content": "Content",
            "word_count": 100,
            "difficulty": "intermediate",
            "target_words": ["test"]
        }
        '''
        mock_prompt_manager.render.return_value = "Rendered prompt"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        await generator.generate(
            words=["transform", "change"],
            word_count=300,
            difficulty="advanced"
        )

        # Should call prompt manager
        mock_prompt_manager.render.assert_called_once()
        call_args = mock_prompt_manager.render.call_args
        assert call_args[0][0] == "context_story"

    @pytest.mark.asyncio
    async def test_passes_llm_config(self):
        """Test that LLM config is passed to LLM service."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '''
        {
            "title": "Test",
            "content": "Content",
            "word_count": 100,
            "difficulty": "intermediate",
            "target_words": ["test"]
        }
        '''
        mock_prompt_manager.render.return_value = "Prompt"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        custom_config = {"temperature": 0.7, "max_tokens": 1500}

        await generator.generate(
            words=["test"],
            word_count=300,
            llm_config=custom_config
        )

        # Should call LLM
        mock_llm.call.assert_called_once()


class TestStoryGeneratorEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_generate_single_word(self):
        """Test generating story with single word."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '''
        {
            "title": "A Story About Transform",
            "content": "Once upon a time, there was a transformation...",
            "word_count": 100,
            "difficulty": "beginner",
            "target_words": ["transform"]
        }
        '''
        mock_prompt_manager.render.return_value = "Prompt"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await generator.generate(words=["transform"], word_count=100)

        assert result is not None
        assert len(result.target_words) == 1
        assert "transform" in result.target_words

    @pytest.mark.asyncio
    async def test_generate_many_words(self):
        """Test generating story with many words."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        words = [f"word{i}" for i in range(10)]

        mock_llm.call.return_value = '''
        {
            "title": "Complex Story",
            "content": "A story with many words...",
            "word_count": 500,
            "difficulty": "advanced",
            "target_words": []
        }
        '''
        mock_prompt_manager.render.return_value = "Prompt"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await generator.generate(words=words, word_count=500)

        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_different_difficulties(self):
        """Test generating stories with different difficulty levels."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '''
        {
            "title": "Test",
            "content": "Content",
            "word_count": 100,
            "target_words": ["test"]
        }
        '''
        mock_prompt_manager.render.return_value = "Prompt"

        generator = StoryGenerator(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        # Test each difficulty level
        for difficulty in ["beginner", "intermediate", "advanced"]:
            result = await generator.generate(
                words=["test"],
                word_count=100,
                difficulty=difficulty
            )

            assert result is not None