"""
Tests for CLI Input Validation.
"""

import pytest
from pathlib import Path
from learning_assistant.utils.validation import (
    InputValidator,
    ValidationError,
    validate_video_input,
    validate_link_input,
    validate_vocabulary_input,
)


class TestInputValidator:
    """Tests for InputValidator class."""

    def test_validate_url_empty(self):
        """Test empty URL raises error."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_url("")
        assert exc_info.value.field == "url"

    def test_validate_url_invalid_scheme(self):
        """Test invalid scheme raises error."""
        with pytest.raises(ValidationError):
            InputValidator.validate_url("ftp://example.com")

    def test_validate_url_valid(self):
        """Test valid URL passes."""
        url = InputValidator.validate_url("https://example.com/article")
        assert url == "https://example.com/article"

    def test_validate_url_strip_whitespace(self):
        """Test URL whitespace is stripped."""
        url = InputValidator.validate_url("  https://example.com  ")
        assert url == "https://example.com"

    def test_validate_url_bilibili(self):
        """Test Bilibili URL passes video validation."""
        url = "https://www.bilibili.com/video/BV1abc123"
        validated = InputValidator.validate_url(url, allow_generic=False)
        assert validated == url

    def test_validate_url_youtube(self):
        """Test YouTube URL passes video validation."""
        url = "https://www.youtube.com/watch?v=abc123"
        validated = InputValidator.validate_url(url, allow_generic=False)
        assert validated == url

    def test_validate_url_unsupported_platform(self):
        """Test unsupported platform raises error."""
        with pytest.raises(ValidationError):
            InputValidator.validate_url(
                "https://unknown.com/video/123",
                allow_generic=False
            )

    def test_validate_url_too_long(self):
        """Test too long URL raises error."""
        long_url = "https://example.com/" + "a" * 2100
        with pytest.raises(ValidationError):
            InputValidator.validate_url(long_url)

    def test_validate_file_path_valid(self, tmp_path: Path):
        """Test valid file path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        validated = InputValidator.validate_file_path(str(test_file))
        assert validated == test_file

    def test_validate_file_path_not_found(self):
        """Test non-existent file raises error."""
        with pytest.raises(ValidationError):
            InputValidator.validate_file_path("/nonexistent/file.txt")

    def test_validate_file_path_directory(self, tmp_path: Path):
        """Test directory path raises error."""
        with pytest.raises(ValidationError):
            InputValidator.validate_file_path(str(tmp_path))

    def test_validate_text_content_empty(self):
        """Test empty text raises error."""
        with pytest.raises(ValidationError):
            InputValidator.validate_text_content("")

    def test_validate_text_content_too_short(self):
        """Test too short text raises error."""
        with pytest.raises(ValidationError):
            InputValidator.validate_text_content("short")

    def test_validate_text_content_valid(self):
        """Test valid text passes."""
        text = InputValidator.validate_text_content("This is valid content.")
        assert text == "This is valid content."

    def test_validate_word_count_valid(self):
        """Test valid word count."""
        assert InputValidator.validate_word_count(10) == 10

    def test_validate_word_count_zero(self):
        """Test zero word count raises error."""
        with pytest.raises(ValidationError):
            InputValidator.validate_word_count(0)

    def test_validate_word_count_exceed(self):
        """Test exceeding max word count."""
        with pytest.raises(ValidationError):
            InputValidator.validate_word_count(100)

    def test_validate_difficulty_valid(self):
        """Test valid difficulty."""
        assert InputValidator.validate_difficulty("intermediate") == "intermediate"
        assert InputValidator.validate_difficulty("BEGINNER") == "beginner"

    def test_validate_difficulty_invalid(self):
        """Test invalid difficulty."""
        with pytest.raises(ValidationError):
            InputValidator.validate_difficulty("expert")

    def test_validate_format_valid(self):
        """Test valid format."""
        assert InputValidator.validate_format("markdown") == "markdown"
        assert InputValidator.validate_format("JSON") == "json"

    def test_validate_format_invalid(self):
        """Test invalid format."""
        with pytest.raises(ValidationError):
            InputValidator.validate_format("yaml")


class TestValidateVideoInput:
    """Tests for video input validation."""

    def test_valid_bilibili(self):
        """Test valid Bilibili URL."""
        url = validate_video_input("https://www.bilibili.com/video/BV1abc")
        assert url == "https://www.bilibili.com/video/BV1abc"

    def test_valid_youtube(self):
        """Test valid YouTube URL."""
        url = validate_video_input("https://www.youtube.com/watch?v=test")
        assert url == "https://www.youtube.com/watch?v=test"


class TestValidateLinkInput:
    """Tests for link input validation."""

    def test_valid_generic_url(self):
        """Test generic URL passes."""
        url = validate_link_input("https://example.com/article")
        assert url == "https://example.com/article"


class TestValidateVocabularyInput:
    """Tests for vocabulary input validation."""

    def test_no_source(self):
        """Test no content source raises error."""
        with pytest.raises(ValidationError):
            validate_vocabulary_input()

    def test_multiple_sources(self):
        """Test multiple sources raises error."""
        with pytest.raises(ValidationError):
            validate_vocabulary_input(text="content", url="https://example.com")

    def test_valid_text_source(self):
        """Test valid text source."""
        result = validate_vocabulary_input(
            text="This is valid content for vocabulary extraction.",
            word_count=10,
            difficulty="intermediate"
        )
        assert result["source_type"] == "text"
        assert result["word_count"] == 10
        assert result["difficulty"] == "intermediate"

    def test_valid_url_source(self):
        """Test valid URL source."""
        result = validate_vocabulary_input(
            url="https://example.com/article",
            word_count=15,
            difficulty="advanced"
        )
        assert result["source_type"] == "url"
        assert result["url"] == "https://example.com/article"