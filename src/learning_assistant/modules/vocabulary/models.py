"""
Data models for Vocabulary Learning Module.

This module defines the core data structures for vocabulary cards,
phonetics, definitions, example sentences, and related content.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Phonetic:
    """
    Phonetic representation of a word.

    Attributes:
        us: American English phonetic transcription (IPA)
        uk: British English phonetic transcription (IPA)
    """

    us: Optional[str] = None
    uk: Optional[str] = None

    def to_dict(self) -> dict[str, Optional[str]]:
        """
        Convert phonetic to dictionary.

        Returns:
            Dictionary with 'us' and 'uk' keys
        """
        return {
            "us": self.us,
            "uk": self.uk,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Phonetic":
        """
        Create Phonetic from dictionary.

        Args:
            data: Dictionary with 'us' and 'uk' keys

        Returns:
            Phonetic instance
        """
        return cls(
            us=data.get("us"),
            uk=data.get("uk"),
        )


@dataclass
class Definition:
    """
    Word definition.

    Attributes:
        zh: Chinese definition
        en: English definition (optional)
    """

    zh: str
    en: Optional[str] = None

    def to_dict(self) -> dict[str, Optional[str]]:
        """
        Convert definition to dictionary.

        Returns:
            Dictionary with 'zh' and 'en' keys
        """
        return {
            "zh": self.zh,
            "en": self.en,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Definition":
        """
        Create Definition from dictionary.

        Args:
            data: Dictionary with 'zh' and 'en' keys

        Returns:
            Definition instance
        """
        return cls(
            zh=data.get("zh", ""),
            en=data.get("en"),
        )


@dataclass
class ExampleSentence:
    """
    Example sentence for a word.

    Attributes:
        sentence: The example sentence
        translation: Chinese translation
        context: Context type ("原文提取" or "LLM生成")
        source: Source of the sentence (optional)
    """

    sentence: str
    translation: str
    context: str  # "原文提取" or "LLM生成"
    source: Optional[str] = None

    def to_dict(self) -> dict[str, Optional[str]]:
        """
        Convert example sentence to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "sentence": self.sentence,
            "translation": self.translation,
            "context": self.context,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExampleSentence":
        """
        Create ExampleSentence from dictionary.

        Args:
            data: Dictionary with sentence data

        Returns:
            ExampleSentence instance
        """
        return cls(
            sentence=data.get("sentence", ""),
            translation=data.get("translation", ""),
            context=data.get("context", "LLM生成"),
            source=data.get("source"),
        )


