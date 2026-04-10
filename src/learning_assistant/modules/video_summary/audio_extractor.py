"""
Audio Extractor for Learning Assistant.

This module provides audio extraction capabilities using FFmpeg.
"""

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class AudioExtractionProgress:
    """
    Audio extraction progress information.
    """

    status: str
    percentage: float
    current_time: float  # seconds
    total_duration: float  # seconds


@dataclass
class AudioInfo:
    """
    Audio information structure.
    """

    duration: float  # seconds
    sample_rate: int
    channels: int
    bitrate: int  # kbps
    codec: str


class AudioExtractor:
    """
    Audio Extractor using FFmpeg.

    Supports:
    - Audio extraction from video files
    - Format conversion (MP3, WAV, AAC, etc.)
    - Quality optimization
    - Progress callback
    """

    # Supported audio formats
    SUPPORTED_FORMATS = ["mp3", "wav", "aac", "flac", "ogg", "m4a"]

    # Default quality settings
    DEFAULT_QUALITY = {
        "mp3": {"bitrate": "192k", "sample_rate": 44100},
        "wav": {"sample_rate": 44100, "bit_depth": 16},
        "aac": {"bitrate": "192k", "sample_rate": 44100},
        "flac": {"sample_rate": 44100},
        "ogg": {"quality": "5", "sample_rate": 44100},
        "m4a": {"bitrate": "192k", "sample_rate": 44100},
    }

    def __init__(
        self,
        output_dir: Path | None = None,
        progress_callback: Callable[[AudioExtractionProgress], None] | None = None,
    ) -> None:
        """
        Initialize AudioExtractor.

        Args:
            output_dir: Output directory for extracted audio
            progress_callback: Progress callback function
        """
        self.output_dir = output_dir or Path("data/audio")
        self.progress_callback = progress_callback

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check FFmpeg availability
        if not self._check_ffmpeg():
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html"
            )

        logger.info(f"AudioExtractor initialized with output_dir: {self.output_dir}")

    def _check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is available.

        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def extract_audio(
        self,
        video_path: Path,
        output_filename: str | None = None,
        output_format: str = "mp3",
        quality: dict[str, Any] | None = None,
    ) -> Path | None:
        """
        Extract audio from video file.

        Args:
            video_path: Video file path
            output_filename: Output filename (without extension)
            output_format: Output audio format (mp3, wav, aac, etc.)
            quality: Quality settings (bitrate, sample_rate, etc.)

        Returns:
            Extracted audio path or None if extraction failed
        """
        # Validate inputs
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return None

        if output_format not in self.SUPPORTED_FORMATS:
            logger.error(f"Unsupported format: {output_format}")
            return None

        logger.info(f"Extracting audio from: {video_path}, format: {output_format}")

        # Prepare output path
        if output_filename:
            output_path = self.output_dir / f"{output_filename}.{output_format}"
        else:
            output_path = self.output_dir / f"{video_path.stem}.{output_format}"

        # Get video duration for progress tracking
        video_duration = self._get_video_duration(video_path)

        # Build FFmpeg command
        cmd = self._build_ffmpeg_command(
            video_path=video_path,
            output_path=output_path,
            output_format=output_format,
            quality=quality,
        )

        try:
            # Execute FFmpeg with progress monitoring
            self._execute_ffmpeg_with_progress(cmd=cmd, total_duration=video_duration)

            if output_path.exists():
                logger.info(f"Audio extracted successfully: {output_path}")
                return output_path
            else:
                logger.error("Audio extraction failed: output file not created")
                return None

        except Exception as e:
            logger.error(f"Failed to extract audio: {e}")
            return None

    def convert_format(
        self,
        input_audio: Path,
        output_format: str,
        output_filename: str | None = None,
        quality: dict[str, Any] | None = None,
    ) -> Path | None:
        """
        Convert audio to different format.

        Args:
            input_audio: Input audio file path
            output_format: Target format
            output_filename: Output filename (without extension)
            quality: Quality settings

        Returns:
            Converted audio path or None if conversion failed
        """
        if not input_audio.exists():
            logger.error(f"Audio file not found: {input_audio}")
            return None

        if output_format not in self.SUPPORTED_FORMATS:
            logger.error(f"Unsupported format: {output_format}")
            return None

        logger.info(f"Converting audio: {input_audio} -> {output_format}")

        # Prepare output path
        if output_filename:
            output_path = self.output_dir / f"{output_filename}.{output_format}"
        else:
            output_path = self.output_dir / f"{input_audio.stem}.{output_format}"

        # Build FFmpeg command for conversion
        cmd = ["ffmpeg", "-i", str(input_audio)]

        # Add format-specific options
        if quality:
            quality_settings = quality
        else:
            quality_settings = self.DEFAULT_QUALITY.get(
                output_format, {}
            )  # type: ignore[assignment]
        cmd.extend(self._get_format_options(output_format, quality_settings))

        cmd.append(str(output_path))

        try:
            # Execute conversion
            subprocess.run(cmd, capture_output=True, check=True, timeout=600)

            if output_path.exists():
                logger.info(f"Audio converted successfully: {output_path}")
                return output_path
            else:
                logger.error("Audio conversion failed: output file not created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to convert audio: {e}")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Audio conversion timed out")
            return None

    def get_audio_info(self, audio_path: Path) -> AudioInfo | None:
        """
        Get audio information using FFprobe.

        Args:
            audio_path: Audio file path

        Returns:
            AudioInfo or None if extraction failed
        """
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return None

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(audio_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                logger.error(f"FFprobe failed: {result.stderr}")
                return None

            import json

            data = json.loads(result.stdout)

            # Find audio stream
            audio_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            if not audio_stream:
                logger.error("No audio stream found")
                return None

            # Extract audio info
            duration = float(data.get("format", {}).get("duration", 0))
            sample_rate = int(audio_stream.get("sample_rate", 44100))
            channels = int(audio_stream.get("channels", 2))
            bitrate = int(data.get("format", {}).get("bit_rate", 0)) // 1000
            codec = audio_stream.get("codec_name", "unknown")

            audio_info = AudioInfo(
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                bitrate=bitrate,
                codec=codec,
            )

            logger.info(f"Audio info: duration={duration}s, codec={codec}")
            return audio_info

        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return None

    def _get_video_duration(self, video_path: Path) -> float:
        """
        Get video duration in seconds.

        Args:
            video_path: Video file path

        Returns:
            Duration in seconds
        """
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def _build_ffmpeg_command(
        self,
        video_path: Path,
        output_path: Path,
        output_format: str,
        quality: dict[str, Any] | None,
    ) -> list[str]:
        """
        Build FFmpeg command for audio extraction.

        Args:
            video_path: Video file path
            output_path: Output audio path
            output_format: Output format
            quality: Quality settings

        Returns:
            FFmpeg command as list of strings
        """
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vn",  # No video
            "-y",  # Overwrite output
        ]

        # Add format-specific options
        if quality:
            quality_settings = quality
        else:
            quality_settings = self.DEFAULT_QUALITY.get(
                output_format, {}
            )  # type: ignore[assignment]
        cmd.extend(self._get_format_options(output_format, quality_settings))

        cmd.append(str(output_path))

        return cmd

    def _get_format_options(
        self, output_format: str, quality: dict[str, Any]
    ) -> list[str]:
        """
        Get format-specific FFmpeg options.

        Args:
            output_format: Output format
            quality: Quality settings

        Returns:
            List of FFmpeg options
        """
        options = []

        if output_format == "mp3":
            options.extend(["-acodec", "libmp3lame"])
            if "bitrate" in quality:
                options.extend(["-b:a", quality["bitrate"]])

        elif output_format == "wav":
            options.extend(["-acodec", "pcm_s16le"])
            if "sample_rate" in quality:
                options.extend(["-ar", str(quality["sample_rate"])])

        elif output_format == "aac":
            options.extend(["-acodec", "aac"])
            if "bitrate" in quality:
                options.extend(["-b:a", quality["bitrate"]])

        elif output_format == "flac":
            options.extend(["-acodec", "flac"])

        elif output_format == "ogg":
            options.extend(["-acodec", "libvorbis"])
            if "quality" in quality:
                options.extend(["-q:a", quality["quality"]])

        elif output_format == "m4a":
            options.extend(["-acodec", "aac"])
            if "bitrate" in quality:
                options.extend(["-b:a", quality["bitrate"]])

        # Add sample rate if specified
        if "sample_rate" in quality and output_format != "wav":
            options.extend(["-ar", str(quality["sample_rate"])])

        return options

    def _execute_ffmpeg_with_progress(
        self, cmd: list[str], total_duration: float
    ) -> None:
        """
        Execute FFmpeg with progress monitoring.

        Args:
            cmd: FFmpeg command
            total_duration: Total video duration in seconds
        """
        # Decide whether to use progress monitoring
        use_progress = self.progress_callback is not None and total_duration > 0

        if use_progress:
            # Add progress output
            cmd_with_progress = cmd.copy()
            cmd_with_progress.extend(["-progress", "pipe:1"])

            process = subprocess.Popen(
                cmd_with_progress,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Monitor progress
            if process.stdout:
                for line in process.stdout:
                    if line.startswith("out_time_ms"):
                        # Extract current time in microseconds
                        time_us = int(line.split("=")[1].strip())
                        current_time = time_us / 1_000_000  # Convert to seconds

                        # Calculate percentage
                        percentage = min(100.0, (current_time / total_duration) * 100)

                        # Create progress
                        progress = AudioExtractionProgress(
                            status="extracting",
                            percentage=percentage,
                            current_time=current_time,
                            total_duration=total_duration,
                        )

                        self.progress_callback(progress)
        else:
            # No progress callback - run without progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )

        # Wait for completion
        process.wait()

        if process.returncode != 0:
            stderr = process.stderr.read() if process.stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg failed: {stderr}")
