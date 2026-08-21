"""
Sarvam AI Speech-to-Text implementation using standard REST API via httpx.
"""

import time
from pathlib import Path
from typing import Optional, Union, BinaryIO, Tuple
import httpx

from app.core.config import settings
from app.core.exceptions import STTProcessingError
from app.core.logging import logger
from app.schemas import TranscriptionResult
from app.stt import BaseSTTEngine

SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".aiff",
    ".amr",
    ".wma",
    ".webm",
    ".pcm",
}

# Maximum allowed audio payload size (25 MB)
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024


class SarvamSTTEngine(BaseSTTEngine):
    """
    Sarvam AI Speech-to-Text Engine.
    Uses the Sarvam AI REST API endpoint: https://api.sarvam.ai/speech-to-text
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = "https://api.sarvam.ai/speech-to-text",
        model: str = "saaras:v3",
        timeout: float = 30.0,
    ):
        self.api_key = api_key if api_key is not None else settings.SARVAM_API_KEY
        self.api_url = api_url
        self.model = model
        self.timeout = timeout

    def _validate_and_load_audio(
        self,
        audio_input: Union[str, Path, bytes, BinaryIO],
        filename: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        Validates audio input and extracts raw bytes and filename.
        Raises STTProcessingError if validation fails.
        """
        if audio_input is None:
            raise STTProcessingError("Audio input cannot be None.")

        audio_bytes: bytes = b""
        resolved_filename: str = filename or "audio.wav"

        if isinstance(audio_input, (str, Path)):
            file_path = Path(audio_input)
            if not file_path.exists():
                raise STTProcessingError(f"Audio file does not exist: {file_path}")
            if file_path.is_dir():
                raise STTProcessingError(f"Audio file path is a directory: {file_path}")

            ext = file_path.suffix.lower()
            if ext and ext not in SUPPORTED_AUDIO_EXTENSIONS:
                raise STTProcessingError(
                    f"Unsupported audio format '{ext}'. "
                    f"Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
                )

            file_size = file_path.stat().st_size
            if file_size == 0:
                raise STTProcessingError("Audio file is empty.")
            if file_size > MAX_AUDIO_SIZE_BYTES:
                raise STTProcessingError("Audio file size exceeds maximum limit of 25MB.")

            try:
                audio_bytes = file_path.read_bytes()
            except Exception as e:
                raise STTProcessingError(f"Failed to read audio file: {e}") from e

            resolved_filename = filename or file_path.name

        elif isinstance(audio_input, bytes):
            if len(audio_input) == 0:
                raise STTProcessingError("Audio data is empty.")
            if len(audio_input) > MAX_AUDIO_SIZE_BYTES:
                raise STTProcessingError("Audio data size exceeds maximum limit of 25MB.")

            # Validate header bytes for obvious non-audio file formats
            header = audio_input[:10]
            if (
                header.startswith(b"%PDF")
                or header.startswith(b"MZ")
                or header.startswith(b"<!DOC")
                or header.startswith(b"<html>")
                or header.startswith(b"{\"")
            ):
                raise STTProcessingError("Invalid audio format or non-audio file detected.")

            audio_bytes = audio_input
            resolved_filename = filename or "audio.wav"

        elif hasattr(audio_input, "read"):
            try:
                content = audio_input.read()
            except Exception as e:
                raise STTProcessingError(f"Failed to read from audio stream: {e}") from e

            if isinstance(content, str):
                content = content.encode("utf-8")

            if not content or len(content) == 0:
                raise STTProcessingError("Audio stream is empty.")
            if len(content) > MAX_AUDIO_SIZE_BYTES:
                raise STTProcessingError("Audio stream size exceeds maximum limit of 25MB.")

            audio_bytes = content
            stream_name = getattr(audio_input, "name", None)
            if stream_name and isinstance(stream_name, str):
                resolved_filename = filename or Path(stream_name).name
            else:
                resolved_filename = filename or "audio.wav"

            ext = Path(resolved_filename).suffix.lower()
            if ext and ext not in SUPPORTED_AUDIO_EXTENSIONS:
                raise STTProcessingError(
                    f"Unsupported audio format '{ext}'. "
                    f"Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
                )

        else:
            raise STTProcessingError(f"Invalid audio input type: {type(audio_input).__name__}")

        return audio_bytes, resolved_filename

    def _get_mime_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        mime_map = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".aac": "audio/aac",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".opus": "audio/ogg",
            ".aiff": "audio/aiff",
            ".amr": "audio/amr",
            ".wma": "audio/x-ms-wma",
            ".webm": "audio/webm",
            ".pcm": "audio/pcm",
        }
        return mime_map.get(ext, "audio/wav")

    async def transcribe(
        self,
        audio_input: Union[str, Path, bytes, BinaryIO],
        filename: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio using Sarvam AI STT REST API.
        Measures pure STT latency using time.perf_counter().
        """
        if not self.api_key or not self.api_key.strip() or self.api_key == "your_sarvam_api_key_here":
            logger.error("STT request failed: Sarvam API key is not configured")
            raise STTProcessingError("Sarvam API key is not configured.")

        audio_bytes, resolved_filename = self._validate_and_load_audio(audio_input, filename)
        mime_type = self._get_mime_type(resolved_filename)

        headers = {
            "api-subscription-key": self.api_key,
        }

        files = {
            "file": (resolved_filename, audio_bytes, mime_type),
        }

        data = {
            "model": self.model,
        }
        if language_code:
            data["language_code"] = language_code

        logger.info(
            "STT request started: provider=sarvam, filename=%s, size=%d bytes",
            resolved_filename,
            len(audio_bytes),
        )

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    files=files,
                    data=data,
                )
        except httpx.TimeoutException as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("STT request failed: Provider request timed out after %.2f ms", elapsed_ms)
            raise STTProcessingError("Sarvam STT request timed out.") from exc
        except httpx.RequestError as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("STT request failed: Network error: %s", str(exc))
            raise STTProcessingError(f"Network failure while connecting to Sarvam STT API: {exc}") from exc

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if response.status_code in (401, 403):
            logger.error("STT request failed: Provider authentication failed (HTTP %d)", response.status_code)
            raise STTProcessingError("Sarvam API authentication failed. Invalid API key.")

        if response.status_code != 200:
            logger.error("STT request failed: Provider error (HTTP %d): %s", response.status_code, response.text)
            raise STTProcessingError(f"Sarvam API error (HTTP {response.status_code}): {response.text[:200]}")

        try:
            res_data = response.json()
        except Exception as exc:
            logger.error("STT request failed: Unexpected provider response (invalid JSON)")
            raise STTProcessingError("Malformed provider response: Unable to parse JSON response.") from exc

        if not isinstance(res_data, dict):
            logger.error("STT request failed: Unexpected provider response structure")
            raise STTProcessingError("Malformed provider response: Expected JSON object.")

        if "transcript" not in res_data:
            logger.error("STT request failed: Missing 'transcript' field in provider response")
            raise STTProcessingError("Malformed provider response: Missing 'transcript' key.")

        raw_transcript = res_data.get("transcript")
        detected_lang = res_data.get("language_code") or language_code

        clean_text = raw_transcript.strip() if isinstance(raw_transcript, str) else ""

        if not clean_text:
            logger.warning("STT request completed in %.2f ms but transcription is empty", elapsed_ms)
            return TranscriptionResult(
                text="",
                language=detected_lang,
                status="error",
                latency_ms=elapsed_ms,
                provider="sarvam",
                error="Empty transcription received from provider.",
            )

        logger.info(
            "STT request completed: provider=sarvam, latency=%.2f ms, transcript_len=%d",
            elapsed_ms,
            len(clean_text),
        )

        return TranscriptionResult(
            text=clean_text,
            language=detected_lang,
            status="success",
            latency_ms=elapsed_ms,
            provider="sarvam",
            error=None,
        )
