"""
Tests for authentication providers.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestBilibiliAuthProvider:
    """Tests for BilibiliAuthProvider."""

    def test_check_status_no_cookie_file(self, tmp_path: Path) -> None:
        """Test check_status when cookie file doesn't exist."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider
        from learning_assistant.auth.models import AuthStatus

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))
        result = provider.check_status()

        assert result.status == AuthStatus.NOT_AUTHENTICATED
        assert result.platform == "bilibili"

    def test_check_status_missing_essential_cookies(self, tmp_path: Path) -> None:
        """Test check_status when cookie file lacks essential cookies."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider
        from learning_assistant.auth.models import AuthStatus

        # Create cookie file without essential cookies
        cookie_file = tmp_path / "bilibili_cookies.txt"
        cookie_file.write_text("# Netscape HTTP Cookie File\n.bilibili.com\tFALSE\t/\tFALSE\t0\tsid\ttest123\n")

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))
        result = provider.check_status()

        assert result.status == AuthStatus.INVALID

    def test_check_status_valid_cookies_mocked(self, tmp_path: Path) -> None:
        """Test check_status with valid cookies (mocked API validation)."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider
        from learning_assistant.auth.models import AuthStatus

        # Create valid cookie file
        cookie_file = tmp_path / "bilibili_cookies.txt"
        cookie_file.write_text(
            "# Netscape HTTP Cookie File\n"
            ".bilibili.com\tFALSE\t/\tTRUE\t0\tSESSDATA\ttest_sessdata\n"
            ".bilibili.com\tFALSE\t/\tFALSE\t0\tDedeUserID\t12345\n"
            ".bilibili.com\tFALSE\t/\tFALSE\t0\tbili_jct\ttest_jct\n"
        )

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))

        # Mock the API validation
        with patch.object(provider, '_validate_cookies', return_value=(True, "TestUser")):
            result = provider.check_status()

            assert result.status == AuthStatus.AUTHENTICATED
            assert result.username == "TestUser"
            assert result.user_id == "12345"

    def test_check_status_expired_cookies_mocked(self, tmp_path: Path) -> None:
        """Test check_status when API validation shows cookies expired."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider
        from learning_assistant.auth.models import AuthStatus

        # Create valid cookie file
        cookie_file = tmp_path / "bilibili_cookies.txt"
        cookie_file.write_text(
            "# Netscape HTTP Cookie File\n"
            ".bilibili.com\tFALSE\t/\tTRUE\t0\tSESSDATA\texpired_sessdata\n"
            ".bilibili.com\tFALSE\t/\tFALSE\t0\tDedeUserID\t12345\n"
            ".bilibili.com\tFALSE\t/\tFALSE\t0\tbili_jct\texpired_jct\n"
        )

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))

        # Mock the API validation to return expired
        with patch.object(provider, '_validate_cookies', return_value=(False, None)):
            result = provider.check_status()

            assert result.status == AuthStatus.EXPIRED

    def test_validate_cookies_success(self, tmp_path: Path) -> None:
        """Test _validate_cookies with successful API response."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider
        from learning_assistant.auth.models import CookieData

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))

        cookies = [
            CookieData(name="SESSDATA", value="test", domain=".bilibili.com"),
            CookieData(name="DedeUserID", value="123", domain=".bilibili.com"),
        ]

        # Mock requests.get
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "isLogin": True,
                "uname": "TestUser",
                "mid": 123456,
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            is_valid, username = provider._validate_cookies(cookies)

            assert is_valid is True
            assert username == "TestUser"

    def test_validate_cookies_not_logged_in(self, tmp_path: Path) -> None:
        """Test _validate_cookies when user is not logged in."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider
        from learning_assistant.auth.models import CookieData

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))

        cookies = [
            CookieData(name="SESSDATA", value="invalid", domain=".bilibili.com"),
        ]

        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "isLogin": False,
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            is_valid, username = provider._validate_cookies(cookies)

            assert is_valid is False
            assert username is None

    def test_validate_cookies_api_error(self, tmp_path: Path) -> None:
        """Test _validate_cookies when API returns error."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider
        from learning_assistant.auth.models import CookieData

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))

        cookies = [
            CookieData(name="SESSDATA", value="test", domain=".bilibili.com"),
        ]

        mock_response = Mock()
        mock_response.json.return_value = {
            "code": -101,
            "message": "No login",
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            is_valid, username = provider._validate_cookies(cookies)

            assert is_valid is False
            assert username is None

    def test_logout(self, tmp_path: Path) -> None:
        """Test logout removes cookie file."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider

        # Create cookie file
        cookie_file = tmp_path / "bilibili_cookies.txt"
        cookie_file.write_text("test cookie data")

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))
        result = provider.logout()

        assert result is True
        assert not cookie_file.exists()

    def test_import_cookies_json_format(self, tmp_path: Path) -> None:
        """Test import_cookies with JSON format."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))

        # JSON format from browser extension
        json_cookies = '[{"name":"SESSDATA","value":"test123","domain":".bilibili.com"}]'

        result = provider.import_cookies(json_cookies)

        assert result.success is True
        assert result.platform == "bilibili"
        assert len(result.cookies) == 1

        # Check file was created
        cookie_file = tmp_path / "bilibili_cookies.txt"
        assert cookie_file.exists()

    def test_import_cookies_string_format(self, tmp_path: Path) -> None:
        """Test import_cookies with cookie string format."""
        from learning_assistant.auth.providers.bilibili import BilibiliAuthProvider

        provider = BilibiliAuthProvider(cookie_dir=str(tmp_path))

        # Cookie string format
        cookie_string = "SESSDATA=test123; DedeUserID=12345; bili_jct=abc123"

        result = provider.import_cookies(cookie_string)

        assert result.success is True
        assert len(result.cookies) >= 1