"""
Unit tests for ASR Data Structures.
"""


from learning_assistant.modules.video_summary.transcriber.asr_data import (
    ASRData,
    ASRDataSeg,
)


class TestASRDataSeg:
    """Test ASRDataSeg dataclass."""

    def test_create_segment(self) -> None:
        """Test creating ASRDataSeg instance."""
        seg = ASRDataSeg(
            text="Hello world",
            start_time=1000,
            end_time=3000,
        )

        assert seg.text == "Hello world"
        assert seg.start_time == 1000
        assert seg.end_time == 3000
        assert seg.translated_text == ""

    def test_transcript_property(self) -> None:
        """Test transcript property."""
        seg = ASRDataSeg(text="Test text", start_time=0, end_time=1000)
        assert seg.transcript == "Test text"

    def test_duration_property(self) -> None:
        """Test duration property."""
        seg = ASRDataSeg(text="Test", start_time=1000, end_time=5000)
        assert seg.duration == 4000

    def test_to_srt_ts(self) -> None:
        """Test SRT timestamp format."""
        seg = ASRDataSeg(text="Test", start_time=1234567, end_time=1244567)
        srt_ts = seg.to_srt_ts()
        assert srt_ts == "00:20:34,567 --> 00:20:44,567"

    def test_to_vtt_ts(self) -> None:
        """Test VTT timestamp format."""
        seg = ASRDataSeg(text="Test", start_time=1234567, end_time=1244567)
        vtt_ts = seg.to_vtt_ts()
        assert vtt_ts == "00:20:34.567 --> 00:20:44.567"

    def test_to_lrc_ts(self) -> None:
        """Test LRC timestamp format."""
        seg = ASRDataSeg(text="Test", start_time=125000, end_time=130000)
        lrc_ts = seg.to_lrc_ts()
        assert lrc_ts == "[02:05.00]"

    def test_to_ass_ts(self) -> None:
        """Test ASS timestamp format."""
        seg = ASRDataSeg(text="Test", start_time=1234567, end_time=1244567)
        ass_ts_start, ass_ts_end = seg.to_ass_ts()
        assert ass_ts_start == "0:20:34.56"
        assert ass_ts_end == "0:20:44.56"

    def test_translated_text(self) -> None:
        """Test translated text field."""
        seg = ASRDataSeg(
            text="你好",
            start_time=0,
            end_time=1000,
            translated_text="Hello",
        )
        assert seg.translated_text == "Hello"


