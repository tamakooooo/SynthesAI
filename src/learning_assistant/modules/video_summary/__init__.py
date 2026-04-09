"""
Video Summary Module for Learning Assistant.

This module provides complete video content summarization workflow.
"""

import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from learning_assistant.core.base_module import BaseModule
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.exporters import MarkdownExporter
from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.prompt_manager import PromptManager
from learning_assistant.modules.video_summary.audio_extractor import AudioExtractor
from learning_assistant.modules.video_summary.downloader import VideoDownloader
from learning_assistant.modules.video_summary.frame_extractor import FrameExtractor
from learning_assistant.modules.video_summary.transcriber import AudioTranscriber


class VideoSummaryModule(BaseModule):
    """
    Video Summary Module.

    Provides complete workflow:
    1. Download video
    2. Extract audio
    3. Transcribe audio
    4. Generate summary with LLM
    5. Export to Markdown/PDF
    """

    def __init__(self) -> None:
        """Initialize video summary module."""
        self.config: dict[str, Any] = {}
        self.event_bus: EventBus | None = None

        # Components
        self.downloader: VideoDownloader | None = None
        self.audio_extractor: AudioExtractor | None = None
        self.transcriber: AudioTranscriber | None = None
        self.prompt_manager: PromptManager | None = None
        self.exporter: MarkdownExporter | None = None
        self.llm_service: LLMService | None = None
        self.frame_extractor: FrameExtractor | None = None

        logger.info("VideoSummaryModule created")

    @property
    def name(self) -> str:
        """Module name."""
        return "video_summary"

    def initialize(self, config: dict[str, Any], event_bus: EventBus) -> None:
        """
        Initialize video summary module.

        Args:
            config: Module configuration
            event_bus: Event bus instance
        """
        self.config = config
        self.event_bus = event_bus

        # Initialize components
        self._init_components()

        logger.info("VideoSummaryModule initialized")

    def _init_components(self) -> None:
        """Initialize all components."""
        import os

        # LLM service (must be initialized first for PromptManager)
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "openai")

        # Get API key with priority: env var > config file
        api_key = None
        api_key_env = f"{provider.upper()}_API_KEY"

        # 1. Try environment variable first
        api_key = os.environ.get(api_key_env)

        # 2. Try config file
        if not api_key and "api_key" in llm_config:
            api_key = llm_config["api_key"]

        if not api_key:
            raise ValueError(
                f"API key not found. Set {api_key_env} environment variable "
                f"or add 'api_key' to video_summary.llm config"
            )

        # Build LLM kwargs with base_url from config
        llm_kwargs = {}
        if "base_url" in llm_config:
            llm_kwargs["base_url"] = llm_config["base_url"]
        if "timeout" in llm_config:
            llm_kwargs["timeout"] = llm_config["timeout"]

        self.llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            model=llm_config.get("model", "kimi-k2.5"),
            max_retries=llm_config.get("max_retries", 3),
            **llm_kwargs,
        )

        # Video downloader
        # Auto-detect cookie file based on platform
        cookie_files_config = self.config.get("cookies", {})
        bilibili_cookie = cookie_files_config.get(
            "bilibili", "config/cookies/bilibili_cookies.txt"
        )

        # Check if cookie file exists
        cookie_file_path = Path(bilibili_cookie) if bilibili_cookie else None
        if cookie_file_path and not cookie_file_path.exists():
            logger.warning(f"Cookie file not found: {cookie_file_path}")
            cookie_file_path = None

        self.downloader = VideoDownloader(
            output_dir=Path(self.config.get("download_dir", "data/downloads")),
            cookie_file=cookie_file_path,
        )

        # Audio extractor
        self.audio_extractor = AudioExtractor(
            output_dir=Path(self.config.get("audio_dir", "data/audio"))
        )

        # Audio transcriber
        self.transcriber = AudioTranscriber(
            engine=self.config.get("transcriber", "bcut"),
            use_cache=True,
            need_word_time_stamp=self.config.get("word_timestamps", False),
        )

        # Prompt manager (requires llm_service)
        template_dirs = [Path("templates/prompts")]
        self.prompt_manager = PromptManager(
            template_dirs=template_dirs,
            llm_service=self.llm_service,
        )

        # Markdown exporter
        self.exporter = MarkdownExporter(
            template_dir=Path("templates/outputs"),
            template_name=self.config.get("export_template", "video_summary.md"),
        )

        # Frame extractor (optional, configurable)
        frame_extraction_config = self.config.get("frame_extraction", {})
        if frame_extraction_config.get("enabled", True):  # Default enabled
            self.frame_extractor = FrameExtractor(
                output_dir=Path(
                    frame_extraction_config.get("output_dir", "data/frames")
                ),
                output_format=frame_extraction_config.get("format", "jpg"),
                quality=frame_extraction_config.get("quality", 85),
            )
            logger.debug("Frame extractor initialized")
        else:
            self.frame_extractor = None
            logger.info("Frame extraction disabled by config")

        logger.debug("All components initialized")

    def set_llm_service(self, llm_service: LLMService) -> None:
        """
        Set LLM service.

        Args:
            llm_service: LLM service instance
        """
        self.llm_service = llm_service
        if self.prompt_manager:
            self.prompt_manager.llm_service = llm_service

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute video summary workflow.

        Args:
            input_data: Input data containing:
                - url: Video URL
                - language: Output language (default: zh)
                - focus_areas: Focus areas for summary
                - output_format: Output format (markdown/pdf)

        Returns:
            Summary output data
        """
        video_url = input_data.get("url")
        if not video_url:
            raise ValueError("Video URL is required")

        language = input_data.get("language", "zh")
        focus_areas = input_data.get("focus_areas", [])
        output_format = input_data.get("output_format", "markdown")

        logger.info(f"Processing video: {video_url}")

        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as tmpdir:
                work_dir = Path(tmpdir)

                # Step 1: Download video
                logger.info("Step 1/5: Downloading video...")
                video_info = self._download_video(video_url, work_dir)

                # Step 2: Extract audio
                logger.info("Step 2/5: Extracting audio...")
                audio_info = self._extract_audio(video_info["video_path"], work_dir)

                # Step 3: Transcribe audio
                logger.info("Step 3/5: Transcribing audio...")
                transcript_data = self._transcribe_audio(audio_info["audio_path"])

                # Step 4: Generate summary
                logger.info("Step 4/5: Generating summary...")
                summary_data = self._generate_summary(
                    video_info=video_info,
                    transcript=transcript_data,
                    language=language,
                    focus_areas=focus_areas,
                )

                # Step 4.5: Extract frames for chapters (if enabled)
                if self.frame_extractor and "chapters" in summary_data:
                    logger.info("Step 4.5/5: Extracting frames for chapters...")
                    summary_data["chapters"] = (
                        self.frame_extractor.extract_frames_for_chapters(
                            video_path=video_info["video_path"],
                            chapters=summary_data["chapters"],
                            video_title=video_info["title"],
                        )
                    )

                # Step 5: Export output
                logger.info("Step 5/5: Exporting output...")
                output_paths = self._export_output(
                    summary_data=summary_data,
                    output_format=output_format,
                    video_info=video_info,
                )

                return {
                    "status": "success",
                    "video_info": video_info,
                    "summary": summary_data,
                    "output_paths": output_paths,
                }

        except Exception as e:
            logger.error(f"Video summary failed: {e}")
            raise

    def _download_video(self, url: str, work_dir: Path) -> dict[str, Any]:
        """Download video."""
        if not self.downloader:
            raise RuntimeError("Downloader not initialized")

        # Extract video info first
        video_info = self.downloader.extract_info(url)
        if not video_info:
            raise RuntimeError("Failed to extract video info")

        # Download video
        video_path = self.downloader.download(
            url=url,
            output_filename="video",
        )

        if not video_path:
            raise RuntimeError("Video download failed")

        # Move to expected location if needed
        expected_path = work_dir / "video.mp4"
        if video_path != expected_path:
            # Copy to work directory
            import shutil

            shutil.copy(video_path, expected_path)
            video_path = expected_path

        return {
            "video_path": video_path,
            "title": video_info.title,
            "duration": video_info.duration,
            "uploader": video_info.uploader,
            "description": video_info.description,
            "platform": video_info.platform,
        }

    def _extract_audio(self, video_path: Path, work_dir: Path) -> dict[str, Any]:
        """Extract audio from video."""
        if not self.audio_extractor:
            raise RuntimeError("Audio extractor not initialized")

        audio_path = work_dir / "audio.mp3"

        def progress_callback(progress: float, status: str) -> None:
            logger.debug(f"Audio extraction: {progress:.1f}% - {status}")

        # Extract audio
        extracted_path = self.audio_extractor.extract_audio(
            video_path=video_path,
            output_filename="audio",
            output_format="mp3",
        )

        if not extracted_path:
            raise RuntimeError("Audio extraction failed")

        # Move to expected location
        if extracted_path != audio_path:
            extracted_path.rename(audio_path)

        # Get audio info
        audio_info = self.audio_extractor.get_audio_info(audio_path)

        if not audio_info:
            # Fallback if info extraction fails
            return {
                "audio_path": audio_path,
                "duration": 0.0,
                "sample_rate": 44100,
                "channels": 2,
            }

        return {
            "audio_path": audio_path,
            "duration": audio_info.duration,
            "sample_rate": audio_info.sample_rate,
            "channels": audio_info.channels,
        }

    def _transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio to text."""
        if not self.transcriber:
            raise RuntimeError("Transcriber not initialized")

        asr_data = self.transcriber.transcribe(audio_path)

        # Return full transcript as text
        return asr_data.to_txt()

    def _generate_summary(
        self,
        video_info: dict[str, Any],
        transcript: str,
        language: str,
        focus_areas: list[str],
    ) -> dict[str, Any]:
        """Generate summary using LLM."""
        if not self.prompt_manager:
            raise RuntimeError("Prompt manager not initialized")

        if not self.llm_service:
            raise RuntimeError("LLM service not configured")

        # Execute prompt template
        summary_data = self.prompt_manager.execute(
            template_name="video_summary",
            variables={
                "video_title": video_info["title"],
                "transcript": transcript,
                "language": language,
                "focus_areas": focus_areas,
            },
            include_examples=True,
            validate_output=True,
        )

        return summary_data

    def _export_output(
        self,
        summary_data: dict[str, Any],
        output_format: str,
        video_info: dict[str, Any],
    ) -> dict[str, Path]:
        """Export summary to output files."""
        if not self.exporter:
            raise RuntimeError("Exporter not initialized")

        output_dir = Path("data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename from video title
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_"
            for c in video_info["title"]
        )
        output_filename = f"{safe_title[:50]}_summary"

        output_paths: dict[str, Path] = {}

        # Export Markdown
        if output_format in ("markdown", "both"):
            md_path = output_dir / f"{output_filename}.md"
            self.exporter.export(summary_data, md_path)
            output_paths["markdown"] = md_path

        # Export PDF (optional)
        if output_format in ("pdf", "both"):
            try:
                from learning_assistant.core.exporters import PDFExporter

                pdf_exporter = PDFExporter()
                pdf_path = output_dir / f"{output_filename}.pdf"
                pdf_exporter.export(summary_data, pdf_path)
                output_paths["pdf"] = pdf_path
            except Exception as e:
                logger.warning(f"PDF export failed: {e}")

        return output_paths

    def cleanup(self) -> None:
        """Cleanup module resources."""
        logger.info("VideoSummaryModule cleanup")
