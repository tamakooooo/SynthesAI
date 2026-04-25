"""
Helper functions for Agent integration.

Provides utilities for URL detection, platform identification,
and module suggestion to simplify Agent integration.
"""

import re
from urllib.parse import urlparse

# Platform URL patterns
_PLATFORM_PATTERNS = {
    "bilibili": [r"bilibili\.com/video", r"b23\.tv"],
    "youtube": [r"youtube\.com/watch", r"youtu\.be/", r"youtube\.com/shorts"],
    "douyin": [r"douyin\.com/video", r"douyin\.com/note"],
}

# Content type patterns
_VIDEO_PLATFORMS = {"bilibili", "youtube", "douyin"}
_ARTICLE_PATTERNS = [r"zhihu\.com", r"jianshu\.com", r"medium\.com", r"blog\.", r"\.com/article"]


def detect_content_type(url: str) -> str:
    """Detect URL content type.

    Returns:
        "video", "article", or "unknown"
    """
    for platform in _VIDEO_PLATFORMS:
        patterns = _PLATFORM_PATTERNS.get(platform, [])
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return "video"
    for pattern in _ARTICLE_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return "article"
    return "unknown"


def get_platform(url: str) -> str:
    """Identify the platform from URL.

    Returns:
        "bilibili", "youtube", "douyin", or "unknown"
    """
    for platform, patterns in _PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return "unknown"


def is_video_url(url: str) -> bool:
    """Check if URL points to a video."""
    return detect_content_type(url) == "video"


def is_article_url(url: str) -> bool:
    """Check if URL points to an article."""
    return detect_content_type(url) == "article"


def suggest_module(url: str) -> str:
    """Suggest which module to use for a given URL.

    Returns:
        "video_summary" or "link_learning"
    """
    content_type = detect_content_type(url)
    if content_type == "video":
        return "video_summary"
    return "link_learning"
