"""
Extended tests for Link Learning Module - ContentFetcher.

Comprehensive tests for content fetching functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp

from learning_assistant.modules.link_learning.content_fetcher import ContentFetcher


class TestContentFetcherExtended:
    """Extended tests for ContentFetcher."""

    def test_fetcher_default_initialization(self):
        """Test default initialization."""
        fetcher = ContentFetcher()

        assert fetcher.timeout == 30
        assert fetcher.max_retries == 3
        assert fetcher.retry_delay == 2
        assert fetcher.use_playwright is False
        assert fetcher.user_agent is None
        assert fetcher.proxy is None

    def test_fetcher_custom_initialization(self):
        """Test custom initialization."""
        fetcher = ContentFetcher(
            timeout=60,
            max_retries=5,
            retry_delay=5,
            use_playwright=True,
            user_agent="CustomAgent/1.0",
            proxy="http://proxy.example.com:8080",
        )

        assert fetcher.timeout == 60
        assert fetcher.max_retries == 5
        assert fetcher.retry_delay == 5
        assert fetcher.use_playwright is True
        assert fetcher.user_agent == "CustomAgent/1.0"
        assert fetcher.proxy == "http://proxy.example.com:8080"

    def test_default_user_agent_format(self):
        """Test default user agent format."""
        fetcher = ContentFetcher()
        user_agent = fetcher._default_user_agent()

        assert "Mozilla" in user_agent
        assert "Chrome" in user_agent
        assert "Safari" in user_agent
        assert len(user_agent) > 50

    @pytest.mark.asyncio
    async def test_fetch_empty_url(self):
        """Test fetch with empty URL."""
        fetcher = ContentFetcher()

        with pytest.raises(ValueError, match="Invalid URL"):
            await fetcher.fetch("")

    @pytest.mark.asyncio
    async def test_fetch_none_url(self):
        """Test fetch with None URL."""
        fetcher = ContentFetcher()

        with pytest.raises(ValueError, match="Invalid URL"):
            await fetcher.fetch(None)

    @pytest.mark.asyncio
    async def test_fetch_relative_url(self):
        """Test fetch with relative URL."""
        fetcher = ContentFetcher()

        with pytest.raises(ValueError, match="Invalid URL"):
            await fetcher.fetch("/relative/path")

    @pytest.mark.asyncio
    async def test_fetch_ftp_url(self):
        """Test fetch with FTP URL (unsupported)."""
        fetcher = ContentFetcher()

        with pytest.raises(ValueError, match="Invalid URL"):
            await fetcher.fetch("ftp://example.com/file")

    @pytest.mark.asyncio
    async def test_fetch_successful_response(self):
        """Test successful fetch with mocked response."""
        fetcher = ContentFetcher()

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert "Test content" in result

    @pytest.mark.asyncio
    async def test_fetch_retry_on_500_error(self):
        """Test retry on 500 server error."""
        fetcher = ContentFetcher(max_retries=2, retry_delay=0.1)

        with patch('aiohttp.ClientSession.get') as mock_get:
            # First call fails
            mock_response_fail = AsyncMock()
            mock_response_fail.status = 500
            mock_response_fail.text = AsyncMock(return_value="Server Error")

            # Second call succeeds
            mock_response_success = AsyncMock()
            mock_response_success.status = 200
            mock_response_success.text = AsyncMock(return_value="<html>Success</html>")

            mock_get.return_value.__aenter__.side_effect = [
                mock_response_fail,
                mock_response_success,
            ]

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert "Success" in result
                assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_max_retries_exceeded(self):
        """Test failure after max retries exceeded."""
        fetcher = ContentFetcher(max_retries=2, retry_delay=0.1)

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Server Error")
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                with pytest.raises(RuntimeError, match="Failed to fetch"):
                    await fetcher.fetch("https://example.com")

                assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_404_error(self):
        """Test 404 not found error."""
        fetcher = ContentFetcher()

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Not Found")
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                with pytest.raises(RuntimeError, match="Failed to fetch"):
                    await fetcher.fetch("https://example.com/notfound")

    @pytest.mark.asyncio
    async def test_fetch_timeout(self):
        """Test fetch timeout."""
        fetcher = ContentFetcher(timeout=1, max_retries=1)

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.side_effect = asyncio.TimeoutError()

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                with pytest.raises(RuntimeError, match="Failed to fetch"):
                    await fetcher.fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_fetch_connection_error(self):
        """Test connection error."""
        fetcher = ContentFetcher(max_retries=1)

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.side_effect = aiohttp.ClientError("Connection failed")

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                with pytest.raises(RuntimeError, match="Failed to fetch"):
                    await fetcher.fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_fetch_with_custom_user_agent(self):
        """Test fetch with custom user agent."""
        fetcher = ContentFetcher(user_agent="MyBot/1.0")

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html>Content</html>")
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                await fetcher.fetch("https://example.com")

                # Verify user agent was used
                call_kwargs = mock_get.call_args[1]
                assert "User-Agent" in call_kwargs.get("headers", {})

    @pytest.mark.asyncio
    async def test_fetch_with_proxy(self):
        """Test fetch with proxy."""
        fetcher = ContentFetcher(proxy="http://proxy.example.com:8080")

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html>Content</html>")
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                await fetcher.fetch("https://example.com")

                # Verify proxy was configured
                assert mock_session.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_redirect_handling(self):
        """Test handling of redirects."""
        fetcher = ContentFetcher()

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html>Redirected content</html>")
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert "Redirected content" in result

    @pytest.mark.asyncio
    async def test_fetch_gzip_compression(self):
        """Test handling of gzip compressed content."""
        fetcher = ContentFetcher()

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html>Compressed content</html>")
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert "Compressed content" in result


class TestContentFetcherEdgeCases:
    """Edge case tests for ContentFetcher."""

    @pytest.mark.asyncio
    async def test_fetch_large_html(self):
        """Test fetching large HTML content."""
        fetcher = ContentFetcher()

        large_content = "<html><body>" + "x" * 1000000 + "</body></html>"

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=large_content)
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert len(result) == len(large_content)

    @pytest.mark.asyncio
    async def test_fetch_unicode_content(self):
        """Test handling of unicode content."""
        fetcher = ContentFetcher()

        unicode_content = "<html><body>中文内容 日本語 한국어</body></html>"

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=unicode_content)
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert "中文内容" in result

    @pytest.mark.asyncio
    async def test_fetch_empty_response(self):
        """Test handling of empty response."""
        fetcher = ContentFetcher()

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="")
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert result == ""

    @pytest.mark.asyncio
    async def test_fetch_malformed_html(self):
        """Test handling of malformed HTML."""
        fetcher = ContentFetcher()

        malformed_html = "<html><body><div>Unclosed tags"

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=malformed_html)
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await fetcher.fetch("https://example.com")

                assert "Unclosed tags" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])