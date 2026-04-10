"""
Bilibili Downloader using httpx + ffmpeg.

This module implements B站 video download based on bili-sync's approach:
- WBI signature for API requests
- Separate video/audio stream download
- CDN preference sorting
- FFmpeg merge for final output
"""

import asyncio
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from loguru import logger


class BilibiliDownloader:
    """
    B站 Video Downloader using httpx + ffmpeg.

    Based on bili-sync implementation:
    - WBI signature for API authentication
    - Separate video/audio download with CDN preference
    - FFmpeg merge for final MP4 output
    """

    # API endpoints
    API_PLAYURL = "https://api.bilibili.com/x/player/wbi/playurl"
    API_VIDEO_INFO = "https://api.bilibili.com/x/web-interface/view"

    # WBI mixin key encoding table (from bili-sync)
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52,
    ]

    # Required headers (from bili-sync)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
    }

    # Quality mappings
    VIDEO_QUALITY_MAP = {
        16: "360P",
        32: "480P",
        64: "720P",
        80: "1080P",
        112: "1080P+",
        116: "1080P60",
        120: "4K",
    }

    AUDIO_QUALITY_MAP = {
        30216: "64k",
        30232: "132k",
        30280: "192k",
        30250: "Dolby",
        30251: "Hi-RES",
    }

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

        # Default cookie file path
        if not self.cookie_file:
            default_cookie_path = Path("config/cookies/bilibili_cookies.txt")
            if default_cookie_path.exists():
                self.cookie_file = default_cookie_path
                logger.info(f"Using default cookie file: {self.cookie_file}")

        # Extract SESSDATA from cookie file
        if not self.sessdata and self.cookie_file and self.cookie_file.exists():
            self.sessdata = self._extract_sessdata_from_cookie_file()

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            headers=self.HEADERS,
            cookies={"SESSDATA": self.sessdata} if self.sessdata else None,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
        )

        # WBI keys (will be fetched on first request)
        self.wbi_img_url: str | None = None
        self.wbi_sub_url: str | None = None
        self.mixin_key: str | None = None

        logger.info(f"BilibiliDownloader initialized with output_dir: {self.output_dir}")

    def _extract_sessdata_from_cookie_file(self) -> str | None:
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
                        logger.info(f"Extracted SESSDATA from cookie file")
                        return parts[6]
        except Exception as e:
            logger.error(f"Failed to extract SESSDATA: {e}")

        return None

    async def _get_wbi_keys(self) -> None:
        """Fetch WBI keys for signature."""
        if self.mixin_key:
            return

        try:
            # Get WBI img keys from navigation API
            resp = await self.client.get(
                "https://api.bilibili.com/x/web-interface/nav"
            )
            data = resp.json()

            if data["code"] != 0:
                logger.warning(f"Failed to get WBI keys: {data.get('message')}")
                return

            wbi_img = data["data"]["wbi_img"]
            self.wbi_img_url = wbi_img["img_url"].split("/")[-1].split(".")[0]
            self.wbi_sub_url = wbi_img["sub_url"].split("/")[-1].split(".")[0]

            # Generate mixin key using encoding table
            combined = self.wbi_img_url + self.wbi_sub_url
            self.mixin_key = "".join(
                combined[i] for i in self.MIXIN_KEY_ENC_TAB[:32]
            )

            logger.debug(f"WBI mixin key generated: {len(self.mixin_key)} chars")

        except Exception as e:
            logger.error(f"Failed to fetch WBI keys: {e}")

    def _sign_wbi(self, params: dict[str, Any]) -> str:
        """Sign parameters with WBI signature."""
        if not self.mixin_key:
            logger.warning("WBI mixin key not available, skipping signature")
            return urlencode(params)

        # Add wts (timestamp)
        import time
        params["wts"] = int(time.time())

        # Sort and encode parameters
        sorted_params = sorted(params.items())
        encoded = "&".join(f"{k}={v}" for k, v in sorted_params)

        # Calculate signature
        signature = hashlib.md5((encoded + self.mixin_key).encode()).hexdigest()
        params["w_rid"] = signature

        return urlencode(params)

    async def _get_video_info(self, bvid: str) -> dict[str, Any]:
        """Get video metadata."""
        resp = await self.client.get(
            self.API_VIDEO_INFO,
            params={"bvid": bvid}
        )
        data = resp.json()

        if data["code"] != 0:
            raise RuntimeError(f"Failed to get video info: {data.get('message')}")

        return data["data"]

    async def _get_playurl(self, bvid: str, cid: int) -> dict[str, Any]:
        """Get playback URL with video/audio streams."""
        await self._get_wbi_keys()

        # Request parameters (from bili-sync)
        params = {
            "bvid": bvid,
            "cid": cid,
            "qn": 127,  # Request highest quality
            "fnval": 4048,  # Support DASH format
            "fourk": 1,  # Enable 4K
        }

        # Sign with WBI
        signed_url = f"{self.API_PLAYURL}?{self._sign_wbi(params)}"

        resp = await self.client.get(signed_url)
        data = resp.json()

        if data["code"] != 0:
            raise RuntimeError(f"Failed to get playurl: {data.get('message')}")

        return data["data"]

    def _select_best_streams(
        self,
        dash_data: dict[str, Any],
        video_quality: int,
        audio_quality: int,
    ) -> tuple[dict, dict]:
        """Select best video and audio streams with CDN preference."""
        # Find matching video stream
        video_streams = dash_data.get("video", [])
        target_video = None

        for stream in video_streams:
            if stream["id"] == video_quality:
                target_video = stream
                break

        # Fallback to highest available quality
        if not target_video and video_streams:
            target_video = max(video_streams, key=lambda s: s["id"])
            logger.info(f"Video quality {video_quality} not available, using {target_video['id']}")

        # Find matching audio stream
        audio_streams = dash_data.get("audio", [])
        target_audio = None

        for stream in audio_streams:
            if stream["id"] == audio_quality:
                target_audio = stream
                break

        # Fallback to highest available quality
        if not target_audio and audio_streams:
            target_audio = max(audio_streams, key=lambda s: s["id"])
            logger.info(f"Audio quality {audio_quality} not available, using {target_audio['id']}")

        if not target_video:
            raise RuntimeError("No video stream available")
        if not target_audio:
            raise RuntimeError("No audio stream available")

        # Select best CDN URL (from bili-sync: upos > cn > mcdn > other)
        def get_best_url(stream: dict) -> str:
            base_url = stream["baseUrl"]
            backup_urls = stream.get("backupUrl", [])

            all_urls = [base_url] + backup_urls

            # Sort by CDN preference
            def cdn_priority(url: str) -> int:
                if "upos-" in url:
                    return 0  # Best: provider CDN
                elif "cn-" in url:
                    return 1  # Good: self-hosted CDN
                elif "mcdn" in url:
                    return 2  # OK: MCDN
                else:
                    return 3  # Last resort: PCDN/other

            all_urls.sort(key=cdn_priority)
            return all_urls[0]

        best_video_url = get_best_url(target_video)
        best_audio_url = get_best_url(target_audio)

        logger.info(
            f"Selected streams: Video {target_video['id']} ({target_video.get('codecid', 'unknown')}), "
            f"Audio {target_audio['id']}"
        )

        return (
            {"url": best_video_url, "size": target_video.get("size", 0)},
            {"url": best_audio_url, "size": target_audio.get("size", 0)},
        )

    async def _download_file(
        self,
        url: str,
        output_path: Path,
        description: str = "file",
    ) -> bool:
        """Download file with progress tracking."""
        try:
            logger.info(f"Downloading {description}...")

            async with self.client.stream("GET", url) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if int(progress) % 10 == 0:  # Log every 10%
                                logger.debug(
                                    f"{description} download: {progress:.1f}% "
                                    f"({downloaded}/{total_size} bytes)"
                                )

            logger.info(f"{description} downloaded: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to download {description}: {e}")
            return False

    def _merge_video_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> bool:
        """Merge video and audio using FFmpeg."""
        try:
            logger.info("Merging video and audio...")

            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c", "copy",  # Stream copy (fast)
                "-strict", "unofficial",
                "-f", "mp4",
                "-y",  # Overwrite
                str(output_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                error = result.stderr.decode("utf-8", errors="ignore")
                logger.error(f"FFmpeg merge failed: {error}")
                return False

            logger.info(f"Merged successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to merge: {e}")
            return False

    async def download_async(
        self,
        url: str,
        video_quality: int = 80,  # 1080P
        audio_quality: int = 30280,  # 192k
        **kwargs: Any,
    ) -> Path | None:
        """
        Download video asynchronously.

        Args:
            url: B站 video URL
            video_quality: Video quality ID (default: 80 for 1080P)
            audio_quality: Audio quality ID (default: 30280 for 192k)
            **kwargs: Additional options

        Returns:
            Downloaded video path or None if failed
        """
        try:
            # Extract BV ID from URL
            match = re.search(r"BV[\w]+", url)
            if not match:
                logger.error(f"Invalid B站 URL: {url}")
                return None

            bvid = match.group(0)
            logger.info(f"Downloading B站 video: {bvid}")

            # Get video info
            video_info = await self._get_video_info(bvid)
            title = video_info["title"]
            cid = video_info["cid"]

            logger.info(f"Video title: {title}")

            # Get playback URLs
            playurl_data = await self._get_playurl(bvid, cid)

            # Check if DASH format available
            if "dash" not in playurl_data:
                logger.error("DASH format not available, video may require premium")
                return None

            dash_data = playurl_data["dash"]

            # Select best streams with CDN preference
            video_stream, audio_stream = self._select_best_streams(
                dash_data, video_quality, audio_quality
            )

            # Prepare output paths
            safe_title = re.sub(r'[<>:"/\\|?*]', "_", title)[:100]
            temp_video = self.output_dir / f"{safe_title}_video.m4s"
            temp_audio = self.output_dir / f"{safe_title}_audio.m4s"
            final_output = self.output_dir / f"{safe_title}.mp4"

            # Download video stream
            if not await self._download_file(
                video_stream["url"], temp_video, "video stream"
            ):
                return None

            # Download audio stream
            if not await self._download_file(
                audio_stream["url"], temp_audio, "audio stream"
            ):
                temp_video.unlink(missing_ok=True)
                return None

            # Merge with FFmpeg
            if not self._merge_video_audio(temp_video, temp_audio, final_output):
                temp_video.unlink(missing_ok=True)
                temp_audio.unlink(missing_ok=True)
                return None

            # Cleanup temp files
            temp_video.unlink(missing_ok=True)
            temp_audio.unlink(missing_ok=True)

            # Verify final output
            if final_output.exists() and final_output.stat().st_size > 0:
                logger.info(f"Download successful: {final_output}")
                return final_output
            else:
                logger.error("Final output file missing or empty")
                return None

        except Exception as e:
            logger.error(f"Download failed: {e}")
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
        Download video synchronously.

        Args:
            url: B站 video URL
            video_quality: Video quality ID (default: 80 for 1080P)
            audio_quality: Audio quality ID (default: 30280 for 192k)
            **kwargs: Additional options

        Returns:
            Downloaded video path or None if failed
        """
        try:
            return asyncio.run(self.download_async(url, video_quality, audio_quality, **kwargs))
        except KeyboardInterrupt:
            logger.info("Download interrupted by user")
            return None
        except Exception as e:
            logger.error(f"Async wrapper error: {e}")
            return None