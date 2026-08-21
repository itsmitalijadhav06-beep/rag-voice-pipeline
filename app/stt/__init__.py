"""
Speech-to-Text (STT) package providing plug-and-play interfaces for Sarvam AI and ElevenLabs.
"""

from abc import ABC, abstractmethod
from app.schemas import STTResponse


class BaseSTTEngine(ABC):
    """Abstract Base Class for Speech-to-Text Engines."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language_code: str = "en-IN") -> STTResponse:
        """Transcribe audio bytes to text transcript."""
        pass
