"""
SynthesAI MCP Server - MCP Protocol Adapter for SynthesAI.

This is a thin adapter layer that exposes SynthesAI's AgentAPI as MCP Tools.
Zero intrusion to existing code - just wraps the existing API.

Installation:
    pip install "synthesai[mcp]"

Usage in Claude Desktop config:
    {
        "mcpServers": {
            "synthesai": {
                "command": "python",
                "args": ["-m", "learning_assistant.mcp.server"],
                "env": {
                    "OPENAI_API_KEY": "sk-...",
                    "ANTHROPIC_API_KEY": "sk-..."
                }
            }
        }
    }
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
except ImportError as e:
    raise ImportError(
        "MCP SDK not installed. Install with: pip install mcp"
    ) from e

# SynthesAI imports
from learning_assistant.api.agent_api import AgentAPI, get_api
from learning_assistant.api.schemas import (
    VideoSummaryResult,
    LinkSummaryResult,
    VocabularyResult,
)


# ── MCP Server Instance ──────────────────────────────────────────────────────

server = Server("synthesai")

# Cached API instance
_api_instance: AgentAPI | None = None


def _get_api() -> AgentAPI:
    """Get or create cached AgentAPI instance."""
    global _api_instance
    if _api_instance is None:
        logger.info("Initializing AgentAPI for MCP server")
        _api_instance = AgentAPI()
    return _api_instance


# ── Tool Definitions ──────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available MCP tools.

    These tools wrap SynthesAI's AgentAPI methods.
    """
    return [
        Tool(
            name="summarize_video",
            description="总结视频内容（B站/YouTube/抖音），提取字幕并生成知识摘要",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "视频URL（支持 B站/YouTube/抖音）",
                    },
                    "format": {
                        "type": "string",
                        "default": "markdown",
                        "description": "输出格式（markdown/pdf）",
                    },
                    "language": {
                        "type": "string",
                        "default": "zh",
                        "description": "总结语言（zh/en）",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="process_link",
            description="处理网页链接，生成知识卡片（摘要、要点、问答、测验）",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "网页URL",
                    },
                    "provider": {
                        "type": "string",
                        "default": "openai",
                        "description": "LLM 提供者（openai/anthropic/deepseek）",
                    },
                    "generate_quiz": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否生成测验题",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="extract_vocabulary",
            description="从文本或URL提取词汇，生成单词卡（音标、释义、例句）",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "文本内容（可选，如果提供url）",
                    },
                    "url": {
                        "type": "string",
                        "description": "网页链接（可选，如果提供content）",
                    },
                    "word_count": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                        "description": "提取单词数量",
                    },
                    "difficulty": {
                        "type": "string",
                        "default": "intermediate",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "目标难度",
                    },
                    "generate_story": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否生成上下文短文",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="list_skills",
            description="列出所有可用的学习技能（模块状态、版本、优先级）",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_history",
            description="获取学习历史记录",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "返回记录数量",
                    },
                    "search": {
                        "type": "string",
                        "description": "搜索关键词（标题匹配）",
                    },
                    "module": {
                        "type": "string",
                        "enum": ["video_summary", "link_learning", "vocabulary"],
                        "description": "按模块筛选",
                    },
                },
            },
        ),
        Tool(
            name="get_statistics",
            description="获取学习统计信息（总视频数、总时长、最常观看平台）",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


# ── Tool Handlers ────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute a tool call.

    Wraps AgentAPI methods and returns structured results.
    """
    api = _get_api()
    logger.info(f"MCP tool called: {name} with arguments: {arguments}")

    try:
        if name == "summarize_video":
            result = await api.summarize_video(
                url=arguments["url"],
                format=arguments.get("format", "markdown"),
                language=arguments.get("language", "zh"),
            )
            return _format_video_result(result)

        elif name == "process_link":
            result = await api.process_link(
                url=arguments["url"],
                provider=arguments.get("provider", "openai"),
                generate_quiz=arguments.get("generate_quiz", True),
            )
            return _format_link_result(result)

        elif name == "extract_vocabulary":
            result = await api.extract_vocabulary(
                content=arguments.get("content"),
                url=arguments.get("url"),
                word_count=arguments.get("word_count", 10),
                difficulty=arguments.get("difficulty", "intermediate"),
                generate_story=arguments.get("generate_story", True),
            )
            return _format_vocabulary_result(result)

        elif name == "list_skills":
            skills = api.list_skills()
            return _format_skills_list(skills)

        elif name == "get_history":
            records = api.get_history(
                limit=arguments.get("limit", 10),
                search=arguments.get("search"),
                module=arguments.get("module"),
            )
            return _format_history(records)

        elif name == "get_statistics":
            stats = api.get_statistics()
            return _format_statistics(stats)

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ── Result Formatters ─────────────────────────────────────────────────────────

def _format_video_result(result: VideoSummaryResult) -> list[TextContent]:
    """Format video summary result for MCP output."""
    text = f"""## 视频总结

**标题**: {result.title}
**URL**: {result.url}
**状态**: {result.status}

### 概要
{result.summary.get('content', '无摘要')}

### 核心要点
"""
    for point in result.summary.get("key_points", []):
        text += f"- {point}\n"

    text += "\n### 知识点\n"
    for knowledge in result.summary.get("knowledge", []):
        text += f"- {knowledge}\n"

    if result.feishu_url:
        text += f"\n**飞书文档**: {result.feishu_url}\n"

    if result.files.get("summary_path"):
        text += f"\n**文件路径**: {result.files['summary_path']}\n"

    return [TextContent(type="text", text=text)]


def _format_link_result(result: LinkSummaryResult) -> list[TextContent]:
    """Format link learning result for MCP output."""
    text = f"""## 知识卡片

**标题**: {result.title}
**来源**: {result.source}
**URL**: {result.url}
**难度**: {result.difficulty}
**字数**: {result.word_count}
**阅读时间**: {result.reading_time}

### 摘要
{result.summary}

### 核心要点
"""
    for point in result.key_points:
        text += f"- {point}\n"

    text += "\n### 标签\n"
    text += ", ".join(result.tags) + "\n"

    if result.qa_pairs:
        text += "\n### 问答\n"
        for qa in result.qa_pairs:
            text += f"**Q**: {qa['question']}\n**A**: {qa['answer']}\n\n"

    if result.quiz:
        text += "\n### 测验\n"
        for q in result.quiz:
            text += f"**{q['type']}**: {q['question']}\n"
            if q.get("options"):
                for opt in q["options"]:
                    text += f"  {opt}\n"
            text += f"**答案**: {q['correct']}\n"
            if q.get("explanation"):
                text += f"**解析**: {q['explanation']}\n\n"

    return [TextContent(type="text", text=text)]


def _format_vocabulary_result(result: VocabularyResult) -> list[TextContent]:
    """Format vocabulary extraction result for MCP output."""
    text = f"""## 词汇学习

**源内容**: {result.content[:100]}...
**提取数量**: {result.word_count}
**难度**: {result.difficulty}

### 单词卡

"""
    for card in result.vocabulary_cards:
        word = card.get("word", "")
        phonetic = card.get("phonetic", {})
        pos = card.get("part_of_speech", "")
        definition = card.get("definition", {})

        text += f"#### {word}\n"
        if phonetic:
            us = phonetic.get("us", "")
            uk = phonetic.get("uk", "")
            text += f"音标: {us} (US) / {uk} (UK)\n"
        if pos:
            text += f"词性: {pos}\n"
        if definition:
            zh = definition.get("zh", "")
            en = definition.get("en", "")
            text += f"释义: {zh} | {en}\n"

        examples = card.get("example_sentences", [])
        if examples:
            text += "例句:\n"
            for ex in examples[:2]:
                text += f"  - {ex.get('sentence', '')}\n"
                text += f"    {ex.get('translation', '')}\n"
        text += "\n"

    if result.context_story:
        story = result.context_story
        text += f"""### 上下文短文

**标题**: {story.get('title', '')}

{story.get('content', '')}

"""

    return [TextContent(type="text", text=text)]


def _format_skills_list(skills: list) -> list[TextContent]:
    """Format skills list for MCP output."""
    text = "## 可用技能\n\n"
    for skill in skills:
        status_icon = "✅" if skill.status == "available" else "❌"
        text += f"{status_icon} **{skill.name}** (v{skill.version})\n"
        text += f"   {skill.description}\n"
        text += f"   类型: {skill.type} | 状态: {skill.status} | 已加载: {skill.loaded}\n"
        if skill.actions:
            text += f"   动作: {', '.join(skill.actions)}\n"
        text += "\n"

    return [TextContent(type="text", text=text)]


def _format_history(records: list) -> list[TextContent]:
    """Format history records for MCP output."""
    if not records:
        return [TextContent(type="text", text="暂无历史记录")]

    text = "## 学习历史\n\n"
    for record in records:
        status_icon = "✅" if record.status == "success" else "⏳"
        text += f"{status_icon} [{record.module}] {record.title}\n"
        text += f"   URL: {record.url}\n"
        text += f"   时间: {record.timestamp}\n\n"

    return [TextContent(type="text", text=text)]


def _format_statistics(stats) -> list[TextContent]:
    """Format statistics for MCP output."""
    text = f"""## 学习统计

- **总视频数**: {stats.total_videos}
- **总学习时长**: {stats.total_duration // 60} 分钟
- **最常观看平台**: {stats.most_watched_platform or '暂无数据'}

"""
    return [TextContent(type="text", text=text)]


# ── Entry Point ───────────────────────────────────────────────────────────────

async def run_server():
    """Run the MCP server via stdio."""
    logger.info("Starting SynthesAI MCP server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point for MCP server."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()