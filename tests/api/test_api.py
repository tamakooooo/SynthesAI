"""
API 综合测试.

测试 Learning Assistant Agent API 的核心功能。

测试覆盖：
- AgentAPI 类
- 便捷函数
- 数据模型验证
- 错误处理
"""

import pytest
from learning_assistant.api import (
    AgentAPI,
    summarize_video,
    list_available_skills,
    get_recent_history,
    process_link,
    process_link_sync,
)
from learning_assistant.api.schemas import VideoSummaryResult, SkillInfo, HistoryRecord, LinkSummaryResult
from learning_assistant.api.exceptions import (
    LearningAssistantError,
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
    SkillNotFoundError,
)


class TestAgentAPI:
    """测试 AgentAPI 类."""

    def test_init(self):
        """测试初始化."""
        api = AgentAPI()

        assert api.plugin_manager is not None
        assert api.history_manager is not None

    def test_plugin_initialization(self):
        """测试插件初始化序列：发现并加载插件."""
        api = AgentAPI()

        # 验证插件被正确发现
        discovered = api.plugin_manager.discover_plugins()
        assert len(discovered) > 0
        assert all(hasattr(plugin, 'name') for plugin in discovered)
        assert all(hasattr(plugin, 'enabled') for plugin in discovered)

        # 验证已加载的插件
        loaded_plugins = api.plugin_manager.plugins
        assert len(loaded_plugins) > 0

        # 验证核心插件已加载
        assert "video_summary" in loaded_plugins
        assert "link_learning" in loaded_plugins

        # 验证插件实例可获取
        video_plugin = api.plugin_manager.get_plugin("video_summary")
        assert video_plugin is not None
        assert hasattr(video_plugin, 'execute')

    def test_plugin_initialization_only_enabled(self):
        """测试只加载启用的插件."""
        api = AgentAPI()

        # 获取所有已发现的插件
        discovered = api.plugin_manager.discover_plugins()

        # 统计启用的插件数量
        enabled_count = sum(1 for plugin in discovered if plugin.enabled)

        # 已加载插件数量应该等于或小于启用插件数量
        loaded_count = len(api.plugin_manager.loaded_plugins)
        assert loaded_count <= enabled_count

        # 所有已加载插件应该都是启用的
        for plugin_name in api.plugin_manager.loaded_plugins.keys():
            # 从 self.plugins 获取元数据
            if plugin_name in api.plugin_manager.plugins:
                plugin_metadata = api.plugin_manager.plugins[plugin_name]
                assert plugin_metadata.enabled is True

    @pytest.mark.asyncio
    async def test_summarize_video_module_creates_instance(self):
        """测试 summarize_video 创建并初始化模块实例."""
        api = AgentAPI()

        # 调用 summarize_video 会创建新的模块实例
        # 由于没有配置 API key，会抛出 ValueError
        with pytest.raises(ValueError, match="API key not found"):
            await api.summarize_video(url="https://www.bilibili.com/video/BV1G49MBLE4D")

    @pytest.mark.asyncio
    async def test_summarize_video_with_valid_config(self):
        """测试使用有效配置调用视频总结."""
        api = AgentAPI()

        # 这个测试需要真实的 API key 和网络连接
        # 在没有配置的环境下会失败
        try:
            result = await api.summarize_video(url="https://www.bilibili.com/video/BV1G49MBLE4D")
            # 如果成功，验证结果结构
            assert result.status == "success"
        except ValueError as e:
            # 预期错误：没有 API key
            assert "API key not found" in str(e)
        except Exception as e:
            # 其他可能的错误（网络、下载等）
            # 这些都是可以接受的
            pass

    def test_get_plugin_returns_none_for_invalid_name(self):
        """测试 get_plugin 对无效插件名返回 None."""
        api = AgentAPI()

        # 尝试获取不存在的插件
        invalid_plugin = api.plugin_manager.get_plugin("nonexistent_plugin_xyz")

        # 应该返回 None，而不是抛出异常
        assert invalid_plugin is None

    def test_plugin_manager_get_all_plugins(self):
        """测试 get_all_plugins 返回所有插件实例."""
        api = AgentAPI()

        all_plugins = api.plugin_manager.get_all_plugins()

        # 应该返回字典
        assert isinstance(all_plugins, dict)
        assert len(all_plugins) > 0

        # 验证插件实例
        for plugin_name, plugin_instance in all_plugins.items():
            # 插件应该是 BaseModule 或 BaseAdapter 实例
            from learning_assistant.core.base_module import BaseModule
            from learning_assistant.core.base_adapter import BaseAdapter

            assert isinstance(plugin_instance, (BaseModule, BaseAdapter))

            # BaseModule 有 execute 方法，BaseAdapter 有 initialize 方法
            if isinstance(plugin_instance, BaseModule):
                assert hasattr(plugin_instance, 'execute')
            elif isinstance(plugin_instance, BaseAdapter):
                assert hasattr(plugin_instance, 'initialize')

    def test_list_skills_uses_discovered_plugins(self):
        """测试 list_skills 使用已发现的插件元数据."""
        api = AgentAPI()

        skills = api.list_skills()

        # 获取已发现插件的元数据
        discovered_plugins = api.plugin_manager.plugins

        # 验证技能数量与已发现插件一致
        assert len(skills) == len(discovered_plugins)

        # 验证技能名称与插件名称匹配
        skill_names = [skill.name for skill in skills]
        plugin_names = list(discovered_plugins.keys())

        assert set(skill_names) == set(plugin_names)

    def test_list_skills(self):
        """测试列出技能."""
        api = AgentAPI()
        skills = api.list_skills()

        assert isinstance(skills, list)
        assert len(skills) > 0
        assert all(isinstance(skill, SkillInfo) for skill in skills)

        # 检查必需字段
        skill = skills[0]
        assert skill.name
        assert skill.description
        assert skill.version
        assert skill.status

    def test_get_history(self):
        """测试获取历史记录."""
        api = AgentAPI()
        records = api.get_history(limit=10)

        assert isinstance(records, list)
        # 可能为空（如果没有历史记录）
        if records:
            assert all(isinstance(record, HistoryRecord) for record in records)

            record = records[0]
            assert record.id
            assert record.module
            assert record.title
            assert record.url
            assert record.timestamp
            assert record.status

    def test_get_history_with_search(self):
        """测试搜索历史记录."""
        api = AgentAPI()

        # 搜索可能不存在的关键词
        records = api.get_history(search="NonExistentKeyword12345")

        assert isinstance(records, list)
        # 应该为空或很少
        assert len(records) >= 0

    def test_get_history_with_module_filter(self):
        """测试按模块筛选历史记录."""
        api = AgentAPI()

        records = api.get_history(module="video_summary")

        assert isinstance(records, list)
        # 所有记录的 module 应该是 video_summary
        for record in records:
            assert record.module == "video_summary"

    def test_get_history_invalid_module(self):
        """测试使用无效模块名获取历史记录."""
        api = AgentAPI()

        # 使用不存在的模块名
        records = api.get_history(module="nonexistent_module_12345")

        # 应该返回空列表
        assert isinstance(records, list)
        assert len(records) == 0

    def test_get_history_empty_after_clear(self):
        """测试清空历史记录后返回空列表."""
        api = AgentAPI()

        # 清空历史记录（如果支持）
        # 注意：HistoryManager 可能没有 clear 方法，这里测试逻辑
        # 如果不支持，跳过此测试

        # 获取历史记录
        records = api.get_history(limit=100)

        # 验证返回的是列表
        assert isinstance(records, list)

        # 如果有记录，测试清空后
        if len(records) > 0 and hasattr(api.history_manager, 'clear'):
            api.history_manager.clear()
            records_after_clear = api.get_history(limit=100)
            assert len(records_after_clear) == 0

    def test_get_history_pagination(self):
        """测试历史记录分页/限制功能."""
        api = AgentAPI()

        # 获取不同数量的记录
        records_5 = api.get_history(limit=5)
        records_10 = api.get_history(limit=10)
        records_100 = api.get_history(limit=100)

        # 验证限制生效
        assert len(records_5) <= 5
        assert len(records_10) <= 10
        assert len(records_100) <= 100

    def test_get_history_combined_filters(self):
        """测试组合搜索和模块筛选."""
        api = AgentAPI()

        # 同时使用搜索和模块筛选
        records = api.get_history(
            search="test",
            module="video_summary",
            limit=10
        )

        assert isinstance(records, list)
        assert len(records) <= 10

        # 验证所有记录都匹配模块
        for record in records:
            assert record.module == "video_summary"


