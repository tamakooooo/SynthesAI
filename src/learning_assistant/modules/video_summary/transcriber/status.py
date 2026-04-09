"""
ASR Status Enums for Learning Assistant.

This module defines status codes and messages for ASR progress tracking.
"""

from enum import IntEnum


class ASRStatus(IntEnum):
    """
    ASR status codes.

    Used for progress callback to track transcription workflow.
    """

    UPLOADING = 10
    CREATING_TASK = 20
    TRANSCRIBING = 30
    COMPLETED = 100
    FAILED = -1

    def callback_tuple(self) -> tuple[int, str]:
        """Get status code and message for callback.

        Returns:
            Tuple of (status_code, status_message)
        """
        status_messages = {
            ASRStatus.UPLOADING: "正在上传音频文件...",
            ASRStatus.CREATING_TASK: "正在创建转录任务...",
            ASRStatus.TRANSCRIBING: "正在进行语音转录...",
            ASRStatus.COMPLETED: "转录完成",
            ASRStatus.FAILED: "转录失败",
        }
        return self, status_messages.get(self, "未知状态")
