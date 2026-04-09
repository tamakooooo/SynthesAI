"""
Tests for Vocabulary Learning Module - Full Module Integration.

Tests the complete vocabulary learning workflow.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from learning_assistant.modules.vocabulary import VocabularyLearningModule
from learning_assistant.modules.vocabulary.models import (
    VocabularyCard,
    Definition,
    ExampleSentence,
    Phonetic,
    ContextStory,
)
from learning_assistant.core.event_bus import EventBus


class TestVocabularyLearningModuleInit:
    """Test module initialization."""

    def test_init_success(self):
        """Test successful module creation."""
        module = VocabularyLearningModule()

        assert module.name == "vocabulary"
        assert module.word_extractor is None
        assert module.phonetic_lookup is None
        assert module.story_generator is None

    def test_initialize_without_llm_api_key(self):
        """Test initialization fails without LLM API key."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"}
        }

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                module.initialize(config, event_bus)

    def test_initialize_with_openai_key(self):
        """Test initialization with OpenAI API key."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"}
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("learning_assistant.modules.vocabulary.LLMService"):
                module.initialize(config, event_bus)

                assert module.llm_service is not None
                assert module.word_extractor is not None
                assert module.phonetic_lookup is not None
                assert module.story_generator is not None


class TestVocabularyLearningModuleProcess:
    """Test module processing workflow."""

    @pytest.mark.asyncio
    async def test_process_success(self):
        """Test successful vocabulary extraction process."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "extraction": {"word_count": 5},
            "story": {"enabled": False}
        }

        # Mock all components
        mock_cards = [
            VocabularyCard(
                word="transform",
                part_of_speech="verb",
                definition=Definition(zh="改变"),
                example_sentences=[
                    ExampleSentence(
                        sentence="Test.",
                        translation="测试。",
                        context="LLM生成"
                    )
                ],
                difficulty="intermediate",
                frequency="high"
            )
        ]

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                # Mock word extractor
                module.word_extractor = AsyncMock()
                module.word_extractor.extract.return_value = mock_cards

                # Mock phonetic lookup
                module.phonetic_lookup = AsyncMock()
                module.phonetic_lookup.lookup.return_value = Phonetic(us="/test/")

                # Mock history manager
                module.history_manager = Mock()

                result = await module.process(
                    content="Test content",
                    word_count=5
                )

                assert result is not None
                assert len(result.vocabulary_cards) == 1
                assert result.vocabulary_cards[0].word == "transform"

    @pytest.mark.asyncio
    async def test_process_with_story(self):
        """Test process with story generation enabled."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "extraction": {"word_count": 3},
            "story": {"enabled": True}
        }

        mock_cards = [
            VocabularyCard(
                word="test",
                part_of_speech="noun",
                definition=Definition(zh="测试"),
                example_sentences=[],
                difficulty="beginner",
                frequency="high"
            )
        ]

        mock_story = ContextStory(
            title="Test Story",
            content="Test content.",
            word_count=100,
            difficulty="beginner",
            target_words=["test"]
        )

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                # Mock components
                module.word_extractor = AsyncMock()
                module.word_extractor.extract.return_value = mock_cards

                module.phonetic_lookup = AsyncMock()
                module.phonetic_lookup.lookup.return_value = None

                module.story_generator = AsyncMock()
                module.story_generator.generate.return_value = mock_story

                module.history_manager = Mock()

                result = await module.process(
                    content="Test",
                    word_count=3,
                    generate_story=True
                )

                assert result is not None
                assert result.context_story is not None
                assert result.context_story.title == "Test Story"

    @pytest.mark.asyncio
    async def test_process_empty_content(self):
        """Test process with empty content."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "story": {"enabled": False}
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                with pytest.raises(ValueError, match="Content cannot be empty"):
                    await module.process(content="", word_count=5)

    @pytest.mark.asyncio
    async def test_process_phonetic_enrichment(self):
        """Test that phonetics are enriched when missing."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "story": {"enabled": False}
        }

        # Card without phonetic
        mock_card = VocabularyCard(
            word="test",
            part_of_speech="noun",
            definition=Definition(zh="测试"),
            example_sentences=[],
            difficulty="beginner",
            frequency="high",
            phonetic=None  # No phonetic
        )

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                module.word_extractor = AsyncMock()
                module.word_extractor.extract.return_value = [mock_card]

                # Phonetic lookup should be called
                module.phonetic_lookup = AsyncMock()
                module.phonetic_lookup.lookup.return_value = Phonetic(us="/test/")

                module.history_manager = Mock()

                result = await module.process(content="Test", word_count=1)

                # Phonetic should be enriched
                assert result.vocabulary_cards[0].phonetic is not None
                assert result.vocabulary_cards[0].phonetic.us == "/test/"


class TestVocabularyLearningModuleExport:
    """Test export functionality."""

    @pytest.mark.asyncio
    async def test_export_to_markdown(self, tmp_path):
        """Test exporting vocabulary to Markdown."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "story": {"enabled": False},
            "output": {"directory": str(tmp_path)}
        }

        mock_cards = [
            VocabularyCard(
                word="test",
                part_of_speech="noun",
                definition=Definition(zh="测试"),
                example_sentences=[],
                difficulty="beginner",
                frequency="high"
            )
        ]

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                module.word_extractor = AsyncMock()
                module.word_extractor.extract.return_value = mock_cards

                module.phonetic_lookup = AsyncMock()
                module.phonetic_lookup.lookup.return_value = None

                module.history_manager = Mock()

                # Mock exporter
                module.exporter = Mock()
                module.exporter.export.return_value = tmp_path / "vocab.md"

                result = await module.process(
                    content="Test",
                    word_count=1,
                    output_dir=str(tmp_path)
                )

                # Should export to file
                assert result is not None


class TestVocabularyLearningModuleEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_process_word_extractor_error(self):
        """Test handling word extractor error."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "story": {"enabled": False}
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                module.word_extractor = AsyncMock()
                module.word_extractor.extract.side_effect = Exception("Extraction failed")

                with pytest.raises(Exception, match="Extraction failed"):
                    await module.process(content="Test", word_count=1)

    @pytest.mark.asyncio
    async def test_process_story_generation_disabled(self):
        """Test that story generation is skipped when disabled."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "story": {"enabled": False}
        }

        mock_cards = [
            VocabularyCard(
                word="test",
                part_of_speech="noun",
                definition=Definition(zh="测试"),
                example_sentences=[],
                difficulty="beginner",
                frequency="high"
            )
        ]

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                module.word_extractor = AsyncMock()
                module.word_extractor.extract.return_value = mock_cards

                module.phonetic_lookup = AsyncMock()
                module.phonetic_lookup.lookup.return_value = None

                module.story_generator = AsyncMock()
                module.history_manager = Mock()

                result = await module.process(
                    content="Test",
                    word_count=1,
                    generate_story=False
                )

                # Story generator should not be called
                module.story_generator.generate.assert_not_called()
                assert result.context_story is None

    @pytest.mark.asyncio
    async def test_process_multiple_difficulty_levels(self):
        """Test processing with different difficulty levels."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "story": {"enabled": False}
        }

        mock_cards_beginner = [
            VocabularyCard(
                word="test",
                part_of_speech="noun",
                definition=Definition(zh="测试"),
                example_sentences=[],
                difficulty="beginner",
                frequency="high"
            )
        ]

        mock_cards_advanced = [
            VocabularyCard(
                word="sophisticated",
                part_of_speech="adjective",
                definition=Definition(zh="复杂的"),
                example_sentences=[],
                difficulty="advanced",
                frequency="low"
            )
        ]

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                module.word_extractor = AsyncMock()
                module.phonetic_lookup = AsyncMock()
                module.phonetic_lookup.lookup.return_value = None
                module.history_manager = Mock()

                # Test beginner
                module.word_extractor.extract.return_value = mock_cards_beginner
                result = await module.process(
                    content="Test",
                    word_count=1,
                    difficulty="beginner"
                )
                assert result.vocabulary_cards[0].difficulty == "beginner"

                # Test advanced
                module.word_extractor.extract.return_value = mock_cards_advanced
                result = await module.process(
                    content="Test",
                    word_count=1,
                    difficulty="advanced"
                )
                assert result.vocabulary_cards[0].difficulty == "advanced"


class TestVocabularyLearningModuleIntegration:
    """Integration tests with real components (mocked LLM)."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete vocabulary extraction workflow."""
        module = VocabularyLearningModule()
        event_bus = EventBus()

        config = {
            "llm": {"provider": "openai"},
            "extraction": {"word_count": 2},
            "story": {"enabled": True, "default_word_count": 200}
        }

        # Mock complete workflow
        mock_cards = [
            VocabularyCard(
                word="transform",
                phonetic=Phonetic(us="/trænsˈfɔrm/", uk="/trænsˈfɔːm/"),
                part_of_speech="verb",
                definition=Definition(zh="改变", en="to change"),
                example_sentences=[
                    ExampleSentence(
                        sentence="ML is transforming industries.",
                        translation="机器学习正在改变各行各业。",
                        context="原文"
                    )
                ],
                synonyms=["change", "convert"],
                antonyms=["maintain"],
                related_words=["transformation"],
                difficulty="intermediate",
                frequency="high"
            ),
            VocabularyCard(
                word="revolution",
                phonetic=Phonetic(us="/ˌrevəˈluːʃn/"),
                part_of_speech="noun",
                definition=Definition(zh="革命"),
                example_sentences=[],
                difficulty="intermediate",
                frequency="medium"
            )
        ]

        mock_story = ContextStory(
            title="The Transformative Revolution",
            content="In recent years, a revolution in machine learning has been transforming industries...",
            word_count=200,
            difficulty="intermediate",
            target_words=["transform", "revolution"]
        )

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(module, '_init_components'):
                module.initialize(config, event_bus)

                # Setup all mocks
                module.word_extractor = AsyncMock()
                module.word_extractor.extract.return_value = mock_cards

                module.phonetic_lookup = AsyncMock()
                module.phonetic_lookup.lookup.return_value = None

                module.story_generator = AsyncMock()
                module.story_generator.generate.return_value = mock_story

                module.history_manager = Mock()

                # Execute full workflow
                result = await module.process(
                    content="Machine learning is transforming industries and causing a revolution.",
                    word_count=2,
                    difficulty="intermediate",
                    generate_story=True
                )

                # Verify complete result
                assert result is not None
                assert len(result.vocabulary_cards) == 2
                assert result.context_story is not None

                # Check statistics
                assert result.statistics["total_words"] == 2
                assert "difficulty_distribution" in result.statistics

                # Verify history was saved
                module.history_manager.save_record.assert_called_once()