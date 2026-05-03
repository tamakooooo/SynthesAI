"""
VideoCaptioner ASR Implementation for Learning Assistant.

This module provides ASR using VideoCaptioner CLI tool.
VideoCaptioner provides multiple free ASR engines including:
- bijian (必剪, free, B站)
- jianying (剪映, free)
- faster-whisper (local, multilingual)
- whisper-api (OpenAI Whisper API)

Installation:
    pip install videocaptioner

CLI Usage:
    videocaptioner transcribe video.mp4 --asr bijian --output subtitle.srt
"""

import json
import re
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger

from .asr_data import ASRData, ASRDataSeg
from .base import BaseASR
from .status import ASRStatus


class VideoCaptionerASR(BaseASR):
    """
    VideoCaptioner ASR implementation using CLI tool.

    Provides multiple free ASR backends through VideoCaptioner CLI.
    Free options (no API key required):
    - bijian: B站必剪语音识别 (推荐中文视频)
    - jianying: 剪映语音识别

    Local options (需要安装模型):
    - faster-whisper: Faster Whisper 本地模型

    API options (需要 API Key):
    - whisper-api: OpenAI Whisper API
    - whisper-cpp: Whisper.cpp 本地推理

    Note: This is a free service with rate limiting for cloud ASR.
    """

    # Available ASR engines in VideoCaptioner
    AVAILABLE_ASR_ENGINES = ["bijian", "jianying", "faster-whisper", "whisper-api", "whisper-cpp"]

    # Default engine (free, no API key)
    DEFAULT_ASR_ENGINE = "bijian"

    # CLI timeout (seconds) - longer for cloud ASR
    CLI_TIMEOUT = 600

    def __init__(
        self,
        audio_input: str | bytes | Path | None = None,
        use_cache: bool = True,
        need_word_time_stamp: bool = False,
        cache_dir: Path | None = None,
        asr_engine: str = "bijian",
        videocaptioner_path: str | None = None,
    ) -> None:
        """
        Initialize VideoCaptionerASR.

        Args:
            audio_input: Path to audio file or raw audio bytes
            use_cache: Whether to cache recognition results
            need_word_time_stamp: Whether to return word-level timestamps
            cache_dir: Cache directory path
            asr_engine: ASR engine to use (bijian/jianying/faster-whisper/whisper-api/whisper-cpp)
            videocaptioner_path: Path to videocaptioner CLI (default: auto-detect)
        """
        super().__init__(
            audio_input=audio_input,
            use_cache=use_cache,
            need_word_time_stamp=need_word_time_stamp,
            cache_dir=cache_dir,
        )

        # Validate and set ASR engine
        if asr_engine not in self.AVAILABLE_ASR_ENGINES:
            logger.warning(f"Unknown ASR engine: {asr_engine}, using default '{self.DEFAULT_ASR_ENGINE}'")
            asr_engine = self.DEFAULT_ASR_ENGINE

        self.asr_engine = asr_engine
        self.videocaptioner_path = videocaptioner_path or self._find_videocaptioner()

        logger.info(f"VideoCaptionerASR initialized: engine={self.asr_engine}, cli={self.videocaptioner_path}")

    def _find_videocaptioner(self) -> str:
        """
        Find videocaptioner CLI path.

        Returns:
            CLI path or raises RuntimeError
        """
        import sys

        # Try common locations including virtual environments
        candidates = [
            "videocaptioner",
            "python -m videocaptioner",
        ]

        # Add virtual environment paths
        venv_candidates = []

        # Current Python's bin directory (if in venv)
        python_bin = Path(sys.executable).parent
        venv_candidates.append(str(python_bin / "videocaptioner"))

        # Common virtual environment names
        for venv_name in [".venv", ".venv-py312", "venv", "env"]:
            venv_path = Path(venv_name)
            if venv_path.exists():
                venv_candidates.append(str(venv_path / "bin" / "videocaptioner"))

        # Combine all candidates
        all_candidates = venv_candidates + candidates

        for candidate in all_candidates:
            try:
                # Handle "python -m" style commands
                cmd = candidate.split() if " " in candidate else [candidate]
                result = subprocess.run(
                    cmd + ["--help"],
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.info(f"Found videocaptioner: {candidate}")
                    return candidate
            except Exception:
                continue

        raise RuntimeError(
            "videocaptioner CLI not found. Install with: pip install videocaptioner"
        )

    def _run(
        self,
        callback: Callable[[int, str], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute ASR using VideoCaptioner CLI.

        Args:
            callback: Progress callback(progress: int, message: str)
            **kwargs: Additional arguments

        Returns:
            Raw ASR result data (parsed from SRT)
        """
        # Default callback
        def _default_callback(progress: int, message: str) -> None:
            logger.info(f"[{progress}%] {message}")

        if callback is None:
            callback = _default_callback

        # Create temp file for audio input if bytes
        audio_path: Path | str
        if isinstance(self.audio_input, bytes):
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(self.audio_input)
                audio_path = tmp.name
        elif isinstance(self.audio_input, Path):
            audio_path = str(self.audio_input)
        else:
            audio_path = self.audio_input

        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Step 1: Upload/Prepare
            callback(*ASRStatus.UPLOADING.callback_tuple())

            # Step 2: Transcribe using CLI
            callback(*ASRStatus.TRANSCRIBING.callback_tuple())

            # Build CLI command
            cmd = self.videocaptioner_path.split() + [
                "transcribe",
                str(audio_path),
                "--asr", self.asr_engine,
                "--output", output_path,
            ]

            logger.info(f"Running: {' '.join(cmd)}")
            logger.info("Transcribing with VideoCaptioner (this may take 1-3 minutes)...")

            # Execute CLI
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.CLI_TIMEOUT,
            )

            if result.returncode != 0:
                callback(*ASRStatus.FAILED.callback_tuple())
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise RuntimeError(f"VideoCaptioner CLI failed: {error_msg}")

            # Step 3: Parse result
            callback(*ASRStatus.COMPLETED.callback_tuple())

            # Read SRT output
            srt_content = Path(output_path).read_text(encoding="utf-8")
            logger.info(f"Transcription completed: {len(srt_content)} characters")

            # Parse SRT to segments
            utterances = self._parse_srt(srt_content)

            # Return as raw data (compatible with ASRData format)
            result_data = {
                "utterances": utterances,
                "srt_content": srt_content,
            }

            logger.info(f"Parsed {len(utterances)} segments")
            return result_data

        finally:
            # Cleanup temp files
            if isinstance(self.audio_input, bytes):
                Path(audio_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def _parse_srt(self, srt_content: str) -> list[dict[str, Any]]:
        """
        Parse SRT content to utterance format.

        SRT format:
        1
        00:00:00,000 --> 00:00:05,000
        Hello world

        Args:
            srt_content: SRT subtitle content

        Returns:
            List of utterances with transcript, start_time, end_time
        """
        utterances = []

        # SRT timestamp pattern
        pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?:\n\n|\n?$)"

        matches = re.findall(pattern, srt_content, re.MULTILINE)

        for match in matches:
            index = int(match[0])
            start_time_str = match[1]
            end_time_str = match[2]
            text = match[3].strip()

            # Convert timestamp to milliseconds
            start_time = self._srt_timestamp_to_ms(start_time_str)
            end_time = self._srt_timestamp_to_ms(end_time_str)

            utterance = {
                "transcript": text,
                "start_time": start_time,
                "end_time": end_time,
            }
            utterances.append(utterance)

        return utterances

    def _srt_timestamp_to_ms(self, timestamp: str) -> int:
        """
        Convert SRT timestamp to milliseconds.

        Args:
            timestamp: SRT timestamp format "00:00:00,000"

        Returns:
            Milliseconds
        """
        hours, minutes, seconds_ms = timestamp.split(":")
        seconds, ms = seconds_ms.split(",")

        total_ms = (
            int(hours) * 3600000 +
            int(minutes) * 60000 +
            int(seconds) * 1000 +
            int(ms)
        )
        return total_ms

    def _make_segments(self, resp_data: dict[str, Any]) -> list[ASRDataSeg]:
        """
        Convert ASR response to segment list.

        Args:
            resp_data: Raw response from VideoCaptioner

        Returns:
            List of ASRDataSeg objects
        """
        utterances = resp_data.get("utterances", [])

        # VideoCaptioner outputs sentence-level timestamps
        segments = [
            ASRDataSeg(
                text=utterance.get("transcript", "").strip(),
                start_time=utterance.get("start_time", 0),
                end_time=utterance.get("end_time", 0),
            )
            for utterance in utterances
        ]

        return segments

    def _get_key(self) -> str:
        """
        Get cache key including ASR engine.

        Returns:
            Cache key string
        """
        base_key = f"{self.__class__.__name__}:{self.asr_engine}:{self.crc32_hex}"
        if self.need_word_time_stamp:
            base_key += ":word_level"
        return base_key

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if VideoCaptioner CLI is available.

        Returns:
            True if available
        """
        try:
            result = subprocess.run(
                ["videocaptioner", "--help"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False