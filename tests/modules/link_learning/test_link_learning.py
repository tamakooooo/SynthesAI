"""
Tests for Link Learning Module.
"""

import pytest

from learning_assistant.modules.link_learning.models import KnowledgeCard, LinkContent, KeyConcept
from learning_assistant.modules.link_learning.content_fetcher import ContentFetcher
from learning_assistant.modules.link_learning.content_parser import ContentParser


class TestModels:
    """Test data models."""

    def test_link_content_creation(self):
        """Test LinkContent creation."""
        content = LinkContent(
            url="https://example.com/article",
            title="Test Article",
            author="Test Author",
            content="This is a test content.",
            source="example.com",
            word_count=5,
        )

        assert content.url == "https://example.com/article"
        assert content.title == "Test Article"
        assert content.author == "Test Author"
        assert content.content == "This is a test content."
        assert content.source == "example.com"
        assert content.word_count == 5
        assert content.language == "zh"  # default

    def test_knowledge_card_to_dict(self):
        """Test KnowledgeCard.to_dict()."""
        from datetime import datetime

        card = KnowledgeCard(
            title="Test",
            url="https://example.com",
            source="example.com",
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            key_concepts=[KeyConcept(term="Term1", definition="Definition1")],
            tags=["test", "example"],
            word_count=100,
            reading_time="1分钟",
            difficulty="beginner",
            created_at=datetime(2026, 3, 31, 10, 0, 0),
        )

        card_dict = card.to_dict()

        assert card_dict["title"] == "Test"
        assert card_dict["url"] == "https://example.com"
        assert card_dict["summary"] == "Test summary"
        assert card_dict["key_points"] == ["Point 1", "Point 2"]
        assert card_dict["key_concepts"] == [{"term": "Term1", "definition": "Definition1"}]
        assert card_dict["tags"] == ["test", "example"]
        assert card_dict["word_count"] == 100
        assert card_dict["reading_time"] == "1分钟"
        assert card_dict["difficulty"] == "beginner"


class TestContentFetcher:
    """Test ContentFetcher."""

    def test_fetcher_initialization(self):
        """Test ContentFetcher initialization."""
        fetcher = ContentFetcher(
            timeout=30,
            max_retries=3,
            retry_delay=2,
        )

        assert fetcher.timeout == 30
        assert fetcher.max_retries == 3
        assert fetcher.retry_delay == 2
        assert fetcher.use_playwright is False

    def test_default_user_agent(self):
        """Test default user agent."""
        fetcher = ContentFetcher()
        user_agent = fetcher._default_user_agent()

        assert "Mozilla" in user_agent
        assert "Chrome" in user_agent

    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self):
        """Test fetch with invalid URL."""
        fetcher = ContentFetcher()

        with pytest.raises(ValueError, match="Invalid URL"):
            await fetcher.fetch("not-a-valid-url")


class TestContentParser:
    """Test ContentParser."""

    def test_parser_initialization(self):
        """Test ContentParser initialization."""
        parser = ContentParser(
            engine="trafilatura",
            include_comments=False,
            include_tables=True,
        )

        assert parser.engine == "trafilatura"
        assert parser.include_comments is False
        assert parser.include_tables is True

    def test_extract_title_from_html(self):
        """Test title extraction from HTML."""
        parser = ContentParser()

        html = "<html><head><title>Test Title</title></head><body></body></html>"
        title = parser._extract_title_from_html(html)

        assert title == "Test Title"

    def test_extract_title_from_h1(self):
        """Test title extraction from H1 when title is missing."""
        parser = ContentParser()

        html = "<html><body><h1>Test H1</h1></body></html>"
        title = parser._extract_title_from_html(html)

        assert title == "Test H1"

    def test_extract_source_from_url(self):
        """Test source extraction from URL."""
        parser = ContentParser()

        url = "https://example.com/article/123"
        source = parser._extract_source_from_url(url)

        assert source == "example.com"

    def test_detect_language_chinese(self):
        """Test language detection for Chinese content."""
        parser = ContentParser()

        content = "这是一段中文内容，包含很多汉字。"
        language = parser._detect_language(content)

        assert language == "zh"

    def test_detect_language_english(self):
        """Test language detection for English content."""
        parser = ContentParser()

        content = "This is English content with multiple words."
        language = parser._detect_language(content)

        assert language == "en"

    def test_parse_with_unknown_engine(self):
        """Test parse with unknown engine."""
        parser = ContentParser(engine="unknown")

        with pytest.raises(ValueError, match="Unknown parsing engine"):
            parser.parse("<html></html>", "https://example.com")


# Integration tests (require network and LLM service)
@pytest.mark.integration
class TestLinkLearningModuleIntegration:
    """Integration tests for Link Learning Module."""

    @pytest.mark.asyncio
    async def test_process_url(self):
        """Test processing a real URL."""
        # This test requires:
        # 1. Valid LLM API key
        # 2. Network access
        # 3. EventBus, LLMService instances
        pytest.skip("Integration test - requires API keys and network")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])