"""
Agent API - 标准化接口供各种 Agent 框架使用.

这是 Learning Assistant 的核心接口类，提供：
- 视频总结功能
- 技能列表查询
- 历史记录查询
- 学习统计信息

支持异步和同步调用，适合各种 Agent 框架集成。

使用示例：
    # 方式 1: 直接调用（推荐）
    from learning_assistant.api import AgentAPI

    api = AgentAPI()
    result = await api.summarize_video(url="https://...")

    # 方式 2: 使用便捷函数
    from learning_assistant.api import summarize_video

    result = await summarize_video(url="https://...")
"""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Any, AsyncGenerator

from loguru import logger

from learning_assistant import PluginManager
from learning_assistant.core.history_manager import HistoryManager
from learning_assistant.core.event_bus import EventBus
from learning_assistant.api.schemas import (
    VideoSummaryResult,
    SkillInfo,
    HistoryRecord,
    LearningStatistics,
    LinkSummaryResult,
    VocabularyResult,
)
from learning_assistant.api.exceptions import (
    SkillNotFoundError,
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
)


class AgentAPI:
    """
    Learning Assistant Agent API.

    提供统一的接口供 Agent 框架调用，封装了底层的模块管理和历史记录管理。

    Attributes:
        plugin_manager: 插件管理器
        history_manager: 历史记录管理器

    Example:
        >>> api = AgentAPI()
        >>> result = await api.summarize_video(url="https://...")
        >>> print(result.title)
        'Python 编程基础教程'
    """

    def __init__(self, config_path: Path | None = None):
        """
        初始化 Agent API.

        Args:
            config_path: 配置目录路径（可选）。如果不提供，优先读取环境变量。
        """
        logger.info("Initializing AgentAPI")
        config_dir = config_path or Path(os.environ.get("SYNTHESAI_CONFIG_DIR", "config"))

        # 初始化配置管理器
        from learning_assistant.core.config_manager import ConfigManager

        self.config_manager = ConfigManager(config_dir=config_dir)
        self.config_manager.load_all()

        # 初始化事件总线
        from learning_assistant.core.event_bus import EventBus

        self.event_bus = EventBus()

        # 初始化插件管理器
        plugin_dirs = [
            config_dir.parent / "src" / "learning_assistant" / "modules",
            config_dir.parent / "src" / "learning_assistant" / "adapters",
            Path("plugins"),
        ]
        self.plugin_manager = PluginManager(plugin_dirs=plugin_dirs)

        # 发现并加载所有插件
        discovered = self.plugin_manager.discover_plugins()
        for plugin_metadata in discovered:
            if plugin_metadata.enabled:
                self.plugin_manager.load_plugin(plugin_metadata.name)

        # 初始化适配器并订阅事件
        self._initialize_adapters()

        # 初始化历史记录管理器
        self.history_manager = HistoryManager()

        logger.success("AgentAPI initialized successfully")

    def _initialize_adapters(self) -> None:
        """Initialize adapters and subscribe to events."""
        adapters_config = self.config_manager.adapters_model
        if not adapters_config:
            logger.warning("No adapters configuration found")
            return

        # Initialize Feishu adapter if enabled
        feishu_adapter_config = adapters_config.feishu
        if feishu_adapter_config and feishu_adapter_config.enabled:
            try:
                from learning_assistant.adapters.feishu.adapter import FeishuKnowledgeBaseAdapter

                adapter = FeishuKnowledgeBaseAdapter()
                # Build adapter config: pass the nested 'config' dict directly
                # also include 'enabled' and subscriptions from event_bus if available
                adapter_config_dict = {
                    "enabled": feishu_adapter_config.enabled,
                    "config": feishu_adapter_config.config,  # This is the inner config dict
                }
                # Add subscriptions from event_bus configuration
                event_bus_config = adapters_config.event_bus
                if event_bus_config and event_bus_config.subscriptions:
                    feishu_subs = event_bus_config.subscriptions.get("feishu", [])
                    if feishu_subs:
                        adapter_config_dict["subscriptions"] = feishu_subs

                adapter.initialize(adapter_config_dict, self.event_bus)
                # Store adapter reference for manual publishing
                self._feishu_adapter = adapter
                logger.info(f"Feishu adapter initialized and subscribed to events, config={feishu_adapter_config.config}")
            except Exception as e:
                logger.warning(f"Failed to initialize Feishu adapter: {e}")
        else:
            self._feishu_adapter = None

    @classmethod
    def create_with_api_key(
        cls,
        provider: str,
        api_key: str,
        model: str | None = None,
        config_path: Path | None = None,
    ) -> AgentAPI:
        """
        Quick creation of AgentAPI with API key, no config file needed.

        Useful for Agents that want to use Learning Assistant without
        managing configuration files.

        Args:
            provider: LLM provider name (openai/anthropic/deepseek)
            api_key: API key for the provider
            model: Model name (optional, uses provider default)
            config_path: Optional config path for other settings

        Returns:
            AgentAPI instance configured with the provided API key

        Example:
            >>> # Quick start without config file
            >>> api = AgentAPI.create_with_api_key(
            ...     provider="openai",
            ...     api_key="sk-...",
            ...     model="gpt-4"
            ... )
            >>> result = await api.summarize_video(url="https://...")
        """
        # Set environment variable for the provider
        env_key = f"{provider.upper()}_API_KEY"
        original_value = os.environ.get(env_key)
        os.environ[env_key] = api_key

        try:
            # Create instance
            instance = cls(config_path=config_path)

            # Override LLM config if model specified
            if model:
                provider_config = instance.config_manager.settings_model.llm.providers.get(provider)
                if provider_config:
                    if hasattr(provider_config, 'model'):
                        provider_config.model = model
                    elif isinstance(provider_config, dict):
                        provider_config['model'] = model

            return instance
        except Exception as e:
            # Restore original environment value on failure
            if original_value:
                os.environ[env_key] = original_value
            elif env_key in os.environ:
                del os.environ[env_key]
            raise

    async def summarize_video(
        self,
        url: str,
        format: str = "markdown",
        language: str = "zh",
        output_dir: str | None = None,
        **kwargs: Any,
    ) -> VideoSummaryResult:
        """
        总结视频内容.

        执行完整的视频处理流程：
        1. 下载视频
        2. 提取音频
        3. 语音转录
        4. LLM 总结
        5. 导出文件

        Args:
            url: 视频URL（支持 B站/YouTube/抖音）
            format: 输出格式（markdown/pdf），默认为 markdown
            language: 总结语言（zh/en），默认为 zh
            output_dir: 输出目录（可选），默认为 ./outputs
            **kwargs: 其他参数（cookie_file, word_timestamps 等）

        Returns:
            VideoSummaryResult 对象，包含总结、字幕、文件路径等

        Raises:
            VideoNotFoundError: 视频不存在
            VideoDownloadError: 下载失败
            TranscriptionError: 转录失败
            LLMAPIError: LLM API 错误

        Example:
            >>> api = AgentAPI()
            >>> result = await api.summarize_video(
            ...     url="https://www.bilibili.com/video/BV...",
            ...     format="pdf",
            ...     language="en"
            ... )
            >>> print(result.title)
            >>> print(result.summary["content"])
        """
        logger.info(f"Summarizing video: {url}")

        try:
            # 初始化模块
            from learning_assistant.modules.video_summary import VideoSummaryModule

            video_module = VideoSummaryModule()
            video_config = self.config_manager.modules_model.video_summary.config.copy()

            # Merge global LLM settings with module config
            if "llm" not in video_config:
                video_config["llm"] = {}

            # Get global LLM provider settings (contains API key)
            provider = video_config["llm"].get("provider", "openai")
            global_llm_settings = self.config_manager.settings_model.llm.providers.get(provider)

            # Convert Pydantic model to dict if needed
            if global_llm_settings and hasattr(global_llm_settings, 'model_dump'):
                global_llm_settings_dict = global_llm_settings.model_dump()
            elif global_llm_settings and hasattr(global_llm_settings, 'dict'):
                global_llm_settings_dict = global_llm_settings.dict()
            else:
                global_llm_settings_dict = global_llm_settings or {}

            # Merge: module config can override global settings
            video_config["llm"] = {
                **global_llm_settings_dict,  # Global settings (has api_key)
                **video_config["llm"],  # Module-specific overrides
            }

            # 覆盖配置
            if format:
                video_config["output"] = video_config.get("output", {})
                video_config["output"]["format"] = format
            if output_dir:
                video_config["output"] = video_config.get("output", {})
                video_config["output"]["directory"] = output_dir

            video_module.initialize(video_config, self.event_bus)

            # 执行视频总结
            # 准备输入数据
            input_data = {
                "url": url,
                "format": format,
                "language": language,
                **kwargs,
            }
            if output_dir:
                input_data["output_dir"] = output_dir

            result = video_module.execute(input_data=input_data)

            logger.success(f"Video summarization completed: {url}")

            # 转为结构化输出
            return VideoSummaryResult(
                status="success",
                url=url,
                title=result.get("video_info", {}).get("title", "Unknown"),
                summary=result.get("summary", {}),
                transcript=result.get("transcript", ""),
                files={
                    "summary_path": result.get("summary_path"),
                    "subtitle_path": result.get("subtitle_path"),
                },
                feishu_url=result.get("feishu_url"),
                metadata=result.get("video_info", {}),
                timestamp=datetime.now().isoformat(),
            )

        except VideoNotFoundError:
            logger.error(f"Video not found: {url}")
            raise
        except VideoDownloadError as e:
            logger.error(f"Video download failed: {e}")
            raise
        except TranscriptionError as e:
            logger.error(f"Transcription failed: {e}")
            raise
        except LLMAPIError as e:
            logger.error(f"LLM API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during video summarization: {e}")
            raise

    async def process_link(
        self,
        url: str,
        provider: str = "openai",
        model: str = "gpt-4",
        output_dir: str | None = None,
        generate_quiz: bool = True,
        **kwargs: Any,
    ) -> LinkSummaryResult:
        """
        处理网页链接，生成知识卡片.

        执行完整的链接处理流程：
        1. 抓取网页内容
        2. 解析正文
        3. LLM 生成知识卡片
        4. 导出文件

        Args:
            url: 网页URL
            provider: LLM 提供者（openai/anthropic/deepseek）
            model: LLM 模型
            output_dir: 输出目录（可选）
            generate_quiz: 是否生成测验题
            **kwargs: 其他选项

        Returns:
            LinkSummaryResult 对象，包含完整的知识卡片信息

        Raises:
            ValueError: URL 无效
            RuntimeError: 处理失败

        Example:
            >>> api = AgentAPI()
            >>> result = await api.process_link(
            ...     url="https://example.com/article",
            ...     provider="openai",
            ...     model="gpt-4"
            ... )
            >>> print(result.title)
            >>> print(result.summary)
        """
        logger.info(f"Processing link: {url}")

        try:
            # 获取 link_learning 模块
            from learning_assistant.modules.link_learning import LinkLearningModule
            from learning_assistant.core.event_bus import EventBus

            # 初始化模块
            module = LinkLearningModule()
            config = {
                "llm": {
                    "provider": provider,
                    "model": model,
                },
                "features": {
                    "generate_quiz": generate_quiz,
                },
            }
            if output_dir:
                config["output"] = {"directory": output_dir}

            event_bus = EventBus()
            module.initialize(config, event_bus)

            # 设置 LLM 服务
            from learning_assistant.core.llm.service import LLMService
            import os

            api_key = os.environ.get(f"{provider.upper()}_API_KEY")
            if not api_key:
                raise ValueError(f"API key not found for provider: {provider}")

            module.llm_service = LLMService(
                provider=provider,
                api_key=api_key,
                model=model,
            )

            # 处理 URL
            knowledge_card = await module.process(url)

            # 构建结果
            return LinkSummaryResult(
                status="success",
                url=knowledge_card.url,
                title=knowledge_card.title,
                source=knowledge_card.source,
                summary=knowledge_card.summary,
                key_points=knowledge_card.key_points,
                tags=knowledge_card.tags,
                word_count=knowledge_card.word_count,
                reading_time=knowledge_card.reading_time,
                difficulty=knowledge_card.difficulty,
                qa_pairs=[
                    {
                        "question": qa.question,
                        "answer": qa.answer,
                        "difficulty": qa.difficulty,
                    }
                    for qa in knowledge_card.qa_pairs
                ],
                quiz=[
                    {
                        "type": q.type,
                        "question": q.question,
                        "options": q.options,
                        "correct": q.correct,
                        "explanation": q.explanation,
                    }
                    for q in knowledge_card.quiz
                ],
                files={},  # 由调用者填充
                timestamp=datetime.now().isoformat(),
            )

        except ValueError as e:
            logger.error(f"Invalid URL: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during link processing: {e}")
            raise

    async def extract_vocabulary(
        self,
        content: str | None = None,
        url: str | None = None,
        word_count: int = 10,
        difficulty: str = "intermediate",
        generate_story: bool = True,
        **kwargs: Any,
    ) -> VocabularyResult:
        """
        提取词汇并生成单词卡.

        执行完整的词汇提取流程：
        1. 从文本或URL获取内容
        2. LLM提取重要单词
        3. 生成单词卡（音标、释义、例句等）
        4. 可选生成上下文短文
        5. 导出文件（Markdown + Visual Card）

        Args:
            content: 文本内容（可选，如果提供url）
            url: 网页链接（可选，如果提供content）
            word_count: 提取单词数量（1-50）
            difficulty: 目标难度（beginner/intermediate/advanced）
            generate_story: 是否生成上下文短文
            **kwargs: 其他选项

        Returns:
            VocabularyResult 对象，包含完整的单词卡信息

        Raises:
            ValueError: 内容和url都为空，或参数无效
            RuntimeError: 处理失败

        Example:
            >>> # 从文本提取
            >>> api = AgentAPI()
            >>> result = await api.extract_vocabulary(
            ...     content="Machine learning is transforming...",
            ...     word_count=10,
            ...     difficulty="intermediate"
            ... )
            >>> print(f"Extracted {len(result.vocabulary_cards)} words")

            >>> # 从URL提取
            >>> result = await api.extract_vocabulary(
            ...     url="https://example.com/article",
            ...     word_count=15,
            ...     generate_card=True
            ... )
            >>> print(f"Visual card: {result.files['png_path']}")
        """
        logger.info(f"Extracting vocabulary: {word_count} words")

        if not content and not url:
            raise ValueError("Either content or url must be provided")

        try:
            from learning_assistant.modules.vocabulary import VocabularyLearningModule

            # 初始化模块
            module = VocabularyLearningModule()
            config = {
                "extraction": {
                    "word_count": word_count,
                },
                "story": {
                    "enabled": generate_story,
                },
                "content_fetcher": {
                    "enabled": True,  # Enable URL support
                },
            }

            # Merge with kwargs
            if "llm" in kwargs:
                config["llm"] = kwargs["llm"]

            event_bus = EventBus()
            module.initialize(config, event_bus)

            # 处理内容
            result = await module.process(
                content=content,
                url=url,
                word_count=word_count,
                difficulty=difficulty,
                generate_story=generate_story,
            )

            # 构建结果
            source = url if url else (content[:200] if content else "")
            return VocabularyResult(
                status="success",
                content=source,
                word_count=len(result.vocabulary_cards),
                difficulty=difficulty,
                vocabulary_cards=[card.to_dict() for card in result.vocabulary_cards],
                context_story=(
                    result.context_story.to_dict() if result.context_story else None
                ),
                statistics=result.statistics,
                files={},  # 由调用者填充
                timestamp=datetime.now().isoformat(),
            )

        except ValueError as e:
            logger.error(f"Invalid content: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during vocabulary extraction: {e}")
            raise

    def list_skills(self) -> list[SkillInfo]:
        """
        列出所有可用技能.

        返回适合 agent 消费的技能信息，包括：
        - 发现到的插件
        - 当前配置下是否启用
        - 当前进程中是否已加载
        - 推荐动作列表

        Returns:
            SkillInfo 列表

        Example:
            >>> api = AgentAPI()
            >>> skills = api.list_skills()
            >>> for skill in skills:
            ...     print(f"{skill.name}: {skill.description}")
        """
        logger.debug("Listing available skills")

        discovered_plugins = self.plugin_manager.plugins
        loaded_plugins = self.plugin_manager.loaded_plugins

        actions_by_plugin = {
            "video_summary": ["submit_video_task", "get_video_task_status", "get_video_task_result"],
            "link_learning": ["process_link"],
            "vocabulary": ["extract_vocabulary"],
            "feishu": ["verify_feishu", "publish_to_feishu", "publish_test_document"],
        }

        skills = [
            SkillInfo(
                name=plugin_metadata.name,
                description=plugin_metadata.description,
                version=plugin_metadata.version,
                status=self._resolve_skill_status(plugin_metadata.name, plugin_metadata.type),
                type=plugin_metadata.type,
                enabled=self._resolve_skill_enabled(plugin_metadata.name, plugin_metadata.type),
                loaded=plugin_metadata.name in loaded_plugins,
                priority=self._resolve_skill_priority(plugin_metadata.name),
                actions=actions_by_plugin.get(plugin_metadata.name, []),
            )
            for plugin_metadata in discovered_plugins.values()
        ]

        logger.debug(f"Found {len(skills)} skills")
        return skills

    def _resolve_skill_enabled(self, plugin_name: str, plugin_type: str) -> bool:
        """Resolve plugin enabled flag from current merged runtime configuration."""
        try:
            plugin_config = self.config_manager.get_plugin_config(plugin_name)
            return bool(plugin_config.get("enabled", True))
        except Exception:
            logger.debug(f"Falling back to discovered metadata for plugin enabled state: {plugin_name}")
            metadata = self.plugin_manager.plugins.get(plugin_name)
            return bool(metadata.enabled) if metadata else False

    def _resolve_skill_priority(self, plugin_name: str) -> int | None:
        """Resolve plugin priority from current merged runtime configuration."""
        try:
            plugin_config = self.config_manager.get_plugin_config(plugin_name)
            priority = plugin_config.get("priority")
            return priority if isinstance(priority, int) else None
        except Exception:
            metadata = self.plugin_manager.plugins.get(plugin_name)
            return metadata.priority if metadata else None

    def _resolve_skill_status(self, plugin_name: str, plugin_type: str) -> str:
        """Resolve runtime-oriented skill status."""
        enabled = self._resolve_skill_enabled(plugin_name, plugin_type)
        loaded = plugin_name in self.plugin_manager.loaded_plugins
        if not enabled:
            return "disabled"
        if loaded:
            return "available"
        return "error"

    def get_history(
        self,
        limit: int = 10,
        search: str | None = None,
        module: str | None = None,
    ) -> list[HistoryRecord]:
        """
        获取学习历史记录.

        查询过去的学习记录，支持分页、搜索和筛选。

        Args:
            limit: 返回记录数量，默认为 10
            search: 搜索关键词（标题匹配），可选
            module: 按模块筛选（video_summary/link_learning），可选

        Returns:
            HistoryRecord 列表

        Example:
            >>> api = AgentAPI()
            >>> # 查看最近10条记录
            >>> records = api.get_history(limit=10)
            >>> # 搜索关键词
            >>> records = api.get_history(search="Python")
            >>> # 按模块筛选
            >>> records = api.get_history(module="video_summary")
        """
        logger.debug(
            f"Getting history: limit={limit}, search={search}, module={module}"
        )

        try:
            # 获取所有记录
            all_records: list[HistoryRecord] = []

            if module:
                # 按模块筛选
                if module in self.history_manager.records:
                    all_records = self.history_manager.records[module]
            else:
                # 获取所有模块的记录
                for module_records in self.history_manager.records.values():
                    all_records.extend(module_records)

            # 搜索筛选
            if search:
                search_results = self.history_manager.search(search)
                # 如果同时指定了模块，需要交集
                if module:
                    all_records = [r for r in search_results if r.module == module]
                else:
                    all_records = search_results

            # 按时间排序（最新的在前）- 使用不可变 sorted() 函数
            all_records = sorted(all_records, key=lambda r: r.timestamp, reverse=True)

            # 限制数量
            records: list[HistoryRecord] = all_records[:limit]

            # 转换为 HistoryRecord schema
            from learning_assistant.api.schemas import HistoryRecord as APIHistoryRecord

            history_records: list[APIHistoryRecord] = [
                APIHistoryRecord(
                    id=record.record_id,
                    module=record.module,
                    title=record.metadata.get("title", record.input[:50]),
                    url=record.input,
                    timestamp=record.timestamp.isoformat(),
                    status=record.metadata.get("status", "success"),
                )
                for record in records
            ]

            logger.debug(f"Found {len(history_records)} history records")
            return history_records

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            raise

    def get_statistics(self) -> LearningStatistics:
        """
        获取学习统计信息.

        返回总体学习统计数据，包括总视频数、总时长、最常观看平台等。

        Returns:
            LearningStatistics 对象

        Example:
            >>> api = AgentAPI()
            >>> stats = api.get_statistics()
            >>> print(f"Total videos: {stats.total_videos}")
            >>> print(f"Total duration: {stats.total_duration} seconds")
        """
        logger.debug("Getting learning statistics")

        try:
            stats = self.history_manager.get_statistics()

            return LearningStatistics(
                total_videos=stats.get("total_videos", 0),
                total_duration=stats.get("total_duration", 0),
                most_watched_platform=stats.get("most_watched_platform"),
                recent_activity=stats.get("recent_activity", []),
            )

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

    async def summarize_video_stream(
        self,
        url: str,
        format: str = "markdown",
        language: str = "zh",
        output_dir: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream video summary with intermediate results.

        Yields processing stages as they complete, allowing Agents to
        show progress and intermediate results to users.

        Args:
            url: Video URL
            format: Output format (markdown/pdf)
            language: Summary language
            output_dir: Output directory
            **kwargs: Other options

        Yields:
            Progress dicts with stage and data:
            - {"stage": "downloading", "data": {"title": "..."}}
            - {"stage": "extracting_audio", "data": {"duration": 900}}
            - {"stage": "transcribing", "data": {"progress": 0.5}}
            - {"stage": "transcribed", "data": {"transcript": "..."}}
            - {"stage": "summarizing", "data": {"progress": 0.3}}
            - {"stage": "completed", "data": {"files": {...}}}

        Example:
            >>> api = AgentAPI()
            >>> for progress in await api.summarize_video_stream(url):
            ...     if progress["stage"] == "transcribed":
            ...         print(f"Got transcript: {len(progress['data']['transcript'])} chars")
            ...     if progress["stage"] == "completed":
            ...         print(f"Done! Files: {progress['data']['files']}")
        """
        import tempfile
        from learning_assistant.modules.video_summary import VideoSummaryModule
        from learning_assistant.core.event_bus import Event, EventType

        logger.info(f"Starting video stream: {url}")

        video_module = VideoSummaryModule()
        video_config = self.config_manager.modules_model.video_summary.config.copy()

        # Merge LLM settings
        if "llm" not in video_config:
            video_config["llm"] = {}
        provider = video_config["llm"].get("provider", "openai")
        global_llm_settings = self.config_manager.settings_model.llm.providers.get(provider)
        if global_llm_settings and hasattr(global_llm_settings, 'model_dump'):
            global_llm_settings_dict = global_llm_settings.model_dump()
        else:
            global_llm_settings_dict = global_llm_settings or {}
        video_config["llm"] = {
            **global_llm_settings_dict,
            **video_config["llm"],
        }

        if format:
            video_config["output"] = video_config.get("output", {})
            video_config["output"]["format"] = format
        if output_dir:
            video_config["output"] = video_config.get("output", {})
            video_config["output"]["directory"] = output_dir

        video_module.initialize(video_config, self.event_bus)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                work_dir = Path(tmpdir)

                # Stage 1: Download
                yield {"stage": "downloading", "data": {"url": url}}
                video_info = video_module._download_video(url, work_dir)
                yield {
                    "stage": "downloaded",
                    "data": {
                        "title": video_info["title"],
                        "duration": video_info["duration"],
                        "platform": video_info["platform"],
                    },
                }

                # Stage 2: Extract audio
                yield {"stage": "extracting_audio", "data": {}}
                audio_info = video_module._extract_audio(video_info["video_path"], work_dir)
                yield {
                    "stage": "audio_extracted",
                    "data": {
                        "duration": audio_info["duration"],
                        "sample_rate": audio_info["sample_rate"],
                    },
                }

                # Stage 3: Transcribe
                yield {"stage": "transcribing", "data": {"progress": 0.0}}
                transcript = video_module._transcribe_audio(audio_info["audio_path"])
                yield {
                    "stage": "transcribed",
                    "data": {
                        "transcript": transcript,
                        "length": len(transcript),
                    },
                }

                # Stage 4: Generate summary
                yield {"stage": "summarizing", "data": {"progress": 0.0}}
                summary_data = video_module._generate_summary(
                    video_info=video_info,
                    transcript=transcript,
                    language=language,
                    focus_areas=kwargs.get("focus_areas", []),
                )
                yield {
                    "stage": "summary_generated",
                    "data": {
                        "key_points": summary_data.get("key_points", []),
                        "knowledge": summary_data.get("knowledge", []),
                    },
                }

                # Stage 5: Export
                yield {"stage": "exporting", "data": {}}
                output_paths = video_module._export_output(
                    summary_data=summary_data,
                    output_format=format,
                    video_info=video_info,
                )

                result = {
                    "status": "success",
                    "video_info": video_info,
                    "summary": summary_data,
                    "output_paths": output_paths,
                }

                yield {
                    "stage": "completed",
                    "data": {
                        "title": video_info["title"],
                        "files": {k: str(v) for k, v in output_paths.items()},
                        "summary_preview": summary_data.get("summary", "")[:500],
                    },
                }

        except Exception as e:
            yield {"stage": "error", "data": {"error": str(e), "error_type": type(e).__name__}}
            raise

    async def process_link_stream(
        self,
        url: str,
        provider: str = "openai",
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream link processing with intermediate results.

        Yields processing stages as they complete.

        Args:
            url: Web URL
            provider: LLM provider
            **kwargs: Other options

        Yields:
            Progress dicts:
            - {"stage": "fetching", "data": {"url": "..."}}
            - {"stage": "fetched", "data": {"word_count": 3500}}
            - {"stage": "analyzing", "data": {}}
            - {"stage": "completed", "data": {"title": "...", "summary": "..."}}
        """
        from learning_assistant.modules.link_learning import LinkLearningModule
        from learning_assistant.core.services import ContentFetcher, ContentParser

        logger.info(f"Starting link stream: {url}")

        yield {"stage": "fetching", "data": {"url": url}}

        try:
            # Fetch content
            fetcher = ContentFetcher()
            content = await fetcher.fetch(url)
            yield {
                "stage": "fetched",
                "data": {
                    "word_count": len(content),
                    "source": url.split("//")[1].split("/")[0] if "//" in url else url,
                },
            }

            # Parse content
            yield {"stage": "parsing", "data": {}}
            parser = ContentParser()
            parsed = parser.parse(content, url)

            yield {
                "stage": "parsed",
                "data": {
                    "title": parsed.title,
                    "word_count": parsed.word_count,
                },
            }

            # Initialize module for LLM processing
            yield {"stage": "analyzing", "data": {"progress": 0.0}}
            module = LinkLearningModule()
            config = {"llm": {"provider": provider}}
            module.initialize(config, self.event_bus)

            # Set LLM service
            from learning_assistant.core.llm.service import LLMService
            api_key = os.environ.get(f"{provider.upper()}_API_KEY")
            if api_key:
                module.llm_service = LLMService(provider=provider, api_key=api_key)

            knowledge_card = await module.process(url)

            yield {
                "stage": "completed",
                "data": {
                    "title": knowledge_card.title,
                    "summary": knowledge_card.summary,
                    "key_points": knowledge_card.key_points[:3],
                    "tags": knowledge_card.tags,
                },
            }

        except Exception as e:
            yield {"stage": "error", "data": {"error": str(e), "error_type": type(e).__name__}}
            raise


# ── Singleton ──────────────────────────────────────────────
_api_instance: AgentAPI | None = None


def get_api() -> AgentAPI:
    """Return a cached AgentAPI instance.

    Avoids reinitializing ConfigManager, PluginManager, etc. on every call.
    """
    global _api_instance
    if _api_instance is None:
        _api_instance = AgentAPI()
    return _api_instance


def reset_api() -> None:
    """Reset the cached instance (useful for tests or config changes)."""
    global _api_instance
    _api_instance = None
