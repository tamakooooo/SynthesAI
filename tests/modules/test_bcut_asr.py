"""
Unit tests for BcutASR.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from learning_assistant.modules.video_summary.transcriber.bcut import BcutASR
from learning_assistant.modules.video_summary.transcriber.status import ASRStatus


class TestBcutASR:
    """Test BcutASR class."""

    @patch("requests.Session")
    @patch("requests.post")
    def test_init_with_file_path(self, mock_post: Mock, mock_session: Mock) -> None:
        """Test initialization with audio file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            audio_file.write_bytes(b"fake audio data")

            bcut_asr = BcutASR(audio_input=audio_file)

            assert bcut_asr.audio_input == audio_file
            assert bcut_asr.file_binary == b"fake audio data"
            assert bcut_asr.use_cache is True
            assert bcut_asr.need_word_time_stamp is False

    @patch("requests.Session")
    def test_init_with_bytes(self, mock_session: Mock) -> None:
        """Test initialization with raw audio bytes."""
        audio_bytes = b"fake audio data"

        bcut_asr = BcutASR(audio_input=audio_bytes)

        assert bcut_asr.audio_input == audio_bytes
        assert bcut_asr.file_binary == audio_bytes

    @patch("requests.Session")
    def test_init_invalid_format(self, mock_session: Mock) -> None:
        """Test initialization with unsupported format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.xyz"
            audio_file.write_bytes(b"fake data")

            with pytest.raises(ValueError, match="Unsupported sound format"):
                BcutASR(audio_input=audio_file)

    @patch("requests.Session")
    def test_init_file_not_found(self, mock_session: Mock) -> None:
        """Test initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            BcutASR(audio_input="nonexistent.mp3")

    @patch("requests.Session")
    @patch("requests.post")
    def test_crc32_calculation(self, mock_post: Mock, mock_session: Mock) -> None:
        """Test CRC32 hash calculation."""
        audio_bytes = b"test audio data"

        bcut_asr = BcutASR(audio_input=audio_bytes)

        # CRC32 should be calculated
        assert bcut_asr.crc32_hex is not None
        assert len(bcut_asr.crc32_hex) == 8

    @patch("requests.Session")
    @patch("pydub.AudioSegment.from_file")
    def test_get_audio_duration(self, mock_audio: Mock, mock_session: Mock) -> None:
        """Test audio duration calculation."""
        mock_audio_segment = MagicMock()
        mock_audio_segment.duration_seconds = 120.5
        mock_audio.return_value = mock_audio_segment

        audio_bytes = b"fake audio data"
        bcut_asr = BcutASR(audio_input=audio_bytes)

        assert bcut_asr.audio_duration == 120.5

    @patch("requests.Session")
    @patch.object(BcutASR, "_check_rate_limit")
    @patch("requests.post")
    @patch("requests.put")
    @patch("requests.get")
    def test_upload_workflow(
        self,
        mock_get: Mock,
        mock_put: Mock,
        mock_post: Mock,
        mock_rate_limit: Mock,
        mock_session: Mock,
    ) -> None:
        """Test upload workflow."""
        # Mock upload authorization
        mock_post.return_value = Mock(
            json=lambda: {
                "data": {
                    "in_boss_key": "test_key",
                    "resource_id": "test_resource",
                    "upload_id": "test_upload_id",
                    "upload_urls": ["http://upload.url"],
                    "per_size": 1000,
                }
            },
            raise_for_status=lambda: None,
        )

        # Mock upload part
        mock_put.return_value = Mock(
            headers={"Etag": "test_etag"},
            raise_for_status=lambda: None,
        )

        # Mock commit upload
        mock_post.side_effect = [
            # First call: upload authorization
            Mock(
                json=lambda: {
                    "data": {
                        "in_boss_key": "test_key",
                        "resource_id": "test_resource",
                        "upload_id": "test_upload_id",
                        "upload_urls": ["http://upload.url"],
                        "per_size": 1000,
                    }
                },
                raise_for_status=lambda: None,
            ),
            # Second call: commit upload
            Mock(
                json=lambda: {"data": {"download_url": "http://download.url"}},
                raise_for_status=lambda: None,
            ),
        ]

        audio_bytes = b"fake audio data"
        bcut_asr = BcutASR(audio_input=audio_bytes)

        bcut_asr.upload()

        assert bcut_asr._BcutASR__in_boss_key == "test_key"
        assert bcut_asr._BcutASR__download_url == "http://download.url"

    @patch("requests.Session")
    @patch.object(BcutASR, "_check_rate_limit")
    @patch("requests.post")
    @patch("requests.put")
    @patch("requests.get")
    def test_create_task(
        self,
        mock_get: Mock,
        mock_put: Mock,
        mock_post: Mock,
        mock_rate_limit: Mock,
        mock_session: Mock,
    ) -> None:
        """Test task creation."""
        # Mock task creation
        mock_post.return_value = Mock(
            json=lambda: {"data": {"task_id": "test_task_123"}},
            raise_for_status=lambda: None,
        )

        audio_bytes = b"fake audio data"
        bcut_asr = BcutASR(audio_input=audio_bytes)

        task_id = bcut_asr.create_task()

        assert task_id == "test_task_123"
        assert bcut_asr.task_id == "test_task_123"

    @patch("requests.Session")
    def test_result_query(self, mock_session: Mock) -> None:
        """Test result query."""
        mock_get = Mock(
            return_value=Mock(
                json=lambda: {
                    "data": {
                        "state": 4,
                        "result": json.dumps(
                            {
                                "utterances": [
                                    {
                                        "transcript": "Hello world",
                                        "start_time": 0,
                                        "end_time": 1000,
                                    }
                                ]
                            }
                        ),
                    }
                },
                raise_for_status=lambda: None,
            )
        )

        audio_bytes = b"fake audio data"
        bcut_asr = BcutASR(audio_input=audio_bytes)

        # Mock upload and task creation
        bcut_asr._BcutASR__download_url = "http://test.url"
        bcut_asr.task_id = "test_task"

        with patch("requests.get", mock_get):
            result = bcut_asr.result()

        assert result["state"] == 4

    def test_make_segments_sentence_level(self) -> None:
        """Test segment creation at sentence level."""
        audio_bytes = b"fake audio"
        bcut_asr = BcutASR(audio_input=audio_bytes, need_word_time_stamp=False)

        resp_data = {
            "utterances": [
                {
                    "transcript": "Hello world",
                    "start_time": 0,
                    "end_time": 1000,
                },
                {
                    "transcript": "Test sentence",
                    "start_time": 1000,
                    "end_time": 2000,
                },
            ]
        }

        segments = bcut_asr._make_segments(resp_data)

        assert len(segments) == 2
        assert segments[0].text == "Hello world"
        assert segments[0].start_time == 0
        assert segments[1].text == "Test sentence"

    def test_make_segments_word_level(self) -> None:
        """Test segment creation at word level."""
        audio_bytes = b"fake audio"
        bcut_asr = BcutASR(audio_input=audio_bytes, need_word_time_stamp=True)

        resp_data = {
            "utterances": [
                {
                    "words": [
                        {
                            "label": "Hello",
                            "start_time": 0,
                            "end_time": 500,
                        },
                        {
                            "label": "world",
                            "start_time": 500,
                            "end_time": 1000,
                        },
                    ]
                }
            ]
        }

        segments = bcut_asr._make_segments(resp_data)

        assert len(segments) == 2
        assert segments[0].text == "Hello"
        assert segments[1].text == "world"

    def test_status_callback_tuple(self) -> None:
        """Test ASRStatus callback tuple."""
        uploading_tuple = ASRStatus.UPLOADING.callback_tuple()
        assert uploading_tuple[0] == 10
        assert "上传" in uploading_tuple[1]

        completed_tuple = ASRStatus.COMPLETED.callback_tuple()
        assert completed_tuple[0] == 100
        assert "完成" in completed_tuple[1]


