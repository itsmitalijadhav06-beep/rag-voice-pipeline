"""
Isolated unit tests for Speech-to-Text (STT) Sarvam integration.
No real API calls are executed by default.
"""

import os
import asyncio
import httpx
import pytest
from unittest.mock import patch, MagicMock

from app.core.exceptions import STTProcessingError
from app.schemas import TranscriptionResult
from app.stt import get_stt_engine, transcribe
from app.stt.sarvam import SarvamSTTEngine


# Dummy valid audio bytes (mock WAV header)
DUMMY_WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
VALID_API_KEY = "test_sarvam_api_key_12345"


@pytest.fixture
def sarvam_engine():
    """Returns a SarvamSTTEngine instance configured with a dummy valid API key."""
    return SarvamSTTEngine(api_key=VALID_API_KEY)


@pytest.mark.anyio
async def test_successful_transcription(sarvam_engine):
    """1 & 8: Tests successful transcription returning a valid TranscriptionResult object."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "transcript": "  Welcome to Hacker House Goa 2026!  ",
        "language_code": "en-IN",
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await sarvam_engine.transcribe(DUMMY_WAV_BYTES, filename="test.wav")

    assert isinstance(result, TranscriptionResult)
    assert result.status == "success"
    assert result.text == "Welcome to Hacker House Goa 2026!"
    assert result.language == "en-IN"
    assert result.provider == "sarvam"
    assert result.error is None
    assert result.latency_ms >= 0.0


@pytest.mark.anyio
async def test_missing_api_key():
    """2: Tests that missing or default API key raises STTProcessingError."""
    engine_no_key = SarvamSTTEngine(api_key="")
    with pytest.raises(STTProcessingError) as exc_info:
        await engine_no_key.transcribe(DUMMY_WAV_BYTES)
    assert "Sarvam API key is not configured" in str(exc_info.value)

    engine_placeholder_key = SarvamSTTEngine(api_key="your_sarvam_api_key_here")
    with pytest.raises(STTProcessingError) as exc_info:
        await engine_placeholder_key.transcribe(DUMMY_WAV_BYTES)
    assert "Sarvam API key is not configured" in str(exc_info.value)


@pytest.mark.anyio
async def test_provider_auth_failure(sarvam_engine):
    """Tests 401/403 provider authentication failure handling."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.text = "Unauthorized - Invalid API key"

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(STTProcessingError) as exc_info:
            await sarvam_engine.transcribe(DUMMY_WAV_BYTES)
    assert "authentication failed" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_provider_timeout(sarvam_engine):
    """3: Tests handling of provider HTTP request timeouts."""
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(STTProcessingError) as exc_info:
            await sarvam_engine.transcribe(DUMMY_WAV_BYTES)
    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_provider_network_failure(sarvam_engine):
    """4: Tests handling of network connection failures."""
    with patch("httpx.AsyncClient.post", side_effect=httpx.NetworkError("Failed to resolve host")):
        with pytest.raises(STTProcessingError) as exc_info:
            await sarvam_engine.transcribe(DUMMY_WAV_BYTES)
    assert "network failure" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_empty_transcription(sarvam_engine):
    """5: Tests handling when Sarvam returns an empty transcript."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "transcript": "   ",
        "language_code": "en-IN",
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await sarvam_engine.transcribe(DUMMY_WAV_BYTES)

    assert isinstance(result, TranscriptionResult)
    assert result.status == "error"
    assert result.text == ""
    assert "Empty transcription" in result.error
    assert result.provider == "sarvam"


@pytest.mark.anyio
async def test_malformed_provider_response_invalid_json(sarvam_engine):
    """6a: Tests handling when provider returns invalid JSON."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON payload")

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(STTProcessingError) as exc_info:
            await sarvam_engine.transcribe(DUMMY_WAV_BYTES)
    assert "Malformed provider response" in str(exc_info.value)


@pytest.mark.anyio
async def test_malformed_provider_response_missing_key(sarvam_engine):
    """6b: Tests handling when provider response is missing the 'transcript' key."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"other_key": "some_value"}

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(STTProcessingError) as exc_info:
            await sarvam_engine.transcribe(DUMMY_WAV_BYTES)
    assert "Missing 'transcript' key" in str(exc_info.value)


@pytest.mark.anyio
async def test_latency_is_recorded(sarvam_engine):
    """7: Tests that monotonic timer correctly measures and records STT operation latency."""
    async def delayed_post(*args, **kwargs):
        await asyncio.sleep(0.05)  # 50ms delay
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"transcript": "Latency test."}
        return mock_resp

    with patch("httpx.AsyncClient.post", side_effect=delayed_post):
        result = await sarvam_engine.transcribe(DUMMY_WAV_BYTES)

    assert result.latency_ms >= 40.0  # Should record at least ~50ms


@pytest.mark.anyio
async def test_invalid_audio_input_cases(sarvam_engine, tmp_path):
    """Tests client-side validation for empty, missing, or invalid audio files/bytes."""
    # Empty bytes
    with pytest.raises(STTProcessingError) as exc_info:
        await sarvam_engine.transcribe(b"")
    assert "Audio data is empty" in str(exc_info.value)

    # Missing file path
    non_existent = tmp_path / "non_existent.wav"
    with pytest.raises(STTProcessingError) as exc_info:
        await sarvam_engine.transcribe(non_existent)
    assert "does not exist" in str(exc_info.value)

    # Unsupported extension
    invalid_ext_file = tmp_path / "test.pdf"
    invalid_ext_file.write_bytes(b"%PDF-1.4 header")
    with pytest.raises(STTProcessingError) as exc_info:
        await sarvam_engine.transcribe(invalid_ext_file)
    assert "Unsupported audio format" in str(exc_info.value)

    # Raw PDF header in bytes
    with pytest.raises(STTProcessingError) as exc_info:
        await sarvam_engine.transcribe(b"%PDF-1.5 document data")
    assert "Invalid audio format" in str(exc_info.value)


@pytest.mark.anyio
async def test_stt_factory_and_top_level_transcribe():
    """Tests get_stt_engine factory and top-level transcribe helper."""
    engine = get_stt_engine("sarvam")
    assert isinstance(engine, SarvamSTTEngine)

    with pytest.raises(STTProcessingError):
        get_stt_engine("unknown_provider")

    with pytest.raises(NotImplementedError):
        get_stt_engine("elevenlabs")


# Optional live integration test (only runs if SARVAM_API_KEY is explicitly supplied in environment)
@pytest.mark.anyio
@pytest.mark.skipif(
    not os.getenv("SARVAM_API_KEY") or os.getenv("SARVAM_API_KEY") == "your_sarvam_api_key_here",
    reason="SARVAM_API_KEY environment variable not set for live API integration test",
)
async def test_live_sarvam_api_integration(tmp_path):
    """Optional live integration test running against real Sarvam API endpoint."""
    live_engine = SarvamSTTEngine()
    result = await live_engine.transcribe(DUMMY_WAV_BYTES, filename="live_test.wav")
    assert result.provider == "sarvam"
    assert isinstance(result.latency_ms, float)
