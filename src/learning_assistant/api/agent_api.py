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

from datetime import datetime
from pathlib import Path
from typing import Any

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
            config_path: 配置文件路径（可选）。如果不提供，使用默认配置。
        """
        logger.info("Initializing AgentAPI")

        # 初始化配置管理器
        from learning_assistant.core.config_manager import ConfigManager

        self.config_manager = ConfigManager()
        self.config_manager.load_all()

        # 初始化插件管理器
        self.plugin_manager = PluginManager(config_path)

        # 发现并加载所有插件
        discovered = self.plugin_manager.discover_plugins()
        for plugin_metadata in discovered:
            if plugin_metadata.enabled:
                self.plugin_manager.load_plugin(plugin_metadata.name)

        # 初始化历史记录管理器
        self.history_manager = HistoryManager()

        # 初始化事件总线
        from learning_assistant.core.event_bus import EventBus

        self.event_bus = EventBus()

        logger.success("AgentAPI initialized successfully")

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
                title=result.get("metadata", {}).get("title", "Unknown"),
                summary=result.get("summary", {}),
                transcript=result.get("transcript", ""),
                files={
                    "summary_path": result.get("summary_path"),
                    "subtitle_path": result.get("subtitle_path"),
                },
                metadata=result.get("metadata", {}),
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

        返回所有已加载模块的信息，包括名称、描述、版本、状态。

        Returns:
            SkillInfo 列表

        Example:
            >>> api = AgentAPI()
            >>> skills = api.list_skills()
            >>> for skill in skills:
            ...     print(f"{skill.name}: {skill.description}")
        """
        logger.debug("Listing available skills")

        # 获取已发现插件的元数据
        discovered_plugins = self.plugin_manager.plugins

        skills = [
            SkillInfo(
                name=plugin_metadata.name,
                description=plugin_metadata.description,
                version=plugin_metadata.version,
                status="available" if plugin_metadata.enabled else "disabled",
            )
            for plugin_metadata in discovered_plugins.values()
        ]

        logger.debug(f"Found {len(skills)} skills")
        return skills

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
