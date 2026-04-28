"""
SiliconCloud ASR Implementation for Learning Assistant.

This module provides ASR using SiliconCloud (硅基流动) API.
SiliconCloud provides high-quality ASR models including:
- FunAudioLLM/SenseVoiceSmall (推荐, 多语言支持)
- TeleAI/TeleSpeechASR

API Documentation: https://docs.siliconflow.cn/cn/api-reference/audio/create-audio-transcriptions

Usage:
    # Set API key via environment variable
    export SILICONCLOUD_API_KEY="sk-..."

    # Or pass directly
    asr = SiliconCloudASR(api_key="sk-...")
    result = asr.transcribe("audio.mp3")

Note: SiliconCloud ASR returns text only (no timestamps).
      For timestamp support, use VideoCaptionerASR instead.
"""

import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
from loguru import logger

from .asr_data import ASRData, ASRDataSeg
from .base import BaseASR
from .status import ASRStatus


class SiliconCloudASR(BaseASR):
    """
    SiliconCloud (硅基流动) ASR implementation.

    Uses SiliconCloud API for audio transcription.
    Compatible with OpenAI API format.

    Available models:
    - FunAudioLLM/SenseVoiceSmall: High-quality multilingual ASR
    - TeleAI/TeleSpeechASR: Alternative ASR model

    Limitations:
    - Max duration: 1 hour
    - Max file size: 50MB
    - Returns text only (no word-level timestamps)

    Note: This service requires API key.
    Get your key at: https://cloud.siliconflow.cn/account/ak
    """

    # API endpoint
    API_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"

    # Available models
    AVAILABLE_MODELS = [
        "FunAudioLLM/SenseVoiceSmall",  # 推荐
        "TeleAI/TeleSpeechASR",
    ]

    # Default model (推荐)
    DEFAULT_MODEL = "TeleAI/TeleSpeechASR"

    # Request timeout (seconds)
    REQUEST_TIMEOUT = 300  # 5 minutes for long audio

    # API key environment variable
    API_KEY_ENV = "SILICONCLOUD_API_KEY"

    def __init__(
        self,
        audio_input: str | bytes | Path | None = None,
        use_cache: bool = True,
        need_word_time_stamp: bool = False,
        cache_dir: Path | None = None,
        api_key: str | None = None,
        model: str = "FunAudioLLM/SenseVoiceSmall",
    ) -> None:
        """
        Initialize SiliconCloudASR.

        Args:
            audio_input: Path to audio file or raw audio bytes
            use_cache: Whether to cache recognition results
            need_word_time_stamp: Whether to return word-level timestamps
                Note: SiliconCloud ASR does not support timestamps.
            cache_dir: Cache directory path
            api_key: SiliconCloud API key (or use env var SILICONCLOUD_API_KEY)
            model: ASR model to use
        """
        super().__init__(
            audio_input=audio_input,
            use_cache=use_cache,
            need_word_time_stamp=need_word_time_stamp,
            cache_dir=cache_dir,
        )

        # Get API key
        self.api_key = api_key or os.environ.get(self.API_KEY_ENV)
        if not self.api_key:
            raise ValueError(
                f"SiliconCloud API key required. "
                f"Set via environment variable '{self.API_KEY_ENV}' or pass 'api_key' parameter. "
                f"Get your key at: https://cloud.siliconflow.cn/account/ak"
            )

        # Validate model
        if model not in self.AVAILABLE_MODELS:
            logger.warning(f"Unknown model: {model}, using default '{self.DEFAULT_MODEL}'")
            model = self.DEFAULT_MODEL

        self.model = model

        # Warn about timestamp limitation
        if self.need_word_time_stamp:
            logger.warning(
                "SiliconCloud ASR does not support word-level timestamps. "
                "Using sentence-level estimation instead."
            )

        logger.info(f"SiliconCloudASR initialized: model={self.model}")

    def _run(
        self,
        callback: Callable[[int, str], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute ASR using SiliconCloud API.

        Args:
            callback: Progress callback(progress: int, message: str)
            **kwargs: Additional arguments

        Returns:
            Raw ASR result data
        """
        # Default callback
        def _default_callback(progress: int, message: str) -> None:
            logger.info(f"[{progress}%] {message}")

        if callback is None:
            callback = _default_callback

        # Check file size limit
        if self.file_binary and len(self.file_binary) > 50 * 1024 * 1024:
            raise ValueError(
                f"File size exceeds 50MB limit: {len(self.file_binary) / (1024 * 1024):.1f}MB"
            )

        # Check duration estimate (rough: MP3 ~16KB/sec at 128kbps)
        if self.audio_duration > 3600:  # 1 hour
            raise ValueError(
                f"Audio duration exceeds 1 hour limit: {self.audio_duration / 60:.1f} minutes"
            )

        # Prepare file for upload
        audio_path: Path | str
        temp_file: tempfile.NamedTemporaryFile | None = None

        if isinstance(self.audio_input, bytes):
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.write(self.audio_input)
            audio_path = temp_file.name
        elif isinstance(self.audio_input, Path):
            audio_path = str(self.audio_input)
        else:
            audio_path = self.audio_input

        try:
            # Step 1: Upload
            callback(*ASRStatus.UPLOADING.callback_tuple())

            # Step 2: Transcribe
            callback(*ASRStatus.TRANSCRIBING.callback_tuple())
            logger.info(f"Transcribing with SiliconCloud API: model={self.model}")

            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }

            # Read file
            with open(audio_path, "rb") as f:
                files = {
                    "file": ("audio.mp3", f, "audio/mpeg"),
                    "model": (None, self.model),
                }

                # Make API request
                response = requests.post(
                    self.API_URL,
                    headers=headers,
                    files=files,
                    timeout=self.REQUEST_TIMEOUT,
                )

            # Check response
            if response.status_code == 401:
                callback(*ASRStatus.FAILED.callback_tuple())
                raise ValueError("Invalid API key")
            elif response.status_code == 429:
                callback(*ASRStatus.FAILED.callback_tuple())
                raise RuntimeError("Rate limit exceeded. Please wait and retry.")
            elif response.status_code != 200:
                callback(*ASRStatus.FAILED.callback_tuple())
                error_msg = response.json().get("message", response.text)
                raise RuntimeError(f"API error: {error_msg}")

            # Parse response
            result = response.json()
            transcript_text = result.get("text", "")

            if not transcript_text:
                callback(*ASRStatus.FAILED.callback_tuple())
                raise RuntimeError("Empty transcription result")

            # Step 3: Complete
            callback(*ASRStatus.COMPLETED.callback_tuple())
            logger.info(f"Transcription completed: {len(transcript_text)} characters")

            # Return raw data (text only, no timestamps)
            return {
                "text": transcript_text,
                "model": self.model,
                "duration": self.audio_duration,
            }

        finally:
            # Cleanup temp file
            if temp_file:
                Path(temp_file.name).unlink(missing_ok=True)

    def _make_segments(self, resp_data: dict[str, Any]) -> list[ASRDataSeg]:
        """
        Convert ASR response to segment list.

        Since SiliconCloud returns text only without timestamps,
        we create estimated segments based on audio duration.

        Args:
            resp_data: Raw response from SiliconCloud

        Returns:
            List of ASRDataSeg objects (estimated timestamps)
        """
        text = resp_data.get("text", "")
        duration_ms = resp_data.get("duration", 0) * 1000

        if not text:
            return []

        # Split text into sentences for estimated segmentation
        # This is a rough approximation since no timestamps are provided
        sentences = self._split_into_sentences(text)

        if not sentences:
            # Single segment for entire text
            return [
                ASRDataSeg(
                    text=text,
                    start_time=0,
                    end_time=duration_ms,
                )
            ]

        # Estimate timestamp for each sentence based on character ratio
        total_chars = sum(len(s) for s in sentences)
        segments = []
        current_time = 0

        for sentence in sentences:
            # Estimate duration based on character proportion
            char_ratio = len(sentence) / total_chars if total_chars > 0 else 0
            sentence_duration = duration_ms * char_ratio

            segments.append(
                ASRDataSeg(
                    text=sentence,
                    start_time=current_time,
                    end_time=current_time + sentence_duration,
                )
            )
            current_time += sentence_duration

        return segments

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for timestamp estimation.

        Args:
            text: Full transcript text

        Returns:
            List of sentences
        """
        # Split by common sentence delimiters
        import re

        # Chinese and English sentence patterns
        pattern = r'[。！？\.!?]+'

        # Split and keep delimiters
        parts = re.split(pattern, text)

        # Re-attach delimiters and filter empty
        sentences = []
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                sentences.append(part)

        return sentences

    def _get_key(self) -> str:
        """
        Get cache key including model name.

        Returns:
            Cache key string
        """
        return f"{self.__class__.__name__}:{self.model}:{self.crc32_hex}"

    @classmethod
    def is_available(cls, api_key: str | None = None) -> bool:
        """
        Check if SiliconCloud API is available with valid key.

        Args:
            api_key: API key to test (optional)

        Returns:
            True if API key is valid
        """
        key = api_key or os.environ.get(cls.API_KEY_ENV)
        if not key:
            return False

        # Simple check - API key format
        return len(key) > 10  # Basic validation