"""
Integration tests for Phase 7 end-to-end backend integration.
Mocks transcribe(), retrieve_with_breakdown(), and generate() at the API boundary.
"""

import io
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.exceptions import STTProcessingError, RetrievalError, GenerationError
from app.schemas import TranscriptionResult
from app.retrieval.records import RetrievedChunk
from app.generation.models import GenerationResult

client = TestClient(app)

DUMMY_AUDIO_CONTENT = b"RIFF dummy audio content for testing integration pipeline"


@pytest.fixture
def mock_transcribe_success():
    with patch("app.api.main.transcribe") as mock:
        mock.return_value = TranscriptionResult(
            text="What is a corporation?",
            language="en-IN",
            status="success",
            latency_ms=120.0,
            provider="sarvam"
        )
        yield mock


@pytest.fixture
def mock_retrieve_success():
    with patch("app.api.main.retrieve_with_breakdown") as mock:
        mock.return_value = (
            [
                RetrievedChunk(
                    chunk_id="chunk_1",
                    document_id="doc_1",
                    text="A corporation is a legal entity created by state law.",
                    score=0.95,
                    metadata={"strategy_used": "fixed"}
                )
            ],
            15.5,
            8.2
        )
        yield mock


@pytest.fixture
def mock_generate_success():
    with patch("app.api.main.generate") as mock:
        mock.return_value = GenerationResult(
            answer="A corporation is a legal entity created by law.",
            grounded=True,
            citations=["chunk_1"],
            refusal=False,
            model="llama-3.1-8b-instant",
            latency_ms=250.0,
            guardrail_latency_ms=18.5
        )
        yield mock


def test_query_success(mock_transcribe_success, mock_retrieve_success, mock_generate_success):
    """Test standard successful voice RAG pipeline flow."""
    files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
    response = client.post("/query", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["transcript"] == "What is a corporation?"
    assert data["answer"] == "A corporation is a legal entity created by law."
    assert data["status"] == "SUCCESS"
    assert data["grounded"] is True
    assert len(data["retrieved_chunks"]) == 1
    assert data["retrieved_chunks"][0]["chunk_id"] == "chunk_1"
    assert data["retrieved_chunks"][0]["strategy_used"] == "fixed"

    # Verify latency breakdown is present and accurate
    latency = data["latency"]
    assert latency["stt_ms"] > 0
    assert latency["embedding_ms"] == 15.5
    assert latency["retrieval_ms"] == 8.2
    assert latency["generation_ms"] == 250.0
    assert latency["guardrail_ms"] == 18.5
    assert latency["rag_pipeline_ms"] > 0
    assert latency["total_ms"] > 0


def test_query_missing_audio():
    """Test API behavior when audio file parameter is missing."""
    response = client.post("/query")
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation)


def test_query_empty_audio(mock_transcribe_success):
    """Test API behavior when audio file upload is empty."""
    files = {"audio": ("test.wav", io.BytesIO(b""), "audio/wav")}
    response = client.post("/query", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_query_stt_failure():
    """Test API behavior when STT provider fails and returns error status."""
    with patch("app.api.main.transcribe") as mock_transcribe:
        mock_transcribe.return_value = TranscriptionResult(
            text="",
            status="error",
            latency_ms=50.0,
            provider="sarvam",
            error="Sarvam service unavailable"
        )
        files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
        response = client.post("/query", files=files)
        assert response.status_code == 502
        assert "unavailable" in response.json()["detail"].lower()


def test_query_stt_exception():
    """Test API behavior when STT provider throws STTProcessingError."""
    with patch("app.api.main.transcribe") as mock_transcribe:
        mock_transcribe.side_effect = STTProcessingError("Invalid audio format detected.")
        files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
        response = client.post("/query", files=files)
        assert response.status_code == 502
        assert "invalid audio format" in response.json()["detail"].lower()


def test_query_empty_transcript():
    """Test API behavior when transcription runs successfully but returns empty text."""
    with patch("app.api.main.transcribe") as mock_transcribe:
        mock_transcribe.return_value = TranscriptionResult(
            text="   ",
            status="success",
            latency_ms=110.0,
            provider="sarvam"
        )
        files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
        response = client.post("/query", files=files)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


def test_query_retrieval_failure(mock_transcribe_success):
    """Test API behavior when retrieval process fails."""
    with patch("app.api.main.retrieve_with_breakdown") as mock_retrieve:
        mock_retrieve.side_effect = RetrievalError("FAISS database not found.")
        files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
        response = client.post("/query", files=files)
        assert response.status_code == 500
        assert "not found" in response.json()["detail"].lower()


def test_query_generation_failure(mock_transcribe_success, mock_retrieve_success):
    """Test API behavior when generation process fails."""
    with patch("app.api.main.generate") as mock_generate:
        mock_generate.side_effect = GenerationError("Groq API rate limit reached.")
        files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
        response = client.post("/query", files=files)
        assert response.status_code == 502
        assert "rate limit" in response.json()["detail"].lower()


def test_query_guardrail_refusal(mock_transcribe_success, mock_retrieve_success):
    """Test API behavior when input guardrails trigger a refusal."""
    with patch("app.api.main.generate") as mock_generate:
        mock_generate.return_value = GenerationResult(
            answer="That question is outside the scope of the available information.",
            grounded=True,
            citations=[],
            refusal=True,
            refusal_reason="OFF_TOPIC",
            model="policy",
            latency_ms=0.0,
            guardrail_latency_ms=8.5
        )
        files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
        response = client.post("/query", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OFF_TOPIC"
        assert data["grounded"] is False
        assert "outside the scope" in data["answer"]
        assert data["latency"]["guardrail_ms"] == 8.5
        assert data["latency"]["generation_ms"] == 0.0
