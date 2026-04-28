"""
Transcriber Module for Learning Assistant.

This module provides ASR (Automatic Speech Recognition) capabilities.

Available Engines:
- videocaptioner: VideoCaptioner CLI (免费, 推荐)
  - bijian: B站必剪 (免费)
  - jianying: 剪映 (免费)
  - faster-whisper: 本地模型
- siliconcloud: 硅基流动 API (付费, 高质量)
  - TeleAI/TeleSpeechASR (默认)
  - FunAudioLLM/SenseVoiceSmall
- faster_whisper: 本地 Faster Whisper (免费)
"""

import os
from pathlib import Path
from typing import Any

from loguru import logger

from .asr_data import ASRData, ASRDataSeg
from .base import BaseASR
from .status import ASRStatus
from .videocaptioner_asr import VideoCaptionerASR
from .siliconcloud_asr import SiliconCloudASR


class AudioTranscriber:
    """
    Audio Transcriber using multiple ASR backends.

    Supports:
    - videocaptioner (VideoCaptioner CLI, 免费, 多种 ASR 引擎)
    - siliconcloud (硅基流动 API, 付费, 高质量)
    - faster_whisper (本地, multilingual)
    """

    # Available ASR engines
    AVAILABLE_ENGINES = [
        "videocaptioner",   # 免费, 推荐
        "siliconcloud",     # 付费, 高质量
        "faster_whisper",   # 本地
    ]

    # Default engine (免费)
    DEFAULT_ENGINE = "videocaptioner"

    def __init__(
        self,
        engine: str = "videocaptioner",
        use_cache: bool = True,
        need_word_time_stamp: bool = False,
        cache_dir: Path | None = None,
        asr_engine: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Initialize AudioTranscriber.

        Args:
            engine: ASR engine to use
                - 'videocaptioner': 免费 (推荐)
                - 'siliconcloud': 付费 (高质量)
                - 'faster_whisper': 本地
            use_cache: Whether to cache recognition results
            need_word_time_stamp: Whether to return word-level timestamps
            cache_dir: Cache directory path
            asr_engine: For videocaptioner, specific backend (bijian/jianying/faster-whisper)
            api_key: For siliconcloud, API key (or use env var SILICONCLOUD_API_KEY)
            model: For siliconcloud, model name (TeleAI/TeleSpeechASR, 默认)
        """
        self.engine = engine
        self.use_cache = use_cache
        self.need_word_time_stamp = need_word_time_stamp
        self.cache_dir = cache_dir or Path("data/cache/asr")
        self.asr_engine = asr_engine or "bijian"  # videocaptioner default
        self.api_key = api_key
        self.model = model or "TeleAI/TeleSpeechASR"  # siliconcloud default

        # Validate engine
        if engine not in self.AVAILABLE_ENGINES:
            logger.warning(f"Unknown engine: {engine}, using default '{self.DEFAULT_ENGINE}'")
            self.engine = self.DEFAULT_ENGINE

        logger.info(
            f"AudioTranscriber initialized: engine={self.engine}, "
            f"asr_backend={self.asr_engine}, model={self.model}"
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

        # Extract kwargs for specific engines
        asr_engine = kwargs.get("asr_engine", self.asr_engine)
        api_key = kwargs.get("api_key", self.api_key)
        model = kwargs.get("model", self.model)

        # Create ASR instance based on engine
        if self.engine == "videocaptioner":
            # VideoCaptioner CLI (免费, 推荐)
            asr = VideoCaptionerASR(
                audio_input=audio_input,
                use_cache=self.use_cache,
                need_word_time_stamp=self.need_word_time_stamp,
                cache_dir=self.cache_dir,
                asr_engine=asr_engine,
            )
        elif self.engine == "siliconcloud":
            # SiliconCloud API (付费, 高质量)
            # Get API key from env if not provided
            if not api_key:
                api_key = os.environ.get("SILICONCLOUD_API_KEY")

            if not api_key:
                raise ValueError(
                    "SiliconCloud API key required. "
                    "Set via environment variable 'SILICONCLOUD_API_KEY' "
                    "or pass 'api_key' parameter. "
                    "Get your key at: https://cloud.siliconflow.cn/account/ak"
                )

            asr = SiliconCloudASR(
                audio_input=audio_input,
                use_cache=self.use_cache,
                need_word_time_stamp=self.need_word_time_stamp,
                cache_dir=self.cache_dir,
                api_key=api_key,
                model=model,
            )
        else:
            # Fallback to VideoCaptioner with faster-whisper
            logger.warning(f"Engine '{self.engine}' not implemented, using 'videocaptioner'")
            asr = VideoCaptionerASR(
                audio_input=audio_input,
                use_cache=self.use_cache,
                need_word_time_stamp=self.need_word_time_stamp,
                cache_dir=self.cache_dir,
                asr_engine="faster-whisper",
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
    "BaseASR",
    "VideoCaptionerASR",
    "SiliconCloudASR",
]