"""
Authentication models for Learning Assistant.

Defines data models for authentication sessions, results, and cookies.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AuthStatus(str, Enum):
    """Authentication status."""

    NOT_AUTHENTICATED = "not_authenticated"
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    INVALID = "invalid"


class QRStatus(str, Enum):
    """QR code scan status."""

    WAITING = "waiting"  # 86101 - Not scanned
    SCANNED = "scanned"  # 86090 - Scanned but not confirmed
    CONFIRMED = "confirmed"  # 0 - Login successful
    EXPIRED = "expired"  # 86038 - QR code expired
    ERROR = "error"  # Other errors


@dataclass
class QRSession:
    """QR code authentication session."""

    session_id: str  # qrcode_key for Bilibili
    qr_url: str  # URL to encode in QR code
    created_at: datetime
    expires_at: datetime
    platform: str

    def is_expired(self) -> bool:
        """Check if QR session is expired."""
        return datetime.now() > self.expires_at


@dataclass
class CookieData:
    """Cookie data structure."""

    name: str
    value: str
    domain: str
    path: str = "/"
    secure: bool = False
    expires: int | None = None  # Unix timestamp or None for session cookies

    def to_netscape_line(self) -> str:
        """
        Convert to Netscape cookie format line.

        Format: domain\tflag\tpath\tsecure\texpiration\tname\tvalue
        """
        flag = "TRUE" if self.domain.startswith(".") else "FALSE"
        secure_str = "TRUE" if self.secure else "FALSE"
        expires = self.expires if self.expires else 0

        return f"{self.domain}\t{flag}\t{self.path}\t{secure_str}\t{expires}\t{self.name}\t{self.value}"


@dataclass
class AuthResult:
    """Authentication result."""

    success: bool
    platform: str
    cookies: list[CookieData] | None = None
    user_id: str | None = None
    username: str | None = None
    error_message: str | None = None
    cookie_file: str | None = None  # Path to saved cookie file


@dataclass
class AuthInfo:
    """Authentication information for a platform."""

    platform: str
    status: AuthStatus
    user_id: str | None = None
    username: str | None = None
    cookie_file: str | None = None
    authenticated_at: datetime | None = None
    expires_at: datetime | None = None
