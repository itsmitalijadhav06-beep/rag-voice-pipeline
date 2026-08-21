"""
Pydantic Schemas for Request/Response payloads, telemetry, and harness structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class STTRequest(BaseModel):
    provider: Optional[str] = Field(None, description="STT Provider: sarvam or elevenlabs")
    language_code: Optional[str] = Field("en-IN", description="Language code")


class STTResponse(BaseModel):
    transcript: str
    confidence: float = 1.0
    latency_ms: float
    provider_used: str


class TranscriptionResult(BaseModel):
    text: str = Field("", description="Transcribed text string")
    language: Optional[str] = Field(None, description="Detected or specified language code")
    status: str = Field("success", description="Status of transcription: success or error")
    latency_ms: float = Field(0.0, description="Speech-to-Text operation latency in milliseconds")
    provider: str = Field("sarvam", description="STT provider name")
    error: Optional[str] = Field(None, description="Error message if transcription failed")


class DocumentRecord(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the document record")
    text: str = Field(..., description="Raw text content of the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class ChunkRecord(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    document_id: str = Field(..., description="Parent document identifier")
    text: str = Field(..., description="Text content of the chunk")
    strategy: str = Field(..., description="Chunking strategy used (fixed_overlap, sentence, passage_metadata)")
    start_position: Optional[int] = Field(None, description="Start character offset in parent document")
    end_position: Optional[int] = Field(None, description="End character offset in parent document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Preserved metadata dictionary")




class ContextChunk(BaseModel):
    chunk_id: str
    text: str
    score: float
    strategy_used: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GuardrailCheckResult(BaseModel):
    passed: bool
    reason: Optional[str] = None
    off_topic: bool = False
    unsafe: bool = False
    grounded: bool = True
    refusal_triggered: bool = False


class RAGQueryRequest(BaseModel):
    query_text: Optional[str] = None
    audio_base64: Optional[str] = None
    chunking_strategy: str = "semantic"
    top_k: int = 3


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    grounded: bool
    retrieved_chunks: List[ContextChunk]
    guardrail_status: GuardrailCheckResult
    stt_latency_ms: Optional[float] = Field(None, description="Speech-to-Text transcription latency")
    rag_pipeline_latency_ms: float = Field(..., description="Chunking + Vector DB retrieval + generation latency (Sub-200ms target path)")
    total_latency_ms: float = Field(..., description="End-to-end total execution time")
    latency_breakdown_ms: Dict[str, float] = Field(default_factory=dict)
    sla_met: bool = Field(..., description="True if rag_pipeline_latency_ms is under SLA target")


class LatencyTelemetry(BaseModel):
    sample_count: int
    p50_ms: float
    p70_ms: float
    p100_ms: float
    sla_compliance_rate: float