class TestBcutASRIntegration:
    """Test BcutASR integration scenarios."""

    @patch("requests.Session")
    @patch(
        "learning_assistant.modules.video_summary.transcriber.base.BaseASR._load_from_cache"
    )
    def test_cache_hit(
        self,
        mock_cache: Mock,
        mock_session: Mock,
    ) -> None:
        """Test cache hit scenario."""
        # Mock cached result
        cached_result = {
            "utterances": [
                {
                    "transcript": "Cached text",
                    "start_time": 0,
                    "end_time": 1000,
                }
            ]
        }
        mock_cache.return_value = cached_result

        audio_bytes = b"fake audio"
        bcut_asr = BcutASR(audio_input=audio_bytes, use_cache=True)

        # Run ASR (should return cached result)
        asr_data = bcut_asr.run()

        assert len(asr_data.segments) == 1
        assert asr_data.segments[0].text == "Cached text"

    @patch("requests.Session")
    def test_rate_limit_exceeded(self, mock_session: Mock) -> None:
        """Test rate limit exceeded error."""
        audio_bytes = b"fake audio"
        bcut_asr = BcutASR(audio_input=audio_bytes)

        # Mock rate limit check to raise error
        with patch.object(
            bcut_asr,
            "_check_rate_limit",
            side_effect=RuntimeError("duration limit exceeded"),
        ):
            with pytest.raises(RuntimeError, match="duration limit exceeded"):
                bcut_asr.run()


class TestBcutASRErrorHandling:
    """Test BcutASR error handling."""

    @patch("requests.Session")
    def test_empty_audio_data(self, mock_session: Mock) -> None:
        """Test empty audio data error."""
        with pytest.raises(ValueError, match="audio_input must be provided"):
            BcutASR(audio_input=None)

    @patch("requests.Session")
    @patch("requests.post")
    def test_upload_failure(self, mock_post: Mock, mock_session: Mock) -> None:
        """Test upload failure."""
        mock_post.side_effect = RuntimeError("Upload failed")

        audio_bytes = b"fake audio"
        bcut_asr = BcutASR(audio_input=audio_bytes)

        with pytest.raises(RuntimeError):
            bcut_asr.upload()

    @patch("requests.Session")
    @patch("requests.get")
    def test_task_timeout(self, mock_get: Mock, mock_session: Mock) -> None:
        """Test task timeout error."""
        # Mock task never completes
        mock_get.return_value = Mock(
            json=lambda: {"data": {"state": 1, "result": ""}},  # Not completed
            raise_for_status=lambda: None,
        )

        audio_bytes = b"fake audio"
        bcut_asr = BcutASR(audio_input=audio_bytes)
        bcut_asr._BcutASR__download_url = "http://test.url"
        bcut_asr.task_id = "test_task"

        with pytest.raises(RuntimeError, match="timeout"):
            bcut_asr._run()

    @patch("requests.Session")
    def test_empty_result(self, mock_session: Mock) -> None:
        """Test empty ASR result."""
        audio_bytes = b"fake audio"
        bcut_asr = BcutASR(audio_input=audio_bytes)

        resp_data = {"utterances": []}
        segments = bcut_asr._make_segments(resp_data)

        assert len(segments) == 0
