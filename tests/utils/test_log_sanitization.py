"""
Tests for Log Sanitization.
"""

import pytest
from learning_assistant.utils.log_sanitization import (
    sanitize_string,
    sanitize_dict,
    sanitize_url,
    sanitize_cookie_string,
    mask_sensitive_value,
    SanitizingFilter,
)


class TestSanitizeString:
    """Tests for string sanitization."""

    def test_sanitize_api_key(self):
        """Test API key is sanitized."""
        text = "API key: sk-abc123def456ghi789"
        sanitized = sanitize_string(text)
        assert "sk-abc123" not in sanitized
        assert "[API_KEY_REDACTED]" in sanitized or "[REDACTED]" in sanitized

    def test_sanitize_openai_key(self):
        """Test OpenAI key format is sanitized."""
        text = "Using key: sk-proj-1234567890abcdef"
        sanitized = sanitize_string(text)
        assert "sk-proj-" not in sanitized

    def test_sanitize_password(self):
        """Test password is sanitized."""
        text = "password=supersecret123"
        sanitized = sanitize_string(text)
        assert "supersecret123" not in sanitized

    def test_sanitize_url_credentials(self):
        """Test URL with credentials is sanitized."""
        text = "https://user:pass@example.com"
        sanitized = sanitize_string(text)
        assert "user:pass" not in sanitized

    def test_no_change_normal_text(self):
        """Test normal text is unchanged."""
        text = "Processing video https://example.com/video"
        sanitized = sanitize_string(text)
        assert sanitized == text


class TestSanitizeDict:
    """Tests for dictionary sanitization."""

    def test_sanitize_api_key_field(self):
        """Test API key field is sanitized."""
        data = {"api_key": "sk-1234567890"}
        sanitized = sanitize_dict(data)
        assert sanitized["api_key"] == "[REDACTED]"

    def test_sanitize_nested_dict(self):
        """Test nested dictionary sanitization."""
        data = {
            "config": {
                "llm": {
                    "api_key": "secret-key",
                }
            }
        }
        sanitized = sanitize_dict(data)
        assert sanitized["config"]["llm"]["api_key"] == "[REDACTED]"

    def test_preserve_non_sensitive(self):
        """Test non-sensitive values preserved."""
        data = {"model": "gpt-4", "temperature": 0.3}
        sanitized = sanitize_dict(data)
        assert sanitized["model"] == "gpt-4"
        assert sanitized["temperature"] == 0.3

    def test_sanitize_empty_value(self):
        """Test empty sensitive value preserved."""
        data = {"api_key": None}
        sanitized = sanitize_dict(data)
        assert sanitized["api_key"] is None

    def test_custom_sensitive_keys(self):
        """Test custom sensitive keys."""
        data = {"custom_secret": "value123"}
        sanitized = sanitize_dict(data, sensitive_keys={"custom_secret"})
        assert sanitized["custom_secret"] == "[REDACTED]"


class TestSanitizeUrl:
    """Tests for URL sanitization."""

    def test_url_with_credentials(self):
        """Test URL credentials removed."""
        url = "https://admin:password@api.example.com"
        sanitized = sanitize_url(url)
        assert "admin:password" not in sanitized

    def test_url_without_credentials(self):
        """Test URL without credentials unchanged."""
        url = "https://api.example.com/data"
        sanitized = sanitize_url(url)
        assert sanitized == url


class TestSanitizeCookieString:
    """Tests for cookie string sanitization."""

    def test_sanitize_long_cookie(self):
        """Test long cookie value sanitized."""
        cookie = "sessionid=abcdefghijklmnopqrstuvwxyz123456"
        sanitized = sanitize_cookie_string(cookie)
        assert "abcdefghijklmnopqrstuvwxyz" not in sanitized

    def test_preserve_short_cookie(self):
        """Test short cookie value preserved."""
        cookie = "lang=en"
        sanitized = sanitize_cookie_string(cookie)
        assert sanitized == cookie


class TestMaskSensitiveValue:
    """Tests for value masking."""

    def test_mask_long_value(self):
        """Test long value masked."""
        masked = mask_sensitive_value("sk-1234567890abcdef")
        assert "sk-12" in masked
        assert "[REDACTED]" in masked

    def test_mask_short_value(self):
        """Test short value fully masked."""
        masked = mask_sensitive_value("abc")
        assert masked == "[MASKED]"

    def test_mask_empty_value(self):
        """Test empty value masked."""
        masked = mask_sensitive_value("")
        assert masked == "[MASKED]"

    def test_custom_visible_chars(self):
        """Test custom visible characters."""
        masked = mask_sensitive_value("abcdefgh", visible_chars=2)
        assert "ab" in masked


class TestSanitizingFilter:
    """Tests for SanitizingFilter class."""

    def test_filter_sanitizes_message(self):
        """Test filter sanitizes log message."""
        filter_obj = SanitizingFilter()
        record = {"message": "API key: sk-123456789"}
        filter_obj(record)
        assert "sk-123456789" not in str(record["message"])

    def test_filter_always_returns_true(self):
        """Test filter always allows record."""
        filter_obj = SanitizingFilter()
        record = {"message": "test"}
        result = filter_obj(record)
        assert result is True

    def test_filter_sanitizes_extra(self):
        """Test filter sanitizes extra data."""
        filter_obj = SanitizingFilter()
        record = {
            "message": "test",
            "extra": {"api_key": "secret123"}
        }
        filter_obj(record)
        assert record["extra"]["api_key"] == "[REDACTED]"