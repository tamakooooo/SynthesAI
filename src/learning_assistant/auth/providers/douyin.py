"""
Douyin authentication provider.

Implements manual cookie import for Douyin (抖音).
"""

from pathlib import Path

from loguru import logger

from ..base import BaseAuthProvider
from ..cookie_manager import CookieManager
from ..models import AuthInfo, AuthResult, AuthStatus, CookieData


class DouyinAuthProvider(BaseAuthProvider):
    """
    Douyin authentication provider using manual cookie import.

    Since Douyin requires OAuth app registration for automated login,
    we provide a guided manual cookie import process.
    """

    # Douyin domain for cookies
    DOUYIN_DOMAIN = ".douyin.com"

    # Essential cookie names for Douyin
    ESSENTIAL_COOKIES = ["odin_tt", "ttwid", "passport_csrf_token", "s_v_web_id"]

    # Cookie file name
    COOKIE_FILENAME = "douyin_cookies.txt"

    def __init__(self, cookie_dir: str, **kwargs):
        """
        Initialize Douyin authentication provider.

        Args:
            cookie_dir: Directory to store cookie files
        """
        super().__init__(cookie_dir)
        self.cookie_manager = CookieManager(cookie_dir)

        logger.info("DouyinAuthProvider initialized")

    def login(self, timeout: int | None = None) -> AuthResult:
        """
        Guide user through manual cookie import.

        Args:
            timeout: Not used for manual import

        Returns:
            Authentication result
        """
        print("\n" + "=" * 70)
        print("抖音 Cookie 导入指南")
        print("=" * 70)
        print("\n抖音需要手动导入 Cookie。请按以下步骤操作：\n")

        print("步骤 1: 打开抖音网页版")
        print("  访问: https://www.douyin.com\n")

        print("步骤 2: 登录抖音账号")
        print("  使用手机扫码或手机号登录\n")

        print("步骤 3: 提取 Cookie")
        print("  方法 1 (推荐):")
        print("    1. 按 F12 打开开发者工具")
        print("    2. 切换到 'Network（网络）' 标签")
        print("    3. 勾选 'Preserve log（保留日志）'")
        print("    4. 刷新页面")
        print("    5. 点击任意请求")
        print("    6. 在 'Headers（标头）' 中找到 'cookie:' 行")
        print("    7. 复制完整的 cookie 字符串\n")

        print("  方法 2 (快捷):")
        print("    1. 按 F12 打开开发者工具")
        print("    2. 切换到 'Console（控制台）' 标签")
        print("    3. 输入: document.cookie")
        print("    4. 复制输出的字符串\n")

        print("步骤 4: 导入 Cookie")
        print("  运行命令:")
        print('  la auth import --platform douyin --cookies "<你复制的cookie字符串>"\n')

        print("=" * 70)
        print("\n提示：Cookie 包含敏感信息，请勿分享给他人！")
        print("=" * 70 + "\n")

        return AuthResult(
            success=False,
            platform="douyin",
            error_message="Manual import required. Follow the instructions above.",
        )

    def check_status(self) -> AuthInfo:
        """
        Check Douyin authentication status.

        Returns:
            Authentication info
        """
        cookie_file = self.get_cookie_file_path()

        if not cookie_file.exists():
            return AuthInfo(
                platform="douyin",
                status=AuthStatus.NOT_AUTHENTICATED,
            )

        try:
            # Import cookies
            cookies = self.cookie_manager.import_cookies(self.COOKIE_FILENAME)

            # Check for essential cookies
            cookie_names = [c.name for c in cookies]

            has_essential = all(
                any(name in cookie_name for cookie_name in cookie_names)
                for name in self.ESSENTIAL_COOKIES
            )

            if not has_essential:
                return AuthInfo(
                    platform="douyin",
                    status=AuthStatus.INVALID,
                    cookie_file=str(cookie_file),
                )

            return AuthInfo(
                platform="douyin",
                status=AuthStatus.AUTHENTICATED,
                cookie_file=str(cookie_file),
            )

        except Exception as e:
            logger.error(f"Failed to check Douyin auth status: {e}")
            return AuthInfo(
                platform="douyin",
                status=AuthStatus.INVALID,
            )

    def logout(self) -> bool:
        """
        Clear Douyin authentication (delete cookies).

        Returns:
            True if logout successful
        """
        try:
            deleted = self.cookie_manager.delete_cookie_file(self.COOKIE_FILENAME)
            if deleted:
                logger.info("Douyin authentication cleared")
            return deleted
        except Exception as e:
            logger.error(f"Failed to logout from Douyin: {e}")
            return False

    def get_cookie_file_path(self) -> Path:
        """Get Douyin cookie file path."""
        return self.cookie_manager.get_cookie_file_path(self.COOKIE_FILENAME)

    def import_cookies(self, cookie_string: str) -> AuthResult:
        """
        Import cookies from browser cookie string.

        Args:
            cookie_string: Cookie string from browser (format: "name1=value1; name2=value2")

        Returns:
            Authentication result
        """
        try:
            # Parse cookie string
            cookies_data = self.cookie_manager.validate_cookie_string(cookie_string)

            # Add Douyin domain to each cookie
            cookies = []
            for cookie_data in cookies_data:
                cookie = CookieData(
                    name=cookie_data.name,
                    value=cookie_data.value,
                    domain=self.DOUYIN_DOMAIN,
                    path="/",
                    secure=False,
                    expires=None,
                )
                cookies.append(cookie)

            # Save to file
            cookie_file = self.cookie_manager.export_cookies(
                cookies, self.COOKIE_FILENAME
            )

            logger.info(f"Douyin cookies imported: {len(cookies)} cookies")

            return AuthResult(
                success=True,
                platform="douyin",
                cookies=cookies,
                cookie_file=str(cookie_file),
            )

        except Exception as e:
            logger.error(f"Failed to import Douyin cookies: {e}")
            return AuthResult(
                success=False,
                platform="douyin",
                error_message=str(e),
            )
