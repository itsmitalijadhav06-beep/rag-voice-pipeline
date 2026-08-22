"""
Unit tests for STT integration local test script CLI.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from scripts.test_stt import main, parse_arguments
from app.schemas import TranscriptionResult
from app.core.exceptions import STTProcessingError

def test_parse_arguments():
    """Verify argparse parsing functionality."""
    # Test case 1: Parse provided --audio and --language arguments
    test_args = ["--audio", "dummy.wav", "--language", "en-IN", "--provider", "sarvam"]
    with patch("sys.argv", ["test_stt.py"] + test_args):
        args = parse_arguments()
        assert args.audio == "dummy.wav"
        assert args.language == "en-IN"
        assert args.provider == "sarvam"

    # Test case 2: Defaults
    test_args_defaults = []
    with patch("sys.argv", ["test_stt.py"] + test_args_defaults):
        args = parse_arguments()
        assert args.audio is None
        assert args.language is None
        assert args.provider == "sarvam"


@pytest.mark.anyio
async def test_cli_success(capsys, tmp_path):
    """Test main function with successful transcription."""
    dummy_wav = tmp_path / "dummy.wav"
    dummy_wav.write_bytes(b"some audio data")

    mock_args = MagicMock()
    mock_args.audio = str(dummy_wav)
    mock_args.language = "hi-IN"
    mock_args.provider = "sarvam"

    mock_engine = MagicMock()
    async def mock_transcribe(audio_input, language_code=None):
        return TranscriptionResult(
            text="Hello World",
            language="hi-IN",
            status="success",
            latency_ms=150.0,
            provider="sarvam"
        )
    mock_engine.transcribe.side_effect = mock_transcribe

    with patch("scripts.test_stt.parse_arguments", return_value=mock_args), \
         patch("scripts.test_stt.get_stt_engine", return_value=mock_engine):
        
        await main()

    captured = capsys.readouterr().out
    assert "Audio:" in captured
    assert "dummy.wav" in captured
    assert "Provider:\nsarvam" in captured
    assert "Requested language:\nhi-IN" in captured
    assert "Status:\nsuccess" in captured
    assert "Latency:\n150.00 ms" in captured
    assert "Transcript:\nHello World" in captured
    assert "Error:" not in captured


@pytest.mark.anyio
async def test_cli_missing_file(capsys):
    """Test main function with missing file error handling."""
    mock_args = MagicMock()
    mock_args.audio = "non_existent_file.wav"
    mock_args.language = None
    mock_args.provider = "sarvam"

    with patch("scripts.test_stt.parse_arguments", return_value=mock_args), \
         patch("sys.exit") as mock_exit:
        
        await main()
        mock_exit.assert_called_once_with(1)

    captured = capsys.readouterr().out
    assert "Audio file does not exist" in captured
    assert "non_existent_file.wav" in captured


@pytest.mark.anyio
async def test_cli_empty_transcript(capsys, tmp_path):
    """Test main function handling empty transcript."""
    dummy_wav = tmp_path / "dummy.wav"
    dummy_wav.write_bytes(b"some audio data")

    mock_args = MagicMock()
    mock_args.audio = str(dummy_wav)
    mock_args.language = None
    mock_args.provider = "sarvam"

    mock_engine = MagicMock()
    async def mock_transcribe(audio_input, language_code=None):
        return TranscriptionResult(
            text="",
            language=None,
            status="success",
            latency_ms=100.0,
            provider="sarvam"
        )
    mock_engine.transcribe.side_effect = mock_transcribe

    with patch("scripts.test_stt.parse_arguments", return_value=mock_args), \
         patch("scripts.test_stt.get_stt_engine", return_value=mock_engine):
        
        await main()

    captured = capsys.readouterr().out
    assert "Status:\nerror" in captured
    assert "Transcript:\n(empty)" in captured
    assert "Error:\nEmpty transcription received from provider." in captured
    assert "Check that the audio contains audible speech." in captured


@pytest.mark.anyio
async def test_cli_processing_error(capsys, tmp_path):
    """Test main function handling STTProcessingError."""
    dummy_wav = tmp_path / "dummy.wav"
    dummy_wav.write_bytes(b"some audio data")

    mock_args = MagicMock()
    mock_args.audio = str(dummy_wav)
    mock_args.language = None
    mock_args.provider = "sarvam"

    mock_engine = MagicMock()
    mock_engine.transcribe.side_effect = STTProcessingError("Authentication failed.")

    with patch("scripts.test_stt.parse_arguments", return_value=mock_args), \
         patch("scripts.test_stt.get_stt_engine", return_value=mock_engine):
        
        await main()

    captured = capsys.readouterr().out
    assert "Status:\nerror" in captured
    assert "Error:\nAuthentication failed." in captured
