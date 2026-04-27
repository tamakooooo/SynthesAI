"""
Bcut ASR Implementation for Learning Assistant.

This module provides ASR using Bilibili's Bcut (必剪) cloud service.
Free online ASR service with high accuracy for Chinese and English.
"""

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]
from loguru import logger

from .asr_data import ASRDataSeg
from .base import BaseASR
from .status import ASRStatus

# API endpoints for Bcut ASR
API_BASE_URL = "https://member.bilibili.com/x/bcut/rubick-interface"
API_REQ_UPLOAD = API_BASE_URL + "/resource/create"
API_COMMIT_UPLOAD = API_BASE_URL + "/resource/create/complete"
API_CREATE_TASK = API_BASE_URL + "/task"
API_QUERY_RESULT = API_BASE_URL + "/task/result"


class BcutASR(BaseASR):
    """
    Bilibili Bcut ASR API implementation.

    Uses Bilibili's cloud ASR service with multipart upload support.
    Free, high-accuracy transcription for Chinese and English audio.

    Note: This is a free public service with rate limiting.
    Supports only Chinese and English languages.
    """

    # Network request timeout (seconds)
    REQUEST_TIMEOUT = 60  # Increased from 30 to handle network instability
    # Max polling attempts (increased for longer videos)
    MAX_POLL_RETRIES = 300  # 5 minutes max
    # Poll interval (seconds)
    POLL_INTERVAL = 1

    headers = {
        "User-Agent": "Bilibili/1.0.0 (https://www.bilibili.com)",
        "Content-Type": "application/json",
    }

    def __init__(
        self,
        audio_input: str | bytes | Path | None = None,
        use_cache: bool = True,
        need_word_time_stamp: bool = False,
        cache_dir: Path | None = None,
    ) -> None:
        """
        Initialize BcutASR.

        Args:
            audio_input: Path to audio file or raw audio bytes
            use_cache: Whether to cache recognition results
            need_word_time_stamp: Whether to return word-level timestamps
            cache_dir: Cache directory path
        """
        super().__init__(
            audio_input=audio_input,
            use_cache=use_cache,
            need_word_time_stamp=need_word_time_stamp,
            cache_dir=cache_dir,
        )

        self.session = requests.Session()
        self.task_id: str | None = None

        # Upload state
        self.__in_boss_key: str | None = None
        self.__resource_id: str | None = None
        self.__upload_id: str | None = None
        self.__upload_urls: list[str] = []
        self.__per_size: int | None = None
        self.__clips: int | None = None
        self.__etags: list[str] = []
        self.__download_url: str | None = None

        logger.info("BcutASR initialized (B站必剪语音识别)")

    def upload(self) -> None:
        """
        Request upload authorization and upload audio file.

        Uses multipart upload for large files.
        """
        if not self.file_binary:
            raise ValueError("No audio data to upload")

        logger.info(f"Uploading audio file: size={len(self.file_binary)} bytes")

        # Request upload authorization
        payload = json.dumps(
            {
                "type": 2,
                "name": "audio.mp3",
                "size": len(self.file_binary),
                "ResourceFileType": "mp3",
                "model_id": "8",
            }
        )

        resp = requests.post(API_REQ_UPLOAD, data=payload, headers=self.headers, timeout=self.REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp_data = resp.json()["data"]

        # Extract upload parameters
        self.__in_boss_key = resp_data["in_boss_key"]
        self.__resource_id = resp_data["resource_id"]
        self.__upload_id = resp_data["upload_id"]
        self.__upload_urls = resp_data["upload_urls"]
        self.__per_size = resp_data["per_size"]
        self.__clips = len(resp_data["upload_urls"])

        logger.debug(
            f"Upload authorized: clips={self.__clips}, per_size={self.__per_size}"
        )

        # Upload parts
        self.__upload_part()

        # Commit upload
        self.__commit_upload()

    def __upload_part(self) -> None:
        """
        Upload audio data in multiple parts.
        """
        if (
            self.__clips is None
            or self.__per_size is None
            or self.__upload_urls is None
            or self.file_binary is None
        ):
            raise ValueError("Upload parameters not initialized")

        logger.info(f"Uploading {self.__clips} parts...")

        for clip_idx in range(self.__clips):
            start_range = clip_idx * self.__per_size
            end_range = (clip_idx + 1) * self.__per_size

            logger.debug(
                f"Uploading part {clip_idx + 1}: bytes {start_range}-{end_range}"
            )

            resp = requests.put(
                self.__upload_urls[clip_idx],
                data=self.file_binary[start_range:end_range],
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()

            etag = resp.headers.get("Etag")
            if etag is not None:
                self.__etags.append(etag)

        logger.info(f"Upload complete: {len(self.__etags)} parts uploaded")

    def __commit_upload(self) -> None:
        """
        Commit the upload and get download URL.
        """
        data = json.dumps(
            {
                "InBossKey": self.__in_boss_key,
                "ResourceId": self.__resource_id,
                "Etags": ",".join(self.__etags) if self.__etags else "",
                "UploadId": self.__upload_id,
                "model_id": "8",
            }
        )

        resp = requests.post(API_COMMIT_UPLOAD, data=data, headers=self.headers, timeout=self.REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp_data = resp.json()["data"]

        self.__download_url = resp_data["download_url"]

        logger.debug(f"Upload committed: download_url={self.__download_url}")

    def create_task(self) -> str:
        """
        Create ASR task.

        Returns:
            Task ID
        """
        resp = requests.post(
            API_CREATE_TASK,
            json={"resource": self.__download_url, "model_id": "8"},
            headers=self.headers,
            timeout=self.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        resp_data = resp.json()["data"]

        self.task_id = resp_data["task_id"]

        logger.info(f"ASR task created: task_id={self.task_id}")

        return self.task_id or ""

    def result(self, task_id: str | None = None) -> dict[str, Any]:
        """
        Query ASR result.

        Args:
            task_id: Task ID (uses self.task_id if None)

        Returns:
            ASR result data
        """
        resp = requests.get(
            API_QUERY_RESULT,
            params={"model_id": 7, "task_id": task_id or self.task_id},
            headers=self.headers,
            timeout=self.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        result_data: dict[str, Any] = resp.json()["data"]
        return result_data

    def _run(
        self,
        callback: Callable[[int, str], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute ASR workflow: upload -> create task -> poll result.

        Args:
            callback: Progress callback(progress: int, message: str)
            **kwargs: Additional arguments

        Returns:
            Raw ASR result data
        """
        # Check rate limit
        self._check_rate_limit()

        # Default callback
        def _default_callback(progress: int, message: str) -> None:
            logger.info(f"[{progress}%] {message}")

        if callback is None:
            callback = _default_callback

        # Step 1: Upload audio
        callback(*ASRStatus.UPLOADING.callback_tuple())
        self.upload()

        # Step 2: Create task
        callback(*ASRStatus.CREATING_TASK.callback_tuple())
        self.create_task()

        # Step 3: Transcribe (poll for result)
        callback(*ASRStatus.TRANSCRIBING.callback_tuple())

        logger.info("Polling for ASR result...")

        # Poll task status until complete
        task_resp = None
        max_retries = self.MAX_POLL_RETRIES
        poll_interval = self.POLL_INTERVAL

        for retry_idx in range(max_retries):
            task_resp = self.result()

            state = task_resp.get("state", -1)
            logger.debug(f"Poll attempt {retry_idx + 1}/{max_retries}: state={state}")

            if state == 4:  # Task completed
                logger.info(f"ASR task completed after {retry_idx + 1} polls")
                break

            # Log progress every 10 attempts
            if (retry_idx + 1) % 10 == 0:
                logger.info(f"Still processing... ({retry_idx + 1}/{max_retries})")

            time.sleep(poll_interval)

        # Check result
        if task_resp is None or task_resp.get("state") != 4:
            callback(*ASRStatus.FAILED.callback_tuple())
            raise RuntimeError(
                f"ASR task failed or timeout after {max_retries} attempts "
                f"({max_retries * poll_interval}s)"
            )

        # Parse result
        callback(*ASRStatus.COMPLETED.callback_tuple())

        result_str = task_resp.get("result", "")
        if not result_str:
            raise RuntimeError("ASR result is empty")

        result_data: dict[str, Any] = json.loads(result_str)

        logger.info(
            f"ASR completed: {len(result_data.get('utterances', []))} utterances"
        )

        return result_data

    def _make_segments(self, resp_data: dict[str, Any]) -> list[ASRDataSeg]:
        """
        Convert ASR response to segment list.

        Args:
            resp_data: Raw response from Bcut ASR service

        Returns:
            List of ASRDataSeg objects
        """
        utterances = resp_data.get("utterances", [])

        if self.need_word_time_stamp:
            # Word-level timestamps
            segments = []
            for utterance in utterances:
                words = utterance.get("words", [])
                for word in words:
                    segments.append(
                        ASRDataSeg(
                            text=word.get("label", "").strip(),
                            start_time=word.get("start_time", 0),
                            end_time=word.get("end_time", 0),
                        )
                    )
            return segments
        else:
            # Sentence-level timestamps
            segments = [
                ASRDataSeg(
                    text=utterance.get("transcript", "").strip(),
                    start_time=utterance.get("start_time", 0),
                    end_time=utterance.get("end_time", 0),
                )
                for utterance in utterances
            ]
            return segments
