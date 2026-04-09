"""
Unit tests for VideoDownloader.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from learning_assistant.modules.video_summary.downloader import (
    DownloadProgress,
    VideoDownloader,
    VideoInfo,
)


class TestVideoInfo:
    """Test VideoInfo dataclass."""

    def test_create_video_info(self) -> None:
        """Test creating VideoInfo instance."""
        info = VideoInfo(
            title="Test Video",
            duration=600,
            uploader="Test User",
            upload_date="20240101",
            description="Test description",
            thumbnail="https://example.com/thumb.jpg",
            url="https://example.com/video",
            platform="youtube",
        )

        assert info.title == "Test Video"
        assert info.duration == 600
        assert info.uploader == "Test User"
        assert info.platform == "youtube"


class TestDownloadProgress:
    """Test DownloadProgress dataclass."""

    def test_create_progress(self) -> None:
        """Test creating DownloadProgress instance."""
        progress = DownloadProgress(
            status="downloading",
            downloaded_bytes=1024,
            total_bytes=2048,
            speed=512.0,
            eta=2.0,
            percentage=50.0,
        )

        assert progress.status == "downloading"
        assert progress.downloaded_bytes == 1024
        assert progress.total_bytes == 2048
        assert progress.speed == 512.0
        assert progress.eta == 2.0
        assert progress.percentage == 50.0


class TestVideoDownloader:
    """Test VideoDownloader class."""

    def test_init_default_dir(self) -> None:
        """Test initialization with default directory."""
        downloader = VideoDownloader()

        assert downloader.output_dir == Path("data/downloads")
        assert downloader.cookie_file is None
        assert downloader.progress_callback is None

    def test_init_custom_dir(self) -> None:
        """Test initialization with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = VideoDownloader(output_dir=Path(tmpdir))

            assert downloader.output_dir == Path(tmpdir)
            # Directory should be created
            assert Path(tmpdir).exists()

    def test_init_with_cookie_file(self) -> None:
        """Test initialization with cookie file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cookie_file = Path(tmpdir) / "cookies.txt"
            cookie_file.touch()

            downloader = VideoDownloader(cookie_file=cookie_file)

            assert downloader.cookie_file == cookie_file

    def test_init_with_progress_callback(self) -> None:
        """Test initialization with progress callback."""
        callback = Mock()
        downloader = VideoDownloader(progress_callback=callback)

        assert downloader.progress_callback == callback

    def test_detect_platform_bilibili(self) -> None:
        """Test detecting Bilibili platform."""
        downloader = VideoDownloader()

        # Test various Bilibili URLs
        urls = [
            "https://www.bilibili.com/video/BV1234567890",
            "https://b23.tv/abc123",
            "https://www.bilibili.com/video/av12345678",
        ]

        for url in urls:
            platform = downloader.detect_platform(url)
            assert platform == "bilibili"

    def test_detect_platform_youtube(self) -> None:
        """Test detecting YouTube platform."""
        downloader = VideoDownloader()

        urls = [
            "https://www.youtube.com/watch?v=abc123",
            "https://youtu.be/abc123",
        ]

        for url in urls:
            platform = downloader.detect_platform(url)
            assert platform == "youtube"

    def test_detect_platform_douyin(self) -> None:
        """Test detecting Douyin platform."""
        downloader = VideoDownloader()

        urls = [
            "https://www.douyin.com/video/123456789",
            "https://v.douyin.com/abc123/",
        ]

        for url in urls:
            platform = downloader.detect_platform(url)
            assert platform == "douyin"

    def test_detect_platform_unknown(self) -> None:
        """Test detecting unknown platform."""
        downloader = VideoDownloader()

        url = "https://example.com/video"
        platform = downloader.detect_platform(url)

        assert platform == "unknown"

    @patch("yt_dlp.YoutubeDL")
    def test_extract_info_success(self, mock_ydl_class: Mock) -> None:
        """Test extracting video info successfully."""
        # Mock YoutubeDL
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Mock extract_info
        mock_info = {
            "title": "Test Video",
            "duration": 600,
            "uploader": "Test User",
            "upload_date": "20240101",
            "description": "Test description",
            "thumbnail": "https://example.com/thumb.jpg",
        }
        mock_ydl.extract_info.return_value = mock_info

        downloader = VideoDownloader()
        info = downloader.extract_info("https://www.youtube.com/watch?v=test")

        assert info is not None
        assert info.title == "Test Video"
        assert info.duration == 600
        assert info.uploader == "Test User"
        assert info.platform == "youtube"

    @patch("yt_dlp.YoutubeDL")
    def test_extract_info_failure(self, mock_ydl_class: Mock) -> None:
        """Test extracting video info with failure."""
        # Mock YoutubeDL to raise exception
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")

        downloader = VideoDownloader()
        info = downloader.extract_info("https://www.youtube.com/watch?v=test")

        assert info is None

    @patch("yt_dlp.YoutubeDL")
    def test_download_success(self, mock_ydl_class: Mock) -> None:
        """Test downloading video successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock YoutubeDL
            mock_ydl = Mock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl

            # Mock extract_info
            mock_info = {
                "title": "Test Video",
                "ext": "mp4",
            }
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl.prepare_filename.return_value = str(
                Path(tmpdir) / "Test Video.mp4"
            )

            # Create the mock downloaded file
            downloaded_file = Path(tmpdir) / "Test Video.mp4"
            downloaded_file.touch()

            downloader = VideoDownloader(output_dir=Path(tmpdir))
            result = downloader.download("https://www.youtube.com/watch?v=test")

            assert result is not None
            assert result.name == "Test Video.mp4"

    @patch("yt_dlp.YoutubeDL")
    def test_download_failure(self, mock_ydl_class: Mock) -> None:
        """Test downloading video with failure."""
        # Mock YoutubeDL to raise exception
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")

        downloader = VideoDownloader()
        result = downloader.download("https://www.youtube.com/watch?v=test")

        assert result is None

    def test_progress_hook_downloading(self) -> None:
        """Test progress hook during downloading."""
        callback = Mock()
        downloader = VideoDownloader(progress_callback=callback)

        # Simulate progress update
        progress_dict = {
            "status": "downloading",
            "downloaded_bytes": 1024,
            "total_bytes": 2048,
            "speed": 512.0,
            "eta": 2.0,
        }

        downloader._progress_hook(progress_dict)

        # Verify callback was called
        assert callback.called
        call_args = callback.call_args[0][0]
        assert isinstance(call_args, DownloadProgress)
        assert call_args.status == "downloading"
        assert call_args.percentage == 50.0

    def test_progress_hook_finished(self) -> None:
        """Test progress hook when download finished."""
        callback = Mock()
        downloader = VideoDownloader(progress_callback=callback)

        # Simulate finished download
        progress_dict = {
            "status": "finished",
            "downloaded_bytes": 2048,
            "total_bytes": 2048,
        }

        downloader._progress_hook(progress_dict)

        # Verify callback was called
        assert callback.called
        call_args = callback.call_args[0][0]
        assert isinstance(call_args, DownloadProgress)
        assert call_args.status == "finished"
        assert call_args.percentage == 100.0

    def test_progress_hook_no_callback(self) -> None:
        """Test progress hook without callback."""
        downloader = VideoDownloader()

        # Should not raise error
        progress_dict = {
            "status": "downloading",
            "downloaded_bytes": 1024,
            "total_bytes": 2048,
        }

        downloader._progress_hook(progress_dict)  # Should not raise

    @patch("yt_dlp.YoutubeDL")
    def test_get_available_formats(self, mock_ydl_class: Mock) -> None:
        """Test getting available formats."""
        # Mock YoutubeDL
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Mock formats
        mock_info = {
            "formats": [
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "resolution": "1920x1080",
                    "fps": 30,
                    "vcodec": "h264",
                    "acodec": "none",
                    "filesize": 1024000,
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "resolution": "audio only",
                    "fps": None,
                    "vcodec": "none",
                    "acodec": "aac",
                    "filesize": 128000,
                },
            ]
        }
        mock_ydl.extract_info.return_value = mock_info

        downloader = VideoDownloader()
        formats = downloader.get_available_formats(
            "https://www.youtube.com/watch?v=test"
        )

        assert len(formats) == 2
        assert formats[0]["format_id"] == "137"
        assert formats[1]["format_id"] == "140"

    @patch("yt_dlp.YoutubeDL")
    def test_download_audio_only(self, mock_ydl_class: Mock) -> None:
        """Test downloading audio only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock YoutubeDL
            mock_ydl = Mock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl

            # Mock extract_info
            mock_info = {
                "title": "Test Audio",
                "ext": "mp3",
            }
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl.prepare_filename.return_value = str(
                Path(tmpdir) / "Test Audio.mp3"
            )

            # Create the mock downloaded file
            downloaded_file = Path(tmpdir) / "Test Audio.mp3"
            downloaded_file.touch()

            downloader = VideoDownloader(output_dir=Path(tmpdir))
            result = downloader.download_audio_only(
                "https://www.youtube.com/watch?v=test"
            )

            assert result is not None
            # Verify download was called with audio format
            call_args = mock_ydl.extract_info.call_args
            assert call_args[0][0] == "https://www.youtube.com/watch?v=test"


class TestVideoDownloaderIntegration:
    """Test VideoDownloader integration scenarios."""

    def test_platform_detection_with_real_urls(self) -> None:
        """Test platform detection with real URL patterns."""
        downloader = VideoDownloader()

        # Test Bilibili
        bilibili_urls = [
            "https://www.bilibili.com/video/BV1xx411c7mD",
            "https://b23.tv/BV1xx411c7mD",
        ]
        for url in bilibili_urls:
            assert downloader.detect_platform(url) == "bilibili"

        # Test YouTube
        youtube_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
        ]
        for url in youtube_urls:
            assert downloader.detect_platform(url) == "youtube"

        # Test Douyin
        douyin_urls = [
            "https://www.douyin.com/video/7123456789012345678",
            "https://v.douyin.com/abc123/",
        ]
        for url in douyin_urls:
            assert downloader.detect_platform(url) == "douyin"

    @patch("yt_dlp.YoutubeDL")
    def test_full_download_workflow(self, mock_ydl_class: Mock) -> None:
        """Test full download workflow with progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock YoutubeDL
            mock_ydl = Mock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl

            # Mock video info
            mock_info = {
                "title": "Test Workflow Video",
                "duration": 300,
                "uploader": "Test User",
                "upload_date": "20240101",
                "description": "Test workflow",
                "thumbnail": "https://example.com/thumb.jpg",
                "ext": "mp4",
            }
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl.prepare_filename.return_value = str(
                Path(tmpdir) / "Test Workflow Video.mp4"
            )

            # Create mock file
            downloaded_file = Path(tmpdir) / "Test Workflow Video.mp4"
            downloaded_file.touch()

            # Create downloader with progress callback
            progress_updates = []

            def progress_callback(progress: DownloadProgress) -> None:
                progress_updates.append(progress)

            downloader = VideoDownloader(
                output_dir=Path(tmpdir), progress_callback=progress_callback
            )

            # Extract info
            info = downloader.extract_info("https://www.youtube.com/watch?v=test")
            assert info is not None
            assert info.title == "Test Workflow Video"

            # Download
            result = downloader.download("https://www.youtube.com/watch?v=test")
            assert result is not None
            assert result.name == "Test Workflow Video.mp4"
