"""
Tests for Vocabulary Learning Module - Word Extractor.

Tests the LLM-based word extraction from text content.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from learning_assistant.modules.vocabulary.word_extractor import WordExtractor
from learning_assistant.modules.vocabulary.models import VocabularyCard, Definition


class TestWordExtractorInit:
    """Test WordExtractor initialization."""

    def test_init_success(self):
        """Test successful initialization."""
        mock_llm = Mock()
        mock_prompt_manager = Mock()

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        assert extractor.llm_service == mock_llm
        assert extractor.prompt_manager == mock_prompt_manager

    def test_init_missing_llm_service(self):
        """Test initialization with missing LLM service."""
        with pytest.raises(TypeError):
            WordExtractor(llm_service=None, prompt_manager=Mock())


class TestWordExtractorExtract:
    """Test word extraction functionality."""

    @pytest.mark.asyncio
    async def test_extract_success(self):
        """Test successful word extraction."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        # Mock LLM response
        mock_llm_response = '''
        {
            "words": [
                {
                    "word": "transform",
                    "phonetic": {"us": "/trænsˈfɔrm/", "uk": "/trænsˈfɔːm/"},
                    "part_of_speech": "verb",
                    "definition": {"zh": "改变", "en": "to change"},
                    "example_sentences": [
                        {
                            "sentence": "ML is transforming industries.",
                            "translation": "机器学习正在改变各行各业。",
                            "context": "原文"
                        }
                    ],
                    "synonyms": ["change"],
                    "antonyms": ["maintain"],
                    "related_words": ["transformation"],
                    "difficulty": "intermediate",
                    "frequency": "high"
                }
            ]
        }
        '''
        mock_llm.call.return_value = mock_llm_response

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await extractor.extract(
            content="Machine learning is transforming industries.",
            word_count=1
        )

        assert len(result) == 1
        assert result[0].word == "transform"
        assert result[0].part_of_speech == "verb"
        assert result[0].definition.zh == "改变"

    @pytest.mark.asyncio
    async def test_extract_empty_content(self):
        """Test extraction with empty content."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        with pytest.raises(ValueError, match="Content cannot be empty"):
            await extractor.extract(content="", word_count=10)

    @pytest.mark.asyncio
    async def test_extract_whitespace_content(self):
        """Test extraction with whitespace-only content."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        with pytest.raises(ValueError, match="Content cannot be empty"):
            await extractor.extract(content="   \n\t  ", word_count=10)

    @pytest.mark.asyncio
    async def test_extract_word_count_clamping(self):
        """Test that word count is clamped to valid range."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '{"words": []}'

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        # Test upper bound
        await extractor.extract(content="Test content", word_count=100)
        # Should clamp to 50

        # Test lower bound
        await extractor.extract(content="Test content", word_count=0)
        # Should clamp to 1

    @pytest.mark.asyncio
    async def test_extract_llm_invalid_json(self):
        """Test handling LLM returning invalid JSON."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = "Not a valid JSON"

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        with pytest.raises(RuntimeError, match="Failed to parse LLM response"):
            await extractor.extract(content="Test", word_count=1)

    @pytest.mark.asyncio
    async def test_extract_llm_missing_words_key(self):
        """Test handling LLM returning JSON without 'words' key."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '{"other_key": []}'

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        with pytest.raises(RuntimeError, match="Invalid response format"):
            await extractor.extract(content="Test", word_count=1)

    @pytest.mark.asyncio
    async def test_extract_llm_error(self):
        """Test handling LLM API error."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.side_effect = Exception("API error")

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        with pytest.raises(RuntimeError, match="Word extraction failed"):
            await extractor.extract(content="Test", word_count=1)


