"""
Unit tests for visual_adapter module.
"""

from datetime import datetime
from typing import Any

import pytest

from learning_assistant.modules.vocabulary.models import (
    ContextStory,
    Definition,
    ExampleSentence,
    Phonetic,
    VocabularyCard,
    VocabularyOutput,
)
from learning_assistant.modules.vocabulary.visual_adapter import (
    vocabulary_output_to_card_data,
)


class TestVocabularyOutputToCardData:
    """Test vocabulary_output_to_card_data adapter function."""

    def _create_mock_vocabulary_card(
        self,
        word: str = "innovative",
        pos: str = "adj",
        zh_def: str = "创新的",
        phonetic_us: str = "/ˈɪnəveɪtɪv/",
    ) -> VocabularyCard:
        """Create a mock VocabularyCard for testing."""
        return VocabularyCard(
            word=word,
            phonetic=Phonetic(us=phonetic_us, uk=None),
            part_of_speech=pos,
            definition=Definition(zh=zh_def, en=None),
            example_sentences=[
                ExampleSentence(
                    sentence="This is an innovative approach.",
                    translation="这是一个创新的方法。",
                    context="LLM生成",
                    source=None,
                ),
            ],
            synonyms=["creative", "novel"],
            antonyms=["traditional"],
            related_words=["innovation", "innovate"],
            difficulty="intermediate",
            frequency="medium",
            memory_status="new",
            created_at=datetime.now(),
            last_reviewed=None,
            review_count=0,
        )

    def _create_mock_vocabulary_output(
        self,
        num_words: int = 5,
        with_story: bool = True,
    ) -> VocabularyOutput:
        """Create a mock VocabularyOutput for testing."""
        # Create vocabulary cards
        cards = [
            self._create_mock_vocabulary_card(
                word=f"word{i}",
                pos="adj",
                zh_def=f"定义{i}",
            )
            for i in range(num_words)
        ]

        # Create context story
        story = None
        if with_story:
            story = ContextStory(
                title="Test Story",
                content="This is a test story with some words to provide context. "
                "The story contains multiple vocabulary words in a meaningful context.",
                word_count=100,
                difficulty="intermediate",
                target_words=["word0", "word1", "word2"],
            )

        # Create statistics
        statistics = {
            "total_words": num_words,
            "difficulty_distribution": {
                "beginner": 1,
                "intermediate": 3,
                "advanced": 1,
            },
            "frequency_distribution": {
                "high": 2,
                "medium": 2,
                "low": 1,
            },
            "part_of_speech_distribution": {
                "adj": 3,
                "noun": 2,
            },
        }

        return VocabularyOutput(
            vocabulary_cards=cards,
            context_story=story,
            statistics=statistics,
        )

    def test_adapter_with_full_data(self) -> None:
        """Test adapter with complete VocabularyOutput."""
        output = self._create_mock_vocabulary_output(num_words=5, with_story=True)
        card_data = vocabulary_output_to_card_data(output)

        # Verify title
        assert card_data["title"].startswith("单词学习 ·")
        assert "word0" in card_data["title"]

        # Verify summary (story content)
        assert card_data["summary"] != ""
        assert "test story" in card_data["summary"].lower()

        # Verify key_points format
        assert len(card_data["key_points"]) == 5
        assert card_data["key_points"][0] == "word0 (adj): 定义0"

        # Verify tags
        assert "vocabulary" in card_data["tags"]
        assert "5 words" in card_data["tags"]
        assert "intermediate" in card_data["tags"]

        # Verify other fields
        assert card_data["key_concepts"] is None
        assert card_data["source"] == "SynthesAI"
        assert card_data["url"] is None

    def test_adapter_word_limit(self) -> None:
        """Test adapter limits words to 10."""
        # Create output with 15 words
        output = self._create_mock_vocabulary_output(num_words=15, with_story=False)
        card_data = vocabulary_output_to_card_data(output)

        # Should only show 10 words
        assert len(card_data["key_points"]) == 10
        assert card_data["key_points"][0] == "word0 (adj): 定义0"

        # Total words tag should show 15
        assert "15 words" in card_data["tags"]

    def test_adapter_with_missing_story(self) -> None:
        """Test adapter when context story is None."""
        output = self._create_mock_vocabulary_output(num_words=3, with_story=False)
        card_data = vocabulary_output_to_card_data(output)

        # Summary should be empty
        assert card_data["summary"] == ""

        # Other fields should still work
        assert len(card_data["key_points"]) == 3
        assert card_data["title"].startswith("单词学习 ·")

    def test_adapter_truncates_long_story(self) -> None:
        """Test adapter truncates story longer than 150 chars."""
        # Create output with long story
        cards = [self._create_mock_vocabulary_card()]
        long_story = ContextStory(
            title="Long Story",
            content="This is a very long story that exceeds 150 characters limit. "
            "The content should be truncated with ellipsis when displayed in the visual card. "
            "We need to ensure that the truncation logic works correctly and adds '...' at the end.",
            word_count=200,
            difficulty="intermediate",
            target_words=["innovative"],
        )

        output = VocabularyOutput(
            vocabulary_cards=cards,
            context_story=long_story,
            statistics={"total_words": 1, "difficulty_distribution": {"intermediate": 1}},
        )

        card_data = vocabulary_output_to_card_data(output)

        # Summary should be truncated
        assert len(card_data["summary"]) <= 153  # 150 + "..."
        assert card_data["summary"].endswith("...")

    def test_adapter_with_no_cards(self) -> None:
        """Test adapter when vocabulary_cards list is empty."""
        output = VocabularyOutput(
            vocabulary_cards=[],
            context_story=None,
            statistics={"total_words": 0, "difficulty_distribution": {}},
        )

        card_data = vocabulary_output_to_card_data(output)

        # Should have default title
        assert card_data["title"] == "单词学习 · 词汇卡片"

        # Should have empty key_points
        assert len(card_data["key_points"]) == 0

        # Should have 0 words tag
        assert "0 words" in card_data["tags"]

    def test_adapter_phonetic_format(self) -> None:
        """Test adapter includes phonetic in word format (brief display)."""
        card_with_phonetic = self._create_mock_vocabulary_card(
            word="example",
            pos="noun",
            zh_def="例子",
            phonetic_us="/ɪgˈzæmpəl/",
        )

        output = VocabularyOutput(
            vocabulary_cards=[card_with_phonetic],
            context_story=None,
            statistics={"total_words": 1, "difficulty_distribution": {"intermediate": 1}},
        )

        card_data = vocabulary_output_to_card_data(output)

        # Key point format: word (pos): definition
        assert card_data["key_points"][0] == "example (noun): 例子"

        # Note: Phonetic not shown in brief format (only in detailed display)

    def test_adapter_statistics_to_tags(self) -> None:
        """Test adapter converts statistics to meaningful tags."""
        output = VocabularyOutput(
            vocabulary_cards=[self._create_mock_vocabulary_card()],
            context_story=None,
            statistics={
                "total_words": 10,
                "difficulty_distribution": {
                    "beginner": 2,
                    "intermediate": 6,  # Primary difficulty
                    "advanced": 2,
                },
            },
        )

        card_data = vocabulary_output_to_card_data(output)

        # Should find primary difficulty (highest count)
        assert "intermediate" in card_data["tags"]
        assert "10 words" in card_data["tags"]

    def test_adapter_preserves_word_order(self) -> None:
        """Test adapter preserves original word order."""
        # Create cards in specific order
        words = ["apple", "banana", "cherry", "date", "elderberry"]
        cards = [
            self._create_mock_vocabulary_card(word=w, pos="noun", zh_def=f"{w}定义")
            for w in words
        ]

        output = VocabularyOutput(
            vocabulary_cards=cards,
            context_story=None,
            statistics={"total_words": 5, "difficulty_distribution": {"intermediate": 5}},
        )

        card_data = vocabulary_output_to_card_data(output)

        # Key points should preserve order
        assert card_data["key_points"][0] == "apple (noun): apple定义"
        assert card_data["key_points"][1] == "banana (noun): banana定义"
        assert card_data["key_points"][4] == "elderberry (noun): elderberry定义"


class TestVisualAdapterIntegration:
    """Integration tests for visual adapter with VisualCardGenerator."""

    @pytest.mark.skip(reason="Requires VisualCardGenerator setup")
    def test_adapter_output_compatible_with_visual_generator(self) -> None:
        """Test that adapter output can be used with VisualCardGenerator."""
        # This test would require initializing VisualCardGenerator
        # and verifying generate_card_html() accepts the output
        pass

    @pytest.mark.skip(reason="Requires Playwright for PNG rendering")
    def test_adapter_output_generates_valid_html(self) -> None:
        """Test that adapter output generates valid HTML template."""
        # This test would require VisualCardGenerator.generate_card_html()
        # and checking the HTML structure
        pass