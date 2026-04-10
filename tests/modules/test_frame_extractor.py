"""
Unit tests for FrameExtractor component.
"""

import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from learning_assistant.modules.video_summary.frame_extractor import (
    FrameExtractor,
    FrameInfo,
)


class TestFrameExtractorInit:
    """Test FrameExtractor initialization."""

    def test_init_default_params(self) -> None:
        """Test initialization with default parameters."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            assert extractor.output_dir == Path("data/frames")
            assert extractor.output_format == "jpg"
            assert extractor.quality == 85

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(
                output_dir=Path("custom/frames"),
                output_format="png",
                quality=90,
            )

            assert extractor.output_dir == Path("custom/frames")
            assert extractor.output_format == "png"
            assert extractor.quality == 90

    def test_init_ffmpeg_not_available(self) -> None:
        """Test initialization fails when FFmpeg not available."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=False):
            with pytest.raises(RuntimeError, match="FFmpeg not found"):
                FrameExtractor()

    def test_output_dir_creation(self) -> None:
        """Test output directory is created."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(output_dir=Path("test_frames"))

            # Directory should be created
            assert extractor.output_dir.exists()
            # Cleanup
            if extractor.output_dir.exists():
                shutil.rmtree(extractor.output_dir)


class TestTimestampConversion:
    """Test timestamp_to_seconds method."""

    def test_mm_ss_format(self) -> None:
        """Test MM:SS format conversion."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            assert extractor.timestamp_to_seconds("05:30") == 330.0
            assert extractor.timestamp_to_seconds("1:15") == 75.0
            assert extractor.timestamp_to_seconds("00:00") == 0.0

    def test_hh_mm_ss_format(self) -> None:
        """Test HH:MM:SS format conversion."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            assert extractor.timestamp_to_seconds("1:15:30") == 4530.0
            assert extractor.timestamp_to_seconds("2:30:45") == 9045.0

    def test_numeric_string(self) -> None:
        """Test numeric string conversion."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            assert extractor.timestamp_to_seconds("330") == 330.0
            assert extractor.timestamp_to_seconds("0") == 0.0

    def test_invalid_format(self) -> None:
        """Test invalid timestamp format."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            # Invalid format should return 0.0 and log warning
            assert extractor.timestamp_to_seconds("invalid") == 0.0
            assert extractor.timestamp_to_seconds("12:34:56:78") == 0.0


class TestFrameExtraction:
    """Test extract_frame method."""

    @patch('subprocess.run')
    def test_extract_frame_success(self, mock_run: Mock) -> None:
        """Test successful frame extraction."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(output_dir=Path("test_frames"))

            # Mock successful FFmpeg execution
            mock_run.return_value = Mock(returncode=0, stderr=b"")
            mock_run.return_value.stdout = b""

            # Create mock video file
            video_path = Path("test_video.mp4")
            video_path.touch()

            # Mock Path.exists() to return True for output file
            output_file = extractor.output_dir / "chapter_01.jpg"
            with patch.object(Path, 'exists', return_value=True):
                # Extract frame
                result = extractor.extract_frame(
                    video_path=video_path,
                    timestamp=330.0,
                    output_filename="chapter_01",
                )

                # Verify FFmpeg command called correctly
                assert mock_run.called
                call_args = mock_run.call_args[0][0]
                assert "ffmpeg" in call_args
                assert "-ss" in call_args
                assert "330.0" in call_args  # Timestamp is converted to string with float
                assert "-frames:v" in call_args
                assert "1" in call_args

                # Verify output path
                assert result == output_file

            # Cleanup
            video_path.unlink()
            if extractor.output_dir.exists():
                shutil.rmtree(extractor.output_dir)

    @patch('subprocess.run')
    def test_extract_frame_failure(self, mock_run: Mock) -> None:
        """Test frame extraction failure."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(output_dir=Path("test_frames"))

            # Mock failed FFmpeg execution
            mock_run.return_value = Mock(
                returncode=1, stderr=b"Error: Invalid video"
            )

            # Create mock video file
            video_path = Path("test_video.mp4")
            video_path.touch()

            # Extract frame
            result = extractor.extract_frame(
                video_path=video_path,
                timestamp=330.0,
                output_filename="chapter_01",
            )

            # Verify result is None
            assert result is None

            # Cleanup
            video_path.unlink()
            if extractor.output_dir.exists():
                shutil.rmtree(extractor.output_dir)

    def test_extract_frame_video_not_found(self) -> None:
        """Test frame extraction when video file not found."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(output_dir=Path("test_frames"))

            # Non-existent video path
            result = extractor.extract_frame(
                video_path=Path("nonexistent.mp4"),
                timestamp=330.0,
                output_filename="chapter_01",
            )

            # Verify result is None
            assert result is None

            # Cleanup
            extractor.output_dir.rmdir()


