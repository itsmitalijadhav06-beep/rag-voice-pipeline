"""
FastAPI Main Web Application for Voice-Enabled RAG Pipeline.
"""

import time
from typing import Optional, List
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import BaseRAGException, STTProcessingError
from app.analytics import latency_tracker
from app.stt import transcribe
from app.retrieval.retrieve import retrieve_with_breakdown
from app.generation import generate
from app.schemas import (
    LatencyTelemetry,
    ContextChunk,
    VoiceQueryResponse,
    PipelineLatencyBreakdown,
)

app = FastAPI(
    title="Voice-Enabled RAG Pipeline API",
    description="Hacker House Goa 2026 Shortlisting Task 2 — Voice RAG API with Sub-200ms Target",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BaseRAGException)
async def rag_exception_handler(request, exc: BaseRAGException):
    logger.error("RAG error in API: status_code=%d, message=%s", exc.status_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    logger.exception("Unexpected error in API endpoint: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred."}
    )


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint confirming API status and active configuration."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "stt_provider": settings.STT_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER,
        "vector_db_type": settings.VECTOR_DB_TYPE,
        "sla_target_ms": settings.MAX_LATENCY_SLA_MS,
    }


@app.get("/analytics/latency", response_model=LatencyTelemetry, tags=["Analytics"])
async def get_latency_metrics():
    """Fetch current P50, P70, P100 latency analytics and SLA compliance rate."""
    return latency_tracker.get_telemetry(sla_ms=settings.MAX_LATENCY_SLA_MS)


@app.post("/query", response_model=VoiceQueryResponse, tags=["Query"])
async def query_pipeline(
    audio: UploadFile = File(...),
    strategy: str = "fixed",
    top_k: int = 5,
    stt_provider: Optional[str] = None,
    llm_provider: Optional[str] = None,
):
    """
    End-to-end Voice-Enabled RAG Query endpoint.
    Accepts audio via multipart/form-data.
    Processes: Audio validation -> STT -> Retrieval -> Generation with guardrails -> Response.
    """
    overall_start = time.perf_counter()

    # 1. Audio validation
    if not audio:
        raise HTTPException(status_code=400, detail="Audio file is required.")

    # Read audio bytes
    try:
        audio_bytes = await audio.read()
    except Exception as exc:
        logger.error("Failed to read audio file: %s", str(exc))
        raise HTTPException(status_code=400, detail="Failed to read audio file.") from exc

    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    # 2. STT
    stt_start = time.perf_counter()
    stt_res = await transcribe(
        audio_input=audio_bytes,
        filename=audio.filename,
        provider=stt_provider or settings.STT_PROVIDER
    )
    stt_ms = (time.perf_counter() - stt_start) * 1000

    if stt_res.status == "error":
        raise STTProcessingError(stt_res.error or "Speech-to-text processing failed.")

    if not stt_res.text or not stt_res.text.strip():
        raise HTTPException(status_code=400, detail="Transcribed text is empty. Please speak clearly.")

    query = stt_res.text.strip()

    # 3. Retrieval
    # Starts the sub-200ms target RAG path timer
    rag_start = time.perf_counter()

    retrieved_chunks, embedding_ms, retrieval_ms = retrieve_with_breakdown(
        query=query,
        top_k=top_k,
        strategy=strategy
    )

    # 4. Generation + Guardrails (Reliability Harness)
    gen_res = await generate(
        query=query,
        chunks=retrieved_chunks,
        provider=llm_provider or settings.LLM_PROVIDER
    )

    # Compute RAG processing path latency
    rag_pipeline_ms = (time.perf_counter() - rag_start) * 1000

    # Calculate overall total latency
    total_ms = (time.perf_counter() - overall_start) * 1000

    # Map the retrieved chunks to the schema ContextChunk for response
    context_chunks = [
        ContextChunk(
            chunk_id=c.chunk_id,
            text=c.text,
            score=c.score,
            strategy_used=c.metadata.get("strategy_used") or strategy,
            metadata=c.metadata
        )
        for c in retrieved_chunks
    ]

    # Map the response status based on whether refusal is triggered
    status = "SUCCESS"
    if gen_res.refusal:
        status = gen_res.refusal_reason or "REFUSED"

    latency_breakdown = PipelineLatencyBreakdown(
        stt_ms=stt_ms,
        embedding_ms=embedding_ms,
        retrieval_ms=retrieval_ms,
        generation_ms=gen_res.latency_ms,
        guardrail_ms=gen_res.guardrail_latency_ms,
        rag_pipeline_ms=rag_pipeline_ms,
        total_ms=total_ms
    )

    return VoiceQueryResponse(
        transcript=query,
        answer=gen_res.answer,
        status=status,
        grounded=gen_res.grounded,
        retrieved_chunks=context_chunks,
        latency=latency_breakdown
    )
