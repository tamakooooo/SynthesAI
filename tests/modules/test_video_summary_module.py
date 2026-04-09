"""
Integration tests for VideoSummaryModule.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.llm.service import LLMService
from learning_assistant.modules.video_summary import VideoSummaryModule
from learning_assistant.modules.video_summary.downloader import VideoInfo


class TestVideoSummaryModuleInit:
    """Test VideoSummaryModule initialization."""

    def test_module_creation(self) -> None:
        """Test module creation."""
        module = VideoSummaryModule()

        assert module.name == "video_summary"
        assert module.config == {}
        assert module.event_bus is None
        assert module.downloader is None
        assert module.audio_extractor is None
        assert module.transcriber is None
        assert module.prompt_manager is None
        assert module.exporter is None
        assert module.llm_service is None

    def test_module_initialization(self) -> None:
        """Test module initialization."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "download_dir": "data/downloads",
            "audio_dir": "data/audio",
            "transcriber": "bcut",
            "word_timestamps": False,
            "export_template": "video_summary.md",
        }

        module.initialize(config, event_bus)

        assert module.config == config
        assert module.event_bus == event_bus
        assert module.downloader is not None
        assert module.audio_extractor is not None
        assert module.transcriber is not None
        assert module.prompt_manager is not None
        assert module.exporter is not None

    def test_module_initialization_with_cookie_file(self) -> None:
        """Test module initialization with cookie file."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "download_dir": "data/downloads",
            "audio_dir": "data/audio",
            "cookie_file": "data/cookies.txt",
        }

        module.initialize(config, event_bus)

        assert module.downloader is not None
        assert module.downloader.cookie_file is not None

    def test_set_llm_service(self) -> None:
        """Test setting LLM service."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)

        llm_service = Mock(spec=LLMService)
        module.set_llm_service(llm_service)

        assert module.llm_service == llm_service
        assert module.prompt_manager is not None
        assert module.prompt_manager.llm_service == llm_service

    def test_module_cleanup(self) -> None:
        """Test module cleanup."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)
        module.cleanup()

        # Cleanup should not raise exceptions
        assert True


class TestVideoSummaryModuleExecute:
    """Test VideoSummaryModule execute workflow."""

    def test_execute_missing_url(self) -> None:
        """Test execute with missing URL."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)

        with pytest.raises(ValueError, match="Video URL is required"):
            module.execute({})

    def test_execute_integration_workflow(self, tmp_path: Path) -> None:
        """Test complete integration workflow with mocks."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "download_dir": str(tmp_path / "downloads"),
            "audio_dir": str(tmp_path / "audio"),
        }
        module.initialize(config, event_bus)

        # Mock all components
        video_info = VideoInfo(
            title="Test Video",
            duration=120,
            uploader="Test Uploader",
            upload_date="20240101",
            description="Test Description",
            thumbnail="https://test.com/thumb.jpg",
            url="https://test.com/video",
            platform="youtube",
        )

        # Create actual files
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        # Setup all mocks
        module.downloader.extract_info = Mock(return_value=video_info)
        module.downloader.download = Mock(return_value=video_file)
        module.audio_extractor.extract_audio = Mock(return_value=tmp_path / "audio.mp3")
        module.audio_extractor.get_audio_info = Mock(
            return_value=Mock(
                duration=120.0,
                sample_rate=44100,
                channels=2,
            )
        )
        module.transcriber.transcribe = Mock(
            return_value=Mock(to_txt=Mock(return_value="Test transcript"))
        )
        module.prompt_manager.execute = Mock(
            return_value={
                "title": "Test Summary",
                "summary": "This is a test summary",
                "key_points": [],
                "topics": [],
            }
        )
        module.exporter.export = Mock(return_value=tmp_path / "output.md")

        # Set LLM service
        module.set_llm_service(Mock(spec=LLMService))

        # Execute workflow
        result = module.execute(
            {
                "url": "https://test.com/video",
                "language": "zh",
                "output_format": "markdown",
            }
        )

        # Verify result
        assert result["status"] == "success"
        assert "video_info" in result
        assert "summary" in result
        assert "output_paths" in result

    def test_execute_download_failure(self) -> None:
        """Test execute with download failure."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)

        module.downloader.extract_info = Mock(return_value=None)

        with pytest.raises(RuntimeError, match="Failed to extract video info"):
            module.execute({"url": "https://test.com/video"})

    def test_execute_transcription_failure(self, tmp_path: Path) -> None:
        """Test execute with transcription failure."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "download_dir": str(tmp_path / "downloads"),
            "audio_dir": str(tmp_path / "audio"),
        }
        module.initialize(config, event_bus)

        video_info = VideoInfo(
            title="Test Video",
            duration=120,
            uploader="Test Uploader",
            upload_date="20240101",
            description="Test Description",
            thumbnail="https://test.com/thumb.jpg",
            url="https://test.com/video",
            platform="youtube",
        )

        module.downloader.extract_info = Mock(return_value=video_info)
        module.downloader.download = Mock(return_value=tmp_path / "video.mp4")
        module.audio_extractor.extract_audio = Mock(return_value=tmp_path / "audio.mp3")
        module.audio_extractor.get_audio_info = Mock(
            return_value=Mock(
                duration=120.0,
                sample_rate=44100,
                channels=2,
            )
        )
        module.transcriber.transcribe = Mock(
            side_effect=RuntimeError("Transcription failed")
        )

        with pytest.raises(RuntimeError, match="Transcription failed"):
            module.execute({"url": "https://test.com/video"})


class TestVideoSummaryModulePrivateMethods:
    """Test VideoSummaryModule private methods."""

    def test_download_video_success(self, tmp_path: Path) -> None:
        """Test _download_video method."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "download_dir": str(tmp_path / "downloads"),
        }
        module.initialize(config, event_bus)

        video_info = VideoInfo(
            title="Test Video",
            duration=120,
            uploader="Test Uploader",
            upload_date="20240101",
            description="Test Description",
            thumbnail="https://test.com/thumb.jpg",
            url="https://test.com/video",
            platform="youtube",
        )

        module.downloader.extract_info = Mock(return_value=video_info)
        module.downloader.download = Mock(return_value=tmp_path / "downloads" / "video.mp4")

        result = module._download_video("https://test.com/video", tmp_path)

        assert result["title"] == "Test Video"
        assert result["duration"] == 120.0
        assert result["platform"] == "youtube"

    def test_extract_audio_success(self, tmp_path: Path) -> None:
        """Test _extract_audio method."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "audio_dir": str(tmp_path / "audio"),
        }
        module.initialize(config, event_bus)

        # Create mock video file
        video_path = tmp_path / "video.mp4"
        video_path.touch()

        module.audio_extractor.extract_audio = Mock(return_value=tmp_path / "audio.mp3")
        module.audio_extractor.get_audio_info = Mock(
            return_value=Mock(
                duration=120.0,
                sample_rate=44100,
                channels=2,
            )
        )

        result = module._extract_audio(video_path, tmp_path)

        assert "audio_path" in result
        assert result["duration"] == 120.0
        assert result["sample_rate"] == 44100

    def test_transcribe_audio_success(self, tmp_path: Path) -> None:
        """Test _transcribe_audio method."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)

        audio_path = tmp_path / "audio.mp3"
        audio_path.touch()

        mock_asr_data = Mock()
        mock_asr_data.to_txt = Mock(return_value="Test transcript")

        module.transcriber.transcribe = Mock(return_value=mock_asr_data)

        result = module._transcribe_audio(audio_path)

        assert result == "Test transcript"

    def test_generate_summary_success(self) -> None:
        """Test _generate_summary method."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)

        # Set LLM service
        module.set_llm_service(Mock(spec=LLMService))

        video_info = {
            "title": "Test Video",
            "duration": 120.0,
        }
        transcript = "Test transcript"

        module.prompt_manager.execute = Mock(
            return_value={
                "title": "Test Summary",
                "summary": "This is a test summary",
                "key_points": [],
                "topics": [],
            }
        )

        result = module._generate_summary(
            video_info=video_info,
            transcript=transcript,
            language="zh",
            focus_areas=["Python", "AI"],
        )

        assert result["title"] == "Test Summary"
        assert "summary" in result

    def test_export_output_markdown(self, tmp_path: Path) -> None:
        """Test _export_output method for Markdown."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "export_template": "video_summary.md",
        }
        module.initialize(config, event_bus)

        summary_data = {
            "title": "Test Summary",
            "summary": "This is a test summary",
            "key_points": [],
            "topics": [],
        }
        video_info = {
            "title": "Test Video Title",
        }

        module.exporter.export = Mock()

        result = module._export_output(
            summary_data=summary_data,
            output_format="markdown",
            video_info=video_info,
        )

        assert "markdown" in result

    def test_export_output_pdf(self, tmp_path: Path) -> None:
        """Test _export_output method for PDF."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)

        summary_data = {
            "title": "Test Summary",
            "summary": "This is a test summary",
        }
        video_info = {
            "title": "Test Video Title",
        }

        # Mock PDFExporter - use the correct import path
        with patch('learning_assistant.core.exporters.pdf.PDFExporter') as mock_pdf_exporter_class:
            mock_pdf_exporter = Mock()
            mock_pdf_exporter_class.return_value = mock_pdf_exporter

            result = module._export_output(
                summary_data=summary_data,
                output_format="pdf",
                video_info=video_info,
            )

            # PDF export should work with mocked exporter
            assert "pdf" in result

    def test_export_output_both_formats(self, tmp_path: Path) -> None:
        """Test _export_output method for both Markdown and PDF."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {}
        module.initialize(config, event_bus)

        summary_data = {
            "title": "Test Summary",
        }
        video_info = {
            "title": "Test Video Title",
        }

        module.exporter.export = Mock()

        # Mock PDFExporter with correct import path
        with patch('learning_assistant.core.exporters.pdf.PDFExporter') as mock_pdf_exporter_class:
            mock_pdf_exporter = Mock()
            mock_pdf_exporter_class.return_value = mock_pdf_exporter

            result = module._export_output(
                summary_data=summary_data,
                output_format="both",
                video_info=video_info,
            )

            assert "markdown" in result
            assert "pdf" in result