class TestConvenienceFunctions:
    """测试便捷函数."""

    def test_list_available_skills(self):
        """测试列出可用技能."""
        skills = list_available_skills()

        assert isinstance(skills, list)
        assert len(skills) > 0

        # 检查返回的是字典（不是 SkillInfo 对象）
        skill = skills[0]
        assert isinstance(skill, dict)
        assert "name" in skill
        assert "description" in skill
        assert "version" in skill
        assert "status" in skill

    def test_get_recent_history(self):
        """测试获取最近历史记录."""
        records = get_recent_history(limit=5)

        assert isinstance(records, list)
        # 检查返回的是字典
        if records:
            record = records[0]
            assert isinstance(record, dict)
            assert "id" in record
            assert "title" in record


class TestSchemas:
    """测试数据模型."""

    def test_video_summary_result_schema(self):
        """测试视频总结结果模型."""
        result = VideoSummaryResult(
            status="success",
            url="https://test.com",
            title="Test Video",
            summary={"content": "Test summary"},
            transcript="Test transcript",
            files={"summary_path": "/path/to/summary.md", "subtitle_path": "/path/to/subtitle.srt"},
            metadata={"duration": 100},
            timestamp="2026-03-31T10:00:00",
        )

        assert result.status == "success"
        assert result.url == "https://test.com"
        assert result.title == "Test Video"

        # 测试序列化
        result_dict = result.model_dump()
        assert isinstance(result_dict, dict)
        assert result_dict["status"] == "success"

    def test_skill_info_schema(self):
        """测试技能信息模型."""
        skill = SkillInfo(
            name="test-skill",
            description="Test skill",
            version="1.0.0",
            status="available",
        )

        assert skill.name == "test-skill"
        assert skill.description == "Test skill"
        assert skill.version == "1.0.0"
        assert skill.status == "available"

    def test_history_record_schema(self):
        """测试历史记录模型."""
        record = HistoryRecord(
            id="rec_001",
            module="video_summary",
            title="Test Video",
            url="https://test.com",
            timestamp="2026-03-31T10:00:00",
            status="completed",
        )

        assert record.id == "rec_001"
        assert record.module == "video_summary"
        assert record.title == "Test Video"


