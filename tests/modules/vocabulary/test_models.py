"""
Tests for Vocabulary Learning Module - Models.

Tests the data models for vocabulary cards, phonetics, definitions, etc.
"""

import pytest
from learning_assistant.modules.vocabulary.models import (
    Phonetic,
    Definition,
    ExampleSentence,
    VocabularyCard,
    ContextStory,
    VocabularyQuiz,
    VocabularyOutput,
)


class TestPhonetic:
    """Test Phonetic model."""

    def test_phonetic_creation_with_both(self):
        """Test creating Phonetic with both US and UK transcriptions."""
        phonetic = Phonetic(us="/trænsˈfɔrm/", uk="/trænsˈfɔːm/")

        assert phonetic.us == "/trænsˈfɔrm/"
        assert phonetic.uk == "/trænsˈfɔːm/"

    def test_phonetic_creation_with_us_only(self):
        """Test creating Phonetic with US transcription only."""
        phonetic = Phonetic(us="/test/", uk=None)

        assert phonetic.us == "/test/"
        assert phonetic.uk is None

    def test_phonetic_creation_with_uk_only(self):
        """Test creating Phonetic with UK transcription only."""
        phonetic = Phonetic(us=None, uk="/test/")

        assert phonetic.us is None
        assert phonetic.uk == "/test/"

    def test_phonetic_to_dict(self):
        """Test converting Phonetic to dictionary."""
        phonetic = Phonetic(us="/us/", uk="/uk/")
        result = phonetic.to_dict()

        assert result == {"us": "/us/", "uk": "/uk/"}

    def test_phonetic_from_dict(self):
        """Test creating Phonetic from dictionary."""
        data = {"us": "/us/", "uk": "/uk/"}
        phonetic = Phonetic.from_dict(data)

        assert phonetic.us == "/us/"
        assert phonetic.uk == "/uk/"


class TestDefinition:
    """Test Definition model."""

    def test_definition_creation_with_both(self):
        """Test creating Definition with both Chinese and English."""
        definition = Definition(zh="改变，转变", en="to change completely")

        assert definition.zh == "改变，转变"
        assert definition.en == "to change completely"

    def test_definition_creation_with_zh_only(self):
        """Test creating Definition with Chinese only."""
        definition = Definition(zh="测试", en=None)

        assert definition.zh == "测试"
        assert definition.en is None

    def test_definition_to_dict(self):
        """Test converting Definition to dictionary."""
        definition = Definition(zh="测试", en="test")
        result = definition.to_dict()

        assert result == {"zh": "测试", "en": "test"}

    def test_definition_from_dict(self):
        """Test creating Definition from dictionary."""
        data = {"zh": "测试", "en": "test"}
        definition = Definition.from_dict(data)

        assert definition.zh == "测试"
        assert definition.en == "test"


class TestExampleSentence:
    """Test ExampleSentence model."""

    def test_example_sentence_creation(self):
        """Test creating ExampleSentence."""
        example = ExampleSentence(
            sentence="ML is transforming industries.",
            translation="机器学习正在改变各行各业。",
            context="原文提取"
        )

        assert example.sentence == "ML is transforming industries."
        assert example.translation == "机器学习正在改变各行各业。"
        assert example.context == "原文提取"

    def test_example_sentence_to_dict(self):
        """Test converting ExampleSentence to dictionary."""
        example = ExampleSentence(
            sentence="Test sentence.",
            translation="测试句子。",
            context="LLM生成"
        )
        result = example.to_dict()

        assert result == {
            "sentence": "Test sentence.",
            "translation": "测试句子。",
            "context": "LLM生成"
        }

    def test_example_sentence_from_dict(self):
        """Test creating ExampleSentence from dictionary."""
        data = {
            "sentence": "Test.",
            "translation": "测试。",
            "context": "原文"
        }
        example = ExampleSentence.from_dict(data)

        assert example.sentence == "Test."
        assert example.translation == "测试。"
        assert example.context == "原文"


