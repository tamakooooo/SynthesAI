"""
Authentication providers for different platforms.
"""

from .bilibili import BilibiliAuthProvider
from .douyin import DouyinAuthProvider

__all__ = [
    "BilibiliAuthProvider",
    "DouyinAuthProvider",
]
