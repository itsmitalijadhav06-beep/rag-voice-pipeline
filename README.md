# Voice-Enabled RAG Pipeline — Hacker House Goa 2026

Shortlisting Task 2: High-Performance Voice-Enabled Retrieval-Augmented Generation (RAG) System.

## Pipeline Architecture Overview
```
Voice Input -> Speech-to-Text -> Chunking/Retrieval (Vector DB) -> Answer Generation
                                              │                         │
                                     Guardrails Engine        Reliability Harness
                                              │                         │
                                      Latency Analytics Dashboard & Telemetry
```

## Features & Requirements Compliance
- **Speech-to-Text**: Plug-and-play abstraction for Sarvam AI and ElevenLabs.
- **Vast Chunking Strategy**: Multi-tier chunking (Fixed-size overlap, Semantic splitting, Metadata-aware chunking).
- **Sub-200ms Target**: Performance-tuned vector retrieval + lightweight inference path.
- **P50 / P70 / P100 Telemetry**: Built-in latency analytics suite for benchmark runs.
- **Reliability Harness**: Retry policy with exponential backoff, structured output parsing, error recovery.
- **Guardrails**: Query safety filter, groundedness evaluation, hallucination detection, explicit refusal mechanism.

## Project Structure
```
rag-voice-pipeline/
├── app/
│   ├── api/          # FastAPI routes & endpoints
│   ├── stt/          # Sarvam & ElevenLabs speech-to-text engines
│   ├── retrieval/    # Chunking strategies & Vector DB indexers
│   ├── generation/   # LLM synthesis & grounded answer generation
│   ├── guardrails/   # Safety & hallucination guardrail checks
│   ├── analytics/    # Latency tracking (P50/P70/P100)
│   ├── core/         # Config, structured logging, custom exceptions
│   └── schemas/      # Pydantic data models
├── data/             # Raw, processed, and vector index storage
├── scripts/          # Benchmark and dataset preprocessing scripts
├── tests/            # Test suite
└── run.py            # Uvicorn app runner
```

## Quickstart

1. Copy `.env.example` to `.env` and fill in credentials:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   python run.py
   ```