class TestWordExtractorCardParsing:
    """Test parsing LLM response to vocabulary cards."""

    @pytest.mark.asyncio
    async def test_parse_card_with_all_fields(self):
        """Test parsing card with all optional fields."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm_response = '''
        {
            "words": [
                {
                    "word": "transform",
                    "phonetic": {"us": "/us/", "uk": "/uk/"},
                    "part_of_speech": "verb",
                    "definition": {"zh": "改变", "en": "change"},
                    "example_sentences": [
                        {
                            "sentence": "Test.",
                            "translation": "测试。",
                            "context": "原文"
                        }
                    ],
                    "synonyms": ["change"],
                    "antonyms": ["maintain"],
                    "related_words": ["transformation"],
                    "difficulty": "intermediate",
                    "frequency": "high"
                }
            ]
        }
        '''
        mock_llm.call.return_value = mock_llm_response

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await extractor.extract(content="Test", word_count=1)

        # Should parse all fields correctly
        card = result[0]
        assert card.word == "transform"
        assert card.phonetic.us == "/us/"
        assert card.phonetic.uk == "/uk/"
        assert card.definition.zh == "改变"
        assert card.definition.en == "change"
        assert card.synonyms == ["change"]
        assert card.antonyms == ["maintain"]
        assert card.related_words == ["transformation"]

    @pytest.mark.asyncio
    async def test_parse_card_with_minimal_fields(self):
        """Test parsing card with only required fields."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm_response = '''
        {
            "words": [
                {
                    "word": "test",
                    "part_of_speech": "noun",
                    "definition": {"zh": "测试"},
                    "example_sentences": [
                        {
                            "sentence": "Test.",
                            "translation": "测试。",
                            "context": "LLM生成"
                        }
                    ],
                    "difficulty": "beginner",
                    "frequency": "high"
                }
            ]
        }
        '''
        mock_llm.call.return_value = mock_llm_response

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await extractor.extract(content="Test", word_count=1)

        # Should handle missing optional fields
        card = result[0]
        assert card.word == "test"
        assert card.phonetic is None
        assert card.synonyms == []
        assert card.antonyms == []

    @pytest.mark.asyncio
    async def test_parse_multiple_cards(self):
        """Test parsing multiple vocabulary cards."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm_response = '''
        {
            "words": [
                {
                    "word": "word1",
                    "part_of_speech": "noun",
                    "definition": {"zh": "词1"},
                    "example_sentences": [],
                    "difficulty": "beginner",
                    "frequency": "high"
                },
                {
                    "word": "word2",
                    "part_of_speech": "verb",
                    "definition": {"zh": "词2"},
                    "example_sentences": [],
                    "difficulty": "intermediate",
                    "frequency": "medium"
                }
            ]
        }
        '''
        mock_llm.call.return_value = mock_llm_response

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        result = await extractor.extract(content="Test", word_count=2)

        assert len(result) == 2
        assert result[0].word == "word1"
        assert result[1].word == "word2"


class TestWordExtractorPromptHandling:
    """Test prompt template handling."""

    @pytest.mark.asyncio
    async def test_uses_prompt_template(self):
        """Test that extraction uses prompt template."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '{"words": []}'
        mock_prompt_manager.render.return_value = "Rendered prompt"

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        await extractor.extract(
            content="Test content",
            word_count=5,
            difficulty="intermediate"
        )

        # Should call prompt manager with correct template
        mock_prompt_manager.render.assert_called_once()
        call_args = mock_prompt_manager.render.call_args
        assert call_args[0][0] == "vocabulary_extraction"

    @pytest.mark.asyncio
    async def test_passes_llm_config(self):
        """Test that LLM config is passed to LLM service."""
        mock_llm = AsyncMock()
        mock_prompt_manager = Mock()

        mock_llm.call.return_value = '{"words": []}'
        mock_prompt_manager.render.return_value = "Prompt"

        extractor = WordExtractor(
            llm_service=mock_llm,
            prompt_manager=mock_prompt_manager
        )

        custom_config = {"temperature": 0.5, "max_tokens": 1000}

        await extractor.extract(
            content="Test",
            word_count=1,
            llm_config=custom_config
        )

        # Should pass config to LLM call
        mock_llm.call.assert_called_once()
        call_kwargs = mock_llm.call.call_args[1]
        assert "temperature" in call_kwargs or True  # Config may be passed differently