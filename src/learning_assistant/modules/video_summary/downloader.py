"""
Video Downloader for Learning Assistant.

This module provides video download capabilities using yt-dlp.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp
from loguru import logger

# Import B站-specific downloader
try:
    from .bilibili_downloader import BilibiliDownloader

    BILIBILI_DOWNLOADER_AVAILABLE = True
except ImportError:
    BILIBILI_DOWNLOADER_AVAILABLE = False
    logger.warning("BilibiliDownloader not available, B站 downloads will use yt-dlp fallback")

# Import yutto CLI (B站专用下载器，更稳定)
try:
    import subprocess

    # Check if yutto CLI is available
    _yutto_check = subprocess.run(["yutto", "--version"], capture_output=True, timeout=5)
    YUTTO_AVAILABLE = _yutto_check.returncode == 0
    if YUTTO_AVAILABLE:
        logger.info("yutto CLI available, will use for B站 downloads")
except (ImportError, FileNotFoundError, subprocess.TimeoutExpired):
    YUTTO_AVAILABLE = False
    logger.warning("yutto not available, using yt-dlp fallback")


@dataclass
class VideoInfo:
    """
    Video information structure.
    """

    title: str
    duration: int  # seconds
    uploader: str
    upload_date: str
    description: str
    thumbnail: str
    url: str
    platform: str


@dataclass
class DownloadProgress:
    """
    Download progress information.
    """

    status: str
    downloaded_bytes: int
    total_bytes: int
    speed: float  # bytes per second
    eta: float  # seconds
    percentage: float


class VideoDownloader:
    """
    Video Downloader using yt-dlp.

    Supports:
    - Multiple platforms (Bilibili, YouTube, Douyin, etc.)
    - Progress callback
    - Cookie configuration
    - Video information extraction
    """

    # Platform detection patterns
    PLATFORM_PATTERNS = {
        "bilibili": [
            r"(bilibili\.com|b23\.tv)",
            r"(BV|av)\w+",
        ],
        "youtube": [
            r"(youtube\.com|youtu\.be)",
            r"v=[\w-]+",
        ],
        "douyin": [
            r"(douyin\.com|v\.douyin\.com)",
        ],
    }

    def __init__(
        self,
        output_dir: Path | None = None,
        cookie_file: Path | None = None,
        progress_callback: Callable[[DownloadProgress], None] | None = None,
        sessdata: str | None = None,
    ) -> None:
        """
        Initialize VideoDownloader.

        Args:
            output_dir: Output directory for downloaded videos
            cookie_file: Cookie file path for authentication
            progress_callback: Progress callback function
            sessdata: B站 SESSDATA cookie value (optional, for yutto)
        """
        self.output_dir = output_dir or Path("data/downloads")
        self.cookie_file = cookie_file
        self.progress_callback = progress_callback
        self.sessdata = sessdata

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize B站-specific downloader if available
        if BILIBILI_DOWNLOADER_AVAILABLE:
            self.bilibili_downloader = BilibiliDownloader(
                output_dir=self.output_dir,
                sessdata=sessdata,
                cookie_file=cookie_file,
            )
        else:
            self.bilibili_downloader = None

        logger.info(f"VideoDownloader initialized with output_dir: {self.output_dir}")

    def detect_platform(self, url: str) -> str:
        """
        Detect video platform from URL.

        Args:
            url: Video URL

        Returns:
            Platform name (bilibili, youtube, douyin, unknown)
        """
        url_lower = url.lower()

        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    logger.debug(f"Detected platform: {platform} for URL: {url}")
                    return platform

        return "unknown"

    def extract_info(self, url: str) -> VideoInfo | None:
        """
        Extract video information without downloading.

        Args:
            url: Video URL

        Returns:
            VideoInfo or None if extraction failed
        """
        logger.info(f"Extracting video info: {url}")

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        # Add cookie file if configured
        if self.cookie_file and self.cookie_file.exists():
            ydl_opts["cookiefile"] = str(self.cookie_file)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    logger.warning(f"Failed to extract info: {url}")
                    return None

                # Extract relevant information
                video_info = VideoInfo(
                    title=info.get("title", "Unknown"),
                    duration=info.get("duration", 0),
                    uploader=info.get("uploader", "Unknown"),
                    upload_date=info.get("upload_date", ""),
                    description=info.get("description", ""),
                    thumbnail=info.get("thumbnail", ""),
                    url=url,
                    platform=self.detect_platform(url),
                )

                logger.info(
                    f"Extracted video info: title={video_info.title}, "
                    f"duration={video_info.duration}s, platform={video_info.platform}"
                )

                return video_info

        except Exception as e:
            logger.error(f"Failed to extract video info: {e}")
            return None

    def download(
        self,
        url: str,
        output_filename: str | None = None,
        format: str = "bestvideo+bestaudio/best",
        **kwargs: Any,
    ) -> Path | None:
        """
        Download video from URL.

        Args:
            url: Video URL
            output_filename: Output filename (without extension)
            format: Video format selection
            **kwargs: Additional yt-dlp options

        Returns:
            Downloaded video path or None if download failed
        """
        logger.info(f"Downloading video: {url}")

        # Detect platform
        platform = self.detect_platform(url)
        logger.info(f"Platform: {platform}")

        # Priority: yutto CLI > BilibiliDownloader > yt-dlp
        if platform == "bilibili" and YUTTO_AVAILABLE:
            logger.info("Using yutto CLI for B站 video (most stable)")
            result = self._download_with_yutto(url, output_filename)
            if result:
                return result
            logger.warning("yutto failed, falling back to yt-dlp")

        # Use BilibiliDownloader for B站 downloads if yutto failed
        if platform == "bilibili" and self.bilibili_downloader:
            logger.info("Using BilibiliDownloader for B站 video (WBI signature + CDN preference)")
            return self.bilibili_downloader.download(url, **kwargs)

        # Fallback to yt-dlp for other platforms or if yutto is not available
        logger.info("Using yt-dlp for download")

        # Prepare output path
        if output_filename:
            output_path = self.output_dir / f"{output_filename}.%(ext)s"
        else:
            # Use video title as filename
            output_path = self.output_dir / "%(title)s.%(ext)s"

        # Configure yt-dlp options
        ydl_opts: dict[str, Any] = {
            "format": format,
            "outtmpl": str(output_path),
            "quiet": False,
            "no_warnings": False,
            "progress_hooks": [self._progress_hook],
            **kwargs,
        }

        # Add cookie file if configured
        if self.cookie_file and self.cookie_file.exists():
            ydl_opts["cookiefile"] = str(self.cookie_file)

        # Platform-specific options
        if platform == "bilibili":
            # Bilibili-specific options
            ydl_opts.setdefault("http_headers", {})
            ydl_opts["http_headers"]["Referer"] = "https://www.bilibili.com"

            # SSL workarounds for Bilibili CDN issues
            ydl_opts["no_check_certificate"] = True
            ydl_opts["legacyserverconnect"] = True

            # Increased timeout for slow CDN connections
            ydl_opts["socket_timeout"] = 60

            # Use single-file format (包含音频的完整文件) instead of separated streams
            # This avoids CDN timeout issues when downloading audio separately
            if "format" not in kwargs:
                # Try single file first, fallback to video+audio merge
                ydl_opts["format"] = (
                    "best[ext=mp4][vcodec!=none][acodec!=none]/"  # Single file with both
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"  # Merge video+audio
                    "best[ext=mp4]/best"  # Ultimate fallback
                )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info and download
                info = ydl.extract_info(url, download=True)

                if not info:
                    logger.error(f"Failed to download: {url}")
                    return None

                # Get downloaded file path
                downloaded_file = ydl.prepare_filename(info)

                # Check if file exists
                if not Path(downloaded_file).exists():
                    # Try with different extensions
                    for ext in ["mp4", "mkv", "webm", "flv"]:
                        potential_file = downloaded_file.replace(
                            downloaded_file.split(".")[-1], ext
                        )
                        if Path(potential_file).exists():
                            downloaded_file = potential_file
                            break

                logger.info(f"Video downloaded successfully: {downloaded_file}")
                return Path(downloaded_file)

        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return None

    def download_audio_only(
        self, url: str, output_filename: str | None = None
    ) -> Path | None:
        """
        Download audio only from video.

        Args:
            url: Video URL
            output_filename: Output filename (without extension)

        Returns:
            Downloaded audio path or None if download failed
        """
        logger.info(f"Downloading audio only: {url}")

        return self.download(
            url,
            output_filename=output_filename,
            format="bestaudio/best",
            postprocessors=[
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        )

    def _progress_hook(self, d: dict[str, Any]) -> None:
        """
        Progress hook for yt-dlp.

        Args:
            d: Progress dictionary from yt-dlp
        """
        if not self.progress_callback:
            return

        status = d.get("status", "unknown")

        if status == "downloading":
            downloaded_bytes = d.get("downloaded_bytes", 0)
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            speed = d.get("speed", 0.0)
            eta = d.get("eta", 0.0)

            # Calculate percentage
            if total_bytes > 0:
                percentage = (downloaded_bytes / total_bytes) * 100
            else:
                percentage = 0.0

            progress = DownloadProgress(
                status=status,
                downloaded_bytes=downloaded_bytes,
                total_bytes=total_bytes,
                speed=speed,
                eta=eta,
                percentage=percentage,
            )

            self.progress_callback(progress)

        elif status == "finished":
            # Download finished
            progress = DownloadProgress(
                status=status,
                downloaded_bytes=d.get("downloaded_bytes", 0),
                total_bytes=d.get("total_bytes", 0),
                speed=0.0,
                eta=0.0,
                percentage=100.0,
            )

            self.progress_callback(progress)

    def _download_with_yutto(
        self, url: str, output_filename: str | None = None
    ) -> Path | None:
        """
        Download B站 video using yutto CLI (most stable option).

        yutto is a dedicated B站 downloader that handles:
        - WBI signature automatically
        - CDN preference and fallback
        - Better error recovery

        Args:
            url: B站 video URL
            output_filename: Output filename (without extension)

        Returns:
            Downloaded video path or None if failed
        """
        import re
        import subprocess
        import tempfile
        import asyncio

        logger.info(f"Downloading with yutto: {url}")

        # Create temporary output directory
        temp_dir = tempfile.mkdtemp(prefix="yutto_")

        try:
            # Build yutto command
            cmd = [
                "yutto", "download",
                url,
                "-d", temp_dir,
                "-q", "64",  # 720p (good balance of quality and speed)
                "-aq", "30216",  # 64kbps audio (smaller file, more stable)
                "--no-danmaku",  # Skip danmaku for faster download
                "--no-subtitle",  # Skip subtitle for faster download
                "-w",  # Overwrite if exists
            ]

            # Add authentication if cookie file exists
            if self.cookie_file and self.cookie_file.exists():
                sessdata = self._extract_sessdata_from_cookie()
                if sessdata:
                    logger.debug(f"Using SESSDATA for authentication")
                    # Extract bili_jct as well
                    bili_jct = self._extract_bili_jct_from_cookie()
                    if bili_jct:
                        auth_str = f"SESSDATA={sessdata}; bili_jct={bili_jct}"
                        cmd.extend(["--auth", auth_str])
                    else:
                        cmd.extend(["-c", sessdata])

            logger.debug(f"yutto command: {' '.join(cmd[:5])}...")

            # Run yutto download using subprocess.run
            # subprocess.run is always safe even in async context because this method
            # is called from a thread pool (via execute's run_in_executor)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
            )

            if result.returncode != 0:
                logger.error(f"yutto failed: {result.stderr[:500]}")
                return None

            logger.info(f"yutto download completed")

            # Find downloaded file in temp directory
            downloaded_files = list(Path(temp_dir).glob("*.mp4"))

            if not downloaded_files:
                logger.error("No MP4 file found after yutto download")
                return None

            # Get the downloaded file
            downloaded_file = downloaded_files[0]
            logger.info(f"Found downloaded file: {downloaded_file.name}")

            # Move to output directory with proper name
            if output_filename:
                target_path = self.output_dir / f"{output_filename}.mp4"
            else:
                # Use original filename from yutto
                target_path = self.output_dir / downloaded_file.name

            # Move file to output directory
            import shutil
            shutil.move(str(downloaded_file), str(target_path))

            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            # Verify file exists and has content
            if target_path.exists() and target_path.stat().st_size > 0:
                logger.info(f"Video downloaded successfully: {target_path}")
                return target_path
            else:
                logger.error("Final output file missing or empty")
                return None

        except subprocess.TimeoutExpired:
            logger.error("yutto download timeout (10 minutes)")
            return None
        except Exception as e:
            logger.error(f"yutto download error: {e}")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None

    def _extract_sessdata_from_cookie(self) -> str | None:
        """Extract SESSDATA from Netscape format cookie file."""
        if not self.cookie_file or not self.cookie_file.exists():
            return None

        try:
            with open(self.cookie_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 7 and parts[5] == "SESSDATA":
                        return parts[6]
        except Exception as e:
            logger.error(f"Failed to extract SESSDATA: {e}")

        return None

    def _extract_bili_jct_from_cookie(self) -> str | None:
        """Extract bili_jct from Netscape format cookie file."""
        if not self.cookie_file or not self.cookie_file.exists():
            return None

        try:
            with open(self.cookie_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 7 and parts[5] == "bili_jct":
                        return parts[6]
        except Exception as e:
            logger.error(f"Failed to extract bili_jct: {e}")

        return None

    def get_available_formats(self, url: str) -> list[dict[str, Any]]:
        """
        Get available formats for a video.

        Args:
            url: Video URL

        Returns:
            List of available formats
        """
        logger.info(f"Getting available formats: {url}")

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
        }

        if self.cookie_file and self.cookie_file.exists():
            ydl_opts["cookiefile"] = str(self.cookie_file)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    return []

                formats = info.get("formats", [])

                # Extract format information
                format_list = []
                for fmt in formats:
                    format_list.append(
                        {
                            "format_id": fmt.get("format_id", "unknown"),
                            "ext": fmt.get("ext", "unknown"),
                            "resolution": fmt.get("resolution", "unknown"),
                            "fps": fmt.get("fps"),
                            "vcodec": fmt.get("vcodec", "none"),
                            "acodec": fmt.get("acodec", "none"),
                            "filesize": fmt.get("filesize"),
                        }
                    )

                logger.info(f"Found {len(format_list)} available formats")
                return format_list

        except Exception as e:
            logger.error(f"Failed to get formats: {e}")
            return []
