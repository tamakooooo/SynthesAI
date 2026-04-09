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
)


class TestAgentAPI:
    """测试 AgentAPI 类."""

    def test_init(self):
        """测试初始化."""
        api = AgentAPI()

        assert api.plugin_manager is not None
        assert api.history_manager is not None

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