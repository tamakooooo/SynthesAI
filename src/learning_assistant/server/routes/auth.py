"""
Authentication endpoints for platform login (Bilibili, Douyin, YouTube).
"""

import base64
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from learning_assistant.auth.providers import BilibiliAuthProvider, DouyinAuthProvider
from learning_assistant.auth.models import AuthStatus, QRStatus

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# Response models
class PlatformAuthStatus(BaseModel):
    """Authentication status for a single platform."""

    platform: str = Field(description="Platform name")
    status: str = Field(description="Auth status: authenticated, not_authenticated, expired")
    username: str | None = Field(default=None, description="User name if authenticated")
    expires_at: str | None = Field(default=None, description="Cookie expiration time")
    message: str | None = Field(default=None, description="Status message")


class AllPlatformsStatus(BaseModel):
    """Authentication status for all platforms."""

    platforms: list[PlatformAuthStatus] = Field(description="Status for each platform")


class QRCodeResponse(BaseModel):
    """QR code for login."""

    platform: str = Field(description="Platform name")
    qr_url: str = Field(description="QR code image URL (base64)")
    session_key: str = Field(description="Session key for polling")
    expires_in: int = Field(description="QR code expiration time in seconds")
    message: str = Field(description="Instructions for user")


class QRPollResponse(BaseModel):
    """QR code polling result."""

    platform: str = Field(description="Platform name")
    status: str = Field(description="Polling status: waiting, scanned, confirmed, expired, error")
    message: str = Field(description="Status message")
    authenticated: bool = Field(description="Whether login is complete")


class ImportCookiesRequest(BaseModel):
    """Request to manually import cookies."""

    cookies: str = Field(
        description="Cookie data to import. Supports two formats: "
        "1) JSON array from browser extension (e.g., 'Get cookies.txt') "
        "2) Cookie string (e.g., 'SESSDATA=xxx; DedeUserID=xxx')"
    )


class ImportCookiesResponse(BaseModel):
    """Response after importing cookies."""

    platform: str = Field(description="Platform name")
    success: bool = Field(description="Import success status")
    message: str = Field(description="Status message")
    cookies_count: int | None = Field(default=None, description="Number of cookies imported")


# Supported platforms
SUPPORTED_PLATFORMS = ["bilibili", "douyin", "youtube"]

# Cookie directory
COOKIE_DIR = Path("config/cookies")


def get_cookie_file(platform: str) -> Path:
    """Get cookie file path for platform."""
    return COOKIE_DIR / f"{platform}_cookies.txt"


def get_bilibili_provider() -> BilibiliAuthProvider:
    """Get Bilibili auth provider."""
    return BilibiliAuthProvider(cookie_dir=str(COOKIE_DIR))


def get_douyin_provider() -> DouyinAuthProvider:
    """Get Douyin auth provider."""
    return DouyinAuthProvider(cookie_dir=str(COOKIE_DIR))


@router.get("/status", response_model=AllPlatformsStatus)
async def get_all_auth_status():
    """
    Get authentication status for all supported platforms.

    Returns:
        Status for each platform
    """
    statuses: list[PlatformAuthStatus] = []

    for platform in SUPPORTED_PLATFORMS:
        try:
            cookie_file = get_cookie_file(platform)

            if platform == "bilibili":
                provider = get_bilibili_provider()
                result = provider.check_status()
                if result.status == AuthStatus.AUTHENTICATED:
                    status_str = "authenticated"
                    username = result.username
                    message = f"已登录 ({username or 'unknown'})"
                elif result.status == AuthStatus.EXPIRED:
                    status_str = "expired"
                    username = None
                    message = "登录已过期，请重新登录"
                else:
                    status_str = "not_authenticated"
                    username = None
                    message = "未登录"

            elif platform == "douyin":
                provider = get_douyin_provider()
                result = provider.check_status()
                if result.status == AuthStatus.AUTHENTICATED:
                    status_str = "authenticated"
                    username = None
                    message = "已登录"
                elif result.status == AuthStatus.EXPIRED:
                    status_str = "expired"
                    username = None
                    message = "登录已过期，请重新登录"
                else:
                    status_str = "not_authenticated"
                    username = None
                    message = "未登录"

            elif platform == "youtube":
                if cookie_file.exists():
                    status_str = "not_authenticated"
                    message = "Cookie file exists, status unknown"
                else:
                    status_str = "not_authenticated"
                    message = "Cookie file not found"
                username = None

            statuses.append(PlatformAuthStatus(
                platform=platform,
                status=status_str,
                username=username,
                message=message,
            ))

        except Exception as e:
            statuses.append(PlatformAuthStatus(
                platform=platform,
                status="error",
                message=f"Failed to check status: {str(e)}",
            ))

    return AllPlatformsStatus(platforms=statuses)


