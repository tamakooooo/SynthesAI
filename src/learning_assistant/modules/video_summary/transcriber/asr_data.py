"""
ASR Data Structures for Learning Assistant.

This module defines data structures for ASR (Automatic Speech Recognition) results.
"""

import re
from dataclasses import dataclass, field


@dataclass
class ASRDataSeg:
    """
    ASR segment data structure.

    Represents a single segment of transcribed text with timestamps.
    """

    text: str
    start_time: int  # milliseconds
    end_time: int  # milliseconds
    translated_text: str = ""

    def to_srt_ts(self) -> str:
        """Convert to SRT timestamp format (HH:MM:SS,mmm --> HH:MM:SS,mmm)."""
        return f"{self._ms_to_srt_time(self.start_time)} --> {self._ms_to_srt_time(self.end_time)}"

    def to_lrc_ts(self) -> str:
        """Convert to LRC timestamp format ([MM:SS.cc])."""
        return f"[{self._ms_to_lrc_time(self.start_time)}]"

    def to_vtt_ts(self) -> str:
        """Convert to VTT timestamp format (HH:MM:SS.mmm --> HH:MM:SS.mmm)."""
        return f"{self._ms_to_vtt_time(self.start_time)} --> {self._ms_to_vtt_time(self.end_time)}"

    def to_ass_ts(self) -> tuple[str, str]:
        """Convert to ASS timestamp format (H:MM:SS.cc, H:MM:SS.cc)."""
        return self._ms_to_ass_ts(self.start_time), self._ms_to_ass_ts(self.end_time)

    @staticmethod
    def _ms_to_lrc_time(ms: int) -> str:
        """Convert milliseconds to LRC time format (MM:SS.cc)."""
        seconds = ms / 1000
        minutes, seconds = divmod(seconds, 60)
        # Format: MM:SS.cc where SS has leading zero
        return f"{int(minutes):02}:{seconds:05.2f}"

    @staticmethod
    def _ms_to_srt_time(ms: int) -> str:
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}"

    @staticmethod
    def _ms_to_vtt_time(ms: int) -> str:
        """Convert milliseconds to VTT time format (HH:MM:SS.mmm)."""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{int(milliseconds):03}"

    @staticmethod
    def _ms_to_ass_ts(ms: int) -> str:
        """Convert milliseconds to ASS timestamp format (H:MM:SS.cc)."""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        centiseconds = int(milliseconds / 10)
        return f"{int(hours):01}:{int(minutes):02}:{int(seconds):02}.{centiseconds:02}"

    @property
    def transcript(self) -> str:
        """Return segment text."""
        return self.text

    @property
    def duration(self) -> int:
        """Return segment duration in milliseconds."""
        return self.end_time - self.start_time


# Multilingual word split pattern
_WORD_SPLIT_PATTERN = (
    r"[a-zA-Z\u00c0-\u00ff\u0100-\u017f]+"  # Latin characters (extended)
    r"|[\u0400-\u04ff]+"  # Cyrillic (Russian)
    r"|[\u0370-\u03ff]+"  # Greek
    r"|[\u0600-\u06ff]+"  # Arabic
    r"|[\u0590-\u05ff]+"  # Hebrew
    r"|\d+"  # Numbers
    r"|[\u4e00-\u9fff]"  # Chinese
    r"|[\u3040-\u309f]"  # Japanese Hiragana
    r"|[\u30a0-\u30ff]"  # Japanese Katakana
    r"|[\uac00-\ud7af]"  # Korean
    r"|[\u0e00-\u0e7f][\u0e30-\u0e3a\u0e47-\u0e4e]*"  # Thai
    r"|[\u0900-\u097f]"  # Devanagari (Hindi)
    r"|[\u0980-\u09ff]"  # Bengali
    r"|[\u0e80-\u0eff]"  # Lao
    r"|[\u1000-\u109f]"  # Myanmar
)


@dataclass
class ASRData:
    """
    ASR data structure containing multiple segments.

    Provides methods to format and export transcription results.
    """

    segments: list[ASRDataSeg] = field(default_factory=list)

    def to_srt(self) -> str:
        """Convert to SRT subtitle format."""
        lines = []
        for i, seg in enumerate(self.segments, start=1):
            lines.append(str(i))
            lines.append(seg.to_srt_ts())
            lines.append(seg.text)
            lines.append("")
        return "\n".join(lines)

    def to_vtt(self) -> str:
        """Convert to VTT subtitle format."""
        lines = ["WEBVTT\n"]
        for i, seg in enumerate(self.segments, start=1):
            lines.append(f"\n{i}")
            lines.append(seg.to_vtt_ts())
            lines.append(seg.text)
        return "\n".join(lines)

    def to_lrc(self) -> str:
        """Convert to LRC subtitle format."""
        lines = []
        for seg in self.segments:
            lines.append(f"{seg.to_lrc_ts()}{seg.text}")
        return "\n".join(lines)

    def to_txt(self) -> str:
        """Convert to plain text format."""
        return "\n".join(seg.text for seg in self.segments)

    def has_text(self) -> bool:
        """Check if transcription contains any text."""
        return len(self.segments) > 0 and any(seg.text.strip() for seg in self.segments)

    def get_word_count(self) -> int:
        """Get total word count of transcription."""
        text = " ".join(seg.text for seg in self.segments)
        words = re.findall(_WORD_SPLIT_PATTERN, text)
        return len(words)

    def get_total_duration(self) -> int:
        """Get total duration in milliseconds."""
        if not self.segments:
            return 0
        return max(seg.end_time for seg in self.segments) - min(
            seg.start_time for seg in self.segments
        )

    def merge_segments(self, max_gap_ms: int = 500) -> "ASRData":
        """Merge segments with small gaps.

        Args:
            max_gap_ms: Maximum gap in milliseconds to merge

        Returns:
            New ASRData with merged segments
        """
        if len(self.segments) < 2:
            return ASRData(segments=self.segments.copy())

        merged = [self.segments[0]]
        for seg in self.segments[1:]:
            last_seg = merged[-1]
            gap = seg.start_time - last_seg.end_time
            if gap <= max_gap_ms:
                # Merge segments
                merged[-1] = ASRDataSeg(
                    text=last_seg.text + " " + seg.text,
                    start_time=last_seg.start_time,
                    end_time=seg.end_time,
                )
            else:
                merged.append(seg)

        return ASRData(segments=merged)
