"""
Base ASR Implementation for Learning Assistant.

This module provides the base class for ASR (Automatic Speech Recognition) implementations.
"""

import os
import subprocess
import threading
import zlib
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from loguru import logger

from learning_assistant.core.history_manager import HistoryManager

from .asr_data import ASRData, ASRDataSeg


class BaseASR:
    """
    Base class for ASR implementations.

    Provides common functionality including:
    - Audio file loading and validation
    - CRC32-based file identification
    - Disk caching with automatic key generation
    - Template method pattern for subclass implementation
    - Rate limiting for public services
    """

    SUPPORTED_SOUND_FORMAT = ["flac", "m4a", "mp3", "wav", "ogg"]
    _lock = threading.Lock()

    # Rate limiting settings (for public charity services)
    RATE_LIMIT_MAX_CALLS = 100
    RATE_LIMIT_MAX_DURATION = 360 * 60  # 360 minutes in seconds
    RATE_LIMIT_TIME_WINDOW = 12 * 3600  # 12 hours in seconds

    def __init__(
        self,
        audio_input: str | bytes | Path | None = None,
        use_cache: bool = True,
        need_word_time_stamp: bool = False,
        cache_dir: Path | None = None,
    ) -> None:
        """
        Initialize ASR with audio data.

        Args:
            audio_input: Path to audio file or raw audio bytes
            use_cache: Whether to cache recognition results
            need_word_time_stamp: Whether to return word-level timestamps
            cache_dir: Cache directory path
        """
        self.audio_input = audio_input
        self.file_binary: bytes | None = None
        self.use_cache = use_cache
        self.need_word_time_stamp = need_word_time_stamp

        # Initialize cache
        self.cache_dir = cache_dir or Path("data/cache/asr")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._history_manager = HistoryManager(history_dir=self.cache_dir)

        # Load audio data
        self._set_data()

        # Calculate audio duration
        self.audio_duration = self._get_audio_duration()

        logger.info(
            f"{self.__class__.__name__} initialized with audio_duration={self.audio_duration:.2f}s"
        )

    def _set_data(self) -> None:
        """
        Load audio data and compute CRC32 hash for cache key.
        """
        if self.audio_input is None:
            raise ValueError("audio_input must be provided")

        # Convert Path to str if needed
        audio_path: str | bytes
        if isinstance(self.audio_input, Path):
            audio_path = str(self.audio_input)
        else:
            audio_path = self.audio_input

        # Load audio data
        if isinstance(audio_path, bytes):
            self.file_binary = audio_path
        elif isinstance(audio_path, str):
            ext = audio_path.split(".")[-1].lower()
            if ext not in self.SUPPORTED_SOUND_FORMAT:
                raise ValueError(f"Unsupported sound format: {ext}")
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            with open(audio_path, "rb") as f:
                self.file_binary = f.read()
        else:
            raise ValueError("audio_input must be str, bytes, or Path")

        # Calculate CRC32 hash
        crc32_value = zlib.crc32(self.file_binary) & 0xFFFFFFFF
        self.crc32_hex = format(crc32_value, "08x")

        logger.debug(f"Audio CRC32: {self.crc32_hex}")

    def _get_audio_duration(self) -> float:
        """
        Get audio duration in seconds using ffprobe.

        Returns:
            Audio duration in seconds
        """
        if not self.file_binary:
            return 0.01

        try:
            # Write audio data to temporary file for ffprobe
            with NamedTemporaryFile(suffix=".mp3", delete=True) as tmp_file:
                tmp_file.write(self.file_binary)
                tmp_file.flush()

                # Use ffprobe to get duration
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v", "quiet",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        tmp_file.name,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and result.stdout.strip():
                    duration = float(result.stdout.strip())
                    return duration
                else:
                    logger.warning(f"ffprobe failed: {result.stderr}")
                    # Fallback: estimate based on file size
                    estimated_duration = len(self.file_binary) / (16 * 1024)
                    return max(estimated_duration, 60.0)

        except Exception as e:
            logger.warning(f"Failed to get audio duration: {e}")
            # Fallback: estimate based on file size (rough approximation)
            # MP3 at 128kbps ≈ 16KB per second
            estimated_duration = len(self.file_binary) / (16 * 1024)
            return max(estimated_duration, 60.0)

    def run(
        self,
        callback: Callable[[int, str], None] | None = None,
        **kwargs: Any,
    ) -> ASRData:
        """
        Run ASR with caching support.

        Args:
            callback: Optional progress callback(progress: int, message: str)
            **kwargs: Additional arguments passed to _run()

        Returns:
            ASRData: Recognition results with segments
        """
        # Generate cache key
        cache_key = self._get_key()

        # Try cache first
        if self.use_cache:
            cached_result = self._load_from_cache(cache_key)
            if cached_result is not None:
                logger.info("Found cached ASR result, returning directly")
                segments = self._make_segments(cached_result)
                return ASRData(segments=segments)

        # Run ASR
        logger.info(f"Running ASR for audio duration={self.audio_duration:.2f}s")
        resp_data = self._run(callback, **kwargs)

        # Cache result
        if self.use_cache:
            self._save_to_cache(cache_key, resp_data)

        # Create segments
        segments = self._make_segments(resp_data)
        return ASRData(segments=segments)

    def _get_key(self) -> str:
        """
        Get cache key for this ASR request.

        Default implementation uses file CRC32.
        Subclasses can override to include additional parameters.

        Returns:
            Cache key string
        """
        base_key = f"{self.__class__.__name__}:{self.crc32_hex}"
        if self.need_word_time_stamp:
            base_key += ":word_level"
        return base_key

    def _load_from_cache(self, cache_key: str) -> dict[str, Any] | None:
        """
        Load ASR result from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached ASR data or None if not found
        """
        try:
            # Use history manager to search for cached results
            if cache_key in self._history_manager._cache:
                record = self._history_manager._cache[cache_key]
                # Parse output JSON
                import json

                cached_data: dict[str, Any] = json.loads(record.output)
                return cached_data
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}")
        return None

    def _save_to_cache(self, cache_key: str, asr_result: dict[str, Any]) -> None:
        """
        Save ASR result to cache.

        Args:
            cache_key: Cache key
            asr_result: ASR result data
        """
        try:
            # Save as history record
            import json
            from datetime import datetime

            record_id = self._history_manager.add_record(
                module="transcriber",
                input=cache_key,
                output=json.dumps(asr_result),
                metadata={
                    "audio_duration": self.audio_duration,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            logger.debug(
                f"ASR result cached with key: {cache_key}, record_id: {record_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")

    def _make_segments(self, resp_data: dict[str, Any]) -> list[ASRDataSeg]:
        """
        Convert ASR response to segment list.

        Args:
            resp_data: Raw response from ASR service

        Returns:
            List of ASRDataSeg objects

        Raises:
            NotImplementedError: Must be implemented in subclass
        """
        raise NotImplementedError(
            "_make_segments method must be implemented in subclass"
        )

    def _run(
        self,
        callback: Callable[[int, str], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute ASR service and return raw response.

        Args:
            callback: Progress callback(progress: int, message: str)
            **kwargs: Implementation-specific parameters

        Returns:
            Raw response data

        Raises:
            NotImplementedError: Must be implemented in subclass
        """
        raise NotImplementedError("_run method must be implemented in subclass")

    def _check_rate_limit(self) -> None:
        """
        Check rate limit for public services.

        Raises:
            RuntimeError: If rate limit exceeded
        """
        service_name = self.__class__.__name__

        # Simplified rate limit check without database queries
        # In production, implement proper rate limiting with Redis or database
        logger.debug(
            f"Rate limit check for {service_name}: "
            f"audio_duration={self.audio_duration:.2f}s"
        )
