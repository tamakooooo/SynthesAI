"""
Extended tests for Link Learning Module - ContentParser.

Comprehensive tests for content parsing functionality.
"""

import pytest
from unittest.mock import Mock, patch

from learning_assistant.modules.link_learning.content_parser import ContentParser
from learning_assistant.modules.link_learning.models import LinkContent


class TestContentParserExtended:
    """Extended tests for ContentParser."""

    def test_parser_default_initialization(self):
        """Test default initialization."""
        parser = ContentParser()

        assert parser.engine == "trafilatura"
        assert parser.include_comments is False
        assert parser.include_tables is True
        assert parser.favor_precision is True
        assert parser.min_content_length == 200

    def test_parser_custom_initialization(self):
        """Test custom initialization."""
        parser = ContentParser(
            engine="readability",
            include_comments=True,
            include_tables=False,
            favor_precision=False,
            min_content_length=500,
        )

        assert parser.engine == "readability"
        assert parser.include_comments is True
        assert parser.include_tables is False
        assert parser.favor_precision is False
        assert parser.min_content_length == 500

    def test_parse_basic_html(self):
        """Test parsing basic HTML."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Test Title</title></head>
            <body>
                <p>This is a test paragraph with enough content.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com/article")

        assert isinstance(result, LinkContent)
        assert result.title == "Test Title"
        assert result.url == "https://example.com/article"
        assert result.source == "example.com"
        assert len(result.content) > 0

    def test_parse_html_with_h1_title(self):
        """Test parsing HTML with H1 as title (no title tag)."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <body>
                <h1>Main Heading</h1>
                <p>This is content with enough length for parsing.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert result.title == "Main Heading"

    def test_parse_html_with_nested_structure(self):
        """Test parsing HTML with nested divs and sections."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Nested Content</title></head>
            <body>
                <div class="wrapper">
                    <section class="main">
                        <article>
                            <p>Main content paragraph with sufficient text.</p>
                        </article>
                    </section>
                </div>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert result.title == "Nested Content"
        assert "Main content" in result.content

    def test_parse_html_with_tables(self):
        """Test parsing HTML with tables."""
        parser = ContentParser(include_tables=True, min_content_length=10)

        html = """
        <html>
            <head><title>Table Test</title></head>
            <body>
                <table>
                    <tr><td>Cell 1</td><td>Cell 2</td></tr>
                    <tr><td>Cell 3</td><td>Cell 4</td></tr>
                </table>
                <p>Additional content to meet minimum length.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert "Cell 1" in result.content or "table" in result.content.lower()

    def test_parse_html_without_tables(self):
        """Test parsing HTML without tables (tables excluded)."""
        parser = ContentParser(include_tables=False, min_content_length=10)

        html = """
        <html>
            <head><title>No Tables</title></head>
            <body>
                <table>
                    <tr><td>Cell 1</td></tr>
                </table>
                <p>This is the main content without tables.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert len(result.content) > 0

    def test_parse_html_with_comments(self):
        """Test parsing HTML with comments."""
        parser = ContentParser(include_comments=True, min_content_length=10)

        html = """
        <html>
            <head><title>Comments Test</title></head>
            <body>
                <p>Main content here with sufficient length.</p>
                <div class="comments">
                    <p>Great article!</p>
                </div>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert len(result.content) > 0

    def test_extract_title_from_html_with_meta(self):
        """Test title extraction from meta og:title."""
        parser = ContentParser()

        html = """
        <html>
            <head>
                <meta property="og:title" content="OG Title">
                <title>Regular Title</title>
            </head>
            <body></body>
        </html>
        """

        title = parser._extract_title_from_html(html)

        # Should prefer og:title or fall back to title
        assert title in ["OG Title", "Regular Title"]

    def test_extract_title_from_h1_fallback(self):
        """Test title extraction fallback to H1."""
        parser = ContentParser()

        html = """
        <html>
            <body>
                <h1>H1 Title</h1>
            </body>
        </html>
        """

        title = parser._extract_title_from_html(html)

        assert title == "H1 Title"

    def test_extract_title_from_h2_fallback(self):
        """Test title extraction fallback to H2 when no H1."""
        parser = ContentParser()

        html = """
        <html>
            <body>
                <h2>H2 Title</h2>
            </body>
        </html>
        """

        title = parser._extract_title_from_html(html)

        assert title == "H2 Title"

    def test_extract_source_from_url_basic(self):
        """Test source extraction from basic URL."""
        parser = ContentParser()

        url = "https://example.com/article/123"
        source = parser._extract_source_from_url(url)

        assert source == "example.com"

    def test_extract_source_from_url_with_subdomain(self):
        """Test source extraction from URL with subdomain."""
        parser = ContentParser()

        url = "https://blog.example.com/post"
        source = parser._extract_source_from_url(url)

        assert "example.com" in source

    def test_extract_source_from_url_with_port(self):
        """Test source extraction from URL with port."""
        parser = ContentParser()

        url = "https://example.com:8080/page"
        source = parser._extract_source_from_url(url)

        assert "example.com" in source

    def test_detect_language_chinese(self):
        """Test language detection for Chinese."""
        parser = ContentParser()

        content = "这是一段中文内容，包含很多汉字。我们测试语言检测功能。"
        language = parser._detect_language(content)

        assert language == "zh"

    def test_detect_language_english(self):
        """Test language detection for English."""
        parser = ContentParser()

        content = "This is English content with multiple words and sentences."
        language = parser._detect_language(content)

        assert language == "en"

    def test_detect_language_mixed(self):
        """Test language detection for mixed content."""
        parser = ContentParser()

        content = "This is English content 这是中文内容混合在一起。"
        language = parser._detect_language(content)

        # Should detect the dominant language
        assert language in ["zh", "en"]

    def test_detect_language_empty_content(self):
        """Test language detection for empty content."""
        parser = ContentParser()

        language = parser._detect_language("")

        assert language == "zh"  # Default

    def test_detect_language_numbers_only(self):
        """Test language detection for numbers only."""
        parser = ContentParser()

        content = "123456 789012"
        language = parser._detect_language(content)

        # Should default to Chinese
        assert language == "zh"

    def test_count_words_chinese(self):
        """Test word counting for Chinese."""
        parser = ContentParser()

        content = "这是一个测试内容"
        count = parser._count_words(content)

        # Chinese characters count
        assert count > 0

    def test_count_words_english(self):
        """Test word counting for English."""
        parser = ContentParser()

        content = "This is a test content with eight words"
        count = parser._count_words(content)

        assert count == 8

    def test_count_words_mixed(self):
        """Test word counting for mixed content."""
        parser = ContentParser()

        content = "This is English 这是中文"
        count = parser._count_words(content)

        assert count > 0

    def test_parse_with_trafilatura_engine(self):
        """Test parsing with trafilatura engine."""
        parser = ContentParser(engine="trafilatura", min_content_length=10)

        html = """
        <html>
            <head><title>Trafilatura Test</title></head>
            <body>
                <article>
                    <p>This is the main article content for testing purposes.</p>
                </article>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert result.title == "Trafilatura Test"

    def test_parse_with_unknown_engine(self):
        """Test parsing with unknown engine raises error."""
        parser = ContentParser(engine="unknown_engine")

        html = "<html><body>Content</body></html>"

        with pytest.raises(ValueError, match="Unknown parsing engine"):
            parser.parse(html, "https://example.com")

    def test_parse_preserves_structure(self):
        """Test that parsing preserves content structure."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Structure Test</title></head>
            <body>
                <h1>Heading 1</h1>
                <p>First paragraph with enough content.</p>
                <h2>Heading 2</h2>
                <p>Second paragraph with more content here.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert "Heading 1" in result.content or "First paragraph" in result.content

    def test_parse_removes_scripts_and_styles(self):
        """Test that parsing removes script and style tags."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head>
                <title>Clean Content</title>
                <style>body { color: red; }</style>
            </head>
            <body>
                <script>console.log('test');</script>
                <p>Main content without scripts or styles.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert "console.log" not in result.content
        assert "color: red" not in result.content

    def test_parse_handles_entities(self):
        """Test that parsing handles HTML entities."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Entities &amp; Test</title></head>
            <body>
                <p>Content with entities: &lt;tag&gt; &amp; &quot;quotes&quot;.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert "Entities" in result.title or "Test" in result.title

    def test_parse_content_too_short(self):
        """Test parsing when content is too short."""
        parser = ContentParser(min_content_length=1000)

        html = """
        <html>
            <head><title>Short Content</title></head>
            <body>
                <p>Too short.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        # Should still parse but content might be empty or short
        assert isinstance(result, LinkContent)


class TestContentParserEdgeCases:
    """Edge case tests for ContentParser."""

    def test_parse_empty_html(self):
        """Test parsing empty HTML."""
        parser = ContentParser(min_content_length=10)

        html = "<html><body></body></html>"

        result = parser.parse(html, "https://example.com")

        assert isinstance(result, LinkContent)
        assert result.content == "" or len(result.content) == 0

    def test_parse_malformed_html(self):
        """Test parsing malformed HTML."""
        parser = ContentParser(min_content_length=10)

        html = "<html><body><p>Unclosed paragraph<div>Mixed tags</body>"

        # Should handle gracefully
        result = parser.parse(html, "https://example.com")

        assert isinstance(result, LinkContent)

    def test_parse_html_with_iframes(self):
        """Test parsing HTML with iframes."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Iframe Test</title></head>
            <body>
                <iframe src="https://example.com/embed"></iframe>
                <p>Main content paragraph with enough text length.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert len(result.content) > 0

    def test_parse_html_with_images(self):
        """Test parsing HTML with images."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Image Test</title></head>
            <body>
                <img src="image.jpg" alt="Test Image">
                <p>Content with images included here for testing.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert len(result.content) > 0

    def test_parse_html_with_links(self):
        """Test parsing HTML with links."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Link Test</title></head>
            <body>
                <a href="https://example.com">Link text</a>
                <p>Content with links and additional text for length.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert len(result.content) > 0

    def test_parse_html_with_special_characters(self):
        """Test parsing HTML with special characters."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Special Characters: <>&"'</title></head>
            <body>
                <p>Content with special chars: © ® ™ € £ ¥</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert isinstance(result, LinkContent)

    def test_parse_large_html(self):
        """Test parsing large HTML."""
        parser = ContentParser(min_content_length=10)

        large_content = "x" * 100000
        html = f"""
        <html>
            <head><title>Large Content</title></head>
            <body>
                <p>{large_content}</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert result.word_count > 0

    def test_parse_unicode_html(self):
        """Test parsing HTML with unicode characters."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Unicode 测试 テスト</title></head>
            <body>
                <p>Unicode content: 中文 日本語 한국어 العربية עברית</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert "中文" in result.content or "Unicode" in result.content

    def test_parse_html_with_base64_images(self):
        """Test parsing HTML with base64 encoded images."""
        parser = ContentParser(min_content_length=10)

        html = """
        <html>
            <head><title>Base64 Image</title></head>
            <body>
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...">
                <p>Content with base64 image and text for length.</p>
            </body>
        </html>
        """

        result = parser.parse(html, "https://example.com")

        assert len(result.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])