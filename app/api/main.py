"""
FastAPI Main Web Application for Voice-Enabled RAG Pipeline.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.analytics import latency_tracker
from app.schemas import LatencyTelemetry

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
