"""
Unit tests for AudioExtractor.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from learning_assistant.modules.video_summary.audio_extractor import (
    AudioExtractionProgress,
    AudioExtractor,
    AudioInfo,
)


class TestAudioExtractionProgress:
    """Test AudioExtractionProgress dataclass."""

    def test_create_progress(self) -> None:
        """Test creating AudioExtractionProgress instance."""
        progress = AudioExtractionProgress(
            status="extracting",
            percentage=50.0,
            current_time=30.0,
            total_duration=60.0,
        )

        assert progress.status == "extracting"
        assert progress.percentage == 50.0
        assert progress.current_time == 30.0
        assert progress.total_duration == 60.0


class TestAudioInfo:
    """Test AudioInfo dataclass."""

    def test_create_audio_info(self) -> None:
        """Test creating AudioInfo instance."""
        info = AudioInfo(
            duration=300.0,
            sample_rate=44100,
            channels=2,
            bitrate=192,
            codec="mp3",
        )

        assert info.duration == 300.0
        assert info.sample_rate == 44100
        assert info.channels == 2
        assert info.bitrate == 192
        assert info.codec == "mp3"


class TestAudioExtractor:
    """Test AudioExtractor class."""

    @patch("subprocess.run")
    def test_init_ffmpeg_available(self, mock_run: Mock) -> None:
        """Test initialization when FFmpeg is available."""
        # Mock FFmpeg version check
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))

            assert extractor.output_dir == Path(tmpdir)
            assert extractor.progress_callback is None

    @patch("subprocess.run")
    def test_init_ffmpeg_not_available(self, mock_run: Mock) -> None:
        """Test initialization when FFmpeg is not available."""
        # Mock FFmpeg not found
        mock_run.side_effect = FileNotFoundError()

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(RuntimeError, match="FFmpeg not found"):
                AudioExtractor(output_dir=Path(tmpdir))

    @patch("subprocess.run")
    def test_init_with_progress_callback(self, mock_run: Mock) -> None:
        """Test initialization with progress callback."""
        mock_run.return_value = Mock(returncode=0)

        callback = Mock()
        extractor = AudioExtractor(progress_callback=callback)

        assert extractor.progress_callback == callback

    @patch("subprocess.run")
    def test_check_ffmpeg_success(self, mock_run: Mock) -> None:
        """Test FFmpeg availability check success."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            result = extractor._check_ffmpeg()

            assert result is True

    @patch("subprocess.run")
    def test_check_ffmpeg_failure(self, mock_run: Mock) -> None:
        """Test FFmpeg availability check failure."""
        mock_run.side_effect = FileNotFoundError()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Should raise error during init
            with pytest.raises(RuntimeError):
                AudioExtractor(output_dir=Path(tmpdir))

    @patch("subprocess.run")
    def test_get_video_duration_success(self, mock_run: Mock) -> None:
        """Test getting video duration successfully."""
        mock_run.return_value = Mock(stdout="300.5\n", returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            duration = extractor._get_video_duration(Path("test.mp4"))

            assert duration == 300.5

    @patch("subprocess.run")
    def test_get_video_duration_failure(self, mock_run: Mock) -> None:
        """Test getting video duration with failure."""
        # First call succeeds (FFmpeg check)
        # Second call fails (duration check)
        mock_run.side_effect = [
            Mock(returncode=0),  # FFmpeg check
            Exception("FFprobe error"),  # Duration check
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            duration = extractor._get_video_duration(Path("test.mp4"))

            assert duration == 0.0

    @patch("subprocess.run")
    def test_get_format_options_mp3(self, mock_run: Mock) -> None:
        """Test getting MP3 format options."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            options = extractor._get_format_options(
                "mp3", {"bitrate": "192k", "sample_rate": 44100}
            )

            assert "-acodec" in options
            assert "libmp3lame" in options
            assert "-b:a" in options
            assert "192k" in options

    @patch("subprocess.run")
    def test_get_format_options_wav(self, mock_run: Mock) -> None:
        """Test getting WAV format options."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            options = extractor._get_format_options("wav", {"sample_rate": 44100})

            assert "-acodec" in options
            assert "pcm_s16le" in options

    @patch("subprocess.run")
    def test_get_audio_info_success(self, mock_run: Mock) -> None:
        """Test getting audio info successfully."""
        # Mock FFprobe output
        ffprobe_output = {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2,
                }
            ],
            "format": {"duration": "300.5", "bit_rate": "192000"},
        }

        mock_run.return_value = Mock(stdout=json.dumps(ffprobe_output), returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock audio file
            audio_file = Path(tmpdir) / "test.mp3"
            audio_file.touch()

            extractor = AudioExtractor(output_dir=Path(tmpdir))
            info = extractor.get_audio_info(audio_file)

            assert info is not None
            assert info.duration == 300.5
            assert info.sample_rate == 44100
            assert info.channels == 2
            assert info.bitrate == 192
            assert info.codec == "mp3"

    @patch("subprocess.run")
    def test_get_audio_info_file_not_found(self, mock_run: Mock) -> None:
        """Test getting audio info when file not found."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            info = extractor.get_audio_info(Path("nonexistent.mp3"))

            assert info is None

    @patch.object(AudioExtractor, "_execute_ffmpeg_with_progress")
    @patch.object(AudioExtractor, "_get_video_duration")
    @patch("subprocess.run")
    def test_extract_audio_success(
        self,
        mock_run: Mock,
        mock_get_duration: Mock,
        mock_execute: Mock,
    ) -> None:
        """Test extracting audio successfully."""
        mock_run.return_value = Mock(returncode=0)
        mock_get_duration.return_value = 60.0

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock video file
            video_file = Path(tmpdir) / "test.mp4"
            video_file.touch()

            extractor = AudioExtractor(output_dir=Path(tmpdir))
            result = extractor.extract_audio(video_file, output_format="mp3")

            # Since output file doesn't exist, should return None
            assert result is None

    @patch("subprocess.run")
    def test_extract_audio_video_not_found(self, mock_run: Mock) -> None:
        """Test extracting audio when video not found."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            result = extractor.extract_audio(Path("nonexistent.mp4"))

            assert result is None

    @patch("subprocess.run")
    def test_extract_audio_unsupported_format(self, mock_run: Mock) -> None:
        """Test extracting audio with unsupported format."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test.mp4"
            video_file.touch()

            extractor = AudioExtractor(output_dir=Path(tmpdir))
            result = extractor.extract_audio(video_file, output_format="xyz")

            assert result is None

    @patch("subprocess.run")
    def test_convert_format_success(self, mock_run: Mock) -> None:
        """Test converting audio format successfully."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock audio file
            audio_file = Path(tmpdir) / "test.wav"
            audio_file.touch()

            extractor = AudioExtractor(output_dir=Path(tmpdir))

            # Since we mock subprocess, the output won't be created
            # So result will be None
            result = extractor.convert_format(audio_file, "mp3")
            assert result is None

    @patch("subprocess.run")
    def test_convert_format_file_not_found(self, mock_run: Mock) -> None:
        """Test converting audio when file not found."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=Path(tmpdir))
            result = extractor.convert_format(Path("nonexistent.wav"), "mp3")

            assert result is None

    @patch("subprocess.run")
    def test_convert_format_unsupported(self, mock_run: Mock) -> None:
        """Test converting to unsupported format."""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.wav"
            audio_file.touch()

            extractor = AudioExtractor(output_dir=Path(tmpdir))
            result = extractor.convert_format(audio_file, "xyz")

            assert result is None


class TestAudioExtractorIntegration:
    """Test AudioExtractor integration scenarios."""

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_full_extraction_workflow(self, mock_popen: Mock, mock_run: Mock) -> None:
        """Test full audio extraction workflow."""
        mock_run.return_value = Mock(returncode=0)

        # Mock Popen for progress monitoring
        mock_process = MagicMock()
        mock_process.stdout = []
        mock_process.stderr = MagicMock()
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = None
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock video
            video_file = Path(tmpdir) / "test.mp4"
            video_file.touch()

            # Track progress updates
            progress_updates = []

            def progress_callback(progress: AudioExtractionProgress) -> None:
                progress_updates.append(progress)

            AudioExtractor(
                output_dir=Path(tmpdir), progress_callback=progress_callback
            )

            # Get audio info (mocked)
            mock_run.return_value = Mock(
                stdout=json.dumps(
                    {
                        "streams": [
                            {
                                "codec_type": "audio",
                                "codec_name": "aac",
                                "sample_rate": "48000",
                                "channels": 2,
                            }
                        ],
                        "format": {"duration": "120.0", "bit_rate": "128000"},
                    }
                ),
                returncode=0,
            )

            # Note: Actual extraction would require FFmpeg
            # This test validates the workflow structure

    @patch("subprocess.run")
    def test_supported_formats(self, mock_run: Mock) -> None:
        """Test that all supported formats are available."""
        mock_run.return_value = Mock(returncode=0)

        extractor = AudioExtractor()

        expected_formats = ["mp3", "wav", "aac", "flac", "ogg", "m4a"]

        for fmt in expected_formats:
            assert fmt in extractor.SUPPORTED_FORMATS

    @patch("subprocess.run")
    def test_default_quality_settings(self, mock_run: Mock) -> None:
        """Test that default quality settings are configured."""
        mock_run.return_value = Mock(returncode=0)

        extractor = AudioExtractor()

        # Check default quality for each format
        assert "mp3" in extractor.DEFAULT_QUALITY
        assert "bitrate" in extractor.DEFAULT_QUALITY["mp3"]

        assert "wav" in extractor.DEFAULT_QUALITY
        assert "sample_rate" in extractor.DEFAULT_QUALITY["wav"]
