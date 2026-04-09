"""
链接学习模块集成测试.

使用真实 URL 和 LLM API 测试完整流程。
需要设置环境变量：OPENAI_API_KEY

运行方式：
    pytest tests/modules/link_learning/test_integration.py -m integration -v
"""

import pytest
from learning_assistant.api import process_link, process_link_sync
from learning_assistant.modules.link_learning import LinkLearningModule
from learning_assistant.core.event_bus import EventBus


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_link_real_url():
    """集成测试：处理真实 URL."""
    # 使用一个简单的测试网站
    result = await process_link(
        url="https://example.com",
        provider="openai",
        model="gpt-3.5-turbo",  # 使用便宜的模型测试
        generate_quiz=False,  # 跳过测验以加快速度
    )

    # 验证基本字段
    assert result["status"] == "success"
    assert "title" in result
    assert "summary" in result
    assert "key_points" in result
    assert "tags" in result
    assert result["url"] == "https://example.com"

    # 验证数据类型
    assert isinstance(result["title"], str)
    assert isinstance(result["summary"], str)
    assert isinstance(result["key_points"], list)
    assert isinstance(result["tags"], list)
    assert isinstance(result["word_count"], int)
    assert result["word_count"] > 0

    # 验证内容质量
    assert len(result["summary"]) > 50  # 摘要至少50字符
    assert len(result["key_points"]) >= 3  # 至少3个要点
    assert len(result["tags"]) >= 3  # 至少3个标签


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_link_with_quiz():
    """集成测试：生成测验题."""
    result = await process_link(
        url="https://example.com",
        provider="openai",
        model="gpt-3.5-turbo",
        generate_quiz=True,  # 启用测验生成
    )

    assert result["status"] == "success"

    # 验证问答对
    if result["qa_pairs"]:
        qa = result["qa_pairs"][0]
        assert "question" in qa
        assert "answer" in qa
        assert len(qa["question"]) > 10
        assert len(qa["answer"]) > 10

    # 验证测验题
    if result["quiz"]:
        quiz = result["quiz"][0]
        assert quiz["type"] == "multiple_choice"
        assert "question" in quiz
        assert "options" in quiz
        assert len(quiz["options"]) == 4  # 4个选项
        assert "correct" in quiz


@pytest.mark.integration
def test_process_link_sync_real_url():
    """集成测试：同步版本处理."""
    result = process_link_sync(
        url="https://example.com",
        provider="openai",
        model="gpt-3.5-turbo",
        generate_quiz=False,
    )

    assert result["status"] == "success"
    assert "title" in result
    assert "summary" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_link_different_providers():
    """集成测试：不同 LLM 提供者."""
    import os

    # 测试 OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        result = await process_link(
            url="https://example.com",
            provider="openai",
            model="gpt-3.5-turbo",
            generate_quiz=False,
        )
        assert result["status"] == "success"

    # 测试 Anthropic (如果有 API key)
    if os.environ.get("ANTHROPIC_API_KEY"):
        result = await process_link(
            url="https://example.com",
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            generate_quiz=False,
        )
        assert result["status"] == "success"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_link_learning_module_direct():
    """集成测试：直接使用模块."""
    from learning_assistant.core.llm.service import LLMService
    import os

    # 初始化模块
    module = LinkLearningModule()
    config = {
        "llm": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
        },
        "features": {
            "generate_quiz": False,
        },
    }
    event_bus = EventBus()
    module.initialize(config, event_bus)

    # 设置 LLM 服务
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    module.llm_service = LLMService(
        provider="openai",
        api_key=api_key,
        model="gpt-3.5-turbo",
    )

    # 处理 URL
    knowledge_card = await module.process("https://example.com")

    # 验证结果
    assert knowledge_card.title
    assert knowledge_card.summary
    assert len(knowledge_card.key_points) >= 3
    assert len(knowledge_card.tags) >= 3
    assert knowledge_card.word_count > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_link_error_handling():
    """集成测试：错误处理."""
    # 测试无效 URL
    with pytest.raises(ValueError):
        await process_link(url="not-a-valid-url")

    # 测试不存在的域名
    with pytest.raises(Exception):  # 可能是 RuntimeError 或其他
        await process_link(url="https://this-domain-does-not-exist-12345.com")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_link_various_content_types():
    """集成测试：不同类型的内容."""
    test_urls = [
        # 简单网页
        ("https://example.com", "beginner"),
        # 技术文档（如果可用）
        # ("https://docs.python.org/3/tutorial/index.html", "intermediate"),
    ]

    for url, expected_difficulty in test_urls:
        result = await process_link(
            url=url,
            provider="openai",
            model="gpt-3.5-turbo",
            generate_quiz=False,
        )

        assert result["status"] == "success"
        assert result["difficulty"] in ["beginner", "intermediate", "advanced"]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_process_link_large_content():
    """集成测试：大型内容处理."""
    # 使用包含大量内容的页面
    result = await process_link(
        url="https://en.wikipedia.org/wiki/Python_(programming_language)",
        provider="openai",
        model="gpt-3.5-turbo",
        generate_quiz=False,
    )

    assert result["status"] == "success"
    assert result["word_count"] > 1000  # 大型内容
    assert len(result["summary"]) > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])