class TestVocabularyCard:
    """Test VocabularyCard model."""

    def test_vocabulary_card_creation_minimal(self):
        """Test creating VocabularyCard with minimal fields."""
        card = VocabularyCard(
            word="test",
            part_of_speech="noun",
            definition=Definition(zh="测试"),
            example_sentences=[
                ExampleSentence(
                    sentence="This is a test.",
                    translation="这是一个测试。",
                    context="LLM生成"
                )
            ],
            difficulty="intermediate",
            frequency="high"
        )

        assert card.word == "test"
        assert card.part_of_speech == "noun"
        assert card.definition.zh == "测试"
        assert len(card.example_sentences) == 1
        assert card.difficulty == "intermediate"
        assert card.frequency == "high"
        assert card.phonetic is None
        assert card.synonyms == []
        assert card.antonyms == []

    def test_vocabulary_card_creation_full(self):
        """Test creating VocabularyCard with all fields."""
        card = VocabularyCard(
            word="transform",
            phonetic=Phonetic(us="/trænsˈfɔrm/", uk="/trænsˈfɔːm/"),
            part_of_speech="verb",
            definition=Definition(zh="改变", en="to change"),
            example_sentences=[
                ExampleSentence(
                    sentence="Test 1.",
                    translation="测试1。",
                    context="原文"
                )
            ],
            synonyms=["change", "convert"],
            antonyms=["maintain"],
            related_words=["transformation"],
            difficulty="intermediate",
            frequency="high"
        )

        assert card.word == "transform"
        assert card.phonetic.us == "/trænsˈfɔrm/"
        assert card.definition.zh == "改变"
        assert card.synonyms == ["change", "convert"]
        assert card.antonyms == ["maintain"]
        assert card.related_words == ["transformation"]

    def test_vocabulary_card_to_dict(self):
        """Test converting VocabularyCard to dictionary."""
        card = VocabularyCard(
            word="test",
            part_of_speech="noun",
            definition=Definition(zh="测试"),
            example_sentences=[],
            difficulty="beginner",
            frequency="high"
        )
        result = card.to_dict()

        assert result["word"] == "test"
        assert result["part_of_speech"] == "noun"
        assert result["definition"]["zh"] == "测试"
        assert result["difficulty"] == "beginner"

    def test_vocabulary_card_from_dict(self):
        """Test creating VocabularyCard from dictionary."""
        data = {
            "word": "test",
            "phonetic": {"us": "/test/", "uk": None},
            "part_of_speech": "noun",
            "definition": {"zh": "测试", "en": "test"},
            "example_sentences": [
                {
                    "sentence": "Test.",
                    "translation": "测试。",
                    "context": "原文"
                }
            ],
            "synonyms": ["exam"],
            "antonyms": [],
            "related_words": ["testing"],
            "difficulty": "intermediate",
            "frequency": "high"
        }
        card = VocabularyCard.from_dict(data)

        assert card.word == "test"
        assert card.phonetic.us == "/test/"
        assert card.definition.zh == "测试"
        assert len(card.example_sentences) == 1
        assert card.synonyms == ["exam"]


class TestContextStory:
    """Test ContextStory model."""

    def test_context_story_creation(self):
        """Test creating ContextStory."""
        story = ContextStory(
            title="The Transformative Power",
            content="In recent years, machine learning has been transforming...",
            word_count=300,
            difficulty="intermediate",
            target_words=["transform", "revolution", "innovation"]
        )

        assert story.title == "The Transformative Power"
        assert "machine learning" in story.content
        assert story.word_count == 300
        assert story.difficulty == "intermediate"
        assert len(story.target_words) == 3

    def test_context_story_to_dict(self):
        """Test converting ContextStory to dictionary."""
        story = ContextStory(
            title="Test Story",
            content="Test content.",
            word_count=100,
            difficulty="beginner",
            target_words=["test"]
        )
        result = story.to_dict()

        assert result["title"] == "Test Story"
        assert result["content"] == "Test content."
        assert result["word_count"] == 100

    def test_context_story_from_dict(self):
        """Test creating ContextStory from dictionary."""
        data = {
            "title": "Test",
            "content": "Content.",
            "word_count": 50,
            "difficulty": "advanced",
            "target_words": ["word1", "word2"]
        }
        story = ContextStory.from_dict(data)

        assert story.title == "Test"
        assert story.content == "Content."
        assert story.word_count == 50
        assert len(story.target_words) == 2


class TestVocabularyQuiz:
    """Test VocabularyQuiz model."""

    def test_vocabulary_quiz_creation(self):
        """Test creating VocabularyQuiz."""
        quiz = VocabularyQuiz(
            quiz_type="multiple_choice",
            question="What does 'transform' mean?",
            options=["改变", "保持", "增加", "减少"],
            correct_answer="改变",
            explanation="'Transform' means to change completely."
        )

        assert quiz.quiz_type == "multiple_choice"
        assert quiz.question == "What does 'transform' mean?"
        assert len(quiz.options) == 4
        assert quiz.correct_answer == "改变"

    def test_vocabulary_quiz_to_dict(self):
        """Test converting VocabularyQuiz to dictionary."""
        quiz = VocabularyQuiz(
            quiz_type="fill_blank",
            question="The company ___ its business model.",
            options=None,
            correct_answer="transformed",
            explanation="Past tense of transform."
        )
        result = quiz.to_dict()

        assert result["quiz_type"] == "fill_blank"
        assert result["question"] == "The company ___ its business model."
        assert result["options"] is None
        assert result["correct_answer"] == "transformed"


class TestVocabularyOutput:
    """Test VocabularyOutput model."""

    def test_vocabulary_output_creation(self):
        """Test creating VocabularyOutput."""
        output = VocabularyOutput(
            vocabulary_cards=[
                VocabularyCard(
                    word="test",
                    part_of_speech="noun",
                    definition=Definition(zh="测试"),
                    example_sentences=[],
                    difficulty="beginner",
                    frequency="high"
                )
            ],
            context_story=None,
            statistics={
                "total_words": 1,
                "difficulty_distribution": {
                    "beginner": 1,
                    "intermediate": 0,
                    "advanced": 0
                }
            }
        )

        assert len(output.vocabulary_cards) == 1
        assert output.vocabulary_cards[0].word == "test"
        assert output.context_story is None
        assert output.statistics["total_words"] == 1

    def test_vocabulary_output_to_dict(self):
        """Test converting VocabularyOutput to dictionary."""
        output = VocabularyOutput(
            vocabulary_cards=[],
            context_story=ContextStory(
                title="Test",
                content="Content",
                word_count=10,
                difficulty="beginner",
                target_words=["test"]
            ),
            statistics={"total_words": 0}
        )
        result = output.to_dict()

        assert result["vocabulary_cards"] == []
        assert result["context_story"]["title"] == "Test"
        assert result["statistics"]["total_words"] == 0