"""
Bilibili Downloader using yutto.

This module provides B站-specific download capabilities using yutto library
to avoid SSL/CDN issues with yt-dlp.
"""

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger

# Import yutto components
try:
    from biliass import BlockOptions
    from yutto.extractor import UgcVideoExtractor
    from yutto.types import EpisodeData, ExtractorOptions
    from yutto.utils.danmaku import DanmakuOptions
    from yutto.utils.fetcher import Fetcher, FetcherContext, create_client
    from yutto.validator import validate_user_info

    YUTTO_AVAILABLE = True
except ImportError:
    YUTTO_AVAILABLE = False
    logger.warning("yutto is not installed. B站 downloads will use yt-dlp fallback.")


class BilibiliDownloader:
    """
    B站 Video Downloader using yutto library.

    Uses yutto's download manager directly to avoid CLI encoding issues
    and SSL problems encountered with yt-dlp.
    """

    def __init__(
        self,
        output_dir: Path,
        sessdata: str | None = None,
        cookie_file: Path | None = None,
    ) -> None:
        """
        Initialize BilibiliDownloader.

        Args:
            output_dir: Output directory for downloaded videos
            sessdata: B站 SESSDATA cookie value (optional)
            cookie_file: Path to Netscape format cookie file (optional)
        """
        self.output_dir = output_dir
        self.sessdata = sessdata
        self.cookie_file = cookie_file

        # Extract SESSDATA from cookie file if not provided
        if not self.sessdata and self.cookie_file and self.cookie_file.exists():
            self.sessdata = self._extract_sessdata_from_cookie_file()

        logger.info(
            f"BilibiliDownloader initialized with output_dir: {self.output_dir}"
        )

    def _extract_sessdata_from_cookie_file(self) -> str | None:
        """
        Extract SESSDATA from Netscape format cookie file.

        Returns:
            SESSDATA value or None if not found
        """
        if not self.cookie_file or not self.cookie_file.exists():
            return None

        try:
            with open(self.cookie_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue

                    parts = line.strip().split("\t")
                    if len(parts) >= 7:
                        domain, path, secure, expiry, name, value = (
                            parts[0],
                            parts[2],
                            parts[3],
                            parts[4],
                            parts[5],
                            parts[6],
                        )

                        if name == "SESSDATA":
                            logger.info(
                                f"Extracted SESSDATA from cookie file: {self.cookie_file}"
                            )
                            return value

        except Exception as e:
            logger.error(f"Failed to extract SESSDATA from cookie file: {e}")

        return None

    async def download_async(
        self,
        url: str,
        video_quality: int = 80,  # 1080P
        audio_quality: int = 30280,  # 320kbps
        **kwargs: Any,
    ) -> Path | None:
        """
        Download video asynchronously using yutto.

        Args:
            url: B站 video URL
            video_quality: Video quality ID (default: 80 for 1080P)
            audio_quality: Audio quality ID (default: 30280 for 320kbps)
            **kwargs: Additional yutto options

        Returns:
            Downloaded video path or None if download failed
        """
        if not YUTTO_AVAILABLE:
            logger.error("yutto is not installed. Cannot download B站 video.")
            return None

        logger.info(f"Downloading B站 video with yutto: {url}")

        # Create FetcherContext
        ctx = FetcherContext()
        ctx.set_fetch_semaphore(fetch_workers=8)

        # Set cookies if SESSDATA is available
        if self.sessdata:
            logger.info("Using authenticated session with SESSDATA")
            # Note: yutto's FetcherContext handles cookies internally
            # We'll pass sessdata via command-line args equivalent

        # Create HTTP client
        try:
            async with create_client(
                cookies=ctx.cookies,
                trust_env=ctx.trust_env,
                proxy=ctx.proxy,
            ) as client:
                # Validate user info
                if not await validate_user_info(
                    ctx, {"is_login": bool(self.sessdata), "vip_status": False}
                ):
                    logger.warning("User validation failed. Download may be limited.")

                # Initialize extractor
                extractor = UgcVideoExtractor()

                # Match URL
                if not extractor.match(url):
                    logger.error(f"URL does not match B站 format: {url}")
                    return None

                # Extract episode data
                logger.info("Extracting video information...")
                download_list = await extractor(
                    ctx,
                    client,
                    ExtractorOptions(
                        episodes=None,
                        with_section=False,
                        require_video=True,
                        require_audio=True,
                        require_danmaku=True,
                        require_subtitle=True,
                        require_metadata=True,
                        require_cover=True,
                        require_chapter_info=False,
                        danmaku_format="ass",
                        subpath_template="{name}",
                        ai_translation_language=None,
                    ),
                )

                if not download_list:
                    logger.error("Failed to extract video data")
                    return None

                # Process first episode
                episode_data_coro = download_list[0]
                if episode_data_coro is None:
                    logger.error("No episode data available")
                    return None

                episode_data = await episode_data_coro
                if episode_data is None:
                    logger.error("Failed to resolve episode data")
                    return None

                # Log download info
                display_name = (
                    episode_data.get("title")
                    or episode_data.get("name")
                    or "bilibili_video"
                )
                logger.info(f"Downloading: {display_name}")

                # The path is already set by yutto's extractor
                # We just need to make sure the parent directory exists
                output_path = episode_data["path"]
                output_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Output path: {output_path}")

                # Import download processor
                from yutto.downloader.downloader import process_download

                # Download
                download_state = await process_download(
                    ctx,
                    client,
                    episode_data,
                    {
                        "output_dir": str(
                            self.output_dir.parent
                            if self.output_dir.name == "data"
                            else self.output_dir
                        ),
                        "tmp_dir": str(
                            self.output_dir.parent
                            if self.output_dir.name == "data"
                            else self.output_dir
                        ),
                        "require_video": True,
                        "require_chapter_info": False,
                        "video_quality": video_quality,
                        "video_download_codec": "avc",
                        "video_save_codec": "avc",
                        "video_download_codec_priority": "auto",
                        "require_audio": True,
                        "audio_quality": audio_quality,
                        "audio_download_codec": "mp4a",
                        "audio_save_codec": "mp4a",
                        "output_format": "infer",
                        "output_format_audio_only": "infer",
                        "overwrite": False,
                        "block_size": int(0.5 * 1024 * 1024),  # 0.5 MiB
                        "num_workers": 8,
                        "save_cover": False,
                        "metadata_format": {
                            "premiered": "%Y-%m-%d",
                            "dateadded": "%Y-%m-%d %H:%M:%S",
                        },
                        "banned_mirrors_pattern": None,
                        "danmaku_options": DanmakuOptions(
                            font_size=25,
                            font="Microsoft YaHei",
                            opacity=0.9,
                            display_region_ratio=1.0,
                            speed=10.0,
                            block_options=BlockOptions(
                                block_top=False,
                                block_bottom=False,
                                block_scroll=False,
                                block_reverse=False,
                                block_special=False,
                                block_colorful=False,
                                block_keyword_patterns=[],
                            ),
                        ),
                    },
                )

                if download_state:
                    # Check for downloaded file (could be .mp4, .m4a, .mkv, etc.)
                    downloaded_path = episode_data["path"]

                    # If the path is relative, prepend output_dir
                    if not downloaded_path.is_absolute():
                        downloaded_path = self.output_dir / downloaded_path.name

                    if not downloaded_path.exists():
                        # Try common video/audio extensions
                        for ext in [".mp4", ".m4a", ".mkv", ".webm"]:
                            test_path = downloaded_path.with_suffix(ext)
                            if test_path.exists():
                                downloaded_path = test_path
                                break

                    if downloaded_path.exists():
                        logger.info(f"Download successful: {downloaded_path}")
                        return downloaded_path
                    else:
                        logger.error(
                            f"Download state shows success but file not found: {downloaded_path}"
                        )
                        logger.error(f"Searched in: {downloaded_path.parent}")
                        logger.error(
                            f"Files in directory: {list(downloaded_path.parent.glob('*')) if downloaded_path.parent.exists() else 'directory not found'}"
                        )
                        return None
                else:
                    logger.error("Download failed")
                    return None

        except Exception as e:
            logger.error(f"Download error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def download(
        self,
        url: str,
        video_quality: int = 80,
        audio_quality: int = 30280,
        **kwargs: Any,
    ) -> Path | None:
        """
        Download video synchronously (wrapper for async method).

        Args:
            url: B站 video URL
            video_quality: Video quality ID (default: 80 for 1080P)
            audio_quality: Audio quality ID (default: 30280 for 320kbps)
            **kwargs: Additional yutto options

        Returns:
            Downloaded video path or None if download failed
        """
        try:
            # Run async download
            return asyncio.run(
                self.download_async(url, video_quality, audio_quality, **kwargs)
            )
        except KeyboardInterrupt:
            logger.info("Download interrupted by user")
            return None
        except Exception as e:
            logger.error(f"Async wrapper error: {e}")
            return None