@dataclass
class VocabularyCard:
    """
    Complete vocabulary card.

    Contains all information about a word including phonetics,
    definitions, examples, synonyms, antonyms, and related words.

    Attributes:
        word: The target word
        phonetic: Phonetic transcription
        part_of_speech: Part of speech (noun/verb/adj/adv/etc)
        definition: Word definition
        example_sentences: List of example sentences (minimum 2)
        synonyms: List of synonyms
        antonyms: List of antonyms
        related_words: List of related words (derivatives, roots)
        difficulty: Difficulty level (beginner/intermediate/advanced)
        frequency: Word frequency (high/medium/low)
        memory_status: Memory status (new/learning/mastered)
        created_at: Creation timestamp
        last_reviewed: Last review timestamp (optional)
        review_count: Number of reviews
    """

    word: str
    phonetic: Phonetic
    part_of_speech: str
    definition: Definition
    example_sentences: list[ExampleSentence]
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)
    related_words: list[str] = field(default_factory=list)
    difficulty: str = "intermediate"  # beginner/intermediate/advanced
    frequency: str = "medium"  # high/medium/low
    memory_status: str = "new"  # new/learning/mastered
    created_at: datetime = field(default_factory=datetime.now)
    last_reviewed: Optional[datetime] = None
    review_count: int = 0

    def to_dict(self) -> dict:
        """
        Convert vocabulary card to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "word": self.word,
            "phonetic": self.phonetic.to_dict(),
            "part_of_speech": self.part_of_speech,
            "definition": self.definition.to_dict(),
            "example_sentences": [ex.to_dict() for ex in self.example_sentences],
            "synonyms": self.synonyms,
            "antonyms": self.antonyms,
            "related_words": self.related_words,
            "difficulty": self.difficulty,
            "frequency": self.frequency,
            "memory_status": self.memory_status,
            "created_at": self.created_at.isoformat(),
            "last_reviewed": (
                self.last_reviewed.isoformat() if self.last_reviewed else None
            ),
            "review_count": self.review_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VocabularyCard":
        """
        Create VocabularyCard from dictionary.

        Args:
            data: Dictionary with vocabulary card data

        Returns:
            VocabularyCard instance
        """
        # Parse phonetic
        phonetic_data = data.get("phonetic", {})
        phonetic = (
            Phonetic.from_dict(phonetic_data)
            if isinstance(phonetic_data, dict)
            else Phonetic()
        )

        # Parse definition
        definition_data = data.get("definition", {})
        definition = (
            Definition.from_dict(definition_data)
            if isinstance(definition_data, dict)
            else Definition(zh="")
        )

        # Parse example sentences
        example_sentences = [
            ExampleSentence.from_dict(ex) if isinstance(ex, dict) else ex
            for ex in data.get("example_sentences", [])
        ]

        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        last_reviewed = data.get("last_reviewed")
        if isinstance(last_reviewed, str):
            last_reviewed = datetime.fromisoformat(last_reviewed)

        return cls(
            word=data.get("word", ""),
            phonetic=phonetic,
            part_of_speech=data.get("part_of_speech", ""),
            definition=definition,
            example_sentences=example_sentences,
            synonyms=data.get("synonyms", []),
            antonyms=data.get("antonyms", []),
            related_words=data.get("related_words", []),
            difficulty=data.get("difficulty", "intermediate"),
            frequency=data.get("frequency", "medium"),
            memory_status=data.get("memory_status", "new"),
            created_at=created_at,
            last_reviewed=last_reviewed,
            review_count=data.get("review_count", 0),
        )


@dataclass
class ContextStory:
    """
    Contextual story containing target vocabulary words.

    A short story or article that naturally incorporates the target
    vocabulary words to help with memory retention.

    Attributes:
        title: Story title
        content: Story content (contains all target words)
        word_count: Number of words in the story
        difficulty: Difficulty level
        target_words: List of target words included in the story
    """

    title: str
    content: str
    word_count: int
    difficulty: str
    target_words: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Convert context story to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "title": self.title,
            "content": self.content,
            "word_count": self.word_count,
            "difficulty": self.difficulty,
            "target_words": self.target_words,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContextStory":
        """
        Create ContextStory from dictionary.

        Args:
            data: Dictionary with story data

        Returns:
            ContextStory instance
        """
        return cls(
            title=data.get("title", ""),
            content=data.get("content", ""),
            word_count=data.get("word_count", 0),
            difficulty=data.get("difficulty", "intermediate"),
            target_words=data.get("target_words", []),
        )


@dataclass
class VocabularyQuiz:
    """
    Vocabulary quiz question.

    A quiz question to test vocabulary knowledge.

    Attributes:
        type: Question type (definition/spelling/usage/fill_blank)
        word: The target word
        question: The quiz question
        options: Multiple choice options (optional)
        correct: Correct answer
        explanation: Explanation for the answer (optional)
    """

    type: str  # definition/spelling/usage/fill_blank
    word: str
    question: str
    correct: str
    options: Optional[list[str]] = None
    explanation: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert quiz question to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "type": self.type,
            "word": self.word,
            "question": self.question,
            "options": self.options,
            "correct": self.correct,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VocabularyQuiz":
        """
        Create VocabularyQuiz from dictionary.

        Args:
            data: Dictionary with quiz data

        Returns:
            VocabularyQuiz instance
        """
        return cls(
            type=data.get("type", "definition"),
            word=data.get("word", ""),
            question=data.get("question", ""),
            correct=data.get("correct", ""),
            options=data.get("options"),
            explanation=data.get("explanation"),
        )


@dataclass
class VocabularyOutput:
    """
    Complete vocabulary learning output.

    Contains vocabulary cards, context story, quiz questions,
    and statistics.

    Attributes:
        vocabulary_cards: List of vocabulary cards
        context_story: Context story (optional)
        quiz: List of quiz questions
        statistics: Statistics about the extracted vocabulary
    """

    vocabulary_cards: list[VocabularyCard]
    context_story: Optional[ContextStory] = None
    quiz: list[VocabularyQuiz] = field(default_factory=list)
    statistics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convert vocabulary output to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "vocabulary_cards": [card.to_dict() for card in self.vocabulary_cards],
            "context_story": (
                self.context_story.to_dict() if self.context_story else None
            ),
            "quiz": [q.to_dict() for q in self.quiz],
            "statistics": self.statistics,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VocabularyOutput":
        """
        Create VocabularyOutput from dictionary.

        Args:
            data: Dictionary with output data

        Returns:
            VocabularyOutput instance
        """
        vocabulary_cards = [
            VocabularyCard.from_dict(card) if isinstance(card, dict) else card
            for card in data.get("vocabulary_cards", [])
        ]

        context_story_data = data.get("context_story")
        context_story = (
            ContextStory.from_dict(context_story_data) if context_story_data else None
        )

        quiz = [
            VocabularyQuiz.from_dict(q) if isinstance(q, dict) else q
            for q in data.get("quiz", [])
        ]

        return cls(
            vocabulary_cards=vocabulary_cards,
            context_story=context_story,
            quiz=quiz,
            statistics=data.get("statistics", {}),
        )
