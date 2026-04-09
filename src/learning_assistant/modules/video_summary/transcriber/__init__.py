"""
Transcriber Module for Learning Assistant.

This module provides ASR (Automatic Speech Recognition) capabilities.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .asr_data import ASRData, ASRDataSeg
from .bcut import BcutASR
from .status import ASRStatus


class AudioTranscriber:
    """
    Audio Transcriber using multiple ASR backends.

    Supports:
    - BcutASR (B站必剪, free online, Chinese/English)
    - FasterWhisperASR (local, multilingual)
    """

    # Available ASR engines
    AVAILABLE_ENGINES = ["bcut", "faster_whisper"]

    def __init__(
        self,
        engine: str = "bcut",
        use_cache: bool = True,
        need_word_time_stamp: bool = False,
        cache_dir: Path | None = None,
    ) -> None:
        """
        Initialize AudioTranscriber.

        Args:
            engine: ASR engine to use ('bcut' or 'faster_whisper')
            use_cache: Whether to cache recognition results
            need_word_time_stamp: Whether to return word-level timestamps
            cache_dir: Cache directory path
        """
        self.engine = engine
        self.use_cache = use_cache
        self.need_word_time_stamp = need_word_time_stamp
        self.cache_dir = cache_dir or Path("data/cache/asr")

        # Validate engine
        if engine not in self.AVAILABLE_ENGINES:
            logger.warning(f"Unknown engine: {engine}, using default 'bcut'")
            self.engine = "bcut"

        logger.info(
            f"AudioTranscriber initialized: engine={self.engine}, "
            f"word_timestamp={self.need_word_time_stamp}"
        )

    def transcribe(
        self,
        audio_input: str | bytes | Path,
        **kwargs: Any,
    ) -> ASRData:
        """
        Transcribe audio to text.

        Args:
            audio_input: Audio file path or raw audio bytes
            **kwargs: Additional arguments for ASR engine

        Returns:
            ASRData with transcription segments
        """
        logger.info(f"Transcribing audio using engine: {self.engine}")

        # Create ASR instance based on engine
        if self.engine == "bcut":
            asr = BcutASR(
                audio_input=audio_input,
                use_cache=self.use_cache,
                need_word_time_stamp=self.need_word_time_stamp,
                cache_dir=self.cache_dir,
            )
        else:
            # Fallback to BcutASR for now
            # TODO: Implement FasterWhisperASR
            logger.warning(f"Engine '{self.engine}' not yet implemented, using 'bcut'")
            asr = BcutASR(
                audio_input=audio_input,
                use_cache=self.use_cache,
                need_word_time_stamp=self.need_word_time_stamp,
                cache_dir=self.cache_dir,
            )

        # Run ASR
        asr_data = asr.run(**kwargs)

        logger.info(
            f"Transcription completed: {len(asr_data.segments)} segments, "
            f"{asr_data.get_word_count()} words"
        )

        return asr_data

    def transcribe_to_srt(
        self,
        audio_input: str | bytes | Path,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Transcribe audio and export to SRT format.

        Args:
            audio_input: Audio file path or raw audio bytes
            output_path: Output SRT file path (optional)
            **kwargs: Additional arguments for ASR engine

        Returns:
            SRT formatted string
        """
        asr_data = self.transcribe(audio_input, **kwargs)
        srt_content = asr_data.to_srt()

        if output_path:
            output_path.write_text(srt_content, encoding="utf-8")
            logger.info(f"SRT file saved: {output_path}")

        return srt_content

    def transcribe_to_vtt(
        self,
        audio_input: str | bytes | Path,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Transcribe audio and export to VTT format.

        Args:
            audio_input: Audio file path or raw audio bytes
            output_path: Output VTT file path (optional)
            **kwargs: Additional arguments for ASR engine

        Returns:
            VTT formatted string
        """
        asr_data = self.transcribe(audio_input, **kwargs)
        vtt_content = asr_data.to_vtt()

        if output_path:
            output_path.write_text(vtt_content, encoding="utf-8")
            logger.info(f"VTT file saved: {output_path}")

        return vtt_content

    def transcribe_to_lrc(
        self,
        audio_input: str | bytes | Path,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Transcribe audio and export to LRC format.

        Args:
            audio_input: Audio file path or raw audio bytes
            output_path: Output LRC file path (optional)
            **kwargs: Additional arguments for ASR engine

        Returns:
            LRC formatted string
        """
        asr_data = self.transcribe(audio_input, **kwargs)
        lrc_content = asr_data.to_lrc()

        if output_path:
            output_path.write_text(lrc_content, encoding="utf-8")
            logger.info(f"LRC file saved: {output_path}")

        return lrc_content


# Export public API
__all__ = [
    "AudioTranscriber",
    "ASRData",
    "ASRDataSeg",
    "ASRStatus",
    "BcutASR",
    "BaseASR",
]
