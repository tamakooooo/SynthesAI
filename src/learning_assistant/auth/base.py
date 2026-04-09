"""
Base authentication provider interface.

Defines the abstract interface for platform-specific authentication providers.
"""

from abc import ABC, abstractmethod

from .models import AuthInfo, AuthResult


class BaseAuthProvider(ABC):
    """
    Abstract base class for authentication providers.

    Each platform (Bilibili, Douyin, etc.) implements this interface.
    """

    def __init__(self, cookie_dir: str, **kwargs):
        """
        Initialize authentication provider.

        Args:
            cookie_dir: Directory to store cookie files
            **kwargs: Platform-specific configuration
        """
        self.cookie_dir = cookie_dir

    @abstractmethod
    def login(self, timeout: int = 180) -> AuthResult:
        """
        Execute authentication flow.

        For QR-based auth (Bilibili):
            1. Generate QR code
            2. Display QR code
            3. Poll for scan confirmation
            4. Extract and save cookies

        For manual import (Douyin):
            1. Display instructions
            2. User manually imports cookies
            3. Validate and save cookies

        Args:
            timeout: QR code timeout in seconds (default: 180)

        Returns:
            Authentication result with cookies and user info
        """
        pass

    @abstractmethod
    def check_status(self) -> AuthInfo:
        """
        Check authentication status.

        Verifies:
        - Cookie file exists
        - Cookies are valid (not expired)
        - User info is accessible

        Returns:
            Authentication info with status
        """
        pass

    @abstractmethod
    def logout(self) -> bool:
        """
        Clear authentication (delete cookies).

        Returns:
            True if logout successful, False otherwise
        """
        pass

    @abstractmethod
    def get_cookie_file_path(self) -> str:
        """
        Get cookie file path for this provider.

        Returns:
            Absolute path to cookie file
        """
        pass

    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        status = self.check_status()
        return status.status == "authenticated"
