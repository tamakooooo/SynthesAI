"""
Authentication Manager for Learning Assistant.

Provides unified interface for platform authentication.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseAuthProvider
from .models import AuthInfo, AuthResult
from .providers import BilibiliAuthProvider, DouyinAuthProvider


class AuthManager:
    """
    Authentication manager facade.

    Manages authentication providers for different platforms.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize AuthManager.

        Args:
            config: Authentication configuration from modules.yaml
        """
        self.config = config
        self.cookie_dir = Path("config/cookies")
        self.cookie_dir.mkdir(parents=True, exist_ok=True)

        # Initialize providers
        self.providers: dict[str, BaseAuthProvider] = {}

        self._init_providers()

        logger.info(
            f"AuthManager initialized with providers: {list(self.providers.keys())}"
        )

    def _init_providers(self) -> None:
        """Initialize authentication providers based on config."""
        providers_config = self.config.get("providers", {})

        # Bilibili provider
        if providers_config.get("bilibili", {}).get("enabled", False):
            bilibili_config = providers_config["bilibili"]
            self.providers["bilibili"] = BilibiliAuthProvider(
                cookie_dir=str(self.cookie_dir),
                timeout=bilibili_config.get("timeout", 180),
                poll_interval=bilibili_config.get("poll_interval", 2),
            )
            logger.info("BilibiliAuthProvider initialized")

        # Douyin provider
        if providers_config.get("douyin", {}).get("enabled", False):
            douyin_config = providers_config["douyin"]
            self.providers["douyin"] = DouyinAuthProvider(
                cookie_dir=str(self.cookie_dir),
            )
            logger.info("DouyinAuthProvider initialized")

    def login(self, platform: str, timeout: int | None = None) -> AuthResult:
        """
        Login to a platform.

        Args:
            platform: Platform name (e.g., "bilibili")
            timeout: QR code timeout in seconds

        Returns:
            Authentication result

        Raises:
            ValueError: If platform not supported
        """
        if platform not in self.providers:
            raise ValueError(
                f"Platform '{platform}' not supported. "
                f"Available: {list(self.providers.keys())}"
            )

        provider = self.providers[platform]
        logger.info(f"Logging in to {platform}...")

        return provider.login(timeout=timeout)

    def check_status(self, platform: str) -> AuthInfo:
        """
        Check authentication status for a platform.

        Args:
            platform: Platform name

        Returns:
            Authentication info

        Raises:
            ValueError: If platform not supported
        """
        if platform not in self.providers:
            raise ValueError(f"Platform '{platform}' not supported")

        provider = self.providers[platform]
        return provider.check_status()

    def logout(self, platform: str) -> bool:
        """
        Logout from a platform.

        Args:
            platform: Platform name

        Returns:
            True if logout successful

        Raises:
            ValueError: If platform not supported
        """
        if platform not in self.providers:
            raise ValueError(f"Platform '{platform}' not supported")

        provider = self.providers[platform]
        return provider.logout()

    def is_authenticated(self, platform: str) -> bool:
        """
        Check if authenticated with a platform.

        Args:
            platform: Platform name

        Returns:
            True if authenticated
        """
        if platform not in self.providers:
            return False

        provider = self.providers[platform]
        return provider.is_authenticated()

    def get_supported_platforms(self) -> list[str]:
        """
        Get list of supported platforms.

        Returns:
            List of platform names
        """
        return list(self.providers.keys())


# Export public API
__all__ = [
    "AuthManager",
    "BilibiliAuthProvider",
    "DouyinAuthProvider",
]
