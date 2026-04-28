"""
统一异常定义.

Learning Assistant 提供清晰的异常层次结构，
帮助 Agent 框架进行精确的错误处理和用户友好的错误提示。

异常层次：
    LearningAssistantError (基类)
    ├─ SkillNotFoundError
    ├─ VideoNotFoundError
    ├─ VideoDownloadError
    ├─ TranscriptionError
    └─ LLMAPIError

使用示例：
    from learning_assistant.api import summarize_video
    from learning_assistant.api.exceptions import VideoNotFoundError

    try:
        result = await summarize_video(url="https://...")
    except VideoNotFoundError:
        print("视频不存在，请检查 URL")
"""


class LearningAssistantError(Exception):
    """
    Learning Assistant 基础异常.

    所有 Learning Assistant 异常的基类。
    """

    is_retryable: bool = False
    retry_after: int | None = None
    retry_suggestion: str | None = None

    def to_http_status(self) -> int:
        """Return corresponding HTTP status code for this exception."""
        return 500


class SkillNotFoundError(LearningAssistantError):
    """
    技能不存在.

    当请求的技能名称不存在时抛出。
    """

    is_retryable = False

    def to_http_status(self) -> int:
        """Return HTTP 404 Not Found."""
        return 404


class VideoNotFoundError(LearningAssistantError):
    """
    视频不存在.

    当视频 URL 无效或视频已删除时抛出。
    """

    is_retryable = False

    def to_http_status(self) -> int:
        """Return HTTP 404 Not Found."""
        return 404


class VideoDownloadError(LearningAssistantError):
    """
    视频下载失败.

    当视频下载过程中出现错误时抛出。

    可能原因：
    - 网络连接问题
    - 平台反爬虫机制
    - 需要登录（Cookie）

    解决方法：等待几秒后重试，或使用 cookie_file 参数。
    """

    is_retryable = True
    retry_after = 5
    retry_suggestion = "等待 5 秒后重试，或使用 cookie_file 参数"

    def to_http_status(self) -> int:
        """Return HTTP 502 Bad Gateway."""
        return 502


class TranscriptionError(LearningAssistantError):
    """
    语音转录失败.

    当音频转录过程中出现错误时抛出。

    可能原因：
    - ASR 服务不可用
    - 音频质量问题
    - 频率限制

    解决方法：等待几分钟后重试。
    """

    is_retryable = True
    retry_after = 3
    retry_suggestion = "等待 3 秒后重试，或检查音频质量"

    def to_http_status(self) -> int:
        """Return HTTP 503 Service Unavailable."""
        return 503


class LLMAPIError(LearningAssistantError):
    """
    LLM API 错误.

    当调用 LLM API 时出现错误时抛出。

    可能原因：
    - API Key 无效
    - API 限流
    - 网络问题
    - 模型不可用

    解决方法：
    - 检查 API Key 配置
    - 等待限流恢复
    - 使用其他 LLM 提供商
    """

    def __init__(self, message: str, is_rate_limit: bool = False):
        super().__init__(message)
        self.is_rate_limit = is_rate_limit
        if is_rate_limit:
            self.is_retryable = True
            self.retry_after = 60
            self.retry_suggestion = "API 限流，等待 60 秒后重试"
        else:
            self.is_retryable = False

    def to_http_status(self) -> int:
        """Return HTTP 502 Bad Gateway."""
        return 502


class ConfigError(LearningAssistantError):
    """配置错误。

    当配置文件格式错误或必需配置缺失时抛出。
    """

    is_retryable = False

    def to_http_status(self) -> int:
        """Return HTTP 500 Internal Server Error."""
        return 500


class HistoryError(LearningAssistantError):
    """历史记录错误。

    当读取或写入历史记录时出现错误时抛出。
    """

    is_retryable = False

    def to_http_status(self) -> int:
        """Return HTTP 500 Internal Server Error."""
        return 500
