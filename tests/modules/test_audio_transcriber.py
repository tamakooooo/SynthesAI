"""
Unit tests for AudioTranscriber.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from learning_assistant.modules.video_summary.transcriber import AudioTranscriber
from learning_assistant.modules.video_summary.transcriber.asr_data import (
    ASRData,
    ASRDataSeg,
)


class TestAudioTranscriber:
    """Test AudioTranscriber class."""

    def test_init_default_engine(self) -> None:
        """Test initialization with default engine."""
        transcriber = AudioTranscriber()

        assert transcriber.engine == "bcut"
        assert transcriber.use_cache is True
        assert transcriber.need_word_time_stamp is False

    def test_init_custom_engine(self) -> None:
        """Test initialization with custom engine."""
        transcriber = AudioTranscriber(
            engine="faster_whisper",
            use_cache=False,
            need_word_time_stamp=True,
        )

        assert transcriber.engine == "faster_whisper"
        assert transcriber.use_cache is False
        assert transcriber.need_word_time_stamp is True

    def test_init_unknown_engine(self) -> None:
        """Test initialization with unknown engine defaults to 'bcut'."""
        transcriber = AudioTranscriber(engine="unknown_engine")

        assert transcriber.engine == "bcut"

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_with_bcut(self, mock_run: Mock) -> None:
        """Test transcription with BcutASR."""
        # Mock ASR result
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Hello world", start_time=0, end_time=1000),
            ]
        )
        mock_run.return_value = asr_data

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            audio_file.write_bytes(b"fake audio")

            transcriber = AudioTranscriber(engine="bcut")
            result = transcriber.transcribe(audio_file)

        assert len(result.segments) == 1
        assert result.segments[0].text == "Hello world"

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_to_srt(self, mock_run: Mock) -> None:
        """Test transcription to SRT format."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Hello", start_time=0, end_time=1000),
                ASRDataSeg(text="World", start_time=1000, end_time=2000),
            ]
        )
        mock_run.return_value = asr_data

        transcriber = AudioTranscriber()
        srt = transcriber.transcribe_to_srt(b"fake audio")

        assert "1" in srt
        assert "00:00:00,000 --> 00:00:01,000" in srt
        assert "Hello" in srt
        assert "2" in srt
        assert "World" in srt

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_to_srt_with_file(self, mock_run: Mock) -> None:
        """Test transcription to SRT file."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Test", start_time=0, end_time=1000),
            ]
        )
        mock_run.return_value = asr_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.srt"

            transcriber = AudioTranscriber()
            transcriber.transcribe_to_srt(b"fake audio", output_file)

            assert output_file.exists()
            assert "Test" in output_file.read_text()

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_to_vtt(self, mock_run: Mock) -> None:
        """Test transcription to VTT format."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Test", start_time=0, end_time=1000),
            ]
        )
        mock_run.return_value = asr_data

        transcriber = AudioTranscriber()
        vtt = transcriber.transcribe_to_vtt(b"fake audio")

        assert vtt.startswith("WEBVTT")
        assert "Test" in vtt

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_to_vtt_with_file(self, mock_run: Mock) -> None:
        """Test transcription to VTT file."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Test", start_time=0, end_time=1000),
            ]
        )
        mock_run.return_value = asr_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.vtt"

            transcriber = AudioTranscriber()
            transcriber.transcribe_to_vtt(b"fake audio", output_file)

            assert output_file.exists()
            assert "WEBVTT" in output_file.read_text()

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_to_lrc(self, mock_run: Mock) -> None:
        """Test transcription to LRC format."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Test", start_time=125000, end_time=130000),
            ]
        )
        mock_run.return_value = asr_data

        transcriber = AudioTranscriber()
        lrc = transcriber.transcribe_to_lrc(b"fake audio")

        assert "[02:05.00]Test" in lrc

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_to_lrc_with_file(self, mock_run: Mock) -> None:
        """Test transcription to LRC file."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Test", start_time=125000, end_time=130000),
            ]
        )
        mock_run.return_value = asr_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.lrc"

            transcriber = AudioTranscriber()
            transcriber.transcribe_to_lrc(b"fake audio", output_file)

            assert output_file.exists()
            assert "[02:05.00]" in output_file.read_text()

    def test_available_engines(self) -> None:
        """Test available engines list."""
        transcriber = AudioTranscriber()

        assert "bcut" in transcriber.AVAILABLE_ENGINES
        assert "faster_whisper" in transcriber.AVAILABLE_ENGINES


class TestAudioTranscriberIntegration:
    """Test AudioTranscriber integration scenarios."""

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_full_transcription_workflow(self, mock_run: Mock) -> None:
        """Test full transcription workflow."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="First sentence", start_time=0, end_time=2000),
                ASRDataSeg(text="Second sentence", start_time=2000, end_time=4000),
                ASRDataSeg(text="Third sentence", start_time=4000, end_time=6000),
            ]
        )
        mock_run.return_value = asr_data

        transcriber = AudioTranscriber(engine="bcut")

        # Transcribe
        result = transcriber.transcribe(b"fake audio")

        assert len(result.segments) == 3
        assert result.get_word_count() > 0
        assert result.has_text()

        # Export to different formats
        srt = transcriber.transcribe_to_srt(b"fake audio")
        vtt = transcriber.transcribe_to_vtt(b"fake audio")
        lrc = transcriber.transcribe_to_lrc(b"fake audio")

        assert "First sentence" in srt
        assert "WEBVTT" in vtt
        assert "sentence" in lrc

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_with_word_timestamps(self, mock_run: Mock) -> None:
        """Test transcription with word-level timestamps."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Hello", start_time=0, end_time=500),
                ASRDataSeg(text="world", start_time=500, end_time=1000),
            ]
        )
        mock_run.return_value = asr_data

        transcriber = AudioTranscriber(need_word_time_stamp=True)
        result = transcriber.transcribe(b"fake audio")

        assert len(result.segments) == 2
        assert result.segments[0].text == "Hello"
        assert result.segments[1].text == "world"

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_with_cache(self, mock_run: Mock) -> None:
        """Test transcription with caching enabled."""
        asr_data = ASRData(
            segments=[
                ASRDataSeg(text="Test", start_time=0, end_time=1000),
            ]
        )
        mock_run.return_value = asr_data

        transcriber = AudioTranscriber(use_cache=True)

        # First transcription
        result1 = transcriber.transcribe(b"fake audio")

        # Second transcription (should use cache)
        result2 = transcriber.transcribe(b"fake audio")

        assert result1.segments[0].text == "Test"
        assert result2.segments[0].text == "Test"


class TestAudioTranscriberErrorHandling:
    """Test AudioTranscriber error handling."""

    def test_transcribe_invalid_input(self) -> None:
        """Test transcription with invalid input."""
        transcriber = AudioTranscriber()

        with pytest.raises(ValueError):
            transcriber.transcribe(None)

    @patch("learning_assistant.modules.video_summary.transcriber.BcutASR.run")
    def test_transcribe_asr_failure(self, mock_run: Mock) -> None:
        """Test transcription when ASR fails."""
        mock_run.side_effect = RuntimeError("ASR service failed")

        transcriber = AudioTranscriber()

        with pytest.raises(RuntimeError, match="ASR service failed"):
            transcriber.transcribe(b"fake audio")
