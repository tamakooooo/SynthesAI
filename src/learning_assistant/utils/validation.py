"""
CLI Input Validation for SynthesAI.

Provides validation utilities for command-line inputs to ensure
security and correctness before processing.
"""

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class ValidationError(ValueError):
    """Validation error with context."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


class InputValidator:
    """Input validator for CLI commands."""

    # Supported URL patterns for video platforms
    VIDEO_URL_PATTERNS = {
        "bilibili": [
            r"https?://(?:www\.)?bilibili\.com/video/(?:BV|av)[a-zA-Z0-9]+",
            r"https?://(?:www\.)?bilibili\.com/video/(?:BV|av)[a-zA-Z0-9]+.*",
        ],
        "youtube": [
            r"https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+",
            r"https?://(?:www\.)?youtu\.be/[a-zA-Z0-9_-]+",
            r"https?://(?:www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]+",
        ],
        "douyin": [
            r"https?://(?:www\.)?douyin\.com/video/[a-zA-Z0-9]+",
            r"https?://v\.douyin\.com/[a-zA-Z0-9]+",
        ],
    }

    # General URL pattern for link learning
    URL_PATTERN = r"https?://[^\s<>'\"{}|\\^`\[\]]+"

    # Maximum lengths for inputs
    MAX_URL_LENGTH = 2048
    MAX_TEXT_LENGTH = 50000
    MAX_FILE_SIZE_MB = 100

    @classmethod
    def validate_url(cls, url: str, allow_generic: bool = True) -> str:
        """
        Validate URL format and check for supported platforms.

        Args:
            url: URL string to validate
            allow_generic: Allow non-video URLs (for link learning)

        Returns:
            Normalized URL string

        Raises:
            ValidationError: If URL is invalid or not supported
        """
        if not url:
            raise ValidationError("URL cannot be empty", "url")

        # Strip whitespace
        url = url.strip()

        # Check length
        if len(url) > cls.MAX_URL_LENGTH:
            raise ValidationError(
                f"URL too long (max {cls.MAX_URL_LENGTH} characters)", "url"
            )

        # Basic URL parsing
        try:
            parsed = urlparse(url)
        except Exception:
            raise ValidationError("Invalid URL format", "url")

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            raise ValidationError(
                f"Invalid URL scheme: {parsed.scheme}. Must be http or https", "url"
            )

        # Check netloc (domain)
        if not parsed.netloc:
            raise ValidationError("URL must have a domain", "url")

        # For video URLs, check platform support
        if not allow_generic:
            supported = False
            for platform, patterns in cls.VIDEO_URL_PATTERNS.items():
                for pattern in patterns:
                    if re.match(pattern, url, re.IGNORECASE):
                        supported = True
                        break

            if not supported:
                platforms = ", ".join(cls.VIDEO_URL_PATTERNS.keys())
                raise ValidationError(
                    f"Unsupported video platform. Supported: {platforms}", "url"
                )

        return url

    @classmethod
    def validate_file_path(
        cls,
        path: str,
        must_exist: bool = True,
        check_size: bool = False
    ) -> Path:
        """
        Validate file path.

        Args:
            path: File path string
            must_exist: File must exist
            check_size: Check file size limit

        Returns:
            Path object

        Raises:
            ValidationError: If path is invalid
        """
        if not path:
            raise ValidationError("File path cannot be empty", "file")

        try:
            file_path = Path(path)
        except Exception:
            raise ValidationError("Invalid file path format", "file")

        # Check if path is absolute or relative
        if not file_path.is_absolute():
            # Resolve relative path
            file_path = Path.cwd() / file_path

        # Check existence
        if must_exist and not file_path.exists():
            raise ValidationError(f"File not found: {file_path}", "file")

        # Check if it's a file (not directory)
        if must_exist and file_path.exists() and not file_path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}", "file")

        # Check file size
        if check_size and file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > cls.MAX_FILE_SIZE_MB:
                raise ValidationError(
                    f"File too large: {size_mb:.1f}MB (max {cls.MAX_FILE_SIZE_MB}MB)", "file"
                )

        return file_path

    @classmethod
    def validate_output_path(cls, path: str) -> Path:
        """
        Validate output file path.

        Args:
            path: Output file path

        Returns:
            Path object

        Raises:
            ValidationError: If path is invalid
        """
        if not path:
            raise ValidationError("Output path cannot be empty", "output")

        try:
            output_path = Path(path)
        except Exception:
            raise ValidationError("Invalid output path format", "output")

        # Check parent directory exists or can be created
        parent = output_path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                raise ValidationError(
                    f"Cannot create output directory: {parent}", "output"
                )

        # Check file extension
        valid_extensions = {".md", ".json", ".txt", ".pdf", ".html"}
        ext = output_path.suffix.lower()
        if ext and ext not in valid_extensions:
            raise ValidationError(
                f"Unsupported output format: {ext}. Supported: {', '.join(valid_extensions)}",
                "output"
            )

        return output_path

    @classmethod
    def validate_text_content(cls, text: str) -> str:
        """
        Validate text content.

        Args:
            text: Text string to validate

        Returns:
            Cleaned text

        Raises:
            ValidationError: If text is invalid
        """
        if not text:
            raise ValidationError("Text content cannot be empty", "text")

        # Strip whitespace
        text = text.strip()

        # Check length
        if len(text) > cls.MAX_TEXT_LENGTH:
            raise ValidationError(
                f"Text too long (max {cls.MAX_TEXT_LENGTH} characters). "
                "Use --file option for large content.",
                "text"
            )

        # Check for minimum content
        if len(text) < 10:
            raise ValidationError(
                "Text content too short. Minimum 10 characters required.",
                "text"
            )

        return text

    @classmethod
    def validate_word_count(cls, count: int) -> int:
        """
        Validate word count parameter.

        Args:
            count: Word count number

        Returns:
            Validated count

        Raises:
            ValidationError: If count is invalid
        """
        if count < 1:
            raise ValidationError(
                "Word count must be at least 1", "word_count"
            )
        if count > 50:
            raise ValidationError(
                "Word count cannot exceed 50", "word_count"
            )
        return count

    @classmethod
    def validate_difficulty(cls, difficulty: str) -> str:
        """
        Validate difficulty level.

        Args:
            difficulty: Difficulty string

        Returns:
            Validated difficulty

        Raises:
            ValidationError: If difficulty is invalid
        """
        valid_levels = ("beginner", "intermediate", "advanced")
        difficulty = difficulty.lower().strip()

        if difficulty not in valid_levels:
            raise ValidationError(
                f"Invalid difficulty: {difficulty}. "
                f"Valid options: {', '.join(valid_levels)}",
                "difficulty"
            )

        return difficulty

    @classmethod
    def validate_format(cls, format: str) -> str:
        """
        Validate output format.

        Args:
            format: Format string

        Returns:
            Validated format

        Raises:
            ValidationError: If format is invalid
        """
        valid_formats = ("markdown", "json", "pdf", "txt", "html")
        format = format.lower().strip()

        if format not in valid_formats:
            raise ValidationError(
                f"Invalid format: {format}. "
                f"Valid options: {', '.join(valid_formats)}",
                "format"
            )

        return format

    @classmethod
    def validate_platform(cls, platform: str) -> str:
        """
        Validate authentication platform.

        Args:
            platform: Platform name

        Returns:
            Validated platform

        Raises:
            ValidationError: If platform is invalid
        """
        valid_platforms = ("bilibili", "douyin", "youtube")
        platform = platform.lower().strip()

        if platform not in valid_platforms:
            raise ValidationError(
                f"Invalid platform: {platform}. "
                f"Valid options: {', '.join(valid_platforms)}",
                "platform"
            )

        return platform


def validate_video_input(url: str) -> str:
    """Validate video URL input."""
    return InputValidator.validate_url(url, allow_generic=False)


def validate_link_input(url: str) -> str:
    """Validate link URL input."""
    return InputValidator.validate_url(url, allow_generic=True)


def validate_vocabulary_input(
    text: Optional[str] = None,
    file: Optional[str] = None,
    url: Optional[str] = None,
    word_count: int = 10,
    difficulty: str = "intermediate",
) -> dict:
    """
    Validate vocabulary command inputs.

    Args:
        text: Text content
        file: File path
        url: URL
        word_count: Number of words
        difficulty: Difficulty level

    Returns:
        Dict with validated inputs

    Raises:
        ValidationError: If inputs are invalid
    """
    validated = {}

    # Validate content source (one required)
    sources = sum(1 for s in [text, file, url] if s)
    if sources == 0:
        raise ValidationError(
            "Must provide one content source: --text, --file, or --url",
            "content"
        )
    if sources > 1:
        raise ValidationError(
            "Cannot use multiple content sources. Choose one: --text, --file, or --url",
            "content"
        )

    # Validate specific source
    if text:
        validated["content"] = InputValidator.validate_text_content(text)
        validated["source_type"] = "text"
    elif file:
        validated["file_path"] = InputValidator.validate_file_path(file)
        validated["source_type"] = "file"
    elif url:
        validated["url"] = InputValidator.validate_url(url)
        validated["source_type"] = "url"

    # Validate parameters
    validated["word_count"] = InputValidator.validate_word_count(word_count)
    validated["difficulty"] = InputValidator.validate_difficulty(difficulty)

    return validated