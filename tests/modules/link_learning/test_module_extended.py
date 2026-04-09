"""
Extended tests for Link Learning Module - Main Module.

Comprehensive tests for LinkLearningModule functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio

from learning_assistant.modules.link_learning import LinkLearningModule
from learning_assistant.modules.link_learning.models import (
    KnowledgeCard,
    LinkContent,
    QAPair,
    QuizQuestion,
)
from learning_assistant.core.event_bus import EventBus


class TestLinkLearningModuleExtended:
    """Extended tests for LinkLearningModule."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = LinkLearningModule()

        assert module.name == "link_learning"
        assert module.config == {}
        assert module.event_bus is None
        assert module.content_fetcher is None
        assert module.content_parser is None
        assert module.llm_service is None

    def test_module_initialize_with_config(self):
        """Test module initialization with config."""
        module = LinkLearningModule()

        config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
            },
            "fetcher": {
                "timeout": 60,
            },
            "parser": {
                "engine": "trafilatura",
            },
        }

        event_bus = EventBus()

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            module.initialize(config, event_bus)

            assert module.config == config
            assert module.event_bus == event_bus
            assert module.content_fetcher is not None
            assert module.content_parser is not None
            assert module.llm_service is not None

    def test_module_initialize_missing_api_key(self):
        """Test module initialization with missing API key."""
        module = LinkLearningModule()

        config = {
            "llm": {
                "provider": "openai",
            },
        }

        event_bus = EventBus()

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                module.initialize(config, event_bus)

    @pytest.mark.asyncio
    async def test_process_invalid_url_empty(self):
        """Test process with empty URL."""
        module = LinkLearningModule()

        with pytest.raises(ValueError, match="Invalid URL"):
            await module.process("")

    @pytest.mark.asyncio
    async def test_process_invalid_url_none(self):
        """Test process with None URL."""
        module = LinkLearningModule()

        with pytest.raises(ValueError, match="Invalid URL"):
            await module.process(None)

    @pytest.mark.asyncio
    async def test_process_invalid_url_format(self):
        """Test process with invalid URL format."""
        module = LinkLearningModule()

        with pytest.raises(ValueError, match="Invalid URL"):
            await module.process("not-a-url")

    @pytest.mark.asyncio
    async def test_process_invalid_url_no_protocol(self):
        """Test process with URL without protocol."""
        module = LinkLearningModule()

        with pytest.raises(ValueError, match="Invalid URL"):
            await module.process("example.com/article")

    @pytest.mark.asyncio
    async def test_process_successful_flow(self):
        """Test successful processing flow."""
        module = LinkLearningModule()

        # Mock components
        module.content_fetcher = AsyncMock()
        module.content_fetcher.fetch = AsyncMock(return_value="<html><body>Test content</body></html>")

        module.content_parser = Mock()
        module.content_parser.parse = Mock(return_value=LinkContent(
            url="https://example.com",
            title="Test Article",
            content="This is test content for the article.",
            source="example.com",
            word_count=10,
        ))

        module.prompt_manager = Mock()
        template = Mock()
        template.render = Mock(return_value=("System prompt", "User prompt"))
        module.prompt_manager.load_template = Mock(return_value=template)

        module.llm_service = Mock()
        module.llm_service.call = Mock(return_value=Mock(content='{"summary": "Test summary", "key_points": ["Point 1"], "tags": ["tag1"], "difficulty": "beginner"}'))

        module.exporter = Mock()
        module.exporter.export = Mock()

        module.history_manager = Mock()
        module.history_manager.add_record = Mock()

        module.config = {"output": {"save_history": False}}

        result = await module.process("https://example.com")

        assert isinstance(result, KnowledgeCard)
        assert result.title == "Test Article"
        assert result.url == "https://example.com"

    def test_parse_llm_response_valid_json(self):
        """Test parsing valid LLM JSON response."""
        module = LinkLearningModule()

        response = '{"summary": "Test", "key_points": ["A", "B"], "tags": ["tag"], "difficulty": "beginner"}'

        result = module._parse_llm_response(response)

        assert result["summary"] == "Test"
        assert result["key_points"] == ["A", "B"]
        assert result["tags"] == ["tag"]
        assert result["difficulty"] == "beginner"

    def test_parse_llm_response_json_in_markdown(self):
        """Test parsing JSON in markdown code block."""
        module = LinkLearningModule()

        response = '''
        Here is the result:
        ```json
        {"summary": "Test", "key_points": ["A"], "tags": ["tag"], "difficulty": "intermediate"}
        ```
        '''

        result = module._parse_llm_response(response)

        assert result["summary"] == "Test"

    def test_parse_llm_response_missing_field(self):
        """Test parsing JSON with missing required field."""
        module = LinkLearningModule()

        response = '{"summary": "Test"}'

        with pytest.raises(ValueError, match="Missing required field"):
            module._parse_llm_response(response)

    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON."""
        module = LinkLearningModule()

        response = 'This is not JSON'

        with pytest.raises(ValueError, match="Invalid JSON"):
            module._parse_llm_response(response)

    def test_estimate_reading_time_short(self):
        """Test reading time estimation for short content."""
        module = LinkLearningModule()

        time_str = module._estimate_reading_time(100)

        assert time_str == "1分钟"

    def test_estimate_reading_time_medium(self):
        """Test reading time estimation for medium content."""
        module = LinkLearningModule()

        time_str = module._estimate_reading_time(1000)

        assert "分钟" in time_str

    def test_estimate_reading_time_long(self):
        """Test reading time estimation for long content."""
        module = LinkLearningModule()

        time_str = module._estimate_reading_time(15000)

        assert "小时" in time_str

    def test_estimate_reading_time_zero(self):
        """Test reading time estimation for zero words."""
        module = LinkLearningModule()

        time_str = module._estimate_reading_time(0)

        assert time_str == "1分钟"  # Minimum 1 minute

    def test_cleanup(self):
        """Test module cleanup."""
        module = LinkLearningModule()

        # Should not raise any errors
        module.cleanup()

    def test_execute_sync_wrapper(self):
        """Test execute synchronous wrapper."""
        module = LinkLearningModule()

        # Mock components
        module.content_fetcher = AsyncMock()
        module.content_fetcher.fetch = AsyncMock(return_value="<html><body>Test</body></html>")

        module.content_parser = Mock()
        module.content_parser.parse = Mock(return_value=LinkContent(
            url="https://example.com",
            title="Test",
            content="Content",
            source="example.com",
            word_count=10,
        ))

        module.prompt_manager = Mock()
        template = Mock()
        template.render = Mock(return_value=("System", "User"))
        module.prompt_manager.load_template = Mock(return_value=template)

        module.llm_service = Mock()
        module.llm_service.call = Mock(return_value=Mock(content='{"summary": "S", "key_points": [], "tags": [], "difficulty": "beginner"}'))

        module.exporter = Mock()
        module.history_manager = Mock()

        module.config = {"output": {"save_history": False}}

        # Execute returns a dict
        result = module.execute({"url": "https://example.com"})

        assert isinstance(result, dict)
        assert "title" in result


class TestLinkLearningModuleDataModels:
    """Tests for data models used in LinkLearningModule."""

    def test_knowledge_card_creation_minimal(self):
        """Test creating KnowledgeCard with minimal fields."""
        card = KnowledgeCard(
            title="Test",
            url="https://example.com",
            source="example.com",
            summary="Summary",
            key_points=["Point 1"],
            tags=["tag"],
            word_count=100,
            reading_time="1分钟",
            difficulty="beginner",
            created_at=datetime.now(),
        )

        assert card.title == "Test"
        assert card.qa_pairs == []
        assert card.quiz == []

    def test_knowledge_card_with_qa(self):
        """Test creating KnowledgeCard with Q&A pairs."""
        card = KnowledgeCard(
            title="Test",
            url="https://example.com",
            source="example.com",
            summary="Summary",
            key_points=["Point"],
            tags=["tag"],
            word_count=100,
            reading_time="1分钟",
            difficulty="beginner",
            created_at=datetime.now(),
            qa_pairs=[
                QAPair(question="Q1", answer="A1", difficulty="easy"),
            ],
        )

        assert len(card.qa_pairs) == 1
        assert card.qa_pairs[0].question == "Q1"

    def test_knowledge_card_with_quiz(self):
        """Test creating KnowledgeCard with quiz questions."""
        card = KnowledgeCard(
            title="Test",
            url="https://example.com",
            source="example.com",
            summary="Summary",
            key_points=["Point"],
            tags=["tag"],
            word_count=100,
            reading_time="1分钟",
            difficulty="beginner",
            created_at=datetime.now(),
            quiz=[
                QuizQuestion(
                    type="multiple_choice",
                    question="Q1",
                    correct="A",
                    options=["A", "B", "C", "D"],
                ),
            ],
        )

        assert len(card.quiz) == 1
        assert card.quiz[0].type == "multiple_choice"

    def test_knowledge_card_to_dict(self):
        """Test KnowledgeCard serialization to dict."""
        card = KnowledgeCard(
            title="Test Article",
            url="https://example.com",
            source="example.com",
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            tags=["tag1", "tag2"],
            word_count=500,
            reading_time="2分钟",
            difficulty="intermediate",
            created_at=datetime(2026, 4, 8, 10, 0, 0),
        )

        card_dict = card.to_dict()

        assert card_dict["title"] == "Test Article"
        assert card_dict["url"] == "https://example.com"
        assert card_dict["word_count"] == 500
        assert isinstance(card_dict["created_at"], str)
        assert isinstance(card_dict["key_points"], list)
        assert isinstance(card_dict["tags"], list)

    def test_link_content_creation(self):
        """Test creating LinkContent."""
        content = LinkContent(
            url="https://example.com",
            title="Test",
            content="Content",
            source="example.com",
            word_count=100,
            author="Author",
            language="en",
        )

        assert content.url == "https://example.com"
        assert content.author == "Author"
        assert content.language == "en"

    def test_qa_pair_creation(self):
        """Test creating QAPair."""
        qa = QAPair(
            question="What is this?",
            answer="This is an answer.",
            difficulty="medium",
        )

        assert qa.question == "What is this?"
        assert qa.answer == "This is an answer."
        assert qa.difficulty == "medium"

    def test_quiz_question_multiple_choice(self):
        """Test creating multiple choice quiz question."""
        quiz = QuizQuestion(
            type="multiple_choice",
            question="Which option?",
            correct="A",
            options=["A", "B", "C", "D"],
            explanation="A is correct because...",
        )

        assert quiz.type == "multiple_choice"
        assert len(quiz.options) == 4
        assert quiz.explanation == "A is correct because..."

    def test_quiz_question_true_false(self):
        """Test creating true/false quiz question."""
        quiz = QuizQuestion(
            type="true_false",
            question="Is this true?",
            correct="True",
        )

        assert quiz.type == "true_false"
        assert quiz.correct == "True"


class TestLinkLearningModuleIntegration:
    """Integration tests for LinkLearningModule."""

    @pytest.mark.asyncio
    async def test_full_workflow_mock(self):
        """Test full workflow with mocked components."""
        module = LinkLearningModule()

        # Setup all components
        module.content_fetcher = AsyncMock()
        module.content_fetcher.fetch = AsyncMock(return_value="""
            <html>
                <head><title>Test Article</title></head>
                <body>
                    <article>
                        <p>This is a comprehensive test article with enough content.</p>
                        <p>It has multiple paragraphs for testing the parsing.</p>
                    </article>
                </body>
            </html>
        """)

        module.content_parser = Mock()
        module.content_parser.parse = Mock(return_value=LinkContent(
            url="https://example.com/test",
            title="Test Article",
            content="This is a comprehensive test article with enough content. It has multiple paragraphs for testing the parsing.",
            source="example.com",
            word_count=20,
            language="en",
        ))

        module.prompt_manager = Mock()
        template = Mock()
        template.render = Mock(return_value=(
            "You are a knowledge extractor",
            "Extract knowledge from: This is a comprehensive test article..."
        ))
        module.prompt_manager.load_template = Mock(return_value=template)

        module.llm_service = Mock()
        module.llm_service.call = Mock(return_value=Mock(content='''
            {
                "summary": "A comprehensive test article about testing.",
                "key_points": ["Testing is important", "Multiple paragraphs included"],
                "tags": ["test", "article", "comprehensive"],
                "difficulty": "intermediate",
                "qa_pairs": [
                    {
                        "question": "What is this article about?",
                        "answer": "Testing and parsing.",
                        "difficulty": "easy"
                    }
                ],
                "quiz": [
                    {
                        "type": "multiple_choice",
                        "question": "What is the main topic?",
                        "options": ["A. Testing", "B. Coding", "C. Design", "D. Management"],
                        "correct": "A",
                        "explanation": "The article focuses on testing."
                    }
                ]
            }
        '''))

        module.exporter = Mock()
        module.exporter.export = Mock()

        module.history_manager = Mock()
        module.history_manager.add_record = Mock()

        module.config = {
            "output": {"save_history": False},
            "llm": {"temperature": 0.3},
        }

        # Execute
        result = await module.process("https://example.com/test")

        # Verify
        assert isinstance(result, KnowledgeCard)
        assert result.title == "Test Article"
        assert result.summary == "A comprehensive test article about testing."
        assert len(result.key_points) == 2
        assert len(result.tags) == 3
        assert result.difficulty == "intermediate"
        assert len(result.qa_pairs) == 1
        assert len(result.quiz) == 1

    @pytest.mark.asyncio
    async def test_error_handling_fetch_failure(self):
        """Test error handling when fetch fails."""
        module = LinkLearningModule()

        module.content_fetcher = AsyncMock()
        module.content_fetcher.fetch = AsyncMock(side_effect=RuntimeError("Network error"))

        with pytest.raises(RuntimeError, match="Processing failed"):
            await module.process("https://example.com")

    @pytest.mark.asyncio
    async def test_error_handling_parse_failure(self):
        """Test error handling when parse fails."""
        module = LinkLearningModule()

        module.content_fetcher = AsyncMock()
        module.content_fetcher.fetch = AsyncMock(return_value="<html>Content</html>")

        module.content_parser = Mock()
        module.content_parser.parse = Mock(side_effect=ValueError("Parse error"))

        with pytest.raises(RuntimeError, match="Processing failed"):
            await module.process("https://example.com")

    @pytest.mark.asyncio
    async def test_error_handling_llm_failure(self):
        """Test error handling when LLM call fails."""
        module = LinkLearningModule()

        module.content_fetcher = AsyncMock()
        module.content_fetcher.fetch = AsyncMock(return_value="<html>Content</html>")

        module.content_parser = Mock()
        module.content_parser.parse = Mock(return_value=LinkContent(
            url="https://example.com",
            title="Test",
            content="Content",
            source="example.com",
            word_count=10,
        ))

        module.prompt_manager = Mock()
        template = Mock()
        template.render = Mock(return_value=("System", "User"))
        module.prompt_manager.load_template = Mock(return_value=template)

        module.llm_service = Mock()
        module.llm_service.call = Mock(side_effect=Exception("LLM error"))

        with pytest.raises(RuntimeError, match="Processing failed"):
            await module.process("https://example.com")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])