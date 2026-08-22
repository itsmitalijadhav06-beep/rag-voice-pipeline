import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.api.main import app
from app.generation.models import GenerationResult
from app.schemas import TranscriptionResult
from app.retrieval.records import RetrievedChunk

client = TestClient(app)
DUMMY_AUDIO_CONTENT = b"RIFF dummy audio content for testing integration pipeline"

@pytest.fixture
def mock_transcribe():
    with patch("app.api.main.transcribe") as mock:
        mock.return_value = TranscriptionResult(
            text="What is corporation?",
            language="en",
            status="success",
            latency_ms=10.0,
            provider="sarvam"
        )
        yield mock

@pytest.fixture
def mock_retrieve():
    with patch("app.api.main.retrieve_with_breakdown") as mock:
        mock.return_value = (
            [
                RetrievedChunk(
                    chunk_id="chunk_1",
                    document_id="doc_1",
                    text="Corporation context info.",
                    score=0.95,
                    metadata={"strategy_used": "fixed"}
                )
            ],
            5.0,
            2.0
        )
        yield mock

@pytest.mark.parametrize(
    "refusal, refusal_reason, gen_grounded, expected_status, expected_grounded",
    [
        (False, None, True, "SUCCESS", True),
        (False, None, False, "UNGROUNDED", False),
        (True, "UNSAFE", False, "UNSAFE", False),
        (True, "OFF_TOPIC", False, "OFF_TOPIC", False),
        (True, "INSUFFICIENT_CONTEXT", False, "INSUFFICIENT_CONTEXT", False),
        (True, "UNGROUNDED", False, "UNGROUNDED", False),
        (True, "REFUSED", False, "REFUSED", False),
        # Test case reproducing the previous inconsistency: refusal=True and grounded=True from harness
        (True, "UNGROUNDED", True, "UNGROUNDED", False),
        (True, "UNSAFE", True, "UNSAFE", False),
        (True, "OFF_TOPIC", True, "OFF_TOPIC", False),
        (True, "INSUFFICIENT_CONTEXT", True, "INSUFFICIENT_CONTEXT", False),
    ]
)
def test_status_and_grounded_are_consistent(
    mock_transcribe,
    mock_retrieve,
    refusal,
    refusal_reason,
    gen_grounded,
    expected_status,
    expected_grounded
):
    """Verify that `/query` status and grounded fields are consistent across different generation results."""
    with patch("app.api.main.generate") as mock_generate:
        mock_generate.return_value = GenerationResult(
            answer="Some response text.",
            grounded=gen_grounded,
            citations=[] if refusal else ["chunk_1"],
            refusal=refusal,
            refusal_reason=refusal_reason,
            model="test-model",
            latency_ms=10.0,
            guardrail_latency_ms=1.0
        )

        files = {"audio": ("test.wav", io.BytesIO(DUMMY_AUDIO_CONTENT), "audio/wav")}
        response = client.post("/query", files=files)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == expected_status
        assert data["grounded"] is expected_grounded