@router.get("/status/{platform}", response_model=PlatformAuthStatus)
async def get_platform_auth_status(platform: str):
    """
    Get authentication status for a specific platform.

    Args:
        platform: Platform name (bilibili, douyin, youtube)

    Returns:
        Authentication status
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")

    cookie_file = get_cookie_file(platform)

    try:
        if platform == "bilibili":
            provider = get_bilibili_provider()
            result = provider.check_status()
            status_str = "authenticated" if result.status == AuthStatus.AUTHENTICATED else "not_authenticated"
            username = result.username if result.status == AuthStatus.AUTHENTICATED else None
            message = "已登录" if result.status == AuthStatus.AUTHENTICATED else "未登录"

        elif platform == "douyin":
            provider = get_douyin_provider()
            result = provider.check_status()
            status_str = "authenticated" if result.status == AuthStatus.AUTHENTICATED else "not_authenticated"
            username = None
            message = "已登录" if result.status == AuthStatus.AUTHENTICATED else "未登录"

        else:  # youtube
            if cookie_file.exists():
                status_str = "not_authenticated"
                message = "Cookie file exists"
            else:
                status_str = "not_authenticated"
                message = "Cookie file not found"
            username = None

        return PlatformAuthStatus(
            platform=platform,
            status=status_str,
            username=username,
            message=message,
        )

    except Exception as e:
        return PlatformAuthStatus(
            platform=platform,
            status="error",
            message=f"Failed to check status: {str(e)}",
        )


@router.get("/qr/{platform}", response_model=QRCodeResponse)
async def get_qr_code(platform: str):
    """
    Get QR code for platform login.

    Note: Currently only Bilibili supports QR code login.
    Douyin requires manual cookie import.

    Args:
        platform: Platform name (bilibili)

    Returns:
        QR code image and session key
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")

    if platform == "douyin":
        raise HTTPException(
            status_code=400,
            detail="Douyin does not support QR login. Use /api/v1/auth/import/douyin instead."
        )

    if platform == "youtube":
        raise HTTPException(
            status_code=400,
            detail="YouTube requires manual cookie file. Please place cookies.txt in config/cookies/"
        )

    try:
        provider = get_bilibili_provider()

        # Generate QR code using internal method
        qr_session = provider._generate_qr()

        # Return the login URL directly - frontend will encode it as QR code
        # (Don't return base64 image data as frontend will encode it again)
        qr_url = qr_session.qr_url

        return QRCodeResponse(
            platform=platform,
            qr_url=qr_url,
            session_key=qr_session.session_id,
            expires_in=180,
            message=f"请使用 {platform} 手机 App 扫描二维码登录",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR code: {str(e)}")


@router.get("/poll/{platform}", response_model=QRPollResponse)
async def poll_qr_status(platform: str, session_key: str):
    """
    Poll QR code login status.

    Args:
        platform: Platform name (bilibili)
        session_key: Session key from QR code generation

    Returns:
        Login status
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")

    try:
        provider = get_bilibili_provider()

        # Check QR status (single poll)
        qr_status, auth_result = provider.check_qr_status(session_key)

        status_map = {
            QRStatus.WAITING: "waiting",
            QRStatus.SCANNED: "scanned",
            QRStatus.CONFIRMED: "confirmed",
            QRStatus.EXPIRED: "expired",
            QRStatus.ERROR: "error",
        }

        status_str = status_map.get(qr_status, "waiting")
        authenticated = qr_status == QRStatus.CONFIRMED

        # Build message based on status
        status_messages = {
            "waiting": "等待扫码",
            "scanned": "已扫码，等待确认",
            "confirmed": "登录成功",
            "expired": "二维码已过期",
            "error": "登录失败",
        }
        message = status_messages.get(status_str, "")

        return QRPollResponse(
            platform=platform,
            status=status_str,
            message=message,
            authenticated=authenticated,
        )

    except Exception as e:
        return QRPollResponse(
            platform=platform,
            status="error",
            message=f"Polling failed: {str(e)}",
            authenticated=False,
        )


@router.post("/import/{platform}", response_model=ImportCookiesResponse)
async def import_cookies(platform: str, request: ImportCookiesRequest):
    """
    Manually import cookies for a platform.

    Args:
        platform: Platform name (douyin, bilibili)
        request: Cookie string to import

    Returns:
        Import result
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")

    if platform == "youtube":
        raise HTTPException(
            status_code=400,
            detail="YouTube requires manual cookie file placement. Please save cookies.txt to config/cookies/"
        )

    try:
        if platform == "bilibili":
            provider = get_bilibili_provider()
        elif platform == "douyin":
            provider = get_douyin_provider()
        else:
            raise HTTPException(status_code=400, detail=f"Platform '{platform}' not supported for import")

        # Import cookies
        result = provider.import_cookies(request.cookies)

        if result is None:
            return ImportCookiesResponse(
                platform=platform,
                success=False,
                message="Failed to import cookies",
            )

        # Count cookies
        cookie_file = get_cookie_file(platform)
        cookies_count = 0
        if cookie_file.exists():
            with open(cookie_file, "r") as f:
                cookies_count = len([line for line in f if line.strip() and not line.startswith("#")])

        return ImportCookiesResponse(
            platform=platform,
            success=True,
            message=f"Cookies imported successfully",
            cookies_count=cookies_count,
        )

    except Exception as e:
        return ImportCookiesResponse(
            platform=platform,
            success=False,
            message=f"Import failed: {str(e)}",
        )


@router.delete("/{platform}")
async def logout(platform: str):
    """
    Logout and remove cookies for a platform.

    Args:
        platform: Platform name (bilibili, douyin)

    Returns:
        Logout result
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")

    cookie_file = get_cookie_file(platform)

    try:
        if cookie_file.exists():
            cookie_file.unlink()
            return {"success": True, "message": f"{platform} cookies removed"}
        else:
            return {"success": True, "message": f"No {platform} cookies found"}

    except Exception as e:
        return {"success": False, "message": f"Logout failed: {str(e)}"}


@router.get("/help/{platform}")
async def get_login_help(platform: str):
    """
    Get instructions for logging into a platform.

    Args:
        platform: Platform name

    Returns:
        Login instructions
    """
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")

    help_texts = {
        "bilibili": {
            "method": "QR Code",
            "steps": [
                "点击「扫码登录」按钮",
                "使用哔哩哔哩手机 App 扫描二维码",
                "在手机上确认登录",
                "等待系统自动完成认证",
            ],
            "note": "二维码有效期约 3 分钟，过期需重新获取",
        },
        "douyin": {
            "method": "Manual Cookie Import",
            "steps": [
                "在浏览器打开 https://www.douyin.com 并登录",
                "按 F12 打开开发者工具",
                "切换到 Network 标签",
                "刷新页面，找到任意请求",
                "复制请求头中的 Cookie 字段内容",
                "粘贴到下方输入框并提交",
            ],
            "note": "或者在 Console 执行 document.cookie 复制结果",
            "required_cookies": ["odin_tt", "ttwid", "passport_csrf_token", "s_v_web_id"],
        },
        "youtube": {
            "method": "Browser Extension",
            "steps": [
                "安装浏览器扩展「Get cookies.txt」",
                "登录 YouTube",
                "使用扩展导出 cookies.txt",
                "将文件放置到 config/cookies/youtube_cookies.txt",
            ],
            "note": "YouTube 需要手动放置 Netscape 格式的 cookie 文件",
        },
    }

    return help_texts.get(platform, {"error": "No help available"})