class TestChapterFrameExtraction:
    """Test extract_frames_for_chapters method."""

    @patch.object(FrameExtractor, 'extract_frame')
    def test_extract_frames_for_all_chapters(self, mock_extract: Mock) -> None:
        """Test extracting frames for multiple chapters."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(output_dir=Path("test_frames"))

            # Mock successful frame extraction
            mock_extract.return_value = Path("test_frames/Video/chapter_01.jpg")

            # Create mock video file
            video_path = Path("test_video.mp4")
            video_path.touch()

            # Chapters data
            chapters = [
                {
                    "title": "Introduction",
                    "start_time": "00:00",
                    "summary": "Intro summary",
                },
                {
                    "title": "Main Content",
                    "start_time": "05:30",
                    "summary": "Main summary",
                },
                {
                    "title": "Conclusion",
                    "start_time": "10:15",
                    "summary": "Conclusion summary",
                },
            ]

            # Extract frames
            updated = extractor.extract_frames_for_chapters(
                video_path=video_path,
                chapters=chapters,
                video_title="Test Video",
            )

            # Verify extract_frame called for each chapter
            assert mock_extract.call_count == 3

            # Verify first chapter uses timestamp 0.0 (cover-like frame)
            first_call_args = mock_extract.call_args_list[0]
            assert first_call_args[1]["timestamp"] == 0.0

            # Verify screenshot_path added to chapters
            assert len(updated) == 3
            for chapter in updated:
                assert "screenshot_path" in chapter

            # Cleanup
            video_path.unlink()
            if extractor.output_dir.exists():
                shutil.rmtree(extractor.output_dir)

    def test_extract_frames_video_not_found(self) -> None:
        """Test chapter frame extraction when video not found."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(output_dir=Path("test_frames"))

            chapters = [
                {"title": "Chapter 1", "start_time": "00:00", "summary": "..."}
            ]

            # Video not found, should return chapters unchanged
            updated = extractor.extract_frames_for_chapters(
                video_path=Path("nonexistent.mp4"),
                chapters=chapters,
                video_title="Test",
            )

            assert updated == chapters

            # Cleanup
            extractor.output_dir.rmdir()

    def test_extract_frames_empty_chapters(self) -> None:
        """Test chapter frame extraction with empty chapters list."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor(output_dir=Path("test_frames"))

            # Empty chapters, should return empty list
            updated = extractor.extract_frames_for_chapters(
                video_path=Path("video.mp4"),
                chapters=[],
                video_title="Test",
            )

            assert updated == []

            # Cleanup
            extractor.output_dir.rmdir()


class TestTitleSanitization:
    """Test _sanitize_title method."""

    def test_sanitize_normal_title(self) -> None:
        """Test sanitizing normal title."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            result = extractor._sanitize_title("Normal Video Title")
            assert result == "Normal Video Title"

    def test_sanitize_special_characters(self) -> None:
        """Test sanitizing title with special characters."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            result = extractor._sanitize_title("Video: Special @#$ Characters!")
            # Special chars should be replaced with underscore
            assert "@" not in result
            assert "#" not in result
            assert "$" not in result

    def test_sanitize_long_title(self) -> None:
        """Test sanitizing very long title."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            long_title = "A" * 100
            result = extractor._sanitize_title(long_title)
            # Should be limited to 50 chars
            assert len(result) == 50

    def test_sanitize_chinese_title(self) -> None:
        """Test sanitizing Chinese title."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            result = extractor._sanitize_title("吃一个花甲_等于吃上万根玻璃纤维")
            # Chinese characters should be preserved
            assert "吃" in result
            assert "花甲" in result


class TestRelativePathCalculation:
    """Test _calculate_relative_path method."""

    def test_relative_path_calculation(self) -> None:
        """Test calculating relative path from output to frames."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            frame_path = Path("data/frames/My_Video/chapter_01.jpg")
            output_dir = Path("data/outputs")

            result = extractor._calculate_relative_path(frame_path, output_dir)

            # Should be ../frames/My_Video/chapter_01.jpg
            assert result == "../frames/My_Video/chapter_01.jpg"

    def test_relative_path_with_backslash(self) -> None:
        """Test calculating relative path with Windows backslash."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            # Windows path with backslash
            frame_path = Path("data\\frames\\My_Video\\chapter_01.jpg")
            output_dir = Path("data\\outputs")

            result = extractor._calculate_relative_path(frame_path, output_dir)

            # Should be normalized to forward slash
            assert "\\" not in result
            assert "/" in result

    def test_relative_path_fallback(self) -> None:
        """Test fallback when relative path calculation fails."""
        with patch.object(FrameExtractor, '_check_ffmpeg', return_value=True):
            extractor = FrameExtractor()

            # Completely different paths (cannot calculate relative)
            frame_path = Path("C:/temp/frames/chapter_01.jpg")
            output_dir = Path("D:/outputs")

            result = extractor._calculate_relative_path(frame_path, output_dir)

            # Should fallback to absolute path
            assert "chapter_01.jpg" in result


class TestFrameInfo:
    """Test FrameInfo dataclass."""

    def test_frame_info_creation(self) -> None:
        """Test creating FrameInfo instance."""
        info = FrameInfo(
            timestamp=330.0,
            frame_path=Path("frames/chapter_01.jpg"),
            chapter_title="Introduction",
        )

        assert info.timestamp == 330.0
        assert info.frame_path == Path("frames/chapter_01.jpg")
        assert info.chapter_title == "Introduction"

    def test_frame_info_without_chapter_title(self) -> None:
        """Test creating FrameInfo without chapter title."""
        info = FrameInfo(
            timestamp=330.0,
            frame_path=Path("frames/frame_330.jpg"),
        )

        assert info.timestamp == 330.0
        assert info.frame_path == Path("frames/frame_330.jpg")
        assert info.chapter_title is None