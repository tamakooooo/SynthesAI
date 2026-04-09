"""
Frame Extractor for Learning Assistant.

Extracts key frames from video at specified timestamps using FFmpeg.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class FrameInfo:
    """
    Extracted frame information.

    Attributes:
        timestamp: Timestamp in seconds
        frame_path: Path to extracted frame file
        chapter_title: Associated chapter title (optional)
    """

    timestamp: float  # seconds
    frame_path: Path
    chapter_title: str | None = None


class FrameExtractor:
    """
    Frame Extractor using FFmpeg.

    Supports:
    - Extract frames at specific timestamps
    - Batch extraction for multiple chapters
    - Timestamp format conversion (MM:SS, HH:MM:SS)
    - Relative path calculation for markdown

    Example:
        >>> extractor = FrameExtractor(output_dir=Path("data/frames"))
        >>> chapters = [
        ...     {"title": "Intro", "start_time": "00:00", "summary": "..."},
        ...     {"title": "Main", "start_time": "05:30", "summary": "..."}
        ... ]
        >>> updated = extractor.extract_frames_for_chapters(
        ...     video_path=Path("video.mp4"),
        ...     chapters=chapters,
        ...     video_title="My Video"
        ... )
        >>> # Each chapter now has screenshot_path field
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        output_format: str = "jpg",
        quality: int = 85,
    ) -> None:
        """
        Initialize FrameExtractor.

        Args:
            output_dir: Output directory for extracted frames (default: data/frames)
            output_format: Image format (jpg or png)
            quality: Image quality for JPEG (1-100)

        Raises:
            RuntimeError: If FFmpeg is not available
        """
        self.output_dir = output_dir or Path("data/frames")
        self.output_format = output_format
        self.quality = quality

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check FFmpeg availability
        if not self._check_ffmpeg():
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg to use frame extraction."
            )

        logger.info(
            f"FrameExtractor initialized: output_dir={self.output_dir}, "
            f"format={self.output_format}, quality={self.quality}"
        )

    def _check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is available in system.

        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.error("FFmpeg not found in system PATH")
            return False

    def timestamp_to_seconds(self, timestamp: str) -> float:
        """
        Convert timestamp string to seconds.

        Supports formats:
        - "MM:SS" or "M:SS" → seconds
        - "HH:MM:SS" → seconds
        - "SS" (number string) → seconds

        Args:
            timestamp: Timestamp string (e.g., "05:30", "1:15:30")

        Returns:
            Timestamp in seconds as float

        Example:
            >>> extractor.timestamp_to_seconds("05:30")
            330.0
            >>> extractor.timestamp_to_seconds("1:15:30")
            4530.0
        """
        # If already a number, return it
        try:
            return float(timestamp)
        except ValueError:
            pass

        # Parse HH:MM:SS or MM:SS format
        parts = timestamp.split(":")

        if len(parts) == 2:
            # MM:SS format
            minutes, seconds = parts
            try:
                return float(minutes) * 60 + float(seconds)
            except ValueError:
                logger.warning(f"Invalid timestamp format: {timestamp}")
                return 0.0
        elif len(parts) == 3:
            # HH:MM:SS format
            hours, minutes, seconds = parts
            try:
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            except ValueError:
                logger.warning(f"Invalid timestamp format: {timestamp}")
                return 0.0
        else:
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return 0.0

    def extract_frame(
        self,
        video_path: Path,
        timestamp: float,
        output_filename: str | None = None,
    ) -> Path | None:
        """
        Extract a single frame at specified timestamp.

        Uses FFmpeg -ss for fast seek (no full decode).

        Args:
            video_path: Video file path
            timestamp: Timestamp in seconds
            output_filename: Output filename (without extension)

        Returns:
            Extracted frame path or None if extraction failed

        Example:
            >>> extractor.extract_frame(
            ...     video_path=Path("video.mp4"),
            ...     timestamp=330.0,
            ...     output_filename="chapter_01"
            ... )
            Path("data/frames/chapter_01.jpg")
        """
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return None

        # Prepare output path
        if output_filename:
            output_path = self.output_dir / f"{output_filename}.{self.output_format}"
        else:
            output_path = (
                self.output_dir / f"frame_{timestamp:.0f}.{self.output_format}"
            )

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-ss",
            str(timestamp),  # Seek to timestamp (fast)
            "-i",
            str(video_path),  # Input video
            "-frames:v",
            "1",  # Extract only 1 frame
            "-q:v",
            str(self.quality),  # JPEG quality
            "-y",  # Overwrite output
            str(output_path),
        ]

        try:
            # Execute FFmpeg (suppress output)
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
            )

            if result.returncode == 0 and output_path.exists():
                logger.info(f"Frame extracted successfully: {output_path}")
                return output_path
            else:
                error_msg = result.stderr.decode("utf-8", errors="ignore")
                logger.error(f"Frame extraction failed: {error_msg}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Frame extraction timed out (30s)")
            return None
        except Exception as e:
            logger.error(f"Failed to extract frame: {e}")
            return None

    def extract_frames_for_chapters(
        self,
        video_path: Path,
        chapters: list[dict[str, Any]],
        video_title: str,
    ) -> list[dict[str, Any]]:
        """
        Extract frames for all chapters at their start_time.

        Creates video-specific subdirectory and extracts one frame per chapter.

        Args:
            video_path: Video file path
            chapters: List of chapter dictionaries (must have start_time field)
            video_title: Video title (for organizing frames)

        Returns:
            Updated chapters with screenshot_path field added

        Example:
            >>> chapters = [
            ...     {"title": "Intro", "start_time": "00:00", "summary": "..."},
            ...     {"title": "Main", "start_time": "05:30", "summary": "..."}
            ... ]
            >>> updated = extractor.extract_frames_for_chapters(
            ...     video_path=Path("video.mp4"),
            ...     chapters=chapters,
            ...     video_title="My Video"
            ... )
            >>> updated[0]["screenshot_path"]
            "My_Video/chapter_01.jpg"
        """
        if not video_path.exists():
            logger.warning(f"Video file not found: {video_path}")
            return chapters

        if not chapters:
            logger.warning("No chapters to extract frames for")
            return chapters

        # Create video-specific directory
        safe_title = self._sanitize_title(video_title)
        video_frame_dir = self.output_dir / safe_title
        video_frame_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Extracting frames for {len(chapters)} chapters " f"to {video_frame_dir}"
        )

        # Extract frame for each chapter
        updated_chapters = []
        successful_count = 0

        for i, chapter in enumerate(chapters):
            # Convert timestamp to seconds
            timestamp_str = chapter.get("start_time", "00:00")
            timestamp_sec = self.timestamp_to_seconds(timestamp_str)

            # Generate frame filename
            frame_filename = f"chapter_{i + 1:02d}"

            # Temporarily set output_dir to video-specific directory
            original_output_dir = self.output_dir
            self.output_dir = video_frame_dir

            # Extract frame
            extracted_path = self.extract_frame(
                video_path=video_path,
                timestamp=timestamp_sec,
                output_filename=frame_filename,
            )

            # Restore original output_dir
            self.output_dir = original_output_dir

            # Update chapter with screenshot path (relative)
            updated_chapter = chapter.copy()
            if extracted_path:
                # Calculate relative path from output directory
                relative_path = self._calculate_relative_path(
                    frame_path=extracted_path,
                    output_dir=Path("data/outputs"),
                )
                updated_chapter["screenshot_path"] = relative_path
                successful_count += 1
                logger.debug(f"Chapter {i + 1}: screenshot added at {relative_path}")
            else:
                updated_chapter["screenshot_path"] = None
                logger.warning(f"Chapter {i + 1}: failed to extract screenshot")

            updated_chapters.append(updated_chapter)

        logger.info(
            f"Frame extraction complete: {successful_count}/{len(chapters)} successful"
        )
        return updated_chapters

    def _sanitize_title(self, title: str) -> str:
        """
        Sanitize video title for directory name.

        Removes special characters and limits length.

        Args:
            title: Video title (may contain special chars)

        Returns:
            Safe directory name

        Example:
            >>> extractor._sanitize_title("吃一个花甲_等于吃上万根玻璃纤维")
            "吃一个花甲_等于吃上万根玻璃纤维"
            >>> extractor._sanitize_title("Video: Special @#$ Characters!")
            "Video_ Special ___ Characters!"
        """
        # Remove special characters (keep alphanumeric, space, hyphen, underscore)
        safe_chars = []
        for c in title:
            if c.isalnum() or c in (" ", "-", "_"):
                safe_chars.append(c)
            else:
                safe_chars.append("_")

        safe_title = "".join(safe_chars)
        # Limit length and strip spaces
        return safe_title[:50].strip()

    def _calculate_relative_path(
        self,
        frame_path: Path,
        output_dir: Path,
    ) -> str:
        """
        Calculate relative path from output directory to frame file.

        Args:
            frame_path: Absolute path to frame file (e.g., data/frames/Video/chapter_01.jpg)
            output_dir: Output directory where markdown is saved (e.g., data/outputs)

        Returns:
            Relative path string (e.g., "../frames/Video/chapter_01.jpg")

        Example:
            >>> frame_path = Path("data/frames/My_Video/chapter_01.jpg")
            >>> output_dir = Path("data/outputs")
            >>> extractor._calculate_relative_path(frame_path, output_dir)
            "../frames/My_Video/chapter_01.jpg"
        """
        # Both are under data/ directory
        # frame: data/frames/{title}/chapter_01.jpg
        # output: data/outputs/{title}_summary.md

        # Calculate relative path: ../frames/{title}/chapter_01.jpg
        try:
            # Get relative path from output_dir's parent (data/)
            relative = frame_path.relative_to(output_dir.parent)
            # Force forward slashes for cross-platform compatibility
            return str(relative).replace("\\", "/")
        except ValueError:
            # Fallback: use absolute path if relative calculation fails
            logger.warning(
                f"Cannot calculate relative path, using absolute: {frame_path}"
            )
            return str(frame_path).replace("\\", "/")
