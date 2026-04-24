"""
Bilibili Video Downloader using WBI Signature.

This module implements B站 video download based on latest API:
- WBI signature for API requests (updated algorithm)
- DASH stream selection with quality preferences
- CDN preference sorting
- FFmpeg merge for final output

Reference:
- https://github.com/SocialSisterYi/bilibili-API-collect
- https://github.com/amtoaer/bili-sync
"""

import asyncio
import hashlib
import re
import subprocess
import time
from functools import reduce
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from loguru import logger


class BilibiliDownloader:
    """
    B站 Video Downloader using WBI signature.

    Based on bilibili-API-collect implementation:
    - WBI signature for API authentication
    - DASH stream download with CDN preference
    - FFmpeg merge for final MP4 output
    """

    # API endpoints
    API_NAV = "https://api.bilibili.com/x/web-interface/nav"
    API_VIDEO_INFO = "https://api.bilibili.com/x/web-interface/view"
    API_PLAYURL = "https://api.bilibili.com/x/player/wbi/playurl"

    # WBI mixin key encoding table (fixed, from bilibili-API-collect)
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52,
    ]

    # Required headers (critical for CDN access)
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

    # Cookie file name
    COOKIE_FILENAME = "bilibili_cookies.txt"

    def __init__(
        self,
        output_dir: Path,
        sessdata: str | None = None,
        cookie_file: Path | None = None,
    ) -> None:
        """
        Initialize Bilibili downloader.

        Args:
            output_dir: Directory to store downloaded videos
            sessdata: B站 SESSDATA cookie value (optional, for premium)
            cookie_file: Path to Netscape format cookie file (optional)
        """
        self.output_dir = output_dir
        self.sessdata = sessdata
        self.cookie_file = cookie_file

        # Load sessdata from cookie file if not provided
        if not self.sessdata and self.cookie_file and self.cookie_file.exists():
            self.sessdata = self._extract_sessdata_from_cookie_file()

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            headers=self.HEADERS,
            cookies={"SESSDATA": self.sessdata} if self.sessdata else None,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
        )

        # WBI keys (cached)
        self.img_key: str | None = None
        self.sub_key: str | None = None
        self.mixin_key: str | None = None
        self.wbi_keys_updated_at: float = 0

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
                        return parts[6]
        except Exception as e:
            logger.error(f"Failed to extract SESSDATA: {e}")

        return None

    async def _get_wbi_keys(self) -> None:
        """
        Fetch WBI keys from nav API and generate mixin key.

        WBI keys are refreshed daily, so we cache them and update if stale.
        """
        # Check if keys are fresh (update every 30 minutes)
        if self.mixin_key and time.time() - self.wbi_keys_updated_at < 1800:
            return

        try:
            resp = await self.client.get(self.API_NAV)
            data = resp.json()

            if data.get("code") != 0:
                logger.warning(f"Failed to get WBI keys: {data.get('message')}")
                return

            wbi_img = data["data"]["wbi_img"]
            img_url = wbi_img["img_url"]
            sub_url = wbi_img["sub_url"]

            # Extract keys from URL filenames
            self.img_key = img_url.rsplit("/", 1)[1].split(".")[0]
            self.sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]

            # Generate mixin key using encoding table
            combined = self.img_key + self.sub_key
            self.mixin_key = reduce(
                lambda s, i: s + combined[i], self.MIXIN_KEY_ENC_TAB, ""
            )[:32]

            self.wbi_keys_updated_at = time.time()
            logger.debug(f"WBI mixin key generated: {len(self.mixin_key)} chars")

        except Exception as e:
            logger.error(f"Failed to fetch WBI keys: {e}")

    def _sign_wbi(self, params: dict[str, Any]) -> str:
        """
        Sign parameters with WBI signature.

        Algorithm:
        1. Add wts (timestamp)
        2. Sort parameters by key
        3. Filter special characters from values
        4. URL encode parameters
        5. Append mixin key and calculate MD5

        Args:
            params: Request parameters

        Returns:
            URL-encoded signed parameters
        """
        if not self.mixin_key:
            logger.warning("WBI mixin key not available")
            return urlencode(params)

        # Add timestamp
        params["wts"] = int(time.time())

        # Sort parameters by key
        sorted_params = dict(sorted(params.items()))

        # Filter special characters "!'()*" from values
        filtered_params = {
            k: "".join(filter(lambda c: c not in "!'()*", str(v)))
            for k, v in sorted_params.items()
        }

        # URL encode (standard format, spaces as %20)
        query = urlencode(filtered_params, safe="")

        # Calculate signature
        w_rid = hashlib.md5((query + self.mixin_key).encode()).hexdigest()

        # Add signature to params
        filtered_params["w_rid"] = w_rid

        return urlencode(filtered_params)

    async def _get_video_info(self, bvid: str) -> dict[str, Any]:
        """
        Get video metadata (title, cid, etc.).

        Args:
            bvid: Video BV ID (e.g., BV1GJ411x7h7)

        Returns:
            Video info dict
        """
        resp = await self.client.get(
            self.API_VIDEO_INFO,
            params={"bvid": bvid},
        )
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Failed to get video info: {data.get('message')}")

        return data["data"]

    async def _get_playurl(self, bvid: str, cid: int) -> dict[str, Any]:
        """
        Get playback URL with DASH streams.

        Args:
            bvid: Video BV ID
            cid: Content ID (from video info)

        Returns:
            PlayURL data with video/audio streams
        """
        await self._get_wbi_keys()

        # Request parameters for DASH format
        # fnval=4048: DASH(16) + 4K(128) + HDR(64) + Dolby(256) + AV1(2048)
        params = {
            "bvid": bvid,
            "cid": cid,
            "qn": 127,  # Request highest quality
            "fnval": 4048,  # DASH + all quality features
            "fourk": 1,  # Enable 4K
        }

        # Sign with WBI
        signed_url = f"{self.API_PLAYURL}?{self._sign_wbi(params)}"

        resp = await self.client.get(signed_url)
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Failed to get playurl: {data.get('message')}")

        return data["data"]

    def _select_best_streams(
        self,
        dash_data: dict[str, Any],
        video_quality: int = 80,
        audio_quality: int = 30280,
    ) -> tuple[dict, dict]:
        """
        Select best video and audio streams with CDN preference.

        CDN priority (from bili-sync):
        1. upos-* (provider CDN) - best
        2. cn-* (self-hosted CDN) - good
        3. mcdn (MCDN) - ok
        4. others (PCDN) - last resort

        Args:
            dash_data: DASH stream data from playurl
            video_quality: Target video quality (default 80=1080P)
            audio_quality: Target audio quality (default 30280=192k)

        Returns:
            Tuple of (video_stream_info, audio_stream_info)
        """
        # Find matching video stream
        video_streams = dash_data.get("video", [])
        target_video = None

        # Try exact quality match first
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

        if not target_audio and audio_streams:
            target_audio = max(audio_streams, key=lambda s: s["id"])
            logger.info(f"Audio quality {audio_quality} not available, using {target_audio['id']}")

        if not target_video:
            raise RuntimeError("No video stream available")
        if not target_audio:
            raise RuntimeError("No audio stream available")

        # Select best CDN URL
        def get_best_url(stream: dict) -> str:
            base_url = stream["baseUrl"]
            backup_urls = stream.get("backupUrl", [])
            all_urls = [base_url] + backup_urls

            def cdn_priority(url: str) -> int:
                if "upos-" in url:
                    return 0  # Best
                elif "cn-" in url:
                    return 1  # Good
                elif "mcdn" in url:
                    return 2  # OK
                else:
                    return 3  # Last resort

            all_urls.sort(key=cdn_priority)
            return all_urls[0]

        best_video_url = get_best_url(target_video)
        best_audio_url = get_best_url(target_audio)

        logger.info(
            f"Selected streams: Video {target_video['id']}, Audio {target_audio['id']}"
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
        """
        Download file with progress tracking.

        Args:
            url: Download URL (must include Referer header)
            output_path: Output file path
            description: Description for logging

        Returns:
            True if successful
        """
        try:
            logger.info(f"Downloading {description}...")

            # Critical: Referer header for CDN access
            headers = {**self.HEADERS}

            async with self.client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0 and downloaded % (1024 * 1024) < 8192:
                            progress = (downloaded / total_size) * 100
                            logger.debug(f"{description}: {progress:.1f}%")

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
        """
        Merge video and audio using FFmpeg (stream copy, lossless).

        Args:
            video_path: Video stream file (.m4s)
            audio_path: Audio stream file (.m4s)
            output_path: Output MP4 file

        Returns:
            True if successful
        """
        try:
            logger.info("Merging video and audio...")

            # Stream copy (lossless, fast)
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-strict", "unofficial",
                "-f", "mp4",
                "-y",
                str(output_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,
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
        video_quality: int = 80,
        audio_quality: int = 30280,
        **kwargs: Any,
    ) -> Path | None:
        """
        Download video asynchronously.

        Args:
            url: B站 video URL
            video_quality: Video quality ID (default: 80=1080P)
            audio_quality: Audio quality ID (default: 30280=192k)
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

            # Select best streams
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

            # Verify output
            if final_output.exists() and final_output.stat().st_size > 0:
                logger.info(f"Download successful: {final_output}")
                return final_output
            else:
                logger.error("Final output missing or empty")
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
            video_quality: Video quality ID
            audio_quality: Audio quality ID
            **kwargs: Additional options

        Returns:
            Downloaded video path or None if failed
        """
        try:
            # Check if we're already in an async context
            import asyncio
            try:
                asyncio.get_running_loop()
                # We're in an async context, use asyncio.create_task instead
                logger.warning("Already in async context, using sync fallback")
                # Fallback to synchronous httpx client
                return self._download_sync_fallback(url, video_quality, audio_quality, **kwargs)
            except RuntimeError:
                # No running loop, safe to use asyncio.run()
                return asyncio.run(self.download_async(url, video_quality, audio_quality, **kwargs))
        except KeyboardInterrupt:
            logger.info("Download interrupted")
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

    def _download_sync_fallback(
        self,
        url: str,
        video_quality: int = 80,
        audio_quality: int = 30280,
        **kwargs: Any,
    ) -> Path | None:
        """
        Synchronous fallback when already in async context.
        Uses synchronous httpx client.

        Args:
            url: B站 video URL
            video_quality: Video quality ID
            audio_quality: Audio quality ID
            **kwargs: Additional options

        Returns:
            Downloaded video path or None if failed
        """
        import re
        import httpx

        try:
            # Extract BV ID from URL
            match = re.search(r"BV[\w]+", url)
            if not match:
                logger.error(f"Invalid B站 URL: {url}")
                return None

            bvid = match.group(0)
            logger.info(f"Downloading B站 video (sync fallback): {bvid}")

            # Use sync client
            sync_client = httpx.Client(
                headers=self.HEADERS,
                cookies={"SESSDATA": self.sessdata} if self.sessdata else None,
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=True,
            )

            # Get video info (sync)
            resp = sync_client.get(
                self.API_VIDEO_INFO,
                params={"bvid": bvid},
            )
            data = resp.json()

            if data.get("code") != 0:
                logger.error(f"Failed to get video info: {data.get('message')}")
                sync_client.close()
                return None

            video_info = data["data"]
            title = video_info["title"]
            cid = video_info["cid"]
            logger.info(f"Video title: {title}")

            # Get WBI keys and playurl
            self._get_wbi_keys_sync(sync_client)

            params = {
                "bvid": bvid,
                "cid": cid,
                "qn": 127,
                "fnval": 4048,
                "fourk": 1,
            }
            signed_url = f"{self.API_PLAYURL}?{self._sign_wbi(params)}"

            resp = sync_client.get(signed_url)
            data = resp.json()

            if data.get("code") != 0:
                logger.error(f"Failed to get playurl: {data.get('message')}")
                sync_client.close()
                return None

            playurl_data = data["data"]
            if "dash" not in playurl_data:
                logger.error("DASH format not available")
                sync_client.close()
                return None

            dash_data = playurl_data["dash"]
            video_stream, audio_stream = self._select_best_streams(
                dash_data, video_quality, audio_quality
            )

            # Prepare output paths
            safe_title = re.sub(r'[<>:"/\\|?*]', "_", title)[:100]
            temp_video = self.output_dir / f"{safe_title}_video.m4s"
            temp_audio = self.output_dir / f"{safe_title}_audio.m4s"
            final_output = self.output_dir / f"{safe_title}.mp4"

            # Download video (sync)
            if not self._download_file_sync(sync_client, video_stream["url"], temp_video, "video stream"):
                sync_client.close()
                return None

            # Download audio (sync)
            if not self._download_file_sync(sync_client, audio_stream["url"], temp_audio, "audio stream"):
                temp_video.unlink(missing_ok=True)
                sync_client.close()
                return None

            # Merge with FFmpeg
            if not self._merge_video_audio(temp_video, temp_audio, final_output):
                temp_video.unlink(missing_ok=True)
                temp_audio.unlink(missing_ok=True)
                sync_client.close()
                return None

            # Cleanup
            temp_video.unlink(missing_ok=True)
            temp_audio.unlink(missing_ok=True)
            sync_client.close()

            if final_output.exists() and final_output.stat().st_size > 0:
                logger.info(f"Download successful (sync fallback): {final_output}")
                return final_output
            else:
                logger.error("Final output missing or empty")
                return None

        except Exception as e:
            logger.error(f"Sync fallback download failed: {e}")
            return None

    def _get_wbi_keys_sync(self, client: httpx.Client) -> None:
        """Get WBI keys using sync client."""
        import time
        from functools import reduce

        if self.mixin_key and time.time() - self.wbi_keys_updated_at < 1800:
            return

        resp = client.get(self.API_NAV)
        data = resp.json()

        if data.get("code") != 0:
            return

        wbi_img = data["data"]["wbi_img"]
        img_url = wbi_img["img_url"]
        sub_url = wbi_img["sub_url"]

        self.img_key = img_url.rsplit("/", 1)[1].split(".")[0]
        self.sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]

        combined = self.img_key + self.sub_key
        self.mixin_key = reduce(
            lambda s, i: s + combined[i], self.MIXIN_KEY_ENC_TAB, ""
        )[:32]
        self.wbi_keys_updated_at = time.time()

    def _download_file_sync(
        self,
        client: httpx.Client,
        url: str,
        output_path: Path,
        description: str = "file",
    ) -> bool:
        """Download file using sync client."""
        try:
            logger.info(f"Downloading {description}...")
            headers = {**self.HEADERS}

            with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

            logger.info(f"{description} downloaded: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to download {description}: {e}")
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()