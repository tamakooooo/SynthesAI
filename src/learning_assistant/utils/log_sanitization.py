"""
Log Sanitization for SynthesAI.

Provides utilities to sanitize sensitive data in logs, preventing
exposure of API keys, cookies, and other sensitive information.
"""

import re
from typing import Any, Optional


# Patterns for sensitive data detection
SENSITIVE_PATTERNS = {
    # API keys
    "api_key": [
        r"(api_key|apikey|api-key)\s*[=:]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?",
        r"(openai_api_key|anthropic_api_key|deepseek_api_key)\s*[=:]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?",
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI key format
        r"sk-ant-[a-zA-Z0-9]{20,}",  # Anthropic key format
    ],
    # Cookies
    "cookie": [
        r"(cookie|cookies)\s*[=:]\s*['\"]?[a-zA-Z0-9_=;:\-.\s]{50,}['\"]?",
        r"SESSDATA=[a-zA-Z0-9_-]+",
        r"bili_jct=[a-zA-Z0-9_-]+",
        r"DedeUserID=[a-zA-Z0-9_-]+",
    ],
    # Tokens
    "token": [
        r"(token|access_token|auth_token)\s*[=:]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?",
        r"Bearer\s+[a-zA-Z0-9_-]{20,}",
    ],
    # Passwords
    "password": [
        r"(password|passwd|pwd)\s*[=:]\s*['\"]?[^'\"\s]{8,}['\"]?",
    ],
    # URLs with credentials
    "url_credentials": [
        r"https?://[^:]+:[^@]+@",  # URL with username:password
    ],
}

# Replacement strings
REPLACEMENTS = {
    "api_key": "[API_KEY_REDACTED]",
    "cookie": "[COOKIE_REDACTED]",
    "token": "[TOKEN_REDACTED]",
    "password": "[PASSWORD_REDACTED]",
    "url_credentials": "[CREDENTIALS_REDACTED]",
}


def sanitize_string(text: str) -> str:
    """
    Sanitize a string by removing sensitive data.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text with sensitive data replaced
    """
    sanitized = text

    for category, patterns in SENSITIVE_PATTERNS.items():
        replacement = REPLACEMENTS.get(category, "[REDACTED]")
        for pattern in patterns:
            try:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            except re.error:
                # Skip invalid patterns
                continue

    return sanitized


def sanitize_dict(data: dict, sensitive_keys: Optional[set] = None) -> dict:
    """
    Sanitize a dictionary by masking sensitive values.

    Args:
        data: Dictionary to sanitize
        sensitive_keys: Set of keys to treat as sensitive

    Returns:
        Sanitized dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = {
            "api_key",
            "apikey",
            "api-key",
            "openai_api_key",
            "anthropic_api_key",
            "deepseek_api_key",
            "password",
            "passwd",
            "pwd",
            "token",
            "access_token",
            "auth_token",
            "secret",
            "cookie",
            "cookies",
            "session_id",
            "sessionid",
            "SESSDATA",
            "bili_jct",
            "DedeUserID",
        }

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower().replace("-", "_")

        if key_lower in sensitive_keys:
            if value:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, sensitive_keys)
        elif isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        else:
            sanitized[key] = value

    return sanitized


def sanitize_log_message(message: str) -> str:
    """
    Sanitize a log message.

    Args:
        message: Log message to sanitize

    Returns:
        Sanitized log message
    """
    return sanitize_string(message)


def sanitize_exception(exc: Exception) -> str:
    """
    Sanitize exception message.

    Args:
        exc: Exception to sanitize

    Returns:
        Sanitized exception string
    """
    return sanitize_string(str(exc))


class SanitizingFilter:
    """
    Loguru filter that sanitizes sensitive data.

    Usage with loguru:
        from loguru import logger
        from learning_assistant.utils.log_sanitization import SanitizingFilter

        logger.add(
            "logs/app.log",
            filter=SanitizingFilter(),
            format="{time} {level} {message}"
        )
    """

    def __call__(self, record: dict) -> bool:
        """
        Filter and sanitize log record.

        Args:
            record: Loguru record dict

        Returns:
            True (always allow record, but sanitize)
        """
        # Sanitize message
        if "message" in record:
            record["message"] = sanitize_log_message(str(record["message"]))

        # Sanitize extra data
        if "extra" in record and isinstance(record["extra"], dict):
            record["extra"] = sanitize_dict(record["extra"])

        return True


def setup_sanitized_logging():
    """
    Setup loguru with sanitization.

    Removes default handler and adds sanitized handlers.
    """
    from loguru import logger

    # Remove default handler
    logger.remove()

    # Add sanitized stdout handler
    logger.add(
        lambda msg: print(sanitize_log_message(msg), end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "{message}",
        level="INFO",
    )

    # Add sanitized file handler
    logger.add(
        "logs/synthesai.log",
        filter=SanitizingFilter(),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
    )


def sanitize_url(url: str) -> str:
    """
    Sanitize URL by removing credentials.

    Args:
        url: URL to sanitize

    Returns:
        URL with credentials removed
    """
    # Remove username:password from URL
    sanitized = re.sub(
        r"https?://[^:]+:[^@]+@",
        "https://[CREDENTIALS_REDACTED]@",
        url
    )
    return sanitized


def sanitize_cookie_string(cookie: str) -> str:
    """
    Sanitize cookie string.

    Args:
        cookie: Cookie string to sanitize

    Returns:
        Sanitized cookie string
    """
    # Replace long cookie values
    return re.sub(
        r"([^=]+)=([^;]+)",
        lambda m: f"{m.group(1)}=[COOKIE_VALUE_REDACTED]" if len(m.group(2)) > 10 else m.group(0),
        cookie
    )


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive value, showing only a few characters.

    Args:
        value: Value to mask
        visible_chars: Number of visible characters at start

    Returns:
        Masked value
    """
    if not value or len(value) <= visible_chars:
        return "[MASKED]"

    return f"{value[:visible_chars]}...[REDACTED]"