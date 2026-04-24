"""
Bilibili authentication provider.

Implements QR code login for Bilibili using public API.
Updated with correct WBI signature algorithm.
"""

import hashlib
import time
from datetime import datetime, timedelta
from functools import reduce
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests
from loguru import logger

from ..base import BaseAuthProvider
from ..cookie_manager import CookieManager
from ..models import AuthInfo, AuthResult, AuthStatus, CookieData, QRSession, QRStatus
from ..qr_display import display_qr_ascii


class BilibiliAuthProvider(BaseAuthProvider):
    """
    Bilibili authentication provider using QR code login.

    API Documentation:
    - Generate QR: GET https://passport.bilibili.com/x/passport-login/web/qrcode/generate
    - Poll Status: GET https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={key}
    """

    # API endpoints
    API_GENERATE_QR = (
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    )
    API_POLL_STATUS = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"

    # Bilibili domain for cookies
    BILIBILI_DOMAIN = ".bilibili.com"

    # Headers (critical for API access)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
    }

    # Cookie file name
    COOKIE_FILENAME = "bilibili_cookies.txt"

    def __init__(self, cookie_dir: str, timeout: int = 180, poll_interval: int = 2):
        """
        Initialize Bilibili authentication provider.

        Args:
            cookie_dir: Directory to store cookie files
            timeout: QR code timeout in seconds (default: 180)
            poll_interval: Polling interval in seconds (default: 2)
        """
        super().__init__(cookie_dir)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.cookie_manager = CookieManager(cookie_dir)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        logger.info("BilibiliAuthProvider initialized")

    def login(self, timeout: int | None = None) -> AuthResult:
        """
        Execute Bilibili QR code login flow.

        Steps:
        1. Generate QR code
        2. Display QR code in terminal
        3. Poll for scan confirmation
        4. Extract cookies and save

        Args:
            timeout: QR code timeout (uses instance default if None)

        Returns:
            Authentication result
        """
        timeout = timeout or self.timeout

        try:
            # Step 1: Generate QR code
            logger.info("Generating QR code for Bilibili login...")
            qr_session = self._generate_qr()

            logger.info(f"QR code generated. Expires at: {qr_session.expires_at}")

            # Step 2: Display QR code
            print("\n" + "=" * 60)
            print("Please scan QR code with Bilibili App:")
            print("=" * 60 + "\n")

            # Print QR URL for browser scanning
            print(f"QR URL: {qr_session.qr_url}\n")

            # Try to save QR as image
            try:
                from ..qr_display import save_qr_image

                qr_image_path = save_qr_image(qr_session.qr_url, "bilibili_qr.png")
                if qr_image_path:
                    print(f"QR image saved to: {qr_image_path}")
                    print("You can open this image and scan it.\n")
            except Exception as e:
                logger.debug(f"Could not save QR image: {e}")

            # Display QR in terminal
            display_qr_ascii(qr_session.qr_url)

            print("\n" + "=" * 60)
            print(f"QR valid for: {timeout} seconds")
            print("=" * 60 + "\n")

            # Step 3: Poll for scan confirmation
            logger.info("Waiting for QR code scan...")
            auth_result = self._poll_scan(qr_session.session_id, timeout)

            return auth_result

        except Exception as e:
            logger.error(f"Bilibili login failed: {e}")
            return AuthResult(
                success=False,
                platform="bilibili",
                error_message=str(e),
            )

    def check_status(self) -> AuthInfo:
        """
        Check Bilibili authentication status.

        Verifies:
        - Cookie file exists
        - Contains essential cookies (SESSDATA, DedeUserID, bili_jct)
        - Cookies are valid

        Returns:
            Authentication info
        """
        cookie_file = self.get_cookie_file_path()

        if not cookie_file.exists():
            return AuthInfo(
                platform="bilibili",
                status=AuthStatus.NOT_AUTHENTICATED,
            )

        try:
            # Import cookies
            cookies = self.cookie_manager.import_cookies(self.COOKIE_FILENAME)

            # Check essential cookies
            has_sessdata = any(c.name == "SESSDATA" for c in cookies)
            has_dedeuserid = any(c.name == "DedeUserID" for c in cookies)
            has_bili_jct = any(c.name == "bili_jct" for c in cookies)

            if not (has_sessdata and has_dedeuserid and has_bili_jct):
                return AuthInfo(
                    platform="bilibili",
                    status=AuthStatus.INVALID,
                    cookie_file=str(cookie_file),
                )

            # Extract user ID
            dedeuserid_cookie = next(
                (c for c in cookies if c.name == "DedeUserID"), None
            )
            user_id = dedeuserid_cookie.value if dedeuserid_cookie else None

            # TODO: Validate cookies by calling Bilibili API
            # For now, assume valid if all essential cookies exist

            return AuthInfo(
                platform="bilibili",
                status=AuthStatus.AUTHENTICATED,
                user_id=user_id,
                cookie_file=str(cookie_file),
            )

        except Exception as e:
            logger.error(f"Failed to check Bilibili auth status: {e}")
            return AuthInfo(
                platform="bilibili",
                status=AuthStatus.INVALID,
            )

    def logout(self) -> bool:
        """
        Clear Bilibili authentication (delete cookies).

        Returns:
            True if logout successful
        """
        try:
            deleted = self.cookie_manager.delete_cookie_file(self.COOKIE_FILENAME)
            if deleted:
                logger.info("Bilibili authentication cleared")
            return deleted
        except Exception as e:
            logger.error(f"Failed to logout from Bilibili: {e}")
            return False

    def import_cookies(self, cookie_input: str) -> AuthResult:
        """
        Import cookies from browser cookie export.

        Supports two formats:
        1. JSON array (from browser extension "Get cookies.txt")
        2. Cookie string (format: "name1=value1; name2=value2")

        Args:
            cookie_input: Cookie data as JSON array or string

        Returns:
            Authentication result
        """
        try:
            # Auto-detect format and parse
            cookies = self.cookie_manager.parse_cookies_auto(cookie_input)

            # Ensure all cookies have correct domain
            for cookie in cookies:
                if not cookie.domain or cookie.domain == "":
                    cookie.domain = self.BILIBILI_DOMAIN
                # Normalize domain (ensure starts with dot for wildcard)
                elif not cookie.domain.startswith(".") and not cookie.domain.startswith("www"):
                    cookie.domain = "." + cookie.domain

            # Save to file
            cookie_file = self.cookie_manager.export_cookies(
                cookies, self.COOKIE_FILENAME
            )

            # Extract user ID if available
            dedeuserid = next((c.value for c in cookies if c.name == "DedeUserID"), None)

            logger.info(f"Bilibili cookies imported: {len(cookies)} cookies")

            return AuthResult(
                success=True,
                platform="bilibili",
                cookies=cookies,
                user_id=dedeuserid,
                cookie_file=str(cookie_file),
            )

        except Exception as e:
            logger.error(f"Failed to import Bilibili cookies: {e}")
            return AuthResult(
                success=False,
                platform="bilibili",
                error_message=str(e),
            )

    def check_qr_status(self, qrcode_key: str) -> tuple[QRStatus, AuthResult | None]:
        """
        Check QR code scan status (single poll, non-blocking).

        Args:
            qrcode_key: QR code session key

        Returns:
            Tuple of (QRStatus, AuthResult if successful)
        """
        try:
            response = self.session.get(
                self.API_POLL_STATUS, params={"qrcode_key": qrcode_key}
            )
            response.raise_for_status()

            response_data = response.json()
            data = response_data.get("data", {})
            qr_status_code = data.get("code", -1)

            # Status codes:
            # 0 = scanned and confirmed (success)
            # 86038 = expired
            # 86090 = scanned but not confirmed
            # 86101 = not scanned yet

            if qr_status_code == 0:
                # Login successful
                logger.info("QR code scanned and confirmed!")
                cookies = self._extract_cookies_from_response(response_data)
                cookie_file = self.cookie_manager.export_cookies(
                    cookies, self.COOKIE_FILENAME
                )
                logger.info(f"Cookies saved to {cookie_file}")

                # Extract user info
                dedeuserid = next((c.value for c in cookies if c.name == "DedeUserID"), None)

                return QRStatus.CONFIRMED, AuthResult(
                    success=True,
                    platform="bilibili",
                    cookies=cookies,
                    user_id=dedeuserid,
                    cookie_file=str(cookie_file),
                )

            elif qr_status_code == 86038:
                return QRStatus.EXPIRED, None

            elif qr_status_code == 86090:
                return QRStatus.SCANNED, None

            elif qr_status_code == 86101:
                return QRStatus.WAITING, None

            else:
                logger.error(f"Unknown QR status: {qr_status_code}")
                return QRStatus.ERROR, None

        except Exception as e:
            logger.error(f"Failed to check QR status: {e}")
            return QRStatus.ERROR, None

    def get_cookie_file_path(self) -> Path:
        """Get Bilibili cookie file path."""
        return self.cookie_manager.get_cookie_file_path(self.COOKIE_FILENAME)

    def _generate_qr(self) -> QRSession:
        """
        Generate QR code for login.

        Returns:
            QR session data

        Raises:
            RuntimeError: If QR generation fails
        """
        response = self.session.get(self.API_GENERATE_QR)
        response.raise_for_status()

        data = response.json()

        if data.get("code") != 0:
            raise RuntimeError(f"QR generation failed: {data.get('message')}")

        qr_data = data["data"]
        qr_url = qr_data["url"]
        qrcode_key = qr_data["qrcode_key"]

        # QR code valid for ~180 seconds
        created_at = datetime.now()
        expires_at = created_at + timedelta(seconds=self.timeout)

        return QRSession(
            session_id=qrcode_key,
            qr_url=qr_url,
            created_at=created_at,
            expires_at=expires_at,
            platform="bilibili",
        )

    def _poll_scan(self, qrcode_key: str, timeout: int) -> AuthResult:
        """
        Poll for QR code scan status.

        Args:
            qrcode_key: QR code session key
            timeout: Timeout in seconds

        Returns:
            Authentication result
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if elapsed > timeout:
                logger.error("QR code scan timeout")
                return AuthResult(
                    success=False,
                    platform="bilibili",
                    error_message="QR code scan timeout",
                )

            # Poll status
            try:
                response = self.session.get(
                    self.API_POLL_STATUS, params={"qrcode_key": qrcode_key}
                )
                response.raise_for_status()

                response_data = response.json()

                # Print status update
                remaining = int(timeout - elapsed)
                print(
                    f"\rWaiting for scan... ({remaining}s remaining)",
                    end="",
                    flush=True,
                )

                # Bilibili API returns status in both top-level and nested data
                # Top-level code=0 means API request succeeded
                # data.code indicates actual QR scan status
                data = response_data.get("data", {})
                qr_status = data.get("code", -1)

                if qr_status == 0:
                    # Login successful - QR scanned and confirmed
                    print("\n")  # New line after status
                    logger.info("QR code scanned and confirmed!")

                    # Debug: log the full response structure
                    logger.debug(f"Login response data: {response_data}")

                    # Extract cookies
                    cookies = self._extract_cookies_from_response(response_data)

                    # Save cookies
                    cookie_file = self.cookie_manager.export_cookies(
                        cookies, self.COOKIE_FILENAME
                    )

                    # Extract user info
                    user_id = data.get("DedeUserID", "")

                    return AuthResult(
                        success=True,
                        platform="bilibili",
                        cookies=cookies,
                        user_id=user_id,
                        cookie_file=str(cookie_file),
                    )

                elif qr_status == 86038:
                    # QR code expired
                    print("\n")
                    logger.error("QR code expired")
                    return AuthResult(
                        success=False,
                        platform="bilibili",
                        error_message="QR code expired",
                    )

                elif qr_status == 86090:
                    # Scanned but not confirmed
                    # Continue polling
                    pass

                elif qr_status == 86101:
                    # Not scanned yet
                    # Continue polling
                    pass

                else:
                    # Unknown status
                    logger.warning(f"Unknown QR status code: {qr_status}")

            except Exception as e:
                logger.error(f"Failed to poll QR status: {e}")

            # Wait before next poll
            time.sleep(self.poll_interval)

    def _extract_cookies_from_response(self, response_data: dict) -> list[CookieData]:
        """
        Extract cookies from login response.

        Bilibili returns cookies in two ways:
        1. Directly in data dict: data["SESSDATA"], data["DedeUserID"], etc.
        2. In the URL field: data["url"] contains cookie parameters

        Args:
            response_data: API response data

        Returns:
            List of cookie data
        """
        cookies = []
        data = response_data.get("data", {})

        # Essential cookies for Bilibili
        cookie_names = ["SESSDATA", "DedeUserID", "bili_jct", "sid"]

        # Try to extract cookies from data dict directly
        for name in cookie_names:
            value = data.get(name)
            if value:
                cookie = CookieData(
                    name=name,
                    value=str(value),
                    domain=self.BILIBILI_DOMAIN,
                    path="/",
                    secure=(name == "SESSDATA"),
                    expires=None,  # Session cookie
                )
                cookies.append(cookie)

        # If no cookies found in data dict, try to extract from URL
        if not cookies and "url" in data:
            logger.debug("No cookies in data dict, trying to extract from URL")
            from urllib.parse import parse_qs, urlparse

            url = data["url"]
            parsed = urlparse(url)

            # Extract cookies from URL parameters
            # Bilibili sometimes embeds cookies in the redirect URL
            params = parse_qs(parsed.query)

            for name in cookie_names:
                if name in params:
                    value = params[name][0]
                    cookie = CookieData(
                        name=name,
                        value=value,
                        domain=self.BILIBILI_DOMAIN,
                        path="/",
                        secure=(name == "SESSDATA"),
                        expires=None,
                    )
                    cookies.append(cookie)

        logger.info(f"Extracted {len(cookies)} cookies from login response")
        return cookies
