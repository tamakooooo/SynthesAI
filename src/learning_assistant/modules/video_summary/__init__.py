"""
Video Summary Module for Learning Assistant.

This module provides complete video content summarization workflow.
"""

import asyncio
import concurrent.futures
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from learning_assistant.core.base_module import BaseModule
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.event_bus import Event, EventType
from learning_assistant.core.exporters import MarkdownExporter
from learning_assistant.core.llm.service import LLMService
from learning_assistant.core.publishing import PublishBlock, PublishPayload
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
        from learning_assistant.core.config_manager import ConfigManager

        config_manager = ConfigManager()
        config_manager.load_all()
        path_config = config_manager.get_path_config()

        # LLM service (must be initialized first for PromptManager)
        self.llm_service = config_manager.create_llm_service(
            provider=self.config.get("llm", {}).get("provider"),
            module_config=self.config,
        )

        # Video downloader
        # Auto-detect cookie file based on platform
        cookie_files_config = self.config.get("cookies", {})
        bilibili_cookie = cookie_files_config.get(
            "bilibili", path_config.config_cookies_bilibili
        )

        # Check if cookie file exists
        cookie_file_path = Path(bilibili_cookie) if bilibili_cookie else None
        if cookie_file_path and not cookie_file_path.exists():
            logger.warning(f"Cookie file not found: {cookie_file_path}")
            cookie_file_path = None

        self.downloader = VideoDownloader(
            output_dir=Path(self.config.get("download_dir", path_config.data_downloads)),
            cookie_file=cookie_file_path,
        )

        # Audio extractor
        self.audio_extractor = AudioExtractor(
            output_dir=Path(self.config.get("audio_dir", path_config.data_audio))
        )

        # Audio transcriber
        self.transcriber = AudioTranscriber(
            engine=self.config.get("transcriber", "bcut"),
            use_cache=True,
            need_word_time_stamp=self.config.get("word_timestamps", False),
        )

        # Prompt manager (requires llm_service)
        template_dirs = [Path(path_config.templates_prompts)]
        self.prompt_manager = PromptManager(
            template_dirs=template_dirs,
            llm_service=self.llm_service,
        )

        # Markdown exporter
        self.exporter = MarkdownExporter(
            template_dir=Path(path_config.templates_outputs),
            template_name=self.config.get("export_template", "video_summary.md"),
        )

        # Frame extractor (optional, configurable)
        frame_extraction_config = self.config.get("frame_extraction", {})
        if frame_extraction_config.get("enabled", True):  # Default enabled
            self.frame_extractor = FrameExtractor(
                output_dir=Path(
                    frame_extraction_config.get("output_dir", path_config.data_frames)
                ),
                output_format=frame_extraction_config.get("format", "jpg"),
                quality=frame_extraction_config.get("quality", 95),  # Higher default quality
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
        Execute video summary workflow (sync wrapper).

        Args:
            input_data: Input data containing:
                - url: Video URL
                - language: Output language (default: zh)
                - focus_areas: Focus areas for summary
                - output_format: Output format (markdown/pdf)

        Returns:
            Summary output data
        """
        # Run async process in event loop (handle both cases)
        try:
            asyncio.get_running_loop()
            # Already running loop - use thread pool to avoid conflict
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run, self.execute_async(input_data)
                )
                return future.result()
        except RuntimeError:
            # No running loop - create new one
            return asyncio.run(self.execute_async(input_data))

    async def execute_async(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute video summary workflow (async).

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
                logger.info(f"Transcription completed: {len(transcript_data)} characters")

                # Step 4: Generate summary
                logger.info("Step 4/5: Generating summary...")
                logger.info("Calling LLM API (this may take 30-60 seconds)...")
                summary_data = self._generate_summary(
                    video_info=video_info,
                    transcript=transcript_data,
                    language=language,
                    focus_areas=focus_areas,
                )
                logger.info("Summary generated successfully")

                # Step 4.5: Extract frames for chapters (if enabled)
                if self.frame_extractor and "chapters" in summary_data:
                    logger.info("Step 4.5/5: Extracting frames for chapters...")

                    # Check if video file has video stream
                    video_path = video_info["video_path"]
                    has_video_stream = self._check_video_stream(video_path)

                    if has_video_stream:
                        # Extract frames from video
                        summary_data["chapters"] = (
                            self.frame_extractor.extract_frames_for_chapters(
                                video_path=video_path,
                                chapters=summary_data["chapters"],
                                video_title=video_info["title"],
                            )
                        )
                    else:
                        # Use cover image for all chapters
                        logger.info("Video file has no video stream, using cover image")
                        # Pass both temp directory and original download directory
                        cover_path = self._find_cover_image(
                            video_path=video_path,
                            download_dir=self.downloader.output_dir if self.downloader else None,
                            video_title=video_info["title"],
                        )
                        if cover_path:
                            summary_data["chapters"] = self._use_cover_for_chapters(
                                chapters=summary_data["chapters"],
                                cover_path=cover_path,
                                video_title=video_info["title"],
                            )
                        else:
                            logger.warning("No cover image found, skipping screenshots")

                # Step 5: Export output
                logger.info("Step 5/5: Exporting output...")
                output_paths = self._export_output(
                    summary_data=summary_data,
                    output_format=output_format,
                    video_info=video_info,
                )

                result = {
                    "status": "success",
                    "video_info": video_info,
                    "summary": summary_data,
                    "output_paths": output_paths,
                }
                self._publish_completion_event(video_url, result)
                return result

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
            # Use shutil.move for cross-device compatibility
            import shutil
            shutil.move(str(extracted_path), str(audio_path))

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

        logger.info(f"Starting audio transcription: {audio_path}")
        logger.info("Uploading audio to ASR service (this may take 1-3 minutes)...")

        asr_data = self.transcriber.transcribe(audio_path)

        # Return full transcript as text
        transcript = asr_data.to_txt()
        logger.info(f"Transcription complete: {len(transcript)} characters, {len(asr_data.segments)} segments")

        return transcript

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
        from learning_assistant.core.config_manager import ConfigManager

        if not self.exporter:
            raise RuntimeError("Exporter not initialized")

        # Get path config
        config_manager = ConfigManager()
        path_config = config_manager.get_path_config()

        output_dir = Path(path_config.data_outputs_video)
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

    def _check_video_stream(self, video_path: Path) -> bool:
        """Check if video file has a video stream."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=codec_type",
                    "-of", "csv=p=0",
                    str(video_path)
                ],
                capture_output=True,
                timeout=10,
            )
            # If there's a video stream, output will contain "video"
            return bool(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Failed to check video stream: {e}")
            return False

    def _publish_completion_event(
        self,
        video_url: str,
        result: dict[str, Any],
    ) -> None:
        """Publish a normalized completion event for external adapters."""
        if not self.event_bus:
            return

        payload = self._build_publish_payload(video_url=video_url, result=result)
        self.event_bus.publish(
            Event(
                event_type=EventType.VIDEO_SUMMARIZED,
                source=self.name,
                data={
                    "module": self.name,
                    "source_url": video_url,
                    "result": result,
                    "publish_payload": payload.model_dump(mode="json"),
                },
            )
        )

    def _build_publish_payload(
        self,
        video_url: str,
        result: dict[str, Any],
    ) -> PublishPayload:
        """Map module output to a normalized publishing payload with full content."""
        video_info = result.get("video_info", {})
        summary_data = result.get("summary", {})
        summary_text = (
            summary_data.get("summary")
            or summary_data.get("content")
            or summary_data.get("overview")
            or ""
        )
        key_points = summary_data.get("key_points", [])
        knowledge_points = summary_data.get("knowledge", [])
        chapters = summary_data.get("chapters", [])
        qa_items = summary_data.get("qa_items", [])
        topics = summary_data.get("topics", [])

        blocks: list[PublishBlock] = []

        # 概述
        if summary_text:
            blocks.append(PublishBlock(type="heading", text="📋 概述", level=2))
            blocks.append(PublishBlock(type="paragraph", text=summary_text))

        def _extract_text(item: Any) -> str:
            """Extract text from dict or return string directly."""
            if isinstance(item, dict):
                return item.get("point") or item.get("knowledge") or item.get("text") or str(item)
            return str(item)

        # 关键要点
        if key_points:
            blocks.append(PublishBlock(type="heading", text="🔑 关键要点", level=2))
            blocks.append(PublishBlock(type="bullet_list", items=[_extract_text(item) for item in key_points]))

        # 知识点
        if knowledge_points:
            blocks.append(PublishBlock(type="heading", text="💡 知识点", level=2))
            blocks.append(PublishBlock(type="bullet_list", items=[_extract_text(item) for item in knowledge_points]))

        # 章节内容
        if chapters:
            blocks.append(PublishBlock(type="heading", text="📖 章节内容", level=2))
            for chapter in chapters:
                chapter_title = chapter.get("title", "")
                chapter_summary = chapter.get("summary", "")
                start_time = chapter.get("start_time", "")
                screenshot_path = chapter.get("screenshot_path")

                # Add screenshot image if available
                if screenshot_path:
                    # Convert relative path to absolute path
                    # screenshot_path is like "../frames/VideoTitle/chapter_01.jpg"
                    from pathlib import Path as PathLib
                    abs_path = PathLib("data") / screenshot_path.replace("../", "")
                    if abs_path.exists():
                        blocks.append(PublishBlock(type="image", image_path=str(abs_path)))

                if chapter_title:
                    blocks.append(PublishBlock(type="heading", text=f"{start_time} - {chapter_title}" if start_time else chapter_title, level=3))
                if chapter_summary:
                    blocks.append(PublishBlock(type="paragraph", text=chapter_summary))

        # 常见问题
        if qa_items:
            blocks.append(PublishBlock(type="heading", text="❓ 常见问题", level=2))
            for qa in qa_items:
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                if question:
                    blocks.append(PublishBlock(type="paragraph", text=f"Q: {question}"))
                if answer:
                    blocks.append(PublishBlock(type="paragraph", text=f"A: {answer}"))

        # 主题标签
        if topics:
            blocks.append(PublishBlock(type="heading", text="🏷️ 主题标签", level=2))
            blocks.append(PublishBlock(type="paragraph", text="、".join([str(t) for t in topics])))

        # 如果没有任何内容，添加一个基本信息块
        if not blocks:
            blocks.append(PublishBlock(type="paragraph", text=f"视频标题：{video_info.get('title', 'Unknown')}"))

        # Extract mindmap structure from LLM output
        mindmap_structure = summary_data.get("mindmap_structure")

        return PublishPayload(
            module=self.name,
            title=str(video_info.get("title", "Untitled Video Summary")),
            summary=summary_text or None,
            source_url=video_url,
            blocks=blocks,
            tags=[str(t) for t in topics] if topics else [str(video_info.get("platform", "video"))],
            metadata={
                "uploader": video_info.get("uploader", ""),
                "duration": video_info.get("duration", 0),
                "platform": video_info.get("platform", ""),
                "output_paths": {
                    key: str(value) for key, value in result.get("output_paths", {}).items()
                },
            },
            mindmap_structure=mindmap_structure,
        )

    def _find_cover_image(
        self, video_path: Path, download_dir: Path | None = None, video_title: str | None = None
    ) -> Path | None:
        """Find cover image for audio file.

        Searches in:
        1. Same directory as video_path (temp directory)
        2. Download directory (using video_title for matching)
        """
        logger.debug(f"Searching for cover image: video_title={video_title}")
        logger.debug(f"Video path: {video_path}")
        logger.debug(f"Download dir: {download_dir}")

        # First check in video directory (temp)
        video_dir = video_path.parent
        video_stem = video_path.stem

        for ext in [".jpg", ".png", ".jpeg"]:
            cover_path = video_dir / f"{video_stem}_cover{ext}"
            logger.debug(f"Checking temp dir: {cover_path}")
            if cover_path.exists():
                logger.info(f"Found cover image in temp dir: {cover_path}")
                return cover_path

        # Check in download directory using video_title
        if download_dir and download_dir.exists() and video_title:
            logger.debug(f"Searching in download dir: {download_dir}")

            # List all cover files for debugging
            jpg_files = list(download_dir.glob("*_cover.jpg"))
            logger.debug(f"Found {len(jpg_files)} cover files in download dir")

            # Try exact title match
            for ext in [".jpg", ".png", ".jpeg"]:
                cover_path = download_dir / f"{video_title}_cover{ext}"
                logger.debug(f"Checking download dir with title: {cover_path}")
                if cover_path.exists():
                    logger.info(f"Found cover image in download dir: {cover_path}")
                    return cover_path

            # Try matching by partial title (in case of special chars)
            for cover_file in download_dir.glob("*_cover.jpg"):
                # Check if video title is contained in the cover filename
                if video_title and video_title in str(cover_file):
                    logger.info(f"Found cover image by partial match: {cover_file}")
                    return cover_file

            # Check for generic cover files in download directory
            for cover_name in ["cover.jpg", "cover.png", "folder.jpg", "poster.jpg"]:
                cover_path = download_dir / cover_name
                if cover_path.exists():
                    logger.info(f"Found generic cover image: {cover_path}")
                    return cover_path
        else:
            if not download_dir:
                logger.warning("Download directory not available")
            elif not video_title:
                logger.warning("Video title not available for cover search")

        return None

    def _use_cover_for_chapters(
        self,
        chapters: list[dict[str, Any]],
        cover_path: Path,
        video_title: str,
    ) -> list[dict[str, Any]]:
        """Use cover image for all chapters."""
        import shutil
        from learning_assistant.core.config_manager import ConfigManager

        # Create video-specific directory
        safe_title = self.frame_extractor._sanitize_title(video_title)
        video_frame_dir = self.frame_extractor.output_dir / safe_title
        video_frame_dir.mkdir(parents=True, exist_ok=True)

        # Copy cover image to frame directory
        cover_dest = video_frame_dir / "cover.jpg"
        shutil.copy(cover_path, cover_dest)

        logger.info(f"Copied cover image to {cover_dest}")

        # Get output path from config
        config_manager = ConfigManager()
        path_config = config_manager.get_path_config()

        # Calculate relative path
        relative_path = self.frame_extractor._calculate_relative_path(
            frame_path=cover_dest,
            output_dir=Path(path_config.data_outputs_video).parent,
        )

        # Add same cover path to all chapters
        updated_chapters = []
        for chapter in chapters:
            updated_chapter = chapter.copy()
            updated_chapter["screenshot_path"] = relative_path
            updated_chapters.append(updated_chapter)

        logger.info(f"Applied cover image to {len(chapters)} chapters")
        return updated_chapters

    def cleanup(self) -> None:
        """Cleanup module resources."""
        logger.info("VideoSummaryModule cleanup")
