"""
输出 Schema - 使用 Pydantic 定义结构化输出.

所有 Skills 返回的数据都使用 Pydantic 模型验证，
确保数据结构一致性和类型安全。
"""

from typing import Any
from pydantic import BaseModel, Field


class VideoSummaryResult(BaseModel):
    """
    视频总结结果.

    Attributes:
        status: 状态（success/error）
        url: 视频URL
        title: 视频标题
        summary: 总结内容（包含 content、key_points、knowledge）
        transcript: 字幕文本
        files: 输出文件路径（summary_path、subtitle_path）
        metadata: 视频元数据（duration、platform、uploader等）
        timestamp: ISO 8601 格式时间戳
    """

    status: str = Field(description="状态（success/error）")
    url: str = Field(description="视频URL")
    title: str = Field(description="视频标题")
    summary: dict[str, Any] = Field(
        description="总结内容",
        examples=[
            {
                "content": "本视频介绍了...",
                "key_points": ["要点1", "要点2"],
                "knowledge": ["知识点1", "知识点2"],
            }
        ],
    )
    transcript: str = Field(description="字幕文本")
    files: dict[str, str | None] = Field(
        description="输出文件路径",
        examples=[
            {
                "summary_path": "./outputs/summary.md",
                "subtitle_path": "./outputs/subtitle.srt",
            }
        ],
    )
    metadata: dict[str, Any] = Field(
        description="视频元数据",
        examples=[{"duration": 900, "platform": "bilibili", "uploader": "UP主"}],
    )
    timestamp: str = Field(description="ISO 8601 格式时间戳")


class SkillInfo(BaseModel):
    """
    技能信息.

    Attributes:
        name: 技能名称
        description: 技能描述
        version: 版本号
        status: 状态（available/disabled/error）
    """

    name: str = Field(description="技能名称")
    description: str = Field(description="技能描述")
    version: str = Field(description="版本号")
    status: str = Field(description="状态（available/disabled/error）")


class HistoryRecord(BaseModel):
    """
    历史记录.

    Attributes:
        id: 记录唯一标识
        module: 模块名称（video_summary/link_learning）
        title: 视频标题或学习主题
        url: 视频 URL 或资源链接
        timestamp: ISO 8601 格式时间戳
        status: 状态（completed/in_progress/failed）
    """

    id: str = Field(description="记录唯一标识")
    module: str = Field(description="模块名称")
    title: str = Field(description="视频标题或学习主题")
    url: str = Field(description="视频 URL 或资源链接")
    timestamp: str = Field(description="ISO 8601 格式时间戳")
    status: str = Field(description="状态（completed/in_progress/failed）")


class LearningStatistics(BaseModel):
    """
    学习统计信息.

    Attributes:
        total_videos: 总视频数
        total_duration: 总学习时长（秒）
        most_watched_platform: 最常观看的平台
        recent_activity: 最近活动记录
    """


class LinkSummaryResult(BaseModel):
    """
    链接学习结果.

    Attributes:
        status: 状态（success/error）
        url: 原始URL
        title: 文章标题
        source: 来源网站
        summary: 摘要（200字左右）
        key_points: 核心要点（3-5个）
        tags: 标签（3-5个）
        word_count: 字数
        reading_time: 阅读时间
        difficulty: 难度（beginner/intermediate/advanced）
        qa_pairs: 问答对
        quiz: 测验题
        files: 输出文件路径
        timestamp: ISO 8601 格式时间戳
    """

    status: str = Field(description="状态（success/error）")
    url: str = Field(description="原始URL")
    title: str = Field(description="文章标题")
    source: str = Field(description="来源网站")
    summary: str = Field(description="摘要（200字左右）")
    key_points: list[str] = Field(description="核心要点（3-5个）")
    tags: list[str] = Field(description="标签（3-5个）")
    word_count: int = Field(description="字数")
    reading_time: str = Field(description="阅读时间")
    difficulty: str = Field(description="难度（beginner/intermediate/advanced）")
    qa_pairs: list[dict[str, str]] = Field(
        default_factory=list,
        description="问答对",
        examples=[
            [
                {
                    "question": "什么是机器学习？",
                    "answer": "机器学习是让计算机从数据中学习模式的技术",
                    "difficulty": "medium",
                }
            ]
        ],
    )
    quiz: list[dict[str, Any]] = Field(
        default_factory=list,
        description="测验题",
        examples=[
            [
                {
                    "type": "multiple_choice",
                    "question": "以下哪个是监督学习的应用？",
                    "options": ["A. 图像分类", "B. 聚类", "C. 异常检测"],
                    "correct": "A",
                }
            ]
        ],
    )
    files: dict[str, str | None] = Field(
        default_factory=dict,
        description="输出文件路径",
        examples=[
            {
                "markdown_path": "./outputs/article.md",
                "json_path": "./outputs/article.json",
            }
        ],
    )
    timestamp: str = Field(description="ISO 8601 格式时间戳")


class VocabularyResult(BaseModel):
    """
    单词学习结果.

    Attributes:
        status: 状态（success/error）
        content: 源内容
        word_count: 提取单词数量
        difficulty: 目标难度
        vocabulary_cards: 单词卡列表
        context_story: 上下文短文
        statistics: 统计信息
        files: 输出文件路径
        timestamp: ISO 8601 格式时间戳
    """

    status: str = Field(description="状态（success/error）")
    content: str = Field(description="源内容（前200字符）")
    word_count: int = Field(description="提取单词数量")
    difficulty: str = Field(description="目标难度")
    vocabulary_cards: list[dict[str, Any]] = Field(
        description="单词卡列表",
        examples=[
            [
                {
                    "word": "example",
                    "phonetic": {"us": "/ɪgˈzæmpəl/", "uk": "/ɪgˈzɑːmpəl/"},
                    "part_of_speech": "noun",
                    "definition": {
                        "zh": "例子",
                        "en": "a thing characteristic of its kind",
                    },
                    "example_sentences": [
                        {
                            "sentence": "This is an example.",
                            "translation": "这是一个例子。",
                            "context": "LLM生成",
                        }
                    ],
                    "difficulty": "intermediate",
                    "frequency": "high",
                }
            ]
        ],
    )
    context_story: dict[str, Any] | None = Field(
        default=None,
        description="上下文短文",
        examples=[
            {
                "title": "Example Story",
                "content": "Once upon a time...",
                "word_count": 300,
                "difficulty": "intermediate",
            }
        ],
    )
    statistics: dict[str, Any] = Field(
        default_factory=dict,
        description="统计信息",
        examples=[
            {
                "total_words": 10,
                "difficulty_distribution": {
                    "beginner": 3,
                    "intermediate": 5,
                    "advanced": 2,
                },
            }
        ],
    )
    files: dict[str, str | None] = Field(
        default_factory=dict,
        description="输出文件路径",
        examples=[{"markdown_path": "./outputs/vocabulary.md"}],
    )
    timestamp: str = Field(description="ISO 8601 格式时间戳")

    total_videos: int = Field(description="总视频数")
    total_duration: int = Field(description="总学习时长（秒）")
    most_watched_platform: str | None = Field(description="最常观看的平台")
    recent_activity: list[dict[str, Any]] = Field(description="最近活动记录")