class TestASRData:
    """Test ASRData dataclass."""

    def test_create_asr_data(self) -> None:
        """Test creating ASRData instance."""
        segments = [
            ASRDataSeg(text="Hello", start_time=0, end_time=1000),
            ASRDataSeg(text="World", start_time=1000, end_time=2000),
        ]
        asr_data = ASRData(segments=segments)

        assert len(asr_data.segments) == 2
        assert asr_data.segments[0].text == "Hello"
        assert asr_data.segments[1].text == "World"

    def test_empty_asr_data(self) -> None:
        """Test empty ASRData."""
        asr_data = ASRData(segments=[])
        assert len(asr_data.segments) == 0
        assert not asr_data.has_text()

    def test_to_srt(self) -> None:
        """Test SRT format output."""
        segments = [
            ASRDataSeg(text="Hello", start_time=0, end_time=1000),
            ASRDataSeg(text="World", start_time=1000, end_time=2000),
        ]
        asr_data = ASRData(segments=segments)
        srt = asr_data.to_srt()

        lines = srt.split("\n")
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:01,000"
        assert lines[2] == "Hello"
        assert lines[4] == "2"
        assert lines[5] == "00:00:01,000 --> 00:00:02,000"
        assert lines[6] == "World"

    def test_to_vtt(self) -> None:
        """Test VTT format output."""
        segments = [
            ASRDataSeg(text="Test", start_time=0, end_time=1000),
        ]
        asr_data = ASRData(segments=segments)
        vtt = asr_data.to_vtt()

        assert vtt.startswith("WEBVTT")
        assert "\n1" in vtt
        assert "00:00:00.000 --> 00:00:01.000" in vtt
        assert "Test" in vtt

    def test_to_lrc(self) -> None:
        """Test LRC format output."""
        segments = [
            ASRDataSeg(text="Hello", start_time=125000, end_time=130000),
        ]
        asr_data = ASRData(segments=segments)
        lrc = asr_data.to_lrc()

        assert "[02:05.00]Hello" in lrc

    def test_to_txt(self) -> None:
        """Test plain text format output."""
        segments = [
            ASRDataSeg(text="Hello", start_time=0, end_time=1000),
            ASRDataSeg(text="World", start_time=1000, end_time=2000),
        ]
        asr_data = ASRData(segments=segments)
        txt = asr_data.to_txt()

        assert txt == "Hello\nWorld"

    def test_has_text(self) -> None:
        """Test has_text method."""
        # Empty segments
        asr_data_empty = ASRData(segments=[])
        assert not asr_data_empty.has_text()

        # Segments with text
        segments = [ASRDataSeg(text="Test", start_time=0, end_time=1000)]
        asr_data = ASRData(segments=segments)
        assert asr_data.has_text()

        # Segments with empty text
        segments_empty_text = [ASRDataSeg(text="", start_time=0, end_time=1000)]
        asr_data_empty_text = ASRData(segments=segments_empty_text)
        assert not asr_data_empty_text.has_text()

    def test_get_word_count(self) -> None:
        """Test word count calculation."""
        # English text
        segments = [ASRDataSeg(text="Hello world test", start_time=0, end_time=1000)]
        asr_data = ASRData(segments=segments)
        assert asr_data.get_word_count() == 3

        # Chinese text (你好世界测试 = 6 characters)
        segments_chinese = [
            ASRDataSeg(text="你好世界测试", start_time=0, end_time=1000)
        ]
        asr_data_chinese = ASRData(segments=segments_chinese)
        assert asr_data_chinese.get_word_count() == 6

        # Mixed text
        segments_mixed = [ASRDataSeg(text="Hello 世界", start_time=0, end_time=1000)]
        asr_data_mixed = ASRData(segments=segments_mixed)
        assert asr_data_mixed.get_word_count() == 3

    def test_get_total_duration(self) -> None:
        """Test total duration calculation."""
        segments = [
            ASRDataSeg(text="Hello", start_time=1000, end_time=2000),
            ASRDataSeg(text="World", start_time=2000, end_time=4000),
        ]
        asr_data = ASRData(segments=segments)
        duration = asr_data.get_total_duration()
        assert duration == 3000  # 4000 - 1000

    def test_merge_segments(self) -> None:
        """Test segment merging."""
        segments = [
            ASRDataSeg(text="Hello", start_time=0, end_time=1000),
            ASRDataSeg(text="World", start_time=1100, end_time=2000),  # Gap = 100ms
        ]
        asr_data = ASRData(segments=segments)

        # Merge with default gap (500ms)
        merged = asr_data.merge_segments()
        assert len(merged.segments) == 1
        assert merged.segments[0].text == "Hello World"
        assert merged.segments[0].start_time == 0
        assert merged.segments[0].end_time == 2000

        # Merge with custom gap (50ms)
        merged_small_gap = asr_data.merge_segments(max_gap_ms=50)
        assert len(merged_small_gap.segments) == 2  # Not merged


class TestASRDataSegTimestamps:
    """Test timestamp conversion edge cases."""

    def test_zero_timestamp(self) -> None:
        """Test zero timestamp."""
        seg = ASRDataSeg(text="Test", start_time=0, end_time=0)
        assert seg.to_srt_ts() == "00:00:00,000 --> 00:00:00,000"
        assert seg.duration == 0

    def test_large_timestamp(self) -> None:
        """Test large timestamp (hours)."""
        seg = ASRDataSeg(text="Test", start_time=0, end_time=7200000)  # 2 hours
        srt_ts = seg.to_srt_ts()
        assert srt_ts == "00:00:00,000 --> 02:00:00,000"

    def test_millisecond_precision(self) -> None:
        """Test millisecond precision."""
        seg = ASRDataSeg(text="Test", start_time=999, end_time=1234)
        srt_ts = seg.to_srt_ts()
        assert "00:00:00,999 --> 00:00:01,234" == srt_ts

    def test_centisecond_precision_ass(self) -> None:
        """Test centisecond precision for ASS."""
        seg = ASRDataSeg(text="Test", start_time=1234, end_time=5678)
        start, end = seg.to_ass_ts()
        assert start == "0:00:01.23"  # Truncated to centiseconds
        assert end == "0:00:05.67"
