"""
Content Fetcher - Shared service for fetching web content.

Fetches HTML content from URLs with retry and error handling.
Can be used across multiple modules (link_learning, vocabulary, etc).
"""

import asyncio
from typing import Optional

import aiohttp
from loguru import logger


class ContentFetcher:
    """
    Content fetcher.

    Fetches web content from URLs with configurable timeout and retry.
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2,
        use_playwright: bool = False,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> None:
        """
        Initialize content fetcher.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            use_playwright: Whether to use Playwright for dynamic pages
            user_agent: Custom user agent string
            proxy: Proxy server URL
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_playwright = use_playwright
        self.user_agent = user_agent or self._default_user_agent()
        self.proxy = proxy

        logger.debug(
            f"ContentFetcher initialized: timeout={timeout}, retries={max_retries}"
        )

    def _default_user_agent(self) -> str:
        """
        Get default user agent string.

        Returns:
            User agent string
        """
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    async def fetch(self, url: str) -> str:
        """
        Fetch HTML content from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content

        Raises:
            ValueError: If URL is invalid
            RuntimeError: If fetch fails after retries
        """
        if not url or not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {url}")

        logger.info(f"Fetching URL: {url}")

        # Try Playwright if enabled
        if self.use_playwright:
            return await self._fetch_with_playwright(url)

        # Use aiohttp for standard requests
        return await self._fetch_with_aiohttp(url)

    async def _fetch_with_aiohttp(self, url: str) -> str:
        """
        Fetch using aiohttp.

        Args:
            url: URL to fetch

        Returns:
            HTML content

        Raises:
            RuntimeError: If fetch fails after retries
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries}")

                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        url,
                        headers=headers,
                        proxy=self.proxy,
                    ) as response:
                        if response.status == 200:
                            html = await response.text()
                            logger.info(f"Successfully fetched: {url}")
                            return html
                        elif response.status == 404:
                            raise RuntimeError(f"Page not found: {url}")
                        elif response.status >= 500:
                            raise RuntimeError(f"Server error: {response.status}")
                        else:
                            raise RuntimeError(f"HTTP error: {response.status}")

            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise RuntimeError(f"Timeout after {self.max_retries} retries")

            except aiohttp.ClientError as e:
                logger.warning(f"Client error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise RuntimeError(
                    f"Fetch failed after {self.max_retries} retries: {e}"
                )

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} retries")

    async def _fetch_with_playwright(self, url: str) -> str:
        """
        Fetch using Playwright for dynamic pages.

        Args:
            url: URL to fetch

        Returns:
            HTML content

        Raises:
            RuntimeError: If Playwright is not available or fetch fails
        """
        try:
            from playwright.async_api import async_playwright

            logger.debug("Using Playwright for dynamic page")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Set user agent
                await page.set_extra_http_headers({"User-Agent": self.user_agent})

                # Navigate to URL
                await page.goto(url, timeout=self.timeout * 1000)

                # Wait for page to load
                await page.wait_for_load_state("networkidle")

                # Get HTML content
                html = await page.content()

                await browser.close()

                logger.info(f"Successfully fetched with Playwright: {url}")
                return html

        except ImportError:
            logger.error(
                "Playwright not installed. Install with: pip install playwright"
            )
            raise RuntimeError(
                "Playwright not available. Install with: pip install playwright"
            )
        except Exception as e:
            logger.error(f"Playwright fetch failed: {e}")
            raise RuntimeError(f"Playwright fetch failed: {e}")