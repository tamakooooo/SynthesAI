"""
Data models for Link Learning Module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LinkContent:
    """
    Parsed link content.

    Represents the raw content extracted from a web page.
    """

    url: str
    title: str
    content: str  # Main content text
    source: str  # Source website name
    word_count: int
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    html: Optional[str] = None  # Original HTML (optional)
    language: str = "zh"  # Content language (zh/en/etc)


@dataclass
class QAPair:
    """
    Question-Answer pair.

    Represents a Q&A pair generated from the content.
    """

    question: str
    answer: str
    difficulty: str = "medium"  # easy/medium/hard


@dataclass
class QuizQuestion:
    """
    Quiz question.

    Represents a quiz question for testing knowledge.
    """

    type: str  # multiple_choice/true_false/fill_blank
    question: str
    correct: str  # Correct answer
    options: Optional[list[str]] = None
    explanation: Optional[str] = None


@dataclass
class KnowledgeCard:
    """
    Knowledge card.

    Represents a structured knowledge card generated from web content.
    """

    title: str  # Article title
    url: str  # Original URL
    source: str  # Source website
    summary: str  # 200-word summary
    key_points: list[str]  # 3-5 key points
    tags: list[str]  # 3-5 tags
    word_count: int  # Total word count
    reading_time: str  # Estimated reading time
    difficulty: str  # beginner/intermediate/advanced
    created_at: datetime  # Creation timestamp
    qa_pairs: list[QAPair] = field(default_factory=list)  # Q&A pairs
    quiz: list[QuizQuestion] = field(default_factory=list)  # Quiz questions

    def to_dict(self) -> dict:
        """
        Convert knowledge card to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "summary": self.summary,
            "key_points": self.key_points,
            "tags": self.tags,
            "word_count": self.word_count,
            "reading_time": self.reading_time,
            "difficulty": self.difficulty,
            "created_at": self.created_at.isoformat(),
            "qa_pairs": [
                {
                    "question": qa.question,
                    "answer": qa.answer,
                    "difficulty": qa.difficulty,
                }
                for qa in self.qa_pairs
            ],
            "quiz": [
                {
                    "type": q.type,
                    "question": q.question,
                    "options": q.options,
                    "correct": q.correct,
                    "explanation": q.explanation,
                }
                for q in self.quiz
            ],
        }