class TestVideoSummaryModuleErrorHandling:
    """Test VideoSummaryModule error handling."""

    def test_execute_without_llm_service(self, tmp_path: Path) -> None:
        """Test execute without LLM service configured."""
        module = VideoSummaryModule()
        event_bus = EventBus()

        config = {
            "download_dir": str(tmp_path / "downloads"),
            "audio_dir": str(tmp_path / "audio"),
        }
        module.initialize(config, event_bus)

        video_info = VideoInfo(
            title="Test Video",
            duration=120,
            uploader="Test Uploader",
            upload_date="20240101",
            description="Test Description",
            thumbnail="https://test.com/thumb.jpg",
            url="https://test.com/video",
            platform="youtube",
        )

        module.downloader.extract_info = Mock(return_value=video_info)
        module.downloader.download = Mock(return_value=tmp_path / "video.mp4")
        module.audio_extractor.extract_audio = Mock(return_value=tmp_path / "audio.mp3")
        module.audio_extractor.get_audio_info = Mock(return_value=Mock(duration=120.0))
        module.transcriber.transcribe = Mock(
            return_value=Mock(to_txt=Mock(return_value="Test transcript"))
        )

        # Should raise RuntimeError when trying to generate summary
        with pytest.raises(RuntimeError, match="LLM service not configured"):
            module.execute({"url": "https://test.com/video"})

    def test_downloader_not_initialized(self) -> None:
        """Test _download_video when downloader not initialized."""
        module = VideoSummaryModule()

        with pytest.raises(RuntimeError, match="Downloader not initialized"):
            module._download_video("https://test.com/video", Path("/tmp"))

    def test_audio_extractor_not_initialized(self, tmp_path: Path) -> None:
        """Test _extract_audio when extractor not initialized."""
        module = VideoSummaryModule()

        video_path = tmp_path / "video.mp4"
        video_path.touch()

        with pytest.raises(RuntimeError, match="Audio extractor not initialized"):
            module._extract_audio(video_path, tmp_path)

    def test_transcriber_not_initialized(self, tmp_path: Path) -> None:
        """Test _transcribe_audio when transcriber not initialized."""
        module = VideoSummaryModule()

        audio_path = tmp_path / "audio.mp3"
        audio_path.touch()

        with pytest.raises(RuntimeError, match="Transcriber not initialized"):
            module._transcribe_audio(audio_path)

    def test_prompt_manager_not_initialized(self) -> None:
        """Test _generate_summary when prompt manager not initialized."""
        module = VideoSummaryModule()

        with pytest.raises(RuntimeError, match="Prompt manager not initialized"):
            module._generate_summary(
                video_info={"title": "Test"},
                transcript="Test transcript",
                language="zh",
                focus_areas=[],
            )

    def test_exporter_not_initialized(self) -> None:
        """Test _export_output when exporter not initialized."""
        module = VideoSummaryModule()

        with pytest.raises(RuntimeError, match="Exporter not initialized"):
            module._export_output(
                summary_data={"title": "Test"},
                output_format="markdown",
                video_info={"title": "Test Video"},
            )


class TestVideoSummaryModuleMetadata:
    """Test VideoSummaryModule metadata."""

    def test_module_name(self) -> None:
        """Test module name property."""
        module = VideoSummaryModule()

        assert module.name == "video_summary"

    def test_get_metadata(self) -> None:
        """Test get_metadata method."""
        module = VideoSummaryModule()

        metadata = module.get_metadata()

        assert metadata["name"] == "video_summary"
        assert metadata["type"] == "module"