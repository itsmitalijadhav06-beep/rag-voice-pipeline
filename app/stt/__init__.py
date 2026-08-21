"""
Speech-to-Text (STT) package providing plug-and-play interfaces for Sarvam AI and ElevenLabs.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, BinaryIO

from app.core.config import settings
from app.core.exceptions import STTProcessingError
from app.schemas import TranscriptionResult


class BaseSTTEngine(ABC):
    """Abstract Base Class for Speech-to-Text Engines."""

    @abstractmethod
    async def transcribe(
        self,
        audio_input: Union[str, Path, bytes, BinaryIO],
        filename: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe audio input to TranscriptionResult."""
        pass


def get_stt_engine(provider: Optional[str] = None) -> BaseSTTEngine:
    """Factory function to retrieve configured STT Engine."""
    chosen_provider = (provider or settings.STT_PROVIDER).lower()
    if chosen_provider == "sarvam":
        from app.stt.sarvam import SarvamSTTEngine
        return SarvamSTTEngine()
    elif chosen_provider == "elevenlabs":
        raise NotImplementedError("ElevenLabs STT provider is not implemented yet.")
    else:
        raise STTProcessingError(f"Unknown STT provider '{chosen_provider}'.")


async def transcribe(
    audio_input: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
    language_code: Optional[str] = None,
    provider: Optional[str] = None,
) -> TranscriptionResult:
    """Convenience top-level transcription function."""
    engine = get_stt_engine(provider)
    return await engine.transcribe(audio_input, filename=filename, language_code=language_code)