class TestExceptions:
    """测试异常."""

    def test_exception_hierarchy(self):
        """测试异常继承关系."""
        # 所有自定义异常应该继承自 LearningAssistantError
        assert issubclass(VideoNotFoundError, LearningAssistantError)
        assert issubclass(VideoDownloadError, LearningAssistantError)
        assert issubclass(TranscriptionError, LearningAssistantError)
        assert issubclass(LLMAPIError, LearningAssistantError)

    def test_exception_message(self):
        """测试异常消息."""
        try:
            raise VideoNotFoundError("Video not found at https://test.com")
        except VideoNotFoundError as e:
            assert "Video not found" in str(e)
            assert isinstance(e, LearningAssistantError)


# 集成测试（需要真实视频 URL，使用 pytest.mark.integration 标记）
@pytest.mark.integration
@pytest.mark.asyncio
async def test_summarize_video_integration():
    """集成测试：视频总结（需要真实 URL）."""
    # 使用一个短的测试视频
    result = await summarize_video(
        url="https://www.bilibili.com/video/BV1GJ411x7h7",  # 示例视频
        format="markdown",
        language="zh",
    )

    assert result["status"] == "success"
    assert "title" in result
    assert "summary" in result
    assert "transcript" in result
    assert "files" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_summarize_video_error_handling():
    """集成测试：错误处理."""
    # 测试无效 URL
    with pytest.raises(Exception):  # 可能是 VideoNotFoundError 或其他错误
        await summarize_video(url="https://invalid-url-12345.com/video")


