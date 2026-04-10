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
class KeyConcept:
    """
    Key concept from the original content.

    Represents an important term or concept mentioned in the source content.
    """

    term: str  # Concept/term name (from original content)
    definition: str  # Brief definition or explanation


@dataclass
class KnowledgeCard:
    """
    Knowledge card.

    Represents a structured knowledge card generated from web content.
    """

    title: str  # Article title
    url: str  # Original URL
    source: str  # Source website
    summary: str  # Single paragraph summary of the content
    key_points: list[str]  # 3-5 key points
    key_concepts: list[KeyConcept]  # Key concepts from the original content
    tags: list[str]  # 3-5 tags
    word_count: int  # Total word count
    reading_time: str  # Estimated reading time
    difficulty: str  # beginner/intermediate/advanced
    created_at: datetime  # Creation timestamp

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
            "key_concepts": [
                {
                    "term": concept.term,
                    "definition": concept.definition,
                }
                for concept in self.key_concepts
            ],
            "tags": self.tags,
            "word_count": self.word_count,
            "reading_time": self.reading_time,
            "difficulty": self.difficulty,
            "created_at": self.created_at.isoformat(),
        }
