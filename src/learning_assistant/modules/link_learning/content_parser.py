"""
Content Parser for Link Learning Module.

Parses HTML content to extract main content, title, and metadata.
"""

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from loguru import logger


class ContentParser:
    """
    Content parser.

    Parses HTML content to extract structured content.
    """

    def __init__(
        self,
        engine: str = "trafilatura",
        include_comments: bool = False,
        include_tables: bool = True,
        favor_precision: bool = True,
        min_content_length: int = 200,
    ) -> None:
        """
        Initialize content parser.

        Args:
            engine: Parsing engine (trafilatura/readability/etc)
            include_comments: Whether to include comments
            include_tables: Whether to include tables
            favor_precision: Favor precision over recall
            min_content_length: Minimum content length
        """
        self.engine = engine
        self.include_comments = include_comments
        self.include_tables = include_tables
        self.favor_precision = favor_precision
        self.min_content_length = min_content_length

        logger.debug(f"ContentParser initialized: engine={engine}")

    def parse(self, html: str, url: str) -> "LinkContent":
        """
        Parse HTML content.

        Args:
            html: HTML content
            url: Original URL

        Returns:
            LinkContent object

        Raises:
            ValueError: If content is too short or parsing fails
        """
        logger.info(f"Parsing content from: {url}")

        if self.engine == "trafilatura":
            return self._parse_with_trafilatura(html, url)
        elif self.engine == "readability":
            return self._parse_with_readability(html, url)
        else:
            raise ValueError(f"Unknown parsing engine: {self.engine}")

    def _parse_with_trafilatura(self, html: str, url: str) -> "LinkContent":
        """
        Parse using trafilatura.

        Args:
            html: HTML content
            url: Original URL

        Returns:
            LinkContent object

        Raises:
            RuntimeError: If trafilatura is not available or parsing fails
        """
        try:
            import trafilatura

            logger.debug("Parsing with trafilatura")

            # Extract content
            content = trafilatura.extract(
                html,
                output_format="txt",
                include_comments=self.include_comments,
                include_tables=self.include_tables,
                favor_precision=self.favor_precision,
            )

            if not content:
                raise ValueError("Failed to extract content")

            # Extract metadata
            metadata = trafilatura.extract_metadata(html)

            # Get title
            title = (
                metadata.title
                if metadata and metadata.title
                else self._extract_title_from_html(html)
            )

            # Get author
            author = metadata.author if metadata and metadata.author else None

            # Get publication date
            published_date = None
            if metadata and metadata.date:
                try:
                    # Try to parse date (format varies)
                    published_date = self._parse_date(metadata.date)
                except Exception:
                    logger.warning(f"Failed to parse date: {metadata.date}")

            # Get source (domain name)
            source = self._extract_source_from_url(url)

            # Calculate word count
            word_count = len(content.split())

            # Validate content length
            if word_count < self.min_content_length:
                raise ValueError(
                    f"Content too short: {word_count} words (min: {self.min_content_length})"
                )

            # Detect language
            language = self._detect_language(content)

            # Import LinkContent here to avoid circular dependency
            from learning_assistant.modules.link_learning.models import LinkContent

            return LinkContent(
                url=url,
                title=title,
                author=author,
                published_date=published_date,
                content=content,
                html=html,
                source=source,
                word_count=word_count,
                language=language,
            )

        except ImportError:
            logger.error(
                "Trafilatura not installed. Install with: pip install trafilatura"
            )
            raise RuntimeError(
                "Trafilatura not available. Install with: pip install trafilatura"
            )
        except Exception as e:
            logger.error(f"Trafilatura parsing failed: {e}")
            raise RuntimeError(f"Content parsing failed: {e}") from e

    def _parse_with_readability(self, html: str, url: str) -> "LinkContent":
        """
        Parse using readability-lxml.

        Args:
            html: HTML content
            url: Original URL

        Returns:
            LinkContent object

        Raises:
            RuntimeError: If readability is not available or parsing fails
        """
        try:
            from readability import Document

            logger.debug("Parsing with readability")

            # Parse with readability
            doc = Document(html)
            content = doc.summary()

            # Get title
            title = doc.title()

            # Get source
            source = self._extract_source_from_url(url)

            # Calculate word count
            word_count = len(content.split())

            # Validate content length
            if word_count < self.min_content_length:
                raise ValueError(
                    f"Content too short: {word_count} words (min: {self.min_content_length})"
                )

            # Detect language
            language = self._detect_language(content)

            # Import LinkContent here
            from learning_assistant.modules.link_learning.models import LinkContent

            return LinkContent(
                url=url,
                title=title,
                author=None,
                published_date=None,
                content=content,
                html=html,
                source=source,
                word_count=word_count,
                language=language,
            )

        except ImportError:
            logger.error(
                "Readability not installed. Install with: pip install readability-lxml"
            )
            raise RuntimeError(
                "Readability not available. Install with: pip install readability-lxml"
            )
        except Exception as e:
            logger.error(f"Readability parsing failed: {e}")
            raise RuntimeError(f"Content parsing failed: {e}") from e

    def _extract_title_from_html(self, html: str) -> str:
        """
        Extract title from HTML.

        Args:
            html: HTML content

        Returns:
            Title string
        """
        import re

        # Try to find <title> tag
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            return title_match.group(1).strip()

        # Try to find <h1> tag
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if h1_match:
            return h1_match.group(1).strip()

        return "Untitled"

    def _extract_source_from_url(self, url: str) -> str:
        """
        Extract source (domain) from URL.

        Args:
            url: URL string

        Returns:
            Domain name
        """
        parsed = urlparse(url)
        return parsed.netloc or "Unknown"

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime.

        Args:
            date_str: Date string

        Returns:
            Datetime object or None
        """
        from dateutil import parser as date_parser

        try:
            return date_parser.parse(date_str)
        except Exception:
            return None

    def _detect_language(self, content: str) -> str:
        """
        Detect content language.

        Args:
            content: Content text

        Returns:
            Language code (zh/en/etc)
        """
        # Simple heuristic: check for Chinese characters
        chinese_chars = sum(1 for char in content if "\u4e00" <= char <= "\u9fff")
        total_chars = len(content)

        if chinese_chars / total_chars > 0.3:
            return "zh"
        else:
            return "en"