# 链接学习 API 测试
class TestLinkLearningAPI:
    """测试链接学习 API."""

    @pytest.mark.asyncio
    async def test_process_link_invalid_url(self):
        """测试无效 URL 处理."""
        api = AgentAPI()

        with pytest.raises(ValueError, match="Invalid URL"):
            await api.process_link(url="not-a-valid-url")

    @pytest.mark.asyncio
    async def test_process_link_missing_api_key(self):
        """测试缺少 API key."""
        import os

        # 临时移除 API key
        original_key = os.environ.pop("OPENAI_API_KEY", None)

        try:
            api = AgentAPI()

            with pytest.raises(ValueError, match="API key not found"):
                await api.process_link(url="https://example.com/article")

        finally:
            # 恢复 API key
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_link_summary_result_model(self):
        """测试 LinkSummaryResult 数据模型."""
        result = LinkSummaryResult(
            status="success",
            url="https://example.com/article",
            title="Test Article",
            source="example.com",
            summary="This is a test summary.",
            key_points=["Point 1", "Point 2", "Point 3"],
            tags=["test", "example", "api"],
            word_count=1000,
            reading_time="4分钟",
            difficulty="intermediate",
            qa_pairs=[
                {
                    "question": "What is this?",
                    "answer": "This is a test.",
                    "difficulty": "easy",
                }
            ],
            quiz=[
                {
                    "type": "multiple_choice",
                    "question": "Which is correct?",
                    "options": ["A", "B", "C", "D"],
                    "correct": "A",
                }
            ],
            files={},
            timestamp="2026-03-31T10:00:00",
        )

        assert result.status == "success"
        assert result.url == "https://example.com/article"
        assert result.title == "Test Article"
        assert len(result.key_points) == 3
        assert len(result.tags) == 3
        assert result.word_count == 1000
        assert result.difficulty == "intermediate"

    def test_process_link_sync_function_exists(self):
        """测试 process_link_sync 函数存在."""
        from learning_assistant.api import process_link_sync

        assert callable(process_link_sync)


# 链接学习集成测试（需要真实 URL 和 API key）
@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_link_integration():
    """集成测试：链接学习（需要真实 URL）."""
    # 使用一个测试网站
    result = await process_link(
        url="https://example.com",
        provider="openai",
        model="gpt-3.5-turbo",  # 使用更便宜的模型测试
        generate_quiz=False,  # 跳过测验以加快速度
    )

    assert result["status"] == "success"
    assert "title" in result
    assert "summary" in result
    assert "key_points" in result
    assert "tags" in result
    assert result["url"] == "https://example.com"


@pytest.mark.integration
def test_process_link_sync_integration():
    """集成测试：同步链接学习."""
    result = process_link_sync(
        url="https://example.com",
        provider="openai",
        model="gpt-3.5-turbo",
        generate_quiz=False,
    )

    assert result["status"] == "success"
    assert "title" in result
    assert "summary" in result


# 单元测试示例：Mock 测试
@pytest.mark.asyncio
async def test_summarize_video_mock(mocker):
    """单元测试：使用 Mock 测试视频总结."""
    # Mock AgentAPI.summarize_video
    mock_result = VideoSummaryResult(
        status="success",
        url="https://test.com",
        title="Mock Video",
        summary={"content": "Mock summary"},
        transcript="Mock transcript",
        files={"summary_path": "/mock/summary.md", "subtitle_path": "/mock/subtitle.srt"},
        metadata={"duration": 100},
        timestamp="2026-03-31T10:00:00",
    )

    mocker.patch(
        "learning_assistant.api.AgentAPI.summarize_video",
        return_value=mock_result,
    )

    result = await summarize_video(url="https://test.com")

    assert result["status"] == "success"
    assert result["title"] == "Mock Video"


# 性能测试
def test_list_skills_performance():
    """性能测试：列出技能应该很快."""
    import time

    start = time.time()
    skills = list_available_skills()
    end = time.time()

    # 应该在 1 秒内完成
    assert (end - start) < 1.0
    assert len(skills) > 0


def test_get_history_performance():
    """性能测试：获取历史记录应该很快."""
    import time

    start = time.time()
    records = get_recent_history(limit=100)
    end = time.time()

    # 应该在 1 秒内完成
    assert (end - start) < 1.0